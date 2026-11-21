; recpage.asm - the records screen's time attack pages of the car ids from
; 30 on (tools/carslot.py, Record.dll).
;
; Record copies the save's rankings into lists of its own at its start,
; 128 entries of room each: the time attack's are 17 courses of 20 pages
; (0x10111cf0, page + course * 20, counts at 0x101bbf3c), the page TOTAL
; and the 19 stock cars. carslot appends the new cars to the car choice,
; pages 20 on (id 30 + page - 20); their lists are here, xrec (page - 20)
; * 17 + course, filled from the exe's carrec (asm/carrec.asm) and put
; back there when the screen ends.
;
;   page        for the list of the page chosen (0x10004bfc): eax from
;               edx the page and ecx the course * 5
;   import_list for a ghost file's record into its car's list (0x100058d4):
;               edx from eax the page, ecx the course; [esi+0x14] its car
;   import_count  its count (0x1000591e): edx from ecx the page, eax the
;               course * 5
;   init        for the two copies' `mov ecx, 0x84` after the lists
;   sort        jumped to after the sort of the lists (0x10005afc)
;   writeback   jumped to after the lists go back (0x10005e6d)
;
; The placeholders are carslot's to fill (RECPAGE_MAGICS in build.py), the
; Record addresses with relocations; xrec past `tail` is carslot's to
; append.

bits 32

%define R_LISTS     0xA5C3B151      ; Record's time attack lists, relocated
%define R_SORT      0xA5C3B152      ; its sort of a list, relocated
%define R_SORTBACK  0xA5C3B153      ; after the bytes the sort's jump replaced, relocated
%define R_WBBACK    0xA5C3B154      ; where the write-back's end went, relocated
%define X_CARREC    0xA5C3B155      ; the exe's carrec lists of id 30 (the exe is not relocated)
%define NREC        0xA5C3B156      ; the pages from 20
%define R_COUNTS    0xA5C3B157      ; Record's time attack counts, relocated

FIRST       equ 30                  ; the first id with a page of its own
PAGE0       equ 20                  ; its page
COURSES     equ 17
LIST        equ 0x800               ; a Record list's room, 128 entries
CARSZ       equ 16 + COURSES * 0x80 ; a carrec slot (carrec.asm's)
MAXREC      equ 12                  ; the car choice holds 32

%macro BASE 1
    call %%here
%%here:
    pop %1
    sub %1, %%here
%endmacro

page:
    cmp edx, PAGE0
    jae .new
    lea eax, [edx + ecx * 4]
    shl eax, 11
    add eax, R_LISTS
    ret
.new:
    push ecx
    push edx
    push ebx
    mov eax, ecx
    xor edx, edx
    mov ebx, 5
    div ebx                         ; the course
    mov ecx, eax
    mov eax, [esp + 4]
    sub eax, PAGE0
    BASE ebx
    call list_of
    pop ebx
    pop edx
    pop ecx
    ret

; eax the page from 20, ecx the course, ebx the blob: eax its list.
list_of:
    imul eax, eax, COURSES
    add eax, ecx
    shl eax, 11
    lea eax, [eax + ebx + xrec]
    ret

import_list:
    movzx edx, byte [esi + 0x14]
    sub edx, FIRST
    cmp edx, NREC
    jb .new
    lea edx, [ecx + ecx * 4]
    lea edx, [eax + edx * 4]
    shl edx, 11
    add edx, R_LISTS
    ret
.new:
    push eax
    push ebx
    BASE ebx
    mov eax, edx
    call list_of
    mov edx, eax
    pop ebx
    pop eax
    ret

import_count:
    movzx edx, byte [esi + 0x14]
    sub edx, FIRST
    cmp edx, NREC
    jb .new
    lea ecx, [ecx + eax * 4]
    shl ecx, 2
    lea edx, [ecx + R_COUNTS]
    ret
.new:
    push eax
    push ebx
    push edx
    xor edx, edx
    mov ebx, 5
    div ebx                         ; the course
    mov ecx, eax
    pop eax
    BASE ebx
    imul eax, eax, COURSES
    add eax, ecx
    shl eax, 2
    lea edx, [eax + ebx + xcnt]
    pop ebx
    pop eax
    ret

init:
    pushad
    BASE ebx
    mov esi, X_CARREC
    lea edi, [ebx + xrec]
    lea edx, [ebx + xcnt]
    xor ebp, ebp
.car:
    cmp ebp, NREC
    jae .done
    push esi
    xor ecx, ecx
.course:
    push ecx
    push edi
    mov ecx, 8
.entry:
    movsd
    movsd
    movsd
    movsd
    mov word [edi - 2], 0xffff      ; no ghost file of it, as Record's own copy
    dec ecx
    jnz .entry
    pop edi
    add edi, LIST
    mov dword [edx], 8
    add edx, 4
    pop ecx
    inc ecx
    cmp ecx, COURSES
    jb .course
    pop esi
    add esi, CARSZ
    inc ebp
    jmp .car
.done:
    popad
    mov ecx, 0x84                   ; what the call replaced
    ret

sort:                               ; ebx Record's screen
    pushad
    BASE esi
    mov ebp, NREC
    imul ebp, ebp, COURSES
    xor edi, edi
.list:
    cmp edi, ebp
    jae .done
    mov eax, edi
    shl eax, 11
    lea eax, [eax + esi + xrec]
    mov [ebx + 0x254c], eax
    lea eax, [esi + xcnt + edi * 4]
    mov [ebx + 0x2550], eax
    mov dword [ebx + 0x2554], 8
    push 0
    mov ecx, ebx
    mov eax, R_SORT
    call eax
    inc edi
    jmp .list
.done:
    popad
    push 0                          ; what the jump replaced
    push 0
    mov ecx, ebx
    push R_SORTBACK
    ret

writeback:                          ; ebx Record's screen
    pushad
    BASE ebx
    lea esi, [ebx + xrec]
    mov edi, X_CARREC
    xor ebp, ebp
.car:
    cmp ebp, NREC
    jae .done
    push edi
    xor edx, edx
.course:
    push esi
    mov ecx, 0x80 / 4               ; the eight shown
    rep movsd
    pop esi
    add esi, LIST
    inc edx
    cmp edx, COURSES
    jb .course
    pop edi
    add edi, CARSZ
    inc ebp
    jmp .car
.done:
    popad
    inc dword [ebx + 8]             ; what the jump replaced
    push R_WBBACK
    ret

align 16
tail:

absolute tail
xcnt:   resd MAXREC * COURSES
xrec:   resb LIST                   ; carslot's: NREC * 17 lists
