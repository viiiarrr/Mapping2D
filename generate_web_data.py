"""
generate_web_data.py
====================
Script untuk menyiapkan data CSV ke dalam folder web-visualisasi/data/
sehingga bisa diakses di GitHub Pages.

Jalankan sekali setiap kali ada data percobaan baru:
    python generate_web_data.py

Yang dilakukan:
  1. Scan folder Data/percobaan_N/koordinat.csv
  2. Copy semua CSV ke web-visualisasi/data/percobaan_N/koordinat.csv
  3. Buat web-visualisasi/data/manifest.json (daftar semua percobaan)
"""

import os
import shutil
import json

DATA_DIR   = os.path.join(os.path.dirname(__file__), 'Data')
WEB_DIR    = os.path.join(os.path.dirname(__file__), 'web-visualisasi', 'data')

def main():
    if not os.path.exists(DATA_DIR):
        print(f'[!] Folder Data/ tidak ditemukan: {DATA_DIR}')
        return

    os.makedirs(WEB_DIR, exist_ok=True)

    experiments = []

    # Scan semua folder percobaan
    entries = sorted(
        [d for d in os.listdir(DATA_DIR) if d.startswith('percobaan_')],
        key=lambda x: int(x.split('_')[1])
    )

    for folder in entries:
        src_csv = os.path.join(DATA_DIR, folder, 'koordinat.csv')
        if not os.path.exists(src_csv):
            continue

        # Hitung jumlah baris data
        with open(src_csv, 'r') as f:
            lines = f.readlines()
        n_rows = max(0, len(lines) - 1)  # minus header

        # Copy ke web-visualisasi/data/
        dst_dir = os.path.join(WEB_DIR, folder)
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src_csv, os.path.join(dst_dir, 'koordinat.csv'))

        num = int(folder.split('_')[1])
        experiments.append({
            'id':     num,
            'name':   f'Percobaan {num}',
            'file':   f'{folder}/koordinat.csv',
            'rows':   n_rows,
        })

        print(f'  [+] {folder:20s}  ({n_rows} paket)')

    # Urutkan dari terbesar ke terkecil (percobaan terbaru duluan)
    experiments.sort(key=lambda x: -x['id'])

    # Tulis manifest.json
    manifest_path = os.path.join(WEB_DIR, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump({'experiments': experiments}, f, indent=2, ensure_ascii=False)

    print(f'\n[OK] Selesai! {len(experiments)} percobaan disalin ke web-visualisasi/data/')
    print(f'[OK] Manifest: {manifest_path}')
    print(f'\nLangkah berikutnya:')
    print(f'  git add web-visualisasi/data/')
    print(f'  git commit -m "Update data percobaan"')
    print(f'  git push')

if __name__ == '__main__':
    main()
