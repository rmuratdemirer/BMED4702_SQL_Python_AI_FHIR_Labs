# BMED4702 Week 2 Visual Demo

Bu paket, **Week 2: Interoperability, HL7 FHIR and Clinical Terminologies**
sunumundaki 15, 21, 24-45. slaytları çalışan bir sınıf gösterimine dönüştürür.

## Ne gösterir?

1. Gerçek MIMIC-IV Demo `labevents` satırını ve kaynak kanıtını gösterir.
2. Aynı satırdan güvenli ve kasıtlı olarak güvensiz iki FHIR Observation üretir.
3. Yapısal, terminolojik, provenance ve klinik invariant kontrollerini karşılaştırır.
4. UCUM kodunun ne zaman yazılabileceğini görselleştirir.
5. Uyumlu kreatinin kayıtlarından zaman serisi oluşturur.
6. Üretilen gerçek FHIR kaynağını JSON ağacı olarak gösterir.
7. Öğrenci eşlemesini 100 puan üzerinden rubrik ekranında değerlendirir.
8. Her çalışmada provenance JSON ve yeniden kullanılabilir çıktılar üretir.

## Mevcut PyCharm projesini bozmadan kurulum

ZIP içindeki `BMED4702_Week2_Visual_Demo_v2` klasörünü, mevcut projenizin **içine**
kopyalayın. Bu klasörün adı Week 1 klasöründen farklıdır; mevcut dosyaların
üzerine yazmaz.

Beklenen görünüm:

```text
BMED4702_SQL_Python_AI_FHIR_Labs/
├── .venv/
├── data/
│   └── mimic_demo.sqlite
├── BMED4702_Week1_Visual_Demo/
└── BMED4702_Week2_Visual_Demo_v2/
    ├── run_week2_visual_demo.py
    ├── sql/
    ├── student_exercise/
    └── tests/
```

## Tek çalıştırma adımı

PyCharm sol panelde şunu açın:

```text
BMED4702_Week2_Visual_Demo_v2/run_week2_visual_demo.py
```

Dosyanın içinde sağ tıklayın ve **Run 'run_week2_visual_demo'** seçin.
`src/db.py` dosyasını çalıştırmayın; o yalnızca yardımcı fonksiyon dosyasıdır.

Paket eksikliği görülürse PyCharm Terminal'e tek satır yazın:

```powershell
.\.venv\Scripts\python.exe -m pip install pandas matplotlib
```

Sonra aynı `run_week2_visual_demo.py` dosyasını yeniden çalıştırın.

## Ekranda ne görünmeli?

- **Run** penceresinde: SQL kaynak satırları, güvenli FHIR JSON, doğrulama
  hataları ve öğretim soruları. Sonuçların başını görmek için Run penceresinde
  yukarı kaydırın.
- **Plots** penceresinde: güvenli/güvensiz karşılaştırması, UCUM kararı,
  kreatinin zaman çizelgesi, FHIR JSON ağacı ve öğrenci puanlama ekranı.
- `output/week2_visual_demo/` altında: CSV, JSON, PNG ve provenance dosyaları.

En son satırdaki `Process finished with exit code 0`, PyCharm'ın otomatik
**başarı mesajıdır**. Hata değildir.

## 35 dakikalık sınıf akışı

| Süre | Eylem | Sunum bağı |
|---:|---|---|
| 0-5 dk | Kaynak satırı okuyun; “hangi alan icat edilemez?” diye sorun | 15, 33-35 |
| 5-13 dk | Güvenli ve güvensiz JSON'u karşılaştırın | 21, 34-36 |
| 13-20 dk | Validation grafiğini ve dört katmanı tartışın | 37, 43-45 |
| 20-26 dk | UCUM kararını tartışın; LOINC eşdeğerliği iddia etmeyin | 24-32 |
| 26-31 dk | Zaman serisinde kavram, birim ve zamanı denetleyin | 40-42 |
| 31-35 dk | Öğrenciler `student_exercise` dosyasındaki dört kusuru onarsın | 43-44 |

## Testleri çalıştırma

PyCharm Terminal:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s BMED4702_Week2_Visual_Demo_v2\tests -v
```

Beklenen sonuç: dört test için `ok` ve en sonda `OK`.

## Güvenlik ve klinik sınır

- SQLite yalnızca salt okunur açılır.
- Hasta kimliği için yalnızca de-identified MIMIC-IV Demo verisi kullanılır.
- Yerel `itemid`, kanıt olmadan LOINC eşdeğeri ilan edilmez.
- Saat dilimi bilinmiyorsa uydurulmaz.
- Bu eğitim kodu klinik karar veya üretim sistemi değildir.
