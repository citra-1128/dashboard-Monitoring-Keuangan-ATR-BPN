# ATR/BPN Surabaya I — Dashboard Proyeksi Anggaran

Dashboard Streamlit untuk monitoring dan proyeksi realisasi anggaran ATR/BPN Surabaya I.

## Fitur
- **Dashboard** — Ringkasan total pagu, realisasi, gauge chart, dan tabel per seksi
- **Monitoring Bulanan** — Filter per tahun & bulan, kartu sisa pagu, chart kumulatif & delta per seksi
- **Analisis & Proyeksi** — Proyeksi 2026–2027, tren historis 2018–2027, heatmap, risiko & toleransi

## Struktur File
```
atrbpn_dashboard/
├── app.py            # Aplikasi utama Streamlit
├── data_b64.txt      # Data Excel ter-embed (base64)
└── requirements.txt  # Dependencies
```

## Cara Menjalankan Lokal
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy ke Streamlit Cloud
1. Push folder ini ke GitHub (repo baru atau subdirectory)
2. Buka https://share.streamlit.io
3. Klik **New app** → pilih repo & set **Main file path** ke `app.py`
4. Klik **Deploy**

> **Catatan:** File `data_b64.txt` harus ikut di-push ke repo — berisi data Excel yang sudah di-encode base64, tidak perlu upload manual.
