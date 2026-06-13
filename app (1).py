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
    "admin": "atrbpn2025",
    "viewer": "bpn2025"
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
            if username in USERS and USERS[username] == password:
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.rerun()
            else:
                st.error("❌ Username atau password salah. Coba lagi.")

        st.markdown("""
        <div style='text-align:center;font-size:11px;color:#b2bec3;margin-top:20px'>
        © 2026 Kantor ATR/BPN Surabaya I
        </div>
        """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    show_login()
    st.stop()

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

# Proyeksi 2026
PROYEKSI_2026 = {
    'S1': [9.54,9.14,8.76,8.38,8.00,7.64,7.28,6.94,6.60,6.27,5.95],
    'S2': [10.04,9.69,9.34,8.99,8.64,8.29,7.94,7.59,7.24,6.89,6.54],
    'S3': [7.66,7.35,7.04,6.74,6.45,6.17,5.89,5.61,5.35,5.09,4.83],
    'S4': [10.50,10.07,9.64,9.21,8.78,8.35,7.93,7.50,7.07,6.64,6.21],
    'S5': [9.99,9.66,9.34,9.02,8.70,8.37,8.05,7.73,7.40,7.08,6.76],
    'S6': [11.18,10.74,10.30,9.86,9.42,8.98,8.54,8.10,7.65,7.21,6.77],
}
# Proyeksi 2027
PROYEKSI_2027 = {
    'S1': [9.63,9.30,8.97,8.64,8.31,7.97,7.64,7.31,6.98,6.65,6.32],
    'S2': [10.03,9.68,9.33,8.98,8.63,8.28,7.93,7.58,7.23,6.88,6.53],
    'S3': [8.02,7.75,7.47,7.19,6.92,6.64,6.37,6.09,5.81,5.54,5.26],
    'S4': [10.50,10.07,9.64,9.21,8.78,8.35,7.93,7.50,7.07,6.64,6.21],
    'S5': [9.99,9.66,9.34,9.02,8.69,8.37,8.05,7.73,7.40,7.08,6.76],
    'S6': [11.18,10.74,10.30,9.86,9.42,8.98,8.54,8.10,7.65,7.21,6.77],
}
# Tren historis
TREN = {
    'S1': {2018:81.79,2019:81.07,2020:84.58,2021:96.08,2022:93.88,2023:93.88,2024:66.75,2025:98.25},
    'S2': {2018:85.00,2019:88.00,2020:86.41,2021:78.99,2022:88.88,2023:98.82,2024:99.94,2025:99.99},
    'S3': {2018:71.53,2019:71.09,2020:55.48,2021:24.34,2022:68.63,2023:95.49,2024:100.00,2025:98.74},
    'S4': {2018:98.00,2019:37.26,2020:100.00,2021:100.00,2022:99.95,2023:100.00,2024:100.00,2025:100.00},
    'S5': {2018:78.61,2019:75.71,2020:89.78,2021:99.81,2022:99.98,2023:99.94,2024:93.44,2025:99.25},
    'S6': {2018:96.60,2019:98.22,2020:98.29,2021:98.95,2022:98.90,2023:99.73,2024:99.39,2025:99.98},
}
# Regresi
REGRESI = {
    'S1': {'a':3.154,'b':-0.065,'transformasi':True,'r2':0.072,'normal':False,'p_value':0.009,'mae':2.53,'risiko':'Sedang'},
    'S2': {'a':10.39,'b':-0.35,'transformasi':False,'r2':0.083,'normal':True,'p_value':0.063,'mae':0.44,'risiko':'Rendah'},
    'S3': {'a':2.825,'b':-0.057,'transformasi':True,'r2':0.062,'normal':False,'p_value':0.011,'mae':4.99,'risiko':'Tinggi'},
    'S4': {'a':10.928,'b':-0.429,'transformasi':False,'r2':0.074,'normal':True,'p_value':0.058,'mae':0.01,'risiko':'Sedang'},
    'S5': {'a':10.31,'b':-0.323,'transformasi':False,'r2':0.073,'normal':True,'p_value':0.061,'mae':0.03,'risiko':'Rendah'},
    'S6': {'a':11.623,'b':-0.441,'transformasi':False,'r2':0.111,'normal':True,'p_value':0.072,'mae':0.01,'risiko':'Rendah'},
}

# ─── LOAD DATA EXCEL (di-embed) ──────────────────────────────────────────────
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
    """Ambil pagu — jika pagu bisa direvisi, pakai bulan terakhir atau s/d bulan_idx."""
    sub = df[(df['Seksi']==seksi) & (df['Tahun']==tahun)].copy()
    if sub.empty:
        return 0
    sub['_idx'] = sub['Bulan'].apply(lambda b: BULAN.index(b) if b in BULAN else -1)
    sub = sub[sub['_idx'] >= 0].sort_values('_idx')
    if bulan_idx is not None:
        sub = sub[sub['_idx'] <= bulan_idx]
        if sub.empty:
            return 0
    row = sub.iloc[-1]  # pagu bulan terakhir (revisi terakhir)
    return int(row['Pagu PNBP (Rp)'] + row['Pagu RM PTSL (Rp)'] + row['Pagu RM Non-PTSL (Rp)'])

def get_pct_bulanan(df, seksi, tahun):
    """% realisasi per bulan (non-kumulatif) — dihitung dari selisih kumulatif antar bulan."""
    pagu = get_pagu(df, seksi, tahun)
    if pagu == 0:
        return [0]*11
    kum_rp = []
    for bln in BULAN:
        sub = df[(df['Seksi']==seksi) & (df['Tahun']==tahun) & (df['Bulan']==bln)]
        kum_rp.append(int(sub.iloc[0]['TotalReal']) if not sub.empty else 0)
    # Non-kumulatif: selisih antar bulan
    hasil = []
    prev = 0
    for val in kum_rp:
        if val > 0:
            delta = val - prev
            hasil.append(round(delta / pagu * 100, 4))
            prev = val
        else:
            hasil.append(0)
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
    """TotalReal adalah kumulatif — ambil nilai bulan terakhir s/d sampai_idx, pagu juga s/d saat itu."""
    pagu = get_pagu(df, seksi, tahun, bulan_idx=sampai_idx)
    total_real = 0
    # cari bulan terakhir yang ada data dari 0..sampai_idx
    for i in range(sampai_idx, -1, -1):
        bln = BULAN[i]
        sub = df[(df['Seksi']==seksi) & (df['Tahun']==tahun) & (df['Bulan']==bln)]
        if not sub.empty:
            total_real = int(sub.iloc[0]['TotalReal'])
            break
    sisa = pagu - total_real
    pct_real = round(total_real / pagu * 100, 2) if pagu > 0 else 0
    sisa_pct = round(sisa / pagu * 100, 2) if pagu > 0 else 0
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
        pagu = get_pagu(df, s, tahun)  # ambil pagu bulan terakhir (sudah revisi)
        # TotalReal adalah kumulatif — ambil bulan terakhir yang ada datanya
        sub = df[(df['Seksi']==s) & (df['Tahun']==tahun)].copy()
        sub['_bulan_idx'] = sub['Bulan'].apply(lambda b: BULAN.index(b) if b in BULAN else -1)
        sub = sub[sub['_bulan_idx'] >= 0].sort_values('_bulan_idx')
        real_rp = int(sub.iloc[-1]['TotalReal']) if not sub.empty else 0
        pct = round(real_rp / pagu * 100, 2) if pagu > 0 else 0
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
    if pct >= 80:
        return "🟢"
    elif pct >= 50:
        return "🟡"
    return "🔴"

def risiko_color(risiko):
    return {'Rendah':'#00b894','Sedang':'#fdcb6e','Tinggi':'#d63031'}.get(risiko,'#636e72')

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
  --primary: #1a3a6b;
  --secondary: #c8a84b;
  --accent: #2e86de;
  --bg: #f0f4f8;
  --success: #00b894;
  --danger: #d63031;
  --warning: #fdcb6e;
  --muted: #636e72;
}
[data-testid="stSidebar"] {
  background: var(--primary) !important;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
[data-testid="stSidebar"] .stSelectbox label { color: rgba(255,255,255,0.6) !important; font-size:11px !important; }
[data-testid="stSidebarNav"] a { color: rgba(255,255,255,0.75) !important; }

.stat-card {
  border-radius: 16px; padding: 22px 24px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  color: white; position: relative; overflow: hidden;
  transition: transform .2s;
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
.section-header {
  font-weight: 800; font-size: 16px; color: var(--primary);
  margin-bottom: 16px; padding-bottom: 8px;
  border-bottom: 2px solid var(--secondary);
}
.badge-success { background:#d4edda; color:#155724; padding:3px 10px;
  border-radius:50px; font-size:11px; font-weight:700; }
.badge-warning { background:#fff3cd; color:#856404; padding:3px 10px;
  border-radius:50px; font-size:11px; font-weight:700; }
.badge-danger { background:#f8d7da; color:#721c24; padding:3px 10px;
  border-radius:50px; font-size:11px; font-weight:700; }
.progress-wrap { background:#f0f4f8; border-radius:50px; height:8px; overflow:hidden; }
.stMetric { background:white; border-radius:12px; padding:16px !important;
  box-shadow:0 2px 12px rgba(0,0,0,0.06); }
</style>
""", unsafe_allow_html=True)

# ─── LOAD ────────────────────────────────────────────────────────────────────
df = load_data()

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
    halaman = st.radio("", ["🏠 Dashboard", "📊 Monitoring Bulanan", "📈 Analisis & Proyeksi", "📐 Regresi Linear"],
                       label_visibility="collapsed")

    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.rerun()
    st.markdown("<div style='font-size:11px;opacity:0.5;text-align:center;margin-top:8px'>© 2026 ATR/BPN Surabaya I</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HALAMAN 1 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
if halaman == "🏠 Dashboard":
    st.markdown("<h4 style='color:#1a3a6b;font-weight:800;margin-bottom:24px'>🏠 Dashboard — Ringkasan Anggaran</h4>", unsafe_allow_html=True)

    tahun_list_db = sorted(df['Tahun'].unique().tolist(), reverse=True)
    tahun_ref = st.selectbox("📅 Pilih Tahun", tahun_list_db, index=0,
                              key='db_tahun')
    summary = get_dashboard_summary(df, tahun_ref)

    # ── Stat Cards ──
    c1,c2,c3,c4 = st.columns(4)
    cards = [
        (c1, "💼", f"Rp {summary['total_pagu']:,.0f}", f"Total Pagu {tahun_ref}", "6 Seksi", "linear-gradient(135deg,#1a3a6b,#2e6da4)"),
        (c2, "✅", f"Rp {summary['total_realisasi']:,.0f}", "Total Realisasi", f"{summary['pct_realisasi']}% tercapai", "linear-gradient(135deg,#00b894,#00cec9)"),
        (c3, "⏳", f"Rp {summary['sisa_pagu']:,.0f}", "Sisa Pagu", f"{summary['sisa_pct']}% belum terserap", "linear-gradient(135deg,#e17055,#d63031)"),
        (c4, "📊", f"{summary['pct_realisasi']}%", "% Realisasi Keseluruhan", f"Tahun {tahun_ref}", "linear-gradient(135deg,#c8a84b,#f9ca24)"),
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

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gauge + Bar ──
    col1, col2 = st.columns([4,6])
    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">🎯 Capaian Realisasi Keseluruhan</div>', unsafe_allow_html=True)
        pct = summary['pct_realisasi']
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=pct,
            delta={'reference':85, 'valueformat':'.1f'},
            number={'suffix':'%', 'font':{'size':40,'color':'#1a3a6b'}},
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
                                 paper_bgcolor='rgba(0,0,0,0)',
                                 plot_bgcolor='rgba(0,0,0,0)',
                                 height=280)
        st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">📊 Realisasi per Seksi</div>', unsafe_allow_html=True)
        seksi_names = [summary['per_seksi'][s]['nama'] for s in SEKSI_LIST]
        seksi_pcts  = [summary['per_seksi'][s]['realisasi_pct'] for s in SEKSI_LIST]
        bar_colors  = ['#00b894' if v>=80 else '#fdcb6e' if v>=50 else '#d63031' for v in seksi_pcts]
        fig_bar = go.Figure(go.Bar(
            x=seksi_names, y=seksi_pcts,
            marker=dict(color=bar_colors),
            text=[f"{v}%" for v in seksi_pcts], textposition='outside',
            hovertemplate='<b>%{x}</b><br>Realisasi: %{y}%<extra></extra>'
        ))
        fig_bar.add_shape(type='line', x0=-0.5, x1=5.5, y0=85, y1=85,
                          line=dict(color='#c8a84b', width=2, dash='dot'))
        fig_bar.add_annotation(x=5.5, y=85, text='Target 85%', showarrow=False,
                                font=dict(color='#c8a84b', size=11), xanchor='right')
        fig_bar.update_layout(margin=dict(t=20,b=60,l=40,r=20),
                               paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                               yaxis=dict(range=[0,115], title='%', gridcolor='#f0f0f0'),
                               xaxis=dict(tickangle=-15, tickfont=dict(size=10)),
                               height=280, font=dict(family='Segoe UI', color='#2d3436'))
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Tabel per Seksi ──
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-title">📋 Ringkasan Anggaran per Seksi — {tahun_ref}</div>', unsafe_allow_html=True)
    rows = []
    for s in SEKSI_LIST:
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

    # ── Akses Cepat ──
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">🚀 Akses Cepat</div>', unsafe_allow_html=True)
    qa1, qa2 = st.columns(2)
    with qa1:
        st.info("📊 **Monitoring Bulanan** — Pantau sisa pagu & pertumbuhan per seksi. Pilih menu di sidebar.")
    with qa2:
        st.info("📈 **Analisis & Proyeksi** — Lihat proyeksi 2026–2027 & analisis risiko. Pilih menu di sidebar.")
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HALAMAN 2 — MONITORING BULANAN
# ═══════════════════════════════════════════════════════════════════════════════
elif halaman == "📊 Monitoring Bulanan":
    st.markdown("<h4 style='color:#1a3a6b;font-weight:800;margin-bottom:8px'>📊 Monitoring Realisasi Bulanan</h4>", unsafe_allow_html=True)

    # ── Filter ──
    fc1, fc2, fc3 = st.columns([1,1,4])
    with fc1:
        tahun_sel = st.selectbox("Tahun", list(range(2018,2026)), index=7)
    with fc2:
        bulan_sel = st.selectbox("s/d Bulan", BULAN, index=10)
    bulan_idx = BULAN.index(bulan_sel)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Summary Cards per Seksi ──
    cols = st.columns(3)
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

    for i, s in enumerate(SEKSI_LIST):
        d = hasil_monitoring[s]
        c = card_colors[i]
        sisa = d['sisa']
        pct_v = sisa['realisasi_pct']
        badge_cls = "badge-success" if pct_v>=80 else "badge-warning" if pct_v>=50 else "badge-danger"
        pct_bar = min(pct_v, 100)
        with cols[i % 3]:
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

    # ── Charts Kumulatif & Delta ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">📈 Kumulatif % Realisasi per Bulan</div>', unsafe_allow_html=True)
        sel_kum = st.selectbox("Pilih Seksi", SEKSI_LIST, key='kum_seksi',
                               format_func=lambda x: f"{x} — {SEKSI_NAMA[x]}")
        d = hasil_monitoring[sel_kum]
        fig_kum = go.Figure()
        fig_kum.add_trace(go.Scatter(
            x=BULAN, y=d['kumulatif'], mode='lines+markers',
            fill='tozeroy', fillcolor='rgba(46,134,222,0.1)',
            line=dict(color='#2e86de', width=2.5),
            marker=dict(size=7, color='#2e86de'),
            hovertemplate='<b>%{x}</b><br>Kumulatif: %{y:.2f}%<extra></extra>'
        ))
        fig_kum.update_layout(
            margin=dict(t=10,b=60,l=45,r=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
            xaxis=dict(tickangle=-30, gridcolor='#f0f0f0'),
            yaxis=dict(title='%', gridcolor='#f0f0f0'),
            height=300, font=dict(family='Segoe UI', size=12)
        )
        st.plotly_chart(fig_kum, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">🌊 Pertumbuhan Delta % per Bulan</div>', unsafe_allow_html=True)
        sel_delta = st.selectbox("Pilih Seksi", SEKSI_LIST, key='delta_seksi',
                                 format_func=lambda x: f"{x} — {SEKSI_NAMA[x]}")
        d2 = hasil_monitoring[sel_delta]
        delta_colors = ['#00b894' if v >= 0 else '#d63031' for v in d2['delta']]
        fig_delta = go.Figure()
        fig_delta.add_trace(go.Bar(
            x=BULAN, y=d2['delta'],
            marker=dict(color=delta_colors),
            hovertemplate='<b>%{x}</b><br>Delta: %{y:+.2f}%<extra></extra>'
        ))
        fig_delta.update_layout(
            margin=dict(t=10,b=60,l=45,r=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
            xaxis=dict(tickangle=-30, gridcolor='#f0f0f0'),
            yaxis=dict(title='%', gridcolor='#f0f0f0', zeroline=True, zerolinecolor='#ccc'),
            height=300, font=dict(family='Segoe UI', size=12)
        )
        st.plotly_chart(fig_delta, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Tabel Detail ──
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">📋 Tabel % Realisasi Bulanan per Seksi</div>', unsafe_allow_html=True)
    rows = []
    for s in SEKSI_LIST:
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

    tab_proj, tab_tren, tab_risiko = st.tabs(["📅 Proyeksi 2026–2027", "📉 Tren 2018–2027", "⚠️ Risiko & Toleransi"])

    # ── TAB 1: PROYEKSI ──
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
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
            yaxis=dict(title='% Realisasi', gridcolor='#f0f0f0'),
            xaxis=dict(tickangle=-20),
            legend=dict(orientation='h', y=-0.3),
            height=420, font=dict(family='Segoe UI')
        )
        st.plotly_chart(fig_proj, use_container_width=True, config={'displayModeBar':False})

        # Tabel 2026 & 2027
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

    # ── TAB 2: TREN ──
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
                line=dict(color=COLORS[i], width=2.5),
                marker=dict(size=8),
                hovertemplate=f'<b>{s}</b> %{{x}}<br>%{{y:.2f}}%<extra></extra>'
            ))
        fig_tren.add_vline(x=2025.5, line_dash="dash", line_color="#636e72", line_width=1.5)
        fig_tren.add_annotation(x=2025.5, y=108, text="← Aktual | Proyeksi →",
                                 showarrow=False, font=dict(color='#636e72', size=11))
        fig_tren.update_layout(
            margin=dict(t=20,b=60,l=50,r=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
            xaxis=dict(title='Tahun', gridcolor='#f0f0f0'),
            yaxis=dict(title='Total % Realisasi', gridcolor='#f0f0f0', range=[0,115]),
            legend=dict(orientation='h', y=-0.25),
            height=420, font=dict(family='Segoe UI')
        )
        st.plotly_chart(fig_tren, use_container_width=True, config={'displayModeBar':False})

        # Tabel tren
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

    # ── TAB 3: RISIKO ──
    with tab_risiko:
        st.markdown("### ⚠️ Klasifikasi Risiko & Toleransi Deviasi")

        c1, c2 = st.columns(2)
        risiko_clr = {'Rendah':'#00b894','Sedang':'#fdcb6e','Tinggi':'#d63031'}

        with c1:
            st.markdown("**🔴 Klasifikasi Risiko Deviasi per Seksi**")
            mae_vals = [REGRESI[s]['mae'] for s in SEKSI_LIST]
            risiko_vals = [REGRESI[s]['risiko'] for s in SEKSI_LIST]
            bubble_colors = [risiko_clr[REGRESI[s]['risiko']] for s in SEKSI_LIST]
            fig_risk = go.Figure(go.Scatter(
                x=SEKSI_LIST, y=mae_vals,
                mode='markers+text', text=risiko_vals, textposition='top center',
                marker=dict(
                    size=[v*12+20 for v in mae_vals],
                    color=bubble_colors, line=dict(width=2, color='#fff')
                ),
                hovertemplate='<b>%{x}</b><br>MAE: %{y:.2f}%<br>Risiko: %{text}<extra></extra>'
            ))
            fig_risk.add_hline(y=1, line_dash='dot', line_color='#fdcb6e', line_width=2)
            fig_risk.add_hline(y=3, line_dash='dot', line_color='#d63031', line_width=2)
            fig_risk.update_layout(
                margin=dict(t=20,b=40,l=50,r=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
                yaxis=dict(title='MAE (%)', gridcolor='#f0f0f0'),
                height=360, font=dict(family='Segoe UI')
            )
            st.plotly_chart(fig_risk, use_container_width=True, config={'displayModeBar':False})

        with c2:
            st.markdown("**⚖️ MAE per Seksi**")
            fig_mae = go.Figure(go.Bar(
                orientation='h',
                x=mae_vals,
                y=[f"{s} — {SEKSI_NAMA[s][:15]}" for s in SEKSI_LIST],
                marker=dict(color=bubble_colors),
                text=[f"{v}%" for v in mae_vals], textposition='outside',
                hovertemplate='%{y}<br>MAE: %{x:.2f}%<extra></extra>'
            ))
            fig_mae.update_layout(
                margin=dict(t=20,b=40,l=200,r=60),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
                xaxis=dict(title='MAE (%)', gridcolor='#f0f0f0'),
                height=360, font=dict(family='Segoe UI')
            )
            st.plotly_chart(fig_mae, use_container_width=True, config={'displayModeBar':False})

        # Tabel toleransi
        st.markdown("**📏 Tabel Toleransi Deviasi ±5% — Proyeksi 2026**")
        rows = []
        for s in SEKSI_LIST:
            for j, b in enumerate(BULAN[:6]):  # 6 bulan pertama
                proj = PROYEKSI_2026[s][j]
                rows.append({
                    'Seksi': f"{s} — {SEKSI_NAMA[s]}",
                    'Bulan': b,
                    'Proyeksi (%)': proj,
                    'Batas Bawah (-5%)': round(proj-5, 2),
                    'Batas Atas (+5%)': round(proj+5, 2),
                    'Keterangan': f"Jika < {round(proj-5,2)}% → perlu tindak lanjut"
                })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Tabel regresi
        st.markdown("**📐 Ringkasan Hasil Regresi Linear per Seksi**")
        rows_reg = []
        for s in SEKSI_LIST:
            r = REGRESI[s]
            rows_reg.append({
                'Seksi': s, 'Nama': SEKSI_NAMA[s],
                'a (Intersep)': r['a'], 'b (Koefisien)': r['b'],
                'R²': r['r2'],
                'Normalitas': '✅ Normal' if r['normal'] else '⚠️ Tidak Normal',
                'p-value': r['p_value'],
                'Transformasi': '√ (Sqrt)' if r.get('transformasi') else '—',
                'MAE (%)': r['mae'],
                'Risiko': r['risiko']
            })
        st.dataframe(pd.DataFrame(rows_reg), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HALAMAN 4 — REGRESI LINEAR
# ═══════════════════════════════════════════════════════════════════════════════
elif halaman == "📐 Regresi Linear":
    st.markdown("<h4 style='color:#1a3a6b;font-weight:800;margin-bottom:4px'>📐 Analisis Regresi Linear</h4>", unsafe_allow_html=True)

    # ── Deskripsi Metode ──
    with st.expander("📖 Tentang Metode Regresi Linear — Klik untuk baca penjelasan", expanded=False):
        st.markdown("""
        <div style='background:#f0f4f8;border-radius:12px;padding:20px 24px;line-height:1.8'>
        <h5 style='color:#1a3a6b;margin-bottom:12px'>Apa itu Regresi Linear Sederhana?</h5>
        <p>Regresi linear sederhana adalah metode statistik yang digunakan untuk memodelkan hubungan antara 
        satu variabel bebas (<b>X</b>) dan satu variabel terikat (<b>Y</b>) dalam bentuk persamaan garis lurus.</p>
        
        <div style='background:white;border-radius:8px;padding:14px 18px;margin:12px 0;border-left:4px solid #1a3a6b'>
        <b>Persamaan Umum:</b><br>
        <span style='font-size:16px;font-family:monospace'><b>Ŷ = a + b·X</b></span><br><br>
        <b>Keterangan:</b><br>
        • <b>Ŷ</b> = nilai prediksi % realisasi anggaran<br>
        • <b>a</b> = konstanta (intersep) → nilai Ŷ saat X = 0<br>
        • <b>b</b> = koefisien regresi (slope) → besarnya perubahan Ŷ tiap X naik 1 satuan<br>
        • <b>X</b> = urutan tahun (1 = 2018, 2 = 2019, ..., 8 = 2025)
        </div>

        <h5 style='color:#1a3a6b;margin:16px 0 8px'>Rumus Perhitungan Manual</h5>
        <div style='background:white;border-radius:8px;padding:14px 18px;border-left:4px solid #c8a84b'>
        <b>Koefisien b (slope):</b><br>
        <span style='font-family:monospace'>b = [n·ΣXY − ΣX·ΣY] / [n·ΣX² − (ΣX)²]</span><br><br>
        <b>Konstanta a (intersep):</b><br>
        <span style='font-family:monospace'>a = (ΣY − b·ΣX) / n</span><br><br>
        <b>Dimana:</b> n = jumlah data, ΣXY = jumlah perkalian X dan Y
        </div>

        <h5 style='color:#1a3a6b;margin:16px 0 8px'>Alur Proyeksi Dua Tahap</h5>
        <div style='background:white;border-radius:8px;padding:14px 18px;border-left:4px solid #00b894'>
        <b>Tahap 1:</b> Data aktual 2018–2025 (X=1 s/d 8) → Regresi → Persamaan 1 → <b>Proyeksi 2026</b> (X=9)<br><br>
        <b>Tahap 2:</b> Data 2018–2025 + Proyeksi 2026 (X=1 s/d 9) → Regresi ulang → Persamaan 2 → <b>Proyeksi 2027</b> (X=10)
        </div>

        <p style='margin-top:14px;font-size:13px;color:#636e72'>Regresi dibangun per seksi per bulan secara terpisah, sehingga menghasilkan 
        66 persamaan regresi (6 seksi × 11 bulan). Akurasi model diukur menggunakan 
        <b>MAE (Mean Absolute Error)</b> — rata-rata selisih antara nilai aktual dan nilai prediksi.</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Fungsi Regresi ──
    def hitung_regresi_manual(x_vals, y_vals):
        """Hitung a, b dengan rumus manual regresi linear."""
        n = len(x_vals)
        x = np.array(x_vals, dtype=float)
        y = np.array(y_vals, dtype=float)
        sum_x  = np.sum(x)
        sum_y  = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x ** 2)
        b = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        a = (sum_y - b * sum_x) / n
        y_pred = a + b * x
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0
        mae = np.mean(np.abs(y - y_pred))
        return round(a, 4), round(b, 4), round(r2, 4), round(mae, 4), y_pred.tolist()

    def get_data_bulanan_seksi(df_data, seksi):
        """Ambil % realisasi per bulan per tahun dari data historis."""
        result = {}
        for tahun in range(2018, 2026):
            pct_list = get_pct_bulanan(df_data, seksi, tahun)
            result[tahun] = pct_list
        return result

    # Hitung semua regresi dari data aktual
    @st.cache_data
    def compute_all_regresi(_df):
        tahun_aktual = list(range(2018, 2026))
        x_aktual = list(range(1, 9))  # X=1..8

        semua = {}
        for s in SEKSI_LIST:
            data_sek = {}
            for t in tahun_aktual:
                data_sek[t] = get_pct_bulanan(_df, s, t)
            semua[s] = data_sek

        hasil = {}
        for s in SEKSI_LIST:
            hasil[s] = {'tahap1': {}, 'tahap2': {}, 'proj2026': [], 'proj2027': []}
            proj26 = []
            for bi, bln in enumerate(BULAN):
                y_vals = [semua[s][t][bi] for t in tahun_aktual]
                a, b, r2, mae, y_pred = hitung_regresi_manual(x_aktual, y_vals)
                pred26 = round(a + b * 9, 4)
                proj26.append(pred26)
                hasil[s]['tahap1'][bln] = {
                    'a': a, 'b': b, 'r2': r2, 'mae': mae,
                    'x': x_aktual, 'y': y_vals, 'y_pred': y_pred, 'pred_next': pred26
                }
            hasil[s]['proj2026'] = proj26

            # Tahap 2: tambah 2026 dari proyeksi
            x2 = list(range(1, 10))  # X=1..9
            proj27 = []
            for bi, bln in enumerate(BULAN):
                y_aktual = [semua[s][t][bi] for t in tahun_aktual]
                y2_vals = y_aktual + [proj26[bi]]
                a2, b2, r2_2, mae2, y2_pred = hitung_regresi_manual(x2, y2_vals)
                pred27 = round(a2 + b2 * 10, 4)
                proj27.append(pred27)
                hasil[s]['tahap2'][bln] = {
                    'a': a2, 'b': b2, 'r2': r2_2, 'mae': mae2,
                    'x': x2, 'y': y2_vals, 'y_pred': y2_pred, 'pred_next': pred27
                }
            hasil[s]['proj2027'] = proj27
        return hasil

    regresi_data = compute_all_regresi(df)

    # ── Tab ──
    tab_r1, tab_r2, tab_r3, tab_r4 = st.tabs([
        "📊 Tahap 1 — Proyeksi 2026",
        "📊 Tahap 2 — Proyeksi 2027",
        "📋 Ringkasan & Akurasi",
        "🧮 Kalkulator Data Baru"
    ])

    # ── TAB 1: REGRESI TAHAP 1 ──
    with tab_r1:
        st.markdown("""
        <div style='background:#e8f4fd;border-radius:10px;padding:14px 18px;margin-bottom:16px;border-left:4px solid #1a3a6b'>
        <b>📌 Regresi Tahap 1</b> — Data aktual 2018–2025 (X = 1 hingga 8) digunakan untuk membangun persamaan regresi 
        per seksi per bulan. Hasil prediksi pada X = 9 menghasilkan <b>proyeksi realisasi tahun 2026</b>.
        </div>
        """, unsafe_allow_html=True)

        col_sel1, _ = st.columns([1, 2])
        with col_sel1:
            sel_s1 = st.selectbox("Pilih Seksi", SEKSI_LIST,
                                   format_func=lambda x: f"{x} — {SEKSI_NAMA[x]}", key='reg_s1')
            sel_b1 = st.selectbox("Pilih Bulan", BULAN, key='reg_b1')

        r1 = regresi_data[sel_s1]['tahap1'][sel_b1]
        a1, b1, r2_1 = r1['a'], r1['b'], r1['r2']
        pred26_val = r1['pred_next']
        tahun_label = [str(2017 + xi) for xi in r1['x']]

        # Info persamaan
        col_eq1, col_eq2, col_eq3, col_eq4 = st.columns(4)
        for col, label, val, color in [
            (col_eq1, "Konstanta (a)", f"{a1}", "#1a3a6b"),
            (col_eq2, "Koefisien (b)", f"{b1}", "#e17055"),
            (col_eq3, "R² (Koef. Determinasi)", f"{r2_1}", "#00b894"),
            (col_eq4, "Proyeksi 2026 (%)", f"{pred26_val:.2f}%", "#c8a84b"),
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
        <b>Persamaan Regresi:</b> &nbsp; Ŷ = {a1} + ({b1}) · X &nbsp;→&nbsp; 
        Proyeksi 2026 (X=9): <span style='color:#c8a84b;font-size:18px;font-weight:800'>{pred26_val:.2f}%</span>
        </div>
        """, unsafe_allow_html=True)

        # Scatter + garis regresi
        fig_r1 = go.Figure()
        fig_r1.add_trace(go.Scatter(
            x=tahun_label, y=r1['y'], mode='markers',
            name='Data Aktual', marker=dict(size=10, color='#1a3a6b', symbol='circle'),
            hovertemplate='<b>%{x}</b>: %{y:.2f}%<extra></extra>'
        ))
        fig_r1.add_trace(go.Scatter(
            x=tahun_label, y=r1['y_pred'], mode='lines',
            name='Garis Regresi', line=dict(color='#e17055', width=2.5, dash='dash'),
            hovertemplate='Prediksi %{x}: %{y:.2f}%<extra></extra>'
        ))
        # Titik proyeksi 2026
        fig_r1.add_trace(go.Scatter(
            x=['2026'], y=[pred26_val], mode='markers+text',
            name='Proyeksi 2026',
            marker=dict(size=14, color='#c8a84b', symbol='star'),
            text=[f"2026: {pred26_val:.2f}%"], textposition='top right',
            hovertemplate='Proyeksi 2026: %{y:.2f}%<extra></extra>'
        ))
        fig_r1.update_layout(
            title=f"Regresi Tahap 1 — {sel_s1} ({SEKSI_NAMA[sel_s1]}) | Bulan: {sel_b1}",
            title_font=dict(size=13, color='#1a3a6b'),
            margin=dict(t=50, b=60, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
            xaxis=dict(title='Tahun', gridcolor='#f0f0f0'),
            yaxis=dict(title='% Realisasi', gridcolor='#f0f0f0'),
            legend=dict(orientation='h', y=-0.25),
            height=380, font=dict(family='Segoe UI')
        )
        st.plotly_chart(fig_r1, use_container_width=True, config={'displayModeBar': False})

        # Residual plot
        residuals1 = [round(r1['y'][i] - r1['y_pred'][i], 4) for i in range(len(r1['y']))]
        fig_resid1 = go.Figure()
        fig_resid1.add_trace(go.Bar(
            x=tahun_label, y=residuals1,
            marker=dict(color=['#00b894' if v >= 0 else '#d63031' for v in residuals1]),
            hovertemplate='<b>%{x}</b><br>Residual: %{y:+.4f}%<extra></extra>'
        ))
        fig_resid1.add_hline(y=0, line_color='#636e72', line_width=1)
        fig_resid1.update_layout(
            title="Residual Plot (Aktual − Prediksi)",
            title_font=dict(size=12, color='#636e72'),
            margin=dict(t=40, b=50, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
            xaxis=dict(gridcolor='#f0f0f0'),
            yaxis=dict(title='Residual (%)', gridcolor='#f0f0f0'),
            height=240, font=dict(family='Segoe UI')
        )
        st.plotly_chart(fig_resid1, use_container_width=True, config={'displayModeBar': False})

        # Tabel semua bulan untuk seksi terpilih
        st.markdown(f"**📋 Tabel Persamaan Regresi Tahap 1 — {sel_s1} (semua bulan)**")
        tbl1 = []
        for bln in BULAN:
            rd = regresi_data[sel_s1]['tahap1'][bln]
            tbl1.append({
                'Bulan': bln,
                'a (Intersep)': rd['a'],
                'b (Koefisien)': rd['b'],
                'Persamaan': f"Ŷ = {rd['a']} + ({rd['b']})·X",
                'R²': rd['r2'],
                'MAE (%)': rd['mae'],
                'Proyeksi 2026 (%)': round(rd['pred_next'], 2)
            })
        st.dataframe(pd.DataFrame(tbl1), use_container_width=True, hide_index=True)

    # ── TAB 2: REGRESI TAHAP 2 ──
    with tab_r2:
        st.markdown("""
        <div style='background:#e8f4fd;border-radius:10px;padding:14px 18px;margin-bottom:16px;border-left:4px solid #00b894'>
        <b>📌 Regresi Tahap 2</b> — Data 2018–2025 (aktual) + 2026 (hasil proyeksi Tahap 1) digabung sebagai 
        X = 1 hingga 9. Regresi dibangun ulang, dan prediksi pada X = 10 menghasilkan <b>proyeksi realisasi tahun 2027</b>.
        </div>
        """, unsafe_allow_html=True)

        col_sel2, _ = st.columns([1, 2])
        with col_sel2:
            sel_s2 = st.selectbox("Pilih Seksi", SEKSI_LIST,
                                   format_func=lambda x: f"{x} — {SEKSI_NAMA[x]}", key='reg_s2')
            sel_b2 = st.selectbox("Pilih Bulan", BULAN, key='reg_b2')

        r2d = regresi_data[sel_s2]['tahap2'][sel_b2]
        a2v, b2v, r2_2v = r2d['a'], r2d['b'], r2d['r2']
        pred27_val = r2d['pred_next']
        tahun_label2 = [str(2017 + xi) for xi in r2d['x']]

        col_eq1, col_eq2, col_eq3, col_eq4 = st.columns(4)
        for col, label, val, color in [
            (col_eq1, "Konstanta (a)", f"{a2v}", "#1a3a6b"),
            (col_eq2, "Koefisien (b)", f"{b2v}", "#e17055"),
            (col_eq3, "R² (Koef. Determinasi)", f"{r2_2v}", "#00b894"),
            (col_eq4, "Proyeksi 2027 (%)", f"{pred27_val:.2f}%", "#9b59b6"),
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
        <b>Persamaan Regresi:</b> &nbsp; Ŷ = {a2v} + ({b2v}) · X &nbsp;→&nbsp; 
        Proyeksi 2027 (X=10): <span style='color:#c8a84b;font-size:18px;font-weight:800'>{pred27_val:.2f}%</span>
        </div>
        """, unsafe_allow_html=True)

        fig_r2 = go.Figure()
        fig_r2.add_trace(go.Scatter(
            x=tahun_label2[:-1], y=r2d['y'][:-1], mode='markers',
            name='Data Aktual (2018–2025)',
            marker=dict(size=10, color='#1a3a6b'),
            hovertemplate='<b>%{x}</b>: %{y:.2f}%<extra></extra>'
        ))
        fig_r2.add_trace(go.Scatter(
            x=['2026'], y=[r2d['y'][-1]], mode='markers',
            name='Proyeksi 2026 (input)',
            marker=dict(size=10, color='#e17055', symbol='diamond'),
            hovertemplate='Proyeksi 2026: %{y:.2f}%<extra></extra>'
        ))
        fig_r2.add_trace(go.Scatter(
            x=tahun_label2, y=r2d['y_pred'], mode='lines',
            name='Garis Regresi Tahap 2',
            line=dict(color='#9b59b6', width=2.5, dash='dash'),
        ))
        fig_r2.add_trace(go.Scatter(
            x=['2027'], y=[pred27_val], mode='markers+text',
            name='Proyeksi 2027',
            marker=dict(size=14, color='#c8a84b', symbol='star'),
            text=[f"2027: {pred27_val:.2f}%"], textposition='top right',
        ))
        fig_r2.update_layout(
            title=f"Regresi Tahap 2 — {sel_s2} ({SEKSI_NAMA[sel_s2]}) | Bulan: {sel_b2}",
            title_font=dict(size=13, color='#1a3a6b'),
            margin=dict(t=50, b=60, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
            xaxis=dict(title='Tahun', gridcolor='#f0f0f0'),
            yaxis=dict(title='% Realisasi', gridcolor='#f0f0f0'),
            legend=dict(orientation='h', y=-0.25),
            height=380, font=dict(family='Segoe UI')
        )
        st.plotly_chart(fig_r2, use_container_width=True, config={'displayModeBar': False})

        # Residual Tahap 2
        residuals2 = [round(r2d['y'][i] - r2d['y_pred'][i], 4) for i in range(len(r2d['y']))]
        fig_resid2 = go.Figure()
        fig_resid2.add_trace(go.Bar(
            x=tahun_label2, y=residuals2,
            marker=dict(color=['#00b894' if v >= 0 else '#d63031' for v in residuals2]),
            hovertemplate='<b>%{x}</b><br>Residual: %{y:+.4f}%<extra></extra>'
        ))
        fig_resid2.add_hline(y=0, line_color='#636e72', line_width=1)
        fig_resid2.update_layout(
            title="Residual Plot (Aktual − Prediksi)",
            title_font=dict(size=12, color='#636e72'),
            margin=dict(t=40, b=50, l=50, r=20),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
            xaxis=dict(gridcolor='#f0f0f0'),
            yaxis=dict(title='Residual (%)', gridcolor='#f0f0f0'),
            height=240, font=dict(family='Segoe UI')
        )
        st.plotly_chart(fig_resid2, use_container_width=True, config={'displayModeBar': False})

        st.markdown(f"**📋 Tabel Persamaan Regresi Tahap 2 — {sel_s2} (semua bulan)**")
        tbl2 = []
        for bln in BULAN:
            rd = regresi_data[sel_s2]['tahap2'][bln]
            tbl2.append({
                'Bulan': bln,
                'a (Intersep)': rd['a'],
                'b (Koefisien)': rd['b'],
                'Persamaan': f"Ŷ = {rd['a']} + ({rd['b']})·X",
                'R²': rd['r2'],
                'MAE (%)': rd['mae'],
                'Proyeksi 2027 (%)': round(rd['pred_next'], 2)
            })
        st.dataframe(pd.DataFrame(tbl2), use_container_width=True, hide_index=True)

    # ── TAB 3: RINGKASAN & AKURASI ──
    with tab_r3:
        st.markdown("### 📋 Ringkasan Semua Seksi")

        # Tabel ringkasan tahap 1 & 2
        tbl_all = []
        for s in SEKSI_LIST:
            mae_list1 = [regresi_data[s]['tahap1'][b]['mae'] for b in BULAN]
            mae_list2 = [regresi_data[s]['tahap2'][b]['mae'] for b in BULAN]
            mae_avg1 = round(np.mean(mae_list1), 4)
            mae_avg2 = round(np.mean(mae_list2), 4)
            proj26_total = round(sum(regresi_data[s]['proj2026']), 2)
            proj27_total = round(sum(regresi_data[s]['proj2027']), 2)
            risiko = 'Rendah' if mae_avg1 <= 1 else 'Sedang' if mae_avg1 <= 3 else 'Tinggi'
            tbl_all.append({
                'Seksi': s, 'Nama Seksi': SEKSI_NAMA[s],
                'MAE Rata² Tahap 1': mae_avg1,
                'MAE Rata² Tahap 2': mae_avg2,
                'Total Proyeksi 2026 (%)': proj26_total,
                'Total Proyeksi 2027 (%)': proj27_total,
                'Klasifikasi Risiko': risiko
            })
        df_all = pd.DataFrame(tbl_all)
        st.dataframe(df_all, use_container_width=True, hide_index=True)

        # Chart MAE per seksi
        st.markdown("<br>", unsafe_allow_html=True)
        col_mae1, col_mae2 = st.columns(2)
        with col_mae1:
            mae_vals_t1 = [row['MAE Rata² Tahap 1'] for row in tbl_all]
            fig_mae1 = go.Figure(go.Bar(
                x=SEKSI_LIST, y=mae_vals_t1,
                marker=dict(color=['#00b894' if v<=1 else '#fdcb6e' if v<=3 else '#d63031' for v in mae_vals_t1]),
                text=[f"{v}%" for v in mae_vals_t1], textposition='outside',
                hovertemplate='<b>%{x}</b><br>MAE: %{y:.4f}%<extra></extra>'
            ))
            fig_mae1.update_layout(
                title="MAE Tahap 1 per Seksi",
                title_font=dict(size=13),
                margin=dict(t=40,b=40,l=40,r=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
                yaxis=dict(title='MAE (%)', gridcolor='#f0f0f0'),
                height=300, font=dict(family='Segoe UI')
            )
            st.plotly_chart(fig_mae1, use_container_width=True, config={'displayModeBar': False})

        with col_mae2:
            mae_vals_t2 = [row['MAE Rata² Tahap 2'] for row in tbl_all]
            fig_mae2 = go.Figure(go.Bar(
                x=SEKSI_LIST, y=mae_vals_t2,
                marker=dict(color=['#00b894' if v<=1 else '#fdcb6e' if v<=3 else '#d63031' for v in mae_vals_t2]),
                text=[f"{v}%" for v in mae_vals_t2], textposition='outside',
                hovertemplate='<b>%{x}</b><br>MAE: %{y:.4f}%<extra></extra>'
            ))
            fig_mae2.update_layout(
                title="MAE Tahap 2 per Seksi",
                title_font=dict(size=13),
                margin=dict(t=40,b=40,l=40,r=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
                yaxis=dict(title='MAE (%)', gridcolor='#f0f0f0'),
                height=300, font=dict(family='Segoe UI')
            )
            st.plotly_chart(fig_mae2, use_container_width=True, config={'displayModeBar': False})

        # Interpretasi MAE
        st.markdown("""
        <div style='background:#f8f9fa;border-radius:10px;padding:16px 20px;margin-top:8px'>
        <b>📏 Interpretasi MAE:</b><br>
        <span style='color:#00b894'>🟢 MAE ≤ 1% → Akurasi Tinggi</span> &nbsp;|&nbsp;
        <span style='color:#fdcb6e'>🟡 MAE 1–3% → Akurasi Sedang</span> &nbsp;|&nbsp;
        <span style='color:#d63031'>🔴 MAE > 3% → Akurasi Rendah (perlu hati-hati)</span>
        </div>
        """, unsafe_allow_html=True)

    # ── TAB 4: KALKULATOR DATA BARU ──
    with tab_r4:
        st.markdown("""
        <div style='background:#e8f4fd;border-radius:10px;padding:14px 18px;margin-bottom:16px;border-left:4px solid #c8a84b'>
        <b>🧮 Kalkulator Data Baru</b> — Tambahkan data realisasi tahun baru (misal setelah 2025 selesai), 
        sistem akan menghitung ulang persamaan regresi secara otomatis dan menghasilkan proyeksi tahun berikutnya.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### Input Data Realisasi Bulanan Tahun Baru")
        col_inp1, col_inp2 = st.columns([1, 2])
        with col_inp1:
            tahun_baru = st.number_input("Tahun Data Baru", min_value=2026, max_value=2035, value=2026, step=1)
            seksi_kalk = st.selectbox("Pilih Seksi", SEKSI_LIST,
                                       format_func=lambda x: f"{x} — {SEKSI_NAMA[x]}", key='kalk_seksi')

        st.markdown(f"**Masukkan % Realisasi Bulanan {seksi_kalk} Tahun {tahun_baru}** (per bulan, non-kumulatif)")
        cols_inp = st.columns(6)
        input_vals = []
        for i, bln in enumerate(BULAN):
            with cols_inp[i % 6]:
                val = st.number_input(bln[:3], min_value=0.0, max_value=30.0, value=0.0,
                                       step=0.01, format="%.2f", key=f"inp_{bln}")
                input_vals.append(val)

        if st.button("🔄 Hitung Ulang Regresi", type="primary", use_container_width=False):
            tahun_aktual = list(range(2018, 2026))
            x_lama = list(range(1, 9))
            x_baru = list(range(1, 10))  # +1 tahun baru
            tahun_x = int(tahun_baru) - 2017  # X untuk tahun baru

            st.markdown(f"---")
            st.markdown(f"#### Hasil Regresi Ulang — {seksi_kalk} | Tahun Baru: {tahun_baru} (X={tahun_x})")

            tbl_kalk = []
            proj_next = []
            for bi, bln in enumerate(BULAN):
                y_lama = [get_pct_bulanan(df, seksi_kalk, t)[bi] for t in tahun_aktual]
                y_baru = y_lama + [input_vals[bi]]
                a_k, b_k, r2_k, mae_k, y_pred_k = hitung_regresi_manual(x_baru, y_baru)
                pred_nxt = round(a_k + b_k * (tahun_x + 1), 4)
                proj_next.append(pred_nxt)
                tbl_kalk.append({
                    'Bulan': bln,
                    'a (Intersep)': a_k,
                    'b (Koefisien)': b_k,
                    'Persamaan': f"Ŷ = {a_k} + ({b_k})·X",
                    'R²': r2_k,
                    'MAE (%)': mae_k,
                    f'Proyeksi {tahun_baru + 1} (%)': round(pred_nxt, 2)
                })

            # Tampilkan ringkasan proyeksi
            total_proj = round(sum(proj_next), 2)
            st.markdown(f"""
            <div style='background:#1a3a6b;color:white;border-radius:10px;padding:14px 20px;margin:12px 0;text-align:center'>
            Total Proyeksi Realisasi <b>{tahun_baru + 1}</b> untuk <b>{seksi_kalk} — {SEKSI_NAMA[seksi_kalk]}</b>: 
            <span style='color:#c8a84b;font-size:22px;font-weight:800'>{total_proj}%</span>
            </div>
            """, unsafe_allow_html=True)

            # Chart proyeksi baru
            fig_kalk = go.Figure()
            fig_kalk.add_trace(go.Bar(
                x=BULAN, y=proj_next,
                marker=dict(color=SEKSI_COLORS[seksi_kalk]),
                text=[f"{v:.2f}%" for v in proj_next], textposition='outside',
                hovertemplate='<b>%{x}</b><br>Proyeksi: %{y:.2f}%<extra></extra>'
            ))
            fig_kalk.update_layout(
                title=f"Proyeksi {tahun_baru + 1} per Bulan — {seksi_kalk}",
                margin=dict(t=50, b=60, l=50, r=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#fafafa',
                xaxis=dict(tickangle=-20, gridcolor='#f0f0f0'),
                yaxis=dict(title='% Realisasi', gridcolor='#f0f0f0'),
                height=320, font=dict(family='Segoe UI')
            )
            st.plotly_chart(fig_kalk, use_container_width=True, config={'displayModeBar': False})
            st.dataframe(pd.DataFrame(tbl_kalk), use_container_width=True, hide_index=True)
