# CAN-FD Hardware Timestamper - Gate 2: Schematic

| | |
|---|---|
| **Document** | SCH-003 |
| **Revision** | A |
| **Date** | 2026-10-02 |
| **Designer** | Muhamad Izzuwan Alif |
| **Against** | REQ-003 Rev A, ARCH-003 Rev A |
| **Status** | Captured, netlist checked, transferred to the PCB |

> **Note on method.** As for Gate 1, the schematic was developed with an AI assistant. The
> netlist is generated from `tools/design.py`, every part has its datasheet in
> `docs/datasheets/`, and every value below is derived from a cited datasheet.

## 1. How the schematic is built

As in project 02, the netlist is written once in `tools/design.py` and everything else is
generated from it: the A1 sheet (`tools/gen_sch.py`), the footprint library
(`tools/gen_pcblib.py`), and through the ECO the PCB netlist. `design.check()` refuses to continue
if a pin is in two nets, a pin is in no net and not marked no-connect, a net has one pin, or a
symbol's pins do not match its footprint's pads.

New for this board: **the FPGA symbol is generated from Lattice's own pinout file**
(`docs/datasheets/Lattice-ECP5U-25-Pinout-FPGA-SC-02033.csv`, TQFP144 column, all 144 pins), and
the eight user pins are taken from the RTL's committed constraint file
(`syn/ecp5_25f_tqfp144.lpf`), so the symbol cannot disagree with either. `check()` also enforces
**IR-01 / IR-05**: no net may join an isolated island to the host side or to the other island.

```
parts 159, nets 89, pins 622 (132 marked no-connect: 88 unused FPGA I/O, 29 unused FTDI bus pins, ...)
```

The sheet has six titled blocks: FPGA, USB bridge, power input, rails, channel 0, channel 1.

## 2. Gate 2 decisions and changes against ARCH-003

| Topic | ARCH-003 | Gate 2 | Why |
|---|---|---|---|
| Isolation transformer (Q-2) | "Wurth 750313370-class", to be chosen | **Wurth 750313638**, 1:1.3, 5 kV RMS test, **reinforced insulation at 800 V RMS working** (IEC 62368-1), datasheet committed | SN6501 datasheet Table 8-3 lists it for 5 V to 5 V with an LDO; its datasheet states a continuous working voltage, which was the whole reason for choosing a transformer over a module |
| Isolated 5 V regulator | "5 V regulator" | **LP2985-50** (150 mA) after two PMEG2010AEH rectifiers | SN6501 Figure 8-7 regulated configuration; 5 V x 1.3 - 0.4 V = 6.1 V in, 150 mA max against a 60 mA load |
| Vehicle supply input | DB9 pin 9 (V+) | **Separate 2-pin screw terminal J4**; DB9 pin 9 left unconnected | A supply taken from the DB9 must return through a DB9 ground pin, which is that channel's **bus** ground. That would tie the host ground to one bus and defeat IR-01/IR-05. Found while writing the netlist; see 2.1 |
| Reverse-polarity FET | P-channel, part open | **Diodes DMP6023LE**, -60 V, 28 mOhm, SOT-223, gate clamped by **BZT52C12** | 60 V rating for the TVS clamp level (ARCH-003 2.6); a 20 V SOT-23 part was first picked and rejected on its V_DS rating |
| 3.3 V and 1.1 V | "buck or LDO" / "buck" | **TLV62569P** for both | one part number, PG output used for sequencing |
| 2.5 V VCCAUX | LDO, ramp < 30 mV/us | **TLV75525P** | datasheet: built-in soft start, t_STR 550 us typical -> 2.5 V / 550 us = **4.5 mV/us**, inside the 30 mV/us limit (DS1044 note 4) with 6x margin |
| Oscillator | 64 MHz, +/-25 ppm | **Abracon ASEMB-64.000MHZ-LR-T** (MEMS, programmable to 64.000 MHz, -40..+85 C, +/-25 ppm option R) | an off-the-shelf 64 MHz crystal oscillator is not a stock frequency at the first two suppliers tried; the programmable MEMS part is ordered at exactly 64.000 MHz |
| Catch diode for the 60 V buck | - | **PMEG6020ER** 60 V 2 A | TI example uses a 60 V 5 A part at 3.5 A; this board draws 0.3 A |
| USB / vehicle OR-ing | OR-ing | two **PMEG2010AEH** Schottkys into a common 5 V node | ER-04: either source alone, no back-feed |
| FTDI configuration EEPROM | not mentioned | **93LC56C** added | the FT2232H datasheet's self-powered example (Figure 6.4); lets the descriptors and channel modes be stored |

### 2.1 The supply-return problem, and why J4 exists

CiA 303-1 reserves DB9 pin 9 for an optional bus supply, and ARCH-003 planned to power the board
from it. The schematic shows why that cannot work on *this* board: the supply current has to
return somewhere, and the only ground pins on a DB9 are CAN_GND and GND, which are the **bus
ground of that channel**. Routing the vehicle supply from pin 9 into the host-side regulator would
connect host ground to channel 0's bus ground through the regulator return, so the "isolated"
host would be galvanically tied to one of the two buses it is supposed to be isolated from.

The fix is a dedicated 2-pin input (J4, Wurth WR-TBL 2.54 mm screw terminal, 6 A, 150 V) for the
6-32 V supply, with its own return to host ground. DB9 pin 9 is a documented no-connect on both
connectors. The cables of projects 01 and 02 still fit (C-04); they simply do not carry power.

## 3. Design values, each from its datasheet

**TPS54360B, 6-32 V to 5.0 V, 600 kHz** (datasheet section 8.2, 5 V design example, scaled to 0.3 A):

```
RFB            53.6k / 10.2k        VOUT = 0.8 V x (1 + 53.6/10.2) = 5.00 V
RT             162k                 600 kHz
COMP           13.0k + 6.8 nF, 39 pF (as the example)
BOOT           100 nF
L1             33 uH, Wurth 7447709330, Isat 5.5 A; ripple at 32 V in: (32-5) x (5/32) / (33u x 600k) = 0.21 A
Catch diode    PMEG6020ER, 60 V
EN             floating: internal pull-up, UVLO 4.3 V (pin table) -> the 6 V end of ER-01 starts the converter
CIN            2 x 2.2 uF 100 V (1210) + 100 nF;  COUT 2 x 22 uF 10 V
```

**Input protection:** SMBJ33CA bidirectional TVS (33 V standoff, Bourns) across J4; DMP6023LE
P-FET in the positive lead with 100k gate pull-down and BZT52C12 clamping V_GS to 12 V (abs max 20 V,
input up to 32 V).

**TLV62569P, 3.3 V and 1.1 V** (V_FB = 0.6 V, output adjustable from 0.6 V):

```
3V3   453k / 100k   0.6 V x (1 + 4.53)  = 3.32 V       1V1   82.5k / 100k   0.6 V x (1 + 0.825) = 1.095 V
L     2.2 uH Wurth 74404024022 (both)                  ECP5 VCC window 1.045 - 1.155 V (DS1044): 1.095 V is inside
```

**Sequencing (ER-05):** 3V3 comes up first from 5 V. Its **PG** (open drain, 100k to 3V3) enables the
2.5 V LDO, so VCCAUX starts only after VCCIO is good. The 1.1 V buck's EN is driven from the 2.5 V
rail through **100k / 1 uF** (about 60 ms), so VCC comes up last, after VCCAUX has finished its
550 us ramp. Order: VCCIO, VCCAUX, VCC, which satisfies FPGA-TN-02038 section 4 ("VCCIO before or
together with VCC and VCCAUX") with the stricter order ARCH-003 chose to implement.

**ECP5 configuration** (FPGA-TN-02038 tables 6.2 and 6.3): master SPI, **CFG[2:0] = 010**
(CFG1 through 4.7k to 3V3, CFG2 and CFG0 to ground). PROGRAMN, INITN, DONE: 4.7k to 3V3. MCLK: 1k
pull-up. CSSPIN: 10k. JTAG: TCK 4.7k down, TMS and TDI 4.7k up. The SPI flash pins are the dual
function pins of bank 8 in the pinout file: **MCLK 54, MOSI 47, MISO 46, CSSPIN 49**. The flash's
IO2 and IO3 (/WP, /HOLD) are pulled up; quad SPI is not available on the TQFP144 package (same TN,
revision 1.8 note).

**rst_n and the button.** `rst_n` (pin 1) is wired to **DONE**, which the FPGA holds low until the
bitstream has loaded, so the logic starts in reset and leaves it only after configuration
(ARCH-003 section 7, item 2). The button SW1 pulls **PROGRAMN** low instead: pressing it
reconfigures the device, which is a full reset of everything including the UART.

**Decoupling:** one 100 nF at every ECP5 supply pin (6 x VCC, 4 x VCCAUX, 9 x VCCIO) plus 10 uF and
22 uF bulk on each rail; one 100 nF at each FT2232H VCCIO / VREGIN pin; VPHY and VPLL fed through
600 Ohm ferrites with 100 nF, as the FTDI datasheet recommends an LC filter; the oscillator through a
third ferrite with 1 uF + 100 nF (FPGA-TN-02038 figure 10.1); 33 Ohm series on the clock output.

**FT2232H:** 12 MHz ABM8 crystal with 2 x 27 pF (datasheet 6.3), REF 12k, RESET# 10k up, TEST to
ground, VREGOUT to VCORE with 4.7 uF. Channel A ADBUS0-3 = TCK, TDI, TDO, TMS (MPSSE JTAG);
channel B BDBUS1 (RXD) = `uart_txd`.

**ISO1042 (per channel):** VCC1 = 3V3, TXD tied to VCC1 = permanently recessive (**FR-02**, by
construction), RXD to the FPGA with a 10k pull-up so the input idles recessive before the FPGA is
configured (ARCH-003 section 7, item 1). VCC2 = ISO5Vk, GND2 = GND_ISOk. CANH/CANL to the DB9
through an ESD2CANFD24-Q1 referenced to GND_ISOk, with **split termination** (2 x 60.4 Ohm,
4.7 nF to GND_ISOk) behind a 2-pin jumper, open by default (C-04, listen-only tap).

**Isolated supply (per channel):** SN6501 on the host 5 V drives transformer pins 1 and 3, centre
tap 2 at 5 V; secondary centre tap 5 is GND_ISOk; pins 4 and 6 through PMEG2010AEH to VRECTk
(10 uF + 100 nF) into the LP2985-50 (10 nF bypass, 4.7 uF out).

## 4. Pin allocation, checked against the logic

| Signal | Pin | Lattice function | Board net |
|---|---|---|---|
| clk | 128 | PT29A, PCLKT0_0 | CLK64 from the ASEMB oscillator |
| rst_n | 1 | PL5C | DONE |
| can0_rx / can1_rx | 10 / 11 | PL14A / PL14C | ISO1042 RXD, 10k pull-ups |
| uart_txd | 102 | PR8D | FT2232H BDBUS1 |
| led_act0 / led_act1 / led_ovf | 103 / 104 / 105 | PR8B / PR8C / PR8A | 1k + LED |
| MCLK, MOSI, MISO, CSSPIN | 54, 47, 46, 49 | bank 8 dual function | W25Q32 CLK, DI, DO, /CS |
| TCK, TDI, TDO, TMS | 63, 61, 60, 64 | dedicated | FT2232H ADBUS0-3 |

All 99 user I/O of the package are in the symbol; the 88 not used carry No-ERC markers.

## 5. Traceability

| ID | Net or part |
|---|---|
| FR-01 | U2/U3 ISO1042, 5 Mbit/s |
| FR-02 | TXD of both transceivers tied to VCC1; no FPGA pin reaches them |
| FR-03, FR-04 | one oscillator X1 into pin 128; the counter is in the RTL |
| FR-05, ER-07 | FT2232H channel B, BDBUS1 |
| FR-08 | FT2232H channel A on TCK/TMS/TDI/TDO |
| FR-09 | W25Q32 on the master-SPI pins, CFG = 010 |
| FR-10 | D10 power, D11/D12 activity, D13 overflow |
| IR-01, IR-05 | two transformers, two LP2985, two GND_ISO nets; enforced by `check()` |
| IR-02 | ISO1042 5 kV RMS; 750313638 5 kV RMS test, 800 V RMS working |
| IR-04 | SMBJ33CA, DMP6023LE, TPS54360B rated 60 V |
| ER-01 | TPS54360B 4.5-60 V, UVLO 4.3 V |
| ER-02, ER-03 | ASEMB 64.000 MHz, +/-25 ppm |
| ER-04 | D4/D5 OR-ing |
| ER-05 | PG-chained enables, LDO ramp 4.5 mV/us |
| C-04 | DB9 pinout, Wurth 618009231221, split termination with jumper |
| C-05 | pin numbers from the committed LPF; nothing in the RTL changed |

## 6. Open items

- ERC report to be committed.
- The FT2232H EEPROM content (descriptors, channel A as MPSSE/JTAG, self-powered) is written with
  FT_Prog at bring-up; it is not part of the hardware package.
- Q-6 (8 Mbaud UART in the RTL) and Q-7 (Lattice Power Calculator) stay open in the logic repository
  and ARCH-003 respectively; neither changes copper.
