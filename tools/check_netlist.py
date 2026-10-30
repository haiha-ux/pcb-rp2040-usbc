"""Compare the kicad-cli netlist (ground truth) with design.nets(), pin by pin. Exit 1 on any mismatch."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design as D  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"


def kicad_nets(sch: Path) -> dict[str, set[str]]:
    out = Path(tempfile.mkdtemp()) / "n.net"
    subprocess.run([CLI, "sch", "export", "netlist", "-o", str(out), str(sch)], check=True, capture_output=True)
    txt = re.sub(r"\s+", " ", out.read_text(encoding="utf-8"))
    nets = {}
    for chunk in txt.split("(net (code ")[1:]:
        name = re.search(r'\(name "([^"]*)"\)', chunk).group(1).lstrip("/")
        nets[name] = {f"{r}.{p}" for r, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', chunk)}
    return nets


def compare(want, got):
    errs = []
    pin_to_net = {p: n for n, ps in got.items() for p in ps}
    for net, pins in want.items():
        for p in pins:
            if not p.startswith("#") and pin_to_net.get(p) != net:
                errs.append(f"{p}: want {net}, got {pin_to_net.get(p)}")
        extra = got.get(net, set()) - set(pins)
        if extra:
            errs.append(f"{net}: extra pins {sorted(extra)}")
    return errs


if __name__ == "__main__":
    want = D.nets()
    got = kicad_nets(ROOT / "rp2040_usbc.kicad_sch")
    errs = compare(want, got)
    sab = {k: set(v) for k, v in got.items()}
    sab["USB_DP_MCU"].discard("U2.47")
    sab["USB_DM_MCU"].add("U2.47")
    assert compare(want, sab), "sabotage not detected - check is vacuous"
    stray = sorted(n for n in got if n not in want and not n.startswith("unconnected"))
    unc = sorted(n for n in got if n.startswith("unconnected"))
    print(f"{len(got)} nets in netlist, {len(want)} designed; stray: {stray}; unconnected: {unc}")
    print("\n".join(errs) if errs else "MATCHES the design net table 100%")
    sys.exit(1 if errs or stray else 0)
