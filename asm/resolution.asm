; resolution.asm - the Graphic Settings page's RESOLUTION row as a list,
; and an ASPECT RATIO row under it that picks which part of the list.
;
; The stock row shows its two choices, 640X480 and 800X600, side by side
; from sprites, and keeps the choice as 0 or 1 in the game's settings at
; +0x50, which a dozen places in the game read as a yes or no for
; 800x600. The list here is the patcher's table of sizes, the stock two
; first, grouped by aspect: row 7, ASPECT RATIO, holds the group, row 6
; the index within it (its count the group's), the value drawn as text,
; and on leaving the page the size goes to SR2.CFG as [Display]
; Resolution = WxH while +0x50 gets 0 or 1 for the stock two and 0 for
; the rest. On entering, a wide size in SR2.CFG that is in the table
; selects its group and entry, else +0x50 does. The exe reads the same
; line (wide.asm). Row 7 is the page's own machinery - a value and a
; count in the page object, left and right through the stock code - with
; its "7"s made "8" so the cursor reaches it before the buttons; its
; plate is row 6's drawn a pitch lower, its label and value text.
;
; Four entries, through the jump table at the top, each replacing a
; few instructions of the page (Options.dll 0x10003415, 0x10003128,
; 0x10003701, 0x1000365b) and doing what they did:
;
;   init   the page's rows from the settings; the counts
;   draw   row 6's value as text, row 7 whole; the other rows as before
;   leave  the rows into the settings and SR2.CFG
;   reset  DEFAULT: row 6 to the stock default and row 7 to 4:3
;
; The groups and the table follow the code: five (first entry, entries)
; pairs, the (width, height) pairs with 0, 0 after the last, then a
; string for each in the same order, NUL-terminated; the patcher fills
; them all. The annex is writable.

bits 32

%define MAGIC_SELFRVA   0xE7E7E7E7      ; this blob's RVA, filled at apply time
%define MAGIC_SETTINGS  0xD3D3D3D3      ; RVAs in Options.dll, from the patcher: the settings pointer
%define MAGIC_TEXT      0xDBDBDBDB      ; the stock text routine
%define MAGIC_GLYPHS    0xDCDCDCDC      ; its 14-px glyph table
%define MAGIC_VALTAB    0xD4D4D4D4      ; the pointer to row 6's choice sprites
%define MAGIC_LOADLIB   0xE3E3E3E3      ; the import slots
%define MAGIC_GETPROC   0xE4E4E4E4
%define MAGIC_GETMODFN  0xE5E5E5E5
%define MAGIC_DRAW      0xD6D6D6D6      ; the sprite draw
%define MAGIC_PLATES    0xD7D7D7D7      ; the row plates' sprite list
%define ROW             6               ; the resolution row
%define ASPECT          7               ; the aspect row
%define GROUPS          5
%define P_SLIDE         0xc             ; the page: its slide, cursor, rows, counts, pulse
%define P_CURSOR        0x10
%define P_VALUE         0x18 + ROW * 4
%define P_ASPECT        0x18 + ASPECT * 4
%define P_COUNT         0x58 + ROW * 4
%define P_ACOUNT        0x58 + ASPECT * 4
%define P_PULSE         0x78
%define MAX_PATH        260
%define ONE             0x3f800000
%define TEN             0x41200000
%define TWELVE          0x41400000
%define PITCH           0x41d80000      ; 27.0: the rows' spacing
%define LABEL_DX        0x41200000      ; 10.0: the label text from the plate's left edge
%define LABEL_DY        0x40000000      ; 2.0: and down
%define VALUE_X         0x43870000      ; 270.0: the values' x, the first choice sprite's
%define COLON_DX        0x41e00000      ; 28.0: the aspect's left part ends here, so "16" starts where the sizes do
%define COLON_DY        0x40c00000      ; 6.0: the second dot up from the first
%define RIGHT_DX        0x42080000      ; 34.0: the right part starts here

        jmp     near init                    ; +0
        jmp     near draw                    ; +5
        jmp     near leave                   ; +10
        jmp     near reset                   ; +15

; ebx = this blob and ebp = the image base, on return.
getbase:
        call    .here
.here:  pop     ebx
        sub     ebx, .here
        mov     ebp, ebx
        sub     ebp, MAGIC_SELFRVA
        ret

; ---- init: replaces mov eax,[settings]; mov edx,[eax+0x50]; mov [esi+0x70],ecx; mov [esi+0x30],edx

init:
        push    ebx
        push    ebp
        push    ecx
        call    getbase
        mov     eax, [ebp + MAGIC_SETTINGS]
        mov     edx, [eax + 0x50]       ; the stock choice
        push    edx
        call    resolve
        call    readcfg                 ; eax = the table entry SR2.CFG names, or -1
        pop     edx
        cmp     eax, 2
        jl      .stock                  ; -1, or a stock size
        mov     edx, eax
.stock: mov     eax, edx
        call    group                   ; ecx = its group, edx = the index within
        mov     [esi + P_VALUE], edx
        mov     [esi + P_ASPECT], ecx
        mov     [ebx + aspect], ecx
        mov     eax, [ebx + groups + ecx * 8 + 4]
        mov     [esi + P_COUNT], eax
        mov     dword [esi + P_ACOUNT], GROUPS
        pop     ecx
        pop     ebp
        pop     ebx
        ret

; ---- draw: replaces mov eax,[esi+ebx*4+0x38]; xor edi,edi; test eax,eax
; ebx = the row, esi = the page; eax, ecx, edx free.

draw:
        cmp     ebx, ROW
        je      .value
        cmp     ebx, ASPECT
        je      .aspect
        mov     eax, [esi + ebx * 4 + 0x38]
        xor     edi, edi
        test    eax, eax
        ret
.value: push    ebx
        push    ebp
        push    esi
        push    edi
        call    getbase
        mov     ecx, [esi + P_ASPECT]   ; the aspect changed since: row 6 to the group's first
        cmp     ecx, [ebx + aspect]
        je      .same
        mov     [ebx + aspect], ecx
        mov     dword [esi + P_VALUE], 0
        mov     eax, [ebx + groups + ecx * 8 + 4]
        mov     [esi + P_COUNT], eax
.same:  mov     eax, [ebp + MAGIC_VALTAB]
        mov     edi, [eax]              ; the first choice sprite: its place
        mov     eax, [edi + 0x18]
        mov     [ebx + ty], eax
        fld     dword [edi + 0x14]
        fadd    dword [esi + P_SLIDE]
        fstp    dword [ebx + tx]
        mov     ecx, ROW
        call    alpha
        mov     [ebx + talpha], eax
        mov     eax, [esi + P_VALUE]
        mov     ecx, [esi + P_ASPECT]
        add     eax, [ebx + groups + ecx * 8]
        call    string                  ; eax = its text
        mov     ecx, 4                  ; proportional
        call    text
        jmp     .out
.aspect:
        push    ebx
        push    ebp
        push    esi
        push    edi
        call    getbase
        lea     eax, [ebp + MAGIC_PLATES]
        mov     edi, [eax + ROW * 4]    ; row 6's plate, a pitch lower
        push    0
        push    0
        push    0
        cmp     dword [esi + P_CURSOR], ASPECT
        jne     .plain
        push    0x20                    ; on the cursor's row: red
        push    0x20
        push    0x100
        push    0x100
        jmp     .plate
.plain: push    0x100
        push    0x100
        push    0x100
        push    0xd8
.plate: push    ONE
        push    ONE
        push    0
        push    0
        push    0
        push    TWELVE                  ; z
        fld     dword [edi + 0x18]
        fadd    dword [ebx + kpitch]
        fst     dword [ebx + ty]
        push    ecx
        fstp    dword [esp]             ; y
        fld     dword [edi + 0x14]
        fadd    dword [esi + P_SLIDE]
        fst     dword [ebx + tx]
        push    ecx
        fstp    dword [esp]             ; x
        push    edi
        lea     eax, [ebp + MAGIC_DRAW]
        call    eax
        add     esp, 0x40
        fld     dword [ebx + tx]        ; the label: in from the plate's edge, a little down
        fadd    dword [ebx + klabeldx]
        fstp    dword [ebx + tx]
        fld     dword [ebx + ty]
        fadd    dword [ebx + klabeldy]
        fstp    dword [ebx + ty]
        mov     dword [ebx + talpha], 0x100
        lea     eax, [ebx + s_aspect]
        mov     ecx, 4
        call    text
        fld     dword [ebx + kvaluex]   ; the value: the left part ends before the colon,
        fadd    dword [esi + P_SLIDE]   ; the right part starts after it, two dots between
        fst     dword [ebx + vx]
        fadd    dword [ebx + kcolondx]
        fstp    dword [ebx + tx]
        mov     ecx, ASPECT
        call    alpha
        mov     [ebx + talpha], eax
        mov     eax, [esi + P_ASPECT]
        call    aname                   ; eax = the left part, edx = the right
        push    edx
        mov     ecx, 4 | 1              ; right-aligned
        call    text
        lea     eax, [ebx + s_dot]
        mov     ecx, 4
        call    text
        fld     dword [ebx + ty]
        fsub    dword [ebx + kcolondy]
        fstp    dword [ebx + ty]
        lea     eax, [ebx + s_dot]
        call    text
        fld     dword [ebx + ty]
        fadd    dword [ebx + kcolondy]
        fstp    dword [ebx + ty]
        fld     dword [ebx + vx]
        fadd    dword [ebx + krightdx]
        fstp    dword [ebx + tx]
        pop     eax
        call    text
.out:   pop     edi
        pop     esi
        pop     ebp
        pop     ebx
        xor     edi, edi
        xor     eax, eax                ; nothing more on this row: ZF set
        ret

; ecx = a row: eax = its text alpha, white, pulsing on the cursor's row.
alpha:
        mov     eax, 0x100
        cmp     [esi + P_CURSOR], ecx
        jne     .done
        mov     eax, [esi + P_PULSE]
        sar     eax, 1
        add     eax, 0x80
.done:  ret

; eax = a string, ecx = its flags: drawn at tx, ty with talpha through
; the stock routine. eax and edx gone, ecx kept.
text:
        push    ecx
        push    ecx                     ; flags
        lea     ecx, [ebp + MAGIC_GLYPHS]
        push    ecx                     ; the glyph table
        push    0x100                   ; blue, green, red
        push    0x100
        push    0x100
        push    dword [ebx + talpha]
        push    ONE                     ; scale y, x
        push    ONE
        push    TEN                     ; the advance of a missing glyph
        push    TEN                     ; z
        push    dword [ebx + ty]
        push    dword [ebx + tx]
        push    eax
        lea     eax, [ebp + MAGIC_TEXT]
        call    eax
        add     esp, 0x34
        pop     ecx
        ret

; eax = a table index: ecx = its group, edx = its index within it.
group:
        xor     ecx, ecx
.g:     mov     edx, eax
        sub     edx, [ebx + groups + ecx * 8]
        cmp     edx, [ebx + groups + ecx * 8 + 4]
        jb      .done
        inc     ecx
        cmp     ecx, GROUPS
        jb      .g
        xor     ecx, ecx                ; past the table: the first group's first
        xor     edx, edx
.done:  ret

; eax = a group: eax = the left part of its name, edx = the right.
aname:
        lea     edx, [ebx + anames]
        add     eax, eax
.next:  test    eax, eax
        jz      .done
.skip:  inc     edx
        cmp     byte [edx - 1], 0
        jne     .skip
        dec     eax
        jmp     .next
.done:  mov     eax, edx
.right: inc     edx
        cmp     byte [edx - 1], 0
        jne     .right
        ret

; ---- reset: replaces mov ecx,[eax+0x50]; mov [esi+0x30],ecx (DEFAULT)
; eax = the defaults block, esi = the page.

reset:
        push    ebx
        push    ebp
        call    getbase
        mov     ecx, [eax + 0x50]
        mov     [esi + P_VALUE], ecx
        mov     dword [esi + P_ASPECT], 0
        mov     dword [ebx + aspect], 0
        mov     ecx, [ebx + groups + 4]
        mov     [esi + P_COUNT], ecx
        pop     ebp
        pop     ebx
        ret

; ---- leave: replaces mov edx,[settings]; mov ecx,[esi+0x30]; mov [edx+0x50],ecx
; esi = the page; eax, ecx, edx free.

leave:
        push    ebx
        push    ebp
        call    getbase
        mov     eax, [esi + P_VALUE]
        mov     ecx, [esi + P_ASPECT]
        add     eax, [ebx + groups + ecx * 8]
        mov     edx, [ebp + MAGIC_SETTINGS]
        cmp     eax, 2
        jb      .stock
        xor     eax, eax
.stock: mov     [edx + 0x50], eax
        call    resolve                 ; both call out: ecx and edx are gone after
        call    cfgpath
        mov     eax, [esi + P_VALUE]
        mov     ecx, [esi + P_ASPECT]
        add     eax, [ebx + groups + ecx * 8]
        call    string
        push    esi
        push    edi
        mov     esi, eax                ; the string, its X as x, into value
        lea     edi, [ebx + value]
.copy:  lodsb
        cmp     al, 'X'
        jne     .put
        mov     al, 'x'
.put:   stosb
        test    al, al
        jnz     .copy
        pop     edi
        pop     esi
        lea     ecx, [ebx + path]
        push    ecx
        lea     eax, [ebx + value]
        push    eax
        lea     eax, [ebx + s_key]
        push    eax
        lea     eax, [ebx + s_section]
        push    eax
        call    [ebx + fn_writepps]
        pop     ebp
        pop     ebx
        ret

; ---- helpers ----------------------------------------------------------

; eax = a table index: eax = its string.
string:
        lea     edx, [ebx + table]
.pair:  cmp     dword [edx], 0
        je      .found                  ; past the end: the strings start here
        add     edx, 8
        jmp     .pair
.found: add     edx, 8
.next:  test    eax, eax
        jz      .done
.skip:  inc     edx
        cmp     byte [edx - 1], 0
        jne     .skip
        dec     eax
        jmp     .next
.done:  mov     eax, edx
        ret

; eax = the table index of the [Display] Resolution in SR2.CFG, or -1.
readcfg:
        push    esi
        push    edi
        call    cfgpath
        lea     eax, [ebx + path]
        push    eax
        push    32
        lea     eax, [ebx + value]
        push    eax
        lea     eax, [ebx + s_empty]
        push    eax
        lea     eax, [ebx + s_key]
        push    eax
        lea     eax, [ebx + s_section]
        push    eax
        call    [ebx + fn_getpps]
        lea     esi, [ebx + value]
        call    number
        jc      .none
        mov     edi, eax
        cmp     byte [esi], 'x'
        je      .sep
        cmp     byte [esi], 'X'
        jne     .none
.sep:   inc     esi
        call    number
        jc      .none
        lea     esi, [ebx + table]
        xor     ecx, ecx
.entry: mov     edx, [esi]
        test    edx, edx
        jz      .none
        cmp     edx, edi
        jne     .skip
        cmp     [esi + 4], eax
        je      .found
.skip:  add     esi, 8
        inc     ecx
        jmp     .entry
.found: mov     eax, ecx
        pop     edi
        pop     esi
        ret
.none:  or      eax, -1
        pop     edi
        pop     esi
        ret

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

; path = SR2.CFG beside the exe. eax, ecx, edx scratch.
cfgpath:
        push    esi
        push    edi
        lea     edi, [ebx + path]
        push    MAX_PATH
        push    edi
        push    0
        call    [ebp + MAGIC_GETMODFN]
        mov     esi, edi
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
        pop     edi
        pop     esi
        ret

; Once: the two profile routines from kernel32. eax, ecx, edx scratch.
resolve:
        cmp     dword [ebx + fn_getpps], 0
        jne     .done
        push    esi
        lea     eax, [ebx + s_kernel32]
        push    eax
        call    [ebp + MAGIC_LOADLIB]
        mov     esi, eax
        lea     eax, [ebx + s_getpps]
        push    eax
        push    esi
        call    [ebp + MAGIC_GETPROC]
        mov     [ebx + fn_getpps], eax
        lea     eax, [ebx + s_writepps]
        push    eax
        push    esi
        call    [ebp + MAGIC_GETPROC]
        mov     [ebx + fn_writepps], eax
        pop     esi
.done:  ret

s_aspect:   db 'ASPECT RATIO', 0
s_dot:      db '.', 0
anames:     db '4', 0, '3', 0, '16', 0, '10', 0, '16', 0, '9', 0, '21', 0, '9', 0, '32', 0, '9', 0
s_section:  db 'Display', 0
s_key:      db 'Resolution', 0
s_empty:    db 0
s_kernel32: db 'kernel32.dll', 0
s_getpps:   db 'GetPrivateProfileStringA', 0
s_writepps: db 'WritePrivateProfileStringA', 0

        align 4
kpitch:     dd PITCH
klabeldx:   dd LABEL_DX
klabeldy:   dd LABEL_DY
kvaluex:    dd VALUE_X
kcolondx:   dd COLON_DX
kcolondy:   dd COLON_DY
krightdx:   dd RIGHT_DX
fn_getpps:  dd 0
fn_writepps: dd 0
aspect:     dd 0                        ; the group row 6's index and count go with
tx:         dd 0                        ; text's place and alpha; vx the value's x
ty:         dd 0
talpha:     dd 0
vx:         dd 0
value:      times 32 db 0
path:       times MAX_PATH db 0
        align 4
groups:     times GROUPS * 2 dd 0       ; (first entry, entries) a group; the patcher fills them
table:                                  ; the patcher's (width, height) pairs, 0, 0, then the strings
