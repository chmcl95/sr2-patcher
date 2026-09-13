; resolution.asm - the Graphic Settings page's RESOLUTION row as a list.
;
; The stock row shows its two choices, 640X480 and 800X600, side by side
; from sprites, and keeps the choice as 0 or 1 in the game's settings at
; +0x50, which a dozen places in the game read as a yes or no for
; 800x600. The list here is the patcher's table of sizes, the stock two
; first: the value is drawn as text, left and right step through the
; table, and on leaving the page the size goes to SR2.CFG as
; [Display] Resolution = WxH while +0x50 gets 0 or 1 for the stock two
; and 0 for the rest. On entering, a wide size in SR2.CFG that is in
; the table selects its entry, else +0x50 does. The exe reads the same
; line (wide.asm).
;
; Three entries, through the jump table at the top, each replacing a
; few instructions of the page (Options.dll 0x10003415, 0x10003128,
; 0x10003701) and doing what they did:
;
;   init   the page's row from the settings; the row's count from the table
;   draw   row 6's value as text; the other rows as before
;   leave  the row into the settings and SR2.CFG
;
; The table follows the code: (width, height) pairs, 0, 0 after the last,
; then a string for each in the same order, NUL-terminated. The annex is
; writable.

bits 32

%define MAGIC_SELFRVA   0xE7E7E7E7      ; this blob's RVA, filled at apply time
%define MAGIC_SETTINGS  0xD3D3D3D3      ; RVAs in Options.dll, from the patcher: the settings pointer
%define MAGIC_TEXT      0xDBDBDBDB      ; the stock text routine
%define MAGIC_GLYPHS    0xDCDCDCDC      ; its 14-px glyph table
%define MAGIC_VALTAB    0xD4D4D4D4      ; the pointer to row 6's choice sprites
%define MAGIC_LOADLIB   0xE3E3E3E3      ; the import slots
%define MAGIC_GETPROC   0xE4E4E4E4
%define MAGIC_GETMODFN  0xE5E5E5E5
%define ROW             6               ; the resolution row
%define P_SLIDE         0xc             ; the page: its slide, cursor, rows, counts, pulse
%define P_CURSOR        0x10
%define P_VALUE         0x18 + ROW * 4
%define P_COUNT         0x58 + ROW * 4
%define P_PULSE         0x78
%define MAX_PATH        260
%define ONE             0x3f800000
%define TEN             0x41200000

        jmp     near init                    ; +0
        jmp     near draw                    ; +5
        jmp     near leave                   ; +10

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
.stock: mov     [esi + P_VALUE], edx
        mov     eax, [ebx + count]
        mov     [esi + P_COUNT], eax
        pop     ecx
        pop     ebp
        pop     ebx
        ret

; ---- draw: replaces mov eax,[esi+ebx*4+0x38]; xor edi,edi; test eax,eax
; ebx = the row, esi = the page; eax, ecx, edx free.

draw:
        cmp     ebx, ROW
        je      .value
        mov     eax, [esi + ebx * 4 + 0x38]
        xor     edi, edi
        test    eax, eax
        ret
.value: push    ebx
        push    ebp
        push    esi
        push    edi
        call    getbase
        mov     eax, [ebp + MAGIC_VALTAB]
        mov     edi, [eax]              ; the first choice sprite: its place
        mov     eax, 0x100              ; the alpha: white, pulsing on the cursor's row
        cmp     dword [esi + P_CURSOR], ROW
        jne     .alpha
        mov     eax, [esi + P_PULSE]
        sar     eax, 1
        add     eax, 0x80
.alpha: push    4                       ; flags: proportional
        lea     ecx, [ebp + MAGIC_GLYPHS]
        push    ecx                     ; the glyph table
        push    0x100                   ; blue, green, red
        push    0x100
        push    0x100
        push    eax                     ; alpha
        push    ONE                     ; scale y, x
        push    ONE
        push    TEN                     ; the advance of a missing glyph
        push    TEN                     ; z
        push    dword [edi + 0x18]      ; y: the first choice sprite's
        fld     dword [edi + 0x14]      ; x: its, slid with the page
        fadd    dword [esi + P_SLIDE]
        push    ecx
        fstp    dword [esp]
        mov     eax, [esi + P_VALUE]
        call    string                  ; eax = its text
        push    eax
        lea     eax, [ebp + MAGIC_TEXT]
        call    eax
        add     esp, 0x34
        pop     edi
        pop     esi
        pop     ebp
        pop     ebx
        xor     edi, edi
        xor     eax, eax                ; nothing more on this row: ZF set
        ret

; ---- leave: replaces mov edx,[settings]; mov ecx,[esi+0x30]; mov [edx+0x50],ecx
; esi = the page; eax, ecx, edx free.

leave:
        push    ebx
        push    ebp
        call    getbase
        mov     ecx, [esi + P_VALUE]
        mov     edx, [ebp + MAGIC_SETTINGS]
        mov     eax, ecx
        cmp     eax, 2
        jb      .stock
        xor     eax, eax
.stock: mov     [edx + 0x50], eax
        call    resolve                 ; both call out: ecx and edx are gone after
        call    cfgpath
        mov     eax, [esi + P_VALUE]
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

s_section:  db 'Display', 0
s_key:      db 'Resolution', 0
s_empty:    db 0
s_kernel32: db 'kernel32.dll', 0
s_getpps:   db 'GetPrivateProfileStringA', 0
s_writepps: db 'WritePrivateProfileStringA', 0

        align 4
fn_getpps:  dd 0
fn_writepps: dd 0
value:      times 32 db 0
path:       times MAX_PATH db 0
        align 4
count:      dd 0                        ; the table's entries; the patcher fills it
table:                                  ; the patcher's (width, height) pairs, 0, 0, then the strings
