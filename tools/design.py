"""Single source of truth for the RP2040 USB-C board: parts, schematic positions, nets, MPNs.

Circuit follows Raspberry Pi "Hardware design with RP2040" (minimal design, section 2) with these changes:
USB-C receptacle (5.1k CC pull-downs) instead of micro-USB, USBLC6-2SC6 ESD on D+/D-, BOOTSEL and RUN
push buttons, SWD header, user LED on GPIO25, Pico-style 1x20 I/O headers.
"""

R0402, C0402 = "Resistor_SMD:R_0402_1005Metric", "Capacitor_SMD:C_0402_1005Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
HDR = "Connector_PinHeader_2.54mm:PinHeader_1x{:02d}_P2.54mm_Vertical"

# ref: (lib_id, value, footprint, x, y, rotation)   schematic placement in mm (A3)
PARTS = {
    "J1": ("Connector:USB_C_Receptacle_USB2.0_16P", "TYPE-C-31-M-12",
           "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", 35.56, 76.2, 0),
    "R6": ("Device:R", "5.1k", R0402, 71.12, 96.52, 0),
    "R7": ("Device:R", "5.1k", R0402, 81.28, 96.52, 0),
    "U4": ("Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6", 109.22, 121.92, 0),
    "R3": ("Device:R", "27", R0402, 142.24, 114.3, 90),
    "R4": ("Device:R", "27", R0402, 142.24, 129.54, 90),
    "U1": ("Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
           104.14, 50.8, 0),
    "C1": ("Device:C", "10u", C0805, 86.36, 58.42, 0),
    "C2": ("Device:C", "10u", C0805, 121.92, 58.42, 0),
    "U2": ("MCU_RaspberryPi:RP2040", "RP2040", "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm",
           218.44, 149.86, 0),
    "U3": ("Memory_Flash:W25Q128JVS", "W25Q128JVSIQ", "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm", 132.08, 175.26, 0),
    "C5": ("Device:C", "100n", C0402, 152.4, 160.02, 0),
    "R1": ("Device:R", "1k", R0402, 101.6, 167.64, 90),
    "SW1": ("Switch:SW_Push", "BOOTSEL", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", 86.36, 180.34, 90),
    "Y1": ("Device:Crystal_GND24", "12MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
           160.02, 218.44, 0),
    "C3": ("Device:C", "15p", C0402, 147.32, 231.14, 0),
    "C4": ("Device:C", "15p", C0402, 172.72, 231.14, 0),
    "R5": ("Device:R", "1k", R0402, 195.58, 218.44, 90),
    "R9": ("Device:R", "10k", R0402, 106.68, 226.06, 0),
    "SW2": ("Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", 119.38, 238.76, 90),
    "R8": ("Device:R", "1k", R0402, 276.86, 205.74, 0),
    "D1": ("Device:LED", "RED", "LED_SMD:LED_0603_1608Metric", 276.86, 223.52, 90),
    "J2": ("Connector_Generic:Conn_01x20", "GPIO L", HDR.format(20), 335.28, 106.68, 0),
    "J3": ("Connector_Generic:Conn_01x20", "GPIO R", HDR.format(20), 375.92, 106.68, 0),
    "J4": ("Connector_Generic:Conn_01x03", "SWD", HDR.format(3), 335.28, 200.66, 0),
    "#FLG1": ("power:PWR_FLAG", "", "", 63.5, 50.8, 0),
    "#FLG2": ("power:PWR_FLAG", "", "", 50.8, 106.68, 0),
}
# decoupling row (net, value, footprint) — each one is placed next to its pin on the PCB
DECAP = {
    "C6": ("+1V1", "100n", C0402), "C7": ("+1V1", "100n", C0402), "C8": ("+1V1", "1u", C0402),
    "C9": ("+3V3", "100n", C0402), "C10": ("+3V3", "1u", C0402), "C11": ("+3V3", "100n", C0402),
    "C12": ("+3V3", "100n", C0402), "C13": ("+3V3", "100n", C0402), "C14": ("+3V3", "100n", C0402),
    "C15": ("+3V3", "100n", C0402), "C16": ("+3V3", "100n", C0402), "C17": ("+3V3", "10u", C0805),
}
for i, (ref, (_, val, fp)) in enumerate(DECAP.items()):
    PARTS[ref] = ("Device:C", val, fp, 177.8 + i * 12.7, 38.1, 0)
for i in range(1, 5):
    PARTS[f"H{i}"] = ("Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", 330.2 + i * 12.7,
                      254.0, 0)

J2_PINS = ["GP0", "GP1", "GND", "GP2", "GP3", "GP4", "GP5", "GND", "GP6", "GP7", "GP8", "GP9", "GND",
           "GP10", "GP11", "GP12", "GP13", "GND", "GP14", "GP15"]
J3_PINS = ["VBUS", "GND", "+3V3", "GP29", "GP28", "GND", "GP27", "GP26", "RUN", "GP24", "GP23", "GP22", "GND",
           "GP21", "GP20", "GP19", "GP18", "GND", "GP17", "GP16"]

RP_GPIO_PIN = {0: 2, 1: 3, 2: 4, 3: 5, 4: 6, 5: 7, 6: 8, 7: 9, 8: 11, 9: 12, 10: 13, 11: 14, 12: 15, 13: 16,
               14: 17, 15: 18, 16: 27, 17: 28, 18: 29, 19: 30, 20: 31, 21: 32, 22: 34, 23: 35, 24: 36, 25: 37,
               26: 38, 27: 39, 28: 40, 29: 41}


def nets() -> dict[str, list[str]]:
    n: dict[str, list[str]] = {}
    add = lambda net, *pins: n.setdefault(net, []).extend(pins)
    add("VBUS", "J1.A4", "J1.A9", "J1.B4", "J1.B9", "U4.5", "U1.1", "U1.3", "C1.1", "#FLG1.1")
    add("GND", "J1.A1", "J1.A12", "J1.B1", "J1.B12", "J1.SH", "U4.2", "U1.2", "C1.2", "C2.2", "Y1.2", "Y1.4",
        "C3.2", "C4.2", "U3.4", "C5.2", "U2.57", "U2.19", "R6.2", "R7.2", "SW1.2", "SW2.2", "D1.1", "J4.2",
        "#FLG2.1")
    add("+3V3", "U1.5", "C2.1", "U3.8", "C5.1", "U2.1", "U2.10", "U2.22", "U2.33", "U2.42", "U2.49", "U2.48",
        "U2.43", "U2.44", "R9.1")
    add("+1V1", "U2.45", "U2.23", "U2.50")
    for ref, (net, _, _) in DECAP.items():
        add(net, f"{ref}.1")
        add("GND", f"{ref}.2")
    add("CC1", "J1.A5", "R6.1")
    add("CC2", "J1.B5", "R7.1")
    add("USB_DP", "J1.A6", "J1.B6", "U4.1", "U4.6", "R3.1")
    add("USB_DM", "J1.A7", "J1.B7", "U4.3", "U4.4", "R4.1")
    add("USB_DP_MCU", "R3.2", "U2.47")
    add("USB_DM_MCU", "R4.2", "U2.46")
    add("QSPI_SS", "U2.56", "U3.1", "R1.1")
    add("BOOT", "R1.2", "SW1.1")
    for name, rp, fl in (("QSPI_SCLK", 52, 6), ("QSPI_SD0", 53, 5), ("QSPI_SD1", 55, 2), ("QSPI_SD2", 54, 3),
                         ("QSPI_SD3", 51, 7)):
        add(name, f"U2.{rp}", f"U3.{fl}")
    add("XIN", "U2.20", "Y1.1", "C3.1")
    add("XOUT_X", "Y1.3", "C4.1", "R5.1")
    add("XOUT", "U2.21", "R5.2")
    add("RUN", "U2.26", "R9.2", "SW2.1")
    add("SWCLK", "U2.24", "J4.1")
    add("SWDIO", "U2.25", "J4.3")
    add("LED", "U2.37", "R8.1")
    add("LED_A", "R8.2", "D1.2")
    for g, pin in RP_GPIO_PIN.items():
        if g != 25:
            add(f"GP{g}", f"U2.{pin}")
    for hdr, pins in (("J2", J2_PINS), ("J3", J3_PINS)):
        for i, net in enumerate(pins, 1):
            add(net, f"{hdr}.{i}")
    return n


NO_CONNECT = ["J1.A8", "J1.B8", "U1.4"]

MPN = {
    "J1": ("Korean Hroparts Elec", "TYPE-C-31-M-12", "C165948"),
    "U1": ("Diodes Incorporated", "AP2112K-3.3TRG1", "C51118"),
    "U2": ("Raspberry Pi", "RP2040", "C2040"),
    "U3": ("Winbond", "W25Q128JVSIQ", "C97521"),
    "U4": ("STMicroelectronics", "USBLC6-2SC6", "C7519"),
    "Y1": ("Abracon", "ABM8-272-T3", "C20625731"),
    "SW1,SW2": ("XKB Connection", "TS-1187A-B-A-B", "C318884"),
    "D1": ("Hubei KENTO Elec", "KT-0603R", "C2286"),
    "R3,R4": ("FOJAN", "FRC0402F27R0TS", "C2909343"),
    "R1,R5,R8": ("UNI-ROYAL", "0402WGF1001TCE", "C11702"),
    "R6,R7": ("UNI-ROYAL", "0402WGF5101TCE", "C25905"),
    "R9": ("UNI-ROYAL", "0402WGF1002TCE", "C25744"),
    "C3,C4": ("FH", "0402CG150J500NT", "C1548"),
    "C5,C6,C7,C9,C11,C12,C13,C14,C15,C16": ("Samsung Electro-Mechanics", "CL05B104KO5NNNC", "C1525"),
    "C8,C10": ("Samsung Electro-Mechanics", "CL05A105KA5NQNC", "C52923"),
    "C1,C2,C17": ("Samsung Electro-Mechanics", "CL21A106KAYNNNE", "C15850"),
    "J2,J3": ("BOOMELE", "2.54-1*20PStraight pin", "C50981"),
    "J4": ("Molex", "22284030", "C587036"),
}

# RP2040 top-edge power pins joined by short wires (one label per chain) instead of one label per pin.
WIRE_CHAINS = {"+3V3": ["U2.48", "U2.43", "U2.1", "U2.44"], "+1V1": ["U2.45", "U2.23"]}
