# CAN-FD Hardware Timestamper

A two-channel CAN-FD capture board that decodes the protocol **inside an FPGA**, so every
frame is timestamped by hardware at its first edge instead of by a host whenever it gets
round to servicing an interrupt. Both channels are isolated, and both are timestamped from
one counter, so timings on one bus can be compared with timings on the other.

> **Note on method.** The requirements and architecture for this board were developed in
> discussion with an AI assistant. Every figure in them is either derived in the document
> itself or taken from a cited datasheet, and the design decisions are mine.

**Status:** Gate 1 (requirements and architecture) complete. All five opening questions
closed, two new ones raised and recorded. No schematic, no board yet.

**The logic already exists and is verified**, in its own repository:
[fpga-can-timestamper](https://github.com/Alifizz01/fpga-can-timestamper) — simulated,
synthesised, timing closed and rebuilt in CI on every push. This project is the board that
logic runs on.

---

## The problem it solves

Projects 01 and 02 in this portfolio both log CAN through a conventional controller: an
MCP2518FD over SPI, and the STM32H563's internal FDCAN. Both hit the same wall, and it is
not a firmware problem.

**A CAN controller tells you a frame arrived. It does not tell you when.** The timestamp is
applied when the interrupt is serviced, so it carries the interrupt latency, the SPI
transfer and the scheduler with it. On a quiet bus you never notice. On a busy bus it is
tens of microseconds — and the error grows exactly when the bus is busy, which is exactly
when the measurement was interesting.

That is fine for reading signal values. It is not fine for:

- **Which of these two messages came first?** Two frames a few hundred microseconds apart
  can be reordered by a logger whose jitter is wider than the gap.
- **How long did the gateway take to forward that frame?** That is a subtraction across two
  different buses. Independent jitter on each makes the answer noise.
- **Did this ECU answer inside its deadline?** A 10 ms deadline measured with 50 us of
  uncertain jitter has an error you cannot characterise.

Put the receiver in fabric and a counter is sampled by the same logic that sees the
start-of-frame edge. The uncertainty becomes one clock instead of one interrupt.

| | conventional logger | this board |
|---|---|---|
| when the clock is read | in the interrupt handler | at the start-of-frame edge |
| jitter source | interrupt latency, SPI, scheduler | one system clock |
| resolution | ~1 us, jitter far worse | **15.6 ns**, no jitter |
| two buses on one time base | only via the host clock | **yes, one counter feeds both** |

---

## Design highlights so far

**The package was chosen by measurement, not by feel.** The RTL's synthesis report gives
3 746 LUTs. The largest iCE40 in the open toolchain would be 71 % full before any future
addition; the ECP5-25F sits at 15 %. And rather than assume the cheap TQFP144 package would
do, the real design was re-placed and re-routed in it — it closes at 84.6 MHz against a
64 MHz target, using 8 of its 98 user pins. A 381-ball BGA cannot escape on four layers and
was rejected on that basis.

**Each channel gets its own isolation barrier**, not one shared barrier around the board.
Sharing would be cheaper and is wrong here: the whole point is measuring between two buses
whose grounds sit volts apart under load, and tying them together through the logger injects
exactly the noise the board exists to measure around.

**The isolated supply is a transformer driver, not a bought module.** Most low-cost isolated
DC-DC modules quote isolation as a one-second production test rather than a continuous
working voltage. The requirement asks for a working rating, so the barrier rests on a
transformer with its own datasheet figure.

**Receive-only by construction.** The transceiver's TXD is tied recessive and no signal is
routed to it from the FPGA. The board cannot drive the bus or the ACK slot because there is
no copper for it to do so, not because firmware declines to.

**The link budget found a problem before the schematic did.** Two channels saturated with
64-byte FD frames produce about 458 kB/s, which needs 4.6 Mbaud — above the 4 Mbaud the RTL
is currently built for. The hardware supports 12 Mbaud and nothing in the layout forecloses
it, so the fix is one constant and a reverification run. Better found here than at bring-up.

**The sequencing rule was read in the datasheet, not on a forum.** The commonly repeated
ECP5 rule is a strict VCCIO → VCCAUX → VCC_CORE ordering. Checking the two Lattice documents
committed here, what they actually say is narrower: *"VCCIO supplies should be powered up
before or together with the VCC and VCCAUX supplies"* (FPGA-TN-02038 §4), plus a hard
*"VCCAUX ramp rate must not exceed 30 mV/µs"* (DS1044). The board implements the stricter
ordering anyway — it costs one power-good gate — but the documents only claim what they
actually say.

---

## Documents

| | |
|---|---|
| [01-requirements.md](docs/01-requirements.md) | REQ-003: what the board must do, and how each item gets verified |
| [02-architecture.md](docs/02-architecture.md) | Gate 1: parts and why, isolation strategy, power architecture and sequencing, power and link budgets, the timestamp error budget, pin map checked against the RTL |

---

## What is honestly not done

- No schematic and no PCB. Gate 1 only.
- The transformer for the isolated supply is chosen in approach but not in part number; its
  datasheet is not yet committed, and MFR-03 says nothing is decided until it is.
- The FPGA core current in the power budget is an estimate, not a Lattice Power Calculator
  result. The budget survives being wrong by 2x, so it does not block Gate 2, but it must be
  replaced before the regulator thermal design is fixed.
- Nothing here has been built or measured. Every number is either derived in the documents
  or cited from a datasheet.
