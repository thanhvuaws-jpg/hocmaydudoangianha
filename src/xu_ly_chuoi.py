import re
import unicodedata

import numpy as np
import pandas as pd

TINH_MOI = {
    'Tuyên Quang': ['Tuyên Quang', 'Hà Giang'],
    'Lào Cai': ['Lào Cai', 'Yên Bái'],
    'Thái Nguyên': ['Thái Nguyên', 'Bắc Kạn'],
    'Phú Thọ': ['Phú Thọ', 'Vĩnh Phúc', 'Hòa Bình'],
    'Bắc Ninh': ['Bắc Ninh', 'Bắc Giang'],
    'Hưng Yên': ['Hưng Yên', 'Thái Bình'],
    'Hải Phòng': ['Hải Phòng', 'Hải Dương'],
    'Ninh Bình': ['Ninh Bình', 'Hà Nam', 'Nam Định'],
    'Quảng Trị': ['Quảng Trị', 'Quảng Bình'],
    'Đà Nẵng': ['Đà Nẵng', 'Quảng Nam'],
    'Quảng Ngãi': ['Quảng Ngãi', 'Kon Tum'],
    'Gia Lai': ['Gia Lai', 'Bình Định'],
    'Khánh Hòa': ['Khánh Hòa', 'Ninh Thuận'],
    'Lâm Đồng': ['Lâm Đồng', 'Đắk Nông', 'Bình Thuận'],
    'Đắk Lắk': ['Đắk Lắk', 'Phú Yên'],
    'Hồ Chí Minh': ['Hồ Chí Minh', 'Bình Dương', 'Bà Rịa - Vũng Tàu'],
    'Đồng Nai': ['Đồng Nai', 'Bình Phước'],
    'Tây Ninh': ['Tây Ninh', 'Long An'],
    'Cần Thơ': ['Cần Thơ', 'Sóc Trăng', 'Hậu Giang'],
    'Vĩnh Long': ['Vĩnh Long', 'Bến Tre', 'Trà Vinh'],
    'Đồng Tháp': ['Đồng Tháp', 'Tiền Giang'],
    'Cà Mau': ['Cà Mau', 'Bạc Liêu'],
    'An Giang': ['An Giang', 'Kiên Giang'],
    'Hà Nội': ['Hà Nội'], 'Huế': ['Huế'], 'Lai Châu': ['Lai Châu'], 'Điện Biên': ['Điện Biên'],
    'Sơn La': ['Sơn La'], 'Lạng Sơn': ['Lạng Sơn'], 'Quảng Ninh': ['Quảng Ninh'], 'Thanh Hóa': ['Thanh Hóa'],
    'Nghệ An': ['Nghệ An'], 'Hà Tĩnh': ['Hà Tĩnh'], 'Cao Bằng': ['Cao Bằng'],
}
CU_SANG_MOI = {cu: moi for moi, ds in TINH_MOI.items() for cu in ds}


def bo_dau(s):
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.replace('đ', 'd').replace('Đ', 'D')


def khoa(s):
    return re.sub(r'[^a-z0-9]', '', bo_dau(s).lower())


DAU_MOI_SANG_CU = {'oà': 'òa', 'oá': 'óa', 'oả': 'ỏa', 'oã': 'õa', 'oạ': 'ọa',
                   'oè': 'òe', 'oé': 'óe', 'oẻ': 'ỏe', 'oẽ': 'õe', 'oẹ': 'ọe',
                   'uỳ': 'ùy', 'uý': 'úy', 'uỷ': 'ủy', 'uỹ': 'ũy', 'uỵ': 'ụy'}
DAU_MOI_SANG_CU.update({k[0].upper() + k[1]: v[0].upper() + v[1] for k, v in list(DAU_MOI_SANG_CU.items())})
MAU_DAU_MOI = re.compile(r'(?<![qQ])(' + '|'.join(DAU_MOI_SANG_CU) + r')(?!\w)')


def chuan_unicode(s):
    if pd.isna(s):
        return np.nan
    s = unicodedata.normalize('NFC', str(s))
    return MAU_DAU_MOI.sub(lambda m: DAU_MOI_SANG_CU[m.group(1)], s)


KHOA_TINH = {khoa(t): t for t in CU_SANG_MOI}
KHOA_TINH.update({'thuathienhue': 'Huế', 'tphochiminh': 'Hồ Chí Minh', 'tphcm': 'Hồ Chí Minh', 'hcm': 'Hồ Chí Minh',
                  'thanhphohochiminh': 'Hồ Chí Minh', 'hn': 'Hà Nội', 'bariavungtau': 'Bà Rịa - Vũng Tàu'})


def chuan_tinh(s):
    if pd.isna(s):
        return np.nan
    s = re.sub(r'\(\s*Mới\s*\)', '', str(s))
    return KHOA_TINH.get(khoa(s), np.nan)


TIEN_TO_QUAN = r'^(quận|huyện|thị xã|thành phố|tp\.?|thị trấn)\s+'
TIEN_TO_PHUONG = r'^(phường|xã|thị trấn)\s+'


def chuan_quan(s, tinh=None):
    if pd.isna(s):
        return np.nan
    s = re.sub(r'\s+', ' ', str(s)).strip().strip('.,')
    goc = re.sub(TIEN_TO_QUAN, '', s, flags=re.I).strip()
    if re.fullmatch(r'\d+', goc):
        goc = f'Quận {int(goc)}'
    if tinh == 'Hồ Chí Minh' and goc in ('Quận 2', 'Quận 9'):
        goc = 'Thủ Đức'
    return goc.title() if goc.islower() else goc


def chuan_phuong(s):
    if pd.isna(s):
        return np.nan
    s = re.sub(r'\s+', ' ', str(s)).strip().strip('.,')
    goc = re.sub(TIEN_TO_PHUONG, '', s, flags=re.I).strip()
    if re.fullmatch(r'\d+', goc):
        goc = f'Phường {int(goc)}'
    return goc


def so(s):
    if pd.isna(s):
        return np.nan
    if isinstance(s, (int, float, np.integer, np.floating)):
        return float(s)
    m = re.search(r'\d[\d.,]*', str(s))
    if not m:
        return np.nan
    t = m.group(0).rstrip('.,')
    if '.' in t and ',' in t:
        t = t.replace('.', '').replace(',', '.')
    elif ',' in t:
        t = t.replace(',', '.') if t.count(',') == 1 else t.replace(',', '')
    elif t.count('.') > 1:
        t = t.replace('.', '')
    try:
        return float(t)
    except ValueError:
        return np.nan


def so_hoac_rong(s):
    v = so(s)
    return np.nan if v == 0 else v


RE_GIA = re.compile(
    r'(\d+(?:[.,]\d+)?)\s*(tỷ|tỉ|ty)\s*(\d{1,3})?(?:\s*(triệu|tr))?(?!\s*/)'
    r'|(\d+(?:[.,]\d+)?)\s*(triệu|tr)\b(?!\s*/)', re.I)


def gia_tu_chuoi(s):
    if pd.isna(s):
        return np.nan
    t = str(s).lower()
    if 'thỏa thuận' in t or 'thoả thuận' in t or 'liên hệ' in t and not re.search(r'\d', t):
        return np.nan
    m = RE_GIA.search(t)
    if not m:
        return np.nan
    if m.group(1):
        ty = so(m.group(1))
        le = m.group(3)
        if le:
            ty += int(le) / (1000 if len(le) == 3 or m.group(4) else 10 ** len(le))
        return ty * 1e9
    return so(m.group(5)) * 1e6


RE_GIA_VB = re.compile(
    r'(?<![\dx])(\d{1,3}(?:[.,]\d{1,3})?)\s*(tỷ|tỉ)(?:\s*(\d{1,3})(?:\s*(?:triệu|tr))?(?!\s*(?:m\b|m2|m²|tầng|pn|phòng|%)))?(?!\w)(?!\s*/\s*(?:m|th|tháng|năm|căn))'
    r'|(?<![\dx.,])(\d{3,4})\s*(triệu|tr)(?![\w/])(?!\s*/)', re.I)
RE_PHU_DINH = re.compile(
    r'(vay|lãi|hỗ trợ|chiết khấu|cọc|thanh toán|trả trước|trước|doanh thu|thuê|hđt|vốn|chỉ cần|giảm|hạ|rẻ hơn|chênh|'
    r'lợi nhuận|thu nhập|\(|%)', re.I)
RE_KHANG_DINH = re.compile(r'(giá|bán|chào|chỉ|nhỉnh|còn|hơn|tầm|khoảng|=)\s*[:\-]?\s*$', re.I)


def gia_tu_van_ban(s):
    if pd.isna(s):
        return np.nan
    t = str(s)
    ung_vien = []
    for m in RE_GIA_VB.finditer(t):
        truoc = t[max(0, m.start() - 20):m.start()]
        sau = t[m.end():m.end() + 6]
        if RE_PHU_DINH.search(truoc[-12:]) or re.match(r'\s*(/|%|\))', sau):
            continue
        if m.group(1):
            ty = so(m.group(1))
            if m.group(3):
                le = m.group(3)
                ty += int(le) / (1000 if len(le) == 3 else 10 ** len(le))
            gia = ty * 1e9
        else:
            gia = so(m.group(4)) * 1e6
        ung_vien.append((bool(RE_KHANG_DINH.search(truoc)), gia))
    if not ung_vien:
        return np.nan
    tot = [g for k, g in ung_vien if k]
    return tot[0] if tot else ung_vien[0][1]


RE_DT = re.compile(r'(?<![\d.,])(\d{1,5}(?:[.,]\d{1,2})?)\s*(m2|m²|mét vuông|met vuong)', re.I)


def dien_tich_tu_van_ban(s):
    if pd.isna(s):
        return np.nan
    m = RE_DT.search(str(s))
    return so(m.group(1)) if m else np.nan
