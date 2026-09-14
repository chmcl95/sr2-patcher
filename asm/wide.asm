; wide.asm - the exe's side of native widescreen: the picture's size from
; SR2.CFG. The field of view and the viewports are MGameGL's business
; (widegl.asm), the 2D MGameD3D's (wide2d.asm).
;
; Three entries, reached through the jump table at the top:
;
;   modecheck  replaces `mov eax, [esp+8]; cmp [MODE], eax` at the start of
;              the mode setter (0x4219f0): reads [Display] Resolution from
;              SR2.CFG beside the exe into want; a size that is in the table
;              and not one of the stock two is the wide size. Leaves ZF
;              clear (a re-init) when the wide size in force differs.
;   setsize    replaces the literal 640x480 / 800x600 stores after
;              `mov [MODE], eax`: mode 0 takes the wide size when there is
;              one, mode 1 stays 800x600 (1024x768 on the American build's
;              flag). Records what was applied.
;   screen     replaces `mov eax, [SETTINGS]; mov ecx, [eax+0x50]` in the
;              screen-change routine (0x451e8a): the stock calls the mode
;              setter there only for the race screens, and for the front
;              end's only on some of the ways in, so a size chosen in
;              Options waited for a race. Now a change in SR2.CFG has
;              the setter called with the front end's mode at the next
;              screen change, wherever it goes; unchanged, nothing.
; The size table follows the code: (width, height) pairs, a zero pair
; after the last; the patcher appends it. The annex is writable.

bits 32

%define MODE            0xF7F7F7F7      ; 0x4d5e54, the mode the exe last applied
%define WIDTH           0xEEEEEEEE      ; 0x4d5e1c, MGameD3D's init struct: the picture's size
%define HEIGHT          0xEFEFEFEF      ; 0x4d5e20
%define IAT_GETPPS      0xF8F8F8F8      ; 0x4951b8, GetPrivateProfileStringA
%define IAT_GETMODFN    0xF9F9F9F9      ; 0x495074, GetModuleFileNameA
%ifdef US
%define HIRES           0xFAFAFAFA      ; 0x4efa1c, the American build's 1024x768 flag
%endif
%define SETTINGS        0xFBFBFBFB      ; 0x50afdc, the game's settings block
%define SETTER          0xFCFCFCFC      ; 0x4219f0, the mode setter, cdecl(mode)
%define MAX_PATH        260

        jmp     near modecheck          ; +0
        jmp     near setsize            ; +5
        jmp     near screen             ; +10

; ebx = this blob, on return.
getbase:
        call    .here
.here:  pop     ebx
        sub     ebx, .here
        ret

; ---- the size ---------------------------------------------------------

modecheck:
        pushad
        call    getbase
        call    readcfg
        popad
        mov     eax, [esp + 0xc]        ; the mode asked for
        cmp     [MODE], eax
        jne     .out
        push    ebx
        push    ecx
        call    getbase
        mov     ecx, [ebx + want - $$]
        cmp     ecx, [ebx + applied - $$]
        jne     .force
        mov     ecx, [ebx + want + 4 - $$]
        cmp     ecx, [ebx + applied + 4 - $$]
        jne     .force
        pop     ecx
        pop     ebx
        cmp     [MODE], eax             ; equal: ZF set
        ret
.force: pop     ecx
        pop     ebx
        test    esp, esp                ; ZF clear
.out:   ret

; eax = the mode, as the exe stored it.
setsize:
        push    ebx
        push    ecx
        call    getbase
        mov     dword [WIDTH], 640
        mov     dword [HEIGHT], 480
        xor     ecx, ecx
        test    eax, eax
        jz      .wide
        mov     dword [WIDTH], 800
        mov     dword [HEIGHT], 600
%ifdef US
        cmp     dword [HIRES], 0
        je      .stock
        mov     dword [WIDTH], 1024
        mov     dword [HEIGHT], 768
%endif
        jmp     .stock
.wide:  mov     ecx, [ebx + want - $$]
        test    ecx, ecx
        jz      .stock
        mov     [WIDTH], ecx
        mov     ecx, [ebx + want + 4 - $$]
        mov     [HEIGHT], ecx
        mov     ecx, [ebx + want - $$]
.stock: mov     [ebx + applied - $$], ecx       ; the wide width in force, 0 for stock
        mov     ecx, [ebx + want + 4 - $$]
        cmp     dword [ebx + applied - $$], 0
        jne     .keep
        xor     ecx, ecx
.keep:  mov     [ebx + applied + 4 - $$], ecx
        pop     ecx
        pop     ebx
        ret

; A screen change: the setter, with the front end's mode, when the size
; in SR2.CFG is not the one in force. The eight bytes replaced follow.
screen:
        pushad
        call    getbase
        call    readcfg
        mov     ecx, [ebx + want - $$]
        cmp     ecx, [ebx + applied - $$]
        jne     .force
        mov     ecx, [ebx + want + 4 - $$]
        cmp     ecx, [ebx + applied + 4 - $$]
        je      .done
.force: mov     eax, [SETTINGS]
        push    dword [eax + 0x50]
        mov     edx, SETTER
        call    edx
        add     esp, 4
.done:  popad
        mov     eax, [SETTINGS]
        mov     ecx, [eax + 0x50]
        ret

; want = the [Display] Resolution in SR2.CFG when it is a wide entry of
; the table, else 0, 0. ebx = the blob.
readcfg:
        mov     dword [ebx + want - $$], 0
        mov     dword [ebx + want + 4 - $$], 0
        lea     edi, [ebx + path - $$]
        push    MAX_PATH
        push    edi
        push    0
        call    [IAT_GETMODFN]
        mov     esi, edi                ; the name after the last backslash
.scan:  mov     al, [edi]
        test    al, al
        jz      .name
        inc     edi
        cmp     al, '\'
        jne     .scan
        mov     esi, edi
        jmp     .scan
.name:  mov     dword [esi], 'SR2.'
        mov     dword [esi + 4], 'CFG'
        lea     eax, [ebx + path - $$]
        push    eax
        push    32
        lea     eax, [ebx + value - $$]
        push    eax
        lea     eax, [ebx + s_empty - $$]
        push    eax
        lea     eax, [ebx + s_key - $$]
        push    eax
        lea     eax, [ebx + s_section - $$]
        push    eax
        call    [IAT_GETPPS]
        lea     esi, [ebx + value - $$]
        call    number                  ; eax = the width, esi past it
        jc      .out
        mov     edi, eax
        cmp     byte [esi], 'x'
        je      .sep
        cmp     byte [esi], 'X'
        jne     .out
.sep:   inc     esi
        call    number                  ; eax = the height
        jc      .out
        lea     esi, [ebx + table - $$]
        add     esi, 16                 ; past the stock two
.entry: mov     ecx, [esi]
        test    ecx, ecx
        jz      .out
        cmp     ecx, edi
        jne     .next
        cmp     [esi + 4], eax
        jne     .next
        mov     [ebx + want - $$], edi
        mov     [ebx + want + 4 - $$], eax
        ret
.next:  add     esi, 8
        jmp     .entry
.out:   ret

; esi = digits: eax = their value, esi past them; carry when there are none.
number:
        xor     eax, eax
        xor     ecx, ecx
.digit: movzx   edx, byte [esi]
        sub     edx, '0'
        cmp     edx, 9
        ja      .done
        imul    eax, eax, 10
        add     eax, edx
        inc     esi
        inc     ecx
        jmp     .digit
.done:  test    ecx, ecx
        jz      .none
        clc
        ret
.none:  stc
        ret

s_section:  db 'Display', 0
s_key:      db 'Resolution', 0
s_empty:    db 0

        align 4
want:       dd 0, 0                     ; the wide size SR2.CFG asks for, or 0, 0
applied:    dd 0, 0                     ; the wide size in force, or 0, 0
value:      times 32 db 0
path:       times MAX_PATH db 0
        align 4
table:                                  ; the patcher's (width, height) pairs, 0, 0 after the last
