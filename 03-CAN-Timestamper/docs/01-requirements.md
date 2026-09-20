# CAN-FD Hardware Timestamper - Requirements Specification

| | |
|---|---|
| **Document** | REQ-003 |
| **Revision** | A |
| **Date** | 2026-09-20 |
| **Author** | Muhamad Izzuwan Alif |
| **Status** | Draft, open for review before Gate 1 |

---

> **Note on method.** The requirements and architecture for this board were developed in
> discussion with an AI assistant. Every figure in them is either derived in the document
> itself or taken from a cited datasheet, and the design decisions are mine.

## 1. Purpose and scope

Design a two-channel CAN-FD capture board that timestamps every frame **in hardware, at
the frame's first edge**, and streams the result to a host over USB.

The protocol is decoded inside an FPGA rather than by an off-the-shelf CAN controller.
The receiver RTL already exists, is simulated, synthesised and timing closed, and lives in
a separate repository: [fpga-can-timestamper](https://github.com/Alifizz01/fpga-can-timestamper).
**This document specifies the board that RTL runs on.** The division is deliberate: the
logic is verified on its own before any copper is committed to it.

### 1.1 The problem this solves

Projects 01 and 02 in this portfolio both log CAN with a conventional controller: an
MCP2518FD over SPI on the Pi HAT, and the STM32H563's internal FDCAN on the test runner.
Both share a limit that firmware cannot remove.

A CAN controller tells you that a frame arrived. It does not tell you **when** it arrived.
The timestamp is applied when the host gets round to servicing the interrupt, so it carries
the interrupt latency, the SPI transfer and the scheduler with it. On a quiet bus this is
invisible. On a busy bus it is tens of microseconds, and — this is the part that matters —
the error grows exactly when the bus is busy, which is exactly when the measurement is
interesting.

That is acceptable for reading signal values. It is not acceptable for these questions:

- **Which of these two messages came first?** Two frames a few hundred microseconds apart
  can be reordered by a logger whose jitter is larger than the gap.
- **How long did the gateway take to forward that frame?** Measuring a gateway's latency
  means subtracting two timestamps taken on two different buses. If each carries independent
  jitter, the answer is noise.
- **Did this ECU respond inside its deadline?** A 10 ms deadline measured with 50 us of
  uncertain jitter is a measurement with a 0.5 % error that cannot be characterised.

Putting the receiver in fabric means a counter is sampled by the same logic that sees the
start-of-frame edge. The uncertainty becomes one clock period instead of one interrupt.

### 1.2 In and out of scope

**In scope:** schematic, PCB layout, manufacturing data package, the board's power and
isolation design, bring-up procedure, and this documentation set. The FPGA logic is
already complete and is treated here as a fixed input with known pin and clock needs.

**Out of scope:** enclosure, EMC certification, LIN and FlexRay, cellular upload, a
production test fixture, and any transmit capability (see FR-02).

---

## 2. Functional requirements

| ID | Requirement | Verification |
|---|---|---|
| **FR-01** | The board shall provide **two independent CAN-FD channels**, ISO 11898-1, supporting arbitration rates to 1 Mbit/s and data phase rates to 5 Mbit/s. | Schematic review; bench test against a known-good CAN-FD node |
| **FR-02** | The board shall be **receive only**. It shall not drive the CAN bus, including the ACK slot. | Schematic review: no TXD path from the FPGA to either transceiver |
| **FR-03** | Every accepted frame shall be timestamped from a **single counter shared by both channels**, so that timestamps from the two channels are directly comparable with no inter-channel offset. | RTL already verified; board test with one source fanned out to both channels |
| **FR-04** | Timestamp resolution shall be **better than 100 ns**, and timestamp jitter relative to the start-of-frame edge shall be **no more than one system clock period**. | Derived from the clock (ER-02); bench test against a pulse generator |
| **FR-05** | The board shall stream decoded frames to a host over **USB**, sustaining the worst-case frame rate of FR-06 without loss. | Bandwidth calculation in the architecture document; soak test |
| **FR-06** | The board shall sustain **both channels simultaneously loaded** with back-to-back 64-byte CAN-FD frames at 500 kbit/s nominal / 2 Mbit/s data, with no dropped frames. | Soak test with two traffic generators |
| **FR-07** | If a frame is nonetheless lost, the board shall **report the loss** in the stream rather than dropping it silently. | Already implemented as the overflow bit in the packet header; bench test by deliberately starving the link |
| **FR-08** | The same USB connection shall also **configure the FPGA**, so that no separate programmer is needed for development. | Bring-up: load a bitstream over USB with no other hardware attached |
| **FR-09** | The board shall hold its configuration in **non-volatile memory** and start capturing without a host after power-on. | Power-cycle test with the host disconnected |
| **FR-10** | The board shall indicate, without a host: power good, per-channel activity, and a latched overflow condition. | Visual check |

---

## 3. Isolation and protection requirements

These exist because the board is intended to be clipped onto a vehicle bus, which is an
electrically hostile place, and connected at the same time to a laptop, which is not.

| ID | Requirement | Verification |
|---|---|---|
| **IR-01** | Each CAN channel shall be **galvanically isolated** from the host side of the board and from the other channel. | Schematic review; isolation barrier continuity check |
| **IR-02** | The isolation barrier shall withstand at least **2.5 kV RMS for 1 minute**, and each transceiver shall be rated for a bus fault voltage of at least **+/-58 V**. | Datasheet citation; layout review of creepage and clearance |
| **IR-03** | Creepage and clearance across the barrier shall be **at least 4 mm**, with no copper, silkscreen, or solder mask bridging pour beneath it. | Layout review; DRC rule with a keepout region |
| **IR-04** | The vehicle supply input shall survive a **load dump** and reverse polarity without damage. | Component rating review against ISO 7637-2 pulse levels |
| **IR-05** | Each CAN channel shall be independently referenced to **its own bus ground**, taken from the connector, not shared with the other channel. | Schematic review |

**Why per-channel isolation and not one shared barrier.** The obvious saving is to put both
channels behind one isolation barrier and share an isolated supply. That is wrong for the
use this board is for. The interesting measurement is between two *different* buses, which
in a vehicle frequently sit on different grounds that can be volts apart under load. Tying
them together through the logger creates a ground loop through the measurement instrument
and injects exactly the noise the board exists to measure around. Two barriers cost a second
isolated supply; sharing one costs the measurement.

---

## 4. Electrical requirements

| ID | Requirement | Verification |
|---|---|---|
| **ER-01** | The board shall operate from a **nominal 12 V vehicle supply**, over a continuous range of 6 V to 32 V. | Bench test across the range |
| **ER-02** | The FPGA system clock shall be **64 MHz**, matching the RTL's timing constraints, giving 15.6 ns timestamp resolution. | Oscillator datasheet; RTL constraint file `syn/ecp5_25f_cabga381.lpf` |
| **ER-03** | The system clock source shall have a frequency stability of **+/-50 ppm or better** over -40 to +85 C, and the resulting timestamp error shall be stated in the architecture document. | Datasheet citation; error budget in Gate 1 |
| **ER-04** | The board shall be powered **either** from the vehicle **or** from USB, with automatic selection and no back-feed between the two. | Bench test with both connected and each alone |
| **ER-05** | The FPGA supply rails shall be brought up in the **order the FPGA datasheet requires**, and the sequencing shall be shown in the architecture document. | Datasheet citation; bench measurement with a scope |
| **ER-06** | Total board power from the vehicle shall not exceed **3 W**. | Power budget in Gate 1; bench measurement |
| **ER-07** | The USB link shall sustain at least **4 Mbaud**, the rate the RTL's UART is configured for. | Link budget in Gate 1; throughput test |

---

## 5. Mechanical requirements

| ID | Requirement | Verification |
|---|---|---|
| **MR-01** | The board shall be no larger than **100 x 80 mm**, so it fits the cheapest prototype panel tier. | Layout review |
| **MR-02** | Each CAN channel shall be presented on its own **DB9 connector with the CiA 303-1 pinout**, matching projects 01 and 02 so the same cables work. | Layout review |
| **MR-03** | The board shall use a **4-layer stack**, with a continuous reference plane under every signal that crosses the board. | Stackup definition in Gate 2; layout review |
| **MR-04** | Mounting shall be four M3 holes, with keepout for washer and screw head. | Layout review |

---

## 6. Manufacturing requirements

| ID | Requirement | Verification |
|---|---|---|
| **MFR-01** | All parts shall be available from a mainstream distributor at the time of design, with a cited order code. | BOM review |
| **MFR-02** | The design shall be manufacturable to a standard low-cost 4-layer process: minimum track and gap 0.127 mm, minimum drill 0.2 mm. | DRC against the chosen fabricator's rules |
| **MFR-03** | Every symbol and footprint shall be drawn from the manufacturer's datasheet, not taken from a vendor library. | Library review, as in projects 01 and 02 |
| **MFR-04** | The output package shall include Gerbers, NC drill, pick and place, a BOM with order codes, and a fabrication drawing stating the stackup and impedance. | Output job review |

---

## 7. Deliverables

1. This requirements specification.
2. Gate 1 architecture document: block diagram, part selection with justification, power
   architecture and budget, isolation strategy, clock and timestamp error budget, pin
   allocation checked against the RTL constraint file, and a cost check.
3. Schematic, with every symbol drawn from a datasheet.
4. PCB layout, 4 layers, DRC clean, with the isolation barrier enforced by a design rule.
5. Manufacturing data package as MFR-04.
6. Bring-up procedure: the order in which rails, clock, configuration and channels are
   brought up, and what to measure at each step.

---

## 8. Constraints

| ID | Constraint |
|---|---|
| **C-01** | Bill of materials target **180 EUR** for a single prototype build, excluding PCB fabrication. |
| **C-02** | The FPGA shall be one supported by an **open-source toolchain**, so the build remains reproducible in CI without a licence. This is already true of the RTL and must stay true. |
| **C-03** | The FPGA shall be available in a package that can be assembled by a **standard low-cost assembly service**, which in practice means no package requiring blind or buried vias to escape. |
| **C-04** | The board shall reuse the DB9 pinout, connector family and CAN termination approach of projects 01 and 02, so cables and test fixtures are shared. |
| **C-05** | The RTL is a **fixed input**. The board shall satisfy its clock frequency, pin count and I/O standard rather than the RTL being changed to suit the board. Any change to the RTL must be justified and reverified in its own repository. |

---

## 9. Acceptance

The board is accepted when all of the following hold.

| ID | Acceptance criterion |
|---|---|
| **AC-01** | A bitstream loads over USB with no external programmer (FR-08) and runs from configuration flash after a power cycle (FR-09). |
| **AC-02** | Frames injected on either channel by a known-good CAN-FD node are decoded and streamed with correct identifier, length and payload (FR-01, FR-05). |
| **AC-03** | A single square-wave source fanned out to both channels produces timestamps on the two channels that agree to within one clock period (FR-03, FR-04). |
| **AC-04** | Both channels loaded to the worst case of FR-06 for 30 minutes produce no overflow indication (FR-06, FR-07). |
| **AC-05** | The isolation barrier passes a continuity check: no DC path between either bus ground and host ground (IR-01). |
| **AC-06** | Measured board power from a 12 V supply is at or below the ER-06 limit. |
| **AC-07** | The manufacturing package passes the fabricator's own design-for-manufacture check with no rule violations (MFR-02, MFR-04). |

---

## 10. Open questions carried into Gate 1

| ID | Question |
|---|---|
| **Q-1** | Integrated isolated transceiver, or digital isolator plus standard transceiver? The integrated part is fewer components and a cleaner barrier; the split version is cheaper and gives a free choice of transceiver. Decide in Gate 1 with a cost and part-count comparison. |
| **Q-2** | How is the isolated side of each channel powered? A transformer driver with a discrete transformer and regulator, or a bought isolated DC-DC module. Decide in Gate 1 against C-01 and the isolation rating of IR-02. |
| **Q-3** | Is a plain +/-50 ppm crystal oscillator good enough for ER-03, or does the timestamp error budget force a TCXO? Requires the error budget to be written before it can be answered. |
| **Q-4** | Which ECP5 device and package meets C-03 while leaving headroom above the measured 15 % logic utilisation? |
| **Q-5** | Does the USB bridge carry both the data stream and the FPGA configuration path (FR-08), and if so which device provides both? |
