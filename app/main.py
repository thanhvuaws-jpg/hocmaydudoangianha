import json
import os
import sys
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(GOC, 'src'))

from du_doan import BoDuDoan

TINH_TINH = os.path.join(GOC, 'app', 'static')
MH = os.path.join(GOC, 'models')


def doc_json(ten):
    with open(os.path.join(MH, ten), encoding='utf-8') as f:
        return json.load(f)


bo_du_doan = BoDuDoan()
DANH_MUC = doc_json('danh_muc.json')
THI_TRUONG = doc_json('thi_truong.json')
TONG_QUAN = doc_json('tong_quan_du_lieu.json')

app = FastAPI(title='Dự đoán giá nhà Việt Nam', version='1.0')
app.mount('/static', StaticFiles(directory=TINH_TINH), name='static')


class YeuCauDinhGia(BaseModel):
    loai_bds: Literal['Nhà ở', 'Căn hộ', 'Đất', 'Biệt thự/Liền kề', 'Shophouse']
    tinh: str
    quan_huyen: Optional[str] = None
    phuong_xa: Optional[str] = None
    duong: Optional[str] = None
    du_an: Optional[str] = None
    dien_tich_m2: float = Field(gt=9, le=10000)
    mat_tien_m: Optional[float] = Field(default=None, gt=0, le=100)
    chieu_dai_m: Optional[float] = Field(default=None, gt=0, le=300)
    duong_vao_m: Optional[float] = Field(default=None, gt=0, le=100)
    so_tang: Optional[float] = Field(default=None, ge=0, le=50)
    so_phong_ngu: Optional[float] = Field(default=None, ge=0, le=30)
    so_phong_tam: Optional[float] = Field(default=None, ge=0, le=30)
    huong_nha: Optional[str] = None
    phap_ly: Optional[str] = None
    noi_that: Optional[str] = None
    vi_tri: Optional[str] = None


@app.get('/')
def trang_chu():
    return FileResponse(os.path.join(TINH_TINH, 'index.html'))


@app.get('/api/danh-muc')
def danh_muc():
    return {'tinh': sorted(DANH_MUC['quan']), **DANH_MUC}


@app.get('/api/thi-truong')
def thi_truong(tinh: str, loai: str = 'Tất cả'):
    if tinh not in THI_TRUONG['tinh']:
        raise HTTPException(404, f'Chưa có dữ liệu thị trường cho {tinh}')
    quan = []
    for khoa, theo_loai in THI_TRUONG['quan'].items():
        t, q = khoa.split('|', 1)
        if t == tinh and loai in theo_loai:
            quan.append({'quan': q, **theo_loai[loai]})
    return {'tinh': tinh, 'loai': loai, 'tong': THI_TRUONG['tinh'][tinh], 'quan': sorted(quan, key=lambda x: -x['gia_m2'])}


@app.get('/api/tong-quan')
def tong_quan():
    tt = bo_du_doan.thong_tin
    return {'du_lieu': TONG_QUAN, 'mo_hinh': {k: tt[k] for k in ['mo_hinh', 'ket_qua_test', 'so_mau_train', 'so_mau_val', 'so_mau_test',
                                                                   'so_sanh', 'mat_can_bang', 'quan_trong'] if k in tt}}


@app.post('/api/dinh-gia')
def dinh_gia(yc: YeuCauDinhGia):
    if yc.tinh not in DANH_MUC['quan']:
        raise HTTPException(422, 'Tỉnh/thành không có trong dữ liệu huấn luyện')
    kq = bo_du_doan.dinh_gia(yc.model_dump())
    tham_chieu = None
    if yc.quan_huyen:
        theo_loai = THI_TRUONG['quan'].get(f'{yc.tinh}|{yc.quan_huyen}', {})
        tham_chieu = theo_loai.get(yc.loai_bds) or theo_loai.get('Tất cả')
        if tham_chieu:
            tham_chieu = {**tham_chieu, 'pham_vi': yc.quan_huyen, 'cung_loai': yc.loai_bds in theo_loai}
    if tham_chieu is None:
        theo_loai = THI_TRUONG['tinh'].get(yc.tinh, {})
        tham_chieu = theo_loai.get(yc.loai_bds) or theo_loai.get('Tất cả')
        if tham_chieu:
            tham_chieu = {**tham_chieu, 'pham_vi': yc.tinh, 'cung_loai': yc.loai_bds in theo_loai}
    return {**kq, 'tham_chieu': tham_chieu}


@app.get('/api/suc-khoe')
def suc_khoe():
    return {'trang_thai': 'ok', 'mo_hinh': bo_du_doan.thong_tin['mo_hinh']}
