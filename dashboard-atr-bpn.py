import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import base64, io, os

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Proyeksi Anggaran ATR/BPN",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── LOGIN ───────────────────────────────────────────────────────────────────
USERS = {
    "admin": {"password": "atrbpn2025", "role": "keuangan"},
    "s1":    {"password": "s12025",     "role": "seksi", "seksi": "S1"},
    "s2":    {"password": "s22025",     "role": "seksi", "seksi": "S2"},
    "s3":    {"password": "s32025",     "role": "seksi", "seksi": "S3"},
    "s4":    {"password": "s42025",     "role": "seksi", "seksi": "S4"},
    "s5":    {"password": "s52025",     "role": "seksi", "seksi": "S5"},
    "s6":    {"password": "s62025",     "role": "seksi", "seksi": "S6"},
}

def show_login():
    st.markdown("""
    <style>
    .login-wrap {
        max-width: 420px; margin: 80px auto 0; background: white;
        border-radius: 20px; padding: 40px 36px;
        box-shadow: 0 8px 40px rgba(26,58,107,0.13);
    }
    .login-logo { text-align:center; margin-bottom:24px; }
    .login-title { font-size:22px; font-weight:800; color:#1a3a6b; text-align:center; margin-bottom:4px; }
    .login-sub { font-size:12px; color:#636e72; text-align:center; margin-bottom:28px; }
    </style>
    <div class="login-wrap">
      <div class="login-logo"><span style="font-size:56px">🏛️</span></div>
      <div class="login-title">ATR/BPN Surabaya I</div>
      <div class="login-sub">Sistem Proyeksi & Monitoring Anggaran</div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1,2,1])
    with col_c:
        st.markdown("<br>", unsafe_allow_html=True)
        username = st.text_input("👤 Username", placeholder="Masukkan username")
        password = st.text_input("🔒 Password", type="password", placeholder="Masukkan password")
        login_btn = st.button("🔑 Masuk", use_container_width=True, type="primary")

        if login_btn:
            if username in USERS and USERS[username]["password"] == password:
                user_info = USERS[username]
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = user_info["role"]
                st.session_state['seksi_akses'] = user_info.get("seksi", None)
                st.rerun()
            else:
                st.error("❌ Username atau password salah. Silakan coba lagi.")
                st.info("⚠️ Akses hanya untuk Admin Keuangan dan Admin Seksi yang terdaftar.")

        st.markdown("""
        <div style='text-align:center;font-size:11px;color:#b2bec3;margin-top:20px'>
        © 2026 Kantor ATR/BPN Surabaya I
        </div>
        """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'seksi_akses' not in st.session_state:
    st.session_state['seksi_akses'] = None

if not st.session_state['logged_in']:
    show_login()
    st.stop()

ROLE = st.session_state['role']
SEKSI_AKSES = st.session_state['seksi_akses']

# ─── KONSTANTA ───────────────────────────────────────────────────────────────
BULAN = ['Februari','Maret','April','Mei','Juni','Juli',
         'Agustus','September','Oktober','November','Desember']
SEKSI_LIST = ['S1','S2','S3','S4','S5','S6']
SEKSI_NAMA = {
    'S1': 'Survei & Pemetaan',
    'S2': 'Penetapan Hak & Pendaftaran',
    'S3': 'Penataan & Pemberdayaan',
    'S4': 'Pengadaan Tanah & Pengembangan',
    'S5': 'Pengendalian & Sengketa',
    'S6': 'Sub Bag Tata Usaha'
}
COLORS = ['#1a3a6b','#00b894','#e17055','#c8a84b','#9b59b6','#2e86de']
SEKSI_COLORS = dict(zip(SEKSI_LIST, COLORS))

# Koefisien regresi HARDCODE dari laporan SPSS (X=indeks bulan, Y=% non-kumulatif)
REGRESI = {
    'S1': {'a': 10.201, 'b': -0.331, 'mae': 2.53,  'risiko': 'Sedang'},
    'S2': {'a': 10.390, 'b': -0.350, 'mae': 0.44,  'risiko': 'Rendah'},
    'S3': {'a':  8.371, 'b': -0.279, 'mae': 4.99,  'risiko': 'Tinggi'},
    'S4': {'a': 10.974, 'b': -0.422, 'mae': 0.01,  'risiko': 'Tinggi'},
    'S5': {'a': 10.312, 'b': -0.324, 'mae': 0.03,  'risiko': 'Sedang'},
    'S6': {'a': 11.724, 'b': -0.446, 'mae': 0.01,  'risiko': 'Rendah'},
}

# Tren historis (% realisasi tahunan dari pagu)
TREN = {
    'S1': {2018:81.79,2019:81.07,2020:84.58,2021:96.08,2022:93.88,2023:93.88,2024:66.75,2025:98.25},
    'S2': {2018:85.00,2019:88.00,2020:86.41,2021:78.99,2022:88.88,2023:98.82,2024:99.94,2025:99.99},
    'S3': {2018:71.53,2019:71.09,2020:55.48,2021:24.34,2022:68.63,2023:95.49,2024:100.00,2025:98.74},
    'S4': {2018:98.00,2019:37.26,2020:100.00,2021:100.00,2022:99.95,2023:100.00,2024:100.00,2025:100.00},
    'S5': {2018:78.61,2019:75.71,2020:89.78,2021:99.81,2022:99.98,2023:99.94,2024:93.44,2025:99.25},
    'S6': {2018:96.60,2019:98.22,2020:98.29,2021:98.95,2022:98.90,2023:99.73,2024:99.39,2025:99.98},
}

# ─── LOAD DATA EXCEL ─────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    b64_path = os.path.join(os.path.dirname(__file__), 'data_b64.txt')
    with open(b64_path, 'r') as f:
        b64 = f.read().strip()
    xls_bytes = base64.b64decode(b64)
    df = pd.read_excel(io.BytesIO(xls_bytes), sheet_name='DATA GABUNGAN LENGKAP', header=2)
    df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
    df = df[df['Seksi'].isin(SEKSI_LIST)]
    df = df[df['Bulan'].isin(BULAN)]
    df['Tahun'] = df['Tahun'].astype(int)
    int_cols = ['Pagu PNBP (Rp)','Pagu RM PTSL (Rp)','Pagu RM Non-PTSL (Rp)',
                'Realisasi PNBP (Rp)','Realisasi RM PTSL (Rp)','Realisasi RM Non-PTSL (Rp)']
    for c in int_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
    df['TotalPagu'] = df['Pagu PNBP (Rp)'] + df['Pagu RM PTSL (Rp)'] + df['Pagu RM Non-PTSL (Rp)']
    df['TotalReal'] = df['Realisasi PNBP (Rp)'] + df['Realisasi RM PTSL (Rp)'] + df['Realisasi RM Non-PTSL (Rp)']
    return df

# ─── HELPER FUNCTIONS ────────────────────────────────────────────────────────
def get_pagu(df, seksi, tahun, bulan_idx=None):
    sub = df[(df['Seksi']==seksi) & (df['Tahun']==tahun)].copy()
    if sub.empty:
        return 0
    sub['_idx'] = sub['Bulan'].apply(lambda b: BULAN.index(b) if b in BULAN else -1)
    sub = sub[sub['_idx'] >= 0].sort_values('_idx')
    if bulan_idx is not None:
        sub = sub[sub['_idx'] <= bulan_idx]
        if sub.empty:
            return 0
    row = sub.iloc[-1]
    return int(row['Pagu PNBP (Rp)'] + row['Pagu RM PTSL (Rp)'] + row['Pagu RM Non-PTSL (Rp)'])

def get_pct_bulanan(df, seksi, tahun):
    pagu = get_pagu(df, seksi, tahun)
    if pagu == 0:
        return [0.0] * 11
    kum_rp = []
    for bln in BULAN:
        sub = df[(df['Seksi']==seksi) & (df['Tahun']==tahun) & (df['Bulan']==bln)]
        kum_rp.append(int(sub.iloc[0]['TotalReal']) if not sub.empty else None)
    for i in range(len(kum_rp)):
        if kum_rp[i] is None:
            kum_rp[i] = kum_rp[i-1] if i > 0 else 0
    hasil = []
    prev = 0
    for val in kum_rp:
        delta_rp = val - prev
        pct = round(delta_rp / pagu * 100, 4)
        pct = max(0.0, pct)
        pct = min(pct, 100.0)
        hasil.append(pct)
        prev = val
    return hasil

def get_kumulatif(pct):
    kum, total = [], 0
    for p in pct:
        total += p
        kum.append(round(total, 4))
    return kum

def get_delta(pct):
    delta = [pct[0]]
    for i in range(1, len(pct)):
        delta.append(round(pct[i] - pct[i-1], 4))
    return delta

def get_sisa(df, seksi, tahun, sampai_idx):
    pagu = get_pagu(df, seksi, tahun, bulan_idx=sampai_idx)
    total_real = 0
    for i in range(sampai_idx, -1, -1):
        bln = BULAN[i]
        sub = df[(df['Seksi']==seksi) & (df['Tahun']==tahun) & (df['Bulan']==bln)]
        if not sub.empty:
            total_real = int(sub.iloc[0]['TotalReal'])
            break
    total_real = min(total_real, pagu) if pagu > 0 else total_real
    sisa = max(0, pagu - total_real)
    pct_real = round(total_real / pagu * 100, 2) if pagu > 0 else 0.0
    pct_real = min(pct_real, 100.0)
    sisa_pct = round(100.0 - pct_real, 2)
    return {
        'total_pagu': pagu,
        'realisasi_rp': total_real,
        'sisa_rp': sisa,
        'realisasi_pct': pct_real,
        'sisa_pct': sisa_pct,
    }

def get_dashboard_summary(df, tahun):
    per_seksi = {}
    total_pagu = 0
    total_real = 0
    for s in SEKSI_LIST:
        pagu = get_pagu(df, s, tahun)
        sub = df[(df['Seksi']==s) & (df['Tahun']==tahun)].copy()
        sub['_bulan_idx'] = sub['Bulan'].apply(lambda b: BULAN.index(b) if b in BULAN else -1)
        sub = sub[sub['_bulan_idx'] >= 0].sort_values('_bulan_idx')
        real_rp = int(sub.iloc[-1]['TotalReal']) if not sub.empty else 0
        real_rp = min(real_rp, pagu) if pagu > 0 else real_rp
        pct = round(real_rp / pagu * 100, 2) if pagu > 0 else 0
        pct = min(pct, 100.0)
        per_seksi[s] = {
            'nama': SEKSI_NAMA[s],
            'pagu': pagu,
            'realisasi_rp': real_rp,
            'realisasi_pct': pct,
        }
        total_pagu += pagu
        total_real += real_rp
    pct_total = round(total_real / total_pagu * 100, 2) if total_pagu > 0 else 0
    return {
        'total_pagu': total_pagu,
        'total_realisasi': total_real,
        'pct_realisasi': pct_total,
        'sisa_pagu': total_pagu - total_real,
        'sisa_pct': round((total_pagu - total_real) / total_pagu * 100, 2) if total_pagu > 0 else 0,
        'per_seksi': per_seksi,
        'tahun': tahun,
    }

def badge_color(pct):
    if pct >= 80: return "🟢"
    elif pct >= 50: return "🟡"
    return "🔴"

def risiko_color(risiko):
    return {'Rendah':'#00b894','Sedang':'#fdcb6e','Tinggi':'#d63031'}.get(risiko,'#636e72')

# ─── REGRESI ─────────────────────────────────────────────────────────────────
@st.cache_data
def compute_all_regresi(_df):
    """
    Tahap 1: Koefisien a1, b1 HARDCODE dari laporan SPSS.
             Proyeksi 2026 = substitusi X=1..11 ke persamaan SPSS.
    Tahap 2: Pool data aktual 2018-2025 + proj2026, fit ulang otomatis.
             Proyeksi 2027 = substitusi X=1..11 ke persamaan Tahap 2.
    """
    tahun_aktual = list(range(2018, 2026))

    def regresi_ols(x_vals, y_vals):
        x = np.array(x_vals, dtype=float)
        y = np.array(y_vals, dtype=float)
        n = len(x)
        if n < 2:
            return 0.0, 0.0, 0.0, 0.0, []
        b = (n*np.sum(x*y) - np.sum(x)*np.sum(y)) / (n*np.sum(x**2) - np.sum(x)**2)
        a = (np.sum(y) - b*np.sum(x)) / n
        y_pred = a + b * x
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r2 = float(1 - ss_res/ss_tot) if ss_tot != 0 else 0.0
        mae = float(np.mean(np.abs(y - y_pred)))
        return round(a,4), round(b,4), round(r2,4), round(mae,4), y_pred.tolist()

    hasil = {}
    for s in SEKSI_LIST:
        # Kumpulkan data aktual (untuk scatter plot & Tahap 2)
        x_gabung, y_gabung = [], []
        for tahun in tahun_aktual:
            pct_list = get_pct_bulanan(_df, s, tahun)
            for bi, pct in enumerate(pct_list):
                x_gabung.append(bi + 1)
                y_gabung.append(pct)

        # ── TAHAP 1: HARDCODE dari laporan SPSS ──────────────────────────────
        a1 = REGRESI[s]['a']
        b1 = REGRESI[s]['b']
        mae1 = REGRESI[s]['mae']
        y_pred_gabung = [round(a1 + b1*x, 4) for x in x_gabung]
        ss_res1 = sum((y - yp)**2 for y, yp in zip(y_gabung, y_pred_gabung))
        ss_tot1 = sum((y - float(np.mean(y_gabung)))**2 for y in y_gabung)
        r2_1 = round(1 - ss_res1/ss_tot1, 4) if ss_tot1 != 0 else 0.0

        # Proyeksi 2026: substitusi X=1..11 ke persamaan SPSS
        proj2026 = [max(0.0, round(a1 + b1*x, 4)) for x in range(1, 12)]

        # ── TAHAP 2: fit ulang 2018-2025 + proj2026 ──────────────────────────
        x_gabung2 = x_gabung.copy()
        y_gabung2 = y_gabung.copy()
        for bi, pct in enumerate(proj2026):
            x_gabung2.append(bi + 1)
            y_gabung2.append(pct)

        a2, b2, r2_2, mae2, y_pred_gabung2 = regresi_ols(x_gabung2, y_gabung2)

        # Proyeksi 2027: substitusi X=1..11 ke persamaan Tahap 2
        proj2027 = [max(0.0, round(a2 + b2*x, 4)) for x in range(1, 12)]

        hasil[s] = {
            'a1': a1, 'b1': b1, 'r2_1': r2_1, 'mae1': mae1,
            'x_gabung': x_gabung, 'y_gabung': y_gabung, 'y_pred_gabung': y_pred_gabung,
            'proj2026': proj2026,
            'a2': a2, 'b2': b2, 'r2_2': r2_2, 'mae2': mae2,
            'x_gabung2': x_gabung2, 'y_gabung2': y_gabung2, 'y_pred_gabung2': y_pred_gabung2,
            'proj2027': proj2027,
        }
    return hasil

# ─── LOAD ────────────────────────────────────────────────────────────────────
df = load_data()
regresi_data = compute_all_regresi(df)
PROYEKSI_2026 = {s: regresi_data[s]['proj2026'] for s in SEKSI_LIST}
PROYEKSI_2027 = {s: regresi_data[s]['proj2027'] for s in SEKSI_LIST}

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
  --primary: #1a3a6b; --secondary: #c8a84b; --accent: #2e86de;
  --bg: #f0f4f8; --success: #00b894; --danger: #d63031;
  --warning: #fdcb6e; --muted: #636e72;
}
[data-testid="stSidebar"] { background: var(--primary) !important; }
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
[data-testid="stSidebar"] .stSelectbox label { color: rgba(255,255,255,0.6) !important; font-size:11px !important; }
[data-testid="stSidebar"] .stButton button {
    background-color: rgba(255,255,255,0.15) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.35) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background-color: rgba(255,255,255,0.28) !important;
    border-color: rgba(255,255,255,0.6) !important;
}
.stat-card {
  border-radius: 16px; padding: 22px 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  color: white; position: relative; overflow: hidden; transition: transform .2s;
}
.stat-card:hover { transform: translateY(-3px); }
.stat-icon { font-size: 28px; margin-bottom: 10px; }
.stat-value { font-size: 22px; font-weight: 800; }
.stat-label { font-size: 12px; opacity: 0.8; margin-top: 2px; }
.stat-sub { font-size: 11px; opacity: 0.7; margin-top: 6px; }
.chart-card {
  background: white; border-radius: 16px; padding: 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06); margin-bottom: 16px;
}
.chart-title {
  font-weight: 700; color: var(--primary); font-size: 14px;
  margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
}
.badge-success { background:#d4edda; color:#155724; padding:3px 10px; border-radius:50px; font-size:11px; font-weight:700; }
.badge-warning { background:#fff3cd; color:#856404; padding:3px 10px; border-radius:50px; font-size:11px; font-weight:700; }
.badge-danger  { background:#f8d7da; color:#721c24; padding:3px 10px; border-radius:50px; font-size:11px; font-weight:700; }
.stMetric { background:white; border-radius:12px; padding:16px !important; box-shadow:0 2px 12px rgba(0,0,0,0.06); }
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:16px 0 12px; border-bottom:1px solid rgba(255,255,255,0.15); margin-bottom:8px'>
      <div style='font-size:42px'>🏛️</div>
      <div style='font-weight:700; font-size:13px; color:#c8a84b; margin-top:6px'>ATR/BPN SURABAYA I</div>
      <div style='font-size:11px; opacity:0.6'>Sistem Proyeksi Anggaran</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style='font-size:11px;color:rgba(255,255,255,0.5);text-align:center;margin-bottom:6px'>
    👤 Login sebagai: <strong style='color:#c8a84b'>{st.session_state.get('username','')}</strong>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-size:10px;text-transform:uppercase;letter-spacing:1.5px;opacity:0.45;padding:12px 0 4px;font-weight:600'>Menu Utama</div>", unsafe_allow_html=True)

    if ROLE == 'keuangan':
        menu_options = ["🏠 Dashboard", "📊 Monitoring Bulanan", "📈 Analisis & Proyeksi", "📐 Regresi Linear"]
    else:
        menu_options = ["🏠 Dashboard", "📊 Monitoring Bulanan"]

    halaman = st.radio("", menu_options, label_visibility="collapsed")

    if ROLE == 'seksi':
        st.markdown(f"""
        <div style='background:rgba(200,168,75,0.15);border-radius:8px;padding:8px 12px;
                    margin-top:8px;font-size:11px;color:#c8a84b;text-align:center'>
        🔒 Akses: <b>{SEKSI_AKSES} — {SEKSI_NAMA[SEKSI_AKSES]}</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        for key in ['logged_in','username','role','seksi_akses']:
            st.session_state[key] = False if key == 'logged_in' else None
        st.rerun()
    st.markdown("<div style='font-size:11px;opacity:0.5;text-align:center;margin-top:8px'>© 2026 ATR/BPN Surabaya I</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HALAMAN 1 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if halaman == "🏠 Dashboard":
    st.markdown("<h4 style='color:#1a3a6b;font-weight:800;margin-bottom:24px'>🏠 Dashboard — Ringkasan Anggaran</h4>", unsafe_allow_html=True)

    tahun_list_db = sorted(df['Tahun'].unique().tolist(), reverse=True)
    tahun_ref = st.selectbox("📅 Pilih Tahun", tahun_list_db, index=0, key='db_tahun')
    summary = get_dashboard_summary(df, tahun_ref)

    if ROLE == 'seksi':
        st.markdown(f"""
        <div style='background:#fff3cd;border-radius:10px;padding:12px 18px;margin-bottom:16px;
                    border-left:4px solid #c8a84b;font-size:13px'>
        🔒 Anda login sebagai <b>Admin {SEKSI_AKSES} — {SEKSI_NAMA[SEKSI_AKSES]}</b>.
        Dashboard hanya menampilkan data seksi Anda.
        </div>
        """, unsafe_allow_html=True)

    tampil_seksi = SEKSI_LIST if ROLE == 'keuangan' else [SEKSI_AKSES]

    if ROLE == 'keuangan':
        c1,c2,c3,c4 = st.columns(4)
        cards = [
            (c1,"💼",f"Rp {summary['total_pagu']:,.0f}",f"Total Pagu {tahun_ref}","6 Seksi","linear-gradient(135deg,#1a3a6b,#2e6da4)"),
            (c2,"✅",f"Rp {summary['total_realisasi']:,.0f}","Total Realisasi",f"{summary['pct_realisasi']}% tercapai","linear-gradient(135deg,#00b894,#00cec9)"),
            (c3,"⏳",f"Rp {summary['sisa_pagu']:,.0f}","Sisa Pagu",f"{summary['sisa_pct']}% belum terserap","linear-gradient(135deg,#e17055,#d63031)"),
            (c4,"📊",f"{summary['pct_realisasi']}%","% Realisasi Keseluruhan",f"Tahun {tahun_ref}","linear-gradient(135deg,#c8a84b,#f9ca24)"),
        ]
        for col, icon, val, lbl, sub, grad in cards:
            col.markdown(f"""
            <div class="stat-card" style="background:{grad}">
              <div class="stat-icon">{icon}</div>
              <div class="stat-value">{val}</div>
              <div class="stat-label">{lbl}</div>
              <div class="stat-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        d = summary['per_seksi'][SEKSI_AKSES]
        c1,c2,c3 = st.columns(3)
        cards_s = [
            (c1,"💼",f"Rp {d['pagu']:,.0f}",f"Pagu {SEKSI_AKSES}",f"Tahun {tahun_ref}","linear-gradient(135deg,#1a3a6b,#2e6da4)"),
            (c2,"✅",f"Rp {d['realisasi_rp']:,.0f}","Realisasi",f"{d['realisasi_pct']}% tercapai","linear-gradient(135deg,#00b894,#00cec9)"),
            (c3,"⏳",f"Rp {d['pagu']-d['realisasi_rp']:,.0f}","Sisa Pagu",f"{round(100-d['realisasi_pct'],2)}% belum terserap","linear-gradient(135deg,#e17055,#d63031)"),
        ]
        for col, icon, val, lbl, sub, grad in cards_s:
            col.markdown(f"""
            <div class="stat-card" style="background:{grad}">
              <div class="stat-icon">{icon}</div>
              <div class="stat-value">{val}</div>
              <div class="stat-label">{lbl}</div>
              <div class="stat-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([4,6])
    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">🎯 Capaian Realisasi</div>', unsafe_allow_html=True)
        pct_gauge = summary['pct_realisasi'] if ROLE == 'keuangan' else summary['per_seksi'][SEKSI_AKSES]['realisasi_pct']
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=pct_gauge,
            delta={'reference':85,'valueformat':'.1f'},
            number={'suffix':'%','font':{'size':40,'color':'#1a3a6b'}},
            gauge={
                'axis':{'range':[0,100],'tickcolor':'#636e72'},
                'bar':{'color':'#1a3a6b','thickness':0.25},
                'steps':[
                    {'range':[0,50],'color':'#ffeaea'},
                    {'range':[50,75],'color':'#fff3cd'},
                    {'range':[75,100],'color':'#d4edda'},
                ],
                'threshold':{'line':{'color':'#c8a84b','width':4},'thickness':0.75,'value':85}
            }
        ))
        fig_gauge.update_layout(margin=dict(t=20,b=20,l=20,r=20),
                                paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',height=280)
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">📊 Realisasi per Seksi</div>', unsafe_allow_html=True)
        seksi_names = [summary['per_seksi'][s]['nama'] for s in tampil_seksi]
        seksi_pcts  = [summary['per_seksi'][s]['realisasi_pct'] for s in tampil_seksi]
        bar_colors  = ['#00b894' if v>=80 else '#fdcb6e' if v>=50 else '#d63031' for v in seksi_pcts]
        fig_bar = go.Figure(go.Bar(
            x=seksi_names, y=seksi_pcts,
            marker=dict(color=bar_colors),
            text=[f"{v}%" for v in seksi_pcts], textposition='outside',
        ))
        fig_bar.add_shape(type='line',x0=-0.5,x1=len(tampil_seksi)-0.5,y0=85,y1=85,
                          line=dict(color='#c8a84b',width=2,dash='dot'))
        fig_bar.update_layout(
            margin=dict(t=20,b=60,l=40,r=20),
            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(range=[0,115],title='%',gridcolor='#f0f0f0'),
            xaxis=dict(tickangle=-15,tickfont=dict(size=10)),
            height=280,font=dict(family='Segoe UI',color='#2d3436')
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-title">📋 Ringkasan Anggaran per Seksi — {tahun_ref}</div>', unsafe_allow_html=True)
    rows = []
    for s in tampil_seksi:
        d = summary['per_seksi'][s]
        pct_v = d['realisasi_pct']
        badge = "🟢 " if pct_v>=80 else "🟡 " if pct_v>=50 else "🔴 "
        rows.append({
            'Seksi': f"{s} — {d['nama']}",
            'Total Pagu (Rp)': f"Rp {d['pagu']:,.0f}",
            'Realisasi (Rp)': f"Rp {d['realisasi_rp']:,.0f}",
            '% Realisasi': f"{badge}{pct_v}%",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if ROLE == 'keuangan':
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">🚀 Akses Cepat</div>', unsafe_allow_html=True)
        qa1, qa2 = st.columns(2)
        with qa1:
            st.info("📊 **Monitoring Bulanan** — Pantau sisa pagu & pertumbuhan per seksi.")
        with qa2:
            st.info("📈 **Analisis & Proyeksi** — Lihat proyeksi 2026–2027 & analisis risiko.")
        st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HALAMAN 2 — MONITORING BULANAN
# ═══════════════════════════════════════════════════════════════════════════════
elif halaman == "📊 Monitoring Bulanan":
    st.markdown("<h4 style='color:#1a3a6b;font-weight:800;margin-bottom:8px'>📊 Monitoring Realisasi Bulanan</h4>", unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns([1,1,4])
    with fc1:
        tahun_sel = st.selectbox("Tahun", list(range(2018,2026)), index=7)
    with fc2:
        bulan_sel = st.selectbox("s/d Bulan", BULAN, index=10)
    bulan_idx = BULAN.index(bulan_sel)

    st.markdown("<br>", unsafe_allow_html=True)

    tampil_seksi_mon = SEKSI_LIST if ROLE == 'keuangan' else [SEKSI_AKSES]

    cols = st.columns(min(3, len(tampil_seksi_mon)))
    card_colors = ['#2196F3','#4CAF50','#FF9800','#E91E63','#9C27B0','#00BCD4']
    hasil_monitoring = {}

    for s in SEKSI_LIST:
        sisa = get_sisa(df, s, tahun_sel, bulan_idx)
        pct  = get_pct_bulanan(df, s, tahun_sel)
        hasil_monitoring[s] = {
            'nama': SEKSI_NAMA[s],
            'sisa': sisa,
            'pct_bulanan': pct,
            'kumulatif': get_kumulatif(pct),
            'delta': get_delta(pct),
        }

    for i, s in enumerate(tampil_seksi_mon):
        d = hasil_monitoring[s]
        c = card_colors[SEKSI_LIST.index(s)]
        sisa = d['sisa']
        pct_v = sisa['realisasi_pct']
        badge_cls = "badge-success" if pct_v>=80 else "badge-warning" if pct_v>=50 else "badge-danger"
        pct_bar = min(pct_v, 100)
        col_idx = i % len(cols)
        with cols[col_idx]:
            st.markdown(f"""
            <div style='background:white;border-radius:14px;padding:18px 20px;
                        box-shadow:0 4px 14px rgba(0,0,0,0.06);
                        border-top:4px solid {c};margin-bottom:16px'>
              <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                <div>
                  <div style='font-weight:800;font-size:14px;color:#1a3a6b'>{s} — {d['nama']}</div>
                  <div style='font-size:11px;color:#636e72;margin-top:2px'>
                    Pagu: <strong>Rp {sisa['total_pagu']:,.0f}</strong>
                  </div>
                </div>
                <span class="{badge_cls}">{pct_v}% terserap</span>
              </div>
              <div style='background:#f0f4f8;border-radius:50px;height:8px;overflow:hidden;margin:12px 0 8px'>
                <div style='width:{pct_bar}%;height:100%;background:{c};border-radius:50px'></div>
              </div>
              <div style='display:flex;justify-content:space-between'>
                <div>
                  <div style='font-size:11px;color:#636e72'>Realisasi s/d {bulan_sel}</div>
                  <div style='font-size:13px;font-weight:700;color:#00b894'>Rp {sisa['realisasi_rp']:,.0f}</div>
                </div>
                <div style='text-align:right'>
                  <div style='font-size:11px;color:#636e72'>Sisa Pagu</div>
                  <div style='font-size:13px;font-weight:700;color:#d63031'>Rp {sisa['sisa_rp']:,.0f}</div>
                  <div style='font-size:11px;color:#d63031'>{sisa['sisa_pct']}% sisa</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">📈 Kumulatif % Realisasi per Bulan</div>', unsafe_allow_html=True)
        sel_kum = st.selectbox("Pilih Seksi", tampil_seksi_mon, key='kum_seksi',
                               format_func=lambda x: f"{x} — {SEKSI_NAMA[x]}")
        d = hasil_monitoring[sel_kum]
        fig_kum = go.Figure()
        fig_kum.add_trace(go.Scatter(
            x=BULAN, y=d['kumulatif'], mode='lines+markers',
            fill='tozeroy', fillcolor='rgba(46,134,222,0.1)',
            line=dict(color='#2e86de',width=2.5),
            marker=dict(size=7,color='#2e86de'),
        ))
        fig_kum.update_layout(
            margin=dict(t=10,b=60,l=45,r=10),
            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fafafa',
            xaxis=dict(tickangle=-30,gridcolor='#f0f0f0'),
            yaxis=dict(title='%',gridcolor='#f0f0f0'),
            height=300,font=dict(family='Segoe UI',size=12)
        )
        st.plotly_chart(fig_kum, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">🌊 Pertumbuhan Serapan per Bulan</div>', unsafe_allow_html=True)
        sel_delta = st.selectbox("Pilih Seksi", tampil_seksi_mon, key='delta_seksi',
                                 format_func=lambda x: f"{x} — {SEKSI_NAMA[x]}")
        d2 = hasil_monitoring[sel_delta]
        delta_colors = ['#00b894' if v>=0 else '#d63031' for v in d2['delta']]
        fig_delta = go.Figure()
        fig_delta.add_trace(go.Bar(
            x=BULAN, y=d2['delta'],
            marker=dict(color=delta_colors),
        ))
        fig_delta.update_layout(
            margin=dict(t=10,b=60,l=45,r=10),
            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fafafa',
            xaxis=dict(tickangle=-30,gridcolor='#f0f0f0'),
            yaxis=dict(title='%',gridcolor='#f0f0f0',zeroline=True,zerolinecolor='#ccc'),
            height=300,font=dict(family='Segoe UI',size=12)
        )
        st.plotly_chart(fig_delta, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">📋 Tabel % Realisasi Bulanan per Seksi</div>', unsafe_allow_html=True)
    rows = []
    for s in tampil_seksi_mon:
        d = hasil_monitoring[s]
        row = {'Seksi': s}
        for j, b in enumerate(BULAN):
            v = d['pct_bulanan'][j]
            row[b[:3]] = f"{v:.2f}%" if v > 0 else "—"
        row['Kumulatif'] = f"{d['kumulatif'][-1]}%"
        sp = d['sisa']['sisa_pct']
        row['Sisa (%)'] = f"{'🟢' if sp<=20 else '🟡' if sp<=50 else '🔴'} {sp}%"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HALAMAN 3 — ANALISIS & PROYEKSI
# ═══════════════════════════════════════════════════════════════════════════════
elif halaman == "📈 Analisis & Proyeksi":
    st.markdown("<h4 style='color:#1a3a6b;font-weight:800;margin-bottom:8px'>📈 Analisis & Proyeksi Realisasi Anggaran</h4>", unsafe_allow_html=True)

    tab_proj, tab_tren, tab_risiko = st.tabs(["📅 Proyeksi 2026–2027","📉 Tren 2018–2027","⚠️ Risiko & Toleransi"])

    with tab_proj:
        st.markdown("### 📅 Proyeksi Realisasi Bulanan per Seksi")
        tahun_proj = st.radio("Pilih Tahun Proyeksi", ["2026","2027"], horizontal=True)
        proj_data  = PROYEKSI_2026 if tahun_proj == "2026" else PROYEKSI_2027

        fig_proj = go.Figure()
        for i, s in enumerate(SEKSI_LIST):
            fig_proj.add_trace(go.Bar(
                name=s, x=BULAN, y=proj_data[s],
                marker=dict(color=COLORS[i]),
                hovertemplate=f'<b>{s}</b><br>%{{x}}: %{{y:.2f}}%<extra></extra>'
            ))
        fig_proj.update_layout(
            barmode='group',
            margin=dict(t=20,b=80,l=50,r=20),
            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fafafa',
            yaxis=dict(title='% Realisasi',gridcolor='#f0f0f0'),
            xaxis=dict(tickangle=-20),
            legend=dict(orientation='h',y=-0.3),
            height=420,font=dict(family='Segoe UI')
        )
        st.plotly_chart(fig_proj, use_container_width=True, config={'displayModeBar':False})

        # Tabel perbandingan 2026 vs 2027 side by side
        st.markdown("#### 📋 Perbandingan Proyeksi 2026 vs 2027 per Seksi")
        rows_cmp = []
        for s in SEKSI_LIST:
            row = {'Seksi': s, 'Nama': SEKSI_NAMA[s]}
            for j, b in enumerate(BULAN):
                p26 = PROYEKSI_2026[s][j]
                p27 = PROYEKSI_2027[s][j]
                selisih = round(p27 - p26, 4)
                arah = "↑" if selisih > 0 else ("↓" if selisih < 0 else "=")
                row[b[:3]] = f"{p26} → {p27} {arah}"
            row['Total 2026'] = round(sum(PROYEKSI_2026[s]), 2)
            row['Total 2027'] = round(sum(PROYEKSI_2027[s]), 2)
            selisih_total = round(sum(PROYEKSI_2027[s]) - sum(PROYEKSI_2026[s]), 2)
            row['Selisih'] = f"{'↑ +' if selisih_total>=0 else '↓ '}{selisih_total}%"
            rows_cmp.append(row)
        st.dataframe(pd.DataFrame(rows_cmp), use_container_width=True, hide_index=True)

        # Tabel terpisah per tahun
        c1, c2 = st.columns(2)
        for col, tahun_t, pdata in [(c1,"2026",PROYEKSI_2026),(c2,"2027",PROYEKSI_2027)]:
            with col:
                st.markdown(f"**📅 Proyeksi {tahun_t} per Seksi (%)**")
                rows = []
                for s in SEKSI_LIST:
                    row = {'Seksi': s}
                    for j, b in enumerate(BULAN):
                        row[b[:3]] = pdata[s][j]
                    row['Total'] = round(sum(pdata[s]),2)
                    rows.append(row)
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab_tren:
        st.markdown("### 📉 Tren Realisasi Anggaran Tahunan per Seksi (2018–2027)")
        tahun_all = list(range(2018, 2028))
        fig_tren = go.Figure()
        for i, s in enumerate(SEKSI_LIST):
            vals = []
            for t in tahun_all:
                if t < 2026:
                    vals.append(TREN[s].get(t, None))
                elif t == 2026:
                    vals.append(round(sum(PROYEKSI_2026[s]),2))
                else:
                    vals.append(round(sum(PROYEKSI_2027[s]),2))
            fig_tren.add_trace(go.Scatter(
                name=f"{s} — {SEKSI_NAMA[s][:18]}",
                x=tahun_all, y=vals, mode='lines+markers',
                line=dict(color=COLORS[i],width=2.5),
                marker=dict(size=8),
            ))
        fig_tren.add_vline(x=2025.5,line_dash="dash",line_color="#636e72",line_width=1.5)
        fig_tren.add_annotation(x=2025.5,y=108,text="← Aktual | Proyeksi →",
                                showarrow=False,font=dict(color='#636e72',size=11))
        fig_tren.update_layout(
            margin=dict(t=20,b=60,l=50,r=20),
            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fafafa',
            xaxis=dict(title='Tahun',gridcolor='#f0f0f0'),
            yaxis=dict(title='Total % Realisasi',gridcolor='#f0f0f0',range=[0,115]),
            legend=dict(orientation='h',y=-0.25),
            height=420,font=dict(family='Segoe UI')
        )
        st.plotly_chart(fig_tren, use_container_width=True, config={'displayModeBar':False})

        st.markdown("**📋 Data Tren Realisasi Tahunan (%)**")
        rows = []
        for s in SEKSI_LIST:
            row = {'Seksi': f"{s} — {SEKSI_NAMA[s]}"}
            for t in range(2018,2026):
                row[str(t)] = TREN[s].get(t,0)
            row['2026 (P)'] = round(sum(PROYEKSI_2026[s]),2)
            row['2027 (P)'] = round(sum(PROYEKSI_2027[s]),2)
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab_risiko:
        st.markdown("### ⚠️ Klasifikasi Risiko & Toleransi Deviasi")
        risiko_clr = {'Rendah':'#00b894','Sedang':'#fdcb6e','Tinggi':'#d63031'}
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🔴 Klasifikasi Risiko per Seksi (berdasarkan CV)**")
            mae_vals  = [REGRESI[s]['mae'] for s in SEKSI_LIST]
            risiko_vals = [REGRESI[s]['risiko'] for s in SEKSI_LIST]
            bubble_colors = [risiko_clr[REGRESI[s]['risiko']] for s in SEKSI_LIST]
            fig_risk = go.Figure(go.Scatter(
                x=SEKSI_LIST, y=mae_vals,
                mode='markers+text', text=risiko_vals, textposition='top center',
                marker=dict(size=[v*12+20 for v in mae_vals],
                            color=bubble_colors,line=dict(width=2,color='#fff')),
            ))
            fig_risk.add_hline(y=1,line_dash='dot',line_color='#fdcb6e',line_width=2)
            fig_risk.add_hline(y=3,line_dash='dot',line_color='#d63031',line_width=2)
            fig_risk.update_layout(
                margin=dict(t=20,b=40,l=50,r=20),
                paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fafafa',
                yaxis=dict(title='MAE (%)',gridcolor='#f0f0f0'),
                height=360,font=dict(family='Segoe UI')
            )
            st.plotly_chart(fig_risk, use_container_width=True, config={'displayModeBar':False})
        with c2:
            st.markdown("**⚖️ MAE per Seksi**")
            fig_mae = go.Figure(go.Bar(
                orientation='h',
                x=mae_vals,
                y=[f"{s} — {SEKSI_NAMA[s][:15]}" for s in SEKSI_LIST],
                marker=dict(color=bubble_colors),
                text=[f"{v}%" for v in mae_vals],textposition='outside',
            ))
            fig_mae.update_layout(
                margin=dict(t=20,b=40,l=200,r=60),
                paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fafafa',
                xaxis=dict(title='MAE (%)',gridcolor='#f0f0f0'),
                height=360,font=dict(family='Segoe UI')
            )
            st.plotly_chart(fig_mae, use_container_width=True, config={'displayModeBar':False})

        st.markdown("**📏 Tabel Toleransi Deviasi ±5% — Proyeksi 2026**")
        rows = []
        for s in SEKSI_LIST:
            for j, b in enumerate(BULAN[:6]):
                proj = PROYEKSI_2026[s][j]
                rows.append({
                    'Seksi': f"{s} — {SEKSI_NAMA[s]}",
                    'Bulan': b,
                    'Proyeksi (%)': proj,
                    'Batas Bawah (-5%)': round(proj-5,2),
                    'Batas Atas (+5%)': round(proj+5,2),
                    'Keterangan': f"Jika < {round(proj-5,2)}% → perlu tindak lanjut"
                })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("**📐 Ringkasan Hasil Regresi per Seksi (dari laporan SPSS)**")
        rows_reg = []
        for s in SEKSI_LIST:
            r = REGRESI[s]
            rows_reg.append({
                'Seksi': s, 'Nama': SEKSI_NAMA[s],
                'a (Intersep)': r['a'], 'b (Koefisien)': r['b'],
                'Persamaan': f"Ŷ = {r['a']} + ({r['b']})·X",
                'MAE (%)': r['mae'],
                'Risiko (CV)': r['risiko']
            })
        st.dataframe(pd.DataFrame(rows_reg), use_container_width=True, hide_index=True)

        st.markdown("""
        <div style='background:#f8f9fa;border-radius:10px;padding:16px 20px;margin-top:8px'>
        <b>Keterangan:</b><br>
        X = indeks bulan (1=Feb, 2=Mar, …, 11=Des) &nbsp;|&nbsp;
        Y = % realisasi non-kumulatif per bulan<br>
        Klasifikasi risiko berdasarkan <b>Koefisien Variasi (CV)</b> sesuai laporan SPSS:<br>
        <span style='color:#d63031'>🔴 S3 & S4 = Tinggi</span> &nbsp;|&nbsp;
        <span style='color:#fdcb6e'>🟡 S1 & S5 = Sedang</span> &nbsp;|&nbsp;
        <span style='color:#00b894'>🟢 S2 & S6 = Rendah</span>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HALAMAN 4 — REGRESI LINEAR
# ═══════════════════════════════════════════════════════════════════════════════
elif halaman == "📐 Regresi Linear":
    st.markdown("<h4 style='color:#1a3a6b;font-weight:800;margin-bottom:4px'>📐 Analisis Regresi Linear</h4>", unsafe_allow_html=True)

    with st.expander("📖 Tentang Metode Regresi Linear", expanded=False):
        st.markdown("""
        <div style='background:#f0f4f8;border-radius:12px;padding:20px 24px;line-height:1.8'>
        <h5 style='color:#1a3a6b;margin-bottom:12px'>Apa itu Regresi Linear Sederhana?</h5>
        <p>Regresi linear sederhana memodelkan hubungan antara variabel bebas (<b>X</b>) dan variabel terikat (<b>Y</b>).</p>
        <div style='background:white;border-radius:8px;padding:14px 18px;margin:12px 0;border-left:4px solid #1a3a6b'>
        <b>Persamaan:</b> <span style='font-size:16px;font-family:monospace'><b>Ŷ = a + b·X</b></span><br><br>
        <b>Dalam konteks laporan ini:</b><br>
        • <b>X</b> = indeks bulan (1=Feb, 2=Mar, …, 11=Des)<br>
        • <b>Y</b> = % realisasi anggaran non-kumulatif per bulan<br>
        • Data digabung dari 2018–2025 → <b>88 observasi per seksi</b><br>
        • Setiap seksi menghasilkan <b>1 persamaan</b> (bukan per bulan)
        </div>
        <div style='background:white;border-radius:8px;padding:14px 18px;margin:12px 0;border-left:4px solid #00b894'>
        <b>Alur Proyeksi Dua Tahap:</b><br>
        <b>Tahap 1:</b> Data 2018–2025 digabung → fit (dari laporan SPSS) → substitusi X=1..11 → <b>Proyeksi 2026</b><br>
        <b>Tahap 2:</b> Data 2018–2025 + Proyeksi 2026 digabung → fit ulang → substitusi X=1..11 → <b>Proyeksi 2027</b>
        </div>
        </div>
        """, unsafe_allow_html=True)

    tab_r1, tab_r2, tab_r3, tab_r4 = st.tabs([
        "📊 Tahap 1 — Proyeksi 2026",
        "📊 Tahap 2 — Proyeksi 2027",
        "📋 Ringkasan & Akurasi",
        "🧮 Kalkulator Data Baru"
    ])

    # ── TAB 1 ──
    with tab_r1:
        st.markdown("""
        <div style='background:#e8f4fd;border-radius:10px;padding:14px 18px;margin-bottom:16px;border-left:4px solid #1a3a6b'>
        <b>📌 Regresi Tahap 1</b> — Data aktual 2018–2025 digabung. <b>X = indeks bulan</b> (1=Feb…11=Des),
        <b>Y = % realisasi non-kumulatif</b>. 1 persamaan per seksi (dari laporan SPSS). Proyeksi 2026 = substitusi X=1..11.
        </div>
        """, unsafe_allow_html=True)

        col_sel1, _ = st.columns([1,2])
        with col_sel1:
            sel_s1 = st.selectbox("Pilih Seksi", SEKSI_LIST,
                                   format_func=lambda x: f"{x} — {SEKSI_NAMA[x]}", key='reg_s1')

        rd1 = regresi_data[sel_s1]
        a1v, b1v, r2_1v, mae1v = rd1['a1'], rd1['b1'], rd1['r2_1'], rd1['mae1']
        proj26 = rd1['proj2026']

        col_eq1,col_eq2,col_eq3,col_eq4 = st.columns(4)
        for col, label, val, color in [
            (col_eq1,"Konstanta (a)",f"{a1v}","#1a3a6b"),
            (col_eq2,"Koefisien (b)",f"{b1v}","#e17055"),
            (col_eq3,"R²",f"{r2_1v}","#00b894"),
            (col_eq4,"MAE (%)",f"{mae1v:.4f}","#c8a84b"),
        ]:
            col.markdown(f"""
            <div style='background:white;border-radius:12px;padding:16px 18px;
                        box-shadow:0 2px 12px rgba(0,0,0,0.07);border-top:3px solid {color};text-align:center'>
              <div style='font-size:11px;color:#636e72;margin-bottom:4px'>{label}</div>
              <div style='font-size:20px;font-weight:800;color:{color}'>{val}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background:#1a3a6b;color:white;border-radius:10px;padding:12px 20px;margin:16px 0;text-align:center;font-size:15px'>
        <b>Persamaan (SPSS):</b> &nbsp; Ŷ = {a1v} + ({b1v}) · X &nbsp;|&nbsp;
        X = 1 (Feb) … 11 (Des) &nbsp;|&nbsp; n = {len(rd1['x_gabung'])} observasi
        </div>
        """, unsafe_allow_html=True)

        fig_r1 = go.Figure()
        fig_r1.add_trace(go.Scatter(
            x=rd1['x_gabung'], y=rd1['y_gabung'], mode='markers',
            name='Data Aktual (2018–2025)',
            marker=dict(size=6,color='#1a3a6b',opacity=0.5),
        ))
        x_line = list(range(1,12))
        y_line = [round(a1v + b1v*x, 4) for x in x_line]
        fig_r1.add_trace(go.Scatter(
            x=x_line, y=y_line, mode='lines',
            name='Garis Regresi (SPSS)',
            line=dict(color='#e17055',width=2.5)
        ))
        fig_r1.add_trace(go.Scatter(
            x=x_line, y=proj26, mode='markers+lines',
            name='Proyeksi 2026',
            marker=dict(size=9,color='#c8a84b',symbol='star'),
            line=dict(color='#c8a84b',dash='dot')
        ))
        fig_r1.update_layout(
            title=f"Sebaran Data & Regresi Tahap 1 — {sel_s1} ({SEKSI_NAMA[sel_s1]})",
            xaxis=dict(title='Indeks Bulan (1=Feb … 11=Des)',gridcolor='#f0f0f0',
                       tickvals=list(range(1,12)),ticktext=BULAN),
            yaxis=dict(title='% Realisasi Non-Kumulatif',gridcolor='#f0f0f0'),
            legend=dict(orientation='h',y=-0.3),
            margin=dict(t=50,b=100,l=50,r=20),
            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fafafa',
            height=420,font=dict(family='Segoe UI')
        )
        st.plotly_chart(fig_r1, use_container_width=True, config={'displayModeBar':False})

        st.markdown(f"**📋 Proyeksi 2026 per Bulan — {sel_s1}**")
        tbl_proj26 = [{'Bulan': BULAN[i], 'X': i+1,
                       'Substitusi': f"Ŷ = {a1v} + ({b1v})×{i+1}",
                       'Proyeksi 2026 (%)': proj26[i]} for i in range(11)]
        st.dataframe(pd.DataFrame(tbl_proj26), use_container_width=True, hide_index=True)

    # ── TAB 2 ──
    with tab_r2:
        st.markdown("""
        <div style='background:#e8f4fd;border-radius:10px;padding:14px 18px;margin-bottom:16px;border-left:4px solid #00b894'>
        <b>📌 Regresi Tahap 2</b> — Data 2018–2025 (aktual) + 2026 (proyeksi) digabung.
        Fit ulang otomatis → persamaan baru → substitusi X=1..11 → <b>Proyeksi 2027</b>.
        </div>
        """, unsafe_allow_html=True)

        col_sel2, _ = st.columns([1,2])
        with col_sel2:
            sel_s2 = st.selectbox("Pilih Seksi", SEKSI_LIST,
                                   format_func=lambda x: f"{x} — {SEKSI_NAMA[x]}", key='reg_s2')

        rd2 = regresi_data[sel_s2]
        a2v,b2v,r2_2v,mae2v = rd2['a2'],rd2['b2'],rd2['r2_2'],rd2['mae2']
        proj27 = rd2['proj2027']

        col_eq1,col_eq2,col_eq3,col_eq4 = st.columns(4)
        for col, label, val, color in [
            (col_eq1,"Konstanta (a)",f"{a2v}","#1a3a6b"),
            (col_eq2,"Koefisien (b)",f"{b2v}","#e17055"),
            (col_eq3,"R²",f"{r2_2v}","#00b894"),
            (col_eq4,"MAE (%)",f"{mae2v:.4f}","#9b59b6"),
        ]:
            col.markdown(f"""
            <div style='background:white;border-radius:12px;padding:16px 18px;
                        box-shadow:0 2px 12px rgba(0,0,0,0.07);border-top:3px solid {color};text-align:center'>
              <div style='font-size:11px;color:#636e72;margin-bottom:4px'>{label}</div>
              <div style='font-size:20px;font-weight:800;color:{color}'>{val}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background:#1a3a6b;color:white;border-radius:10px;padding:12px 20px;margin:16px 0;text-align:center;font-size:15px'>
        <b>Persamaan Tahap 2:</b> &nbsp; Ŷ = {a2v} + ({b2v}) · X &nbsp;|&nbsp;
        n = {len(rd2['x_gabung2'])} observasi (2018–2026)
        </div>
        """, unsafe_allow_html=True)

        fig_r2 = go.Figure()
        n_aktual = len(rd2['x_gabung2']) - 11
        fig_r2.add_trace(go.Scatter(
            x=rd2['x_gabung2'][:n_aktual], y=rd2['y_gabung2'][:n_aktual], mode='markers',
            name='Data Aktual (2018–2025)',
            marker=dict(size=6,color='#1a3a6b',opacity=0.5)
        ))
        fig_r2.add_trace(go.Scatter(
            x=rd2['x_gabung2'][n_aktual:], y=rd2['y_gabung2'][n_aktual:], mode='markers',
            name='Proyeksi 2026 (input)',
            marker=dict(size=9,color='#e17055',symbol='diamond')
        ))
        x_line2 = list(range(1,12))
        y_line2 = [round(a2v + b2v*x,4) for x in x_line2]
        fig_r2.add_trace(go.Scatter(
            x=x_line2, y=y_line2, mode='lines',
            name='Garis Regresi Tahap 2',
            line=dict(color='#9b59b6',width=2.5)
        ))
        fig_r2.add_trace(go.Scatter(
            x=x_line2, y=proj27, mode='markers+lines',
            name='Proyeksi 2027',
            marker=dict(size=9,color='#c8a84b',symbol='star'),
            line=dict(color='#c8a84b',dash='dot')
        ))
        fig_r2.update_layout(
            title=f"Sebaran Data & Regresi Tahap 2 — {sel_s2} ({SEKSI_NAMA[sel_s2]})",
            xaxis=dict(title='Indeks Bulan (1=Feb … 11=Des)',gridcolor='#f0f0f0',
                       tickvals=list(range(1,12)),ticktext=BULAN),
            yaxis=dict(title='% Realisasi Non-Kumulatif',gridcolor='#f0f0f0'),
            legend=dict(orientation='h',y=-0.3),
            margin=dict(t=50,b=100,l=50,r=20),
            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fafafa',
            height=420,font=dict(family='Segoe UI')
        )
        st.plotly_chart(fig_r2, use_container_width=True, config={'displayModeBar':False})

        st.markdown(f"**📋 Proyeksi 2027 per Bulan — {sel_s2}**")
        tbl_proj27 = [{'Bulan': BULAN[i], 'X': i+1,
                       'Substitusi': f"Ŷ = {a2v} + ({b2v})×{i+1}",
                       'Proyeksi 2027 (%)': proj27[i]} for i in range(11)]
        st.dataframe(pd.DataFrame(tbl_proj27), use_container_width=True, hide_index=True)

    # ── TAB 3 ──
    with tab_r3:
        st.markdown("### 📋 Ringkasan Semua Seksi — 1 Persamaan per Seksi")
        tbl_all = []
        for s in SEKSI_LIST:
            rd = regresi_data[s]
            tbl_all.append({
                'Seksi': s, 'Nama Seksi': SEKSI_NAMA[s],
                'a Tahap1': rd['a1'], 'b Tahap1': rd['b1'],
                'Persamaan Tahap1': f"Ŷ = {rd['a1']} + ({rd['b1']})·X",
                'R² T1': rd['r2_1'], 'MAE T1 (%)': rd['mae1'],
                'a Tahap2': rd['a2'], 'b Tahap2': rd['b2'],
                'Persamaan Tahap2': f"Ŷ = {rd['a2']} + ({rd['b2']})·X",
                'R² T2': rd['r2_2'], 'MAE T2 (%)': rd['mae2'],
                'Total Proj 2026 (%)': round(sum(rd['proj2026']),2),
                'Total Proj 2027 (%)': round(sum(rd['proj2027']),2),
                'Selisih 2027-2026 (%)': round(sum(rd['proj2027'])-sum(rd['proj2026']),2),
                'Risiko (CV)': REGRESI[s]['risiko'],
            })
        st.dataframe(pd.DataFrame(tbl_all), use_container_width=True, hide_index=True)

        risiko_clr = {'Rendah':'#00b894','Sedang':'#fdcb6e','Tinggi':'#d63031'}
        col_mae1, col_mae2 = st.columns(2)
        for col, tahap, key_mae in [(col_mae1,"Tahap 1",'mae1'),(col_mae2,"Tahap 2",'mae2')]:
            with col:
                mae_vals = [regresi_data[s][key_mae] for s in SEKSI_LIST]
                clrs = [risiko_clr[REGRESI[s]['risiko']] for s in SEKSI_LIST]
                fig_m = go.Figure(go.Bar(
                    x=SEKSI_LIST, y=mae_vals,
                    marker=dict(color=clrs),
                    text=[f"{v:.4f}%" for v in mae_vals],textposition='outside'
                ))
                fig_m.update_layout(
                    title=f"MAE {tahap} per Seksi",
                    margin=dict(t=40,b=40,l=40,r=20),
                    paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fafafa',
                    yaxis=dict(title='MAE (%)',gridcolor='#f0f0f0'),
                    height=300,font=dict(family='Segoe UI')
                )
                st.plotly_chart(fig_m, use_container_width=True, config={'displayModeBar':False})

        st.markdown("""
        <div style='background:#f8f9fa;border-radius:10px;padding:16px 20px;margin-top:8px'>
        <b>📏 Interpretasi MAE:</b><br>
        <span style='color:#00b894'>🟢 MAE ≤ 1% → Akurasi Tinggi</span> &nbsp;|&nbsp;
        <span style='color:#fdcb6e'>🟡 MAE 1–3% → Akurasi Sedang</span> &nbsp;|&nbsp;
        <span style='color:#d63031'>🔴 MAE > 3% → Akurasi Rendah</span><br>
        Klasifikasi risiko: S3 & S4 = Tinggi | S1 & S5 = Sedang | S2 & S6 = Rendah
        </div>
        """, unsafe_allow_html=True)

    # ── TAB 4 ──
    with tab_r4:
        st.markdown("""
        <div style='background:#e8f4fd;border-radius:10px;padding:14px 18px;margin-bottom:16px;border-left:4px solid #c8a84b'>
        <b>🧮 Kalkulator Data Baru</b> — Tambahkan data realisasi tahun baru,
        sistem akan menghitung ulang persamaan regresi dan proyeksi tahun berikutnya.
        </div>
        """, unsafe_allow_html=True)

        col_inp1, col_inp2 = st.columns([1,2])
        with col_inp1:
            tahun_baru = st.number_input("Tahun Data Baru", min_value=2026, max_value=2035, value=2026, step=1)
            seksi_kalk = st.selectbox("Pilih Seksi", SEKSI_LIST,
                                       format_func=lambda x: f"{x} — {SEKSI_NAMA[x]}", key='kalk_seksi')

        st.markdown(f"**Masukkan % Realisasi Bulanan {seksi_kalk} Tahun {tahun_baru}** (non-kumulatif per bulan)")
        cols_inp = st.columns(6)
        input_vals = []
        for i, bln in enumerate(BULAN):
            with cols_inp[i % 6]:
                val = st.number_input(bln[:3], min_value=0.0, max_value=30.0, value=0.0,
                                       step=0.01, format="%.2f", key=f"inp_{bln}")
                input_vals.append(val)

        if st.button("🔄 Hitung Ulang Regresi", type="primary"):
            tahun_aktual = list(range(2018, 2026))

            def regresi_manual_kalk(x_vals, y_vals):
                x = np.array(x_vals, dtype=float)
                y = np.array(y_vals, dtype=float)
                n = len(x)
                b = (n*np.sum(x*y) - np.sum(x)*np.sum(y)) / (n*np.sum(x**2) - np.sum(x)**2)
                a = (np.sum(y) - b*np.sum(x)) / n
                y_pred = a + b*x
                mae = float(np.mean(np.abs(y - y_pred)))
                ss_res = np.sum((y-y_pred)**2)
                ss_tot = np.sum((y-np.mean(y))**2)
                r2 = float(1-ss_res/ss_tot) if ss_tot!=0 else 0.0
                return round(a,4), round(b,4), round(r2,4), round(mae,4)

            x_pool_k, y_pool_k = [], []
            for tahun in tahun_aktual:
                pct_list = get_pct_bulanan(df, seksi_kalk, tahun)
                for bi, pct in enumerate(pct_list):
                    x_pool_k.append(bi+1)
                    y_pool_k.append(pct)
            for bi, pct in enumerate(input_vals):
                x_pool_k.append(bi+1)
                y_pool_k.append(pct)

            a_k, b_k, r2_k, mae_k = regresi_manual_kalk(x_pool_k, y_pool_k)
            proj_next = [max(0.0, round(a_k + b_k*x, 4)) for x in range(1,12)]

            st.markdown(f"""
            <div style='background:#1a3a6b;color:white;border-radius:10px;padding:14px 20px;margin:12px 0;text-align:center'>
            Persamaan Baru: <b>Ŷ = {a_k} + ({b_k})·X</b> &nbsp;|&nbsp; R²={r2_k} &nbsp;|&nbsp; MAE={mae_k:.4f}%<br>
            Total Proyeksi <b>{tahun_baru+1}</b> untuk <b>{seksi_kalk}</b>:
            <span style='color:#c8a84b;font-size:22px;font-weight:800'>{round(sum(proj_next),2)}%</span>
            </div>
            """, unsafe_allow_html=True)

            fig_kalk = go.Figure(go.Bar(
                x=BULAN, y=proj_next,
                marker=dict(color=SEKSI_COLORS[seksi_kalk]),
                text=[f"{v:.2f}%" for v in proj_next],textposition='outside',
            ))
            fig_kalk.update_layout(
                title=f"Proyeksi {tahun_baru+1} per Bulan — {seksi_kalk}",
                margin=dict(t=50,b=60,l=50,r=20),
                paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='#fafafa',
                xaxis=dict(tickangle=-20,gridcolor='#f0f0f0'),
                yaxis=dict(title='% Realisasi',gridcolor='#f0f0f0'),
                height=320,font=dict(family='Segoe UI')
            )
            st.plotly_chart(fig_kalk, use_container_width=True, config={'displayModeBar':False})

            tbl_kalk = [{'Bulan': BULAN[i], 'X': i+1,
                         'Substitusi': f"Ŷ = {a_k} + ({b_k})×{i+1}",
                         f'Proyeksi {tahun_baru+1} (%)': proj_next[i]} for i in range(11)]
            st.dataframe(pd.DataFrame(tbl_kalk), use_container_width=True, hide_index=True)