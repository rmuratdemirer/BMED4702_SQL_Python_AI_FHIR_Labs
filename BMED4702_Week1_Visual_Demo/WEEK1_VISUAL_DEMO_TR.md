# BMED4702 — PyCharm'da Görünen SQL + Python Demonstrasyonu

Bu ek paket mevcut projedeki hiçbir dosyayı değiştirmez. Yalnızca yeni bir
çalıştırıcı ve yeni bir SQL örneği ekler.

## Kurulum

ZIP'e sağ tıklayıp **Tümünü ayıkla** seçeneğine basın. Oluşan
`BMED4702_Week1_Visual_Demo` klasörünün tamamını mevcut proje klasörünün içine
kopyalayın. Son görünüm şöyle olmalıdır:

```text
C:\2026-27 Academic Year\BMED 4702 MEDICAL INFORMATION SYSTEMS\BMED4702_SQL_Python_AI_FHIR_Labs
└── BMED4702_Week1_Visual_Demo
    ├── run_week1_visual_demo.py
    ├── WEEK1_VISUAL_DEMO_TR.md
    └── sql
        └── 01_table_counts_visual.sql
```

Hiçbir dosyanın değiştirilmesi sorulmamalıdır. Sorulursa işlemi iptal edin.

## Çalıştırma

1. PyCharm'da `BMED4702_Week1_Visual_Demo` klasörünü genişletin.
2. `run_week1_visual_demo.py` dosyasını açın.
3. Kod alanında sağ tıklayın.
4. `Run 'run_week1_visual_demo'` seçeneğine basın.

## Öğrencinin göreceği sonuçlar

PyCharm'ın **Run** penceresinde:

- çalıştırılan SQL,
- tablo adları ve satır sayıları,
- eksiklik yüzdeleri,
- `charttime`–`storetime` gecikme özeti,
- kaydedilen CSV ve PNG dosyalarının konumu

görünür.

Ayrıca üç grafik açılır:

1. En büyük 15 tablonun satır sayıları,
2. `labevents` eksiklik yüzdeleri,
3. Laboratuvar sonucunun erişilebilirlik gecikmesi.

Grafikler aynı zamanda `output` klasörüne PNG olarak kaydedilir. Program
veritabanını salt-okunur açar ve MIMIC-IV verisini değiştiremez.

## Üretilen dosyalar

```text
output\week1_01_table_counts.csv
output\week1_01_table_counts.png
output\week1_02_missingness.csv
output\week1_02_missingness.png
output\week1_03_availability_lag_summary.csv
output\week1_03_availability_lag.png
output\week1_demo_provenance.json
```

Önceki bir CSV veya PNG Excel/Fotoğraflar içinde açıksa program eski dosyanın
üzerine yazmaya çalışmaz; zaman damgalı yeni bir dosya oluşturur.
