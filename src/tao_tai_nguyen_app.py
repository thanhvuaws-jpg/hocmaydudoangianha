import json
import os

import numpy as np
import pandas as pd

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DL = os.path.join(GOC, 'data')
MH = os.path.join(GOC, 'models')
BC = os.path.join(GOC, 'reports')
TEN_NGUON = {
    1: 'yashdev01/vietnam-real-estates', 2: 'qmanhbeo/vietnamese-real-estate-listings',
    3: 'ladcva/vietnam-housing-dataset-hanoi', 4: 'cresht2606 – batdongsan.vn',
    5: 'nguyentiennhan/vietnam-housing-dataset-2024', 6: 'huytrngquc/hanoi-housing-price-2024',
}


def danh_muc(train, toi_thieu=5):
    q = train.groupby(['tinh', 'quan_huyen']).size()
    q = q[q >= toi_thieu].reset_index()
    p = train.groupby(['tinh', 'quan_huyen', 'phuong_xa']).size()
    p = p[p >= toi_thieu].reset_index()
    d = train.groupby(['tinh', 'du_an']).size()
    d = d[d >= toi_thieu].reset_index()
    return {
        'quan': {t: sorted(g['quan_huyen'].tolist()) for t, g in q.groupby('tinh')},
        'phuong': {f'{t}|{qh}': sorted(g['phuong_xa'].tolist()) for (t, qh), g in p.groupby(['tinh', 'quan_huyen'])},
        'du_an': {t: sorted(g['du_an'].tolist()) for t, g in d.groupby('tinh')},
    }


def thi_truong(df, toi_thieu=20):
    def tom(g):
        return {'n': int(len(g)), 'gia_m2': float(g['gia_m2'].median()), 'gia': float(g['gia_vnd'].median()),
                'dien_tich': float(g['dien_tich_m2'].median())}
    out = {'tinh': {}, 'quan': {}}
    for (t, loai), g in df.groupby(['tinh', 'loai_bds']):
        if len(g) >= toi_thieu:
            out['tinh'].setdefault(t, {})[loai] = tom(g)
    for t, g in df.groupby('tinh'):
        out['tinh'].setdefault(t, {})['Tất cả'] = tom(g)
    for (t, q, loai), g in df.groupby(['tinh', 'quan_huyen', 'loai_bds']):
        if len(g) >= toi_thieu:
            out['quan'].setdefault(f'{t}|{q}', {})[loai] = tom(g)
    for (t, q), g in df.groupby(['tinh', 'quan_huyen']):
        if len(g) >= toi_thieu:
            out['quan'].setdefault(f'{t}|{q}', {})['Tất cả'] = tom(g)
    return out


def tong_quan(sach):
    nk = pd.read_csv(os.path.join(BC, 'nhat_ky_lam_sach.csv'))
    sua = pd.read_csv(os.path.join(BC, 'thong_ke_sua_loi.csv'), index_col=0)
    cl = pd.read_csv(os.path.join(BC, 'chat_luong_truoc_sau.csv'), index_col=0)
    goc = pd.read_parquet(os.path.join(DL, 'interim', 'gop_6_nguon.parquet'), columns=['nguon'])['nguon'].value_counts()
    con = sach['nguon'].value_counts()
    tach = {t: len(pd.read_parquet(os.path.join(DL, 'processed', f'{t}.parquet'), columns=['nguon'])) for t in ['train', 'val', 'test']}
    return {
        'nguon': [{'ma': int(k), 'ten': TEN_NGUON[int(k)], 'tho': int(goc.get(k, 0)), 'sach': int(con.get(k, 0))} for k in sorted(goc.index)],
        'nhat_ky': [{'buoc': r['Bước'], 'sau': int(r['Sau']), 'bo': int(r['Bỏ đi'])} for _, r in nk.iterrows() if r['Bước'] != 'TỔNG'],
        'tong_tho': int(goc.sum()), 'tong_sach': int(len(sach)),
        'sua_loi': [{'viec': k, 'so': int(v)} for k, v in sua.iloc[:, 0].items()],
        'chat_luong': [{'chi_so': k, 'truoc': float(r.iloc[0]), 'sau': float(r.iloc[1])} for k, r in cl.iterrows()],
        'loai_bds': {k: int(v) for k, v in sach['loai_bds'].value_counts().items()},
        'vung': {k: int(v) for k, v in sach['tinh'].where(sach['tinh'].isin(['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng']), 'Tỉnh khác').value_counts().items()},
        'chia_tap': tach, 'so_tinh': int(sach['tinh'].nunique()), 'so_quan': int(sach['quan_huyen'].nunique()),
    }


if __name__ == '__main__':
    train = pd.read_parquet(os.path.join(DL, 'processed', 'train.parquet'))
    sach = pd.read_parquet(os.path.join(DL, 'processed', 'du_lieu_sach.parquet'),
                           columns=['nguon', 'tinh', 'quan_huyen', 'loai_bds', 'gia_vnd', 'gia_m2', 'dien_tich_m2'])
    for ten, noi_dung in [('danh_muc.json', danh_muc(train)), ('thi_truong.json', thi_truong(sach)), ('tong_quan_du_lieu.json', tong_quan(sach))]:
        with open(os.path.join(MH, ten), 'w', encoding='utf-8') as f:
            json.dump(noi_dung, f, ensure_ascii=False)
        print('Da tao models/' + ten, round(os.path.getsize(os.path.join(MH, ten)) / 1e3), 'KB')
