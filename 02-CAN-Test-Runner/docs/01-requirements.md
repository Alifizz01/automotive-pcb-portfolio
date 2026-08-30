# CAN-FD Test Runner - Requirements Specification

| | |
|---|---|
| **Document** | REQ-002 |
| **Revision** | A |
| **Date** | 2026-08-29 |
| **Author** | Muhamad Izzuwan Alif |
| **Status** | Draft, open for review before Gate 1 |

---

> **Note on method.** The requirements and architecture for this board were developed in
> discussion with an AI assistant. Every figure in them is either derived in the document
> itself or taken from a cited datasheet, and the design decisions are mine.

## 1. Purpose and scope

Design a handheld device that connects to a vehicle's OBD-II port through an adapter
cable, runs a **test defined by the user** for the length of a drive or a bench session,
and ends with a verdict: **PASSED**, **FAILED**, or **INCOMPLETE**.

Existing loggers record and hope. This one is given a question before the session starts,
checks it continuously while recording, and answers it. The problem it solves is finding
out at the desk, hours later, that a capture was worthless, when the vehicle and the
conditions are no longer available.

The device carries its own rechargeable battery, charged from the vehicle while it is
plugged in. A test therefore **does not end when the ignition does**. The device keeps
watching the bus after key-off, through the ECU sleep sequence and overnight, which is
where a whole class of faults lives: parasitic drain, an ECU that refuses to sleep, and
something waking the bus at three in the morning.

The device is a test and diagnostics tool for bench, workshop and road use. It is not a
permanently installed telematics unit and it is not an ECU.

**In scope:** schematic, PCB layout, manufacturing data package, firmware, the test file
format, and the design documentation.

**Out of scope:** enclosure design, EMC certification, cellular or cloud upload, LIN and
FlexRay, production test fixture.

### 1.1 What a "test" is

A plain text file on the SD card that states what must be true. For example:

```
poll     22 F1 90    every 1000 ms    answer within 100 ms
range    SOC                          0 to 100 %
range    cell_voltage                 2.5 to 4.3 V
require  signal      pack_current     present for the whole session
quiet    bus 1                        no traffic from 22:00 to 06:00
```

The device transmits what the test tells it to, watches everything that comes back, and
grades the session against those rules.

---

## 2. Functional requirements

| ID | Requirement | Verification |
|---|---|---|
| **FR-01** | The device shall provide **two independent CAN-FD channels**, ISO 11898-1, arbitration to 1 Mbit/s and data to 5 Mbit/s. | Schematic review, bench test |
| **FR-02** | The device shall present each CAN channel on its own **DB9 connector with the CiA 303-1 pinout**, and shall take its power from **DB9 pin 9**. Connection to a vehicle OBD-II port shall be by adapter cable, not by a plug fixed to the device. | Layout review, vehicle test |
| **FR-03** | The device shall log every received frame to a removable SD card, with a timestamp, on both channels. | Bench test against injected traffic |
| **FR-04** | The device shall read a **test definition file** from the SD card at power-on, with no PC attached. | Bench test |
| **FR-05** | The device shall transmit the requests the test defines, at the cadence the test defines, including UDS requests on ISO 15765-2. | Bench test with a responding node |
| **FR-06** | The device shall evaluate the test rules **live during the session**, covering at least: response present, response within a time limit, decoded value inside a range, transmit cadence held, and a named signal present for the whole session. | Bench test with deliberately broken traffic |
| **FR-07** | The device shall show live session status on an **on-board display**: elapsed time, frames captured, rules passing, and the most recent failure. | Visual check |
| **FR-08** | The device shall end every session with a verdict of **PASSED**, **FAILED** or **INCOMPLETE**, shown on the display and written to the SD card as a readable report. | Bench test of all three outcomes |
| **FR-09** | The device shall flag a rule break **at the moment it happens**, visibly, and record the timestamp and the rule that broke. | Bench test |
| **FR-10** | The device shall detect loss of vehicle power, stop logging, close the log file and write the verdict before it dies. | Power interruption test, 50 repetitions |
| **FR-11** | The device shall hold absolute time across sessions with a battery-backed real-time clock. | Bench test over a power cycle |
| **FR-12** | The user shall be able to start and stop a session from the device itself, with no PC. | Visual check |
| **FR-13** | Log files shall be readable by existing tools without a custom viewer. | Open a produced file in asammdf |
| **FR-14** | Each log shall record the firmware version and an identifier of the test file used, so a result can be traced back to what produced it. | File inspection |
| **FR-15** | The device shall continue a running session on its **internal battery** when vehicle power is removed, for at least **12 hours**, and the transition shall not interrupt logging or lose a frame. | Runtime test, ignition-off during an injection test |
| **FR-16** | The device shall charge its internal battery from the vehicle while plugged in, and shall run from vehicle power while charging. | Bench test |
| **FR-17** | While on battery the device shall detect and log **bus wake-up events**: what woke the bus, when, and how long it stayed awake. | Bench test with a scheduled wake node |
| **FR-18** | The display shall show battery state and estimated remaining runtime, and the device shall end the session cleanly before the battery is exhausted. | Runtime test to depletion |
| **FR-19** | The device shall present the SD card to a host computer as a **USB mass storage device**, so logs and reports can be read and test files written without removing the card. | Plug into a PC, read and write files |
| **FR-20** | A session shall not run while the card is mounted over USB. Connecting USB shall **end the session cleanly** and write the verdict first. | Connect USB mid-session, inspect the log and report |
| **FR-21** | The device shall charge its cell from USB as well as from the vehicle, so it is usable on a bench with no vehicle attached. | Bench test |

## 3. Firmware requirements

New relative to project 01, where firmware was out of scope. These are the requirements
that decide whether the device is trustworthy.

| ID | Requirement | Verification |
|---|---|---|
| **SR-01** | The test file format shall be human readable and human editable in a text editor, and it shall be documented. | Format specification document |
| **SR-02** | The device shall not drop a frame at a sustained aggregate of **20 000 frames per second** across both channels. Raised from 10 000 at Gate 1, because two fully loaded CAN-FD channels carrying minimum-length frames produce roughly that, and a requirement a real bus can exceed is worse than none. | Injection test, compare transmitted and logged counts |
| **SR-03** | Writing to the SD card shall never block frame reception. Buffering shall absorb the worst-case card write latency. | Injection test during forced slow writes |
| **SR-04** | Timestamps shall be monotonic, with a resolution of **100 microseconds or better**, and shall never step backwards. | Log file analysis |
| **SR-05** | The device shall handle a missing card, a full card and a card removed mid-session without a lockup, and shall say so on the display. | Fault injection |
| **SR-06** | The verdict shall be written even when the session ends by power loss. | Same test as FR-10 |
| **SR-07** | Time from power-on to logging shall be **under 2 seconds**, so the ignition-on burst is not missed. | Measurement |
| **SR-08** | A malformed test file shall be rejected at startup with a readable error on the display, not accepted silently. | Fault injection with broken test files |
| **SR-09** | On battery, with the bus quiet, the firmware shall drop to a low-power watch state and wake on bus activity, so that FR-15 is met without logging hours of silence. | Current measurement, wake latency measurement |
| **SR-10** | INCOMPLETE shall record **why**: battery exhausted, card full, card removed, or stopped by the user. "Incomplete" with no reason is not acceptable. | Fault injection of each case |

## 4. Electrical requirements

| ID | Requirement | Verification |
|---|---|---|
| **ER-01** | The device shall operate from a nominal 12 V vehicle supply over the range **6 V to 32 V**, covering a cranking dip and a 24 V vehicle. | Bench supply sweep |
| **ER-02** | The input shall survive **reverse polarity** and shall clamp the ISO 7637-2 transients present on a vehicle rail. Certification is not claimed. | Schematic review, datasheet check |
| **ER-03** | With no session running and the internal battery full, current drawn from the vehicle shall be **under 1 mA**. The OBD-II port stays live on most vehicles, and the device must never flatten the car if it is left plugged in. | Measurement |
| **ER-14** | Every externally exposed line, both CAN pairs, the USB data pair and the supply, shall carry **ESD protection**. These connectors get handled in a workshop. | Schematic review, datasheet check |
| **ER-04** | Current drawn from the vehicle supply on DB9 pin 9 shall not exceed **500 mA** in any state, charging included. | Calculation, then measurement |
| **ER-05** | The device shall detect low battery and shut down cleanly with at least **60 seconds** of energy still in reserve, and shall hold up for **100 ms** if the cell is physically disconnected, so that a write in progress can always be closed. | Calculation, then measurement |
| **ER-06** | All logic shall be 3.3 V. Every IC shall have a decoupling capacitor of at least 100 nF within 5 mm of its supply pin. | Schematic and layout review |
| **ER-07** | Each CAN transceiver shall withstand a bus short to 12 V without damage. | Datasheet check |
| **ER-08** | The controller oscillator shall meet the CAN-FD frequency tolerance required by the controller, and the timebase shall be accurate to **30 ppm or better** so SR-04 holds over a long session. | Datasheet check, measurement |
| **ER-09** | The charger shall accept the full 6 V to 32 V input range and shall share the load, so the device runs from the vehicle while the cell charges. | Bench test across the input range |
| **ER-10** | Charging shall be **temperature qualified**. The device shall measure cell temperature and refuse to charge outside the range the cell datasheet allows. A car cabin reaches 60 to 70 C in summer and below 0 C in winter, and both ends are outside the charge window of common chemistries. | Schematic review, thermal chamber or oven test |
| **ER-11** | The cell shall be protected against over-voltage, under-voltage, over-current and short circuit, by a protection circuit that does not rely on firmware being alive. | Schematic review, fault injection |
| **ER-12** | Battery capacity shall give **at least 12 hours** in the low-power watch state of SR-09, and at least 2 hours logging continuously at full rate. Both figures shall be budgeted before the cell is chosen. | Calculation at Gate 1, measurement at Gate 4 |
| **ER-13** | The device shall report battery state of charge accurately enough to predict remaining runtime to within 20 %. | Runtime test against the prediction |

**Note on isolation.** Project 01 listed the lack of galvanic isolation as a limitation.
It is deliberately not a requirement here, and the reason is worth stating: this device
takes its power from the same connector as the bus it listens to, so it already shares the
vehicle ground. Isolating the transceivers while feeding them from vehicle power isolates
nothing. Isolation only becomes meaningful if the device is later powered separately, and
that is a rev B question, not a rev A one.

## 5. Mechanical requirements

| ID | Requirement | Verification |
|---|---|---|
| **MR-01** | The board and cell together shall fit a handheld enclosure no larger than **110 x 70 x 30 mm**. Grown from the original 90 x 60 x 25 mm to take the cell. | Measured in PCB, 3D view |
| **MR-02** | The display shall be readable with the device sitting on a seat or a bench at the end of its cable, not only when held up to the eye. | 3D view, vehicle fit check |
| **MR-03** | The SD card shall be removable without opening the enclosure or unplugging the device. | 3D view |
| **MR-04** | At least one user button shall be reachable with the device in place. | 3D view |
| **MR-08** | Both DB9 connectors and the USB connector shall be reachable without dismantling anything, and shall be labelled CH1 and CH2 on the enclosure. | 3D view |
| **MR-05** | Mounting holes shall suit an off-the-shelf enclosure chosen before layout starts. | Layout review against the chosen enclosure drawing |
| **MR-06** | The cell shall be retained mechanically, not held by its solder tabs, and shall be replaceable without cutting anything. | 3D view, physical check |
| **MR-07** | The cell shall sit away from the hottest parts on the board, and the temperature sensor of ER-10 shall measure the **cell**, not the board. | Layout review, thermal measurement |

## 6. Manufacturing requirements

| ID | Requirement | Verification |
|---|---|---|
| **MFR-01** | Four-layer board, 1.6 mm FR-4, 1 oz copper, with the stack-up documented. | Layer stack manager |
| **MFR-02** | Design shall respect a **4 mil / 4 mil** minimum trace width and clearance capability, enforced by design rules. | Design rules, DRC |
| **MFR-03** | Minimum drill 0.3 mm, minimum annular ring 0.15 mm. | Design rules, DRC |
| **MFR-04** | All components shall be currently orderable, with a named supplier and a stock figure recorded at design time. | BOM review |
| **MFR-05** | Passives shall be 0603 or larger. Fine-pitch parts are allowed only where no larger package exists. | BOM review |
| **MFR-06** | Silkscreen shall show designator, pin-1 and polarity marking, board name, revision, and the designer's name. | Layout review |
| **MFR-07** | Any net requiring controlled impedance shall be identified and its target impedance documented. | Layer stack, rules |

## 7. Deliverables

The design is complete when all of the following exist in the repository:

| ID | Deliverable |
|---|---|
| **D-01** | Schematic and PDF export, readable, with a filled title block |
| **D-02** | PCB layout |
| **D-03** | Documented design rule set, with a justification for each non-default value |
| **D-04** | DRC report showing zero violations, or a written waiver for each one |
| **D-05** | Gerber X2 and NC drill files, in a dated zip |
| **D-06** | BOM with MPN, supplier, supplier PN, quantity, unit price and extended price |
| **D-07** | Assembly drawing and pick-and-place file |
| **D-08** | 3D render of the assembled board |
| **D-09** | Firmware source, building from a documented toolchain with one command |
| **D-10** | Test file format specification |
| **D-11** | Evidence of a real test run: one PASSED, one FAILED and one INCOMPLETE session, with the log files and reports committed |
| **D-11b** | Measured battery runtime against the ER-12 budget, and a measured charge-inhibit test showing the device refusing to charge a hot cell |
| **D-14** | Mechanical assembly model: enclosure, board, cell and every volume part, with a collision check and the resulting board outline and keep-out drawing |
| **D-12** | `README.md`: what it does, key design decisions and why, traceability table, known limitations |
| **D-13** | Requirement verification table, every ID in sections 2 to 6 marked Pass, Fail or Waived, with evidence |

## 8. Constraints

- **C-01** Budget: 150 EUR for one prototype build including PCB fabrication and parts. Raised
  from 120 EUR to cover the charger, the protection circuit, the fuel gauge and the cell.
- **C-02** The board must be routable in four layers.
- **C-03** No unverified part enters the BOM. No datasheet means no part.
- **C-04** Firmware shall be developed and proven on an off-the-shelf development board with
  CAN-FD transceivers attached, **before** the custom PCB is ordered. Recorded MF4 logs from
  a real vehicle shall be replayed into it as test input.
- **C-05** The device shall be usable by someone who has not read the firmware source. If
  it needs a manual to run one test, it has failed.
- **C-06** The device gets left in a hot car. No charging decision may depend on firmware
  behaving correctly, and no single component failure may allow a cell to be charged
  outside its rated temperature window.

## 9. Acceptance

Design review at four gates. Nothing proceeds past a gate without sign-off.

1. **Gate 1, architecture.** Part selection justified, block diagram, power budget, test
   file format sketched, **cell chemistry chosen with the temperature argument written
   down**, and the runtime budget of ER-12 calculated.
2. **Gate 1.5, mechanical integration.** Enclosure chosen and its drawing obtained. A 3D
   model for every part with real volume: cell and holder, display, SD socket, OBD-II
   plug, buttons, connectors. Those models assembled against the enclosure and checked
   for collision. The gate closes when the **board outline, the mounting holes and every
   keep-out are fixed numbers**, not intentions. Passives are not modelled individually.
3. **Gate 2, schematic.** Full schematic, ERC clean, every requirement in sections 2 to 4
   traceable to a net or a part.
4. **Gate 3, layout and release.** DRC clean, all hardware deliverables present, and the
   populated board checked back against the Gate 1.5 assembly.
5. **Gate 4, firmware and proof.** Firmware meeting section 3, and the three demonstrated
   sessions required by D-11.

---

*Anything ambiguous in here gets written down as a question in the Gate 1 document and
answered before layout starts. An ambiguity left unresolved turns into a respin, and this
time it can also turn into a test result nobody can trust.*
