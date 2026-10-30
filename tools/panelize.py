"""2x2 production panel of rp2040_usbc.kicad_pcb for JLCPCB (run with KiCad's python, KiCad closed).

Numbers follow https://jlcpcb.com/capabilities/pcb-capabilities (fetched 2026-10-30):
  5 mm tooling edges, 2 mm tooling holes and 1 mm fiducials centred 3.85 mm from the panel edges;
  breakaway tab >= 5 mm wide when it carries mouse bites; mouse-bite holes 0.5-0.8 mm, 0.2-0.3 mm apart.
Edge.Cuts = panel rectangle + every routed slot (frame interior minus boards minus tabs), so each slot is
one closed outline and the board edges inside a tab stay uncut.
"""
import shutil
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "rp2040_usbc.kicad_pcb"
OUT_DIR = ROOT / "panel"
OUT = OUT_DIR / "rp2040_usbc_panel.kicad_pcb"
mm = pcbnew.FromMM

BW, BH = 30.0, 58.0          # single board
RAIL, GAP = 5.0, 2.0         # tooling edge, routed slot between boards
TAB_W = 5.0                  # JLC minimum width of a tab that carries mouse bites
BITE_D, BITE_PITCH = 0.5, 0.8  # 0.5 mm holes, 0.3 mm web between them
COLS, ROWS = 2, 2
# the routed slot runs inside the 5 mm rail, so the rail stays 5 mm of solid board for tooling holes/fiducials
PW = 2 * (RAIL + GAP) + COLS * BW + (COLS - 1) * GAP
PH = 2 * (RAIL + GAP) + ROWS * BH + (ROWS - 1) * GAP

# tab centres in board coordinates: (side, position along that side). The top edge carries the M2 holes
# and the USB-C receptacle, so no tab can sit there; boards hang on 2+2 side tabs, and the bottom row also
# on 2 tabs to the bottom rail.
SIDE_TABS = [("L", 14.0), ("L", 44.0), ("R", 14.0), ("R", 44.0)]
BOTTOM_TABS = [("B", 4.0), ("B", 26.0)]


def tabs(r):
    return SIDE_TABS + (BOTTOM_TABS if r == ROWS - 1 else [])


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def origin(c, r):
    return RAIL + GAP + c * (BW + GAP), RAIL + GAP + r * (BH + GAP)


def rect_poly(x0, y0, x1, y1):
    ps = pcbnew.SHAPE_POLY_SET()
    ps.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ps.Append(mm(x), mm(y))
    return ps


def tab_rect(ox, oy, side, pos):
    """Tab rectangle spanning from the board edge across the slot/rail gap (GAP wide)."""
    h = TAB_W / 2
    if side == "L":
        return ox - GAP, oy + pos - h, ox, oy + pos + h
    if side == "R":
        return ox + BW, oy + pos - h, ox + BW + GAP, oy + pos + h
    if side == "T":
        return ox + pos - h, oy - GAP, ox + pos + h, oy
    return ox + pos - h, oy + BH, ox + pos + h, oy + BH + GAP


def bites(ox, oy, side, pos):
    """Hole centres on the board edge across the tab (one row per board edge the tab touches)."""
    n = int((TAB_W - BITE_D) // BITE_PITCH) + 1
    span = (n - 1) * BITE_PITCH
    along = [pos - span / 2 + i * BITE_PITCH for i in range(n)]
    if side == "L":
        return [(ox, oy + a) for a in along]
    if side == "R":
        return [(ox + BW, oy + a) for a in along]
    if side == "T":
        return [(ox + a, oy) for a in along]
    return [(ox + a, oy + BH) for a in along]


def one_pad_fp(b, x, y, ref, npth_d=None, smd_d=None, mask_d=None):
    """Footprint with one round pad, built in code (FootprintLoad is broken in KiCad 10's python):
    an NPTH hole of npth_d, or an F.Cu SMD dot of smd_d with a mask opening of mask_d (fiducial)."""
    fp = pcbnew.FOOTPRINT(b)
    fp.SetReference(ref)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    pad = pcbnew.PAD(fp)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    if npth_d:
        pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
        pad.SetSize(V(npth_d, npth_d))
        pad.SetDrillSize(V(npth_d, npth_d))
        lset = pcbnew.LSET()
        lset.AddLayer(pcbnew.F_Mask)
        lset.AddLayer(pcbnew.B_Mask)
        pad.SetLayerSet(lset)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
    else:
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad.SetSize(V(smd_d, smd_d))
        lset = pcbnew.LSET()
        lset.AddLayer(pcbnew.F_Cu)
        lset.AddLayer(pcbnew.F_Mask)
        pad.SetLayerSet(lset)
        pad.SetLocalSolderMaskMargin(mm((mask_d - smd_d) / 2))
        fp.SetExcludedFromBOM(True)
    fp.Add(pad)
    fp.SetPosition(V(x, y))
    b.Add(fp)
    return fp


def main():
    OUT_DIR.mkdir(exist_ok=True)
    shutil.copy(SRC, OUT)                                   # same rules, net classes and nets as the board
    shutil.copy(SRC.with_suffix(".kicad_pro"), OUT.with_suffix(".kicad_pro"))
    b = pcbnew.LoadBoard(str(OUT))
    # the panel outline replaces the board outline; keep the removed shapes referenced; letting Python free
    # them right after BOARD.Remove() crashes the next GetFootprints() in KiCad 10
    old_edge = [d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    for d in old_edge:
        b.Remove(d)
    items = list(b.GetFootprints()) + list(b.GetTracks()) + list(b.Zones()) + list(b.GetDrawings())
    for c in range(COLS):
        for r in range(ROWS):
            if (c, r) != (0, 0):
                off = V(*origin(c, r))
                for it in items:
                    try:                            # KiCad 10: footprints and zones take addToParentGroup
                        n = it.Duplicate(False)
                    except TypeError:
                        n = it.Duplicate()
                    n.thisown = 0                   # the board owns the copy, not Python
                    n.Move(off)
                    b.Add(n)
    for it in items:                                        # originals last, so the copies start from (0, 0)
        it.Move(V(*origin(0, 0)))
    # routed slots = frame interior - boards - tabs
    voids = rect_poly(RAIL, RAIL, PW - RAIL, PH - RAIL)
    holes = []
    for c in range(COLS):
        for r in range(ROWS):
            ox, oy = origin(c, r)
            voids.BooleanSubtract(rect_poly(ox, oy, ox + BW, oy + BH))
            for side, pos in tabs(r):
                voids.BooleanSubtract(rect_poly(*tab_rect(ox, oy, side, pos)))
                holes += bites(ox, oy, side, pos)
    seg = 0
    for i in range(voids.OutlineCount()):
        ol = voids.Outline(i)
        pts = [ol.CPoint(k) for k in range(ol.PointCount())]
        for a, c_ in zip(pts, pts[1:] + pts[:1]):
            s = pcbnew.PCB_SHAPE(b)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetLayer(pcbnew.Edge_Cuts)
            s.SetWidth(mm(0.1))
            s.SetStart(a)
            s.SetEnd(c_)
            b.Add(s)
            seg += 1
    for (x0, y0), (x1, y1) in zip([(0, 0), (PW, 0), (PW, PH), (0, PH)], [(PW, 0), (PW, PH), (0, PH), (0, 0)]):
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        s.SetStart(V(x0, y0))
        s.SetEnd(V(x1, y1))
        b.Add(s)
    # mouse bites (NPTH 0.5 mm), tooling holes (NPTH 2 mm) and fiducials on the rails
    for k, (x, y) in enumerate(sorted(set((round(x, 3), round(y, 3)) for x, y in holes))):
        one_pad_fp(b, x, y, f"MB{k + 1}", npth_d=BITE_D)
    e = 3.85
    for k, (x, y) in enumerate([(e, e), (PW - e, e), (e, PH - e), (PW - e, PH - e)]):
        one_pad_fp(b, x, y, f"TH{k + 1}", npth_d=2.0)
    for k, (x, y) in enumerate([(12.0, e), (PW - 12.0, e), (PW / 2, PH - e)]):   # clear of the USB-C bodies
        one_pad_fp(b, x, y, f"FID{k + 1}", smd_d=1.0, mask_d=2.0)
    txt = pcbnew.PCB_TEXT(b)
    txt.SetText("RP2040 USB-C  2x2 panel  JLC04161H-7628")
    txt.SetLayer(pcbnew.F_SilkS)
    txt.SetTextSize(V(1.5, 1.5))
    txt.SetTextThickness(mm(0.2))
    txt.SetPosition(V(PW / 2, PH - 1.6))
    b.Add(txt)
    b.BuildConnectivity()
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(str(OUT), b)
    print(f"panel {PW:.1f} x {PH:.1f} mm, slot outlines {voids.OutlineCount()}, edge segments {seg}, "
          f"mouse-bite holes {len(set(holes))}")


if __name__ == "__main__":
    main()
