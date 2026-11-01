"""C3: visual hand labels on 96 sampled left frames (16 per session, evenly spaced; AI visual labelling, not human re-checked).
hand_y: approximate vertical centre of the visible hand(s) on a 300-px-tall thumbnail (0 = top); missing = no hand visible.
desk_phone: frames where the worker checks a phone at the same desk (used as a repeated-posture check of rig placement)."""
import numpy as np, pandas as pd
HAND_Y = {0:290,3:270,4:260,5:265,6:260,7:280,8:230,9:210,10:230,12:205,13:175,14:220,16:185,17:210,18:250,19:170,20:198,21:215,22:228,23:280,24:225,25:180,26:178,27:180,28:210,29:190,30:192,
          32:240,33:265,35:203,36:205,37:190,38:175,39:155,40:190,42:190,43:195,44:210,45:138,46:178,47:210,48:215,49:178,50:235,51:192,53:232,54:240,55:190,56:250,57:195,58:190,59:200,
          60:180,61:210,62:190,63:190,64:215,65:125,66:190,67:240,68:185,69:245,70:115,72:178,73:150,74:220,75:145,76:182,77:185,78:210,79:195,80:215,81:208,82:190,83:155,84:168,85:190,
          86:220,88:190,89:192,92:210,93:180,95:190}
DESK = [32, 48, 64, 79, 80, 95]
D = pd.read_csv('out17/c2_self_occlusion.csv')
S = pd.concat([g.iloc[np.linspace(0, len(g) - 1, 16).astype(int)] for _, g in D.groupby('session')]).reset_index(drop=True)
S['lid'] = range(len(S))
S['hand_y_frac'] = S.lid.map(lambda i: HAND_Y.get(i, np.nan) / 300)
S['hands_visible'] = S.lid.isin(HAND_Y).astype(int); S['desk_phone'] = S.lid.isin(DESK).astype(int)
S.to_csv('out17/c3_hand_labels.csv', index=False, float_format='%.3f'); print(S.hands_visible.sum(), len(S))
