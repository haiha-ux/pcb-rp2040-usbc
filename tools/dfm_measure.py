"""Measure the fab-relevant minimums actually present on the board (run with KiCad's python).
Printed as JSON so the README table can be checked against it."""
import itertools
import json
import math

import pcbnew

b = pcbnew.LoadBoard("rp2040_usbc.kicad_pcb")
mm = pcbnew.ToMM
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
pads = [p for f in b.GetFootprints() for p in f.Pads()]
holes = [(mm(v.GetPosition().x), mm(v.GetPosition().y), mm(v.GetDrillValue())) for v in vias] + \
        [(mm(p.GetPosition().x), mm(p.GetPosition().y), mm(min(p.GetDrillSize().x, p.GetDrillSize().y)))
         for p in pads if p.GetDrillSize().x > 0]
h2h = min(math.hypot(a[0] - c[0], a[1] - c[1]) - a[2] / 2 - c[2] / 2 for a, c in itertools.combinations(holes, 2))
edge = b.GetBoardEdgesBoundingBox()
cu_items = tracks + vias
def edge_dist(x, y):
    return min(x - mm(edge.GetLeft()), mm(edge.GetRight()) - x, y - mm(edge.GetTop()), mm(edge.GetBottom()) - y)
trk_edge = min(min(edge_dist(mm(t.GetStart().x), mm(t.GetStart().y)), edge_dist(mm(t.GetEnd().x), mm(t.GetEnd().y)))
               - mm(t.GetWidth()) / 2 for t in tracks)
silk_h = [mm(t.GetTextHeight()) for f in b.GetFootprints() for t in (f.Reference(),)
          if t.IsVisible() and t.GetLayer() == pcbnew.F_SilkS]
silk_w = [mm(t.GetTextThickness()) for f in b.GetFootprints() for t in (f.Reference(),)
          if t.IsVisible() and t.GetLayer() == pcbnew.F_SilkS]
ds = b.GetDesignSettings()
out = {
    "copper_layers": b.GetCopperLayerCount(),
    "board_mm": [round(mm(edge.GetWidth()), 2), round(mm(edge.GetHeight()), 2)],
    "min_track_mm": round(min(mm(t.GetWidth()) for t in tracks), 3),
    "rule_min_clearance_mm": round(mm(ds.m_MinClearance), 3),
    "min_via_dia_mm": round(min(mm(v.GetWidth(pcbnew.F_Cu)) for v in vias), 3),
    "min_via_drill_mm": round(min(mm(v.GetDrillValue()) for v in vias), 3),
    "min_via_ring_mm": round(min((mm(v.GetWidth(pcbnew.F_Cu)) - mm(v.GetDrillValue())) / 2 for v in vias), 3),
    "via_count": len(vias),
    "min_hole_to_hole_mm": round(h2h, 3),
    "min_track_to_board_edge_mm": round(trk_edge, 3),
    "zone_edge_clearance_mm": round(max(mm(z.GetLocalClearance() or 0) for z in b.Zones()), 3),
    "silk_ref_min_height_mm": round(min(silk_h), 3),
    "silk_ref_min_thickness_mm": round(min(silk_w), 3),
    "solder_mask_expansion_mm": round(mm(ds.m_SolderMaskExpansion), 3),
    "solder_mask_min_web_rule_mm": round(mm(ds.m_SolderMaskMinWidth), 3),
}
print(json.dumps(out, indent=1))
