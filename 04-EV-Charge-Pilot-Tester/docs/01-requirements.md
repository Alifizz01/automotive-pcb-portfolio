# EV Charge Pilot Tester - Requirements Specification

| | |
|---|---|
| **Document** | REQ-004 |
| **Revision** | A |
| **Date** | 2026-10-05 |
| **Author** | Muhamad Izzuwan Alif |
| **Status** | Draft, open for review before Gate 1 |

---

> **Note on method.** The requirements for this board were developed in discussion with an AI
> assistant. Every figure in them is either derived in the document itself or taken from a cited
> source, and the design decisions are mine.

## 1. Purpose and scope

Before an AC charging session delivers any energy, the charger and the vehicle hold a conversation on
two signal wires of the Type 2 connector. On the **control pilot (CP)** the charger sends a ±12 V, 1 kHz
PWM signal, and the vehicle answers by loading that line with resistors. The voltage level says what state
the vehicle is in, and the duty cycle says how much current the charger allows. On the **proximity pilot
(PP)** a resistor inside the cable tells both sides how much current the cable can carry. Almost every
"the car will not charge" fault in the field is a fault in this conversation, not in the power path.

This device takes part in that conversation and measures it. It can play **either side**:

- **As a charger (EVSE role):** it drives the CP line exactly as a charging station would, and reads back
  how a real vehicle, or a vehicle simulator, responds.
- **As a vehicle (EV role):** it loads the CP line exactly as a vehicle would, steps through the charging
  states, and measures what a real charging station sends.

In both roles it can **inject faults on purpose**: a missing diode, a shorted line, resistances just inside
and just outside tolerance, and invalid duty cycles. A charger or vehicle under test has to react to those
correctly, and that reaction is what a test engineer needs to see.

Every measurement is streamed over USB, and the current state is published on **CAN-FD**, so the CAN-FD
Test Runner (project 02) can grade a whole charging session automatically.

**In scope:** schematic, PCB layout, manufacturing data package, firmware, a USB command and streaming
protocol, the design documentation, and a **built and measured prototype**.

**Out of scope:**
- the power path: no mains voltage, no contactors, no current measurement on the charging conductors
- high-level communication: ISO 15118 / HomePlug Green PHY on the CP line. The 5 % duty cycle that requests it is *detected and reported*, nothing more
- DC charging (CCS), the Type 1 connector, an enclosure, and certification

### 1.1 The signals this device must reproduce

These numbers define the design. Their sources are listed in section 10.

**Control pilot circuit.** The EVSE drives ±12 V at 1 kHz through a **1 kΩ** source resistor. The vehicle
puts a diode in series with a load to protective earth (PE), and switches resistors into that load:

| State | Meaning | Vehicle load, CP to PE | CP high level |
|---|---|---|---|
| A | No vehicle connected | open | +12 V |
| B | Vehicle connected, not ready | 2.74 kΩ | +9 V ± 1 V |
| C | Ready, charging | 2.74 kΩ ∥ 1.3 kΩ = 882 Ω | +6 V ± 1 V |
| D | Ready, ventilation required | 2.74 kΩ ∥ 270 Ω = 246 Ω | +3 V ± 1 V |
| E | No power, or CP shorted to PE | short | 0 V |
| F | EVSE fault or not available | (driven by the EVSE) | −12 V |

The low level of the PWM stays at −12 V in states B to D, because the vehicle's diode blocks the negative
half. A low level that is not −12 V therefore means the diode is missing or shorted, and an EVSE checks for
that. This is why fault FI-01 exists.

*Check of the table, as a worked example:* in state B, with a diode drop of about 0.7 V, the high level is
0.7 V + (12 V − 0.7 V) × 2.74 kΩ / (1 kΩ + 2.74 kΩ) ≈ **9.0 V**, inside the 9 V ± 1 V band.

**Duty cycle to permitted current:**

| Duty cycle D | Meaning |
|---|---|
| 3 % to 7 % (nominal 5 %) | High-level communication requested (ISO 15118); no PWM current limit |
| 8 % to below 10 % | 6 A |
| 10 % to 85 % | I = D × 0.6 A, so 6 A at 10 % up to 51 A at 85 % |
| above 85 % to 96 % | I = (D − 64) × 2.5 A, up to 80 A |
| above 96 % to 97 % | 80 A |
| anything else (below 3 %, above 7 % and below 8 %, above 97 %) | Not a valid current offer |

The band edges are as given by S-3, and are to be confirmed against S-1 (Q-02).

**Proximity pilot (cable coding).** A resistor between PP and PE in the cable plug:

| Cable rating | Resistor |
|---|---|
| 13 A | 1.5 kΩ |
| 20 A | 680 Ω |
| 32 A | 220 Ω (see Q-01) |
| 63 A three-phase / 70 A single-phase | 100 Ω |

---

## 2. Functional requirements

| ID | Requirement | Verification |
|---|---|---|
| **FR-01** | The device shall operate in **EVSE role** or **EV role**, selected by command. The role shall be shown on the board at all times, and no output shall be driven during a role change. | Bench test, visual check |
| **FR-02** | In EVSE role the device shall generate the CP signal: **+12 V / −12 V at 1 kHz** through a **1 kΩ ± 1 %** source resistor, with the duty cycle settable from **0 % to 100 % in steps of 0.1 %**, and a static +12 V (state A offer) and −12 V (state F). | Oscilloscope measurement |
| **FR-03** | In EVSE role the device shall measure the CP high and low levels every PWM period and classify the vehicle state A to F using the bands of section 1.1, reporting the measured voltage alongside the state. | Bench test against FR-05 in a second unit, and against fixed resistors |
| **FR-04** | In EVSE role the device shall measure the **PP to PE resistance** and report the cable rating it encodes, or "invalid" for a value outside every band. | Bench test with resistors at each nominal value and at ±3 % |
| **FR-05** | In EV role the device shall load the CP line through a diode with switchable **2.74 kΩ, 1.3 kΩ and 270 Ω** resistors (all ± 1 %), to present states A, B, C and D on command. | Measurement of the presented load |
| **FR-06** | In EV role the device shall measure the incoming CP signal every period: **high level, low level, frequency and duty cycle**, and decode the permitted current with the formulas of section 1.1. | Bench test against FR-02 in a second unit, and against a real charging station |
| **FR-07** | In EV role the device shall present a **PP cable-coding resistor** selectable from 1.5 kΩ, 680 Ω, 220 Ω and 100 Ω, or open. | Measurement |
| **FR-08** | In EV role the device shall step through a **scripted charging sequence** (for example A, then B, wait for a valid PWM, then C, then B, then A) and record when each transition happened and how the counterpart reacted, with timing resolution of **1 ms**. | Bench test against a real charging station, log inspection |
| **FR-09** | The device shall inject the faults of section 3 on command, in either role where they apply, and record the counterpart's reaction. | Fault injection tests, one per fault |
| **FR-10** | The device shall stream every measurement over **USB** as text lines that a terminal or a script can read, and accept commands the same way. The protocol shall be documented. | Protocol document, scripted test |
| **FR-11** | The device shall publish its role, the CP state, the measured levels, the duty cycle, the decoded current, the PP rating and any active fault on **CAN-FD** at 10 Hz and on every change, in a documented layout with a DBC file. | Bus capture, decode with the DBC |
| **FR-12** | The device shall show the CP state, the role and a fault indication on **LEDs** visible from 1 m, so it is usable with no PC attached. | Visual check |
| **FR-13** | The device shall run a stored **self-test** with its two halves connected to each other (EVSE output looped into EV input), covering every state and every fault, and report pass or fail. | Self-test run, inspection of the report |

## 3. Fault injection

These faults are the point of the device. Each one is something a real installation or a real vehicle gets
wrong, and each must be selectable on its own.

| ID | Fault | Role | What a correct counterpart does |
|---|---|---|---|
| **FI-01** | **Diode missing** (diode bypassed, so the low level rises from −12 V) | EV | EVSE refuses to proceed, and should signal state F |
| **FI-02** | **CP shorted to PE** | both | Both sides recognise state E, and no charging proceeds |
| **FI-03** | **CP open** after charging has started | EV | EVSE treats it as disconnection and stops the PWM |
| **FI-04** | **Vehicle resistance at the edge of tolerance**: high level placed just inside and just outside each 1 V band | EV | EVSE accepts inside, rejects outside |
| **FI-05** | **Duty cycle at and beyond every band edge**: 0 %, 2 %, 3 %, 7 %, 7.5 %, 8 %, 10 %, 85 %, 96 %, 97 %, 98 %, 100 % | EVSE | Vehicle decodes each valid offer as section 1.1 says, and draws no current on an invalid one |
| **FI-06** | **Duty cycle step during charging**, for example 32 A to 6 A | EVSE | Vehicle reduces current within the time the standard allows (see Q-03) |
| **FI-07** | **Frequency off nominal**: settable from 900 Hz to 1100 Hz | EVSE | Vehicle accepts frequencies inside the tolerance of S-1 and rejects those outside (tolerance to be confirmed, Q-06) |
| **FI-08** | **PP resistance invalid or open**, and the PP value changing during a session | EV | EVSE refuses, or stops |
| **FI-09** | **Abrupt state C to A**, imitating a cable pulled under load | EV | EVSE stops the PWM and reports it |

## 4. Firmware requirements

| ID | Requirement | Verification |
|---|---|---|
| **SR-01** | Level measurement shall sample the high and low plateau of each PWM period away from the edges, so that the rise time of a long cable does not corrupt the reading. | Measurement with an added 10 m cable capacitance |
| **SR-02** | A state change shall be classified within **2 PWM periods** and reported within **5 ms**. | Timed bench test |
| **SR-03** | State classification shall use **hysteresis** at each band edge, so a level sitting on a boundary does not chatter. The hysteresis value shall be documented. | Bench test at each band edge |
| **SR-04** | Every logged event shall carry a monotonic timestamp with **1 ms** resolution or better. | Log analysis |
| **SR-05** | On loss of USB the device shall return to a **safe state**: EVSE role at static +12 V (state A), EV role with all loads open. | Unplug test in each role |
| **SR-06** | A malformed command shall be rejected with a readable error, never half-executed. | Fault injection on the USB protocol |
| **SR-07** | Firmware version and serial number shall be reported on request and included in every log header. | Inspection |

## 5. Electrical requirements

| ID | Requirement | Verification |
|---|---|---|
| **ER-01** | The device shall run from **USB-C at 5 V**, drawing no more than **500 mA**, with the ±12 V rails generated on the board. | Measurement |
| **ER-02** | The EVSE output shall hold **+12 V ± 0.4 V and −12 V ± 0.4 V** unloaded, the tolerance of the source being emulated. | Measurement |
| **ER-03** | The PWM edges shall rise and fall in **under 10 µs** into the state-D load, so that the duty cycle offer stays accurate to 0.1 %. | Oscilloscope measurement |
| **ER-04** | CP level measurement shall be accurate to **±0.1 V** across ±13 V, a tenth of the narrowest band, so that FI-04 can place a level just inside or just outside a band. | Calibration against a reference meter |
| **ER-05** | Duty cycle measurement shall be accurate to **±0.1 %**, and frequency to **±0.5 %**. | Measurement against a signal generator |
| **ER-06** | PP resistance measurement shall be accurate to **±1 %** from 50 Ω to 5 kΩ, which distinguishes ±3 % cable tolerances. | Measurement against reference resistors |
| **ER-07** | The CP and PP inputs shall survive a **continuous ±15 V** applied by mistake, and carry ESD protection. | Schematic review, datasheet check |
| **ER-08** | Resistor switching for states and faults shall use parts that are **open when unpowered**, so a device losing power presents state A, never a stale state C. | Schematic review, power-off measurement |
| **ER-09** | The CAN-FD interface shall withstand a bus short to 12 V, as on project 02. | Datasheet check |
| **ER-10** | The PE reference of the CP/PP connector shall be the board's measurement ground, and that ground shall be **isolated from the USB ground** by at least **1 kV**, so that a laptop never shares earth with a charging station's PE. | Schematic review, isolation test |

**Note on safety.** The device only ever touches CP, PP and PE. But a charging station closes its contactor
when it sees state C, which puts **mains voltage** on the L and N pins of the plug the device is connected to.
The device therefore never connects to a station through a full Type 2 inlet with live pins. It connects through
a **CP/PP breakout adapter** that brings out only CP, PP and PE, and the EV role refuses to present state C
unless the adapter type has been confirmed by command. This is requirement **ER-11** below, not a footnote.

| ID | Requirement | Verification |
|---|---|---|
| **ER-11** | The EV role shall not present state C or D until the user has confirmed, by an explicit command each power-up, that the connection is a CP/PP/PE-only adapter. | Bench test of the interlock |

## 6. Mechanical requirements

| ID | Requirement | Verification |
|---|---|---|
| **MR-01** | The board shall be no larger than **100 x 60 mm**. | Measured in PCB |
| **MR-02** | CP, PP and PE shall be brought out on a **4 mm safety banana socket** each, to suit standard test leads and commercial breakout adapters, and on a test header for the self-test loop of FR-13. | 3D view |
| **MR-03** | The isolation barrier of ER-10 shall be visible on the board as a keep-out slot or gap, with no copper crossing it. | Layout review |
| **MR-04** | Four mounting holes, M3. | Layout review |

## 7. Manufacturing requirements

| ID | Requirement | Verification |
|---|---|---|
| **MFR-01** | Two-layer board, 1.6 mm FR-4, 1 oz copper. | Layer stack |
| **MFR-02** | Design rules within a standard low-cost prototype process: 6 mil / 6 mil, 0.3 mm drill. | Design rules, DRC |
| **MFR-03** | All components currently orderable, with supplier and stock recorded at design time, and **assembly-service compatible** where possible, so the prototype can be ordered assembled. | BOM review |
| **MFR-04** | Passives 0603 or larger. | BOM review |
| **MFR-05** | Silkscreen shall mark CP, PP, PE, the isolation barrier, the board name, the revision, and "NO MAINS - CP/PP/PE ONLY". | Layout review |

## 8. Deliverables

| ID | Deliverable |
|---|---|
| **D-01** | Schematic and PDF export with a filled title block |
| **D-02** | PCB layout, design rule set with justifications, DRC report with zero violations or written waivers |
| **D-03** | Gerber X2, NC drill, BOM, pick-and-place, assembly drawing, 3D render |
| **D-04** | Firmware source, building with one documented command |
| **D-05** | USB protocol specification and the CAN-FD DBC file |
| **D-06** | **Measurement report from the built board**: CP levels and edges on an oscilloscope, duty cycle accuracy, PP accuracy, the self-test result, and at least one session against a real charging station in EV role |
| **D-07** | `README.md`: what it does, decisions and why, traceability table, known limitations |
| **D-08** | Requirement verification table, every ID marked Pass, Fail or Waived, with evidence |

## 9. Constraints

- **C-01** Budget: **80 EUR** for one assembled prototype including PCB fabrication and parts.
- **C-02** Two layers.
- **C-03** No unverified part enters the BOM. No datasheet means no part.
- **C-04** Firmware shall be developed and proven on an off-the-shelf development board with the CP circuit built on a breadboard **before** the PCB is ordered.
- **C-05** Unlike projects 01 to 03, this board **shall be built and measured**. D-06 is not optional; it is the reason the board exists.
- **C-06** No requirement may be met by a part of the device touching mains voltage, now or in a later revision.

## 10. Sources

| Ref | Source | Used for |
|---|---|---|
| S-1 | IEC 61851-1, *Electric vehicle conductive charging system, Part 1: General requirements*, Annex A (control pilot) and Annex B (proximity) | Normative reference. **Not yet purchased**; see Q-02 |
| S-2 | SAE J1772 control pilot description, which IEC 61851-1 matches for the pilot circuit: [Wikipedia, SAE J1772](https://en.wikipedia.org/wiki/SAE_J1772) | 1 kΩ source, 2.74 kΩ / 1.3 kΩ / 270 Ω loads, state voltages, ±0.4 V tolerance, duty-cycle formulas |
| S-3 | [einfochips, IEC 61851 explained](https://www.einfochips.com/blog/iec-61851-everything-you-need-to-know-about-the-ev-charging-standard/) | State meanings, duty-cycle bands |
| S-4 | [Pico Technology, Type 2 proximity line resistance](https://www.picoauto.com/library/automotive-guided-tests/charger-vehicle-proximity-line-resistance-type-2) | PP resistor per cable rating |

## 11. Open questions

| ID | Question | Why it matters |
|---|---|---|
| **Q-01** | The 32 A cable resistor: **220 Ω** (as used in open-hardware designs) or **200 Ω** (as listed by S-4)? | Sets the FR-07 resistor and the FR-04 band. Both must be confirmed against S-1 Table B.2 before schematic |
| **Q-02** | Secondary sources are used until IEC 61851-1 is available. Can the standard be read through the THI library before Gate 1? | Every figure in 1.1 should be checked against the normative text, not a summary of it |
| **Q-03** | What reaction time does S-1 require of a vehicle after a duty-cycle change (FI-06)? | Sets the pass/fail limit of FI-06 |
| **Q-04** | Which commercial CP/PP breakout adapter will be used for real-station tests? | Fixes the connector of MR-02 and the interlock procedure of ER-11 |
| **Q-05** | Is 1 kV isolation (ER-10) enough, or should the barrier follow a reinforced-insulation rule? | Sets the isolator part and the slot width of MR-03 |
| **Q-06** | What frequency tolerance does S-1 give the CP oscillator? | Sets the pass/fail limits of FI-07 |

## 12. Acceptance

1. **Gate 1, architecture.** ±12 V generation chosen and its ripple budgeted against ER-02. Measurement
   chain budgeted against ER-04 to ER-06. Switch parts chosen against ER-08. Isolation approach chosen. Q-01,
   Q-02 and Q-05 answered.
2. **Gate 2, schematic.** ERC clean, every requirement in sections 2 to 5 traceable to a net or a part.
3. **Gate 3, layout and release.** DRC clean, isolation keep-out enforced by a rule, all hardware deliverables present.
4. **Gate 4, built and measured.** Board assembled, D-06 measurement report complete, verification table filled in.

---

*Anything ambiguous in here gets written down as a question in the Gate 1 document and answered before
layout starts.*
