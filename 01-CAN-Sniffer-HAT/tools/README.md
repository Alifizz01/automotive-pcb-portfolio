# Generators

The symbol library, the footprint library and the schematic sheet in this project are
generated rather than drawn by hand. These scripts are the source. Run them from this
folder and they write into `../hardware/`.

| Script | Produces |
|---|---|
| `paths.py` | where the Altium files are, worked out from the repository layout |
| `gen_spec.py` | `../hardware/library_spec.txt`, every symbol's pins and body graphics |
| `gen_fp.py` | `../hardware/footprint_spec.txt`, every land pattern, pad by pad |
| `gen_place.py` | the component placement table (`PARTS`) imported by the two below |
| `gen_sheet2.py` | `build_sheet2.pas`, DelphiScript that builds all 26 components on the sheet |
| `gen_wire.py` | `wire.pas`, DelphiScript that draws the stub wires, net labels and power ports |

Order: `gen_spec.py` and `gen_fp.py` first, then `gen_sheet2.py`, then `gen_wire.py`.

Keeping the netlist in Python rather than in the Altium file buys one useful thing:
`gen_wire.py` asserts that every pin belongs to exactly one net and that no net has fewer
than two pins, so an edit that breaks coverage fails at the keyboard instead of turning up
as an ERC warning later. All 138 pins are checked on every run.

## Running a DelphiScript file, `altium/`

Altium will execute a loose snippet, but not one that declares its own variables, and a
record type such as `TPolySegment` has to be declared before it can be filled in. Since
that record is the only way to write a board outline, `altium/arun2.py` deploys a real
Altium script project and launches it from the command line:

```
python altium/arun2.py altium/outline2.pas
```

It substitutes the real board path for the `{{PCB_DOC}}` placeholder on the way in, waits
for the script to drop its result in `C:\Users\Public\altium_hat\`, and prints the log.
`dialog_guard.py` runs alongside it and clicks away the modal dialogs Altium throws
during an unattended run, since any one of them blocks the scripting engine until a human
turns up.

| File | Does |
|---|---|
| `altium/arun2.py` | deploys and runs a script project, then reports the result |
| `altium/outline2.pas` | sets the 65 x 30 mm board outline and the four M2.5 mounting holes |
| `altium/verifypcb.pas` | reopens the saved `.PcbDoc` and reports what is really in it |
| `altium/procs.pas` | lists the commands the PCB server publishes, plus the log helpers |
| `dialog_guard.py` | dismisses Altium modal dialogs while a script runs |

## Altium behaviour worth remembering

Four things here cost real time.

- A schematic document must be marked `Modified := True` before `DoFileSave('')`, or the
  save silently does nothing and the file never reaches disk. The kind string must be
  empty; `DoFileSave('SCH')` also does nothing.
- `ISch_Component.Replicate` on an open `.SchLib` is unreliable. Depending on the library
  editor's current component it returns clones with no pins, or does not place the
  component at all. These scripts therefore build every component directly from
  `library_spec.txt` instead of copying it out of the library.
- A component's child objects, pins and body graphics, must each set `OwnerPartId := 1`
  and `OwnerPartDisplayMode := 0`. Without them Altium creates the objects, and they are
  even countable through the iterators, but never draws them, so the sheet shows only
  designators and comments floating in space.
- Setting `Component.Location` does not move the pins and graphics with it, whether it is
  set before or after the children are added. Only `MoveToXY`, called *after*
  `RegisterSchObjectInContainer`, translates the whole component. Child coordinates are
  therefore written symbol-relative and the component is moved into place afterwards.
  Because `MoveToXY` works off the current location, `Location` must be left unset.
