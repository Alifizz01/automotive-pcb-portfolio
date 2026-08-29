# CAN-FD Sniffer pHAT - Gate 3: Layout

| | |
|---|---|
| **Document** | PCB-001 |
| **Revision** | A |
| **Date** | 2026-08-29 |
| **Designer** | Muhamad Izzuwan Alif |
| **Against** | REQ-001 Rev A, ARCH-001 Rev A, SCH-001 Rev A |
| **Status** | Routed, DRC clean; fabrication output package outstanding |

## 1. Done so far

| Item | State | Evidence |
|---|---|---|
| `CAN_Sniffer_HAT.PcbLib` | 10 footprints | pad counts read back from the library |
| Footprints assigned | 26 / 26 components | every component carries a `PCBLIB` model |
| `CAN_Sniffer_HAT.PcbDoc` | created, in the project | project reports 2 source documents |
| Board outline | **65.0 x 30.0 mm** | vertices `(0,0) (65,0) (65,30) (0,30)`, read back after reopening the file |
| Mounting holes | 4 x 2.75 mm, non-plated | MH1 (3.5, 3.5), MH2 (61.5, 3.5), MH3 (3.5, 26.5), MH4 (61.5, 26.5) |

Requirements closed by the above: **MR-01** (outline 65.0 x 30.0 mm) and **MR-02**
(hole positions per the cited Raspberry Pi drawings, 58 x 23 mm pitch, drilled 2.75 mm).
The holes are non-plated with no copper land, matching the HAT drawing's instruction that
mounting-hole land be bare board and never connected to GND.

## 2. Netlist import - done

The board carries **26 components and 42 nets**, matching the schematic exactly, verified
by reopening the saved file.

Two things had to be fixed before the ECO would place anything:

1. **Footprint models pointed at the wrong library.** Every implementation was created
   with `UseComponentLibrary = True`, meaning "find the footprint in the library this
   component came from" - the `.SchLib`, which holds no footprints. The ECO therefore
   failed every component with *"Failed to add class member : Component ..."*; those
   class-member errors were the symptom, not the cause. Fixed by setting
   `UseComponentLibrary = False` and registering the `.PcbLib` as an available library.
2. **The libraries were not visible to the project.** Added to the `.PrjPcb` directly -
   it is an INI text file, far more reliable than asking Altium to save it (a scripted
   project save hung the application).

The import must be driven from the menu: **Design > Import Changes from Project >
Execute Changes**. `PCB:Import` is a file importer, and `PCB:EngineeringChangeOrder`
returns without doing anything when invoked headlessly.

### Design rules (MFR-02, MFR-03)

| Rule | Value | Property |
|---|---|---|
| Clearance | 6 mil | `Gap` |
| Width | 6 mil min / 10 pref / 60 max, per layer | `MinWidth(layer)` - indexed, not plain |
| Hole size | 0.3 - 3.0 mm | `MinLimit` / `MaxLimit` |
| Annular ring | 0.15 mm | `Minimum` - not `MinimumRing` |

All four applied and saved. Maximum hole size is 3.0 mm so the 2.75 mm mounting holes do
not violate it.

**Warning learned the hard way:** a script that dies between `PCBServer.PreProcess` and
`PostProcess` leaves an open transaction. An import done while that transaction was open
appeared on screen but was rolled back on save - 26 components were lost that way. Always
clear a wedged script before trusting a save.


## 3. Placement

Components placed by the designer, then checked numerically against the requirements
rather than by eye. Distances are pad-to-pad, which is what ER-04 actually constrains.

| Check | Before | After | Limit |
|---|---|---|---|
| C1 -> U1 (VDD 100nF) | 4.5 mm | 4.5 mm | 5 mm |
| C2 -> U2 (VDD 100nF) | **18.2 mm** | 2.6 mm | 5 mm |
| C3 -> U2 (VIO 100nF) | **15.6 mm** | 2.7 mm | 5 mm |
| C4 -> U3 (VCC 100nF) | **23.6 mm** | 2.7 mm | 5 mm |
| Y1 -> U1 (crystal) | **15.2 mm** | 0.4 mm | 10 mm |
| C7 -> Y1 (load cap) | 2.8 mm | 1.7 mm | 5 mm |
| C8 -> Y1 (load cap) | **13.3 mm** | 1.7 mm | 5 mm |

The original placement lined every capacitor up in a row along the bottom edge
(all at y = 7-9 mm) instead of beside the chip each one serves, and put the 40 MHz
crystal next to U3 - the EEPROM - when it belongs to U1. **ER-04 now passes for all
four ICs**, and the crystal loop is tight.

Open judgement call, not a requirement failure: U2 to J2 is 31.7 mm, so the CAN pair
crosses half the board. Acceptable for a 5 Mbit/s bench tool; moving U2 to about
x = 42 would shorten it to ~17 mm at the cost of relocating its decouplers.


## 4. Routing

Autorouted: **300 track segments, 6 vias**, two layers.

### Defect found and fixed: signal shorted to a mounting hole

The autorouter treated the unnetted, unplated mounting-hole pads as free vias and used
**MH2 to change layers, shorting net `LED_PWR` to the mounting hole**. On a HAT that hole
takes an M2.5 screw into a metal standoff, so this is a short to the Pi's mechanical
ground - exactly what the HAT drawing's "do not connect these to GND" note is guarding
against.

Detected by checking every `MH*` pad's net, not by eye:

```
before   MH1 clean  MH2 = LED_PWR (SHORT!)  MH3 clean  MH4 clean
after    MH1 clean  MH2 clean               MH3 clean  MH4 clean
```

Fix: cleared the net from all four holes, deleted the 2 track segments landing on them,
and set `Moveable := False` on each pad - a locked primitive is not reused by the router.

That left `LED_PWR` unrouted for one short hop, R5 to D1, which was then routed by hand
away from the hole.

**Lesson for any board with mounting holes:** an unnetted through-hole pad is a free via
as far as the autorouter is concerned. Lock mounting holes before routing, and check
their nets afterwards.

## 5. Defect: connectors had no pads

Every through-hole pad in `CAN_Sniffer_HAT.PcbLib` was created on **"No Layer"** instead
of Multi-Layer, so J1, J2, J3 and JP1 had no copper at all - they drew as bare silkscreen
outlines and connected to nothing. 69 pads across the four connectors.

Cause: the footprint generator set the pad layer by *name*. Altium's `String2Layer`
accepted `'Top Layer'` but rejected `'Multi-Layer'`, silently assigning eNoLayer rather
than reporting an error. Only the surface-mount parts were unaffected, which is why the
board looked plausible.

Fixed by assigning the `eMultiLayer` constant directly, in both the library and the
placed pads on the board. Verified after reopening the file from disk: 69 pads on
Multi-Layer, 0 off-layer.

Two lessons worth keeping:

- Set Altium layers with the **constant**, never a string.
- A board iterator filtered by `AllLayers` does **not** return objects on eNoLayer, so the
  obvious repair script finds nothing. Walk the components and use their group iterators.

It was spotted by looking at the screen - the connectors had visibly been empty yellow
boxes since the first render - not by any of the scripted checks, which happily read back
pad coordinates that were electrically meaningless.

## 6. Design rule check (D-04)

Run over the finished board on 29-08-2026. The report is committed at
`hardware/Project Outputs for CAN_Sniffer_HAT/`, in both `.drc` and `.html` form.

```
Violations Detected : 0
Waived Violations   : 0
```

All 15 rules pass, including the four that carry the manufacturing limits: clearance
0.1 mm, width min 0.152 mm, annular ring min 0.15 mm, hole size 0.3 to 3.0 mm. The
un-routed net constraint reports 0, so every net on the board is connected, which is the
other thing this report is worth reading for.

**D-04 closed: DRC clean, no waivers needed.**

## 7. Still to do

| ID | Item |
|---|---|
| MFR-01 | Layer stack: 2 layers, 1.6 mm FR-4, 1 oz copper |
| D-05..D-08 | Gerbers, BOM, assembly drawing, pick-and-place, 3D render |

## 8. Scripting notes

Board outline vertices can only be written through `TPolySegment` records, and a script
has to declare a variable to hold one, which Altium will not do for a loose snippet.
`tools/altium/arun2.py` deploys and runs a real Altium script project instead, which lifts
that restriction; `outline2.pas` is the script that defines the board.

Two traps cost time here and are worth remembering:

- `BoardOutline.BoundingRectangle` does **not** report the outline's own extent - it kept
  returning the 152.4 x 101.6 mm sheet size while the polygon was already correct at
  65 x 30. Measure by walking `Segments[]`, never by the bounding rectangle.
- The board-shape commands Altium publishes (`PlaceBoardOutline`, `OutlineSelectedObjects`)
  are interactive and cannot define a shape headlessly, so the `Segments[]` route is the
  only scripted option.
