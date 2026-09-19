; hudlast.asm - the race's HUD drawn after the water, so the gauge's
; plate blends over the lake instead of blanking it.
;
; The race's frame is two draws. The state's own (0x4187b0): the scene
; pass - the ground, the cars - then the HUD (0x429d70, called at
; 0x418ab1 while the state's +0x3c says so). Then the frame object's
; (0x4280a0): with the game running (RUNNING), and on the European and
; American builds a flag (LATEFLAG) clear, a BeginScene, the root
; tree's draw (TREEDRAW at 0x4280f2) and an EndScene. The water is a
; node of that tree: a screen-space plane, z-tested so it shows only
; through the hole in the ground mesh, drawn after the HUD. The
; tachometer's plate is alpha-blended and writes its z, so under the
; plate the water fails the test and the plate shows what was there,
; the backdrop, a flat grey. Stock does the same.
;
; Three entries. `state`, in place of the HUD call at 0x418ab1: when
; the frame object's draw is going to run the tree - the flag clear and
; the game running - it draws nothing and notes the HUD as pending;
; otherwise it draws the HUD there as before, so a paused race or a
; state the tree is not drawn in keeps its HUD. `fade`, in place of the
; fade node's draw thunk (0x426930: `mov ecx, [renderer]; jmp
; 0x46bd80`, a node of the tree that draws the fade-in's and fade-out's
; quad over the whole picture, at z 0.00014 with the z-write on): with a
; HUD pending it draws the HUD first, so the fade stays over the HUD as
; it was and the HUD is not z-tested away under the quad. `late`, in
; place of the tree draw at 0x4280f2: the tree, then the HUD if it is
; still pending, the frames the fade node did not draw in. The HUD's
; draw is the full viewport through the exe's own wrapper as the
; state's draw sets it in split screen, the HUD, and the reset the
; state's draw made after it (HUDRESET, colour key and blending off).
; The pending note, not the state's own HUD flag, so a state of another
; kind never gets the race's HUD. Everything called keeps the callee's
; registers; esi is the frame object at the late site.

bits 32

%define HUDDRAW         0xC6C6C6C6      ; placeholders, EXE_MAGICS
%define TREEDRAW        0xC7C7C7C7
%define HUDRESET        0xC8C8C8C8
%define LATEFLAG        0xCCCCCCCC      ; a global that, set, skips the tree; 0 on a build without one
%define FADEDRAW        0xCDCDCDCD
%define RUNNING         0xF3F3F3F3
%define RENDERER        0xC3C3C3C3
%define SETVIEWPORT     0xC4C4C4C4
%define VPRECTS         0xC5C5C5C5

        jmp     near state              ; +0
        jmp     near late               ; +5
        jmp     near fade               ; +10

state:  call    .here
.here:  pop     eax
        sub     eax, .here              ; eax = this blob
        mov     byte [eax + pending], 0
        mov     ecx, LATEFLAG
        test    ecx, ecx
        jz      .running
        cmp     dword [ecx], 0
        jne     .now
.running:
        cmp     dword [RUNNING], 0
        je      .now
        mov     byte [eax + pending], 1
        ret                             ; the tree runs: the HUD after it
.now:   mov     eax, HUDDRAW
        jmp     eax

fade:   call    hud
        mov     ecx, [RENDERER]
        mov     eax, FADEDRAW
        jmp     eax

late:   mov     eax, TREEDRAW
        call    eax
        jmp     hud

; The HUD, if pending, and the note cleared.
hud:    call    .here
.here:  pop     eax
        sub     eax, .here
        cmp     byte [eax + pending], 0
        je      .out
        mov     byte [eax + pending], 0
        mov     ecx, [RENDERER]
        push    0
        push    VPRECTS                 ; the full rect, its centre the middle
        mov     eax, SETVIEWPORT
        call    eax
        mov     eax, HUDDRAW
        call    eax
        mov     ecx, [RENDERER]
        mov     eax, HUDRESET
        call    eax
.out:   ret

pending: db 0                           ; the state's HUD skipped this frame, to draw after the tree
