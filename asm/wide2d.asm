; wide2d.asm - the 2D drawn in 640x480 terms, scaled to the back buffer,
; and the device's viewport with it.
;
; Every screen DLL, MainMode and the exe draw their menus, text and HUD
; as pre-transformed geometry, FVF 0x1c4, in 640x480 pixels whatever
; the buffer's size, through MGameD3D's draws: quads (vtable +0xb4,
; 0x10005120), triangles (+0xb0, 0x100050d0), triangle lists plain
; (+0xb8, 0x10004fe0) and indexed (+0xc4, 0x10005170), strips (+0xbc,
; 0x10005030) and fans (+0xc0, 0x10005080). MGameGL's 3D is
; untransformed (FVF 0x1e2 and 0x112, the device transforms it), so
; every draw with the FVF the game set (0x1001121c) at 0x1c4 is 2D.
; With that FVF and a buffer that is not 640x480, the vertices are
; scaled into a copy here and the copy is drawn: uniformly by height,
; centred, so the 4:3 layout keeps its shape in the middle of a wide
; picture; a quad that spans the whole width (a fade, a background) is
; stretched across instead; a tile at one edge is drawn out to the
; picture's edge (see extend). A list longer than the copy holds goes
; as it is. The first two entries replace the six-byte `mov edx,
; [0x10011220]` each draw begins with, the next four the list,
; indexed-list, strip and fan draws' first ten bytes, and each
; continues after them.
;
; Vertex: x, y, z, rhw, diffuse, specular, u, v - 32 bytes.
;
; The device's viewport setter (vtable +0x158 of the second interface,
; 0x10006040: this, &{left, top, right, bottom, four fractions}) is the
; seventh entry: the exe sets the countdown's viewport on the device
; itself from its own table (0x5b24f0: 640x480, the split halves, the
; 800x600 set), a path MGameGL's SetViewport never sees, so a rect no
; wider than 640 and no taller than 480 while the picture is wider is
; scaled to the picture through a copy here; MGameGL's, in real pixels,
; pass.
;
; With `trace` set (the d3dtrace diagnostic) every draw through the six
; draw entries reports itself on OutputDebugStringA, the first 60000:
; "sr2 d e fvf count ret x0 y0 z0", e the entry (q, t, l, i, s, f), ret
; the draw's return address (the loaddll lines say whose), the first
; vertex in hex before any scaling.

bits 32

%define MAGIC_SELFRVA   0xE7E7E7E7      ; this blob's RVA, filled at apply time
%define FVF             0x1121c         ; RVAs in MGameD3D.dll
%define FLAGS           0x11220         ; the draw flags the replaced mov loads
%define WIDTH           0x123fc         ; the back buffer's size
%define HEIGHT          0x12400
%define RESUME_QUAD     0x5126          ; after the bytes replaced
%define RESUME_TRI      0x50d6
%define RESUME_LIST     0x4fea
%define RESUME_INDEXED  0x517a
%define RESUME_STRIP    0x503a
%define RESUME_FAN      0x508a
%define STRIP           0x10000000      ; flags the count of a strip on the stack
%define FAN             0x08000000      ; and of a fan
%define TRIANGLES       0x12764         ; the count the list draws' second instruction loads
%define WRAP            0x11240         ; the texture addressing as last set through +0xf8: nonzero wraps
%define SETWRAP         0xf8            ; that method, in the vtable
%define TILE            0x43000000      ; 128.0: a clamped quad no wider than this is a tile
%define LIST            0x40000000      ; flags the count of a list on the stack
%define INDEXED         0x20000000      ; and of an indexed one
%define CAPACITY        2048            ; vertices the copy holds
%define RESUME_VIEWPORT 0x6049          ; the viewport setter after its first nine bytes
%define IAT_LOADLIB     0xf114          ; MGameD3D's import slots
%define IAT_GETPROC     0xf0ac

        jmp     near quad               ; +0
        jmp     near tri                ; +5
        jmp     near list               ; +10
        jmp     near indexed            ; +15
        jmp     near strip              ; +20
        jmp     near fan                ; +25
        jmp     near viewport           ; +30

quad:   push    4
        jmp     draw
tri:    push    3
        jmp     draw
list:   push    dword [esp + 0xc]       ; the count, the third argument
        or      dword [esp], LIST
        jmp     draw
indexed:
        push    dword [esp + 0xc]       ; the vertex count, the third argument
        or      dword [esp], LIST | INDEXED
        jmp     draw
strip:  push    dword [esp + 0xc]       ; the count, the third argument
        or      dword [esp], LIST | STRIP
        jmp     draw
fan:    push    dword [esp + 0xc]
        or      dword [esp], LIST | FAN

; [esp] = the vertex count, [esp+4] the draw's return address, [esp+8]
; its `this`, [esp+0xc] the vertices. eax, ecx and edx are free at both
; sites. ebx = this blob, ebp = the image base.
draw:
        push    ebp
        push    ebx
        call    getbase
        call    tracedraw
        cmp     dword [ebp + FVF], 0x1c4
        jne     .out
        mov     ecx, [esp + 8]          ; the count
        and     ecx, ~(LIST | INDEXED | STRIP | FAN)
        cmp     ecx, CAPACITY
        ja      .out
        cmp     dword [ebp + WIDTH], 640
        jne     .scale
        cmp     dword [ebp + HEIGHT], 480
        je      .out
.scale: push    esi
        push    edi
        mov     esi, [esp + 0x1c]       ; the vertices
        lea     edi, [ebx + copy]
        push    ecx
        shl     ecx, 3
        rep movsd                       ; the copy
        pop     ecx
        lea     edi, [ebx + copy]
        mov     esi, edi
        fild    dword [ebp + HEIGHT]
        fdiv    dword [ebx + k480]      ; the scale, by height
        fild    dword [ebp + WIDTH]
        fld     st1
        fmul    dword [ebx + k640]
        fsubp   st1, st0
        fmul    dword [ebx + khalf]     ; the bar: (W - 640 * scale) / 2
        ; st0 = the bar, st1 = the scale
        fst     dword [ebx + bar]
        fld     st1
        fstp    dword [ebx + sc]
        push    ecx                     ; bit 16 set for an x at the left edge, 17 the right
.span:  fld     dword [esi]
        fcomp   dword [ebx + khalf]
        fnstsw  ax
        sahf
        jae     .right
        or      dword [esp], 0x10000
.right: fld     dword [esi]
        fcomp   dword [ebx + kalmost]
        fnstsw  ax
        sahf
        jb      .next
        or      dword [esp], 0x20000
.next:  add     esi, 32
        dec     ecx
        jnz     .span
        pop     ecx
        test    ecx, 0x10000
        jz      .centred
        test    ecx, 0x20000
        jz      .centred
        and     ecx, 0xffff             ; spans the width: x * W / 640, y * scale
        fstp    st0                     ; the bar goes
        fild    dword [ebp + WIDTH]
        fdiv    dword [ebx + k640]      ; st0 = the x scale, st1 = the y scale
.stretch:
        fld     dword [edi]
        fmul    st0, st1
        fstp    dword [edi]
        fld     dword [edi + 4]
        fmul    st0, st2
        fstp    dword [edi + 4]
        add     edi, 32
        dec     ecx
        jnz     .stretch
        jmp     .done
.centred:
        mov     [ebx + edges], ecx
        and     ecx, 0xffff             ; x * scale + the bar, y * scale
        push    ecx
.c:     fld     dword [edi]
        fmul    st0, st2
        fadd    st0, st1
        fstp    dword [edi]
        fld     dword [edi + 4]
        fmul    st0, st2
        fstp    dword [edi + 4]
        add     edi, 32
        dec     ecx
        jnz     .c
        pop     ecx
        call    extend
.done:  fstp    st0
        fstp    st0
        lea     eax, [ebx + copy]
        mov     [esp + 0x1c], eax       ; the draw takes the copy
        pop     edi
        pop     esi
.out:   mov     eax, [esp + 8]          ; the count
        test    eax, LIST
        jnz     .list
        mov     edx, [ebp + FLAGS]      ; the six bytes replaced
        cmp     eax, 4
        je      .quad
        add     ebp, RESUME_TRI
        jmp     .go
.quad:  add     ebp, RESUME_QUAD
        jmp     .go
.list:  mov     ecx, [ebp + TRIANGLES]  ; the ten bytes replaced: mov eax, [esp+0xc] (the indexed draw's [esp+0x14]); mov ecx, [triangles]
        test    eax, INDEXED
        jnz     .indexed
        test    eax, STRIP
        jnz     .strip
        test    eax, FAN
        jnz     .fan
        mov     eax, [esp + 0x18]
        add     ebp, RESUME_LIST
        jmp     .go
.strip: mov     eax, [esp + 0x18]
        add     ebp, RESUME_STRIP
        jmp     .go
.fan:   mov     eax, [esp + 0x18]
        add     ebp, RESUME_FAN
        jmp     .go
.indexed:
        mov     eax, [esp + 0x20]
        add     ebp, RESUME_INDEXED
.go:    mov     [esp + 8], ebp          ; the resume address over the count
        pop     ebx
        pop     ebp
        ret

; ebx = this blob and ebp = the image base, on return.
getbase:
        call    .here
.here:  pop     ebx
        sub     ebx, .here
        mov     ebp, ebx
        sub     ebp, MAGIC_SELFRVA
        ret

; [esp] = the return, [esp+4] this, [esp+8] the rect and fractions.
viewport:
        push    ebx
        push    ebp
        call    getbase
        cmp     dword [ebp + WIDTH], 640
        jbe     .out                    ; 640 wide or less: nothing to scale to
        mov     eax, [esp + 0x10]       ; the rect
        cmp     dword [eax + 8], 640
        jg      .out
        cmp     dword [eax + 0xc], 480
        jg      .out
        push    esi
        push    edi
        push    ecx
        mov     esi, eax
        lea     edi, [ebx + vpcopy]
        mov     ecx, 8
        rep movsd                       ; the copy, its fractions as they are
        lea     edi, [ebx + vpcopy]
        xor     ecx, ecx
.side:  mov     eax, [edi + ecx * 4]
        test    ecx, 1
        jnz     .y
        imul    eax, [ebp + WIDTH]
        push    edx
        cdq
        push    ecx
        mov     ecx, 640
        idiv    ecx
        pop     ecx
        pop     edx
        jmp     .put
.y:     imul    eax, [ebp + HEIGHT]
        push    edx
        cdq
        push    ecx
        mov     ecx, 480
        idiv    ecx
        pop     ecx
        pop     edx
.put:   mov     [edi + ecx * 4], eax
        inc     ecx
        cmp     ecx, 4
        jb      .side
        mov     [esp + 0x1c], edi       ; the rect argument, on the stack
        pop     ecx
        pop     edi
        pop     esi
.out:   lea     eax, [ebp + RESUME_VIEWPORT]
        pop     ebp
        pop     ebx
        sub     esp, 8                  ; the nine bytes replaced
        push    esi
        mov     esi, [esp + 0x14]
        push    edi
        jmp     eax

; ---- the trace ----------------------------------------------------------

; [esp+4] = the pushed ebx, then ebp, the count with its flags, the
; return, this, the vertices.
tracedraw:
        cmp     dword [ebx + trace], 0
        je      .done
        cmp     dword [ebx + left], 0
        je      .done
        dec     dword [ebx + left]
        pushad
        lea     edi, [ebx + line]
        lea     esi, [ebx + s_d]
        call    scat
        mov     eax, [esp + 0x20 + 0xc]         ; the entry, from the count's flags
        mov     ecx, eax
        and     ecx, 0xffff
        mov     dl, 'q'
        cmp     ecx, 4
        je      .kind
        mov     dl, 't'
        test    eax, LIST
        jz      .kind
        mov     dl, 'l'
        test    eax, INDEXED
        jz      .notidx
        mov     dl, 'i'
.notidx:
        test    eax, STRIP
        jz      .notstrip
        mov     dl, 's'
.notstrip:
        test    eax, FAN
        jz      .kind
        mov     dl, 'f'
.kind:  mov     al, dl
        stosb
        mov     al, ' '
        stosb
        mov     eax, [ebp + FVF]
        call    hex8
        mov     eax, ecx
        call    hex8
        mov     eax, [esp + 0x20 + 0x10]        ; the return
        call    hex8
        mov     esi, [esp + 0x20 + 0x18]        ; the vertices
        mov     eax, [esi]
        call    hex8
        mov     eax, [esi + 4]
        call    hex8
        mov     eax, [esi + 8]
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

s_d:        db 'sr2 d ', 0
s_kernel32: db 'kernel32.dll', 0
s_ods:      db 'OutputDebugStringA', 0
digits:     db '0123456789abcdef'
s_marker:   db 'D3DTRACE', 0            ; the patcher finds the flag by this
trace:      dd 0
        align 4
fn_ods:     dd 0
left:       dd 60000                    ; lines still to report
vpcopy:     times 8 dd 0                ; the viewport setter's rect and fractions, scaled
line:       times 128 db 0

; A quad or triangle with a vertex at or past one edge of the 640 - the
; left edge of a tiled background, say - is drawn out to the picture's
; edge on that side, its texture coordinate shifted at the same rate as
; across the rest of it for the distance that vertex moves, so a tiling
; texture goes on, scrolling or not. Only a tile-sized quad, no more
; than 128 by 128: a wider or taller one at the edge is a picture or a
; strip of one - the mode select's photo - and keeps its 4:3 place. A clamped tile has wrap switched on
; for its draw through the device's own method; its cache then has the
; next clamp request applied again. ecx = the count, edges = the span
; bits; the copy at [ebx+copy], the originals at [esp+0x20] and the
; device at [esp+0x1c] (under the return here).
extend:
        mov     eax, [ebx + edges]
        and     eax, 0x30000
        jz      .none
        cmp     eax, 0x30000
        je      .none                   ; both edges: stretched already
        cmp     ecx, 4
        ja      .none                   ; a list is text, not a background
        push    esi
        push    edi
        mov     esi, [esp + 0x28]       ; the originals
        ; the leftmost and rightmost vertex, their x and u; the top and bottom
        fld     dword [esi]
        fst     dword [ebx + xmin]
        fstp    dword [ebx + xmax]
        fld     dword [esi + 4]
        fst     dword [ebx + ymin]
        fstp    dword [ebx + ymax]
        mov     eax, [esi + 24]
        mov     [ebx + umin], eax
        mov     [ebx + umax], eax
        push    ecx
.scan:  fld     dword [esi + 4]
        fcomp   dword [ebx + ymin]
        fnstsw  ax
        sahf
        jae     .nottop
        mov     eax, [esi + 4]
        mov     [ebx + ymin], eax
.nottop:
        fld     dword [esi + 4]
        fcomp   dword [ebx + ymax]
        fnstsw  ax
        sahf
        jbe     .notbottom
        mov     eax, [esi + 4]
        mov     [ebx + ymax], eax
.notbottom:
        fld     dword [esi]
        fcomp   dword [ebx + xmin]
        fnstsw  ax
        sahf
        jae     .notmin
        mov     eax, [esi]
        mov     [ebx + xmin], eax
        mov     eax, [esi + 24]
        mov     [ebx + umin], eax
.notmin:
        fld     dword [esi]
        fcomp   dword [ebx + xmax]
        fnstsw  ax
        sahf
        jbe     .notmax
        mov     eax, [esi]
        mov     [ebx + xmax], eax
        mov     eax, [esi + 24]
        mov     [ebx + umax], eax
.notmax:
        add     esi, 32
        dec     ecx
        jnz     .scan
        pop     ecx
        ; shift = (umax - umin) * (bar / scale) / (xmax - xmin)
        fld     dword [ebx + xmax]
        fsub    dword [ebx + xmin]      ; dx
        fld     st0
        fcomp   dword [ebx + khalf]
        fnstsw  ax
        sahf
        jb      .thin                   ; no width to speak of
        fld     st0
        fcomp   dword [ebx + ktile]
        fnstsw  ax
        sahf
        ja      .thin                   ; wider than a tile: a picture, left alone
        fld     dword [ebx + ymax]
        fsub    dword [ebx + ymin]
        fcomp   dword [ebx + ktile]
        fnstsw  ax
        sahf
        ja      .thin                   ; taller than a tile: a strip of one, likewise
        cmp     dword [ebp + WRAP], 0
        jne     .shift                  ; wrapping already
        push    ecx                     ; a clamped tile: wrap for this draw
        push    edx
        mov     ecx, [esp + 0x24 + 8]   ; the device
        mov     edx, [ecx]
        push    1
        push    ecx
        call    [edx + SETWRAP]
        pop     edx
        pop     ecx
.shift:
        fld     dword [ebx + umax]
        fsub    dword [ebx + umin]      ; du
        fdivrp  st1, st0                ; du / dx, the rate
        fstp    dword [ebx + rate]
        fld     dword [ebx + bar]
        fdiv    dword [ebx + sc]
        fstp    dword [ebx + barpx]     ; the bar in 640 pixels
        jmp     .apply
.thin:  fstp    st0
        jmp     .out
.apply: mov     esi, [esp + 0x28]       ; the originals
        lea     edi, [ebx + copy]
.v:     fld     dword [esi]
        fcomp   dword [ebx + khalf]
        fnstsw  ax
        sahf
        jae     .notleft
        mov     dword [edi], 0          ; to the left edge: moved by x + bar
        fld     dword [esi]
        fadd    dword [ebx + barpx]
        fmul    dword [ebx + rate]
        fsubr   dword [edi + 24]
        fstp    dword [edi + 24]
        jmp     .next
.notleft:
        fld     dword [esi]
        fcomp   dword [ebx + kalmost]
        fnstsw  ax
        sahf
        jb      .next
        fild    dword [ebp + WIDTH]     ; to the right edge: moved by 640 + bar - x
        fstp    dword [edi]
        fld     dword [ebx + k640]
        fadd    dword [ebx + barpx]
        fsub    dword [esi]
        fmul    dword [ebx + rate]
        fadd    dword [edi + 24]
        fstp    dword [edi + 24]
.next:  add     esi, 32
        add     edi, 32
        dec     ecx
        jnz     .v
.out:   pop     edi
        pop     esi
.none:  ret

ktile:      dd TILE
k640:       dd 0x44200000               ; 640.0
k480:       dd 0x43F00000               ; 480.0
khalf:      dd 0x3F000000               ; 0.5
kalmost:    dd 0x441FC000               ; 639.0
        align 4
bar:        dd 0                        ; the scaling in force: the bar, the scale
sc:         dd 0
edges:      dd 0                        ; the span bits of the vertices in hand
xmin:       dd 0                        ; extend's leftmost and rightmost x and their u, top and bottom y
ymin:       dd 0
ymax:       dd 0
xmax:       dd 0
umin:       dd 0
umax:       dd 0
rate:       dd 0                        ; du / dx across the quad, and the bar in 640 pixels
barpx:      dd 0
        align 16
copy:       times CAPACITY * 32 db 0
