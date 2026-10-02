import json
import os
from datetime import date

import joblib
import numpy as np
import pandas as pd

from xu_ly_chuoi import chuan_unicode

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_MH = os.path.join(GOC, 'models')


def _tai_mo_hinh(tep):
    duong_dan = os.path.join(THU_MUC_MH, tep)
    if tep.endswith('.json'):
        import xgboost as xgb
        mh = xgb.Booster()
        mh.load_model(duong_dan)
        so_cay = int(mh.attr('best_iteration')) + 1 if mh.attr('best_iteration') is not None else 0
        return lambda X: mh.predict(xgb.DMatrix(X), iteration_range=(0, so_cay))
    if tep.endswith('.txt'):
        import lightgbm as lgb
        return lgb.Booster(model_file=duong_dan).predict
    if tep.endswith('.cbm'):
        from catboost import CatBoostRegressor
        mh = CatBoostRegressor()
        mh.load_model(duong_dan)
        return mh.predict
    raise ValueError(f'Không nhận ra định dạng mô hình: {tep}')


class BoDuDoan:
    def __init__(self):
        with open(os.path.join(THU_MUC_MH, 'thong_tin_mo_hinh.json'), encoding='utf-8') as f:
            self.thong_tin = json.load(f)
        self.bo = joblib.load(os.path.join(THU_MUC_MH, 'bo_tien_xu_ly.joblib'))
        self.ham = {tep: _tai_mo_hinh(tep) for tep in self.thong_tin['tep']}
        self.trong_so = self.thong_tin['trong_so']

    def du_doan_log(self, khung):
        X = self.bo.transform(khung)[self.thong_tin['dac_trung']].values
        return sum(w * np.asarray(self.ham[tep](X), dtype=np.float64) for tep, w in self.trong_so.items())

    def dinh_gia(self, thong_so):
        la_dat = thong_so['loai_bds'] == 'Đất'
        dong = {
            'tinh': thong_so['tinh'], 'quan_huyen': thong_so.get('quan_huyen'), 'phuong_xa': thong_so.get('phuong_xa'),
            'duong': chuan_unicode((thong_so.get('duong') or '').strip().title()) or None, 'du_an': thong_so.get('du_an'),
            'loai_bds': thong_so['loai_bds'], 'dien_tich_m2': float(thong_so['dien_tich_m2']),
            'mat_tien_m': thong_so.get('mat_tien_m'), 'chieu_dai_m': thong_so.get('chieu_dai_m'),
            'duong_vao_m': thong_so.get('duong_vao_m'),
            'so_tang': 0.0 if la_dat else thong_so.get('so_tang'),
            'so_phong_ngu': 0.0 if la_dat else thong_so.get('so_phong_ngu'),
            'so_phong_tam': 0.0 if la_dat else thong_so.get('so_phong_tam'),
            'huong_nha': thong_so.get('huong_nha'), 'phap_ly': thong_so.get('phap_ly'), 'noi_that': thong_so.get('noi_that'),
            'vi_tri': thong_so.get('vi_tri'), 'nguon': 1, 'dia_gioi_moi': False, 'loai_doan': False, 'ngay_uoc_luong': False,
            'ngay_dang': pd.Timestamp(date.today()),
        }
        khung = pd.DataFrame([{k: np.nan if v is None else v for k, v in dong.items()}])
        for c in ['mat_tien_m', 'chieu_dai_m', 'duong_vao_m', 'so_tang', 'so_phong_ngu', 'so_phong_tam']:
            khung[c] = pd.to_numeric(khung[c], errors='coerce')
        gia = float(np.exp(self.du_doan_log(khung)[0]))
        k = self.thong_tin['khoang_sai_so'].get(thong_so['loai_bds'], self.thong_tin['khoang_sai_so']['Tất cả'])
        return {'gia': gia, 'don_gia_m2': gia / dong['dien_tich_m2'], 'thap': gia * k[0], 'cao': gia * k[1]}
