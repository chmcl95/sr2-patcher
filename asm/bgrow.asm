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
;   fit the surface with its aspect kept (nearest pixel) and centred on
;   black, and does nothing on the rows after.
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
; +0x30 rows left, +0x34 the source, +0x38 the destination row.
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
        sub     esp, 0x3c
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
        lea     esp, [ebp + 0x3c]
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
