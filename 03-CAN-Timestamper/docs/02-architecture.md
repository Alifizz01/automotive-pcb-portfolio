# CAN-FD Hardware Timestamper - Gate 1: Architecture

| | |
|---|---|
| **Document** | ARCH-003 |
| **Revision** | A |
| **Date** | 2026-09-20 |
| **Author** | Muhamad Izzuwan Alif |
| **Status** | Gate 1, closing Q-1 to Q-5 of REQ-003 |

---

> **Note on method.** The requirements and architecture for this board were developed in
> discussion with an AI assistant. Every figure in them is either derived in the document
> itself or taken from a cited datasheet, and the design decisions are mine.

This document closes Gate 1. It selects the parts, fixes the power and isolation
architecture, writes the timestamp error budget that REQ-003 asked for, and checks the pin
allocation against the constraint file the FPGA logic is already built with.

The logic is not designed here. It exists, and it is verified:
[fpga-can-timestamper](https://github.com/Alifizz01/fpga-can-timestamper). Several numbers
below are taken from that repository's synthesis reports rather than estimated, and where
that is so it is said.

---

## 1. Block diagram

```
   CHANNEL 0                    |  ISOLATION  |            HOST SIDE
                                |   BARRIER   |
  DB9-0  --- CANH/CANL --->  ISO1042  =====>  RXD0 ------+
  (CiA 303-1)                   |             |          |
                          iso 5V |            |          |
                     SN6501 + xfmr <----------+          |
                                |             |          v
   CHANNEL 1                    |             |    +-------------+
  DB9-1  --- CANH/CANL --->  ISO1042  =====>  RXD1 |   LFE5U-25F |
                                |             |    |   TQFP144   |
                          iso 5V |            |    |             |
                     SN6501 + xfmr <----------+    |  64 MHz in  |<-- XO
                                |             |    +------+------+
                                |             |           |  ^
                                                    UART  |  | SPI
                                                   4 Mbaud|  | config
                                                          v  |
   12 V vehicle --> TVS --> ideal diode --> TPS54360 --> 5 V |  W25Q32
      (DB9 pin 9)     reverse + load dump       buck        |  flash
                                                    |       |
   USB-C  --> VBUS --> OR-ing --------------------->+       |
     |                                              |       |
     |                                    3.3V / 2.5V / 1.1V rails
     |                                       (sequenced)
     +--> FT2232H  ch.B UART  <-------------------------------+
                   ch.A JTAG  --> FPGA configuration
```

Two things in that diagram are the whole point of the board:

- **The isolation barrier runs between each transceiver and the FPGA**, not around the
  board as a whole, so the two channels never share a ground.
- **One FPGA sees both channels**, so one counter timestamps both. That is what makes
  cross-channel timing meaningful (FR-03).

---

## 2. Part selection and justification

| Function | Part | Why |
|---|---|---|
| FPGA | **LFE5U-25F-6TQFP144C** (Lattice ECP5) | See 2.1 |
| Isolated CAN-FD transceiver x2 | **TI ISO1042BDWV** | See 2.2 |
| Isolated supply driver x2 | **TI SN6501** + push-pull transformer | See 2.3 |
| USB bridge | **FTDI FT2232H** | See 2.4 |
| Configuration flash | **Winbond W25Q32JVSSIQ**, 32 Mbit SPI | Bitstream is 170 kB (measured, `ecppack` output); 32 Mbit leaves room for a golden image and a user image |
| System clock | **64.000 MHz XO, +/-25 ppm**, LVCMOS 3.3 V | See 2.5 and section 6 |
| Primary regulator | **TI TPS54360B**, 4.5-60 V in, 3.5 A | See 2.6 |
| Input protection | Bidirectional TVS + P-channel reverse-blocking FET | See 2.6 |

### 2.1 Why this FPGA, and why a TQFP and not a BGA

**Why an ECP5 at all** is fixed by constraint C-02: the toolchain must be open source so the
build stays reproducible in CI without a licence. That rules out Xilinx and Intel parts,
whose vendor tools cannot run unattended in a public CI job. It leaves Lattice iCE40 and
ECP5, both fully supported by Yosys and nextpnr.

**Why the 25F and not an iCE40.** This is decided by measurement, not by feel. The
synthesis report for the existing RTL gives:

```
TRELLIS_COMB:    3746 / 24288    15 %      (logic)
TRELLIS_FF:      3573 / 24288    14 %      (registers)
DP16KD:             2 /    56     3 %      (block RAM)
```

The largest iCE40 in the open flow, the UP5K, has 5 280 LUT4s. The design as it stands
would fill **71 %** of it before any of the additions this board is meant to allow — a
second FIFO, a timestamp discipline input, a filter block. It also has no 4 kB of block RAM
to spare in the same shape. The ECP5-25F sits at 15 % and leaves the board useful for more
than one revision of the logic.

**Why TQFP144 and not caBGA.** The ECP5-25F is available in caBGA256, caBGA381, csfBGA285
and TQFP144. Constraint C-03 requires a package a low-cost assembly service can build and,
in practice, one that escapes on four layers. A 381-ball 0.8 mm grid does not: escaping the
inner rows needs via-in-pad or more layers, which breaks both C-03 and MR-03.

TQFP144 provides **98 user I/O**. The design uses **8**. There is no reason to pay for a
BGA to leave 189 pins unused.

This is not assumed. The design was re-placed and re-routed for TQFP144 with a real pin
assignment, and the constraint file is committed as
`syn/ecp5_25f_tqfp144.lpf` in the logic repository:

```
Max frequency for clock 'clk': 84.60 MHz (PASS at 64.00 MHz)
pin assignment: clk -> 128, rst_n -> 1, can0_rx -> 10, can1_rx -> 11,
                uart_txd -> 102, led_act0 -> 103, led_act1 -> 104, led_ovf -> 105
```

**This closes Q-4.**

### 2.2 Isolated transceiver: ISO1042, closing Q-1

Q-1 asked whether to use an integrated isolated transceiver or a digital isolator plus a
standard transceiver. **Decision: the integrated part.**

The split approach needs, per channel, a digital isolator (ISO7721 class) plus a
transceiver (TCAN1044 class) plus the isolated supply. The integrated part replaces the
first two with one device and, more importantly, puts the barrier inside a component with a
**specified and certified** isolation rating rather than spread across a board layout I
would have to justify myself.

ISO1042 specifications against REQ-003, from the TI product data:

| Requirement | ISO1042 | Result |
|---|---|---|
| IR-02, isolation >= 2.5 kV RMS 1 min | **5 000 V RMS** withstand, 1 060 V RMS working | Pass, with reinforced margin |
| IR-02, bus fault >= +/-58 V | **-70 to +70 V** | Pass |
| FR-01, data phase to 5 Mbit/s | **5 Mbit/s** CAN FD | Pass, exactly at the limit |
| Automotive noise | **85 kV/us** common-mode transient immunity | See note |
| Temperature | -40 to +125 C | Pass |

The **DWV** package is chosen over DW. It is the 8-pin wide-body variant, which is the one
carrying the reinforced creepage and clearance; the extra width is what makes IR-03's 4 mm
achievable without fighting the layout.

The 85 kV/us CMTI figure matters more than it looks. The measurement this board exists to
make is between two buses whose grounds move relative to each other. Every volt of that
movement appears across the barrier as a common-mode transient, and a transceiver with poor
CMTI would corrupt data precisely during the events worth capturing.

**Note on FR-02 (receive only).** The ISO1042 has a TXD input. It is tied to its **recessive**
level on the isolated side and no signal is routed to it from the FPGA. The board therefore
cannot drive the bus, including the ACK slot, by construction rather than by firmware
convention. This is recorded in the schematic as a deliberate tie-off, not a floating pin.

### 2.3 Isolated supply: SN6501 and a transformer, closing Q-2

Q-2 asked how to power the isolated side. **Decision: a transformer driver, not a bought
DC-DC module.**

The obvious answer is a small isolated DC-DC module, and for many designs it would be right.
It is rejected here for one specific reason: most low-cost modules are specified as, for
example, "3 kVDC isolation" where that number is a **one-second production test**, not a
working voltage. IR-02 asks for a barrier rated for continuous working voltage, and a part
whose datasheet only quotes a momentary test figure cannot be used to claim it.

The chosen approach is a **TI SN6501** push-pull transformer driver with a centre-tapped
transformer, rectifier and a 5 V regulator on the isolated side. The transformer is then a
component with its own stated working isolation voltage, and the claim in IR-02 rests on a
datasheet figure rather than on optimism.

Per channel, the isolated side must supply:
- ISO1042 bus-side supply, 4.5 to 5.5 V
- the transceiver's own bus drive current, which for a receive-only node is only the
  recessive-state bias

**Open item, carried to Gate 2:** the exact transformer must be selected and its datasheet
committed to `docs/datasheets/`, confirming both the turns ratio for 5 V to 5 V and a
**continuous working** isolation voltage meeting IR-02. TI's SN6501 datasheet lists
recommended transformers; the candidate is a Wurth 750313370-class part, but this is not
treated as decided until the datasheet is in the repository, per MFR-03.

### 2.4 USB bridge: FT2232H, closing Q-5

Q-5 asked whether one device can carry both the data stream and the FPGA configuration path.
**Decision: yes, the FT2232H.**

The FT2232H is a dual-channel device:

- **Channel A in MPSSE mode** drives JTAG, which configures the ECP5 directly. This is what
  satisfies FR-08: a developer plugs in one USB cable and can load a bitstream with no
  separate programmer.
- **Channel B in asynchronous serial mode** carries the frame stream. It supports well above
  the 4 Mbaud of ER-07.

A single-channel FT232H could do either, but not both at once, which would mean unplugging a
cable to switch between programming and capturing. The extra few euro is worth removing that.

### 2.5 Clock

A **64.000 MHz crystal oscillator** at **+/-25 ppm**, LVCMOS 3.3 V output, feeding the ECP5
dedicated clock input (pin 128, `PCLKT0_0`).

64 MHz is not a free choice: it comes from the logic, which is constrained at 64 MHz because
that frequency divides exactly for both the 500 kbit/s nominal rate (128 clocks per bit) and
the 2 Mbit/s data rate (32 clocks per bit). See section 6 for why +/-25 ppm is sufficient
and a TCXO is not required.

An oscillator is used rather than a bare crystal plus the FPGA's internal oscillator circuit,
because the timestamp is only as good as its clock edge and a packaged XO has a specified
jitter figure that a crystal-and-inverter loop does not.

### 2.6 Power chain

| Stage | Part | Note |
|---|---|---|
| Input protection | Bidirectional TVS, 33 V standoff | Clamps ISO 7637-2 load dump energy |
| Reverse polarity | P-channel MOSFET ideal-diode | Lower drop than a Schottky, which matters at the 6 V end of ER-01 |
| 12 V to 5 V | **TPS54360B** | 4.5 to 60 V input. The 60 V rating is chosen against ER-01's 32 V continuous plus load-dump headroom above the TVS clamp |
| 5 V to 3.3 V | Buck or LDO | VCCIO, FT2232H, flash, oscillator |
| 3.3 V to 2.5 V | LDO | VCCAUX, low current |
| 3.3 V to 1.1 V | Buck | VCC core, the largest FPGA rail |

**Why 60 V for a 32 V requirement.** The TVS clamps the load dump, but it clamps to its
clamping voltage, not to 32 V. A 33 V standoff TVS clamps in the high forties under surge.
A regulator rated at 40 V would be inside its absolute maximum during exactly the event the
TVS is there to survive.

### Parts deliberately not used

| Part or approach | Why not |
|---|---|
| Xilinx Artix-7 or Intel Cyclone | Vendor toolchain cannot run in public CI without a licence; breaks C-02 and the reproducibility the logic repository is built around |
| iCE40 UP5K | 71 % full with the current design, no headroom for a second revision (2.1) |
| caBGA381 package | Cannot escape on four layers; breaks C-03 and MR-03 |
| A conventional CAN controller (MCP2518FD, as project 01) | It is the thing this board exists to replace: it cannot report when a frame arrived, only that it did |
| One shared isolation barrier for both channels | Ties the two bus grounds together through the instrument and injects the noise the board is meant to measure around (REQ-003 section 3) |
| Low-cost isolated DC-DC module | Isolation usually specified as a one-second test, not a working voltage (2.3) |
| Single-channel FT232H | Cannot stream and program at the same time (2.4) |
| On-board SD card | Out of scope: this board streams to a host. Standalone logging is project 02's job |

---

## 3. Power architecture and sequencing (ER-05)

The ECP5 constrains how its rails may come up. Both constraints below are quoted from
datasheets committed in `docs/datasheets/`, and both were checked in the PDF rather than
taken from a summary.

**Rail voltages** (ECP5 Family Data Sheet DS1044, Recommended Operating Conditions):

| Rail | Min | Max | Used here |
|---|---|---|---|
| VCC, core | 1.045 V | 1.155 V | 1.1 V |
| VCCAUX | 2.375 V | 2.625 V | 2.5 V |
| VCCIO | 1.14 V | 3.465 V | 3.3 V |

**Constraint 1, ordering** (ECP5 and ECP5-5G Hardware Checklist FPGA-TN-02038, section 4,
quoted in full because it is the whole of what the document says on the subject):

> VCCIO supplies should be powered up before or together with the VCC and VCCAUX supplies.

**Constraint 2, ramp rate** (DS1044, Recommended Operating Conditions, note 4):

> V_CCAUX ramp rate must not exceed 30 mV/us during power-up when transitioning between
> 0 V and 3 V.

Note what the first constraint does **not** say. It gives no required order between VCC and
VCCAUX, and it says "should", not "shall". A stricter ordering
(VCCIO then VCCAUX then VCC) is widely repeated in application notes and forum answers, but
it is not in either document committed here, so this design does not claim it as a
requirement. It does, however, **implement** that stricter order anyway, because doing so
costs one power-good gate and satisfies the documented constraint as a side effect. Meeting
a rule that might be stricter than the one written down is cheap; discovering the written
one was incomplete after fabrication is not.

The resulting topology:

```
  5 V ──> 3.3 V ──┬──> VCCIO (all banks, including the configuration bank 8)
   (first)        ├──> W25Q32 config flash
                  ├──> FT2232H, oscillator, LEDs
                  │
                  ├──> LDO ──> 2.5 V VCCAUX      (second, ramp < 30 mV/us)
                  │              │
                  │              └── power-good ──┐
                  │                               v
                  └──> buck ────────────────> 1.1 V VCC core  (last)
```

Three consequences for part selection:

1. **3.3 V comes up first and feeds both VCCIO and the configuration flash.** Sharing one
   rail between them removes any question of the FPGA trying to read a bitstream from a
   flash that is not yet alive. This is design reasoning, not a datasheet requirement.
2. **VCCAUX is an LDO from 3.3 V, deliberately not a switcher.** The 30 mV/us limit is a
   hard number, and an LDO's ramp is set by a soft-start capacitor that can be calculated
   and measured. A switcher's ramp is harder to hold to a slope.
3. **1.1 V is enabled last**, gated from the 2.5 V rail's power-good.

**To be measured at bring-up:** the actual ramps on a scope, confirming the order holds and
the VCCAUX slope is inside the limit. This is listed in the bring-up procedure rather than
assumed to follow from the schematic.

---

## 4. Power budget (ER-06, limit 3 W)

| Rail | Load | Current (est.) | Power |
|---|---|---|---|
| 1.1 V | ECP5 core, 15 % utilisation at 64 MHz | 150 mA | 0.17 W |
| 2.5 V | ECP5 VCCAUX | 20 mA | 0.05 W |
| 3.3 V | ECP5 VCCIO, 8 I/O | 20 mA | 0.07 W |
| 3.3 V | FT2232H | 50 mA | 0.17 W |
| 3.3 V | Oscillator, flash, LEDs | 40 mA | 0.13 W |
| 5 V | 2 x SN6501 isolated supplies, incl. transformer and rectifier losses | 2 x 60 mA | 0.60 W |
| | **Sub-total, loads** | | **1.19 W** |
| | Regulator losses, assume 85 % overall | | 0.21 W |
| | **Total from 12 V** | **~117 mA** | **~1.40 W** |

Against the 3 W limit of ER-06 this passes with roughly 2x margin.

**Honesty about the FPGA figure.** The 150 mA core estimate is the least certain number in
this table. FPGA static and dynamic power depends on utilisation, toggle rate and
temperature, and the proper way to get it is the Lattice Power Calculator with the real
design loaded. That has **not** been done. The estimate is scaled from published ECP5-25F
figures for a design of this size and clock rate. Even if it is wrong by a factor of two,
the total stays under 1.8 W and the budget still holds — which is why the design is not
blocked on it — but the figure should be replaced with a calculator result before the
regulator inductor and thermal design are finalised in Gate 2.

---

## 5. Link budget (ER-07)

The worst case of FR-06 is both channels saturated with back-to-back 64-byte CAN-FD frames
at 500 kbit/s nominal and 2 Mbit/s data.

```
  arbitration + control, ~30 bits at 500 kbit/s (2 us/bit)  =  60 us
  data + CRC, ~540 bits at 2 Mbit/s (0.5 us/bit)            = 270 us
  interframe and stuffing overhead, allow                   =  15 us
                                                    total   ~ 345 us per frame
```

One channel therefore produces about **2 900 frames/s**; two channels about **5 800/s**.
Each frame becomes a 79-byte packet (14-byte header + 64-byte payload + checksum), so:

```
  5 800 frames/s x 79 bytes  =  458 kB/s
```

At 8N1 the UART carries 10 bits per byte, so the link must exceed **4.6 Mbaud**.

**This does not fit the 4 Mbaud the logic is currently configured for.** The link is
adequate for one saturated channel (229 kB/s, 2.3 Mbaud) but not for two.

Three ways out, in order of preference:

1. **Raise the UART rate.** The FT2232H supports 12 Mbaud; the RTL's divisor is a port, not
   a generic, so the rate is a register change and a resynthesis. 8 Mbaud gives 800 kB/s and
   ample margin. This is the intended fix and costs nothing in hardware.
2. **Use the FT2232H's synchronous FIFO mode** instead of a UART, which reaches far higher
   throughput but requires new RTL and loses the "it is just a serial port" simplicity on
   the host.
3. Accept the overflow reporting of FR-07 and let the sustained-worst-case be a documented
   limit.

**Decision: option 1.** The board is laid out for it — the UART pair is routed as a normal
signal pair with a continuous reference, and no hardware choice forecloses 12 Mbaud. The
RTL change is one constant and a reverification run, tracked in the logic repository rather
than here.

This is the kind of thing a link budget exists to find, and it was found before the
schematic rather than during bring-up.

---

## 6. Clock and timestamp error budget (ER-02, ER-03, closing Q-3)

Q-3 asked whether a plain crystal oscillator meets ER-03 or whether a TCXO is required.
Answering it needs the error to be separated into the two kinds this board produces.

**Resolution and jitter.** The counter increments once per 64 MHz clock, so one count is
**15.625 ns**. The RTL samples that counter with the same logic that detects the
start-of-frame edge, so the uncertainty is one clock period, satisfying FR-04's "better than
100 ns" with a factor of six to spare.

**Error between the two channels: zero by construction.** Both channels latch the *same*
counter. Whatever the oscillator does, it does to both simultaneously. For the measurement
this board is built for — comparing an event on bus A with an event on bus B — the
oscillator's absolute accuracy cancels exactly. This is the single most important line in
this document, and it is the reason the block diagram has one clock and one counter.

**Error within a measured interval.** For an interval of length T, a frequency error of
*e* produces a timing error of *e x T*:

| Interval being measured | Error at +/-25 ppm | Error at +/-2 ppm (TCXO) |
|---|---|---|
| 1 ms gateway latency | **25 ns** | 2 ns |
| 100 ms | 2.5 us | 0.2 us |
| 1 s | 25 us | 2 us |
| 1 hour session, end to end | 90 ms | 7.2 ms |

The intervals this board is for are in the first two rows. A 25 ns error on a 1 ms latency
measurement is **smaller than the 15.6 ns resolution is coarse**, which is to say the
oscillator is not the limiting term at all.

**Decision: a +/-25 ppm XO. A TCXO is not justified.** A TCXO would only matter for
aligning this board's timestamps against an external absolute time reference over a long
session, which is explicitly out of scope in REQ-003 section 1.2. Fitting one would improve
a number nobody is reading.

**What is recorded as a limitation:** absolute timestamps drift by up to 90 ms over an hour,
so the stream's time base is a *relative* one. If a future revision needs wall-clock
alignment, the route is a discipline input — a PPS from GPS, or the vehicle's own time
sync — into the counter, not a better oscillator. The RTL's `can_timestamp` block already
has a `clear` input that such a discipline scheme would drive.

---

## 7. Pin allocation, checked against the logic

The FPGA side is not a fresh design; it must match the constraint file the logic is built
and timing-closed with. Checked against `syn/ecp5_25f_tqfp144.lpf`:

| Signal | TQFP144 pin | Direction | I/O standard | Board net |
|---|---|---|---|---|
| `clk` | 128 (`PCLKT0_0`) | in | LVCMOS33 | 64 MHz XO output |
| `rst_n` | 1 | in | LVCMOS33, pull-up | Reset button and power-good |
| `can0_rx` | 10 | in | LVCMOS33, pull-up | ISO1042 channel 0 RXD |
| `can1_rx` | 11 | in | LVCMOS33, pull-up | ISO1042 channel 1 RXD |
| `uart_txd` | 102 | out, 8 mA | LVCMOS33 | FT2232H channel B RXD |
| `led_act0` | 103 | out, 4 mA | LVCMOS33 | Activity LED, channel 0 |
| `led_act1` | 104 | out, 4 mA | LVCMOS33 | Activity LED, channel 1 |
| `led_ovf` | 105 | out, 4 mA | LVCMOS33 | Latched overflow LED |

Plus the pins the FPGA needs regardless of the design: JTAG (TCK, TMS, TDI, TDO) to the
FT2232H channel A, the configuration SPI to the W25Q32, `PROGRAMN`, `INITN`, `DONE`, and
the `CFG` mode pins strapped for SPI boot.

**Two things this check produced.**

1. **The pull-ups are a requirement, not a default.** `can0_rx` and `can1_rx` carry
   `PULLMODE=UP` in the constraint file. If a transceiver is unpowered or unfitted, its RXD
   floats, and a floating input into a CAN receiver reads as random dominant bits — which
   the logic would try to decode as frames. The pull-up forces the recessive, idle state.
   The same intent is duplicated on the board as a physical resistor, because relying on an
   FPGA configuration setting for a safe state means the input is unsafe for the whole
   interval between power-on and configuration being loaded.
2. **`rst_n` must not be held by the FPGA's own power-good alone.** The reset must be
   released only after configuration completes, so it is gated with `DONE` rather than with
   a rail comparator. Noted for the schematic.

---

## 8. Stackup (MR-03)

Four layers, 1.6 mm finished:

| Layer | Use |
|---|---|
| 1 | Signal, components, all high-speed routing |
| 2 | **Solid ground**, unbroken under every signal on layer 1 |
| 3 | Power planes, split by rail |
| 4 | Signal, low-speed and routing overflow |

The ground plane on layer 2 is continuous **on the host side only**. It stops at the
isolation barrier and does not cross it, on any layer. Each channel's bus-side ground is a
separate, local pour referenced to its own DB9 shell.

**The barrier is enforced by a design rule, not by care.** A keepout region is defined
across the barrier on all four layers, with a minimum clearance rule of 4 mm (IR-03), so
that any future edit that pours copper across it fails DRC rather than passing review.

No controlled-impedance requirement is imposed. The fastest signal on the board is the
64 MHz clock and the 8 Mbaud UART; neither has edge rates that make a 100 mm board a
transmission-line problem. The fabrication drawing will state the stackup but will not call
out an impedance spec, because specifying one that is not needed costs money at the
fabricator for nothing.

---

## 9. Cost check (C-01, budget 180 EUR)

Single-unit indicative prices, excluding PCB fabrication:

| Item | Qty | Unit | Total |
|---|---|---|---|
| LFE5U-25F-6TQFP144C | 1 | 28 | 28 |
| ISO1042BDWV | 2 | 5.50 | 11 |
| SN6501 + transformer + LDO, per channel | 2 | 6 | 12 |
| FT2232H | 1 | 7 | 7 |
| TPS54360B + inductor and passives | 1 | 6 | 6 |
| 3.3 V, 2.5 V, 1.1 V regulators and passives | 1 | 8 | 8 |
| W25Q32 flash | 1 | 1 | 1 |
| 64 MHz XO, +/-25 ppm | 1 | 3 | 3 |
| DB9 male, right angle | 2 | 2 | 4 |
| USB-C receptacle, TVS, FETs, LEDs, connectors | - | - | 12 |
| Passives, bulk | - | - | 10 |
| | | **Total** | **~102 EUR** |

Inside the 180 EUR budget with headroom for the transformer selection of 2.3 landing more
expensive than assumed.

---

## 10. Requirement traceability at architecture level

| Requirement | Where it is met | Status |
|---|---|---|
| FR-01 two CAN-FD channels to 5 Mbit/s | 2 x ISO1042, rated 5 Mbit/s | Met at the part, exactly at the limit |
| FR-02 receive only | ISO1042 TXD tied recessive, no FPGA path (2.2) | Met by construction |
| FR-03 shared time base | One FPGA, one counter (section 1, section 6) | Met, verified in RTL |
| FR-04 resolution < 100 ns | 15.625 ns at 64 MHz (section 6) | Met, 6x margin |
| FR-05 / FR-06 streaming both channels saturated | Link budget (section 5) | **Needs 8 Mbaud, not the 4 Mbaud currently in the RTL.** Hardware supports it; RTL change tracked |
| FR-07 report loss | Overflow bit in packet header | Met, implemented and tested in RTL |
| FR-08 configure over the same USB | FT2232H ch. A JTAG (2.4) | Met |
| FR-09 boot without a host | W25Q32 config flash, SPI boot straps | Met |
| FR-10 indicators | 3 LEDs on pins 103-105 | Met |
| IR-01 / IR-02 isolation | ISO1042 DWV, 5 kV RMS, +/-70 V bus (2.2) | Met with margin |
| IR-03 4 mm creepage | Wide-body package + DRC keepout (section 8) | Met by rule |
| IR-04 load dump and reverse | TVS + ideal diode + 60 V regulator (2.6) | Met |
| IR-05 separate bus grounds | Two barriers, two isolated supplies (section 1) | Met |
| ER-01 6-32 V | TPS54360B, 4.5-60 V | Met with load-dump headroom |
| ER-02 / ER-03 clock | 64 MHz, +/-25 ppm, budget in section 6 | Met, Q-3 closed |
| ER-05 sequencing | VCCIO before/with VCC and VCCAUX per FPGA-TN-02038 s.4; VCCAUX ramp < 30 mV/us per DS1044 (section 3) | Designed; to be measured at bring-up |
| ER-06 <= 3 W | ~1.4 W estimated (section 4) | Met, FPGA figure to be confirmed with the Power Calculator |
| ER-07 >= 4 Mbaud | FT2232H, 12 Mbaud capable | Met at the part; see FR-05 note |
| MR-03 4-layer | Stackup in section 8 | Met |
| C-01 180 EUR | ~102 EUR (section 9) | Met |
| C-02 open toolchain | ECP5, Yosys/nextpnr, already running in CI | Met |
| C-03 assemblable package | TQFP144, verified by re-running P&R (2.1) | Met, Q-4 closed |
| C-05 RTL is fixed | Pin map taken from the committed constraint file (section 7) | Met, with the one exception in FR-05 |

---

## 11. Open questions, and the decision taken on each

| ID | Question | Decision |
|---|---|---|
| **Q-1** | Integrated isolated transceiver, or isolator plus transceiver? | **Closed.** Integrated: ISO1042BDWV. Fewer parts and, more importantly, a certified barrier rather than one I would have to justify from layout geometry (2.2) |
| **Q-2** | How is the isolated side powered? | **Closed in approach, open in part.** SN6501 transformer driver, not a module, because module isolation ratings are usually a one-second test rather than a working voltage. The specific transformer is a Gate 2 selection with its datasheet to be committed (2.3) |
| **Q-3** | +/-50 ppm crystal or a TCXO? | **Closed.** A +/-25 ppm XO. Cross-channel error is zero by construction, and within-interval error at the timescales that matter is below the clock resolution. A TCXO would improve a number nobody reads (section 6) |
| **Q-4** | Which ECP5 device and package? | **Closed.** LFE5U-25F in TQFP144, verified by re-placing and re-routing the real design in that package at 84.6 MHz (2.1) |
| **Q-5** | One device for both streaming and configuration? | **Closed.** FT2232H: channel A JTAG, channel B serial (2.4) |
| **Q-6 (new)** | The link budget shows two saturated channels need 8 Mbaud, above the 4 Mbaud the RTL is built with. | **Open, but not blocking.** The hardware supports 12 Mbaud and nothing in the layout forecloses it. The change is one constant in the RTL plus a reverification run, tracked in the logic repository (section 5) |
| **Q-7 (new)** | The ECP5 core current estimate is not from the Lattice Power Calculator. | **Open.** Budget holds even at twice the estimate, so Gate 2 is not blocked, but the figure must be replaced before the regulator thermal design is fixed (section 4) |

---

## 12. What Gate 2 will do

1. Select the isolation transformer and commit its datasheet, closing Q-2 fully.
2. Run the Lattice Power Calculator on the real bitstream, closing Q-7.
3. Draw every symbol from the committed datasheets, per MFR-03.
4. Capture the schematic, sheet per functional block: power, FPGA and configuration,
   channel 0, channel 1, USB and indicators.
5. Define the isolation keepout and the 4 mm clearance rule in the PCB before any placement,
   so the barrier constrains the layout from the first component placed rather than being
   checked at the end.

---

## 13. Datasheets cited by this document

Per MFR-03, every figure quoted above comes from one of these, committed in
`docs/datasheets/`. Where a figure could not be traced to a committed document it is said
so in the text.

| Document | File | What is taken from it |
|---|---|---|
| TI ISO1042 | `ISO1042.pdf` | Isolation rating, bus fault range, 5 Mbit/s, CMTI, package variants (2.2) |
| TI SN6501 | `SN6501.pdf` | Transformer driver topology and recommended transformers (2.3) |
| TI TPS54360B | `TPS54360B.pdf` | 4.5-60 V input range, current rating (2.6) |
| Lattice ECP5 Family Data Sheet DS1044 | `Lattice-ECP5-Family-DS1044.pdf` | Rail voltages, VCCAUX 30 mV/us ramp limit (section 3) |
| Lattice ECP5 Hardware Checklist FPGA-TN-02038 | `Lattice-ECP5-Hardware-Checklist-FPGA-TN-02038.pdf` | Power sequencing statement (section 3) |

**Not yet committed, and therefore not yet decided:**

| Part | Why it is outstanding |
|---|---|
| Isolation transformer for the SN6501 | Q-2: the part must be chosen and its **continuous working** isolation voltage confirmed against IR-02, not a one-second test figure |
| FTDI FT2232H | Cited for 12 Mbaud capability and dual-channel operation (2.4, section 5). The claim is from FTDI product documentation; the datasheet download failed and must be retrieved before Gate 2 |
| Winbond W25Q32JV | Cited only for capacity, which the bitstream size comfortably fits. Retrieve for Gate 2 |
