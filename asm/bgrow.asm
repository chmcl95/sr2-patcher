; bgrow.asm - a .bg picture into the back buffer, at either depth and size.
;
; The full-screen pictures (title, loading, game over, the course cards)
; are 16-bit 565 files the game copies straight into a locked back
; buffer, one row at a time, with rep movsd (0x415271). That is right for
; the 16-bit 640x480 mode it was written for. In a window on a 32-bit
; desktop the back buffer is 32-bit, and the same copy puts two pixels'
; worth of bytes into each pixel: the picture at half width, garbage.
; With a wide picture size the buffer is larger than the picture, which
; would sit in its top-left corner.
;
; This replaces the twenty-byte row copy. It reads the locked surface's
; description - the game keeps it at 0x4e6878 - and:
;
; - when the surface is the picture's size, copies the row as before, or
;   expands each 565 pixel to XRGB8888 when the surface is 32-bit,
;   replicating the high bits into the low ones as the display would;
; - when it is not, draws the whole picture on the first row, scaled to
;   fit the surface with its aspect kept (nearest pixel) and centred,
;   with a bar each side carrying the picture behind it: the whole
;   picture stretched to the surface's width, nearest pixel, the drawn
;   one covering the middle, so each bar shows the sliver beyond the
;   drawn edge spread across it. In Title.dll's build (-DTITLE) that is
;   the picture, blurred across first - each column of the sliver the
;   box mean of the columns a sixty-fourth of the width either side, so
;   it comes out as a motion blur - and at DIM of its brightness. The
;   exe's build draws the loading, game-over and course screens, which
;   are pictures on a plain background: there each bar is the row's own
;   edge pixel throughout, and nothing more. Does nothing on the rows
;   after.
;
; Registers as the copy left them: eax (the row's byte count), ebx (source
; row) and edx (destination row) untouched; ecx, esi, edi and ebp are
; scratch there, the game reloads them after. The picture's height is on
; the stack: the loop's object, whose +4 is the picture, height at +8.
;
; Title.dll has its own copy of the same loop (0x100014ba, 22 bytes, with
; the source advanced at the end), its lock description on the stack and
; the rows still to copy - the height, on the first - at [esp+0x10]:
; assembled with -DTITLE it reads those, tells the sizes apart by width
; alone, and advances ebx. The TITLE
; variant holds no absolute address; the other has the one placeholder
; the patcher fills.

bits 32

%define SCRATCH     512                 ; columns a blurred sliver may hold, on the stack
%define DIM         0x66                ; the bars at this much of the picture's brightness, eight bits of
                                        ; fraction: two fifths, so they sit behind it


%ifdef TITLE
%define DESC        esp + 0x1c          ; the lock description, past the return address
%else
%define DESC        0xF1F1F1F1          ; a placeholder: the description, 0x4e6878 in the European build
%endif
%define D_HEIGHT    8                   ; DDSURFACEDESC2 fields
%define D_WIDTH     0xc
%define D_PITCH     0x10
%define D_SURFACE   0x24
%define D_BITCOUNT  0x54

%ifdef TITLE
        lea     esi, [DESC]             ; the description
%else
        mov     esi, DESC
%endif
        mov     ecx, eax
        shr     ecx, 1                  ; the picture's width
%ifdef TITLE
        mov     ebp, [esp + 4 + 0x10]   ; its height: the rows still to copy
%else
        mov     ebp, [esp + 4 + 0x18]   ; its height: the loop's object, its picture
        mov     ebp, [ebp + 4]
        mov     ebp, [ebp + 8]
%endif
        cmp     [esi + D_WIDTH], ecx
        jne     .picture
%ifndef TITLE                           ; Title.dll's count is the height on the first row only
        cmp     [esi + D_HEIGHT], ebp
        jne     .picture
%endif
        cmp     dword [esi + D_BITCOUNT], 32
        je      .expand
        mov     ecx, eax                ; the original copy
        mov     ebp, ecx
        shr     ecx, 2
        mov     esi, ebx
        mov     edi, edx
        rep movsd
        mov     ecx, ebp
        and     ecx, 3
        rep movsb
%ifdef TITLE
        add     ebx, eax
%endif
        ret

.expand:
        push    eax
        push    ebx
        push    edx
        mov     ecx, eax
        shr     ecx, 1                  ; pixels in the row
        jz      .done
        mov     esi, ebx
        mov     edi, edx
.pixel:
        movzx   eax, word [esi]
        add     esi, 2
        call    pixel32
        stosd
        dec     ecx
        jnz     .pixel
.done:
        pop     edx
        pop     ebx
        pop     eax
%ifdef TITLE
        add     ebx, eax
%endif
        ret

; The bars each side of the drawn picture, in the mean colour of the
; picture's own edge columns: ebp = the frame, the picture drawn. Nothing
; to do when it fills the width.
bars:
        mov     eax, [ebp + 8]
        sub     eax, [ebp + 0x1c]
        shr     eax, 1
        mov     [ebp + 0x3c], eax       ; the bar's width
        test    eax, eax
        jz      .out
        mov     eax, [ebp + 0]          ; the source column a surface column falls on, 16.16: the whole
        shl     eax, 16                 ; picture over the whole width
        xor     edx, edx
        div     dword [ebp + 8]
        mov     [ebp + 0x40], eax
        mov     eax, [ebp + 0]          ; the blur's reach either side of a column: a sixty-fourth of the
        shr     eax, 6                  ; width, so the box is a thirty-second across, at least a column
        jnz     .reach
        mov     eax, 1
.reach: mov     [ebp + 0x4c], eax
        mov     eax, [ebp + 0x3c]       ; the slivers, in source columns: the left from 0, the right from
        add     eax, [ebp + 0x1c]       ; the first past the picture, and how far each runs
        mov     [ebp + 0x64], eax       ; (the right's first surface column, kept for the walk)
        imul    eax, [ebp + 0x40]
        mov     [ebp + 0x68], eax       ; the right's first source column, 16.16
        shr     eax, 16
        mov     ecx, [ebp + 0]
        sub     ecx, eax
        cmp     ecx, SCRATCH
        jbe     .rightfits
        mov     ecx, SCRATCH
.rightfits:
        mov     [ebp + 0x6c], ecx       ; the right's columns
        mov     eax, [ebp + 0x3c]
        imul    eax, [ebp + 0x40]
        shr     eax, 16
        inc     eax
        cmp     eax, SCRATCH
        jbe     .leftfits
        mov     eax, SCRATCH
.leftfits:
        mov     [ebp + 0x70], eax       ; the left's columns
        mov     dword [ebp + 0x48], 0   ; the same walk down the picture the drawing made
        mov     eax, [ebp + 0xc]        ; the rows above it take its first row
        sub     eax, [ebp + 0x20]
        shr     eax, 1
        mov     [ebp + 0x30], eax
        mov     esi, [ebp + 0x14]
        mov     edx, [ebp + 0xc]
.fill:  mov     eax, [ebp + 0x48]       ; this row's source row
        shr     eax, 16
        imul    eax, [ebp + 0]
        lea     ebx, [eax * 2]
        add     ebx, [ebp + 0x34]
        push    esi
        push    edx
        xor     eax, eax                ; the left sliver into the scratch row, and stretched
        mov     ecx, [ebp + 0x70]
        lea     edi, [ebp + 0x90]
        call    sliver
        lea     ebx, [ebp + 0x90]
        mov     edi, esi
        xor     eax, eax
        mov     ecx, [ebp + 0x3c]
        call    stretch
        mov     eax, [ebp + 0x48]       ; the right likewise, from its own first column
        shr     eax, 16
        imul    eax, [ebp + 0]
        lea     ebx, [eax * 2]
        add     ebx, [ebp + 0x34]
        mov     eax, [ebp + 0x68]
        shr     eax, 16
        mov     ecx, [ebp + 0x6c]
        lea     edi, [ebp + 0x90]
        call    sliver
        lea     ebx, [ebp + 0x90]
        mov     edi, [ebp + 0x64]
        cmp     dword [ebp + 0x18], 32
        jne     .right16
        shl     edi, 1
.right16:
        lea     edi, [esi + edi * 2]
        mov     eax, [ebp + 0x68]
        and     eax, 0xffff             ; the walk from the scratch row's first column: the fraction alone
        mov     ecx, [ebp + 8]
        sub     ecx, [ebp + 0x64]
        call    stretch
        pop     edx
        pop     esi
        cmp     dword [ebp + 0x30], 0   ; the picture's rows step the source, the bands above it do not
        je      .step
        dec     dword [ebp + 0x30]
        jmp     .next
.step:  mov     eax, [ebp + 0x28]
        add     [ebp + 0x48], eax
        mov     eax, [ebp + 0x48]       ; and it stops at the last row, for the bands below
        shr     eax, 16
        cmp     eax, [ebp + 4]
        jb      .next
        mov     eax, [ebp + 4]
        dec     eax
        shl     eax, 16
        mov     [ebp + 0x48], eax
.next:  add     esi, [ebp + 0x10]
        dec     edx
        jnz     .fill
.out:   ret

; ebx = a row of the picture, eax = its first column of interest, ecx =
; how many, edi = a scratch row: the sliver as its bar shows it. In
; Title.dll that is the picture, blurred and dimmed; in the exe - the
; loading, game-over and course screens, pictures on a plain background
; - it is the row's own edge pixel, the background, throughout. esi and
; edx kept.
sliver:
%ifdef TITLE
        jmp     blur
%else
        push    ecx
        test    eax, eax                ; the left sliver starts at the edge; the right ends at it
        jz      .edge
        mov     eax, [ebp + 0]
        dec     eax
.edge:  movzx   eax, word [ebx + eax * 2]
        rep     stosw
        pop     ecx
        ret
%endif

; ebx = a row of the picture, eax = its first column of interest, ecx =
; how many, edi = a scratch row: each column's box mean, over the
; columns the reach either side of it that the sliver has, into the
; scratch as 565. A running sum: a column comes into the box as one goes
; out, the count following at the sliver's ends. esi and edx kept.
blur:
        push    esi
        push    edx
        mov     [ebp + 0x74], ecx       ; columns to do
        mov     [ebp + 0x78], eax       ; the column in hand
        mov     [ebp + 0x88], eax       ; the sliver's first and last: the box stays inside it, so the
        add     ecx, eax                ; picture beside the bar does not bleed into it
        dec     ecx
        mov     [ebp + 0x8c], ecx
        xor     ecx, ecx                ; the sums and the count, over the box around the first column
        mov     [ebp + 0x54], ecx
        mov     [ebp + 0x58], ecx
        mov     [ebp + 0x5c], ecx
        mov     [ebp + 0x50], ecx
        mov     esi, eax
        mov     edx, eax
        add     edx, [ebp + 0x4c]
        cmp     edx, [ebp + 0x8c]
        jbe     .to
        mov     edx, [ebp + 0x8c]
.to:    movzx   eax, word [ebx + esi * 2]
        call    boxin
        inc     esi
        cmp     esi, edx
        jbe     .to
.col:   mov     eax, [ebp + 0x54]       ; the mean, dimmed, back to 565
        xor     edx, edx
        div     dword [ebp + 0x50]
        imul    eax, DIM
        shr     eax, 8
        shl     eax, 11
        mov     ecx, eax
        mov     eax, [ebp + 0x58]
        xor     edx, edx
        div     dword [ebp + 0x50]
        imul    eax, DIM
        shr     eax, 8
        shl     eax, 5
        or      ecx, eax
        mov     eax, [ebp + 0x5c]
        xor     edx, edx
        div     dword [ebp + 0x50]
        imul    eax, DIM
        shr     eax, 8
        or      eax, ecx
        stosw
        mov     eax, [ebp + 0x78]       ; the box slides: the column the reach behind goes out
        sub     eax, [ebp + 0x4c]
        cmp     eax, [ebp + 0x88]
        jl      .nothingout
        movzx   eax, word [ebx + eax * 2]
        call    boxout
.nothingout:
        mov     eax, [ebp + 0x78]       ; and the one the reach ahead, plus one, comes in
        add     eax, [ebp + 0x4c]
        inc     eax
        cmp     eax, [ebp + 0x8c]
        ja      .nothingin
        movzx   eax, word [ebx + eax * 2]
        call    boxin
.nothingin:
        inc     dword [ebp + 0x78]
        dec     dword [ebp + 0x74]
        jnz     .col
        pop     edx
        pop     esi
        ret

; eax = a 565 pixel: its channels onto the box's sums, and the count up.
; ecx, edx, esi and edi kept.
boxin:
        push    edx
        mov     edx, eax
        shr     edx, 11
        add     [ebp + 0x54], edx
        mov     edx, eax
        shr     edx, 5
        and     edx, 63
        add     [ebp + 0x58], edx
        and     eax, 31
        add     [ebp + 0x5c], eax
        inc     dword [ebp + 0x50]
        pop     edx
        ret

; eax = a 565 pixel: its channels off the box's sums, and the count down.
boxout:
        push    edx
        mov     edx, eax
        shr     edx, 11
        sub     [ebp + 0x54], edx
        mov     edx, eax
        shr     edx, 5
        and     edx, 63
        sub     [ebp + 0x58], edx
        and     eax, 31
        sub     [ebp + 0x5c], eax
        dec     dword [ebp + 0x50]
        pop     edx
        ret

; ebx = a row, edi = a destination, ecx = pixels, eax = the row's column
; the first of them falls on in 16.16: the span filled with the row,
; nearest pixel, at the surface's depth. esi and edx kept.
stretch:
        push    esi
        push    edx
        mov     esi, eax
.px:    mov     eax, esi
        shr     eax, 16
        movzx   eax, word [ebx + eax * 2]
        cmp     dword [ebp + 0x18], 32
        jne     .narrow
        push    ecx
        push    edx
        push    ebx
        call    pixel32
        pop     ebx
        pop     edx
        pop     ecx
        stosd
        jmp     .on
.narrow:
        stosw
.on:    add     esi, [ebp + 0x40]
        dec     ecx
        jnz     .px
        pop     edx
        pop     esi
        ret

; eax = a 565 pixel: eax = it as XRGB8888. ebx and edx scratch.
pixel32:
        push    ebp
        mov     ebx, eax
        mov     edx, eax
        and     ebx, 0xf800             ; r5 << 11
        and     edx, 0x07e0             ; g6 << 5
        and     eax, 0x001f             ; b5
        mov     ebp, ebx
        shl     ebx, 8                  ; r5 << 19
        shl     ebp, 3
        and     ebp, 0x070000           ; r5 >> 2, at bit 16
        or      ebx, ebp
        mov     ebp, edx
        shl     edx, 5                  ; g6 << 10
        shr     ebp, 1
        and     ebp, 0x000300           ; g6 >> 4, at bit 8
        or      edx, ebp
        mov     ebp, eax
        shl     eax, 3                  ; b5 << 3
        shr     ebp, 2                  ; b5 >> 2
        or      eax, ebp
        or      eax, ebx
        or      eax, edx
        pop     ebp
        ret

; The surface is not the picture's size: esi = the description, ebp = the
; picture's height.
; Frame: [ebp+0] src width, +4 src height, +8 dst width, +0xc dst height,
; +0x10 pitch, +0x14 surface, +0x18 bitcount, +0x1c drawn width, +0x20
; drawn height, +0x24 x step, +0x28 y step (16.16), +0x2c y accumulator,
; +0x30 rows left, +0x34 the source, +0x38 the destination row. The
; bars' own, after the picture is drawn: +0x3c the bar's width, +0x40
; the source column a surface column falls on (16.16), +0x48 the bars'
; own walk down the picture, +0x4c the blur's reach, +0x50 to +0x5c the
; box's count and sums, +0x64 to +0x70 the two slivers' first columns
; and lengths, +0x74 and +0x78 the blur's own counters, +0x88 and +0x8c
; the sliver the box stays inside, and from +0x90 the scratch row a
; sliver goes into.
.picture:
        cmp     edx, [esi + D_SURFACE]
        jne     .later                  ; not the first row: drawn already
        push    eax
        push    ebx
        push    edx
        push    esi
        push    edi
        push    ebp
        mov     ecx, ebp
        sub     esp, 0x90 + SCRATCH * 2
        mov     ebp, esp
        mov     [ebp + 4], ecx
        mov     [ebp + 0x34], ebx
        mov     ecx, eax
        shr     ecx, 1
        mov     [ebp + 0], ecx
        mov     eax, [esi + D_WIDTH]
        mov     [ebp + 8], eax
        mov     eax, [esi + D_HEIGHT]
        mov     [ebp + 0xc], eax
        mov     eax, [esi + D_PITCH]
        mov     [ebp + 0x10], eax
        mov     eax, [esi + D_SURFACE]
        mov     [ebp + 0x14], eax
        mov     eax, [esi + D_BITCOUNT]
        mov     [ebp + 0x18], eax
        ; clear the surface
        mov     edi, [ebp + 0x14]
        mov     edx, [ebp + 0xc]
.clear: mov     ecx, [ebp + 0x10]
        shr     ecx, 2
        xor     eax, eax
        push    edi
        rep stosd
        pop     edi
        add     edi, [ebp + 0x10]
        dec     edx
        jnz     .clear
        ; the drawn size: the largest with the picture's aspect that fits
        mov     eax, [ebp + 8]          ; dst w * src h
        imul    eax, [ebp + 4]
        mov     ecx, [ebp + 0xc]        ; dst h * src w
        imul    ecx, [ebp + 0]
        cmp     eax, ecx
        jbe     .fitwidth
        mov     eax, ecx                ; height fills: width = dst h * src w / src h
        xor     edx, edx
        div     dword [ebp + 4]
        mov     [ebp + 0x1c], eax
        mov     eax, [ebp + 0xc]
        mov     [ebp + 0x20], eax
        jmp     .steps
.fitwidth:                              ; width fills: height = dst w * src h / src w
        xor     edx, edx
        div     dword [ebp + 0]
        mov     [ebp + 0x20], eax
        mov     eax, [ebp + 8]
        mov     [ebp + 0x1c], eax
.steps: mov     eax, [ebp + 0]
        shl     eax, 16
        xor     edx, edx
        div     dword [ebp + 0x1c]
        mov     [ebp + 0x24], eax
        mov     eax, [ebp + 4]
        shl     eax, 16
        xor     edx, edx
        div     dword [ebp + 0x20]
        mov     [ebp + 0x28], eax
        mov     dword [ebp + 0x2c], 0
        ; the first drawn row: (dst h - drawn h) / 2 rows down, (dst w - drawn w) / 2 pixels in
        mov     eax, [ebp + 0xc]
        sub     eax, [ebp + 0x20]
        shr     eax, 1
        imul    eax, [ebp + 0x10]
        add     eax, [ebp + 0x14]
        mov     ecx, [ebp + 8]
        sub     ecx, [ebp + 0x1c]
        shr     ecx, 1
        cmp     dword [ebp + 0x18], 32
        jne     .bpp16
        shl     ecx, 1
.bpp16: lea     eax, [eax + ecx * 2]
        mov     [ebp + 0x38], eax
        mov     eax, [ebp + 0x20]
        mov     [ebp + 0x30], eax
.row:   mov     eax, [ebp + 0x2c]
        shr     eax, 16                 ; the source row
        imul    eax, [ebp + 0]
        lea     esi, [eax * 2]
        add     esi, [ebp + 0x34]
        mov     edi, [ebp + 0x38]
        xor     edx, edx                ; the x accumulator
        mov     ecx, [ebp + 0x1c]
.px:    push    edx
        shr     edx, 16
        movzx   eax, word [esi + edx * 2]
        cmp     dword [ebp + 0x18], 32
        je      .px32
        stosw
        jmp     .pxnext
.px32:  push    ecx
        call    pixel32
        pop     ecx
        stosd
.pxnext:
        pop     edx
        add     edx, [ebp + 0x24]
        dec     ecx
        jnz     .px
        mov     eax, [ebp + 0x28]
        add     [ebp + 0x2c], eax
        mov     eax, [ebp + 0x10]
        add     [ebp + 0x38], eax
        dec     dword [ebp + 0x30]
        jnz     .row
        call    bars
        lea     esp, [ebp + 0x90 + SCRATCH * 2]
        pop     ebp
        pop     edi
        pop     esi
        pop     edx
        pop     ebx
        pop     eax
.later:
%ifdef TITLE
        add     ebx, eax
%endif
        ret
