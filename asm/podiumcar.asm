; podiumcar.asm - the podium's extra car gets a race entry of its own.
;
; Each race fills the race state's entries 1..count (+0x100, 0x30 bytes
; apiece) from the championship's standings, count being how many cars
; the course takes (0x41b630); the entries past count are left as the
; last race that used them wrote them. The podium (0x412740) loads the
; year's rival, and in the championship car 14 as well, into the slots
; past count through 0x412a30, and the car's init (0x449740) reads its
; car from the entry of its slot, not from the car itself. When that
; stale entry names car 15 or 20 (the ST185s), the init takes the rival
; for one and writes through the ST185's extra part, which the rival's
; model does not have: a write to 0x0000000c. In year 2 of the
; ten-year championship that is the second course's fourth car, there
; when the first course's finish leaves exactly thirteen cars ahead.
;
; 0x412a30 has put the car in its slot (eax, slot esi) and goes on to
; `mov edx, [esi*4 + CARS]` - the car again - before the car's own
; vtable +0x1c runs the init. That instruction calls here instead: the
; car's id (its model's +4, as the podium compares it) goes into the
; slot's entry, and edx is the car, as the displaced load left it.
;
; The race state's pointer is a placeholder (RACE), filled by the
; patcher from the build's row.

bits 32

%define RACE            0xA9A9A9A9      ; placeholder, EXE_MAGICS
%define ENTRIES         0x100           ; the race state's first entry
%define ENTRY           0x30            ; and its size
%define C_MODEL         0x10            ; a car's model, whose +4 is its car id
%define M_ID            4

        mov     edx, [eax + C_MODEL]
        mov     edx, [edx + M_ID]
        imul    ecx, esi, ENTRY
        add     ecx, [RACE]
        mov     [ecx + ENTRIES], edx    ; the slot's entry names the car in it
        mov     edx, eax                ; the displaced load: the car just stored in the slot
        ret
