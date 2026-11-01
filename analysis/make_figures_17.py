"""Figures for Field Note #17 (where the head-mounted camera points). Run after c1_view_direction.py, c2_self_occlusion.py, c3 labels."""
import os, glob, numpy as np, pandas as pd, cv2, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT = 'out17'; FIG = f'{OUT}/figures'; RAW = 'raw'; os.makedirs(FIG, exist_ok=True)
INK, GR, C1, C2 = '#1d232b', '#8a8f98', '#1f5fbf', '#d9622b'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10.5, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#e7eaee', 'axes.edgecolor': '#c9ced6', 'axes.axisbelow': True})
def save(fig, name): fig.savefig(f'{FIG}/{name}.png', dpi=170, bbox_inches='tight'); fig.savefig(f'{FIG}/{name}.svg', bbox_inches='tight'); plt.close(fig)
f_px, cy_px = 482.3, 2 * 306.28 + 0.5   # factory intrinsics scaled to 1600x1200
S = pd.read_csv(f'{OUT}/c1_per_second.csv.gz', dtype={'session': str})
S['clock'] = pd.to_datetime(S.session.str[:8] + S.session.str[9:], format='%Y%m%d%H%M%S') + pd.to_timedelta(S.sec, unit='s')

# 1) distribution and course over the morning
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={'width_ratios': [1, 1.25]})
ax = axs[0]; bands = [(-10, 30, '#eef2f7'), (45, 75, '#e3ecf9')]
for lo, hi, c in bands: ax.axvspan(lo, hi, color=c, zorder=0)
ax.hist(S.pitch_below_deg, bins=np.arange(-10, 91, 2.5), color=C1)
ax.axvline(S.pitch_below_deg.median(), color=C2, lw=1.5)
ax.text(S.pitch_below_deg.median() - 1.5, ax.get_ylim()[1] * 0.95, f'median {S.pitch_below_deg.median():.0f}°', color=C2, fontsize=9.5, ha='right')
sh = lambda lo, hi: ((S.pitch_below_deg >= lo) & (S.pitch_below_deg < hi)).mean() * 100
ax.text(9, ax.get_ylim()[1] * 0.55, f'< 30°\n{sh(-90, 30):.0f}% of time', ha='center', fontsize=9, color=INK)
ax.text(83, ax.get_ylim()[1] * 0.55, f'45–75°\n{sh(45, 75):.0f}%', ha='center', fontsize=9, color=INK)
ax.set_xlim(-10, 90); ax.set_xlabel('Optical axis below horizontal (°)'); ax.set_ylabel('Seconds')
ax.set_title(f'{len(S):,} s of real work, 1 s windows', loc='left', fontsize=10.5)
ax = axs[1]
B = S.groupby(S.clock.dt.floor('5min')).agg(n=('sec', 'size'), med=('pitch_below_deg', 'median'), q1=('pitch_below_deg', lambda v: v.quantile(.25)), q3=('pitch_below_deg', lambda v: v.quantile(.75)))
B = B[B.n >= 60]; x = B.index.hour + B.index.minute / 60 + 2.5 / 60
ax.fill_between(x, B.q1, B.q3, color='#c9d8f2', lw=0, label='Middle 50% of seconds'); ax.plot(x, B.med, 'o-', color=C1, ms=3.5, lw=1.3, label='Median per 5 min')
ax.axvspan(9.8, 10 + 20 / 60, color='#f4f4f4', zorder=0); ax.text(9.83, 8, 'carrying and\nstaging produce', fontsize=8.5, color=GR)
ax.text(11.2, 8, 'portioning at the bench', fontsize=8.5, color=GR)
ax.set_ylim(0, 90); ax.set_xticks([10, 11, 12]); ax.set_xticklabels(['10:00', '11:00', '12:00']); ax.set_ylabel('Below horizontal (°)'); ax.set_xlabel('Time of day, 2026-11-01')
ax.legend(frameon=False, fontsize=8.5, loc='upper right', ncol=2); ax.set_title('Course over the morning', loc='left', fontsize=10.5)
save(fig, 'fn17_view_direction')

# 2) validation: predicted horizon from the IMU on frames where the scene has a visible vanishing point
F = pd.read_csv(f'{OUT}/c1_sampled_frames.csv', dtype={'session': str})
picks = ['20261101_094808_00000_left_f005062.jpg', '20261101_094808_00000_left_f001687.jpg', '20261101_094808_00002_left_f005062.jpg']
fig, axs = plt.subplots(1, 3, figsize=(12, 3.4))
for ax, fn in zip(axs, picks):
    r = F[F.file == fn].iloc[0]; im = cv2.cvtColor(cv2.imread(glob.glob(f'{RAW}/*/frames/{fn}')[0]), cv2.COLOR_BGR2RGB)
    im = cv2.resize(im, (800, 600)); yh = (cy_px - np.radians(r.pitch_below_deg) * f_px) / 2
    ax.imshow(im); ax.axhline(yh, color='#ff3b30', lw=1.6); ax.axhline(cy_px / 2, color='#34c759', lw=0.9, ls='--')
    ax.set_title(f'IMU: {r.pitch_below_deg:.0f}° below horizontal', loc='left', fontsize=9.5); ax.axis('off')
save(fig, 'fn17_horizon_check')

# 3) example frames by pitch with own-body mask
L = pd.read_csv(f'{OUT}/c3_hand_labels.csv', dtype={'session': str})
ex = [12, 60, 88]
fig, axs = plt.subplots(1, 3, figsize=(12, 3.4))
for ax, lid in zip(axs, ex):
    r = L[L.lid == lid].iloc[0]; im = cv2.cvtColor(cv2.imread(glob.glob(f'{RAW}/*/frames/{r.file}')[0]), cv2.COLOR_BGR2RGB)
    im = cv2.resize(im, (640, 480)); m = cv2.resize(cv2.imread(f'{OUT}/mask_{r.file[:-4]}.png', 0), (640, 480)) > 0
    im[m] = (im[m] * 0.45 + np.array([217, 98, 43]) * 0.55).astype(np.uint8)
    ax.imshow(im); ax.axhline(240, color='white', lw=0.8, ls='--'); ax.axis('off')
    ax.set_title(f'{r.pitch_below_deg:.0f}° below horizontal · own body {r.body_share*100:.0f}% of frame', loc='left', fontsize=9.5)
save(fig, 'fn17_frames_by_pitch')

# 4) own-body share vs pitch, and where the hands are
D = pd.read_csv(f'{OUT}/c2_self_occlusion.csv', dtype={'session': str})
fig, axs = plt.subplots(1, 2, figsize=(11, 3.7))
ax = axs[0]; ax.scatter(D.pitch_below_deg, D.body_share * 100, s=10, color=C1, alpha=0.55, lw=0)
edges = [0, 30, 45, 60, 75, 91]; mids = [(a + b) / 2 for a, b in zip(edges[:-1], edges[1:])]
med = [D[(D.pitch_below_deg >= a) & (D.pitch_below_deg < b)].body_share.median() * 100 for a, b in zip(edges[:-1], edges[1:])]
ax.plot(mids, med, 'o-', color=C2, lw=1.8, ms=5, label='Median per 15° band')
ax.set_xlabel('Optical axis below horizontal (°)'); ax.set_ylabel("Frame covered by wearer's jacket (%)"); ax.set_xlim(0, 90); ax.set_ylim(0, 35)
ax.legend(frameon=False, fontsize=8.5, loc='upper left'); ax.set_title(f'Own body in view, {len(D)} sampled frames', loc='left', fontsize=10.5)
ax = axs[1]; hy = L.hand_y_frac.dropna() * 100
ax.hist(hy, bins=np.arange(30, 101, 5), color=C1, orientation='horizontal'); ax.invert_yaxis()
ax.axhline(50, color=GR, ls='--', lw=1); ax.text(ax.get_xlim()[1] * 0.98, 49, 'image centre row', ha='right', va='bottom', fontsize=8.5, color=GR)
ax.axhline(hy.median(), color=C2, lw=1.5); ax.text(ax.get_xlim()[1] * 0.98, hy.median() + 1, f'median {hy.median():.0f}% (≈{np.degrees((hy.median()/100-0.5)*1200/f_px):.0f}° below the axis)', ha='right', va='top', fontsize=8.5, color=C2)
ax.set_ylim(100, 30); ax.set_ylabel('Hand height in image (% from top)'); ax.set_xlabel('Frames')
ax.set_title(f'Where the hands are: {L.hands_visible.sum()} of {len(L)} frames show a hand', loc='left', fontsize=10.5)
save(fig, 'fn17_body_and_hands')
print('ok')
