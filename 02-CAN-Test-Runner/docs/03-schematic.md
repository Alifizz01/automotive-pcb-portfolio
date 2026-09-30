# CAN-FD Test Runner - Gate 2: Schematic

| | |
|---|---|
| **Document** | SCH-002 |
| **Revision** | A |
| **Date** | 2026-09-30 |
| **Designer** | Muhamad Izzuwan Alif |
| **Against** | REQ-002 Rev A, ARCH-002 Rev A |
| **Status** | Captured, netlist checked, transferred to the PCB |

> **Note on method.** As for Gate 1, the schematic was developed with an AI assistant. The
> netlist is generated from `tools/design.py`, every part has its datasheet in
> `docs/datasheets/`, and every value below is derived from a cited datasheet.

## 1. How the schematic is built

The netlist is written once, in `tools/design.py`, and everything else is generated from it:
the A1 schematic sheet (`tools/gen_sch.py`), the footprint library (`tools/gen_pcblib.py`) and,
through the ECO, the PCB netlist. `design.check()` refuses to continue if a pin is in two
nets, a pin is in no net and not marked no-connect, a net has one pin, or a symbol's pins do not
match its footprint's pads.

```
parts 131, nets 89, pins 493 (50 marked no-connect)
PCB after ECO: 131 components, 516 pads, 0 pad/net mismatches against design.py
```

The sheet is laid out in eight titled blocks: vehicle input and buck, charger and power path,
cell, rails, microcontroller, CAN, USB and SD, display/RTC/buttons.

## 2. Part changes against ARCH-002

Three first choices from ARCH-002 section 12 could not enter the BOM, because C-03 says no
datasheet, no part, and the manufacturer would not serve the PDF to a scripted download. Each
replacement keeps the property that chose the original.

| Role | ARCH-002 | Used | Why the replacement still meets the requirement |
|---|---|---|---|
| Charger | LTC4098-3.6 | **TI BQ25170** + P-FET load share | LiFePO4 3.60 V by resistor (VSET = 82 k), NTC on TS suspends charge in hardware (C-06), 30 V tolerant input. Power path by a P-FET that turns on when the charge input drops (FR-15: no switch-over decision). |
| Fuel gauge | LTC2942 | **Microchip PAC1941-1** | Has a coulomb-counting mode: the accumulator sums the shunt voltage, so it counts charge rather than modelling a Li-ion curve - the ARCH-002 argument unchanged. |
| Cell protection | "LiFePO4-threshold protector" | **TI BQ29706** + 2 x PMV16XN | OVP 3.85 V, UVP 2.5 V: LiFePO4 thresholds, so the over-voltage trip can actually fire on this cell (ARCH-002 finding 2). |

Parts that were only named by function are now chosen: buck **LM5164-Q1**, buck-boost
**TPS63802**, 5 V boost **TPS610997** (fixed 5.0 V), CAN ESD **ESD2CANFD24-Q1** (the CAN-FD,
low-capacitance variant), USB ESD **TPD2E2U06**, input TVS **SMBJ36A**, OR-ing/reverse
diodes **PMEG10030ELP**, 24 MHz crystal **ABM8-24.000MHZ-B2-T**, display **Sharp LS027B7DH01A**
on a Wurth 0.5 mm FPC, microSD **Hirose DM3AT** (push-push with card detect, as the
architecture asked), USB-C **GCT USB4105**, DB9 **Wurth 618009231221**, 18650 holder
**Keystone 1042**, CR1220 retainer **Keystone 3000**, SWD on a **Tag-Connect TC2050** footprint.

## 3. Design values, each from its datasheet

**LM5164-Q1, 6-32 V to 5 V, 400 kHz** (datasheet section 7.2.2):

```
RFB1 / RFB2   158k / 49.9k            VOUT = 1.2 V x (1 + 158/49.9) = 5.00 V
RRON          5 V x 2500 / 400 kHz  = 31.25k -> 31.6k (396 kHz)
L1            33 uH, Wurth 74404064330, Isat 2.0 A > LM5164 current limit 1.75 A max
RA, CA        75k, 3.3 nF             FB ripple 31 mV at 13.5 V, 42 mV at 32 V
CB            180 pF C0G              >= 75 us / (3 x 158k)
EN/UVLO       232k / 100k             start at 1.5 V x 3.32 = 5.0 V
```

**BQ25170**: ISET 1 k -> 300 A.ohm / 1 k = 300 mA charge. VSET 82 k -> 3.60 V (Table 7-1).
TS to the cell NTC through J6; Q4 pulls TS below VTS_ENZ so firmware can additionally stop a
charge, but cannot start one the NTC has refused.

**TPS63802**: VFB 0.5 V, R1 383 k / R2 68.1 k -> 3.31 V. L2 0.47 uH (Wurth 744383430047,
6.5 A saturation), as TI's inductor table recommends.

**TPS610997**: fixed 5.0 V, FB to GND, L3 2.2 uH (Wurth 74404024022, TI's own recommendation).

**BQ29706**: 330 R + 100 nF on BAT, 2.2 k on V- (datasheet Figure 9-1).

**PAC1941-1**: 0.1 R shunt between cell and pack, bipolar range covers +/-1 A. Unused sense
channels grounded as the datasheet requires.

**STM32H563**: LDO part, so VCAP = 2 x 2.2 uF (DS14258 section 3). 100 nF on every VDD pin,
4.7 uF bulk, 1 uF + 100 nF on VDDA/VREF+. BOOT0 10 k to GND. HSE 24 MHz, 27 pF load caps
for an 18 pF crystal with about 5 pF stray.

## 4. Pin allocation

Every alternate function was checked against DS14258 Table 14, which was extracted from the
PDF by `tools/stm32_pins.py` rather than read by eye.

| Function | Pins |
|---|---|
| FDCAN1 RX/TX, STBY | PD0, PD1, PD3 |
| FDCAN2 RX/TX, STBY | PB12, PB13, PB14 |
| SDMMC1 D0-D3, CK, CMD | PC8-PC11, PC12, PD2 (CMD moved from PB2 to sit beside the other SD pins) |
| USB FS | PA11, PA12, VBUS sense PA9 |
| Display SPI1, CS, DISP | PA5, PA7, PA4, PA6 |
| Display EXTCOMIN | PB2 = LPTIM1_CH1, so the 1 Hz toggle keeps running in stop mode |
| RTC 1 Hz reference | PA0 = TIM2_CH1, to discipline the fast timebase against the 1 ppm RTC |
| I2C1 (RTC, gauge) | PB6, PB7 |
| SWD | PA13, PA14, SWO PB3 |

## 5. Traceability, sections 2 to 4

| ID | Net or part |
|---|---|
| FR-01, FR-02 | U2/U3 MCP2562FD on FDCAN1/2, J1/J2 DB9 CiA 303-1 (2 CAN_L, 7 CAN_H, 3/6 GND, 9 V+) |
| FR-03, SR-05 | J4 microSD on SDMMC1 4-bit, card-detect switch to SD_CD |
| FR-07 | J5 LS027B7DH01A on SPI1 |
| FR-10 | VEH_PG from LM5164 PGOOD, VIN_SENSE divider to ADC |
| FR-11 | U10 RV-3028-C7 with BT2 CR1220 backup |
| FR-12 | SW1 START/STOP, SW2 MODE |
| FR-15, FR-16 | D6 + Q1 power path: VSYS never waits for a decision |
| FR-17, SR-09 | transceiver RXD on EXTI-capable pins, STBY default high (standby) |
| FR-19 to FR-21 | J3 USB-C device (5.1 k CC pull-downs), VBUS to the charger via D5 |
| ER-01, ER-02 | D1/D2 100 V Schottky OR-ing (also reverse polarity), D3 SMBJ36A, LM5164 to 100 V |
| ER-03 | quiescent path: LM5164 10 uA standby, BQ25170 sleep, TPS610997 1 uA |
| ER-06 | a decoupling capacitor on every supply pin; placement distances in the layout document |
| ER-07 | MCP2562FD bus pins rated to +/-58 V |
| ER-10, C-06 | NTC on BQ25170 TS, charge suspended in hardware |
| ER-11 | U6 BQ29706 + Q2/Q3, independent of firmware |
| ER-13 | U7 PAC1941 charge accumulator |
| ER-14 | U11/U12 ESD2CANFD24, U13 TPD2E2U06, D3 on the supply |

## 6. Open items

- The ERC report is still to be committed.
- The ABM8 load capacitance and the crystal's stray-capacitance estimate must be confirmed on the
  first board (clock output measured against the 30 ppm budget of ER-08).
- The display's logic inputs are driven at 3.3 V from a 5 V panel; the Sharp specification
  describes a 3 V serial interface, and this is to be confirmed on hardware.
