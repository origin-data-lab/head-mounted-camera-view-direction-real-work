"""Summary tables for Field Note #17."""
import numpy as np, pandas as pd
S = pd.read_csv('out17/c1_per_second.csv.gz', dtype={'session': str})
D = pd.read_csv('out17/c2_self_occlusion.csv', dtype={'session': str})
L = pd.read_csv('out17/c3_hand_labels.csv', dtype={'session': str})
def sess_row(g, name):
    p = g.pitch_below_deg; ok = p < 70
    return dict(session=name, minutes=len(g) / 60, pitch_median=p.median(), pitch_q1=p.quantile(.25), pitch_q3=p.quantile(.75),
                share_lt30=(p < 30).mean(), share_45_75=((p >= 45) & (p < 75)).mean(), share_gt75=(p >= 75).mean(),
                roll_median=g[ok].roll_deg.median(), share_absroll_gt10=(g[ok].roll_deg.abs() > 10).mean(), yaw_rate_median=g.yaw_rate_dps.median())
T = pd.DataFrame([sess_row(g, s) for s, g in S.groupby('session')] + [sess_row(S, 'ALL')])
T.to_csv('out17/c4_by_session.csv', index=False, float_format='%.4f'); print(T.round(2).to_string())
edges = [-90, 30, 45, 60, 75, 91]; lab = ['<30', '30-45', '45-60', '60-75', '>75']
D['band'] = pd.cut(D.pitch_below_deg, edges, labels=lab, right=False); L['band'] = pd.cut(L.pitch_below_deg, edges, labels=lab, right=False)
B = D.groupby('band', observed=False).agg(frames=('body_share', 'size'), body_median=('body_share', 'median'), body_q1=('body_share', lambda v: v.quantile(.25)), body_q3=('body_share', lambda v: v.quantile(.75))).reset_index()
B['time_share'] = [((S.pitch_below_deg >= a) & (S.pitch_below_deg < b)).mean() for a, b in zip(edges[:-1], edges[1:])]
H = L.groupby('band', observed=False).agg(label_frames=('lid', 'size'), hands_visible=('hands_visible', 'mean'), hand_y_median=('hand_y_frac', 'median')).reset_index()
B = B.merge(H, on='band'); B.to_csv('out17/c4_by_pitch_band.csv', index=False, float_format='%.4f'); print(B.round(3).to_string())
n, k, z = len(L), int(L.hands_visible.sum()), 1.96; p = k / n
c = (p + z * z / (2 * n)) / (1 + z * z / n); h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
desk = L[L.desk_phone == 1]
summ = dict(seconds=len(S), pitch_median=S.pitch_below_deg.median(), share_45_75=((S.pitch_below_deg >= 45) & (S.pitch_below_deg < 75)).mean(), share_lt30=(S.pitch_below_deg < 30).mean(),
            bench_phase_median=S[pd.to_datetime(S.session.str[:8] + S.session.str[9:], format='%Y%m%d%H%M%S') >= pd.Timestamp('2026-11-01 10:20')].pitch_below_deg.median(),
            first_session_median=S[S.session == '20261101_094808'].pitch_below_deg.median(),
            hands_visible=k, label_frames=n, hands_ci_lo=c - h, hands_ci_hi=c + h, hand_y_median=L.hand_y_frac.median(), hand_y_q1=L.hand_y_frac.quantile(.25), hand_y_q3=L.hand_y_frac.quantile(.75),
            hand_deg_below_axis=np.degrees((L.hand_y_frac.median() - .5) * 1200 / 482.3), hand_px_below_centre=(L.hand_y_frac.median() - .5) * 1200,
            body_median_all=D.body_share.median(), body_frames=len(D), desk_pitch_min=desk.pitch_below_deg.min(), desk_pitch_max=desk.pitch_below_deg.max(), desk_n=len(desk), desk_sessions=desk.session.nunique(),
            roll_median=S[S.pitch_below_deg < 70].roll_deg.median(), absroll_gt10=(S[S.pitch_below_deg < 70].roll_deg.abs() > 10).mean(), absroll_gt20=(S[S.pitch_below_deg < 70].roll_deg.abs() > 20).mean(),
            yaw_median=S.yaw_rate_dps.median(), yaw_p90=S.yaw_rate_dps.quantile(.9))
pd.Series(summ).to_csv('out17/c4_summary.csv', header=['value']); print(pd.Series(summ).round(3).to_string())
