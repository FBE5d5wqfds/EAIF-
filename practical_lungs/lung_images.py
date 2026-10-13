"""Synthetic grey-scale chest images for L1_P4 (64 x 64 pixels, three smoking classes).

The images are NOT realistic radiographs. They contain a schematic chest (body, two lungs, heart shadow,
spine, ribs) and, inside the lungs, small bright nodules and thin streaks whose number grows with
smoking exposure. This mimics the "dirty chest" of smokers: more lung markings on the radiograph,
which grow with pack-years (Kirchner et al., 2012, Br J Radiol 85:339-345).
Every image then receives a random rotation, scale, shear (a crude change of perspective) and shift,
as if patients stood differently in front of the detector.

Usage:  python lung_images.py   -> writes data/lung_xray/*.png and data/lung_xray/annotations.csv
"""
import numpy as np
from scipy import ndimage as ndi

N_PIX = 64
CLASSES = ["never", "former", "current"]          # never smoked / quit within the last 5 years / smokes now
LABELS = {"never": "never smoked", "former": "former smoker, quit within the last 5 years", "current": "current smoker"}


def _ellipse(yy, xx, cy, cx, ry, rx):
    return ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1.0


def make_image(label, rng, n=N_PIX):
    yy, xx = np.mgrid[0:n, 0:n].astype(float)
    img = np.full((n, n), 0.15)                                   # air outside the body: dark
    body = _ellipse(yy, xx, 34, 32, 30 + rng.normal(0, 1), 27 + rng.normal(0, 1.5))
    img[body] = 0.62                                              # soft tissue: bright
    w = rng.uniform(0.9, 1.1)                                     # patient build
    lungL = _ellipse(yy, xx, 33, 20, 17 * w, 8.5 * w)
    lungR = _ellipse(yy, xx, 33, 44, 17 * w, 8.5 * w)
    lungs = lungL | lungR
    img[lungs] = 0.28                                             # aerated lung: dark
    img += 0.10 * np.exp(-(((yy - 44) / 7) ** 2 + ((xx - 29) / 7) ** 2))   # heart shadow
    img[(np.abs(xx - 32) < 2.2) & body] += 0.12                   # spine
    for k in range(6):                                            # ribs: faint bright arcs
        yr = 19 + 5 * k + rng.normal(0, 0.4)
        arc = np.abs(yy - (yr + 0.012 * (xx - 32) ** 2)) < 0.9
        img[arc & lungs] += 0.04
    # ---- class-specific local patterns inside the lungs
    ly, lx = np.where(lungs)
    n_nod = {"never": rng.integers(0, 2), "former": rng.integers(3, 6), "current": rng.integers(8, 13)}[label]
    n_str = {"never": 0, "former": rng.integers(0, 2), "current": rng.integers(3, 6)}[label]
    amp = 0.45
    for _ in range(n_nod):                                        # small round nodules
        i = rng.integers(len(ly)); r = rng.uniform(1.8, 2.6)
        img += amp * np.exp(-(((yy - ly[i]) / r) ** 2 + ((xx - lx[i]) / r) ** 2)) * lungs
    for _ in range(n_str):                                        # thin linear streaks
        i = rng.integers(len(ly)); ang = rng.uniform(0, np.pi); L = rng.uniform(4, 8)
        t = np.linspace(-L / 2, L / 2, 30)
        for s in t:
            cy, cx = ly[i] + s * np.sin(ang), lx[i] + s * np.cos(ang)
            img += 0.9 * amp / 4 * np.exp(-(((yy - cy) / 0.7) ** 2 + ((xx - cx) / 0.7) ** 2)) * lungs
    img += rng.normal(0, 0.03, img.shape)                         # sensor noise
    img = ndi.gaussian_filter(img, 0.6)
    # ---- acquisition variation: rotation, shift, scale and a slight shear (perspective)
    ang = np.deg2rad(rng.uniform(-12, 12)); sc = rng.uniform(0.9, 1.1); sh = rng.uniform(-0.08, 0.08)
    A = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]]) @ np.array([[1, sh], [0, 1]]) / sc
    c = np.array([n / 2, n / 2]); off = c - A @ c + rng.uniform(-4, 4, 2)
    img = ndi.affine_transform(img, A, offset=off, order=1, mode="constant", cval=0.15)
    # ---- exposure variation; then standardise so overall brightness carries no class information
    img = img * rng.uniform(0.9, 1.1) + rng.uniform(-0.05, 0.05)
    lo, hi = np.percentile(img, [5, 90])                           # air and soft tissue as reference levels
    img = 0.10 + 0.50 * (img - lo) / (hi - lo)                     # same grey scale for every image
    return np.clip(img, 0, 1).astype(np.float32)


def make_dataset(n_per_class=20, seed=2026):
    rng = np.random.default_rng(seed)
    X, y = [], []
    for k, lab in enumerate(CLASSES):
        for _ in range(n_per_class):
            X.append(make_image(lab, rng)); y.append(k)
    return np.stack(X), np.array(y)


def save_dataset(folder="data/lung_xray", n_per_class=20, seed=2026):
    """Write one PNG per image and an annotation table; the order of the files is shuffled."""
    from pathlib import Path
    import pandas as pd
    from PIL import Image
    X, y = make_dataset(n_per_class, seed)
    out = Path(folder); out.mkdir(parents=True, exist_ok=True)
    order = np.random.default_rng(seed + 1).permutation(len(y))
    rows = []
    for j, i in enumerate(order, 1):
        name = f"chest_{j:03d}.png"
        Image.fromarray(np.round(X[i] * 255).astype(np.uint8), mode="L").save(out / name)
        rows.append(dict(image_id=f"chest_{j:03d}", file=name, smoking_status=CLASSES[y[i]], description=LABELS[CLASSES[y[i]]]))
    pd.DataFrame(rows).to_csv(out / "annotations.csv", index=False)
    return out


if __name__ == "__main__":
    print("written to", save_dataset())
