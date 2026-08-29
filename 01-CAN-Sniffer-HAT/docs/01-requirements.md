# CAN-FD Sniffer pHAT - Requirements Specification

| | |
|---|---|
| **Document** | REQ-001 |
| **Revision** | A |
| **Date** | 2026-08-23 |
| **Author** | Muhamad Izzuwan Alif |
| **Status** | Frozen, design started against it |

---

## 1. Purpose and scope

Design a Raspberry Pi pHAT that lets a Pi Zero 2 W capture and transmit CAN and
CAN-FD traffic on a vehicle bus. The board is a diagnostic/logging tool, not an
in-vehicle production ECU.

Target use case: bench and workshop capture of automotive CAN-FD traffic,
comparable in function to a Waveshare CAN HAT but with CAN-FD support and a
documented, self-designed hardware baseline.

**In scope:** schematic, PCB layout, manufacturing data package, design
documentation.
**Out of scope:** firmware, enclosure, EMC certification, production test fixture.

---

## 2. Functional requirements

| ID | Requirement | Verification |
|---|---|---|
| **FR-01** | The board shall provide one CAN-FD channel accessible to the host Pi over SPI. | Schematic review |
| **FR-02** | The CAN controller shall support ISO 11898-1 CAN-FD at arbitration rates up to 1 Mbit/s and data rates up to 5 Mbit/s. | Datasheet check |
| **FR-03** | The board shall present CAN_H, CAN_L and GND on a removable screw terminal, 3.5 mm pitch minimum. | Layout review |
| **FR-04** | A 120 Ω bus termination resistor shall be fitted and selectable by the user without soldering. | Schematic + layout review |
| **FR-05** | The board shall provide at least two user-visible status LEDs (power, bus activity). | Schematic review |
| **FR-06** | The board shall carry an I²C ID EEPROM per the Raspberry Pi HAT specification, addressable at 0x50 on ID_SD/ID_SC. | Schematic review |
| **FR-07** | The CAN controller interrupt line shall be routed to a GPIO usable for edge-triggered interrupts. | Schematic review |
| **FR-08** | Unused Pi GPIO shall be passed through to a 0.1" breakout header for future expansion. | Layout review |

## 3. Electrical requirements

| ID | Requirement | Verification |
|---|---|---|
| **ER-01** | The board shall be powered exclusively from the Pi 40-pin header. No external supply. | Schematic review |
| **ER-02** | Total current draw from the Pi 5 V rail shall not exceed 150 mA. | Calculation, documented in README |
| **ER-03** | All SPI signals between the Pi and the CAN controller shall operate at 3.3 V logic. No 5 V shall reach any Pi GPIO. | Schematic review. **This one destroys the Pi if it is wrong, so check it twice.** |
| **ER-04** | Every IC shall have a decoupling capacitor of at least 100 nF placed within 5 mm of its supply pin. | Layout review |
| **ER-05** | The CAN transceiver shall withstand a bus short to 12 V without damage. | Datasheet check |
| **ER-06** | The controller oscillator shall meet the CAN-FD frequency tolerance required by the controller datasheet. | Datasheet check |

## 4. Mechanical requirements

| ID | Requirement | Verification |
|---|---|---|
| **MR-01** | Board outline shall be 65.0 × 30.0 mm (Pi Zero pHAT form factor). | Measured in PCB |
| **MR-02** | Four M2.5 mounting holes shall be positioned per the official Raspberry Pi mechanical drawing. Designer shall obtain and cite the source. | Layout review vs cited drawing |
| **MR-03** | The 40-pin header shall be positioned so the board seats on a Pi Zero 2 W without mechanical interference. | 3D view + drawing check |
| **MR-04** | The screw terminal shall be accessible with the board mounted on the Pi. | 3D view |
| **MR-05** | No component shall exceed the height available under a standard 11 mm HAT stacking spacer, except the terminal block and header. | 3D view |

## 5. Manufacturing requirements

| ID | Requirement | Verification |
|---|---|---|
| **MFR-01** | Two-layer board, 1.6 mm FR-4, 1 oz copper. | Layer stack manager |
| **MFR-02** | Design shall respect a 6 mil / 6 mil minimum trace-width / clearance capability. Rules shall be configured to enforce this. | Design rules + DRC |
| **MFR-03** | Minimum drill 0.3 mm, minimum annular ring 0.15 mm. | Design rules + DRC |
| **MFR-04** | All components shall be currently orderable, with a named supplier and a stock figure recorded at design time. | BOM review |
| **MFR-05** | Passives shall be 0805 or larger, for hand-solderability. | BOM review |
| **MFR-06** | Silkscreen shall show designator, polarity/pin-1 marking, board name, revision, and the designer's name. | Layout review |

## 6. Deliverables

The design is complete when **all** of the following exist in the repository:

| ID | Deliverable |
|---|---|
| **D-01** | Schematic (`.SchDoc`) and PDF export, readable, with a filled title block |
| **D-02** | PCB layout (`.PcbDoc`) |
| **D-03** | Documented design rule set, with a written justification for each non-default value |
| **D-04** | DRC report showing **zero** violations, or a written waiver for each one |
| **D-05** | Gerber X2 + NC drill files, in a dated zip |
| **D-06** | BOM with MPN, supplier, supplier PN, quantity, unit price, and extended price |
| **D-07** | Assembly drawing (top and bottom) and pick-and-place file |
| **D-08** | 3D render (PNG) of the assembled board |
| **D-09** | `README.md`: what it does, key design decisions **and why**, requirement traceability table, known limitations |
| **D-10** | Requirement verification table: every ID in §2-§5 marked Pass / Fail / Waived with evidence |

## 7. Constraints

- **C-01** Budget: 50 € for one prototype build including PCB fabrication.
- **C-02** The board must be routable in two layers. If you cannot, document why and propose four.
- **C-03** No unverified part may enter the BOM. If you cannot find a datasheet, you cannot use the part.

## 8. Acceptance

Design review at three gates. Do not proceed past a gate without sign-off:

1. **Gate 1, architecture.** Part selection justified, block diagram, power budget.
2. **Gate 2, schematic.** Full schematic, ERC clean, every requirement in §2-§3 traceable to a net or part.
3. **Gate 3, layout and release.** DRC clean, all deliverables in §6 present.

---

*Anything ambiguous in here gets written down as a question in the Gate 1 document and
answered before layout starts. An ambiguity left unresolved turns into a respin.*
