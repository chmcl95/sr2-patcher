; nogeneric.asm - MGInput.dll's device list without the HID devices of
; no kind.
;
; The DLL enumerates every attached DirectInput device into a vector of
; DIDEVICEINSTANCEs and then makes a device of each - CreateDevice,
; GetDeviceInfo, GetCapabilities, EnumObjects, SetDataFormat, an object
; of its own polled every frame - skipping only an instance whose GUID is
; null. On a machine of today that list holds LED controllers, a stream
; deck, audio devices' control collections, a receiver's spare
; collections: things DirectInput 8 reports as DI8DEVTYPE_DEVICE, type
; 0x11, a device of no kind, and the game can do nothing with. The four
; kinds above the controllers go the same way - 0x19 device control,
; 0x1a screen pointer, 0x1b remote, 0x1c supplemental - which is what a
; composite pad's spare collections come up as. This skips them all,
; before anything is opened; mice (0x12), keyboards (0x13) and every
; controller kind (0x14-0x18) go through as before.
;
; One entry, reached by a jmp from the loop's `je skip; mov ecx, [esi];
; push edx`, the five bytes after the null-GUID compare, with its flags:
; the je is made here, then the type byte is looked at - eax holds the
; instance's guidInstance, so dwDevType is at +0x20 - and the two
; displaced instructions are done on the way to the continuation. No
; register but edi is touched, as before. Needs dinput8: the type codes
; are DirectInput 8's.
;
; Placeholders the patcher fills, offsets from this blob: CONT, the
; instruction after the displaced ones; SKIP, the je's target.

bits 32

%define MAGIC_CONT      0xE6E6E6E6
%define MAGIC_SKIP      0xE7E7E7E7
%define DI8DEVTYPE_DEVICE   0x11
%define DI8DEVTYPE_DEVICECTRL 0x19      ; the first of the four above the controllers
%define DI8DEVTYPE_SUPPLEMENTAL 0x1c    ; the last

filter: je      .skip                   ; the null GUID, as the site had it
        cmp     byte [eax + 0x20], DI8DEVTYPE_DEVICE
        je      .skip
        cmp     byte [eax + 0x20], DI8DEVTYPE_DEVICECTRL
        jb      .make
        cmp     byte [eax + 0x20], DI8DEVTYPE_SUPPLEMENTAL
        jbe     .skip
.make:  call    .here
.here:  pop     edi
        sub     edi, .here              ; edi = this blob; the site reloads it
        lea     edi, [edi + MAGIC_CONT]
        mov     ecx, [esi]              ; the displaced two
        push    edx
        jmp     edi
.skip:  call    .there
.there: pop     edi
        sub     edi, .there
        lea     edi, [edi + MAGIC_SKIP]
        jmp     edi
