; padmenu.asm - the pad's Back button as TAB on the multiplayer screens.
;
; The team room's MENU row is a task the slot list spawns on TAB, and the
; list tests TAB in the keyboard's menu word only (0x4366c9, bit 13 of
; 0x4d5e08), which WM_KEYDOWN fills; the pad's word (0x4edcb4) never
; carries bit 13, so a pad cannot reach the row (NOTES.md, *The menus'
; directions*). The multiplayer controller polls the pad every frame at
; 0x43f8e0 before its screen runs its tasks; this replaces the six-byte
; store of the frame's edge word there (0x43f955, `mov [0x4ef7e4], edx`)
; with a call that makes the store, asks MGInput's annex for side 0's
; Back through the poll it publishes (PADPOLL, null without the xinput
; patch), and on its press sets bit 13 in the keyboard word, which the
; list takes as TAB and the row as back. The tasks clear the word each
; frame.
;
; Placeholders the patcher fills: the edge word (PADEDGE), the keyboard
; word (MENUKEYS), the poll's slot (PADPOLL).

bits 32

%define PADEDGE     0xCECECECE          ; placeholders, EXE_MAGICS: the poll's edge word
%define MENUKEYS    0xCFCFCFCF          ; the keyboard's menu word
%define PADPOLL     0xDFDFDFDF          ; the exe slot holding the annex's page poll
%define SRC_BACK    0x305               ; the annex's source id: side 0, Back
%define TAB         0x2000              ; bit 13

entry:  mov     [PADEDGE], edx          ; the six bytes replaced
        push    eax
        push    ecx
        push    edx
        push    ebp
        call    .here
.here:  pop     ebp
        sub     ebp, .here              ; ebp = this blob
        mov     eax, [PADPOLL]
        test    eax, eax
        jz      .done
        sub     esp, 8                  ; [esp] the value, [esp + 4] its range
        lea     ecx, [esp + 4]
        push    ecx                     ; &range
        lea     ecx, [esp + 4]
        push    ecx                     ; &value
        push    SRC_BACK
        call    eax                     ; stdcall (source, &value, &range)
        pop     eax                     ; the value
        pop     ecx
        test    eax, eax
        setnz   al                      ; al = down now
        mov     cl, [ebp + prev]
        mov     [ebp + prev], al
        test    cl, cl
        jnz     .done                   ; was down: no press
        test    al, al
        jz      .done
        or      dword [MENUKEYS], TAB
.done:  pop     ebp
        pop     edx
        pop     ecx
        pop     eax
        ret

prev:   db 0
        align 4
