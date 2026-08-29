# CAN-FD Sniffer pHAT - Gate 2: Schematic

| | |
|---|---|
| **Document** | SCH-001 |
| **Revision** | A |
| **Date** | 2026-08-26 |
| **Designer** | Muhamad Izzuwan Alif |
| **Against** | REQ-001 Rev A, ARCH-001 Rev A |
| **Status** | Schematic complete and verified; formal ERC report outstanding |

## 1. What exists

| File | Contents |
|---|---|
| `CAN_Sniffer_HAT.PrjPcb` | Project, one source document |
| `CAN_Sniffer_HAT.SchDoc` | The schematic sheet |
| `CAN_Sniffer_HAT.SchLib` | 12 self-drawn symbols, no external library dependency |
| `library_spec.txt` | Text source the library is generated from - the symbol single source of truth |

Every symbol was drawn for this project against the datasheets in `docs/datasheets/`;
nothing depends on an installed Altium library.

## 2. Verified content of the saved sheet

Read back **from the file on disk**, not from the editor's memory:

```
components    26
pins         138
wires        135
net labels    86
power ports   49
No-ERC        3
```

`135 wires = 138 pins - 3 deliberate no-connects`, and every wire carries exactly one
named connection object (86 + 49 = 135).

## 3. Netlist

Connectivity is by named net: each pin has a short stub wire carrying either a net label
or a power port. Counts below were confirmed against the objects actually present on the
saved sheet.

| Net | Pins | Carried by | Members |
|---|---|---|---|
| `+3V3` | 15 | power port | J1.1, J1.17, U1.14, U2.5, U3.8, C1.1, C3.1, C4.1, C6.1, R1.2, R2.2, R3.2, R5.1, R6.1, J3.22 |
| `+5V` | 5 | power port | J1.2, J1.4, U2.3, C2.1, C5.1 |
| `GND` | 29 | power port | J1.6, J1.9, J1.14, J1.20, J1.25, J1.30, J1.34, J1.39, U1.7, U2.2, U3.4, U3.1, U3.2, U3.3, C1.2, C2.2, C3.2, C4.2, C5.2, C6.2, C7.2, C8.2, R4.2, D1.2, J2.3, J3.23, J3.24, Y1.2, Y1.4 |
| `CANH` | 3 | net label | U2.7, J2.1, R7.1 |
| `CANL` | 3 | net label | U2.6, J2.2, JP1.2 |
| `CAN_INT` | 2 | net label | J1.22, U1.4 |
| `EE_WP` | 3 | net label | U3.7, R3.1, TP1.1 |
| `GPIO12` | 2 | net label | J1.32, J3.7 |
| `GPIO13` | 2 | net label | J1.33, J3.8 |
| `GPIO14` | 2 | net label | J1.8, J3.9 |
| `GPIO15` | 2 | net label | J1.10, J3.10 |
| `GPIO16` | 2 | net label | J1.36, J3.11 |
| `GPIO17` | 2 | net label | J1.11, J3.12 |
| `GPIO18` | 2 | net label | J1.12, J3.13 |
| `GPIO19` | 2 | net label | J1.35, J3.14 |
| `GPIO2` | 2 | net label | J1.3, J3.1 |
| `GPIO20` | 2 | net label | J1.38, J3.15 |
| `GPIO21` | 2 | net label | J1.40, J3.16 |
| `GPIO22` | 2 | net label | J1.15, J3.17 |
| `GPIO23` | 2 | net label | J1.16, J3.18 |
| `GPIO24` | 2 | net label | J1.18, J3.19 |
| `GPIO26` | 2 | net label | J1.37, J3.20 |
| `GPIO27` | 2 | net label | J1.13, J3.21 |
| `GPIO3` | 2 | net label | J1.5, J3.2 |
| `GPIO4` | 2 | net label | J1.7, J3.3 |
| `GPIO5` | 2 | net label | J1.29, J3.4 |
| `GPIO6` | 2 | net label | J1.31, J3.5 |
| `GPIO7` | 2 | net label | J1.26, J3.6 |
| `ID_SC` | 3 | net label | J1.28, U3.6, R2.1 |
| `ID_SD` | 3 | net label | J1.27, U3.5, R1.1 |
| `LED_ACT` | 2 | net label | R6.2, D2.1 |
| `LED_PWR` | 2 | net label | R5.2, D1.1 |
| `RXCAN` | 3 | net label | U1.2, U2.4, D2.2 |
| `SPI_CE0` | 2 | net label | J1.24, U1.13 |
| `SPI_MISO` | 2 | net label | J1.21, U1.12 |
| `SPI_MOSI` | 2 | net label | J1.19, U1.11 |
| `SPI_SCLK` | 2 | net label | J1.23, U1.10 |
| `STBY` | 2 | net label | U2.8, R4.1 |
| `TERM` | 2 | net label | R7.2, JP1.1 |
| `TXCAN` | 2 | net label | U1.1, U2.1 |
| `XTAL1` | 3 | net label | U1.6, Y1.1, C7.1 |
| `XTAL2` | 3 | net label | U1.5, Y1.3, C8.1 |

**No-ERC markers** (deliberately unconnected, MCP2518FD): `U1.3` CLKO/SOF,
`U1.8` INT1/GPIO1, `U1.9` INT0/GPIO0/XSTBY. The design uses the single combined `INT`
pin (FR-07); the spare interrupt/GPIO pins and the clock output are not needed.

## 4. Checks that passed

| Check | Result |
|---|---|
| Every pin belongs to exactly one net or is marked No-ERC | **Pass** - 138/138, asserted in the generator |
| No pin appears in two nets | **Pass** |
| No net has fewer than two pins (no single-pin nets) | **Pass** - 42 nets, all >= 2 |
| Designators unique | **Pass** - 26 unique |
| Object counts on disk match the design | **Pass** - see section 2 |
| Per-net connection-object counts match the netlist | **Pass** - GND 29, +3V3 15, +5V 5, all signal nets exact |
| Pinouts match datasheets | **Pass** - MCP2518FD Table 1-1, MCP2561/2FD Table 1-2, CAT24C32 pin configurations |

**Still outstanding for Gate 2 sign-off:** a captured ERC report artifact. Altium's
compile runs the electrical rule check, but this build's scripting API does not expose
the Messages panel, and the report-generation process hangs the script executor. The
structural checks above cover the ERC classes that apply here (floating pins, single-pin
nets, duplicate designators, undriven power), but the formal report still needs to be
produced from the GUI or a working output job.

## 5. Requirement traceability - schematic level

| ID | Evidence on the sheet |
|---|---|
| FR-01 | `U1` on SPI0 via `SPI_MOSI`/`SPI_MISO`/`SPI_SCLK`/`SPI_CE0` |
| FR-02 | `U1` MCP2518FD + `U2` MCP2562FD, 40 MHz `Y1` on `XTAL1`/`XTAL2` |
| FR-03 | `J2` SCREWTERM_3 on `CANH`/`CANL`/`GND` |
| FR-04 | `R7` 120R in series with `JP1` via net `TERM` |
| FR-05 | `D1` on `LED_PWR`, `D2` on `LED_ACT`/`RXCAN` |
| FR-06 | `U3` on `ID_SD`/`ID_SC`, `R1`/`R2` 3k9 pull-ups, `R3`+`TP1` on `EE_WP`, A0-A2 to GND = 0x50 |
| FR-07 | `CAN_INT`: `U1.4` to `J1.22` (GPIO25) |
| FR-08 | `J3` 2x12, all 21 unused GPIO |
| ER-01 | Only `J1` supplies power; `+5V` and `+3V3` originate there |
| ER-02 | Budget in ARCH-001 section 4 |
| ER-03 | `U2.5` VIO on `+3V3`; no `+5V` net reaches any pin that also connects to `J1` GPIO |
| ER-04 | `C1`-`C4` one per IC supply; `C5`/`C6` bulk |
| ER-05 | `U2` bus pins rated +/-58 V |
| ER-06 | `Y1` 40 MHz on `XTAL1`/`XTAL2` with `C7`/`C8` |

## 6. Footprints (first Gate 3 task, done)

`CAN_Sniffer_HAT.PcbLib` holds 10 footprints, and all 26 components carry a `PCBLIB`
model. Verified by reading both files back from disk.

| Footprint | Pads | Used by | Land pattern source |
|---|---|---|---|
| `SOIC-14_150MIL` | 14 | U1 | Microchip drawing C04-2065-SL |
| `SOIC-8_150MIL` | 8 | U2, U3 | same 150 mil SOIC pattern, 4 pads/side |
| `0805` | 2 | R1-R7, C1-C8 | IPC-7351 hand-solder variant |
| `LED_0805` | 2 | D1, D2 | as 0805, plus a cathode bar (MFR-06) |
| `XTAL_3225_4P` | 4 | Y1 | generic 3.2 x 2.5 mm 4-pad - see Q-6 |
| `HDR_2X20_254` | 40 | J1 | 1.0 mm drill / 1.65 mm pad |
| `HDR_2X12_254` | 24 | J3 | 1.0 mm drill / 1.65 mm pad |
| `HDR_1X2_254` | 2 | JP1 | 1.0 mm drill / 1.65 mm pad |
| `TERM_3P_350` | 3 | J2 | 1.2 mm drill / 2.2 mm pad, 3.5 mm pitch |
| `TESTPOINT_60` | 1 | TP1 | 60 mil round pad |

Annular ring check against MFR-03 (min 0.15 mm): headers (1.65-1.00)/2 = 0.33 mm,
terminal (2.2-1.2)/2 = 0.50 mm. Both pass; minimum drill 1.0 mm is well over the
0.3 mm floor.

**Q-6 - the crystal is now a 4-pad part.** A 3.2 x 2.5 mm 40 MHz crystal is supplied as
4 pads (two signal, two case). Y1's symbol was changed to 4 pins (XI, GND, XO, GND) and
the case pads tied to GND, which also improves EMC. The land pattern is a generic 3225
footprint and **must be re-checked against the crystal actually ordered** before release.

## 7. Next (Gate 3)

PCB layout, design rules, DRC, and the output package. Footprints are done; the next step
is creating the `.PcbDoc`, importing the netlist, and setting the board outline to
65.0 x 30.0 mm with the mounting holes from ARCH-001 section 5.
