"""4-layer RP2040 USB-C board, built with KiCad's own pcbnew API (run with KiCad's python, KiCad closed).

  python tools/build_pcb.py all      place -> hand-route USB -> planes -> DSN -> Freerouting -> SES -> fill
Board coordinates in mm, origin top-left, USB-C on the top edge (y = 0).
Stackup: JLC04161H-7628 — F.Cu signal / In1.Cu GND plane / In2.Cu +3V3 plane / B.Cu signal + GND pour.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design as D  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "rp2040_usbc.kicad_pcb"
SCH = ROOT / "rp2040_usbc.kicad_sch"
REP = ROOT / "reports"
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
FPLIB = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
JAVA = os.environ.get("JAVA", "java")                      # Freerouting 2.4 needs Java 21+
FR_JAR = os.environ.get("FREEROUTING_JAR", "freerouting-2.4.1.jar")
mm = pcbnew.FromMM
W, H = 30.0, 58.0

# USB pair geometry from tools/usb_impedance.py (JLC04161H-7628, L1 over L2): 90 ohm diff -> w 0.27, s 0.15
W_USB, W_USB_NECK = 0.27, 0.20
VIA_D, VIA_DRILL = 0.45, 0.25
U2C = (13.6, 26.0)


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def P(b, ref, num):
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNumber() == num:
            q = p.GetPosition()
            return round(q.x / 1e6, 4), round(q.y / 1e6, 4)
    raise KeyError(f"{ref}.{num}")


def at_pad(b, ref, num, x, y, rot):
    fp = b.FindFootprintByReference(ref)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(V(0, 0))
    px, py = P(b, ref, num)
    fp.SetPosition(V(x - px, y - py))


def center(b, ref, x, y, rot):
    fp = b.FindFootprintByReference(ref)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(V(x, y))


# ---------------- placement ----------------
def place_all(b):
    center(b, "J1", 15.0, 3.65, 180)                       # opening on the top edge (body front at y=0)
    center(b, "U2", *U2C, 0)
    # ESD: D+ (I/O1, pins 1/6) column on the LEFT, D- (I/O2, pins 3/4) on the right
    for rot in (90, 270):
        center(b, "U4", 15.0, 13.5, rot)
        if P(b, "U4", "1")[0] < P(b, "U4", "3")[0]:
            break
    assert P(b, "U4", "1")[0] < P(b, "U4", "3")[0]
    at_pad(b, "R3", "1", 14.0, 17.2, 270)
    at_pad(b, "R4", "1", 15.0, 17.2, 270)
    assert P(b, "R3", "2")[1] > P(b, "R3", "1")[1]
    center(b, "R6", 17.5, 11.2, 90)                        # CC1 (A5 at x=16.25)
    center(b, "R7", 12.4, 11.2, 90)                        # CC2 (B5 at x=13.25)
    center(b, "U1", 21.2, 13.4, 0)                         # AP2112K-3.3 LDO
    center(b, "C1", 22.6, 10.0, 0)                         # LDO in (VBUS)
    center(b, "C2", 22.6, 16.4, 0)                         # LDO out (3V3)
    center(b, "U3", 8.4, 15.0, 90)                         # QSPI flash, top-left near QSPI pins 51-56
    center(b, "C5", 8.4, 9.4, 0)
    center(b, "C17", 7.6, 21.3, 180)                         # 3V3 bulk
    # decoupling: outside the QFN courtyard (+-4.17 mm), next to each supply pin
    center(b, "C9", 8.2, 23.4, 180)       # IOVDD 1
    center(b, "C11", 8.4, 27.0, 180)      # IOVDD 10
    center(b, "C12", 12.6, 32.4, 270)    # IOVDD 22
    center(b, "C7", 14.2, 31.9, 270)     # DVDD 23
    center(b, "C13", 18.8, 27.0, 0)     # IOVDD 33
    center(b, "C14", 18.8, 23.4, 0)     # IOVDD 42
    center(b, "C16", 18.8, 22.2, 0)     # ADC_AVDD 43
    center(b, "C10", 17.4, 19.9, 90)    # VREG_VIN 44 (1u), hand-routed
    center(b, "C8", 16.4, 19.9, 90)     # VREG_VOUT 45 (1u), hand-routed
    center(b, "C6", 11.9, 20.4, 90)     # DVDD 50
    center(b, "C15", 18.45, 19.9, 90)    # IOVDD 49 / USB_VDD 48
    # crystal below XIN/XOUT (pins 20/21)
    center(b, "Y1", 10.0, 35.4, 0)
    center(b, "C3", 7.3, 35.6, 90)
    center(b, "C4", 12.8, 35.8, 90)
    center(b, "R5", 11.0, 32.0, 0)
    # boot / reset / LED / debug
    center(b, "R1", 7.2, 41.0, 0)
    center(b, "SW1", 9.3, 46.0, 0)
    center(b, "R9", 22.0, 41.0, 0)
    center(b, "SW2", 20.7, 46.0, 0)
    center(b, "R8", 21.0, 33.0, 0)
    center(b, "D1", 21.0, 35.0, 180)
    center(b, "J4", 12.46, 53.5, 90)                       # SWD 1x3 horizontal, bottom edge
    # 1x20 headers 0.9" apart (breadboard compatible), pin 1 at the top
    center(b, "J2", 3.57, 7.0, 0)
    center(b, "J3", 26.43, 7.0, 0)
    for ref, (x, y) in {"H1": (6.0, 2.6), "H2": (24.0, 2.6), "H3": (8.0, 54.8), "H4": (22.0, 54.8)}.items():
        center(b, ref, x, y, 0)


# ---------------- hand routing ----------------
def track(b, pts, net, layer, w):
    ni = b.FindNet(net)
    assert ni is not None, net
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
            continue
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(V(x1, y1))
        t.SetEnd(V(x2, y2))
        t.SetWidth(mm(w))
        t.SetLayer(layer)
        t.SetNet(ni)
        t.SetLocked(True)
        b.Add(t)


def via(b, x, y, net, d=VIA_D, drill=VIA_DRILL):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(V(x, y))
    v.SetDrill(mm(drill))
    v.SetWidth(pcbnew.F_Cu, mm(d))
    v.SetNet(b.FindNet(net))
    v.SetLocked(True)
    b.Add(v)


def route_usb(b):
    F, B = pcbnew.F_Cu, pcbnew.B_Cu
    dp_main, dm_main = P(b, "J1", "B6"), P(b, "J1", "B7")       # left: D+, right: D-
    dp_2nd, dm_2nd = P(b, "J1", "A6"), P(b, "J1", "A7")
    assert dp_main[0] < dp_2nd[0] < dm_main[0] and dp_main[0] < dm_2nd[0] < dm_main[0], (dp_main, dm_main)
    tip = dp_main[1] + 0.725                                     # inner end of the connector pads
    e1, e6, e3, e4 = P(b, "U4", "6"), P(b, "U4", "1"), P(b, "U4", "4"), P(b, "U4", "3")
    top_dp, bot_dp = sorted([e1, e6], key=lambda p: p[1])
    top_dm, bot_dm = sorted([e3, e4], key=lambda p: p[1])
    # connector -> ESD (straight, then 45 deg onto the ESD columns)
    for main, top in ((dp_main, top_dp), (dm_main, top_dm)):
        net = "/USB_DP" if main is dp_main else "/USB_DM"
        dx = abs(top[0] - main[0])
        track(b, [main, (main[0], top[1] - 1.0 - dx), (top[0], top[1] - 1.0), top], net, F, W_USB)
    # A6 (D+ second contact): via under the pad, cross under the D- contact on B.Cu, back up onto D+ main
    va = (dp_2nd[0], tip + 0.75)
    vb = (dp_main[0] - 0.45, tip + 0.75)
    track(b, [dp_2nd, va], "/USB_DP", F, W_USB_NECK)
    via(b, *va, "/USB_DP", d=0.40, drill=0.20)       # sits between two D- lines 0.5 mm apart
    track(b, [va, vb], "/USB_DP", B, W_USB)
    via(b, *vb, "/USB_DP", d=0.40, drill=0.20)
    track(b, [vb, (dp_main[0], vb[1])], "/USB_DP", F, W_USB)
    # A7 (D- second contact): down past the A6 via, then right onto D- main (F.Cu)
    yj = va[1] + 1.3
    track(b, [dm_2nd, (dm_2nd[0], yj), (dm_main[0], yj)], "/USB_DM", F, W_USB_NECK)
    # ESD VBUS (middle top) through a via between the pair, ESD GND (middle bottom) straight to the plane
    vbus, gnd = P(b, "U4", "5"), P(b, "U4", "2")
    track(b, [vbus, (vbus[0], vbus[1] - 0.9)], "/VBUS", F, 0.3)
    via(b, vbus[0], vbus[1] - 0.9, "/VBUS")
    track(b, [gnd, (gnd[0], gnd[1] + 0.9)], "/GND", F, 0.3)
    via(b, gnd[0], gnd[1] + 0.9, "/GND")
    # ESD -> 27R series resistors -> RP2040 USB_DP (47) / USB_DM (46)
    for bot, r, pin, net_a, net_b in ((bot_dp, "R3", "47", "/USB_DP", "/USB_DP_MCU"),
                                      (bot_dm, "R4", "46", "/USB_DM", "/USB_DM_MCU")):
        r1, r2, ip = P(b, r, "1"), P(b, r, "2"), P(b, "U2", pin)
        dx = abs(r1[0] - bot[0])
        track(b, [bot, (bot[0], r1[1] - 0.6 - dx), (r1[0], r1[1] - 0.6), r1], net_a, F, W_USB)
        dx2 = abs(ip[0] - r2[0])
        ybend = ip[1] - 1.2
        track(b, [r2, (r2[0], ybend - dx2), (ip[0], ybend)], net_b, F, W_USB_NECK)
        track(b, [(ip[0], ybend), ip], net_b, F, W_USB_NECK)
    # RP2040 top-edge supply pins fanned out to their own caps (Raspberry Pi minimal-design style):
    # 45 VREG_VOUT -> C8, 44 VREG_VIN -> C10, 43 ADC_AVDD -> C16, 50 DVDD -> C6. Paths never cross:
    # each pin goes straight up 0.3-0.7 mm past the pad tip, then 45 deg to its cap.
    (px, py), (cx_, cy_) = P(b, "U2", "45"), P(b, "C8", "1")
    y1 = py - 0.44 - 1.0
    track(b, [(px, py), (px, y1), (px + (y1 - cy_), cy_), (cx_, cy_)], "/+1V1", F, 0.2)
    (px, py), (cx_, cy_) = P(b, "U2", "44"), P(b, "C10", "1")
    track(b, [(px, py), (px, 21.6), (cx_, 21.6), (cx_, cy_)], "/+3V3", F, 0.2)
    (px, py), (cx_, cy_) = P(b, "U2", "43"), P(b, "C16", "1")
    track(b, [(px, py), (px, 22.0), (cx_, 22.0), (cx_, cy_)], "/+3V3", F, 0.2)
    # 43 ADC_AVDD and 44 VREG_VIN are both +3V3 and adjacent: bridge them on the pad tips
    (x43, y43), (x44, y44) = P(b, "U2", "43"), P(b, "U2", "44")
    track(b, [(x44, y44 - 0.25), (x43, y43 - 0.25)], "/+3V3", F, 0.2)
    # C12 (IOVDD 22 cap) +3V3 pad straight to the In2 pour
    cx_, cy_ = P(b, "C12", "1")
    track(b, [(cx_, cy_), (cx_ + 0.75, cy_)], "/+3V3", F, 0.25)
    via(b, cx_ + 0.75, cy_, "/+3V3", d=0.40, drill=0.20)
    # 23 DVDD straight down to C7 (placed directly under the pin)
    track(b, [P(b, "U2", "23"), P(b, "C7", "1")], "/+1V1", F, 0.2)
    # 42 IOVDD joins the 43/44 +3V3 group around the QFN corner; one via takes the group to the In2 pour
    (x42, y42) = P(b, "U2", "42")
    jx = x42 + 0.44
    track(b, [(x42, y42), (jx, y42), (jx, 22.0)], "/+3V3", F, 0.2)
    via(b, jx, 22.0, "/+3V3", d=0.40, drill=0.20)
    # +1V1: pin 50 side and pin 45 side sit on opposite sides of the USB pair -> join them on B.Cu
    v1 = (P(b, "U2", "50")[0] - (P(b, "U2", "50")[1] - 0.44 - 0.3 - P(b, "C6", "1")[1]), P(b, "C6", "1")[1])
    v2 = (P(b, "U2", "45")[0] + (P(b, "U2", "45")[1] - 0.44 - 1.0 - P(b, "C8", "1")[1]), P(b, "C8", "1")[1])
    via(b, *v1, "/+1V1", d=0.40, drill=0.20)
    via(b, *v2, "/+1V1", d=0.40, drill=0.20)
    track(b, [v1, v2], "/+1V1", B, 0.3)
    # 48 USB_VDD + 49 IOVDD: joined above the pads, small via straight down to the In2 +3V3 pour
    (x48, y48), (x49, y49) = P(b, "U2", "48"), P(b, "U2", "49")
    vx, vy = (x48 + x49) / 2, y48 - 1.05
    track(b, [(x49, y49), (x49, y49 - 0.6), (vx, vy)], "/+3V3", F, 0.2)
    track(b, [(x48, y48), (x48, y48 - 0.6), (vx, vy)], "/+3V3", F, 0.2)
    via(b, vx, vy, "/+3V3", d=0.40, drill=0.20)
    (px, py), (cx_, cy_) = P(b, "U2", "50"), P(b, "C6", "1")
    y1 = py - 0.44 - 0.3
    track(b, [(px, py), (px, y1), (px - (y1 - cy_), cy_), (cx_, cy_)], "/+1V1", F, 0.2)
    # GND via right next to the GND pad of every 2-pad part (decoupling caps, LED, CC resistors, ...):
    # placed along the part axis, 0.65 mm beyond the pad, so the cap's loop is pad -> via -> plane.
    for fp in b.GetFootprints():
        pads = list(fp.Pads())
        if len(pads) != 2:
            continue
        g = [p for p in pads if p.GetNetname() == "/GND"]
        o = [p for p in pads if p.GetNetname() != "/GND"]
        if len(g) != 1 or len(o) != 1:
            continue
        gx, gy = g[0].GetPosition().x / 1e6, g[0].GetPosition().y / 1e6
        ox, oy = o[0].GetPosition().x / 1e6, o[0].GetPosition().y / 1e6
        L = ((gx - ox) ** 2 + (gy - oy) ** 2) ** 0.5
        reach = max(g[0].GetSize().x, g[0].GetSize().y) / 2e6 + 0.45
        vx, vy = gx + (gx - ox) / L * reach, gy + (gy - oy) / L * reach
        track(b, [(gx, gy), (vx, vy)], "/GND", F, 0.3)
        via(b, vx, vy, "/GND")
    gx, gy = P(b, "U3", "4")                                     # flash GND pin
    track(b, [(gx, gy), (gx, gy + 1.0)], "/GND", F, 0.3)
    via(b, gx, gy + 1.0, "/GND")
    # RP2040 exposed pad: 3x3 GND vias to In1.Cu
    cx, cy = U2C
    for dx in (-1.0, 0.0, 1.0):
        for dy in (-1.0, 0.0, 1.0):
            via(b, cx + dx, cy + dy, "/GND")


# ---------------- netlist -> board ----------------
def netlist():
    out = REP / "rp2040_usbc.net"
    subprocess.run([CLI, "sch", "export", "netlist", "-o", str(out), str(SCH)], check=True, capture_output=True)
    t = re.sub(r"\s+", " ", out.read_text(encoding="utf-8"))
    comps = {}
    for ch in t.split("(libparts")[0].split("(comp (ref ")[1:]:
        ref = re.match(r'"([^"]+)"', ch).group(1)
        fields = dict(re.findall(r'\(field \(name "([^"]+)"\)(?: "([^"]*)")?\)', ch))
        comps[ref] = {"value": re.search(r'\(value "([^"]*)"\)', ch).group(1),
                      "fp": re.search(r'\(footprint "([^"]*)"\)', ch).group(1),
                      "fields": {k: v for k, v in fields.items() if k not in ("Footprint", "Value", "Reference")},
                      "uuid": re.search(r'\(tstamps "([^"]+)"\)', ch).group(1),
                      "no_bom": '(name "exclude_from_bom")' in ch}
    pins = {}
    for ch in t.split("(net (code ")[1:]:
        name = re.search(r'\(name "([^"]*)"\)', ch).group(1)
        for r_, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', ch):
            pins[(r_, p)] = name
    return comps, pins


def outline(b):
    pts = [(0, 0), (W, 0), (W, H), (0, H)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        s.SetStart(V(x1, y1))
        s.SetEnd(V(x2, y2))
        b.Add(s)


def zone(b, net, layer, margin=0.5, clearance=0.2):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNetCode(b.FindNet(net).GetNetCode())
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(0.2))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in [(margin, margin), (W - margin, margin), (W - margin, H - margin), (margin, H - margin)]:
        o.Append(mm(x), mm(y))
    z.thisown = 0
    b.Add(z)


def place():
    comps, pins = netlist()
    b = pcbnew.NewBoard(str(PCB))
    b.SetCopperLayerCount(4)
    nets = {}
    for name in sorted(set(pins.values())):
        ni = pcbnew.NETINFO_ITEM(b, name)
        b.Add(ni)
        nets[name] = ni
    for ref, c in comps.items():
        lib, name = c["fp"].split(":")
        fp = pcbnew.FootprintLoad(str(FPLIB / f"{lib}.pretty"), name)
        assert fp is not None, c["fp"]
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetFPIDAsString(c["fp"])
        for k_, v_ in c["fields"].items():
            fp.SetField(k_, v_)
            if k_ not in ("Reference", "Value"):
                fp.GetField(k_).SetVisible(False)
        fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        fp.SetSheetname("rp2040_usbc")
        fp.SetSheetfile("rp2040_usbc.kicad_sch")
        fp.SetExcludedFromBOM(c["no_bom"])
        if ref.startswith("H"):
            fp.Reference().SetVisible(False)
        b.Add(fp)
        for pad in fp.Pads():
            if (ref, pad.GetNumber()) in pins:
                pad.SetNet(nets[pins[(ref, pad.GetNumber())]])
    place_all(b)
    route_usb(b)
    outline(b)
    zone(b, "/GND", pcbnew.In1_Cu)
    # +3V3 is routed as a normal net (Freerouting cannot fan SMD pads out to a plane); the In2 pour is added in finish()
    ds = b.GetDesignSettings()
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_MinClearance = mm(0.15)
    ds.m_ViasMinSize = mm(0.40)
    ds.m_MinThroughDrill = mm(0.20)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(0.15))
    nc.SetTrackWidth(mm(0.2))
    nc.SetViaDiameter(mm(VIA_D))
    nc.SetViaDrill(mm(VIA_DRILL))
    pcbnew.SaveBoard(str(PCB), b)
    print("placed", len(comps), "footprints,", len(nets), "nets")


def export_dsn():
    b = pcbnew.LoadBoard(str(PCB))
    dsn = REP / "route.dsn"
    assert pcbnew.ExportSpecctraDSN(b, str(dsn)), "DSN export failed"
    t = dsn.read_text(encoding="utf-8")
    s = t.index("(class kicad_default")
    e = t.index("(circuit", s)
    names = re.findall(r'"[^"]*"|[^\s()]+', t[s + len("(class kicad_default"):e])
    pw = [n for n in names if n.strip('"') in ("/VBUS", "/+3V3", "/+1V1", "/GND")]
    rest = [n for n in names if n not in pw]
    via = f'(circuit (use_via "Via[0-3]_{int(VIA_D * 1000)}:{int(VIA_DRILL * 1000)}_um"))'
    new = (f"(class PWR {' '.join(pw)} {via} (rule (width 400) (clearance 150)))\n    "
           f"(class kicad_default {' '.join(rest)}\n      ")
    t = t[:s] + new + t[e:]
    t = re.sub(r"\(width \d+\)\n(\s+)\(clearance \d+\)", r"(width 200)\n\1(clearance 150)", t, count=1)
    # inner layers are planes only: the router must not put tracks on them
    t = re.sub(r"\(layer (In[12]\.Cu)\s+\(type signal\)", lambda m: "(layer " + m.group(1) + " (type power)", t)
    dsn.write_text(t, encoding="utf-8")
    print("DSN planes:", re.findall(r"\(plane (\S+)", t), "| layers:", re.findall(r"\(layer (\S+)\s+\(type (\w+)", t))


def route():
    (REP / "route.ses").unlink(missing_ok=True)
    with open(REP / "freerouting.log", "w") as log:
        subprocess.run([JAVA, "-jar", FR_JAR, "-de", str(REP / "route.dsn"), "-do", str(REP / "route.ses"),
                        "-mp", "100", "--gui.enabled=false", "--router.fanout.enabled=true"], check=True, timeout=900, stdout=log,
                       stderr=subprocess.STDOUT)
    assert (REP / "route.ses").exists()
    tail = (REP / "freerouting.log").read_text(errors="replace")
    print([l.split("] ")[-1][:160] for l in tail.splitlines() if "final score" in l][-1:])


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


def stitch(b, pitch=2.5, keep=0.5):
    """GND stitching vias on a grid; skip any spot closer than `keep` mm (edge to edge) to other-net copper
    or inside a courtyard, so F/B pours are tied to the In1 plane everywhere."""
    gnd = b.FindNet("/GND").GetNetCode()
    segs = []
    for t in b.GetTracks():
        if t.GetNetCode() == gnd and t.GetClass() != "PCB_VIA":   # GND vias still count: hole-to-hole
            continue
        s, e = t.GetStart(), t.GetEnd()
        hw = t.GetWidth(pcbnew.F_Cu) / 2e6 if t.GetClass() == "PCB_VIA" else t.GetWidth() / 2e6
        segs.append((s.x / 1e6, s.y / 1e6, e.x / 1e6, e.y / 1e6, hw))
    boxes = []
    for fp in b.GetFootprints():
        bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
        boxes.append((bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6))
        for p in fp.Pads():
            pb = p.GetBoundingBox()
            boxes.append((pb.GetLeft() / 1e6 - keep, pb.GetTop() / 1e6 - keep,
                          pb.GetRight() / 1e6 + keep, pb.GetBottom() / 1e6 + keep))
    n, y = 0, 1.5
    while y < H - 1:
        x = 1.5
        while x < W - 1:
            if all(not (l <= x <= r and t_ <= y <= bt) for l, t_, r, bt in boxes) and \
                    all(_seg_dist(x, y, ax, ay, bx, by) - hw - VIA_D / 2 >= keep for ax, ay, bx, by, hw in segs):
                via(b, x, y, "/GND")
                n += 1
            x += pitch
        y += pitch
    return n


def fix_starved():
    rep = REP / "_starved.json"
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "-o", str(rep), str(PCB)], capture_output=True)
    hits = set()
    for v in json.loads(rep.read_text(encoding="utf-8"))["violations"]:
        if v["type"] == "starved_thermal":
            for it in v["items"]:
                m = re.match(r"(?:PTH )?[Pp]ad (\S+) \[/GND\] of (\S+)", it["description"])
                if m:
                    hits.add((m.group(2), m.group(1)))
    rep.unlink()
    if not hits:
        return
    b = pcbnew.LoadBoard(str(PCB))
    for ref, num in hits:
        for p in b.FindFootprintByReference(ref).Pads():
            if p.GetNumber() == num:
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB), b)
    print("starved -> solid:", sorted(hits))


def finish():
    b = pcbnew.LoadBoard(str(PCB))
    assert pcbnew.ImportSpecctraSES(b, str(REP / "route.ses")), "SES import failed"
    print("stitch vias:", stitch(b))
    zone(b, "/+3V3", pcbnew.In2_Cu)
    zone(b, "/GND", pcbnew.F_Cu, clearance=0.25)
    zone(b, "/GND", pcbnew.B_Cu, clearance=0.25)
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(PCB), b)
    b = pcbnew.LoadBoard(str(PCB))
    b.BuildConnectivity()
    print("unconnected:", b.GetConnectivity().GetUnconnectedCount(True), "tracks:", len(b.GetTracks()))
    fix_starved()


def tidy_silk(rounds=4):
    """1.0 mm reference text (JLC minimum); any ref DRC reports over copper / over other silk is tried at the 4 sides of
    its courtyard in turn; refs that never fit go to F.Fab (assembly drawing). Returns the moved-to-Fab list."""
    b = pcbnew.LoadBoard(str(PCB))
    for fp in b.GetFootprints():
        r = fp.Reference()
        r.SetTextSize(V(1.0, 1.0))           # JLC: min silkscreen text height 1.0 mm
        r.SetTextThickness(mm(0.15))         # JLC: min silkscreen line width 0.15 mm
        r.SetTextAngleDegrees(0)
    pcbnew.SaveBoard(str(PCB), b)
    tried: dict[str, int] = {}
    for _ in range(rounds + 1):
        rep = REP / "_silk.json"
        subprocess.run([CLI, "pcb", "drc", "--format", "json", "-o", str(rep), str(PCB)], capture_output=True)
        bad = set()
        for v in json.loads(rep.read_text(encoding="utf-8"))["violations"]:
            if v["type"] in ("silk_over_copper", "silk_overlap", "silk_edge_clearance"):
                for it in v["items"]:
                    m = re.match(r"Reference field of (\S+)", it["description"])
                    if m:
                        bad.add(m.group(1))
        rep.unlink()
        if not bad:
            break
        b = pcbnew.LoadBoard(str(PCB))
        for ref in bad:
            fp = b.FindFootprintByReference(ref)
            k = tried.get(ref, 0)
            tried[ref] = k + 1
            if k >= 4:
                fp.Reference().SetLayer(pcbnew.F_Fab)
                continue
            bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            cx, cy = bb.Centre().x / 1e6, bb.Centre().y / 1e6
            hw, hh = bb.GetWidth() / 2e6, bb.GetHeight() / 2e6
            spots = [(cx, cy - hh - 0.6), (cx, cy + hh + 0.6), (cx - hw - 1.2, cy), (cx + hw + 1.2, cy)]
            fp.Reference().SetPosition(V(*spots[k]))
        pcbnew.SaveBoard(str(PCB), b)
    b = pcbnew.LoadBoard(str(PCB))
    fab = sorted(fp.GetReference() for fp in b.GetFootprints()
                 if fp.Reference().GetLayer() == pcbnew.F_Fab and fp.Reference().IsVisible())
    print("refs moved to F.Fab:", fab)
    return fab


def unconnected_count():
    rep = REP / "_unc.json"
    subprocess.run([CLI, "pcb", "drc", "--format", "json", "-o", str(rep), str(PCB)], capture_output=True)
    n = len(json.loads(rep.read_text(encoding="utf-8")).get("unconnected_items", []))
    rep.unlink()
    return n


def build_until_clean(tries=6):
    """Freerouting is not deterministic around the 0.4 mm QFN: rebuild until a run leaves 0 unconnected."""
    for i in range(1, tries + 1):
        place(); export_dsn(); route(); finish()
        n = unconnected_count()
        print(f"attempt {i}: {n} unconnected")
        if n == 0:
            return
    raise SystemExit("no clean route after %d attempts" % tries)


if __name__ == "__main__":
    if sys.argv[1:] == ["clean"]:
        REP.mkdir(exist_ok=True)
        build_until_clean()
        sys.exit(0)
    REP.mkdir(exist_ok=True)
    steps = {"place": place, "dsn": export_dsn, "route": route, "finish": finish, "silk": tidy_silk}
    for s in (sys.argv[1:] if sys.argv[1:] != ["all"] else ["place", "dsn", "route", "finish"]):
        steps[s]()
