; padmenu.asm - the pad on the multiplayer screens, straight from MGInput's
; annex.
;
; The multiplayer controller polls the pad every frame at 0x43f8e0: the
; input wrapper's button mask packed into a level word, an edge word
; from it and the previous level, and the three stored (0x43f94f,
; 0x4ef7c4 / 0x4ef7e4 / 0x4ef7d4). Its screens test the edge word for
; up, down, left, right (bits 0-3), confirm (4), cancel (5) and Enter
; (15), and the keyboard's own word (0x4d5e08, from WM_KEYDOWN) for the
; same and for TAB (bit 13), which alone opens the team room's MENU row
; (NOTES.md, *The menus' directions*). On these screens the wrapper's
; mask carries nothing from an XInput pad, so this replaces the six-byte
; store of the level word with a call that asks the annex for side 0's
; D-pad, left stick, A, B, Start and Back through the poll it publishes
; (PADPOLL, null without the xinput patch), ORs the first five into the
; level as those bits, makes the edge and the three stores itself, and
; on a press of Back sets TAB in the keyboard word, which the tasks clear
; each frame. It returns past the two stores that followed the site.
;
; Placeholders the patcher fills: the level, edge and previous words
; (PADLEVEL, PADEDGE, PADPREV), the keyboard word (MENUKEYS), the poll's
; slot (PADPOLL).

bits 32

%define PADLEVEL    0xB1B1B1B1          ; placeholders, EXE_MAGICS: the poll's level word
%define PADEDGE     0xCECECECE          ; its edge word
%define PADPREV     0xB2B2B2B2          ; its previous level
%define MENUKEYS    0xCFCFCFCF          ; the keyboard's menu word
%define PADPOLL     0xDFDFDFDF          ; the exe slot holding the annex's page poll
%define SOURCE      0x300               ; the annex's source ids: side 0's inputs
%define TAB         0x2000              ; bit 13
%define SKIP        13                  ; the two stores after the site, returned past
%define INPUTS      12                  ; the inputs asked for

; ecx = the level packed so far, edx = the previous level
entry:  add     dword [esp], SKIP
        push    eax
        push    esi
        push    edi
        push    ebp
        call    .here
.here:  pop     ebp
        sub     ebp, .here              ; ebp = this blob
        cmp     dword [PADPOLL], 0
        je      .store
        push    edx
        push    ecx
        sub     esp, 8                  ; [esp] a value, [esp + 4] its range
        xor     esi, esi                ; the annex's bits
        xor     edi, edi
.input: lea     eax, [esp + 4]
        push    eax                     ; &range
        lea     eax, [esp + 4]
        push    eax                     ; &value
        movzx   eax, byte [ebp + inputs + edi]
        add     eax, SOURCE
        push    eax
        call    [PADPOLL]               ; stdcall (source, &value, &range)
        mov     eax, [esp]
        add     eax, eax
        cmp     eax, [esp + 4]
        jbe     .next                   ; down: the value past half its range
        or      si, [ebp + masks + edi * 2]
.next:  inc     edi
        cmp     edi, INPUTS
        jb      .input
        add     esp, 8
        pop     ecx
        pop     edx
        mov     eax, esi
        and     esi, ~TAB
        or      ecx, esi
        and     eax, TAB                ; Back: a press is TAB in the keyboard word
        shr     eax, 13                 ; al = down now
        mov     ah, [ebp + back]
        mov     [ebp + back], al        ; ah was down
        test    ah, ah
        jnz     .store
        test    al, al
        jz      .store
        or      dword [MENUKEYS], TAB
.store: not     edx
        and     edx, ecx                ; the edge: down now, not before
        mov     [PADLEVEL], ecx
        mov     [PADEDGE], edx
        mov     [PADPREV], ecx
        pop     ebp
        pop     edi
        pop     esi
        pop     eax
        ret

; the inputs asked for, XINPUT_GAMEPAD order as the annex numbers them,
; and the bit each sets
inputs: db 0, 1, 2, 3, 20, 21, 18, 19, 12, 13, 4, 5
masks:  dw 1, 2, 4, 8, 1, 2, 4, 8, 0x10, 0x20, 0x8000, TAB
back:   db 0
        align 4
