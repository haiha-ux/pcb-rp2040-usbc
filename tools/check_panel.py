"""Panel DRC summary. The four copies share net names, so KiCad also lists every net as unconnected between
copies; those are expected. What must be zero is unconnected items INSIDE one board, and every violation."""
import collections
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent
K = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
RPT = ROOT / "reports" / "panel_drc.json"


def board_of(pos):
    """Which copy (col, row) a point lies in, from the panel geometry used by panelize.py."""
    import panelize as P
    for c in range(P.COLS):
        for r in range(P.ROWS):
            ox, oy = P.origin(c, r)
            if ox - 0.5 <= pos["x"] <= ox + P.BW + 0.5 and oy - 0.5 <= pos["y"] <= oy + P.BH + 0.5:
                return c, r
    return None


subprocess.run([K, "pcb", "drc", "--severity-all", "--format", "json", "-o", str(RPT),
                str(ROOT / "panel" / "rp2040_usbc_panel.kicad_pcb")], check=True, capture_output=True)
d = json.loads(RPT.read_text(encoding="utf-8"))
viol = collections.Counter(v["type"] for v in d["violations"])
intra = [u for u in d["unconnected_items"] if len({board_of(i["pos"]) for i in u["items"]}) == 1]
cross = len(d["unconnected_items"]) - len(intra)
print("violations:", dict(viol))
for v in d["violations"]:
    print("  ", v["type"], "|", " || ".join(i["description"] for i in v["items"]))
print(f"unconnected inside one board: {len(intra)}   between copies (same net name, expected): {cross}")
sys.exit(1 if intra or any(v["severity"] == "error" for v in d["violations"]) else 0)
