"""C1: where the head-mounted camera points during real work.
Per 1 s window from accelerometer (gravity direction in camera frame) + gyro:
  pitch_below_horizon_deg  = angle of optical axis (+z) below horizontal
  roll_deg                 = rotation about optical axis (0 = image rows level)
  yaw_rate_dps             = rotation about the vertical (head turning), |omega . up|
  step band ratio          = share of accel-magnitude spectrum in 1.4-2.6 Hz (walking cadence)
Also per sampled frame (for validation against images).
"""
import sys, os, glob
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, '/home/claude/fn/common'); from read_zximu import load
import yaml
# usage: python c1_view_direction.py [packs_dir] [out_dir]; calibration yaml from env ODL_CALIB (factory calibration, not redistributed)
Y = yaml.safe_load(open(os.environ.get('ODL_CALIB', '/home/claude/fn/common/data/factory_calibration.yaml')))
Rci = np.array(Y['cam0']['T_cam_imu'])[:3, :3]; shift_us = Y['cam0']['timeshift_cam_imu'] * 1e6
RAW = sys.argv[1] if len(sys.argv) > 1 else 'raw'; OUT = sys.argv[2] if len(sys.argv) > 2 else 'out17'
W = 500  # samples per 1 s

def unit(v): return v / np.linalg.norm(v, axis=-1, keepdims=True)
def angles(up):
    pitch = -np.degrees(np.arcsin(np.clip(up[..., 2], -1, 1)))
    roll = np.degrees(np.arctan2(up[..., 0], -up[..., 1]))
    return pitch, roll

sec_rows, frame_rows = [], []
for d in sorted(glob.glob(f'{RAW}/ODL_pack_*')):
    sess = d.split('ODL_pack_')[1]
    r, _ = load(glob.glob(f'{d}/*.imu')[0])
    a = r[r['k1'] == 4]; g = r[r['k1'] == 2]
    ta = a['ts'].astype(np.int64); A = (Rci @ np.c_[a['x'], a['y'], a['z']].astype(float).T).T
    tg = g['ts'].astype(np.int64); G = (Rci @ np.c_[g['x'], g['y'], g['z']].astype(float).T).T
    n = min(len(A), len(G)) // W * W
    Aw = A[:n].reshape(-1, W, 3); Gw = G[:n].reshape(-1, W, 3)
    up = unit(Aw.mean(1)); pitch, roll = angles(up)
    yaw = np.degrees(np.abs((Gw * up[:, None, :]).sum(2)).mean(1))
    rate = np.degrees(np.linalg.norm(Gw, axis=2).mean(1))
    mag = np.linalg.norm(Aw, axis=2); mag = mag - mag.mean(1, keepdims=True)
    # 2 s windows for cadence (pair consecutive seconds)
    m2 = np.concatenate([mag[:-1], mag[1:]], 1)
    X = np.abs(np.fft.rfft(m2 * np.hanning(2 * W), axis=1)) ** 2; fr = np.fft.rfftfreq(2 * W, 1 / 500)
    tot = X[:, (fr > 0.5) & (fr < 8)].sum(1) + 1e-12
    band = X[:, (fr >= 1.4) & (fr <= 2.6)].sum(1) / tot
    pk = fr[(fr >= 1.4) & (fr <= 2.6)][np.argmax(X[:, (fr >= 1.4) & (fr <= 2.6)], 1)]
    band = np.r_[band, band[-1]]; pk = np.r_[pk, pk[-1]]
    accsd = np.linalg.norm(Aw, axis=2).std(1)
    t_mid = ta[:n].reshape(-1, W)[:, W // 2]
    sec_rows.append(pd.DataFrame(dict(session=sess, t_us=t_mid, sec=np.arange(len(up)), pitch_below_deg=pitch, roll_deg=roll,
        yaw_rate_dps=yaw, ang_speed_dps=rate, acc_sd=accsd, step_band=band, step_hz=pk)))
    # per sampled frame: 1 s centred mean of accel
    cumA = np.vstack([np.zeros(3), np.cumsum(A, 0)])
    for fj in sorted(glob.glob(f'{d}/frames/*_left_f*.jpg')):
        b = os.path.basename(fj); chunk = b[16:21]; fi = int(b.split('_f')[1][:6])
        sei = pd.read_csv(f'{d}/{sess}_{chunk}_left_sei.csv')
        tc = sei.exposure_start_us.values[fi] + shift_us + sei.exposure_us.values[fi] / 2
        i = np.searchsorted(ta, tc); lo, hi = max(i - W // 2, 0), min(i + W // 2, len(A))
        u = unit((cumA[hi] - cumA[lo]) / (hi - lo)); p, ro = angles(u)
        frame_rows.append(dict(session=sess, chunk=chunk, frame=fi, file=b, pitch_below_deg=p, roll_deg=ro))
S = pd.concat(sec_rows, ignore_index=True); S.to_csv(f'{OUT}/c1_per_second.csv.gz', index=False, float_format='%.4g')
Fr = pd.DataFrame(frame_rows); Fr.to_csv(f'{OUT}/c1_sampled_frames.csv', index=False, float_format='%.2f')
q = lambda c: S[c].quantile([.05, .25, .5, .75, .95]).round(2).tolist()
for c in ['pitch_below_deg', 'roll_deg', 'yaw_rate_dps', 'ang_speed_dps', 'acc_sd', 'step_band']: print(c, q(c))
print('seconds', len(S), 'sampled frames', len(Fr))
print(S.groupby('session').agg(sec=('sec', 'size'), pitch_med=('pitch_below_deg', 'median'), p25=('pitch_below_deg', lambda v: v.quantile(.25)),
      p75=('pitch_below_deg', lambda v: v.quantile(.75)), roll_med=('roll_deg', 'median'), yaw_med=('yaw_rate_dps', 'median')).round(1).to_string())
