import numpy as np
import pandas as pd

THU_TU_PHAN_KHUC = ['< 1 tỷ', '1–2 tỷ', '2–3 tỷ', '3–5 tỷ', '5–8 tỷ', '8–15 tỷ', '15–30 tỷ', '> 30 tỷ']


def chi_so(y, p):
    y = np.asarray(y, dtype=np.float64)
    p = np.asarray(p, dtype=np.float64)
    sai_tl = np.abs(np.exp(p - y) - 1)
    gia, du = np.exp(y), np.exp(p)
    return {'RMSE log': float(np.sqrt(np.mean((p - y) ** 2))),
            'R² log': float(1 - np.mean((p - y) ** 2) / np.var(y)),
            'MAE (tỷ)': float(np.mean(np.abs(du - gia)) / 1e9),
            'MAPE (%)': float(sai_tl.mean() * 100),
            'Trung vị APE (%)': float(np.median(sai_tl) * 100),
            'Lệch ≤10% (%)': float((sai_tl <= 0.1).mean() * 100),
            'Lệch ≤20% (%)': float((sai_tl <= 0.2).mean() * 100)}


def theo_nhom(y, p, nhom):
    d = pd.DataFrame({'nhom': np.asarray(nhom), 'y': np.asarray(y, dtype=np.float64), 'p': np.asarray(p, dtype=np.float64)})
    d['ape'] = np.abs(np.exp(d['p'] - d['y']) - 1) * 100
    d['se'] = (d['p'] - d['y']) ** 2
    g = d.groupby('nhom').agg(so_mau=('y', 'size'), MAPE=('ape', 'mean'), trung_vi_APE=('ape', 'median'), mse=('se', 'mean'))
    g['RMSE log'] = np.sqrt(g.pop('mse'))
    return g
