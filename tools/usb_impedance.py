"""USB diff pair on JLC04161H-7628 (jlcpcb.com/impedance), L1 over L2 GND: prepreg 7628 h=0.2104 mm, Er=4.4, Cu 0.035 mm.
Z0: Hammerstad-Jensen (scikit-rf MLine) cross-checked with IPC-2141; Zdiff = 2*Z0*(1-0.48*exp(-0.96*s/h)) (IPC-2141).
Formula estimate, not a field solver: expect about +-10%."""
import math
import numpy as np
import skrf
from skrf.media import MLine

H, ER, T = 0.2104e-3, 4.4, 0.035e-3


def z0_hj(w):
    f = skrf.Frequency(10, 10, 1, "MHz")
    ml = MLine(frequency=f, w=w, h=H, t=T, ep_r=ER, rough=0, tand=0, model="hammerstadjensen",
               disp="none", compatibility_mode=None)
    return float(np.real(ml.z0[0]))


def z0_ipc(w):  # IPC-2141 microstrip, cross-check of the skrf value
    return 87 / math.sqrt(ER + 1.41) * math.log(5.98 * H / (0.8 * w + T))


def zdiff(w, s):
    return 2 * z0_hj(w) * (1 - 0.48 * math.exp(-0.96 * s / H))


if __name__ == "__main__":
    for s in (0.15e-3, 0.2e-3):
        lo, hi = 0.05e-3, 0.6e-3
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if zdiff(mid, s) > 90 else (lo, mid)
        w = (lo + hi) / 2
        print(f"s={s*1e3:.2f} mm -> w={w*1e3:.3f} mm: Z0(HJ)={z0_hj(w):.1f} Z0(IPC)={z0_ipc(w):.1f} Zdiff={zdiff(w, s):.1f}")
    for w, s in ((0.30e-3, 0.15e-3), (0.25e-3, 0.15e-3), (0.20e-3, 0.15e-3)):
        print(f"check w={w*1e3:.2f} s={s*1e3:.2f}: Zdiff={zdiff(w, s):.1f}  Z0={z0_hj(w):.1f}")
