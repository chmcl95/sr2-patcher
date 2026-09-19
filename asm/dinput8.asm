; dinput8.asm - MGInput.dll's DirectInput object made through dinput8.dll.
;
; The DLL makes its DirectInput object with DirectInputCreateA(hinst,
; 0x500, &out, NULL) and takes IDirectInput2 from it; each device is
; made through that object's CreateDevice and asked for
; IDirectInputDevice2. All of it goes through Windows' legacy dinput.dll,
; whose enumeration of every attached HID device is where the starts
; that hang on a white window go wrong. dinput8.dll's objects carry the
; same vtables - IDirectInput8 matches IDirectInput2 slot for slot,
; IDirectInputDevice8 is IDirectInputDevice2's with three methods after
; - so the DLL's calls stand as they are once the object is DirectInput
; 8's. Three things differ and are taken care of here or by the patcher:
;
; - The create. The eighteen bytes of the DirectInputCreateA call are a
;   jmp to `create`, which looks up dinput8.dll!DirectInput8Create once
;   through the DLL's own LoadLibraryA and GetProcAddress slots and
;   calls it with (hinst, 0x800, IID_IDirectInput8A, &out, NULL); a
;   machine without the DLL gets E_FAIL, as a failed create did. Back at
;   the site's continuation with the result in eax, as the call left it.
; - The interface ids. The patcher writes IID_IDirectInput8A over
;   IID_IDirectInput2A and IID_IDirectInputDevice8A over
;   IID_IDirectInputDevice2A in .rdata, so the two QueryInterface calls
;   succeed on the new objects and hand back the same pointers.
; - The device type. DIDEVCAPS.dwDevType's low byte was 2 mouse, 3
;   keyboard, 4 joystick, which the DLL switches on; DirectInput 8 says
;   0x12, 0x13 and 0x14-0x1c for the joystick kinds, 0x11 for a device
;   of no kind. `kind`, called where the DLL first reads the byte,
;   writes the old code over the new and then does what the displaced
;   instruction did: loads edx with the dword and compares the byte
;   with 3, the flags kept through the ret.
;
; Placeholders the patcher fills, offsets from this blob: LOADLIB and
; GETPROC to the two import slots, CONT to the create site's
; continuation.

bits 32

%define MAGIC_LOADLIB   0xE3E3E3E3
%define MAGIC_GETPROC   0xE4E4E4E4
%define MAGIC_CONT      0xE6E6E6E6

%define DIRECTINPUT_VERSION 0x800
%define E_FAIL          0x80004005

        jmp     near create             ; +0, the create site's entry
                                        ; +5, the kind site's, a call

; The DLL's first read of the device's type byte: made DirectInput 5's,
; then the displaced instruction.
kind:   push    eax
        movzx   eax, byte [esi + 0x260]
        cmp     al, 0x11
        jb      .keep
        cmp     al, 0x14
        jae     .stick
        sub     al, 0x10                ; 0x11-0x13: device, mouse, keyboard
        jmp     .write
.stick: mov     al, 4                   ; joystick, gamepad, wheel and the rest
.write: mov     [esi + 0x260], al
.keep:  pop     eax
        mov     edx, [esi + 0x260]
        cmp     byte [esi + 0x260], 3
        ret

; DirectInput8Create(ebx = hinst, 0x800, IID_IDirectInput8A, &out, NULL),
; the out slot where the site had it; eax = the result.
create: push    ebp
        call    .here
.here:  pop     ebp
        sub     ebp, .here              ; ebp = this blob
        mov     eax, [ebp + fn_create]
        test    eax, eax
        jnz     .call
        lea     eax, [ebp + s_dinput8]
        push    eax
        call    [ebp + MAGIC_LOADLIB]
        test    eax, eax
        jz      .fail
        lea     ecx, [ebp + s_create]
        push    ecx
        push    eax
        call    [ebp + MAGIC_GETPROC]
        test    eax, eax
        jz      .fail
        mov     [ebp + fn_create], eax
.call:  lea     ecx, [esp + 0x14]       ; the site's [esp + 0x10], past the pushed ebp
        push    0
        push    ecx
        lea     ecx, [ebp + iid_di8]
        push    ecx
        push    DIRECTINPUT_VERSION
        push    ebx
        call    eax
        jmp     .back
.fail:  mov     eax, E_FAIL
.back:  lea     ecx, [ebp + MAGIC_CONT]
        pop     ebp
        jmp     ecx

s_dinput8:  db 'dinput8.dll', 0
s_create:   db 'DirectInput8Create', 0
        align 4
iid_di8:    dd 0xbf798030               ; IID_IDirectInput8A, {BF798030-483A-4DA2-AA99-5D64ED369700}
            dw 0x483a, 0x4da2
            db 0xaa, 0x99, 0x5d, 0x64, 0xed, 0x36, 0x97, 0x00
fn_create:  dd 0                        ; DirectInput8Create, once found
