"""Build the schematic through the Konnect MCP server (never edits .kicad_sch as text).

Run: python tools/build_schematic.py   (move an existing rp2040_usbc.kicad_sch out of the way first)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design as D            # noqa: E402
from kcall import Konnect     # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCH = str(ROOT / "rp2040_usbc.kicad_sch")

NOTES = [
    "Circuit after Raspberry Pi 'Hardware design with RP2040', section 2 (minimal design): LDO (AP2112K-3.3 here, NCP1117 in the reference),",
    "W25Q128JVS QSPI flash, ABM8-272-T3 12 MHz crystal with 15p load caps and 1k XOUT series resistor,",
    "27R USB series resistors close to RP2040, 1u on VREG_VIN / VREG_VOUT, 100n per IOVDD/DVDD pin.",
    "Changes vs. reference: USB-C receptacle (CC1/CC2 5.1k to GND = UFP/sink), USBLC6-2SC6 ESD on D+/D-,",
    "BOOTSEL button pulls QSPI_SS low through 1k, RUN button with 10k pull-up, SWD header, LED on GPIO25.",
]


def pin_xy(k, ref, num):
    locs = k.call("batch_get_schematic_pin_locations", {"schematic": SCH, "references": [ref]})
    p = next(p for p in locs["components"][0]["pins"] if p["number"] == num)
    return round(p["x"], 2), round(p["y"], 2)


def main():
    k = Konnect()
    k.call("load_toolset", {"name": ["sch_wiring", "sch_components", "sch_batch", "sch_hierarchy", "sch_export", "sch_analysis"]})
    if Path(SCH).exists():
        sys.exit(f"{SCH} exists - move it away first")
    k.call("create_schematic", {"path": SCH, "size": "A3"})
    comps = [{"lib_id": lib, "reference": ref, "value": val, "x": x, "y": y, "rotation": rot,
              **({"footprint": fp} if fp else {})}
             for ref, (lib, val, fp, x, y, rot) in D.PARTS.items()]
    placed = k.call("batch_place_components", {"schematic": SCH, "components": comps})
    assert placed["placed_count"] == len(comps), placed.get("errors")
    for chain in D.WIRE_CHAINS.values():
        k.call("batch_connect_pins", {"schematic": SCH, "connections": [
            {"ref1": a.split(".")[0], "pin1": a.split(".")[1], "ref2": c.split(".")[0], "pin2": c.split(".")[1]}
            for a, c in zip(chain, chain[1:])]})
    skip = {p for chain in D.WIRE_CHAINS.values() for p in chain[1:]}
    for net, pins in D.nets().items():
        ps = [{"reference": p.rsplit(".", 1)[0], "pin_number": p.rsplit(".", 1)[1]} for p in pins if p not in skip]
        r = k.call("batch_connect_to_net", {"schematic": SCH, "net_name": net, "pins": ps, "stub_length": 2.54})
        assert not r.get("errors"), (net, r["errors"])
    # connect_pins may also drop a label on the far pin of a chain; keep only the first pin's label.
    labs = k.call("list_schematic_labels", {"schematic": SCH})["labels"]
    for net, chain in D.WIRE_CHAINS.items():
        keep_x = pin_xy(k, *chain[0].split("."))[0]
        for lab in labs:
            if (lab.get("net") or lab.get("name")) == net and abs(lab["y"] - pin_xy(k, *chain[0].split("."))[1] + 2.54) < 0.01 \
                    and abs(lab["x"] - keep_x) > 0.01:
                k.call("delete_schematic_net_label", {"schematic": SCH, "net": net, "x": lab["x"], "y": lab["y"]})
                k.call("delete_schematic_wire", {"schematic": SCH, "x1": lab["x"], "y1": lab["y"],
                                                 "x2": lab["x"], "y2": round(lab["y"] + 2.54, 2)})
    k.call("batch_add_no_connect", {"schematic": SCH, "positions": [
        dict(zip(("x", "y"), pin_xy(k, *p.split(".")))) for p in D.NO_CONNECT]})
    for i, t in enumerate(NOTES):
        k.call("add_schematic_text", {"schematic": SCH, "text": t, "x": 20.32, "y": 259.08 + i * 4.57, "size": 1.8})
    edits = [{"reference": ref, "fields": {"Manufacturer": m, "MPN": p, "LCSC": l}}
             for refs, (m, p, l) in D.MPN.items() for ref in refs.split(",")]
    r = k.call("batch_edit_schematic_components", {"schematic": SCH, "edits": edits, "create_missing": True})
    assert not r.get("errors") and not r.get("failures"), r
    print("placed", len(comps), "| nets", len(D.nets()), "| mpn", len(edits))


if __name__ == "__main__":
    main()
