# -*- coding: utf-8 -*-
"""Where the Altium files live.

Everything is derived from this file's own location, so the repository can be
cloned anywhere. The generators emit DelphiScript, and DelphiScript only takes
absolute paths, which is why these are absolutised here rather than left
relative.
"""
import os

HARDWARE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hardware")

SCHLIB = os.path.join(HARDWARE, "CAN_Sniffer_HAT.SchLib")
SCHDOC = os.path.join(HARDWARE, "CAN_Sniffer_HAT.SchDoc")
PCBLIB = os.path.join(HARDWARE, "CAN_Sniffer_HAT.PcbLib")
PCBDOC = os.path.join(HARDWARE, "CAN_Sniffer_HAT.PcbDoc")

LIBRARY_SPEC = os.path.join(HARDWARE, "library_spec.txt")
FOOTPRINT_SPEC = os.path.join(HARDWARE, "footprint_spec.txt")
