# Dự đoán giá nhà Việt Nam bằng các mô hình hồi quy học máy

## Dữ liệu
Ghép 6 bộ tin đăng bán bất động sản Việt Nam trên Kaggle, tổng 1.429.399 dòng thô:

| Nguồn | Kaggle | Số dòng | Thời gian |
|---|---|---|---|
| 1 | yashdev01/vietnam-real-estates | 1.000.000 | 06–12/2025 |
| 2 | qmanhbeo/vietnamese-real-estate-listings-may-2024 | 236.226 | 03–09/2025 |
| 3 | ladcva/vietnam-housing-dataset-hanoi | 82.497 | 2019–2020 |
| 4 | cresht2606/vietnam-real-estate-datasets-catalyst | 66.912 | 2023–12/2025 |
| 5 | nguyentiennhan/vietnam-housing-dataset-2024 | 30.229 | 2024 |
| 6 | huytrngquc/hanoi-housing-price-2024 | 13.535 | 10–12/2024 |

File gốc (không đưa lên git vì nặng 1,2 GB) tải từ Kaggle rồi đặt vào `data/raw/` với tên:
`nguon1_vietnam_real_estate_2025.csv`, `nguon2_vn_real_estate_apr_sep_2025.csv`, `nguon3_vn_housing_hanoi_2020.csv`,
`nguon4_batdongsan_house_buying_2025.csv`, `nguon5_vietnam_housing_2024.csv`, `nguon6_hanoi_houseprice_2024.csv`.

Sau làm sạch còn **863.524 mẫu**. Mô hình cuối (notebook 08 tự chọn theo tổng hạng trên tập kiểm định) là kết hợp
XGBoost + LightGBM + CatBoost với trọng số tối ưu NNLS: trên 129.529 căn của tập kiểm tra đạt RMSE (log) 0,376,
R² 0,881, sai lệch trung vị 16,5%, 57% số căn lệch không quá 20%.

## Cấu trúc thư mục
```
data/raw          dữ liệu gốc 6 nguồn
data/interim      dữ liệu trung gian (sau khi ghép)
data/processed    dữ liệu sạch dùng để huấn luyện
notebooks/        các bước xử lý, đánh số theo thứ tự chạy
src/              hàm dùng chung (xử lý chuỗi, địa danh, ...)
app/              ứng dụng web FastAPI + HTML/CSS/JS
models/           mô hình đã huấn luyện
reports/          hình ảnh, báo cáo
```

## Các notebook (chạy theo thứ tự)
| # | Notebook | Nội dung |
|---|---|---|
| 1 | `01_tong_quan_du_lieu_tho` | Mô tả 6 nguồn và mức độ "dơ" của dữ liệu gốc (1.429.399 dòng) |
| 2 | `02_chuan_hoa_va_ghep_nguon` | Đưa 6 nguồn về cùng 28 cột, cùng đơn vị, địa giới mới 34 tỉnh, chuẩn hoá Unicode; đọc giá/diện tích từ văn bản; từ điển dữ liệu |
| 3 | `03_lam_sach_du_lieu` | Loại tin ngoài phạm vi, sửa lỗi đơn vị/định dạng, khôi phục dữ liệu thiếu (văn bản, KNN toạ độ, mô hình phân loại), loại trùng trong và giữa các nguồn, loại ngoại lai theo ngữ cảnh – còn 863.524 mẫu |
| 4 | `04_phan_tich_va_mat_can_bang` | Phân tích dữ liệu, đo mất cân bằng, chia tập phân tầng, trọng số mẫu, tăng mẫu nhóm hiếm |
| 5 | `05_dac_trung_ma_hoa_chuan_hoa` | Tạo đặc trưng, điền thiếu, target encoding out-of-fold, one-hot, chuẩn hoá, chọn đặc trưng |
| 6 | `06_mo_hinh_tu_code` | Linear Regression (nghiệm đóng, Gradient Descent), Ridge, Kernel Ridge tự cài bằng NumPy |
| 7 | `07_nhieu_mo_hinh_thu_vien` | 13 mô hình thư viện + dò tham số + ensemble + kiểm định chéo 5-fold |
| 8 | `08_mat_can_bang_va_mo_hinh_cuoi` | 5 cách xử lý mất cân bằng khi huấn luyện, chọn mô hình cuối, phân tích sai số, permutation importance |

Kết quả (bảng CSV, hình) được lưu trong `reports/`.

## Mã nguồn dùng chung (`src/`)
- `xu_ly_chuoi.py` – đọc giá/diện tích từ chuỗi và văn bản, chuẩn hoá địa danh và mã Unicode / kiểu đặt dấu, bảng sáp nhập tỉnh 07/2025
- `can_bang.py` – tầng, trọng số nghịch tần suất, tăng mẫu nhóm hiếm
- `dac_trung.py` – lớp `BoTienXuLy` (fit trên train, dùng lại cho val/test và app)
- `mo_hinh_tu_code.py` – các mô hình tự cài đặt bằng NumPy
- `danh_gia.py` – các chỉ số đánh giá chung, đánh giá theo nhóm
- `du_doan.py` – nạp bộ tiền xử lý + mô hình cuối, định giá một căn
- `tao_tai_nguyen_app.py` – tạo danh mục địa danh, số liệu thị trường, tổng quan dữ liệu cho web app

## Web app (`app/`)
FastAPI (`app/main.py`) + giao diện HTML/CSS/JS thuần (`app/static/`), không cần internet:
- **Định giá:** nhập đặc điểm căn nhà, hình mặt tiền vẽ theo số tầng/mặt tiền, giá ước tính, khoảng giá 80%, so sánh với trung vị khu vực
- **Thị trường:** trung vị giá/m² theo quận cho từng tỉnh và loại BĐS
- **Dữ liệu & mô hình:** hành trình làm sạch dữ liệu, lỗi đã sửa, chất lượng trước/sau, mất cân bằng, so sánh mô hình

API: `GET /api/danh-muc`, `GET /api/thi-truong?tinh=...&loai=...`, `GET /api/tong-quan`, `POST /api/dinh-gia`, tài liệu tự động tại `/docs`.

## Chạy trên máy (VS Code)
```
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
```
Mở thư mục dự án bằng VS Code, chọn interpreter `.venv`, cài extension Jupyter rồi chạy lần lượt các notebook 01 → 08, sau đó:
```
.venv\Scripts\python src\tao_tai_nguyen_app.py
.venv\Scripts\uvicorn app.main:app --port 8000
```
Mở http://localhost:8000

## Chạy bằng Docker
Trên Windows: bấm đúp **`chay_docker.bat`** – file tự mở Docker Desktop nếu chưa chạy, khởi động container, chờ mô hình nạp xong
rồi mở trình duyệt tại http://localhost:8000. Bấm **`dung_docker.bat`** để tắt; chạy `chay_docker.bat build` để build lại sau khi sửa code.

Hoặc dùng lệnh:
```
docker compose up --build
```
Mở http://localhost:8000 (tài liệu API: http://localhost:8000/docs)

## Lưu ý về mô hình trên git
Hai tệp `models/xgb.json` (150 MB) và `models/lightgbm.txt` (373 MB) vượt giới hạn 100 MB/tệp của GitHub, nên cả ba tệp mô
hình của ensemble (kèm `models/catboost.cbm`, 25 MB) đều không có trong repo. Chạy lại notebook 07 → 08 (khoảng 1,5 giờ) để tạo lại, hoặc chép ba tệp này
vào thư mục `models/`. Các tệp nhỏ đi kèm (`bo_tien_xu_ly.joblib`, `thong_tin_mo_hinh.json`, `danh_muc.json`,
`thi_truong.json`, `tong_quan_du_lieu.json`) đã có sẵn.
