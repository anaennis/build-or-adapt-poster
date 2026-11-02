"""Redraw the poster figures from the small tables in data/.

    python plot_figures.py            # writes PNGs to figures/

Needs: numpy, matplotlib. Uses the Libre Baskerville font if installed (or pass FONT_PATH=/path/to/LibreBaskerville.ttf)
(https://fonts.google.com/specimen/Libre+Baskerville), otherwise falls back to a serif.
"""
import csv, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures"); os.makedirs(FIG, exist_ok=True)
BURG, SLATE, GOLD, INK, GREY = "#7A2E4D", "#5B7083", "#B08D3C", "#3b3b3b", "#666666"
if os.environ.get("FONT_PATH"): fm.fontManager.addfont(os.environ["FONT_PATH"])   # optional: path to LibreBaskerville.ttf
fam = "Libre Baskerville" if any("Libre Baskerville" in f.name for f in fm.fontManager.ttflist) else "serif"
plt.rcParams.update({"font.family": fam, "font.size": 22, "text.color": INK, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.edgecolor": INK,
                     "xtick.labelsize": 22, "ytick.labelsize": 22, "axes.labelsize": 24})
WINDOWS = [96, 192, 384, 768, 960]; X = np.arange(5)

def read(name):
    with open(os.path.join(HERE, "data", name)) as f: return list(csv.DictReader(f))
def num(s): return float(s) if s not in ("", None) else None
def errbar(ax, xp, v, lo, hi, c, m):
    ax.errorbar(xp, v, yerr=[[v - lo], [hi - v]], color=c, marker=m, ms=14, lw=3.5, capsize=8, capthick=3)

# ---- tidal features: gain over the S2 baseline, primary config -------------------
gain = read("tidal_gain_primary_t0.5.csv")
def series(delta, kind):
    out = []
    for w in WINDOWS:
        r = next(r for r in gain if int(r["window_px"]) == w and r["delta"] == delta)
        out.append((num(r[f"d_{kind}"]), num(r[f"d_{kind}_lo"]), num(r[f"d_{kind}_hi"])))
    return out
def gain_fig(kind, ylabel, ylim, foot, fname):
    fig, ax = plt.subplots(figsize=(11, 8), dpi=300); ax.axhline(0, color=GREY, lw=2.5)
    for delta, dx, c, m, lab in [("S3-S2", -0.07, BURG, "o", "Embedding only"), ("S4-S2", 0.07, SLATE, "^", "Embedding + baseline")]:
        s = series(delta, kind); ax.plot(X + dx, [a[0] for a in s], color=c, lw=3.5, label=lab)
        for i, (v, lo, hi) in enumerate(s): errbar(ax, X[i] + dx, v, lo, hi, c, m)
    ax.set_xticks(X); ax.set_xticklabels(WINDOWS); ax.set_xlabel("Window size (pixels)"); ax.set_ylabel(ylabel)
    ax.set_ylim(*ylim); ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, loc="lower right", fontsize=21)
    fig.text(0.02, 0.012, foot, fontsize=20, color=GREY, va="bottom"); fig.tight_layout(rect=(0, 0.20, 1, 1))
    fig.savefig(os.path.join(FIG, fname), dpi=300); plt.close(fig)
gain_fig("auc", "Better at spotting tidal\ngalaxies (gain in AUC)", (-0.07, 0.16),
         "Pilot: 2000 galaxies, 264 positives, one run. Bars: 95% interval\nover sky regions. AUC = chance a tidal galaxy is ranked above\na non-tidal one (0.5 = guessing).", "tidal_gain_auc.png")
gain_fig("ap", "Better at flagging tidal\ngalaxies (gain in AP)", (-0.12, 0.34),
         "Pilot: 2000 galaxies, 264 positives, one run. Bars: 95% interval\nover sky regions. AP = precision of the flagged galaxies.", "tidal_gain_ap.png")

# ---- cluster richness (values transcribed from the project log) ---------------------
rich = read("richness_logged_values.csv")
fig, ax = plt.subplots(figsize=(11, 8), dpi=300); ax.axhline(0, color=GREY, lw=2.5)
for key, dx, c, m, lab in [("over_catalogue_baseline", -0.07, BURG, "o", "Over catalogue baseline"),
                           ("over_catalogue_plus_crowding_colour_counts", 0.07, GOLD, "s", "Over catalogue + crowding/colour counts")]:
    rs = [next(r for r in rich if int(r["window_px"]) == w and r["series"] == key) for w in WINDOWS]
    ax.plot(X + dx, [num(r["gain_r2"]) for r in rs], color=c, lw=3.5, label=lab)
    for i, r in enumerate(rs):
        v, lo, hi = num(r["gain_r2"]), num(r["lo"]), num(r["hi"])
        if lo is None: ax.plot(X[i] + dx, v, marker=m, ms=14, mfc="white", mec=c, mew=3)
        else: errbar(ax, X[i] + dx, v, lo, hi, c, m)
ax.set_xticks(X); ax.set_xticklabels(WINDOWS); ax.set_xlabel("Window size (pixels)")
ax.set_ylabel("Better at predicting\nrichness (gain in R\u00b2)"); ax.set_ylim(-0.04, 0.70)
ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, loc="upper left", fontsize=20)
fig.text(0.02, 0.012, "Exploratory, no pass bar. 1,962 redMaPPer clusters\n(DES Y3, z 0.25\u20130.35). Bars: logged intervals;\nhollow points have none logged.", fontsize=20, color=GREY, va="bottom")
fig.tight_layout(rect=(0, 0.20, 1, 1)); fig.savefig(os.path.join(FIG, "richness_gain.png"), dpi=300); plt.close(fig)

# ---- ablations: S3 minus S2 (AUC) ------------------------------------------------------
abl = read("tidal_gain_ablations.csv")
def pick(w, cfg):
    r = next(r for r in abl if int(r["window_px"]) == w and r["config"] == cfg and r["delta"] == "S3-S2")
    return num(r["d_auc"]), num(r["d_auc_lo"]), num(r["d_auc_hi"])
def prim(w):
    r = next(r for r in gain if int(r["window_px"]) == w and r["delta"] == "S3-S2")
    return num(r["d_auc"]), num(r["d_auc_lo"]), num(r["d_auc_hi"])
cols = [BURG, GOLD, BURG, SLATE]
fig, axes = plt.subplots(1, 3, figsize=(11.2, 5.4), dpi=300, sharey=True)
for ax, w in zip(axes, (384, 768, 960)):
    vals = [prim(w), pick(w, "nocolour"), pick(w, "cmask_SAME_orig"), pick(w, "cmask_SAME_cmask")]
    ax.axhline(0, color=GREY, lw=2)
    for i, (v, lo, hi) in enumerate(vals): errbar(ax, i if i < 2 else i + 0.6, v, lo, hi, cols[i], "o")
    ax.set_xticks([0.5, 3.1]); ax.set_xticklabels(["all\ngalaxies", "same\nsubset"], fontsize=19)
    ax.set_title(f"{w} px", fontsize=22); ax.spines[["top", "right"]].set_visible(False); ax.tick_params(axis="y", labelsize=20)
axes[0].set_ylabel("Gain in AUC\nover baseline", fontsize=22); axes[0].set_ylim(-0.01, 0.28)
h = [plt.Line2D([], [], marker="o", ls="", color=c, ms=13) for c in (BURG, GOLD, SLATE)]
fig.legend(h, ["Original", "Colour destroyed", "Galaxy masked"], loc="lower center", ncol=3, frameon=False, fontsize=20)
fig.tight_layout(rect=(0, 0.1, 1, 1)); fig.savefig(os.path.join(FIG, "tidal_ablations.png"), dpi=300); plt.close(fig)
print("wrote figures to", FIG)
