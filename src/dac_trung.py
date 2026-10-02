import numpy as np
import pandas as pd

COT_SO = ['mat_tien_m', 'chieu_dai_m', 'duong_vao_m', 'so_tang', 'so_phong_ngu', 'so_phong_tam']
COT_ONE_HOT = {
    'loai_bds': ['Nhà ở', 'Đất', 'Căn hộ', 'Biệt thự/Liền kề', 'Shophouse'],
    'vung': ['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Tỉnh khác'],
    'huong_nha': ['Đông', 'Tây', 'Nam', 'Bắc', 'Đông Nam', 'Đông Bắc', 'Tây Nam', 'Tây Bắc'],
    'phap_ly': ['Có sổ', 'Hợp đồng mua bán', 'Đang chờ sổ', 'Khác'],
    'noi_that': ['Đầy đủ', 'Cơ bản', 'Không / thô'],
    'vi_tri': ['Mặt phố', 'Ngõ/Hẻm'],
    'nguon': [1, 2, 3, 4, 5, 6],
}
BO_MOC = ('loai_bds', 'vung', 'nguon')
CAP_TE = {
    'te_tinh': (['tinh'], None),
    'te_quan': (['tinh', 'quan_huyen'], 'te_tinh'),
    'te_phuong': (['tinh', 'quan_huyen', 'phuong_xa'], 'te_quan'),
    'te_duong': (['tinh', 'quan_huyen', 'duong'], 'te_quan'),
    'te_du_an': (['tinh', 'du_an'], 'te_quan'),
}
MOC_THOI_GIAN = pd.Timestamp('2019-01-01')


def vung(tinh):
    return tinh.where(tinh.isin(['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng']), 'Tỉnh khác')


def dac_trung_co_ban(df):
    out = pd.DataFrame(index=df.index)
    out['log_dien_tich'] = np.log(df['dien_tich_m2'])
    for c in COT_SO:
        out[c] = df[c].astype(float)
    out['thang_tu_2019'] = (df['ngay_dang'] - MOC_THOI_GIAN).dt.days / 30.44
    for c in COT_SO:
        out['thieu_' + c] = df[c].isna().astype(float)
    out['thieu_quan'] = df['quan_huyen'].isna().astype(float)
    out['co_du_an'] = df['du_an'].notna().astype(float)
    out['dia_gioi_moi'] = df['dia_gioi_moi'].astype(float)
    out['loai_doan'] = df.get('loai_doan', pd.Series(False, index=df.index)).astype(float)
    out['ngay_uoc_luong'] = df.get('ngay_uoc_luong', pd.Series(False, index=df.index)).astype(float)
    return out


class BoTienXuLy:
    def __init__(self, m_lam_tron=20, so_fold=5, seed=42):
        self.m = m_lam_tron
        self.so_fold = so_fold
        self.seed = seed
        self.cot_chon = None

    def _khung(self, df):
        k = df[['tinh', 'quan_huyen', 'phuong_xa', 'duong', 'du_an', 'loai_bds']].copy()
        for c in ['quan_huyen', 'phuong_xa', 'duong', 'du_an']:
            k[c] = k[c].fillna('?')
        return k

    def _hoc_te(self, k, y):
        bang = {}
        tb_chung = float(y.mean())
        for ten, (khoa, cha) in CAP_TE.items():
            g = pd.DataFrame({'y': y.values}, index=k.index).join(k[khoa]).groupby(khoa)['y'].agg(['sum', 'count'])
            bang[ten] = (g, khoa, cha)
        return {'chung': tb_chung, 'bang': bang}

    def _ap_te(self, k, te):
        out = pd.DataFrame(index=k.index)
        for ten, (g, khoa, cha) in te['bang'].items():
            nen = out[cha] if cha else pd.Series(te['chung'], index=k.index)
            g2 = g if len(khoa) == 1 else g[g.index.get_level_values(-1) != '?']
            khop = k[khoa].join(g2, on=khoa)
            s, n = khop['sum'].fillna(0).values, khop['count'].fillna(0).values
            out[ten] = (s + self.m * nen.values) / (n + self.m)
        return out

    def _dem(self, k):
        return {'quan': k.groupby(['tinh', 'quan_huyen']).size(), 'du_an': k.groupby(['tinh', 'du_an']).size()}

    def _ap_dem(self, k):
        out = pd.DataFrame(index=k.index)
        q = k[['tinh', 'quan_huyen']].join(self.dem['quan'].rename('n'), on=['tinh', 'quan_huyen'])['n'].fillna(0)
        d = k[['tinh', 'du_an']].join(self.dem['du_an'].rename('n'), on=['tinh', 'du_an'])['n'].fillna(0)
        out['log_dem_quan'] = np.log1p(q.where(k['quan_huyen'] != '?', 0))
        out['log_dem_du_an'] = np.log1p(d.where(k['du_an'] != '?', 0))
        return out

    def _one_hot(self, df):
        out = pd.DataFrame(index=df.index)
        cot = df.assign(vung=vung(df['tinh']))
        for c, gia_tri in COT_ONE_HOT.items():
            for v in (gia_tri[1:] if c in BO_MOC else gia_tri):
                out[f'{c}={v}'] = (cot[c] == v).astype(float)
        return out

    def _dien_thieu(self, X, df):
        X = X.copy()
        khoa = list(zip(df['loai_bds'], df['tinh']))
        for c in COT_SO:
            nhom = pd.Series(khoa, index=df.index).map(self.trung_vi_nhom[c])
            X[c] = X[c].fillna(nhom).fillna(self.trung_vi_chung[c])
        X['thang_tu_2019'] = X['thang_tu_2019'].fillna(self.trung_vi_chung['thang_tu_2019'])
        return X

    def _ghep(self, df, te):
        k = self._khung(df)
        X = pd.concat([dac_trung_co_ban(df), te, self._ap_dem(k), self._one_hot(df)], axis=1)
        return self._dien_thieu(X, df)

    def fit_transform(self, df, y_log_gia_m2):
        k = self._khung(df)
        self.te = self._hoc_te(k, y_log_gia_m2)
        self.dem = self._dem(k)
        co_ban = dac_trung_co_ban(df)
        khoa = pd.Series(list(zip(df['loai_bds'], df['tinh'])), index=df.index)
        self.trung_vi_nhom = {c: co_ban[c].groupby(khoa).median().dropna().to_dict() for c in COT_SO}
        self.trung_vi_chung = co_ban[COT_SO + ['thang_tu_2019']].median().to_dict()
        rng = np.random.default_rng(self.seed)
        fold = rng.integers(0, self.so_fold, len(df))
        te_oof = pd.DataFrame(index=df.index, columns=list(CAP_TE), dtype=float)
        for f in range(self.so_fold):
            hoc, ap = fold != f, fold == f
            te_f = self._hoc_te(k[hoc], y_log_gia_m2[hoc])
            te_oof.loc[ap] = self._ap_te(k[ap], te_f).values
        X = self._ghep(df, te_oof)
        self.cot = list(X.columns)
        self.tb = X.mean()
        self.dl = X.std().replace(0, 1)
        return self._chon(self._chuan_hoa(X))

    def transform(self, df):
        X = self._ghep(df, self._ap_te(self._khung(df), self.te))[self.cot]
        return self._chon(self._chuan_hoa(X))

    def _chuan_hoa(self, X):
        return ((X - self.tb) / self.dl).astype(np.float32)

    def _chon(self, X):
        return X if self.cot_chon is None else X[self.cot_chon]
