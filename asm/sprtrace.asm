; sprtrace.asm - a diagnostic in MGameGL, applied by name: the sprite
; draw and the model draw report what they are given. Written for the
; cars' lamp housings, which sit off the car; its first run showed
; them not to be sprites - every sprite of a race is drawn under the
; camera's matrix - and an opponent's lamps to be models placed where
; lamps belong, so what is left to look at is the player car's own
; sixteen model draws and the lamp models' geometry.
;
; The sprite draw (+0x70, 0x1000e710; this, &def, &point) builds a
; camera-facing quad about the point transformed by the model-view
; matrix at [0x10012c68] - or the point as it is when bit 8 of the
; def's +0xc is set - into the vertex buffer at [0x10012c10], and
; returns 1 when the point is outside the near and far planes, else
; the buffer's next slot. The
; model draw (+0x64, 0x1000db40; this, &model) sets the device's world
; transform to that matrix and draws the model. Each call reports on
; OutputDebugStringA, in hex, floats as they are:
;
;   sr2 sp def flags px py pz ps mx my mz r qx qy qz
;     the def, its flags, the point and its scale, the matrix's
;     translation, the draw's result, and the first vertex of the quad
;     it built (zeros when r is 1, the point culled);
;   sr2 md model mx my mz m00 m11 m22
;     the model, the matrix's translation and its diagonal.
;
; The first LINES calls of each kind. Both entries replace the
; method's first bytes, do them themselves and continue after them;
; the sprite draw is called as a routine with its arguments pushed
; again so the quad can be read after it.

bits 32

%define MAGIC_SELFRVA   0xE7E7E7E7      ; this blob's RVA, filled at apply time
%define MODELVIEW       0x12c68         ; RVAs in MGameGL.dll: the model-view matrix's address
%define VBUF            0x12c10         ; the sprite quad written next, 0x80 a quad
%define RESUME_SPRITE   0xe717          ; after the seven bytes replaced
%define RESUME_MODEL    0xdb49          ; after the nine
%define IAT_LOADLIB     0x100ec         ; MGameGL's import slots
%define IAT_GETPROC     0x10088
%define LINES           20000

        jmp     near sprite             ; +0
        jmp     near model              ; +5

; ebx = this blob and ebp = the image base, on return.
getbase:
        call    .here
.here:  pop     ebx
        sub     ebx, .here
        mov     ebp, ebx
        sub     ebp, MAGIC_SELFRVA
        ret

; [esp] = the return, [esp+4] this, [esp+8] &def, [esp+0xc] &point.
sprite:
        push    ebx
        push    ebp
        call    getbase
        push    dword [esp + 0x14]      ; the point
        push    dword [esp + 0x14]      ; the def
        push    dword [esp + 0x14]      ; this
        lea     edx, [ebp + RESUME_SPRITE]
        call    .body                   ; the draw, its `ret 0xc` taking the three
        call    tracesp
        pop     ebp
        pop     ebx
        ret     0xc
.body:  sub     esp, 0xc                ; the seven bytes replaced
        mov     eax, [esp + 0x14]
        jmp     edx

; [esp] = the return, [esp+4] this, [esp+8] &model.
model:
        push    ebx
        push    ebp
        call    getbase
        call    tracemd
        lea     eax, [ebp + RESUME_MODEL]
        pop     ebp
        pop     ebx
        push    ebp                     ; the nine bytes replaced
        mov     ebp, esp
        sub     esp, 8
        add     esp, -8
        jmp     eax

; eax = the draw's result; [esp+4] = the pushed ebp, ebx, the return, this, def, point.
tracesp:
        cmp     dword [ebx + spleft], 0
        je      .done
        dec     dword [ebx + spleft]
        pushad
        mov     [ebx + result], eax
        lea     edi, [ebx + line]
        lea     esi, [ebx + s_sp]
        call    scat
        mov     eax, [esp + 0x20 + 0x14]        ; the def and its flags
        call    hex8
        mov     esi, eax
        mov     eax, [esi + 0xc]
        call    hex8
        mov     esi, [esp + 0x20 + 0x18]        ; the point and its scale
        mov     ecx, 4
        call    floats
        mov     esi, [ebp + MODELVIEW]          ; the matrix's translation
        add     esi, 0x30
        mov     ecx, 3
        call    floats
        mov     eax, [ebx + result]
        call    hex8
        cmp     dword [ebx + result], 1
        je      .none
        mov     esi, [ebp + VBUF]               ; the quad just built, 0x80 back
        sub     esi, 0x80
        mov     ecx, 3
        call    floats
        jmp     .report
.none:  mov     ecx, 3
.zero:  xor     eax, eax
        call    hex8
        loop    .zero
.report:
        call    report
        popad
.done:  ret

; [esp+4] = the pushed ebp, ebx, the return, this, model.
tracemd:
        cmp     dword [ebx + mdleft], 0
        je      .done
        dec     dword [ebx + mdleft]
        pushad
        lea     edi, [ebx + line]
        lea     esi, [ebx + s_md]
        call    scat
        mov     eax, [esp + 0x20 + 0x14]
        call    hex8
        mov     esi, [ebp + MODELVIEW]
        add     esi, 0x30
        mov     ecx, 3
        call    floats
        mov     esi, [ebp + MODELVIEW]
        mov     eax, [esi]
        call    hex8
        mov     eax, [esi + 0x14]
        call    hex8
        mov     eax, [esi + 0x28]
        call    hex8
        call    report
        popad
.done:  ret

; ecx dwords at esi -> hex at edi. esi advanced.
floats:
        lodsd
        call    hex8
        loop    floats
        ret

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

s_sp:       db 'sr2 sp ', 0
s_md:       db 'sr2 md ', 0
s_kernel32: db 'kernel32.dll', 0
s_ods:      db 'OutputDebugStringA', 0
digits:     db '0123456789abcdef'
        align 4
fn_ods:     dd 0
result:     dd 0
spleft:     dd LINES
mdleft:     dd LINES
line:       times 256 db 0
