; widegl.asm - in MGameGL: the viewport and the field of view for a wide
; picture, at the two methods every caller goes through.
;
; The exe's wrapper (0x46bfd0, 0x46bf90) is one way to the renderer;
; MSelect sets the car select's viewport and perspective on the renderer
; itself, Champagn its perspective. So the two methods are taken over at
; their prologues:
;
;   SetViewport (0x100037c0; this, &rect, cx, cy): every rect but the
;     picture's own full one is in 640x480 terms - the race's, the
;     halves of the split screen, the frame the countdown zooms about
;     its centre, the screens' own - and is scaled to the whole picture
;     through a copy here, and the centre with it; the full one, which
;     only the exe's re-init sets, passes.
;   SetPerspective (0x10003870; this, angle, near, far): the horizontal
;     angle (65536 = 360 degrees) becomes 2 atan(tan(a/2) * (W/H) / (4/3))
;     while the picture is wider than 4:3, so the vertical field of view
;     is the 4:3 one and the extra width shows more.
;
; The picture's size is MGameD3D's, the dwords at its 0x100123fc and
; 0x10012400 (width, height), set at each of its inits: MGameGL's own
; floats (0x100128d8, 0x100128d4) are set at its one init and stay at
; 640x480 whatever the exe resizes to. The module is found once through
; GetModuleHandleA. Each entry replaces the method's prologue, does the
; prologue itself and continues after it. The annex is writable for the
; rect copy and the handle.
;
; With `trace` set (the gltrace diagnostic) each call reports itself on
; OutputDebugStringA, in hex: "sr2 vp L T R B cx cy r1 r2" as it came
; in (r1 the return address, r2 the one a wrapper's frame up), then
; "sr2 vp> L T R B cx cy" as it went on; "sr2 fov a W H a>" (W, H the
; picture's, as floats).

bits 32

%define MAGIC_SELFRVA   0xE7E7E7E7      ; this blob's RVA, filled at apply time
%define GLWIDTH         0x128d8         ; RVAs in MGameGL.dll: its own size floats, stale; traced only
%define GLHEIGHT        0x128d4
%define D3DWIDTH        0x123fc         ; RVAs in MGameD3D.dll: the picture's size, dwords
%define D3DHEIGHT       0x12400
%define IAT_GETMODULE   0x1008c         ; MGameGL's import slot
%define RESUME_VP       0x37ca          ; after the ten bytes replaced
%define RESUME_PERSP    0x3879          ; after the nine
%define IAT_LOADLIB     0x100ec         ; MGameGL's import slots
%define IAT_GETPROC     0x10088

        jmp     near viewport           ; +0
        jmp     near perspective        ; +5

; ebx = this blob and ebp = the image base, on return.
getbase:
        call    .here
.here:  pop     ebx
        sub     ebx, .here
        mov     ebp, ebx
        sub     ebp, MAGIC_SELFRVA
        ret

; The picture's size into width and height, as floats; carry when
; MGameD3D is not to be found yet. ebx = the blob, ebp = the image base.
; eax, ecx, edx scratch.
picture:
        mov     eax, [ebx + d3d]
        test    eax, eax
        jnz     .have
        lea     eax, [ebx + s_d3d]
        push    eax
        call    [ebp + IAT_GETMODULE]
        test    eax, eax
        jz      .none
        mov     [ebx + d3d], eax
.have:  fild    dword [eax + D3DWIDTH]
        fstp    dword [ebx + width]
        fild    dword [eax + D3DHEIGHT]
        fstp    dword [ebx + height]
        clc
        ret
.none:  stc
        ret

; [esp] = the return, [esp+4] this, [esp+8] the rect, [esp+0xc] cx, [esp+0x10] cy.
viewport:
        push    ebx
        push    ebp
        push    ecx
        call    getbase
        call    tracevp
        call    picture
        jc      .out
        fld     dword [ebx + width]
        fcomp   dword [ebx + k640]
        fnstsw  ax
        sahf
        jbe     .out                    ; 640 wide or less: nothing to scale to
        mov     ecx, [esp + 0x14]       ; the rect
        mov     eax, [ebx + d3d]
        cmp     dword [ecx], 0
        jne     .scale
        cmp     dword [ecx + 4], 0
        jne     .scale
        mov     eax, [eax + D3DWIDTH]
        cmp     [ecx + 8], eax          ; the full picture: as it is
        jne     .scale
        mov     eax, [ebx + d3d]
        mov     eax, [eax + D3DHEIGHT]
        cmp     [ecx + 0xc], eax
        je      .out
.scale: push    esi
        push    edi
        mov     esi, ecx
        lea     edi, [ebx + rect]
        xor     ecx, ecx
.side:  fild    dword [esi + ecx * 4]
        call    scale
        fistp   dword [edi + ecx * 4]
        inc     ecx
        cmp     ecx, 4
        jb      .side
        mov     [esp + 0x1c], edi       ; the rect argument, on the stack
        xor     ecx, ecx
        fild    dword [esp + 0x20]      ; cx
        call    scale
        fistp   dword [esp + 0x20]
        inc     ecx
        fild    dword [esp + 0x24]      ; cy
        call    scale
        fistp   dword [esp + 0x24]
        pop     edi
        pop     esi
.out:   call    tracevp2
        pop     ecx
        lea     eax, [ebp + RESUME_VP]  ; eax is free at the entry
        pop     ebp
        pop     ebx
        push    ebp                     ; the ten bytes replaced
        mov     ebp, esp
        sub     esp, 0x28
        mov     [esp + 4], esi
        jmp     eax

; st0 = a coordinate, ecx even for x, odd for y: st0 = it scaled from
; 640x480 to the picture.
scale:
        test    ecx, 1
        jnz     .y
        fmul    dword [ebx + width]
        fdiv    dword [ebx + k640]
        ret
.y:     fmul    dword [ebx + height]
        fdiv    dword [ebx + k480]
        ret

; [esp] = the return, [esp+4] this, [esp+8] the angle, [esp+0xc] near, [esp+0x10] far.
perspective:
        push    ebx
        push    ebp
        call    getbase
        mov     eax, [esp + 0x10]
        mov     [ebx + angle], eax
        call    picture
        jc      .go
        fld     dword [ebx + width]
        fdiv    dword [ebx + height]
        fmul    dword [ebx + k34]       ; W/H against 4:3
        fld     st0
        fcomp   dword [ebx + kone]
        fnstsw  ax
        sahf
        jbe     .same                   ; 4:3 or narrower: as it is
        fild    dword [esp + 0x10]      ; the angle
        fmul    dword [ebx + ktorad]    ; half of it, in radians
        fptan
        fstp    st0
        fmulp   st1, st0                ; tan * factor
        fld1
        fpatan
        fmul    dword [ebx + kfromrad]
        fistp   dword [esp + 0x10]
        jmp     .go
.same:  fstp    st0
.go:    call    tracefov
        lea     eax, [ebp + RESUME_PERSP]
        pop     ebp
        pop     ebx
        push    ebp                     ; the nine bytes replaced
        mov     ebp, esp
        sub     esp, 0x18
        mov     [esp], ebx
        jmp     eax

; ---- the trace ----------------------------------------------------------

; [esp+4] = the pushed ecx, then ebp, ebx, the return, this, the rect, cx, cy.
tracevp:
        cmp     dword [ebx + trace], 0
        je      .done
        pushad
        lea     edi, [ebx + line]
        lea     esi, [ebx + s_vp]
        call    scat
        mov     esi, [esp + 0x20 + 0x18]        ; the rect
        mov     ecx, 4
.r:     lodsd
        call    hex8
        loop    .r
        mov     eax, [esp + 0x20 + 0x1c]        ; cx
        call    hex8
        mov     eax, [esp + 0x20 + 0x20]        ; cy
        call    hex8
        mov     eax, [esp + 0x20 + 0x10]        ; the return, and the one above the wrapper's frame
        call    hex8
        mov     eax, [esp + 0x20 + 0x30]
        call    hex8
        call    report
        popad
.done:  ret

tracevp2:
        cmp     dword [ebx + trace], 0
        je      .done
        pushad
        lea     edi, [ebx + line]
        lea     esi, [ebx + s_vp2]
        call    scat
        mov     esi, [esp + 0x20 + 0x18]
        mov     ecx, 4
.r:     lodsd
        call    hex8
        loop    .r
        mov     eax, [esp + 0x20 + 0x1c]
        call    hex8
        mov     eax, [esp + 0x20 + 0x20]
        call    hex8
        call    report
        popad
.done:  ret

; [esp+4] = the pushed ebp, ebx, the return, this, the angle as it goes on.
tracefov:
        cmp     dword [ebx + trace], 0
        je      .done
        pushad
        lea     edi, [ebx + line]
        lea     esi, [ebx + s_fov]
        call    scat
        mov     eax, [ebx + angle]
        call    hex8
        mov     eax, [ebx + width]
        call    hex8
        mov     eax, [ebx + height]
        call    hex8
        mov     eax, [esp + 0x20 + 0x14]
        call    hex8
        call    report
        popad
.done:  ret

; eax -> 8 hex digits at edi, then a space.
hex8:
        push    ecx
        mov     ecx, 8
.d:     rol     eax, 4
        push    eax
        and     eax, 0xf
        mov     al, [ebx + digits + eax]
        stosb
        pop     eax
        loop    .d
        mov     al, ' '
        stosb
        pop     ecx
        ret

scat:   lodsb
        test    al, al
        jz      .done
        stosb
        jmp     scat
.done:  ret

; the line at [ebx+line], ending at edi, to OutputDebugStringA.
report:
        mov     byte [edi], 0
        cmp     dword [ebx + fn_ods], 0
        jne     .have
        lea     eax, [ebx + s_kernel32]
        push    eax
        call    [ebp + IAT_LOADLIB]
        lea     ecx, [ebx + s_ods]
        push    ecx
        push    eax
        call    [ebp + IAT_GETPROC]
        mov     [ebx + fn_ods], eax
.have:  lea     eax, [ebx + line]
        push    eax
        call    [ebx + fn_ods]
        ret

s_vp:       db 'sr2 vp ', 0
s_vp2:      db 'sr2 vp> ', 0
s_fov:      db 'sr2 fov ', 0
s_kernel32: db 'kernel32.dll', 0
s_d3d:      db 'MGameD3D.dll', 0
s_ods:      db 'OutputDebugStringA', 0
digits:     db '0123456789abcdef'
s_marker:   db 'GLTRACE', 0             ; the patcher finds the flag by this
trace:      dd 0
        align 4
fn_ods:     dd 0
angle:      dd 0
line:       times 128 db 0

k640:       dd 0x44200000               ; 640.0
k480:       dd 0x43F00000               ; 480.0
k34:        dd 0x3F400000               ; 0.75
kone:       dd 0x3F800000
ktorad:     dd 0x38490FDB               ; pi / 65536
kfromrad:   dd 0x46A2F983               ; 65536 / pi
        align 4
d3d:        dd 0                        ; MGameD3D's module handle, once found
width:      dd 0                        ; its size, as floats
height:     dd 0
rect:       dd 0, 0, 0, 0
