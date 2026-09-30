# -*- coding: utf-8 -*-
"""The CAN-FD Test Runner netlist: every part, every symbol, every connection.

This file is the single source of truth. The schematic, the libraries and the PCB netlist
are all generated from it, and check() refuses to continue if a pin is in two nets, a pin
is in no net and not marked no-connect, or a net has fewer than two pins.

Design values are derived in docs/03-schematic.md from the datasheets in docs/datasheets/.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ============================================================== symbols
# SYM[name] = (description, left pins, right pins); a pin is (number, name, type)
P, I, O, B, PW = "Passive", "Input", "Output", "IO", "Power"
SYM = {}


def sym(name, desc, left, right):
    SYM[name] = (desc, left, right)


sym("RES", "Resistor", [("1", "1", P)], [("2", "2", P)])
sym("CAP", "Capacitor, non-polarised", [("1", "1", P)], [("2", "2", P)])
sym("IND", "Inductor", [("1", "1", P)], [("2", "2", P)])
sym("LED", "LED", [("1", "A", P)], [("2", "K", P)])
sym("DIODE_SCHOTTKY", "Schottky diode (pad 1 = cathode)", [("2", "A", P)], [("1", "K", P)])
sym("TVS_UNI", "Unidirectional TVS (pad 1 = cathode)", [("1", "K", P)], [("2", "A", P)])
sym("NMOS", "N-channel MOSFET, SOT-23", [("1", "G", I)], [("3", "D", P), ("2", "S", P)])
sym("PMOS", "P-channel MOSFET, SOT-23", [("1", "G", I)], [("2", "S", P), ("3", "D", P)])
sym("XTAL_4P", "Crystal, 4-pad package, pads 2 and 4 = case", [("1", "X1", P), ("2", "GND", P)],
    [("3", "X2", P), ("4", "GND", P)])
sym("SW_4P", "Tactile switch, pads 1/3 and 2/4 common", [("1", "A", P), ("3", "A", P)],
    [("2", "B", P), ("4", "B", P)])

sym("MCP2562FD", "CAN FD transceiver with VIO, SOIC-8",
    [("1", "TXD", I), ("4", "RXD", O), ("8", "STBY", I), ("3", "VDD", PW), ("5", "VIO", PW), ("2", "VSS", PW)],
    [("7", "CANH", B), ("6", "CANL", B)])
sym("LM5164", "LM5164-Q1 100 V 1 A synchronous buck, DDA PowerPAD",
    [("2", "VIN", PW), ("3", "EN/UVLO", I), ("4", "RON", P), ("1", "GND", PW), ("9", "EP", PW)],
    [("8", "SW", P), ("7", "BST", P), ("5", "FB", I), ("6", "PGOOD", O)])
sym("BQ25170", "BQ25170 800 mA linear charger, Li-ion / LiFePO4, WSON-8",
    [("1", "IN", PW), ("2", "ISET", P), ("7", "VSET", P), ("3", "TS", P), ("4", "GND", PW), ("9", "EP", PW)],
    [("8", "OUT", PW), ("5", "STAT", O), ("6", "/PG", O)])
sym("BQ2970", "BQ29706 single-cell protector, OVP 3.85 V / UVP 2.5 V, WSON-6",
    [("5", "BAT", PW), ("4", "VSS", PW), ("6", "V-", P), ("1", "NC", P)],
    [("3", "DOUT", O), ("2", "COUT", O)])
sym("PAC1941", "PAC1941-1 power monitor with charge accumulator, VQFN-16",
    [("2", "VDD", PW), ("3", "GND", PW), ("4", "SCL", I), ("5", "SDA", B), ("6", "ADDRSEL", P),
     ("16", "PWRDN", I), ("1", "SLOW/ALERT1", B), ("15", "GPIO/ALERT2", B), ("17", "EP", P)],
    [("11", "SENSE1+", I), ("12", "SENSE1-", I), ("13", "SENSE2+", I), ("14", "SENSE2-", I),
     ("7", "SENSE3-", I), ("8", "SENSE3+", I), ("9", "SENSE4-", I), ("10", "SENSE4+", I)])
sym("TPS63802", "TPS63802 2 A buck-boost, VSON-10",
    [("10", "VIN", PW), ("1", "EN", I), ("2", "MODE", I), ("3", "AGND", PW), ("8", "GND", PW)],
    [("9", "L1", P), ("7", "L2", P), ("6", "VOUT", PW), ("4", "FB", I), ("5", "PG", O)])
sym("TPS61099", "TPS610997 5.0 V boost, 1 uA Iq, WSON-6",
    [("6", "VIN", PW), ("4", "EN", I), ("1", "GND", PW), ("7", "EP", PW)],
    [("5", "SW", P), ("2", "VOUT", PW), ("3", "FB", I)])
sym("RV3028", "RV-3028-C7 RTC module, 45 nA",
    [("7", "VDD", PW), ("6", "VBACKUP", PW), ("5", "VSS", PW), ("8", "EVI", I)],
    [("3", "SCL", I), ("4", "SDA", B), ("2", "INT", O), ("1", "CLKOUT", O)])
sym("ESD_CAN", "ESD2CANFD24-Q1 CAN FD ESD protection, SOT-23",
    [("1", "IO1", P), ("2", "IO2", P)], [("3", "GND", P)])
sym("ESD_2CH", "TPD2E2U06 2-channel ESD, SC-70", [("1", "IO1", P), ("2", "IO2", P)], [("3", "GND", P)])
sym("DB9_M", "DB9 male, CiA 303-1: 2 CAN_L, 3 CAN_GND, 5 SHLD, 6 GND, 7 CAN_H, 9 V+",
    [("1", "1", P), ("2", "CAN_L", P), ("3", "CAN_GND", P), ("4", "4", P), ("5", "SHLD", P)],
    [("6", "GND", P), ("7", "CAN_H", P), ("8", "8", P), ("9", "V+", P), ("MH", "MH", P)])
sym("USB_C", "USB-C 2.0 receptacle",
    [("A4", "VBUS", P), ("A9", "VBUS", P), ("A5", "CC1", P), ("B5", "CC2", P), ("A8", "SBU1", P),
     ("B8", "SBU2", P)],
    [("A6", "DP1", P), ("B6", "DP2", P), ("A7", "DN1", P), ("B7", "DN2", P), ("A1", "GND", P),
     ("A12", "GND", P), ("SH", "SHIELD", P)])
sym("MICROSD", "microSD push-push with card-detect switch (9/10)",
    [("4", "VDD", P), ("6", "VSS", P), ("9", "CD_A", P), ("10", "CD_B", P), ("SH", "SHIELD", P)],
    [("5", "CLK", P), ("3", "CMD", P), ("7", "DAT0", P), ("8", "DAT1", P), ("1", "DAT2", P), ("2", "CD/DAT3", P)])
sym("FPC10_LCD", "10-pin 0.5 mm FPC, Sharp LS027B7DH01A pin order",
    [("6", "VDDA", P), ("7", "VDD", P), ("8", "EXTMODE", P), ("9", "VSS", P), ("10", "VSSA", P), ("MP", "MP", P)],
    [("1", "SCLK", P), ("2", "SI", P), ("3", "SCS", P), ("4", "EXTCOMIN", P), ("5", "DISP", P)])
sym("CONN3", "3-pin connector", [("1", "1", P), ("2", "2", P), ("3", "3", P)], [("MP", "MP", P)])
sym("SWD_TC2050", "Tag-Connect TC2050, Cortex 10-pin SWD",
    [("1", "VTREF", P), ("3", "GND", P), ("5", "GND", P), ("9", "GND_DET", P), ("7", "KEY", P)],
    [("2", "SWDIO", P), ("4", "SWCLK", P), ("6", "SWO", P), ("8", "NC", P), ("10", "NRST", P)])
sym("BATT_18650", "18650 cell holder", [("1", "+", P)], [("2", "-", P)])
sym("BATT_COIN", "Coin cell retainer", [("1", "+", P)], [("2", "-", P)])

# STM32H563VIT6: all 100 pins from ST DS14258 Table 14 (tools/stm32h563_lqfp100.txt)
_mcu = []
for line in open(os.path.join(HERE, "stm32h563_lqfp100.txt"), encoding="utf-8"):
    num, name, typ = line.split("|")[:3]
    short = name.split("(")[0]
    _mcu.append((num, short, PW if typ == "S" else B))
_power = [p for p in _mcu if p[2] == PW or p[1] in ("NRST", "BOOT0") or p[1].startswith("PH")]
_io = [p for p in _mcu if p not in _power]
sym("STM32H563VIT6", "STM32H563VIT6 Cortex-M33 250 MHz, 2 MB flash, 640 KB SRAM, LQFP-100",
    _power + _io[:len(_io) // 2 - 12], _io[len(_io) // 2 - 12:])

# ============================================================== parts
# (ref, symbol, footprint, comment, manufacturer part number)
PARTS = []
BLOCK = {}          # ref -> functional block, used to lay the schematic out in sections
_blk = ["CONNECTORS"]


def block(name):
    _blk[0] = name


def part(ref, s, f, comment, mpn):
    PARTS.append((ref, s, f, comment, mpn))
    BLOCK[ref] = _blk[0]


block("CONNECTORS")
# --- connectors
part("J1", "DB9_M", "DSUB-9_M_WR-DSUB_618009231221", "CH1 DB9", "Wurth 618009231221")
part("J2", "DB9_M", "DSUB-9_M_WR-DSUB_618009231221", "CH2 DB9", "Wurth 618009231221")
part("J3", "USB_C", "USB-C_GCT_USB4105", "USB-C", "GCT USB4105-GF-A")
part("J4", "MICROSD", "MICROSD_HIROSE_DM3AT", "microSD", "Hirose DM3AT-SF-PEJM5")
part("J5", "FPC10_LCD", "FPC_10P_0.5_WR-FPC_687110149022", "LS027B7DH01A", "Wurth 687110149022")
part("J6", "CONN3", "JST_PH_S3B-PH-SM4-TB", "Cell NTC x2", "JST S3B-PH-SM4-TB")
part("J7", "SWD_TC2050", "TAG-CONNECT_TC2050-IDC-NL", "SWD", "Tag-Connect TC2050-IDC-NL (footprint only)")
part("BT1", "BATT_18650", "BATT_KEYSTONE_1042_18650", "LiFePO4 18650", "Keystone 1042")
part("BT2", "BATT_COIN", "BATT_KEYSTONE_3000_12MM", "CR1220", "Keystone 3000")
part("SW1", "SW_4P", "SW_WS-TASV_6x6", "START/STOP", "Wurth 430182050816")
part("SW2", "SW_4P", "SW_WS-TASV_6x6", "MODE", "Wurth 430182050816")
# --- ICs
part("U1", "STM32H563VIT6", "LQFP-100_14x14", "STM32H563VIT6", "ST STM32H563VIT6")
part("U2", "MCP2562FD", "SOIC-8_150MIL", "MCP2562FD CH1", "Microchip MCP2562FD-E/SN")
part("U3", "MCP2562FD", "SOIC-8_150MIL", "MCP2562FD CH2", "Microchip MCP2562FD-E/SN")
part("U4", "LM5164", "SOIC-8_DDA_PowerPAD", "LM5164-Q1", "TI LM5164QDDARQ1")
part("U5", "BQ25170", "WSON-8_DSG", "BQ25170", "TI BQ25170DSGR")
part("U6", "BQ2970", "WSON-6_DSE", "BQ29706", "TI BQ29706DSER")
part("U7", "PAC1941", "VQFN-16_3x3_4MX", "PAC1941-1", "Microchip PAC1941T-1E/4MX")
part("U8", "TPS63802", "VSON-10_DLA", "TPS63802", "TI TPS63802DLAR")
part("U9", "TPS61099", "WSON-6_DRV", "TPS610997", "TI TPS610997DRVR")
part("U10", "RV3028", "RV-3028-C7", "RV-3028-C7", "Micro Crystal RV-3028-C7 32.768kHz 1ppm-TA-QC")
part("U11", "ESD_CAN", "SOT-23-3", "ESD2CANFD24", "TI ESD2CANFD24DBZRQ1")
part("U12", "ESD_CAN", "SOT-23-3", "ESD2CANFD24", "TI ESD2CANFD24DBZRQ1")
part("U13", "ESD_2CH", "SC-70-3", "TPD2E2U06", "TI TPD2E2U06DCKR")
part("Y1", "XTAL_4P", "XTAL_3225_4P", "24 MHz", "Abracon ABM8-24.000MHZ-B2-T")
# --- discretes
part("D1", "DIODE_SCHOTTKY", "SOD128", "PMEG10030ELP", "Nexperia PMEG10030ELPX")
part("D2", "DIODE_SCHOTTKY", "SOD128", "PMEG10030ELP", "Nexperia PMEG10030ELPX")
part("D3", "TVS_UNI", "SMB", "SMBJ36A", "Bourns SMBJ36A")
part("D4", "DIODE_SCHOTTKY", "SOD123W", "PMEG4030ER", "Nexperia PMEG4030ERX")
part("D5", "DIODE_SCHOTTKY", "SOD123W", "PMEG4030ER", "Nexperia PMEG4030ERX")
part("D6", "DIODE_SCHOTTKY", "SOD123W", "PMEG4030ER", "Nexperia PMEG4030ERX")
part("D7", "LED", "LED0603", "Green", "generic 0603 green LED")
part("Q1", "PMOS", "SOT-23-3", "PMV48XP", "Nexperia PMV48XP")
part("Q2", "NMOS", "SOT-23-3", "PMV16XN", "Nexperia PMV16XN")
part("Q3", "NMOS", "SOT-23-3", "PMV16XN", "Nexperia PMV16XN")
part("Q4", "NMOS", "SOT-23-3", "PMV16XN", "Nexperia PMV16XN")
part("Q5", "PMOS", "SOT-23-3", "PMV48XP", "Nexperia PMV48XP")
part("L1", "IND", "L_WE-LQS-6045", "33uH", "Wurth 74404064330")
part("L2", "IND", "L_WE-MAPI-2016", "0.47uH", "Wurth 744383430047")
part("L3", "IND", "L_WE-LQS-2520", "2.2uH", "Wurth 74404024022")

NETS = {}
NOERC = []


def net(name, *pins):
    NETS.setdefault(name, []).extend(pins)


# passives: auto-numbered, (value, footprint, net a, net b)
_rn, _cn = [0], [0]


def R(value, a, b, f="R0603"):
    _rn[0] += 1
    ref = "R%d" % _rn[0]
    part(ref, "RES", f, value, "generic %s 1%%" % f[1:])
    net(a, ref + ".1"); net(b, ref + ".2")
    return ref


def C(value, a, b, f="C0603"):
    _cn[0] += 1
    ref = "C%d" % _cn[0]
    part(ref, "CAP", f, value, "generic %s X7R/C0G" % f[1:])
    net(a, ref + ".1"); net(b, ref + ".2")
    return ref


# ============================================================== circuit
block("POWER_IN")
# ---- vehicle input: DB9 pin 9 -> OR-ing Schottky (also reverse polarity) -> TVS -> buck
for j, ch, d in (("J1", "1", "D1"), ("J2", "2", "D2")):
    net("CAN%s_L_C" % ch, j + ".2"); net("CAN%s_H_C" % ch, j + ".7")
    net("GND", j + ".3", j + ".5", j + ".6", j + ".MH")
    net("V%s_IN" % ch, j + ".9", d + ".2")
    net("VIN_P", d + ".1")
    NOERC.extend([j + ".1", j + ".4", j + ".8"])
net("VIN_P", "D3.1"); net("GND", "D3.2")
C("2.2uF 100V", "VIN_P", "GND", "C1210")
C("2.2uF 100V", "VIN_P", "GND", "C1210")
net("VIN_P", "U4.2"); net("GND", "U4.1", "U4.9")
R("232k", "VIN_P", "BUCK_EN"); R("100k", "BUCK_EN", "GND"); net("BUCK_EN", "U4.3")
R("31.6k", "BUCK_RON", "GND"); net("BUCK_RON", "U4.4")
net("BUCK_SW", "U4.8", "L1.1"); net("5V_BUCK", "L1.2")
C("2.2nF 50V", "BUCK_BST", "BUCK_SW"); net("BUCK_BST", "U4.7")
R("158k", "5V_BUCK", "BUCK_FB"); R("49.9k", "BUCK_FB", "GND"); net("BUCK_FB", "U4.5")
R("75k", "BUCK_SW", "BUCK_RIP"); C("3.3nF", "BUCK_RIP", "5V_BUCK"); C("180pF C0G", "BUCK_RIP", "BUCK_FB")
C("22uF 25V", "5V_BUCK", "GND", "C1210")
R("100k", "3V3", "VEH_PG"); net("VEH_PG", "U4.6")
R("200k", "VIN_P", "VIN_SENSE"); R("20k", "VIN_SENSE", "GND"); C("100nF", "VIN_SENSE", "GND")

block("CHARGER")
# ---- charge input OR (vehicle 5 V or USB VBUS) and charger
net("5V_BUCK", "D4.2"); net("VBUS", "D5.2"); net("VCHG", "D4.1", "D5.1")
C("10uF", "VCHG", "GND", "C0805")
net("VCHG", "U5.1"); net("GND", "U5.4", "U5.9"); net("VBAT", "U5.8")
R("1k", "CHG_ISET", "GND"); net("CHG_ISET", "U5.2")          # 300 mA
R("82k", "CHG_VSET", "GND"); net("CHG_VSET", "U5.7")         # LiFePO4 3.60 V
net("NTC_CHG", "U5.3", "J6.1")
R("10k", "3V3", "CHG_STAT"); net("CHG_STAT", "U5.5")
R("10k", "3V3", "CHG_PG"); net("CHG_PG", "U5.6")
C("4.7uF", "VBAT", "GND", "C0805")
# firmware charge disable: pulls TS below VTS_ENZ (second layer; hardware NTC stays in charge)
net("NTC_CHG", "Q4.3"); net("GND", "Q4.2"); net("CHG_DIS", "Q4.1"); R("100k", "CHG_DIS", "GND")

block("CHARGER")
# ---- power path: VCHG -> VSYS by Schottky, cell -> VSYS by P-FET that turns on when VCHG goes
net("VCHG", "D6.2"); net("VSYS", "D6.1")
net("VSYS", "Q1.2"); net("VBAT", "Q1.3"); net("VCHG", "Q1.1"); R("47k", "VCHG", "GND")
C("22uF", "VSYS", "GND", "C1210")

block("CELL")
# ---- cell, shunt, protection
net("CELL_P", "BT1.1"); net("CELL_N", "BT1.2")
R("0.1R", "CELL_P", "VBAT", "R0805")                          # coulomb-count shunt
R("330", "CELL_P", "PROT_BAT"); C("100nF", "PROT_BAT", "CELL_N")
net("PROT_BAT", "U6.5"); net("CELL_N", "U6.4"); NOERC.append("U6.1")
R("2.2k", "PROT_VM", "GND"); net("PROT_VM", "U6.6")
net("PROT_DOUT", "U6.3", "Q2.1"); net("PROT_COUT", "U6.2", "Q3.1")
net("CELL_N", "Q2.2"); net("FET_MID", "Q2.3", "Q3.3"); net("GND", "Q3.2")

block("CELL")
# ---- fuel gauge (charge accumulator on the shunt)
net("3V3", "U7.2"); net("GND", "U7.3", "U7.17"); C("100nF", "3V3", "GND")
net("I2C_SCL", "U7.4"); net("I2C_SDA", "U7.5")
R("0", "PAC_ADDR", "GND"); net("PAC_ADDR", "U7.6")
net("PAC_PWRDN", "U7.16"); R("10k", "3V3", "PAC_PWRDN")
R("10k", "PAC_SLOW", "GND"); net("PAC_SLOW", "U7.1")
net("PAC_ALERT", "U7.15"); R("10k", "3V3", "PAC_ALERT")
net("CELL_P", "U7.11"); net("VBAT", "U7.12")
net("GND", "U7.13", "U7.14", "U7.7", "U7.8", "U7.9", "U7.10")    # unused channels grounded (DS20006543 note 3)

block("RAILS")
# ---- 3V3 buck-boost
net("VSYS", "U8.10", "U8.1"); net("GND", "U8.2", "U8.3", "U8.8")
net("BB_L1", "U8.9", "L2.1"); net("BB_L2", "U8.7", "L2.2"); net("3V3", "U8.6")
R("383k", "3V3", "BB_FB"); R("68.1k", "BB_FB", "GND"); net("BB_FB", "U8.4")
NOERC.append("U8.5")
C("10uF", "VSYS", "GND", "C0805"); C("22uF", "3V3", "GND", "C0805"); C("100nF", "3V3", "GND")

block("RAILS")
# ---- 5 V boost for transceivers and display
net("VSYS", "U9.6", "U9.4"); net("GND", "U9.1", "U9.3", "U9.7")
net("BOOST_SW", "U9.5", "L3.2"); net("VSYS", "L3.1"); net("5V_AUX", "U9.2")
C("10uF", "VSYS", "GND", "C0805"); C("10uF", "5V_AUX", "GND", "C0805"); C("10uF", "5V_AUX", "GND", "C0805")

block("MCU")
# ---- MCU power, reset, boot, clock
mcu = {}
for line in open(os.path.join(HERE, "stm32h563_lqfp100.txt"), encoding="utf-8"):
    n, name = line.split("|")[:2]
    mcu[name.split("(")[0].split("-")[0]] = n
PINS_BY_NAME = {}
for line in open(os.path.join(HERE, "stm32h563_lqfp100.txt"), encoding="utf-8"):
    n, name = line.split("|")[:2]
    PINS_BY_NAME.setdefault(name.split("(")[0], []).append(n)
for n in PINS_BY_NAME["VDD"] + PINS_BY_NAME["VDDUSB"] + PINS_BY_NAME["VDDA"] + PINS_BY_NAME["VREF+"] + PINS_BY_NAME["VBAT"]:
    net("3V3", "U1." + n)
for n in PINS_BY_NAME["VSS"] + PINS_BY_NAME["VSSA"] + PINS_BY_NAME["VREF-"]:
    net("GND", "U1." + n)
vc = PINS_BY_NAME["VCAP"]
net("VCAP1", "U1." + vc[0]); C("2.2uF", "VCAP1", "GND")
net("VCAP2", "U1." + vc[1]); C("2.2uF", "VCAP2", "GND")
for _ in PINS_BY_NAME["VDD"]:
    C("100nF", "3V3", "GND")
C("4.7uF", "3V3", "GND", "C0805")
C("100nF", "3V3", "GND"); C("1uF", "3V3", "GND")                 # VDDUSB, VDDA/VREF+
net("NRST", "U1." + PINS_BY_NAME["NRST"][0], "J7.10"); C("100nF", "NRST", "GND")
net("BOOT0", "U1." + PINS_BY_NAME["BOOT0"][0]); R("10k", "BOOT0", "GND")
net("OSC_IN", "U1." + PINS_BY_NAME["PH0-OSC_IN"][0], "Y1.1")
net("OSC_OUT", "U1." + PINS_BY_NAME["PH1-OSC_OUT"][0], "Y1.3")
net("GND", "Y1.2", "Y1.4"); C("27pF C0G", "OSC_IN", "GND"); C("27pF C0G", "OSC_OUT", "GND")

# ---- MCU signal allocation (checked against DS14258 alternate functions, tools/stm32_pins.py)
ALLOC = {
    "PA0": "RTC_CLKOUT", "PA4": "LCD_CS", "PA5": "LCD_SCK", "PA6": "LCD_DISP", "PA7": "LCD_SI",
    "PB2": "EXTCOMIN", "PC0": "VIN_SENSE", "PC1": "NTC_MCU",
    "PE7": "CHG_STAT", "PE8": "CHG_PG", "PE9": "CHG_DIS", "PE10": "VEH_PG", "PE11": "BTN1",
    "PE12": "BTN2", "PE13": "LED_STAT",
    "PB12": "CAN2_RX", "PB13": "CAN2_TX", "PB14": "CAN2_STBY",
    "PC8": "SD_D0", "PC9": "SD_D1", "PC10": "SD_D2", "PC11": "SD_D3", "PC12": "SD_CLK_MCU", "PD2": "SD_CMD",
    "PA9": "VBUS_DET", "PA11": "USB_DM", "PA12": "USB_DP", "PA13": "SWDIO", "PA14": "SWCLK", "PB3": "SWO",
    "PD0": "CAN1_RX", "PD1": "CAN1_TX", "PD3": "CAN1_STBY", "PD4": "SD_CD", "PD5": "SD_PWR_EN_N",
    "PB6": "I2C_SCL", "PB7": "I2C_SDA", "PB8": "RTC_INT", "PB9": "PAC_ALERT", "PE0": "PAC_PWRDN",
}
for pname, sig in ALLOC.items():
    net(sig, "U1." + mcu[pname])
used = {p.split(".")[1] for pins in NETS.values() for p in pins if p.startswith("U1.")}
for num, name, typ in _mcu:
    if num not in used:
        NOERC.append("U1." + num)

# ---- SWD (Cortex 10-pin on TC2050)
net("3V3", "J7.1"); net("GND", "J7.3", "J7.5", "J7.9")
net("SWDIO", "J7.2"); net("SWCLK", "J7.4"); net("SWO", "J7.6"); NOERC.extend(["J7.7", "J7.8"])

block("USB_SD")
# ---- USB-C, device only: CC pulled down 5.1k, VBUS sensed, data ESD
net("VBUS", "J3.A4", "J3.A9"); net("GND", "J3.A1", "J3.A12", "J3.SH")
net("USB_CC1", "J3.A5"); R("5.1k", "USB_CC1", "GND")
net("USB_CC2", "J3.B5"); R("5.1k", "USB_CC2", "GND")
net("USB_DP", "J3.A6", "J3.B6", "U13.1"); net("USB_DM", "J3.A7", "J3.B7", "U13.2"); net("GND", "U13.3")
NOERC.extend(["J3.A8", "J3.B8"])
R("22k", "VBUS", "VBUS_DET"); R("33k", "VBUS_DET", "GND")

block("USB_SD")
# ---- microSD, switched supply so an idle card does not dominate the watch current
net("3V3", "Q5.2"); net("SD_VDD", "Q5.3"); net("SD_PWR_EN_N", "Q5.1"); R("100k", "3V3", "SD_PWR_EN_N")
net("SD_VDD", "J4.4"); net("GND", "J4.6", "J4.SH", "J4.10")
C("10uF", "SD_VDD", "GND", "C0805"); C("100nF", "SD_VDD", "GND")
for sig, pin in (("SD_CMD", "3"), ("SD_D0", "7"), ("SD_D1", "8"), ("SD_D2", "1"), ("SD_D3", "2")):
    net(sig, "J4." + pin); R("47k", "SD_VDD", sig)
R("22", "SD_CLK_MCU", "SD_CLK"); net("SD_CLK", "J4.5")
net("SD_CD", "J4.9"); R("100k", "3V3", "SD_CD")

block("CAN")
# ---- CAN channels
for ch, u, e, j in (("1", "U2", "U11", "J1"), ("2", "U3", "U12", "J2")):
    net("CAN%s_TX" % ch, u + ".1"); net("CAN%s_RX" % ch, u + ".4"); net("CAN%s_STBY" % ch, u + ".8")
    R("10k", "3V3", "CAN%s_STBY" % ch)                               # default: standby, off the bus
    net("5V_AUX", u + ".3"); net("3V3", u + ".5"); net("GND", u + ".2")
    C("100nF", "5V_AUX", "GND"); C("100nF", "3V3", "GND")
    net("CAN%s_H_C" % ch, u + ".7", e + ".1"); net("CAN%s_L_C" % ch, u + ".6", e + ".2"); net("GND", e + ".3")

block("UI")
# ---- display
net("LCD_SCK", "J5.1"); net("LCD_SI", "J5.2"); net("LCD_CS", "J5.3"); net("EXTCOMIN", "J5.4")
net("LCD_DISP", "J5.5"); net("5V_AUX", "J5.6", "J5.7", "J5.8"); net("GND", "J5.9", "J5.10", "J5.MP")
R("100k", "LCD_CS", "GND"); R("100k", "LCD_DISP", "GND")          # SCS is active high
C("1uF", "5V_AUX", "GND"); C("100nF", "5V_AUX", "GND")

block("UI")
# ---- RTC, backup cell, I2C
net("3V3", "U10.7"); net("GND", "U10.5", "U10.8"); net("VBACKUP", "U10.6", "BT2.1"); net("GND", "BT2.2")
net("I2C_SCL", "U10.3"); net("I2C_SDA", "U10.4")
net("RTC_INT", "U10.2"); R("10k", "3V3", "RTC_INT"); net("RTC_CLKOUT", "U10.1")
C("100nF", "3V3", "GND")
R("4.7k", "3V3", "I2C_SCL"); R("4.7k", "3V3", "I2C_SDA")

block("UI")
# ---- user interface
net("BTN1", "SW1.1", "SW1.3"); net("GND", "SW1.2", "SW1.4"); R("10k", "3V3", "BTN1"); C("100nF", "BTN1", "GND")
net("BTN2", "SW2.1", "SW2.3"); net("GND", "SW2.2", "SW2.4"); R("10k", "3V3", "BTN2"); C("100nF", "BTN2", "GND")
R("1k", "LED_STAT", "LED_A"); net("LED_A", "D7.1"); net("GND", "D7.2")
net("NTC_MCU", "J6.2"); net("GND", "J6.3", "J6.MP"); R("10k", "3V3", "NTC_MCU"); C("100nF", "NTC_MCU", "GND")


# ============================================================== checks
def pins_of(ref):
    s = next(p for p in PARTS if p[0] == ref)[1]
    d, left, right = SYM[s]
    return [ref + "." + x[0] for x in left + right]


def check(verbose=True):
    from footprints import FP
    allpins = set()
    for ref, s, f, c, m in PARTS:
        ps = pins_of(ref)
        pads = {p[0] for p in FP[f]["pads"] if p[0]}
        sympins = {x.split(".", 1)[1] for x in ps}
        if sympins != pads:
            raise SystemExit("%s: symbol pins %s != footprint %s pads %s"
                             % (ref, sorted(sympins - pads), f, sorted(pads - sympins)))
        allpins.update(ps)
    seen = {}
    for n, members in NETS.items():
        for m in members:
            if m not in allpins:
                raise SystemExit("net %s: unknown pin %s" % (n, m))
            if m in seen and seen[m] != n:
                raise SystemExit("pin %s in both %s and %s" % (m, seen[m], n))
            seen[m] = n
    for m in NOERC:
        if m in seen:
            raise SystemExit("NoERC pin %s is also in net %s" % (m, seen[m]))
    missing = sorted(allpins - set(seen) - set(NOERC))
    if missing:
        raise SystemExit("pins in no net: %s" % missing)
    for n, members in NETS.items():
        if len(set(members)) < 2:
            raise SystemExit("net %s has one pin: %s" % (n, members))
    if verbose:
        print("parts %d, nets %d, pins %d (%d no-connect)" % (len(PARTS), len(NETS), len(allpins), len(NOERC)))
    return True


if __name__ == "__main__":
    check()
