import numpy as np
import pandas as pd

MOC_GIA_TY = [0, 1, 2, 3, 5, 8, 15, 30, np.inf]
NHAN_GIA = ['< 1 tỷ', '1–2 tỷ', '2–3 tỷ', '3–5 tỷ', '5–8 tỷ', '8–15 tỷ', '15–30 tỷ', '> 30 tỷ']


def vung(tinh):
    return tinh.where(tinh.isin(['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng']), 'Tỉnh khác')


def phan_khuc_gia(gia_vnd):
    return pd.cut(gia_vnd / 1e9, MOC_GIA_TY, labels=NHAN_GIA, right=False)


def tang(df):
    return df['loai_bds'].astype(str) + ' | ' + vung(df['tinh']) + ' | ' + phan_khuc_gia(df['gia_vnd']).astype(str)


def trong_so_nghich_tan_suat(nhom, mu=0.5, thap=0.2, cao=5.0):
    tan_suat = nhom.map(nhom.value_counts(normalize=True))
    w = (1.0 / tan_suat) ** mu
    w = w / w.mean()
    return w.clip(thap, cao) / w.clip(thap, cao).mean()


def tang_mau_nhom_hiem(df, nhom, muc_toi_thieu, cot_so=(), nhieu=0.02, seed=42):
    rng = np.random.default_rng(seed)
    dem = nhom.value_counts()
    phan_them = []
    for ten, n in dem[dem < muc_toi_thieu].items():
        chi_so = nhom.index[nhom == ten]
        them = df.loc[rng.choice(chi_so, size=muc_toi_thieu - n, replace=True)].copy()
        for c in cot_so:
            if c in them:
                them[c] = them[c] * (1 + rng.normal(0, nhieu, len(them)))
        phan_them.append(them)
    if not phan_them:
        return df.copy()
    return pd.concat([df] + phan_them, ignore_index=True)
