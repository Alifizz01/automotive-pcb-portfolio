# PCB portfolio

Hardware projects I design end to end: requirements first, then schematic, then layout,
then a manufacturing package, with the reasoning written down as I go. Everything here is
built in Altium Designer, and every symbol and footprint is drawn from the manufacturer's
datasheet rather than pulled from a vendor library.

Each project folder is self-contained and carries its own README, its own design
documents, and the datasheets that back the part choices.

## Projects

| # | Project | What it is | State |
|---|---|---|---|
| 01 | [CAN-FD Sniffer pHAT](01-CAN-Sniffer-HAT/) | A 65 x 30 mm Raspberry Pi Zero 2 W HAT that puts one CAN-FD channel on SPI, for logging and transmitting on a vehicle bus | Schematic and layout complete, DRC clean, not yet fabricated |
| 02 | [CAN-FD Test Runner](02-CAN-Test-Runner/) | A battery-backed handheld that plugs into OBD-II, runs a test you defined on the SD card for the whole drive, and ends with PASSED, FAILED or INCOMPLETE. Keeps watching after key-off to catch what wakes the bus overnight | Architecture complete and pin-verified, schematic not started |

## How each project is organised

```
NN-project-name/
  README.md      what it does, the decisions and why, traceability, limitations
  docs/          requirements, architecture, schematic and layout documents
    datasheets/  every datasheet cited in those documents
  hardware/      the Altium project: schematic, PCB, libraries, output reports
  tools/         any scripts the design is generated or checked with
```

The design documents follow the gates I work to: requirements, then architecture, then
schematic, then layout. Nothing moves to the next gate until the current one holds
together, and the questions raised against the specification are written down with the
decision taken on each.

## What "state" means

I would rather be honest about how far a design has gone than dress it up. A board marked
DRC clean has passed the design rule check and nothing more. Where a board has actually
been fabricated and tested, the project README says so and shows the measurements.

## License

MIT, see [LICENSE](LICENSE).
