"""C1 — where the head-mounted camera points, per frame.
For every left frame (exposure centre): gravity direction from the accelerometer averaged over 1 s centred on the frame,
expressed in the camera frame (T_cam_imu), and gyro rotation about the vertical.
  pitch_below_deg : optical axis angle below horizontal (0 = looking level, 90 = straight down)
  roll_deg        : rotation about the optical axis (0 = image rows level); unreliable when pitch > 70 deg
  yaw_rate_dps    : head turning rate about the vertical, 1 s mean
Run: python c1_view_angles.py <packs_dir> <out_dir>   (calibration yaml from env ODL_CALIB)
"""
import sys, os, glob
import numpy as np, pandas as pd, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from read_zximu import load
RAW, OUT = sys.argv[1], sys.argv[2]
Y = yaml.safe_load(open(os.environ['ODL_CALIB']))
Rci = np.array(Y['cam0']['T_cam_imu'])[:3, :3]; shift_us = Y['cam0']['timeshift_cam_imu'] * 1e6
HALF = 250  # samples = 0.5 s at 500 Hz

def window_mean(t, X, tc):
    c = np.vstack([np.zeros(X.shape[1]), np.cumsum(X, 0)]); i = np.searchsorted(t, tc)
    lo = np.clip(i - HALF, 0, len(X) - 1); hi = np.clip(i + HALF, lo + 1, len(X))
    return (c[hi] - c[lo]) / (hi - lo)[:, None]

rows = []
for d in sorted(glob.glob(os.path.join(RAW, 'ODL_pack_*'))):
    sess = os.path.basename(d).split('ODL_pack_')[1]
    r, _ = load(glob.glob(os.path.join(d, '*.imu'))[0])
    a = r[r['k1'] == 4]; g = r[r['k1'] == 2]
    ta = a['ts'].astype(np.int64); A = (Rci @ np.c_[a['x'], a['y'], a['z']].astype(float).T).T
    tg = g['ts'].astype(np.int64); G = (Rci @ np.c_[g['x'], g['y'], g['z']].astype(float).T).T
    for p in sorted(glob.glob(os.path.join(d, '*_left_sei.csv'))):
        x = pd.read_csv(p); tc = x.exposure_start_us.values + shift_us + x.exposure_us.values / 2
        up = window_mean(ta, A, tc); up /= np.linalg.norm(up, axis=1, keepdims=True)
        w = window_mean(tg, G, tc)
        rows.append(pd.DataFrame(dict(session=sess, chunk=os.path.basename(p)[16:21], frame=np.arange(len(x)),
            pitch_below_deg=-np.degrees(np.arcsin(np.clip(up[:, 2], -1, 1))), roll_deg=np.degrees(np.arctan2(up[:, 0], -up[:, 1])),
            yaw_rate_dps=np.degrees(np.abs((w * up).sum(1))))))
F = pd.concat(rows, ignore_index=True)
F.to_csv(os.path.join(OUT, 'c1_per_frame_view.csv.gz'), index=False, float_format='%.2f')
bins = [-90, 30, 45, 60, 75, 91]; lab = ['<30', '30-45', '45-60', '60-75', '>75']
B = pd.cut(F.pitch_below_deg, bins, labels=lab).value_counts(normalize=True).reindex(lab)
pd.DataFrame(dict(pitch_band_deg=lab, share=B.values)).to_csv(os.path.join(OUT, 'c1_pitch_bands.csv'), index=False, float_format='%.4f')
print('frames', len(F), 'pitch median', round(F.pitch_below_deg.median(), 1)); print(B.round(3).to_string())
