"""C2: share of the image covered by the wearer's own body (blue work jacket), per sampled left frame.
Mask = jacket hue (H 92-107, S>120, V>40), keep connected components touching the bottom image edge."""
import cv2, numpy as np, pandas as pd, glob, os
F = pd.read_csv('out17/c1_sampled_frames.csv'); rows = []
for _, r in F.iterrows():
    p = glob.glob(f'raw/ODL_pack_{r.session}/frames/{r.file}')[0]
    im = cv2.imread(p); h, w = im.shape[:2]; hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (92, 120, 40), (107, 255, 255))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)); m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    keep = [i for i in range(1, n) if st[i, cv2.CC_STAT_TOP] + st[i, cv2.CC_STAT_HEIGHT] >= h - 3 and st[i, cv2.CC_STAT_AREA] > 2000]
    body = np.isin(lab, keep)
    rows.append(dict(**r.to_dict(), body_share=body.mean(), body_top_row=(np.where(body.any(1))[0].min() / h if body.any() else np.nan)))
    cv2.imwrite(f'out17/mask_{r.file[:-4]}.png', (body * 255).astype(np.uint8)[::4, ::4])
D = pd.DataFrame(rows); D.to_csv('out17/c2_self_occlusion.csv', index=False, float_format='%.4f')
D['pb'] = pd.cut(D.pitch_below_deg, [0, 30, 45, 60, 75, 90])
print(D.groupby('pb', observed=True).body_share.describe().round(3))
print('corr', D[['pitch_below_deg', 'body_share']].corr().iloc[0, 1].round(3))
