; carrec.asm - the records of the car ids from 30 on, kept out of SR2_SAVE.DAT
; (tools/carslot.py, exe).
;
; SR2_SAVE.DAT packs a record's car through a 32-entry table (0x4c9d00):
; an id from 30 on comes back as another car, and a stock exe that reads
; one indexes its tables past their end. So the save keeps the stock cars
; only, and the new ones' records go to RECORD\:
;
;   RECORD\RANKING.REC   the shared rankings' entries of the new cars: the
;                        arcade, the four course lists, the ten years, the
;                        17 time attack totals and the 17 best laps; each
;                        entry's car an index into the file's folder names
;   RECORD\<FOLDER>.REC  one new car's own time attack records, 17 lists
;
; Two shadows of the shared rankings live beside the save buffer, STOCK
; (the stock cars' entries) and NEW (the new cars'), in one layout: the
; save's 0x000-0xcff as it is, then the 17 totals (0xd10 + c * 0xa00) at
; 0xd00 + c * 0x80, then the 17 best laps (0xd604 + c * 0x10) at 0x1580.
; Every entry is 16 bytes, {name 8, time, car, gearbox, 0}.
;
;   load_hook    for the call of the save's load at the start: STOCK is the
;                loaded rankings, NEW and the cars' lists come from their
;                files, and NEW is merged into the rankings by time
;   save_hook    for the call of the save's write at the exit: what the
;                rankings got since is put into the shadows, STOCK goes in
;                for the write, then the files
;   hook_shared  for the four calls of the insert (0x44eb80) on a shared
;                ranking: the entry into its car's shadow too, with the
;                password only from STOCK's, then into the ranking itself
;   pw_gate      for the call that makes the ten years' total password:
;                none for a new car
;   bestlap      for the time attack's best lap update: the shadow's too
;   s1-s5        for the five places a car's own list is found by id
;                (index * 0x80 + course * 0xa00 + 0xd10): a new car's is
;                its own, in carrec
;
; The placeholders are carslot's to fill (CARREC_MAGICS in build.py); the
; buffers past `tail` are carslot's to append.

bits 32

%define P_GAME      0xA5C3B131      ; the game's state pointer (+0x100 the car id, +0x104 the gearbox, +0x108 the name, +0x28c the record's car)
%define P_SAVE      0xA5C3B132      ; the save buffer's pointer
%define P_INSERT    0xA5C3B133      ; the insert into a ranking
%define P_PASSWORD  0xA5C3B134      ; the password maker
%define P_CODE      0xA5C3B135      ; a car id's record code
%define P_LOAD      0xA5C3B136      ; the save's load
%define P_SAVEFN    0xA5C3B137      ; the save's write
%define P_BLBACK    0xA5C3B138      ; the best lap update's branch on its compare
%define P_LAPTIME   0xA5C3B139      ; the lap just driven
%define P_FOLDERS   0xA5C3B13A      ; the folder names by id, moved
%define P_NCAR      0xA5C3B13B      ; how many ids from 30 have a carrec slot
%define P_CREATEFILE 0xA5C3B13C     ; and the import slots
%define P_READFILE  0xA5C3B13D
%define P_WRITEFILE 0xA5C3B13E
%define P_CLOSE     0xA5C3B13F
%define P_GETPROC   0xA5C3B140
%define P_GETMOD    0xA5C3B141
%define P_LSTRCPY   0xA5C3B142
%define P_LSTRCAT   0xA5C3B143
%define P_LSTRCMPI  0xA5C3B144

FIRST       equ 30                  ; the first id with records of its own
SH_BEST     equ 0x1580              ; a shadow's best laps
SH_SIZE     equ 0x1690
SH_LISTED   equ SH_BEST / 16        ; the entries in its lists
SH_ENTRIES  equ SH_SIZE / 16
COURSES     equ 17
CARLISTS    equ COURSES * 0x80
CARSZ       equ 16 + CARLISTS       ; a carrec slot: the spec's MD5, the lists
MAXNAMES    equ 160
NAMESZ      equ 32
MAXUNK      equ 32
RANKHDR     equ 16
FILEMAX     equ RANKHDR + MAXNAMES * NAMESZ + SH_SIZE
CARHDR      equ 16 + NAMESZ + 16
CARFILE     equ CARHDR + CARLISTS
EMPTY       equ 0xff                ; an entry's car when it holds none
OWN         equ 0xfe                ; a car file's entry of that car

%macro BASE 1                       ; the blob's address into %1
    call %%here
%%here:
    pop %1
    sub %1, %%here
%endmacro

; ---------------------------------------------------------------- hooks

hook_shared:                        ; cdecl (list, n, password, code)
    push ebp
    mov ebp, esp
    push ebx
    push esi
    BASE ebx
    mov eax, [P_GAME]
    movzx eax, byte [eax + 0x28c]
    lea esi, [ebx + stock]
    mov edx, [ebp + 16]             ; a stock car's password from STOCK
    cmp eax, FIRST
    jb .shadow
    lea esi, [ebx + new]
    xor edx, edx                    ; a new car's none
.shadow:
    mov eax, [ebp + 8]
    call shadow_of
    add esi, eax
    push dword [ebp + 20]
    push edx
    push dword [ebp + 12]
    push esi
    mov eax, P_INSERT
    call eax
    add esp, 16
    push dword [ebp + 20]           ; the ranking last: the insert's place
    push 0                          ; and work list are its
    push dword [ebp + 12]
    push dword [ebp + 8]
    mov eax, P_INSERT
    call eax
    add esp, 16
    pop esi
    pop ebx
    pop ebp
    ret

pw_gate:                            ; cdecl (fields, out), for the password maker
    mov eax, [P_GAME]
    cmp dword [eax + 0x100], FIRST
    jae .none
    mov eax, P_PASSWORD
    jmp eax
.none:
    xor eax, eax
    ret

bestlap:                            ; jumped to; ebx the course, [esp+0x10] the save's 0xb920
    pushad
    BASE edi
    mov eax, [P_GAME]
    mov ecx, [eax + 0x100]
    lea edi, [edi + stock + SH_BEST]
    cmp ecx, FIRST
    jb .shadow
    add edi, new - stock
.shadow:
    shl ebx, 4
    add edi, ebx
    mov edx, [P_LAPTIME]
    mov esi, [edi + 8]
    test esi, esi
    jz .write
    cmp esi, edx
    jbe .done
.write:
    mov esi, [eax + 0x108]
    mov [edi], esi
    mov esi, [eax + 0x10c]
    mov [edi + 4], esi
    mov [edi + 8], edx
    push ecx
    mov eax, P_CODE
    call eax
    add esp, 4
    mov [edi + 12], al
    mov eax, [P_GAME]
    mov al, [eax + 0x104]
    mov [edi + 13], al
    mov word [edi + 14], 0
.done:
    popad
    mov eax, [esp + 0x10]           ; what the jump replaced
    mov edx, ebx
    shl edx, 4
    mov ecx, [edx + eax + 0x1cec]
    lea esi, [edx + eax]
    cmp ecx, [P_LAPTIME]
    push P_BLBACK                   ; on with the compare's flags
    ret

; A car's own list, found by id: eax the stock place, edx the car.
redir:
    sub edx, FIRST
    jb .out
    cmp edx, P_NCAR
    jae .out
    push ecx
    push ebx
    push edx
    BASE ebx
    sub eax, [P_SAVE]
    sub eax, 0xd10
    push eax
    and dword [esp], 0x7f           ; the offset in the entry
    xor edx, edx
    mov ecx, 0xa00
    div ecx                         ; the course
    shl eax, 7
    pop ecx
    add eax, ecx
    pop edx
    imul edx, edx, CARSZ
    add eax, edx
    lea eax, [eax + ebx + carrec + 16]
    pop ebx
    pop ecx
.out:
    ret

%macro BYID 0                       ; edx the player's car id
    mov edx, [P_GAME]
    mov edx, [edx + 0x100]
%endmacro

s1:                                 ; lea esi, [esi + edi + 0xd18]
    lea esi, [esi + edi + 0xd18]
    push eax
    push edx
    BYID
    mov eax, esi
    call redir
    mov esi, eax
    pop edx
    pop eax
    ret

s2:                                 ; mov eax, [edx + ecx + 0xd18]
    push edx
    lea eax, [edx + ecx + 0xd18]
    BYID
    call redir
    pop edx
    mov eax, [eax]
    ret

s3:                                 ; lea ebx, [edx + eax + 0xd10], the record's car at [esp+0x24]
    lea ebx, [edx + eax + 0xd10]
    push eax
    push edx
    movzx edx, byte [esp + 0x24 + 12]
    mov eax, ebx
    call redir
    mov ebx, eax
    pop edx
    pop eax
    ret

s4:                                 ; lea ecx, [edx + eax + 0xd10]
    lea ecx, [edx + eax + 0xd10]
s4_from:
    push eax
    push edx
    BYID
    mov eax, ecx
    call redir
    mov ecx, eax
    pop edx
    pop eax
    ret

s5:                                 ; lea ecx, [ecx + edx + 0xd10], a car's list when [esp+8] is 0
    lea ecx, [ecx + edx + 0xd10]
    cmp dword [esp + 12], 0
    je s4_from
    ret

; ---------------------------------------------------------------- load and save

load_hook:
    mov eax, P_LOAD
    call eax
    pushad
    BASE ebx
    mov edx, [P_SAVE]
    lea ebp, [ebx + stock]
    lea eax, [ebx + copy_out]
    call each_region                ; STOCK: what was loaded
    call read_ranking
    call read_cars
    lea ebp, [ebx + lists]          ; NEW into the rankings
.list:
    mov eax, [ebp + 4]
    lea esi, [ebx + new + eax]
    mov edi, [ebp]
    add edi, [P_SAVE]
    mov ecx, [ebp + 8]
    push ecx
.entry:
    cmp byte [esi + 12], 0x80
    jae .skip
    cmp dword [esi + 8], -1
    je .skip
    push ecx
    mov ecx, [esp + 4]
    call ins
    pop ecx
.skip:
    add esi, 16
    dec ecx
    jnz .entry
    pop ecx
    add ebp, 12
    cmp dword [ebp + 8], 0
    jne .list
    xor ecx, ecx                    ; and the best laps
.best:
    mov esi, ecx
    shl esi, 4
    lea esi, [ebx + new + SH_BEST + esi]
    mov edi, ecx
    shl edi, 4
    add edi, [P_SAVE]
    add edi, 0xd604
    call best_into
    inc ecx
    cmp ecx, COURSES
    jb .best
    popad
    ret

save_hook:
    pushad
    BASE ebx
    lea ebp, [ebx + lists]          ; what the rankings got, into the shadows
.list:
    mov esi, [ebp]
    add esi, [P_SAVE]
    mov ecx, [ebp + 8]
.entry:
    lea edi, [ebx + stock]
    movzx eax, byte [esi + 12]
    sub eax, FIRST
    cmp eax, 0x80 - FIRST
    jae .stock
    lea edi, [ebx + new]
.stock:
    add edi, [ebp + 4]
    push ecx
    mov ecx, [ebp + 8]
    call has
    test eax, eax
    jnz .there
    call ins
.there:
    pop ecx
    add esi, 16
    dec ecx
    jnz .entry
    add ebp, 12
    cmp dword [ebp + 8], 0
    jne .list
    xor ecx, ecx
.best:
    mov esi, ecx
    shl esi, 4
    add esi, [P_SAVE]
    add esi, 0xd604
    lea edi, [ebx + stock + SH_BEST]
    movzx eax, byte [esi + 12]
    sub eax, FIRST
    cmp eax, 0x80 - FIRST
    jae .bstock
    lea edi, [ebx + new + SH_BEST]
.bstock:
    mov eax, ecx
    shl eax, 4
    add edi, eax
    call best_into
    inc ecx
    cmp ecx, COURSES
    jb .best
    mov edx, [P_SAVE]               ; STOCK in for the write
    lea ebp, [ebx + stock]
    lea eax, [ebx + swap]
    call each_region
    mov esi, [P_SAVE]
    push dword [esi + 0xd08]        ; the ten years' total, of STOCK's tops
    xor eax, eax
    xor ecx, ecx
.year:
    add eax, [esi + ecx + 0x308]
    add ecx, 0x100
    cmp ecx, 0xa00
    jb .year
    mov [esi + 0xd08], eax
    mov eax, P_SAVEFN
    call eax
    mov esi, [P_SAVE]
    pop dword [esi + 0xd08]
    mov edx, esi
    lea ebp, [ebx + stock]
    lea eax, [ebx + swap]
    call each_region
    call make_dir
    call write_ranking
    call write_cars
    popad
    ret

; The save's regions against a shadow's: edx the save, ebp the shadow,
; eax the routine, given esi the save's, edi the shadow's and ecx dwords,
; and keeping them and edx.
each_region:
    push ebx
    push esi
    push edi
    push ecx
    push eax                        ; [esp] the routine
    mov esi, edx
    mov edi, ebp
    mov ecx, 0xd00 / 4
    call [esp]
    xor ebx, ebx
.total:
    mov ecx, ebx
    imul ecx, ecx, 0xa00
    lea esi, [edx + ecx + 0xd10]
    mov ecx, ebx
    shl ecx, 7
    lea edi, [ebp + ecx + 0xd00]
    mov ecx, 0x80 / 4
    call [esp]
    inc ebx
    cmp ebx, COURSES
    jb .total
    lea esi, [edx + 0xd604]
    lea edi, [ebp + SH_BEST]
    mov ecx, COURSES * 16 / 4
    call [esp]
    pop eax
    pop ecx
    pop edi
    pop esi
    pop ebx
    ret

copy_out:                           ; save -> shadow
    push esi
    push edi
    push ecx
    rep movsd
    pop ecx
    pop edi
    pop esi
    ret

swap:
    push esi
    push edi
    push ecx
    push edx
.dword:
    mov eax, [esi]
    mov edx, [edi]
    mov [esi], edx
    mov [edi], eax
    add esi, 4
    add edi, 4
    dec ecx
    jnz .dword
    pop edx
    pop ecx
    pop edi
    pop esi
    ret

; The list's offset in a shadow: eax the save's list.
shadow_of:
    sub eax, [P_SAVE]
    cmp eax, 0xd10
    jb .low
    push edx
    push ecx
    sub eax, 0xd10
    xor edx, edx
    mov ecx, 0xa00
    div ecx
    shl eax, 7
    add eax, 0xd00
    pop ecx
    pop edx
.low:
    ret

; Entry esi into list edi of ecx entries, before the first with a later
; time, the last going.
ins:
    push ebx
    push edx
    push ecx
    mov edx, [esi + 8]
    xor ebx, ebx
.find:
    cmp ebx, ecx
    jae .out
    mov eax, ebx
    shl eax, 4
    cmp [edi + eax + 8], edx
    ja .shift
    inc ebx
    jmp .find
.shift:
    mov eax, ecx
    dec eax
.down:
    cmp eax, ebx
    jbe .put
    push esi
    push edi
    push ecx
    mov ecx, eax
    shl ecx, 4
    lea esi, [edi + ecx - 16]
    add edi, ecx
    mov ecx, 4
    rep movsd
    pop ecx
    pop edi
    pop esi
    dec eax
    jmp .down
.put:
    push esi
    push edi
    shl ebx, 4
    add edi, ebx
    mov ecx, 4
    rep movsd
    pop edi
    pop esi
.out:
    pop ecx
    pop edx
    pop ebx
    ret

; Whether list edi of ecx entries holds entry esi (its 14 bytes): eax.
has:
    push ebx
    push ecx
    push edx
    xor eax, eax
    mov ebx, edi
.next:
    test ecx, ecx
    jz .out
    mov edx, [esi]
    cmp edx, [ebx]
    jne .not
    mov edx, [esi + 4]
    cmp edx, [ebx + 4]
    jne .not
    mov edx, [esi + 8]
    cmp edx, [ebx + 8]
    jne .not
    mov dx, [esi + 12]
    cmp dx, [ebx + 12]
    jne .not
    inc eax
    jmp .out
.not:
    add ebx, 16
    dec ecx
    jmp .next
.out:
    pop edx
    pop ecx
    pop ebx
    ret

; Best lap esi over edi when it holds one and edi none or a slower.
best_into:
    push ecx
    mov eax, [esi + 8]
    test eax, eax
    jz .out
    cmp byte [esi + 12], 0x80
    jae .out
    mov ecx, [edi + 8]
    test ecx, ecx
    jz .copy
    cmp eax, ecx
    jae .out
.copy:
    push esi
    push edi
    mov ecx, 4
    rep movsd
    pop edi
    pop esi
.out:
    pop ecx
    ret

; ---------------------------------------------------------------- files

; A folder name's car: the id whose folder it is, else an unknown one's
; 0x80 + its place (kept for the file), else EMPTY. esi the name.
resolve:
    push ecx
    push edi
    xor edi, edi
.id:
    cmp edi, P_NCAR
    jae .unknown
    mov eax, P_FOLDERS
    mov eax, [eax + edi * 4 + FIRST * 4]
    test eax, eax
    jz .nextid
    push eax
    push esi
    call [P_LSTRCMPI]
    test eax, eax
    jz .found
.nextid:
    inc edi
    jmp .id
.found:
    lea eax, [edi + FIRST]
    jmp .out
.unknown:
    xor edi, edi
.unk:
    cmp edi, [ebx + nunk]
    jae .add
    mov eax, edi
    shl eax, 5
    lea eax, [ebx + unk + eax]
    push eax
    push esi
    call [P_LSTRCMPI]
    test eax, eax
    jz .known
    inc edi
    jmp .unk
.known:
    lea eax, [edi + 0x80]
    jmp .out
.add:
    mov eax, EMPTY
    cmp edi, MAXUNK
    jae .out
    inc dword [ebx + nunk]
    mov eax, edi
    shl eax, 5
    lea eax, [ebx + unk + eax]
    push esi
    push eax
    call [P_LSTRCPY]
    lea eax, [edi + 0x80]
.out:
    pop edi
    pop ecx
    ret

; Open the file named at esi: eax the handle or -1. ecx 0 to read, else write.
open_file:
    push 0
    push 0x80
    test ecx, ecx
    jnz .write
    push 3                          ; OPEN_EXISTING
    push 0
    push 1                          ; FILE_SHARE_READ
    push 0x80000000                 ; GENERIC_READ
    jmp .call
.write:
    push 2                          ; CREATE_ALWAYS
    push 0
    push 0
    push 0x40000000                 ; GENERIC_WRITE
.call:
    push esi
    call [P_CREATEFILE]
    ret

; Read up to ecx bytes of file esi into filebuf: eax the count, 0 when none.
read_whole:
    push ecx
    xor ecx, ecx
    call open_file
    pop ecx
    cmp eax, -1
    je .none
    push eax
    push 0
    lea edx, [ebx + got]
    push edx
    push ecx
    lea edx, [ebx + filebuf]
    push edx
    push eax
    call [P_READFILE]
    call [P_CLOSE]                  ; the handle pushed first
    mov eax, [ebx + got]
    ret
.none:
    xor eax, eax
    ret

; Write ecx bytes of filebuf to file esi.
write_whole:
    push ecx
    mov ecx, 1
    call open_file
    pop ecx
    cmp eax, -1
    je .out
    push eax
    push 0
    lea edx, [ebx + got]
    push edx
    push ecx
    lea edx, [ebx + filebuf]
    push edx
    push eax
    call [P_WRITEFILE]
    call [P_CLOSE]
.out:
    ret

read_ranking:
    lea esi, [ebx + s_rank]
    mov ecx, FILEMAX
    call read_whole
    lea edi, [ebx + filebuf]
    cmp eax, RANKHDR + SH_SIZE
    jb .out
    cmp dword [edi], 'SR2R'
    jne .out
    cmp dword [edi + 4], 1
    jne .out
    mov ecx, [edi + 8]              ; its names
    cmp ecx, MAXNAMES
    ja .out
    mov edx, ecx
    shl edx, 5
    add edx, RANKHDR + SH_SIZE
    cmp eax, edx
    jne .out
    xor ebp, ebp
.name:
    cmp ebp, ecx
    jae .data
    mov esi, ebp
    shl esi, 5
    lea esi, [edi + RANKHDR + esi]
    mov byte [esi + NAMESZ - 1], 0
    call resolve
    mov [ebx + map + ebp], al
    inc ebp
    jmp .name
.data:
    mov esi, ecx
    shl esi, 5
    lea esi, [edi + RANKHDR + esi]
    push ecx
    push esi                        ; NEW from the file
    lea edi, [ebx + new]
    mov ecx, SH_SIZE / 4
    rep movsd
    pop esi
    pop ecx
    lea edi, [ebx + new]            ; its cars, now
    xor edx, edx
.entry:
    movzx eax, byte [edi + 12]
    cmp eax, ecx
    jae .empty
    mov al, [ebx + map + eax]
    cmp al, EMPTY
    je .empty
    mov [edi + 12], al
    jmp .next
.empty:
    call empty
.next:
    add edi, 16
    inc edx
    cmp edx, SH_ENTRIES
    jb .entry
.out:
    ret

; Entry edi (number edx in a shadow) holds none.
empty:
    mov dword [edi], 0
    mov dword [edi + 4], 0
    mov dword [edi + 12], EMPTY
    mov dword [edi + 8], -1
    cmp edx, SH_LISTED
    jb .out
    mov dword [edi + 8], 0          ; a best lap's none
.out:
    ret

write_ranking:
    lea edi, [ebx + filebuf]
    mov dword [edi], 'SR2R'
    mov dword [edi + 4], 1
    mov eax, P_NCAR
    add eax, [ebx + nunk]
    mov [edi + 8], eax
    mov dword [edi + 12], 0
    push eax
    lea edi, [edi + RANKHDR]        ; the names: the ids' from FIRST, the unknown
    push edi
    mov ecx, MAXNAMES * NAMESZ / 4
    xor eax, eax
    rep stosd
    pop edi
    xor ebp, ebp
.ids:
    cmp ebp, P_NCAR
    jae .unk
    mov eax, P_FOLDERS
    mov eax, [eax + ebp * 4 + FIRST * 4]
    test eax, eax
    jz .noid
    push eax
    push edi
    call [P_LSTRCPY]
.noid:
    add edi, NAMESZ
    inc ebp
    jmp .ids
.unk:
    xor ebp, ebp
.unks:
    cmp ebp, [ebx + nunk]
    jae .data
    mov eax, ebp
    shl eax, 5
    lea eax, [ebx + unk + eax]
    push eax
    push edi
    call [P_LSTRCPY]
    add edi, NAMESZ
    inc ebp
    jmp .unks
.data:
    lea esi, [ebx + new]
    push edi
    mov ecx, SH_SIZE / 4
    rep movsd
    pop edi
    mov ecx, SH_ENTRIES             ; its cars as the names' places
.entry:
    movzx eax, byte [edi + 12]
    cmp eax, EMPTY
    je .next
    cmp eax, 0x80
    jae .unknown
    sub eax, FIRST
    jmp .put
.unknown:
    sub eax, 0x80
    add eax, P_NCAR
.put:
    mov [edi + 12], al
.next:
    add edi, 16
    dec ecx
    jnz .entry
    pop ecx                         ; the names
    shl ecx, 5
    add ecx, RANKHDR + SH_SIZE
    lea esi, [ebx + s_rank]
    call write_whole
    ret

; The car file's name into path: ebp the car's place from FIRST, eax 0 when it has no folder.
car_path:
    mov eax, P_FOLDERS
    mov eax, [eax + ebp * 4 + FIRST * 4]
    test eax, eax
    jz .out
    push eax                        ; lstrcatA(path, name) after
    lea eax, [ebx + path]
    push eax
    lea eax, [ebx + s_pre]
    push eax
    lea eax, [ebx + path]
    push eax
    call [P_LSTRCPY]
    call [P_LSTRCAT]
    lea eax, [ebx + s_ext]
    push eax
    lea eax, [ebx + path]
    push eax
    call [P_LSTRCAT]
    lea esi, [ebx + path]
    mov eax, 1
.out:
    ret

read_cars:
    xor ebp, ebp
.car:
    cmp ebp, P_NCAR
    jae .out
    call car_path
    test eax, eax
    jz .next
    mov ecx, CARFILE
    call read_whole
    cmp eax, CARFILE
    jne .next
    lea esi, [ebx + filebuf]
    cmp dword [esi], 'SR2C'
    jne .next
    cmp dword [esi + 4], 1
    jne .next
    add esi, CARHDR
    mov edi, ebp
    imul edi, edi, CARSZ
    lea edi, [ebx + carrec + 16 + edi]
    push edi
    mov ecx, CARLISTS / 4
    rep movsd
    pop edi
    lea eax, [ebp + FIRST]
    mov ecx, CARLISTS / 16
.entry:
    cmp byte [edi + 12], OWN
    jne .other
    mov [edi + 12], al
.other:
    add edi, 16
    dec ecx
    jnz .entry
.next:
    inc ebp
    jmp .car
.out:
    ret

write_cars:
    xor ebp, ebp
.car:
    cmp ebp, P_NCAR
    jae .out
    call car_path
    test eax, eax
    jz .next
    push esi
    lea edi, [ebx + filebuf]
    mov ecx, CARHDR / 4
    xor eax, eax
    rep stosd
    lea edi, [ebx + filebuf]
    mov dword [edi], 'SR2C'
    mov dword [edi + 4], 1
    mov eax, P_FOLDERS
    push dword [eax + ebp * 4 + FIRST * 4]
    lea eax, [edi + 16]
    push eax
    call [P_LSTRCPY]
    mov esi, ebp
    imul esi, esi, CARSZ
    lea esi, [ebx + carrec + esi]   ; the spec's MD5, then the lists
    lea edi, [ebx + filebuf + 16 + NAMESZ]
    mov ecx, CARSZ / 4
    rep movsd
    lea edi, [ebx + filebuf + CARHDR]
    lea eax, [ebp + FIRST]
    mov ecx, CARLISTS / 16
.entry:
    cmp [edi + 12], al
    jne .other
    mov byte [edi + 12], OWN
.other:
    add edi, 16
    dec ecx
    jnz .entry
    pop esi
    mov ecx, CARFILE
    call write_whole
.next:
    inc ebp
    jmp .car
.out:
    ret

make_dir:                           ; RECORD, through CreateDirectoryA (not imported)
    lea eax, [ebx + s_k32]
    push eax
    call [P_GETMOD]
    test eax, eax
    jz .out
    lea edx, [ebx + s_cd]
    push edx
    push eax
    call [P_GETPROC]
    test eax, eax
    jz .out
    push 0
    lea edx, [ebx + s_dir]
    push edx
    call eax
.out:
    ret

; ---------------------------------------------------------------- data

align 4
lists:                              ; the shared rankings: save offset, shadow offset, entries
    dd 0, 0, 16                     ; the arcade
%assign i 0
%rep 4
    dd 0x100 + i * 0x80, 0x100 + i * 0x80, 8    ; the course lists
%assign i i + 1
%endrep
%assign i 0
%rep 10
    dd 0x300 + i * 0x100, 0x300 + i * 0x100, 16 ; the years
%assign i i + 1
%endrep
%assign i 0
%rep COURSES
    dd 0xd10 + i * 0xa00, 0xd00 + i * 0x80, 8   ; the time attack totals
%assign i i + 1
%endrep
    dd 0, 0, 0
nunk:   dd 0
got:    dd 0
map:    times MAXNAMES db 0
path:   times 64 db 0
s_dir:  db 'RECORD', 0
s_rank: db 'RECORD\RANKING.REC', 0
s_pre:  db 'RECORD\', 0
s_ext:  db '.REC', 0
s_k32:  db 'KERNEL32.DLL', 0
s_cd:   db 'CreateDirectoryA', 0
align 16
tail:                               ; carslot appends the rest

absolute tail
unk:     resb MAXUNK * NAMESZ
stock:   resb SH_SIZE
new:     resb SH_SIZE               ; carslot's: every list entry EMPTY with time -1, best laps EMPTY with 0
filebuf: resb FILEMAX
carrec:  resb CARSZ                 ; carslot's: per id from 30, the spec's MD5 and its perf car's default lists
