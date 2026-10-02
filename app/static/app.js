const $ = (s, g = document) => g.querySelector(s);
const $$ = (s, g = document) => [...g.querySelectorAll(s)];
const GIAM_CHUYEN_DONG = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const LOAI = [
  { v: 'Nhà ở', nhan: 'Nhà phố', icon: '<path d="M10 32V12l6-4 6 4v20M22 32V16h8v16" /><path d="M14 18h4M14 24h4M25 21h2" />' },
  { v: 'Căn hộ', nhan: 'Căn hộ', icon: '<path d="M11 32V6h18v26" /><path d="M15 10h3M22 10h3M15 15h3M22 15h3M15 20h3M22 20h3M18 32v-5h4v5" />' },
  { v: 'Đất', nhan: 'Đất nền', icon: '<path d="M5 30l7-10h17l6 10z" stroke-dasharray="3 2" /><path d="M27 20v-8M27 12h6v4h-6" />' },
  { v: 'Biệt thự/Liền kề', nhan: 'Biệt thự, liền kề', icon: '<path d="M7 18L20 8l13 10M10 16v16h20V16" /><path d="M17 32v-7h6v7M13 21h3M24 21h3" />' },
  { v: 'Shophouse', nhan: 'Shophouse', icon: '<path d="M9 32V8h22v24" /><path d="M9 22h22M12 32v-8h16v8M13 12h4M23 12h4M13 17h4M23 17h4" />' },
];
const CHIP = {
  vi_tri: [['Mặt phố', 'Mặt phố'], ['Ngõ/Hẻm', 'Trong ngõ, hẻm']],
  phap_ly: [['Có sổ', 'Có sổ đỏ, sổ hồng'], ['Hợp đồng mua bán', 'Hợp đồng mua bán'], ['Đang chờ sổ', 'Đang chờ sổ']],
  noi_that: [['Đầy đủ', 'Đầy đủ'], ['Cơ bản', 'Cơ bản'], ['Không / thô', 'Nhà thô']],
  huong_nha: ['Đông', 'Tây', 'Nam', 'Bắc', 'Đông Nam', 'Đông Bắc', 'Tây Nam', 'Tây Bắc'].map(h => [h, h]),
};

const so = (x, d = 0) => Number(x).toLocaleString('vi-VN', { minimumFractionDigits: d, maximumFractionDigits: d });
const ty = x => so(x / 1e9, 2);
const trieuM2 = x => `${so(x / 1e6, x < 1e8 ? 1 : 0)} triệu/m²`;
const kepGiua = (v, a, b) => Math.min(b, Math.max(a, v));
const soHoacRong = el => { const v = parseFloat(el.value); return Number.isFinite(v) && v > 0 ? v : null; };

let danhMuc = null;
const trangThai = { loai: 'Nhà ở', chip: {}, ketCau: { 'so-tang': 4, 'phong-ngu': 3, 'phong-tam': 3 }, giaDangHien: 0 };

async function api(duongDan, tuyChon) {
  const r = await fetch(duongDan, tuyChon);
  const noiDung = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(noiDung.detail ? (typeof noiDung.detail === 'string' ? noiDung.detail : 'Dữ liệu nhập chưa hợp lệ, kiểm tra lại các ô số.') : `Máy chủ trả lỗi ${r.status}`);
  return noiDung;
}

function taoChonLoai(khung, ten, coTatCa, khiDoi) {
  const ds = coTatCa ? [{ v: 'Tất cả', nhan: 'Tất cả' }, ...LOAI] : LOAI;
  khung.innerHTML = ds.map((l, i) => `
    <label>
      <input type="radio" name="${ten}" value="${l.v}" ${i === 0 ? 'checked' : ''}>
      ${l.icon ? `<svg viewBox="0 0 40 36" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${l.icon}</svg>` : ''}
      <span>${l.nhan}</span>
    </label>`).join('');
  khung.addEventListener('change', e => khiDoi(e.target.value));
}

function taoChip() {
  $$('.hang-chip').forEach(hang => {
    const truong = hang.dataset.truong;
    CHIP[truong].forEach(([gt, nhan]) => {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'chip'; b.textContent = nhan;
      b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', () => {
        const dangChon = trangThai.chip[truong] === gt;
        trangThai.chip[truong] = dangChon ? null : gt;
        $$('.chip', hang).forEach(c => c.setAttribute('aria-pressed', 'false'));
        if (!dangChon) b.setAttribute('aria-pressed', 'true');
        veNha();
      });
      hang.appendChild(b);
    });
  });
}

function datTuyChon(select, ds, nhanRong) {
  select.innerHTML = `<option value="">${nhanRong}</option>` + ds.map(x => `<option>${x}</option>`).join('');
}

function capNhatQuan() {
  const tinh = $('#tinh').value;
  datTuyChon($('#quan'), danhMuc.quan[tinh] || [], 'Không rõ');
  datTuyChon($('#du-an'), danhMuc.du_an[tinh] || [], 'Không thuộc dự án');
  capNhatPhuong();
}
function capNhatPhuong() {
  datTuyChon($('#phuong'), danhMuc.phuong[`${$('#tinh').value}|${$('#quan').value}`] || [], 'Không rõ');
}

function doiLoai(v) {
  trangThai.loai = v;
  const laDat = v === 'Đất';
  $('#nhom-ket-cau').hidden = laDat;
  $('#o-du-an').hidden = laDat;
  if (v === 'Căn hộ') { capNhatBuoc('so-tang', 0); $('[data-id="so-tang"]').hidden = true; } else { $('[data-id="so-tang"]').hidden = false; if (!trangThai.ketCau['so-tang']) capNhatBuoc('so-tang', 4); }
  veNha();
}

function capNhatBuoc(id, giaTri) {
  trangThai.ketCau[id] = kepGiua(giaTri, 0, id === 'so-tang' ? 15 : 12);
  $(`#${id}`).textContent = trangThai.ketCau[id] || '–';
}

function veNha() {
  const svg = $('#mat-nha');
  const loai = trangThai.loai;
  const mt = soHoacRong($('#mat-tien'));
  const dt = soHoacRong($('#dien-tich'));
  const tang = trangThai.ketCau['so-tang'];
  const viTri = trangThai.chip.vi_tri;
  const DAT = 258, VANG = '#E3A92B', VANG_DAM = '#C98F17', CHOP = '#2E6B57', KINH = '#C3D7EC', XAM = '#D7DDE5';
  let h = `<rect x="0" y="${DAT}" width="340" height="32" fill="#E6EAF0"/><line x1="0" y1="${DAT}" x2="340" y2="${DAT}" stroke="#AEB8C5" stroke-width="1.5"/>`;
  const nhaBen = (x, w, n) => {
    let s = `<rect x="${x}" y="${DAT - n * 28}" width="${w}" height="${n * 28}" fill="${XAM}"/>`;
    for (let i = 1; i < n; i++) s += `<rect x="${x + w * 0.3}" y="${DAT - (i + 1) * 28 + 7}" width="${w * 0.4}" height="14" fill="#EEF2F6"/>`;
    return s;
  };
  const kichThuoc = (x, w, nhan) => `<g stroke="#5B6676" stroke-width="1"><line x1="${x}" y1="${DAT + 14}" x2="${x + w}" y2="${DAT + 14}"/><line x1="${x}" y1="${DAT + 9}" x2="${x}" y2="${DAT + 19}"/><line x1="${x + w}" y1="${DAT + 9}" x2="${x + w}" y2="${DAT + 19}"/></g><text x="${x + w / 2}" y="${DAT + 28}" text-anchor="middle" font-size="11" fill="#5B6676" font-family="Segoe UI, sans-serif">${nhan}</text>`;
  let chuThich = '';

  if (loai === 'Nhà ở' || loai === 'Shophouse') {
    const m = kepGiua(mt || 4.5, 2.5, 12);
    const w = 36 + m * 15, n = kepGiua(tang || 3, 1, 8), fh = n > 6 ? 25 : 29, x0 = 170 - w / 2;
    h += nhaBen(x0 - 62, 58, 3) + nhaBen(x0 + w + 4, 58, Math.min(n + 2, 8));
    for (let i = 0; i < n; i++) {
      const y = DAT - (i + 1) * fh;
      h += `<rect x="${x0}" y="${y}" width="${w}" height="${fh}" fill="${i % 2 ? VANG : '#E8B240'}"/><line x1="${x0}" y1="${y}" x2="${x0 + w}" y2="${y}" stroke="${VANG_DAM}" stroke-width="2"/>`;
      if (i === 0) {
        if (loai === 'Shophouse') {
          h += `<rect x="${x0 + 6}" y="${y + 5}" width="${w - 12}" height="${fh - 5}" fill="${KINH}"/>`;
          for (let k = 1; k < 4; k++) h += `<line x1="${x0 + 6 + (w - 12) * k / 4}" y1="${y + 5}" x2="${x0 + 6 + (w - 12) * k / 4}" y2="${DAT}" stroke="#8FA9C4"/>`;
        } else if (viTri === 'Mặt phố') {
          h += `<rect x="${x0 + 6}" y="${y + 5}" width="${w - 12}" height="${fh - 5}" fill="#A3AEBB"/>`;
          for (let k = y + 9; k < DAT; k += 4) h += `<line x1="${x0 + 6}" y1="${k}" x2="${x0 + w - 6}" y2="${k}" stroke="#8994A2"/>`;
        } else {
          h += `<rect x="${x0 + w / 2 - 9}" y="${y + 7}" width="18" height="${fh - 7}" fill="${CHOP}"/>`;
        }
      } else {
        const cw = Math.max(16, w * 0.42), cx = x0 + (w - cw) / 2, cy = y + fh * 0.18, ch = fh * 0.62;
        h += `<rect x="${cx}" y="${cy}" width="${cw}" height="${ch}" fill="${KINH}"/><rect x="${cx - 8}" y="${cy}" width="7" height="${ch}" fill="${CHOP}"/><rect x="${cx + cw + 1}" y="${cy}" width="7" height="${ch}" fill="${CHOP}"/>`;
        h += `<line x1="${cx - 10}" y1="${cy + ch}" x2="${cx + cw + 10}" y2="${cy + ch}" stroke="#1B2638" stroke-width="1.6"/>`;
        for (let k = cx - 8; k <= cx + cw + 8; k += 5) h += `<line x1="${k}" y1="${cy + ch - 7}" x2="${k}" y2="${cy + ch}" stroke="#1B2638" stroke-width="0.8"/>`;
      }
    }
    const dinh = DAT - n * fh;
    h += `<rect x="${x0 - 3}" y="${dinh - 5}" width="${w + 6}" height="5" fill="${VANG_DAM}"/>`;
    if (n >= 2) h += `<rect x="${x0 + 4}" y="${dinh - 21}" width="${w * 0.42}" height="16" fill="#E8B240"/><rect x="${x0 + 4}" y="${dinh - 24}" width="${w * 0.42 + 4}" height="3" fill="${VANG_DAM}"/>`;
    h += kichThuoc(x0, w, mt ? `mặt tiền ${so(mt, 1)} m` : 'mặt tiền chưa nhập');
    chuThich = `${loai === 'Shophouse' ? 'Shophouse' : 'Nhà phố'} ${tang ? `${tang} tầng` : 'chưa rõ số tầng'}${viTri ? (viTri === 'Mặt phố' ? ', mặt phố' : ', trong ngõ') : ''}${dt ? `, ${so(dt, 0)} m²` : ''}`;
  } else if (loai === 'Biệt thự/Liền kề') {
    const n = kepGiua(tang || 3, 1, 4), fh = 34, w = 190, x0 = 75;
    for (let c = 0; c < 2; c++) h += `<circle cx="${c ? 300 : 40}" cy="${DAT - 26}" r="22" fill="#5E9C7E"/><rect x="${(c ? 300 : 40) - 3}" y="${DAT - 10}" width="6" height="10" fill="#6B5B45"/>`;
    for (let i = 0; i < n; i++) {
      const y = DAT - (i + 1) * fh;
      h += `<rect x="${x0}" y="${y}" width="${w}" height="${fh}" fill="#F1E4C6"/><line x1="${x0}" y1="${y}" x2="${x0 + w}" y2="${y}" stroke="${VANG_DAM}" stroke-width="2"/>`;
      for (const cx of [x0 + 22, x0 + w - 62]) h += `<rect x="${cx}" y="${y + 7}" width="40" height="${fh - 14}" fill="${KINH}"/><rect x="${cx - 6}" y="${y + 7}" width="5" height="${fh - 14}" fill="${CHOP}"/><rect x="${cx + 41}" y="${y + 7}" width="5" height="${fh - 14}" fill="${CHOP}"/>`;
      if (i === 0) h += `<rect x="${x0 + w / 2 - 12}" y="${y + 8}" width="24" height="${fh - 8}" fill="${CHOP}"/>`;
    }
    const dinh = DAT - n * fh;
    h += `<polygon points="${x0 - 14},${dinh} ${x0 + w + 14},${dinh} ${x0 + w / 2},${dinh - 46}" fill="#B5452F"/>`;
    h += kichThuoc(x0, w, mt ? `mặt tiền ${so(mt, 1)} m` : 'mặt tiền chưa nhập');
    chuThich = `Biệt thự, liền kề ${tang ? `${tang} tầng` : ''}${dt ? `, ${so(dt, 0)} m²` : ''}`;
  } else if (loai === 'Căn hộ') {
    const x0 = 95, w = 150, fh = 16, n = 12;
    h += nhaBen(20, 60, 6) + nhaBen(262, 60, 5);
    h += `<rect x="${x0}" y="${DAT - n * fh}" width="${w}" height="${n * fh}" fill="#C7D1DD"/><line x1="${x0 + w / 2}" y1="${DAT - n * fh}" x2="${x0 + w / 2}" y2="${DAT - n * fh - 18}" stroke="#7D8896" stroke-width="2"/>`;
    for (let i = 0; i < n; i++) for (let k = 0; k < 5; k++) {
      const noiBat = i === 7 && k === 2;
      h += `<rect x="${x0 + 9 + k * 28}" y="${DAT - (i + 1) * fh + 4}" width="20" height="9" fill="${noiBat ? VANG : '#EEF2F7'}" ${noiBat ? `stroke="${VANG_DAM}" stroke-width="1.5"` : ''}/>`;
    }
    h += `<rect x="${x0 + w / 2 - 14}" y="${DAT - 14}" width="28" height="14" fill="#5B6676"/>`;
    chuThich = `Căn hộ${dt ? ` ${so(dt, 0)} m²` : ''}${trangThai.ketCau['phong-ngu'] ? `, ${trangThai.ketCau['phong-ngu']} phòng ngủ` : ''}`;
  } else {
    h += `<polygon points="70,${DAT} 270,${DAT} 238,${DAT - 52} 102,${DAT - 52}" fill="#D9C79E" stroke="#8C7A52" stroke-dasharray="6 4" stroke-width="1.5"/>`;
    h += `<line x1="250" y1="${DAT - 30}" x2="250" y2="${DAT - 88}" stroke="#6B5B45" stroke-width="3"/><rect x="226" y="${DAT - 112}" width="52" height="28" rx="3" fill="#FFFFFF" stroke="#1D4E9E" stroke-width="2"/><text x="252" y="${DAT - 93}" text-anchor="middle" font-size="13" font-weight="600" fill="#1D4E9E" font-family="Bahnschrift, sans-serif">Bán</text>`;
    h += kichThuoc(70, 200, mt ? `mặt tiền ${so(mt, 1)} m` : 'mặt tiền chưa nhập');
    chuThich = `Đất nền${dt ? ` ${so(dt, 0)} m²` : ''}`;
  }
  svg.innerHTML = h;
  $('#chu-thich-nha').textContent = chuThich;
}

function demSo(den) {
  const el = $('#gia-so');
  const tu = trangThai.giaDangHien;
  trangThai.giaDangHien = den;
  if (GIAM_CHUYEN_DONG || !tu) { el.textContent = ty(den); return; }
  const batDau = performance.now();
  const buoc = t => {
    const p = Math.min(1, (t - batDau) / 600);
    const e = 1 - Math.pow(1 - p, 3);
    el.textContent = ty(tu + (den - tu) * e);
    if (p < 1) requestAnimationFrame(buoc);
  };
  requestAnimationFrame(buoc);
}

function hienKetQua(kq, yeuCau) {
  demSo(kq.gia);
  const bien = $('#bien-gia');
  bien.classList.remove('moi'); void bien.offsetWidth; bien.classList.add('moi');
  $('#chi-tiet').hidden = false;
  $('#don-gia').textContent = trieuM2(kq.don_gia_m2);
  $('#khoang-gia').textContent = `${ty(kq.thap)} – ${ty(kq.cao)} tỷ`;
  $('#moc-gia').style.left = `${12 + 76 * (kq.gia - kq.thap) / (kq.cao - kq.thap)}%`;
  const ss = $('#so-sanh');
  const tc = kq.tham_chieu;
  if (tc) {
    const lon = Math.max(kq.don_gia_m2, tc.gia_m2);
    const chenh = (kq.don_gia_m2 / tc.gia_m2 - 1) * 100;
    const nhomSoSanh = tc.cung_loai ? LOAI.find(l => l.v === yeuCau.loai_bds).nhan.toLowerCase() : 'nhà đất nói chung';
    ss.innerHTML = `
      <h3>So với giá/m² trung vị ở ${tc.pham_vi}</h3>
      <div class="cot"><span>Căn này</span><span class="thanh" style="width:${100 * kq.don_gia_m2 / lon}%"></span><span>${trieuM2(kq.don_gia_m2)}</span></div>
      <div class="cot"><span>Trung vị khu vực</span><span class="thanh tt" style="width:${100 * tc.gia_m2 / lon}%"></span><span>${trieuM2(tc.gia_m2)}</span></div>
      <p class="nhan-xet">Đơn giá ${Math.abs(chenh) < 3 ? 'ngang' : chenh > 0 ? `cao hơn ${so(chenh, 0)}%` : `thấp hơn ${so(-chenh, 0)}%`} so với ${so(tc.n)} tin ${nhomSoSanh} đã làm sạch ở ${tc.pham_vi}.</p>`;
  } else ss.innerHTML = '';
  luuLichSu(kq, yeuCau);
}

function docLichSu() { try { return JSON.parse(localStorage.getItem('lich-su-dinh-gia') || '[]'); } catch { return []; } }
function luuLichSu(kq, yc) {
  const ds = [{ mo_ta: `${LOAI.find(l => l.v === yc.loai_bds).nhan} ${so(yc.dien_tich_m2, 0)} m², ${yc.quan_huyen || yc.tinh}`, gia: kq.gia }, ...docLichSu()].slice(0, 5);
  try { localStorage.setItem('lich-su-dinh-gia', JSON.stringify(ds)); } catch { }
  veLichSu(ds);
}
function veLichSu(ds = docLichSu()) {
  $('#lich-su').hidden = !ds.length;
  $('#ds-lich-su').innerHTML = ds.map(x => `<li><span>${x.mo_ta}</span><strong>${ty(x.gia)} tỷ</strong></li>`).join('');
}

async function guiDinhGia(e) {
  e.preventDefault();
  const loi = $('#loi'); loi.hidden = true;
  const dt = soHoacRong($('#dien-tich'));
  if (!dt || dt < 10) { loi.textContent = 'Nhập diện tích từ 10 m² trở lên.'; loi.hidden = false; $('#dien-tich').focus(); return; }
  const laDat = trangThai.loai === 'Đất';
  const kc = trangThai.ketCau;
  const yeuCau = {
    loai_bds: trangThai.loai, tinh: $('#tinh').value, quan_huyen: $('#quan').value || null, phuong_xa: $('#phuong').value || null,
    duong: $('#duong').value.trim() || null, du_an: laDat ? null : ($('#du-an').value || null), dien_tich_m2: dt,
    mat_tien_m: soHoacRong($('#mat-tien')), chieu_dai_m: soHoacRong($('#chieu-dai')), duong_vao_m: soHoacRong($('#duong-vao')),
    so_tang: laDat || trangThai.loai === 'Căn hộ' ? null : (kc['so-tang'] || null),
    so_phong_ngu: laDat ? null : (kc['phong-ngu'] || null), so_phong_tam: laDat ? null : (kc['phong-tam'] || null),
    huong_nha: trangThai.chip.huong_nha || null, phap_ly: trangThai.chip.phap_ly || null,
    noi_that: trangThai.chip.noi_that || null, vi_tri: trangThai.chip.vi_tri || null,
  };
  const nut = $('#nut-dinh-gia');
  nut.setAttribute('aria-busy', 'true'); nut.textContent = 'Đang định giá…';
  try {
    hienKetQua(await api('/api/dinh-gia', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(yeuCau) }), yeuCau);
    if (window.innerWidth < 980) $('#bien-gia').scrollIntoView({ behavior: GIAM_CHUYEN_DONG ? 'auto' : 'smooth', block: 'center' });
  } catch (err) {
    loi.textContent = `Chưa định giá được: ${err.message}`; loi.hidden = false;
  } finally {
    nut.removeAttribute('aria-busy'); nut.textContent = 'Định giá căn này';
  }
}

async function veThiTruong() {
  const tinh = $('#tt-tinh').value;
  const loai = $('input[name="tt-loai"]:checked').value;
  try {
    const d = await api(`/api/thi-truong?tinh=${encodeURIComponent(tinh)}&loai=${encodeURIComponent(loai)}`);
    const tong = d.tong[loai] || d.tong['Tất cả'];
    $('#tt-tom-tat').textContent = d.quan.length
      ? `${tinh}: ${so(tong.n)} tin ${loai === 'Tất cả' ? '' : LOAI.find(l => l.v === loai).nhan.toLowerCase() + ' '}đã làm sạch, trung vị ${trieuM2(tong.gia_m2)}, giá trung vị ${ty(tong.gia)} tỷ cho ${so(tong.dien_tich, 0)} m².`
      : `${tinh} chưa có quận nào đủ 20 tin cho loại này. Thử chọn "Tất cả".`;
    const lon = Math.max(...d.quan.map(q => q.gia_m2), 1);
    $('#tt-quan').innerHTML = d.quan.map(q => `
      <li><span class="ten">${q.quan}</span><span class="thanh" style="width:${100 * q.gia_m2 / lon}%"></span>
      <span class="so">${so(q.gia_m2 / 1e6, 0)} tr/m²</span><span class="phu">${so(q.n)} tin, ${ty(q.gia)} tỷ</span></li>`).join('');
  } catch (err) {
    $('#tt-tom-tat').textContent = err.message; $('#tt-quan').innerHTML = '';
  }
}

let daVeDuLieu = false;
async function veDuLieu() {
  if (daVeDuLieu) return;
  daVeDuLieu = true;
  const { du_lieu: d, mo_hinh: m } = await api('/api/tong-quan');
  $('#dl-tieu-de').textContent = `Từ ${so(d.tong_tho)} tin thô đến ${so(d.tong_sach)} mẫu sạch`;
  $('#dl-nguon').innerHTML = `<thead><tr><th>Nguồn</th><th>Bộ dữ liệu Kaggle</th><th class="so">Tin thô</th><th class="so">Sau làm sạch</th><th class="so">Giữ lại</th></tr></thead><tbody>` +
    d.nguon.map(n => `<tr><td>${n.ma}</td><td>${n.ten}</td><td class="so">${so(n.tho)}</td><td class="so">${so(n.sach)}</td><td class="so">${so(100 * n.sach / n.tho, 1)}%</td></tr>`).join('') +
    `<tr class="noi-bat"><td></td><td>Tổng</td><td class="so">${so(d.tong_tho)}</td><td class="so">${so(d.tong_sach)}</td><td class="so">${so(100 * d.tong_sach / d.tong_tho, 1)}%</td></tr></tbody>`;
  const buocs = [{ buoc: 'Ghép 6 nguồn, chuẩn hoá cấu trúc và đơn vị', sau: d.tong_tho, bo: 0 }, ...d.nhat_ky];
  $('#dl-pheu').innerHTML = buocs.map(b => `<li><div class="vach"><span style="width:${100 * b.sau / d.tong_tho}%"></span><em>${b.buoc.replace(/^\w+\.\s*/, '')}</em></div>
    <div class="so"><b>${so(b.sau)}</b>${b.bo ? `bỏ ${so(b.bo)}` : 'điểm xuất phát'}</div></li>`).join('');
  $('#dl-sua').innerHTML = d.sua_loi.map(s => `<li><span>${s.viec.replace(' -> ', ' → ')}</span><b>${so(s.so)}</b></li>`).join('');
  $('#dl-chat-luong').innerHTML = `<thead><tr><th>Chỉ số</th><th class="so">Trước</th><th class="so">Sau</th></tr></thead><tbody>` +
    d.chat_luong.map(c => { const pt = c.chi_so.includes('%'); return `<tr><td>${c.chi_so.replace(' (%)', '').replace(' (số tin)', '')}</td><td class="so">${pt ? so(c.truoc, 1) + '%' : so(c.truoc)}</td><td class="so">${pt ? so(c.sau, 1) + '%' : so(c.sau)}</td></tr>`; }).join('') + '</tbody>';
  const cotNgang = (el, obj, dinhDang) => {
    const lon = Math.max(...Object.values(obj));
    el.innerHTML = Object.entries(obj).map(([k, v]) => `<li><span>${k}</span><span class="thanh" style="width:${100 * v / lon}%"></span><span class="so">${dinhDang(v)}</span></li>`).join('');
  };
  const tongMau = Object.values(d.loai_bds).reduce((a, b) => a + b, 0);
  cotNgang($('#dl-loai'), d.loai_bds, v => `${so(100 * v / tongMau, 1)}%`);
  cotNgang($('#dl-vung'), d.vung, v => `${so(100 * v / tongMau, 1)}%`);
  if (m.mat_can_bang) {
    $('#dl-can-bang').innerHTML = `<thead><tr><th>Cách huấn luyện</th><th class="so">RMSE (log)</th><th class="so">MAPE trung bình các loại BĐS</th><th class="so">MAPE trung bình các phân khúc giá</th></tr></thead><tbody>` +
      m.mat_can_bang.map(c => `<tr class="${m.mo_hinh.endsWith(c.cach) ? 'noi-bat' : ''}"><td>${c.cach}</td><td class="so">${so(c.rmse, 4)}</td><td class="so">${so(c.mape_macro_loai, 2)}%</td><td class="so">${so(c.mape_macro_phan_khuc, 2)}%</td></tr>`).join('') + '</tbody>';
  }
  const kq = m.ket_qua_test;
  $('#dl-mo-hinh-cuoi').textContent = `Mô hình dùng trong ứng dụng: ${m.mo_hinh}. Trên ${so(m.so_mau_test)} căn của tập kiểm tra (chưa dùng khi huấn luyện): R² ${so(kq['R² log'], 3)}, sai lệch trung vị ${so(kq['Trung vị APE (%)'], 1)}%, ${so(kq['Lệch ≤20% (%)'], 0)}% căn được dự đoán lệch không quá 20%. Bảng xếp theo RMSE trên thang log, càng nhỏ càng tốt.`;
  const MAU = { 'Mô hình cuối': '#E3A92B', 'Kết hợp': '#B5452F', 'Boosting': '#1D4E9E', 'Bagging': '#6FA77F', 'Mạng nơ-ron': '#8E5BA8', 'Cây đơn': '#D9A441', 'Tự code (NumPy)': '#5B6FB5', 'Tuyến tính': '#9AA4B1', 'Lân cận': '#9C7F68' };
  const coSan = m.so_sanh.some(x => x.mo_hinh === m.mo_hinh);
  const ds = (coSan
    ? m.so_sanh.map(x => x.mo_hinh === m.mo_hinh ? { ...x, mo_hinh: `${x.mo_hinh} (dùng trong ứng dụng)`, cuoi: true } : x)
    : [{ mo_hinh: `${m.mo_hinh} (dùng trong ứng dụng)`, nhom: 'Mô hình cuối', rmse: kq['RMSE log'], r2: kq['R² log'], mape: kq['MAPE (%)'], lech20: kq['Lệch ≤20% (%)'], thoi_gian: null, cuoi: true },
      ...m.so_sanh]).sort((a, b) => a.rmse - b.rmse);
  $('#dl-so-sanh').outerHTML = `<div class="cuon"><table class="bang" id="dl-so-sanh"><thead><tr><th>Mô hình</th><th>Nhóm</th><th class="so">RMSE (log)</th><th class="so">R² (log)</th><th class="so">MAPE</th><th class="so">Lệch ≤ 20%</th><th class="so">Huấn luyện</th></tr></thead><tbody>` +
    ds.map(x => `<tr class="${x.cuoi ? 'noi-bat' : ''}"><td>${x.mo_hinh}</td><td><span class="cham" style="--m:${MAU[x.nhom] || '#1D4E9E'}"></span>${x.nhom}</td>
      <td class="so">${so(x.rmse, 3)}</td><td class="so">${so(x.r2, 3)}</td><td class="so">${so(x.mape, 1)}%</td><td class="so">${so(x.lech20, 1)}%</td>
      <td class="so">${x.thoi_gian == null ? '' : x.thoi_gian < 60 ? `${so(x.thoi_gian, 1)} giây` : `${so(x.thoi_gian / 60, 1)} phút`}</td></tr>`).join('') + '</tbody></table></div>';
  $('#dl-chu-giai').hidden = true;
  if (m.quan_trong) {
    const TEN = { log_dien_tich: 'Diện tích', te_duong: 'Mặt bằng giá của tuyến đường', te_phuong: 'Mặt bằng giá của phường', te_du_an: 'Mặt bằng giá của dự án',
      te_quan: 'Mặt bằng giá của quận', te_tinh: 'Mặt bằng giá của tỉnh', thang_tu_2019: 'Thời điểm đăng tin', so_tang: 'Số tầng', so_phong_ngu: 'Số phòng ngủ',
      so_phong_tam: 'Số phòng tắm', mat_tien_m: 'Mặt tiền', chieu_dai_m: 'Chiều dài', duong_vao_m: 'Độ rộng đường vào', log_dem_quan: 'Số tin đăng trong quận',
      log_dem_du_an: 'Quy mô dự án', 'loai_bds=Căn hộ': 'Là căn hộ', 'loai_bds=Đất': 'Là đất nền', 'loai_bds=Biệt thự/Liền kề': 'Là biệt thự, liền kề',
      'vi_tri=Ngõ/Hẻm': 'Nằm trong ngõ, hẻm', 'vi_tri=Mặt phố': 'Nằm ở mặt phố', thieu_mat_tien_m: 'Tin không ghi mặt tiền', thieu_so_phong_ngu: 'Tin không ghi số phòng ngủ',
      thieu_duong_vao_m: 'Tin không ghi đường vào', co_du_an: 'Thuộc dự án', thieu_quan: 'Không rõ quận' };
    const qt = Object.fromEntries(m.quan_trong.map(x => [TEN[x.dac_trung] ? `${TEN[x.dac_trung]} (${x.dac_trung})` : x.dac_trung, x.gia_tri]));
    cotNgang($('#dl-quan-trong'), qt, v => so(v, 3));
  }
}

function chuyenTrang(id) {
  $$('.dieu-huong [role="tab"]').forEach(t => t.setAttribute('aria-selected', String(t.id === id)));
  $$('[role="tabpanel"]').forEach(p => { p.hidden = p.getAttribute('aria-labelledby') !== id; });
  if (id === 'tab-du-lieu') veDuLieu().catch(err => { $('#dl-tieu-de').textContent = err.message; });
  if (id === 'tab-thi-truong') veThiTruong();
  try { history.replaceState(null, '', `#${id.replace('tab-', '')}`); } catch { }
}

async function khoiDong() {
  taoChonLoai($('#chon-loai'), 'loai', false, doiLoai);
  taoChonLoai($('#tt-loai'), 'tt-loai', true, veThiTruong);
  taoChip();
  $$('.buoc').forEach(b => b.addEventListener('click', e => {
    const nut = e.target.closest('button'); if (!nut) return;
    capNhatBuoc(b.dataset.id, trangThai.ketCau[b.dataset.id] + Number(nut.dataset.d)); veNha();
  }));
  const dt = $('#dien-tich'), thanh = $('#thanh-dien-tich');
  dt.addEventListener('input', () => { thanh.value = Math.min(500, dt.value || 10); veNha(); });
  thanh.addEventListener('input', () => { dt.value = thanh.value; veNha(); });
  $('#mat-tien').addEventListener('input', veNha);
  $('#form-dinh-gia').addEventListener('submit', guiDinhGia);
  $$('.dieu-huong [role="tab"]').forEach(t => t.addEventListener('click', () => chuyenTrang(t.id)));
  veNha(); veLichSu();
  try {
    danhMuc = await api('/api/danh-muc');
    const ds = danhMuc.tinh;
    datTuyChon($('#tinh'), ds, 'Chọn tỉnh'); $('#tinh').value = ds.includes('Hà Nội') ? 'Hà Nội' : ds[0];
    datTuyChon($('#tt-tinh'), ds, 'Chọn tỉnh'); $('#tt-tinh').value = $('#tinh').value;
    $('#tinh').addEventListener('change', capNhatQuan);
    $('#quan').addEventListener('change', capNhatPhuong);
    $('#tt-tinh').addEventListener('change', veThiTruong);
    capNhatQuan();
  } catch (err) {
    $('#loi').textContent = `Không tải được danh mục địa danh: ${err.message}`; $('#loi').hidden = false;
  }
  const dau = location.hash.replace('#', '');
  if (['thi-truong', 'du-lieu'].includes(dau)) chuyenTrang(`tab-${dau}`);
}
khoiDong();
