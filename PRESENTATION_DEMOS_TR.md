# BMED4702 — 1. Hafta Sunum Örnekleri

Bu ek paket, çalışan ilk laboratuvarı değiştirmez. Sunumdaki veri kalitesi,
zaman, `NULL`, `JOIN`, provenance ve güvenli AI kavramlarını ayrı SQL ve Python
örneklerine dönüştürür.

## En kolay çalıştırma

PyCharm'da proje kökünde `run_all_demos.py` dosyasını açın ve yeşil
üçgene basın. Alternatif olarak PyCharm Terminal penceresinde:

```text
python run_all_demos.py
```

Her çalıştırma `output/presentation_demos/` altında **yeni ve zaman damgalı bir
klasör** oluşturur. Önceki CSV veya grafik dosyasının üstüne yazılmaz. Böylece
Excel'de ya da PyCharm'da açık bir çıktı dosyası `PermissionError` oluşturmaz.

## Ders sırasında önerilen sıra

| Adım | SQL dosyası | Python dosyası | Ana kavram |
|---|---|---|---|
| 1 | `01_table_counts.sql` | `run_table_counts_demo.py` | tablo ve satır greni |
| 2 | `04_missingness_profile.sql` | `run_missingness_demo.py` | payda, eksiklik, completeness |
| 3 | `05_availability_lag_distribution.sql` ve `06_availability_lag_summary.sql` | `run_availability_demo.py` | charttime, storetime, leakage |
| 4 | `07_join_multiplicity_audit.sql` | `run_join_demo.py` | yanlış/doğru JOIN ve çoğalma |
| 5 | `08_event_trace.sql` | `run_event_trace_demo.py` | bir iddiayı kaynak satıra izleme |
| 6 | `09_null_three_valued_logic.sql` | `run_null_logic_demo.py` | TRUE/FALSE/UNKNOWN |

Altı kavramsal demoyu tek seferde çalıştırmak için `run_all_demos.py` kullanılır.
Availability konusu iki SQL sorgusu kullandığı için toplam **7 SQL**, ayrı konu
çalıştırıcıları ise **6 Python** dosyasıdır. `run_all_demos.py` bunlara ek ana
orkestrasyon dosyasıdır.

## SQL'i doğrudan çalıştırma

DataGrip ya da PyCharm Professional kullanıyorsanız mevcut
`data/mimic_demo.sqlite` bağlantısını seçin, bir SQL dosyasını açın ve sorguyu
çalıştırın. Yeni bir veritabanı veya sunucu kurmanız gerekmez. Python ile SQL
konsolu aynı SQLite dosyasını okur.

PyCharm Community sürümünde Database aracı yoksa SQL yine çalışır:
`run_..._demo.py` dosyaları sorguyu Python'un yerleşik `sqlite3` modülüyle
çalıştırır.

## Oluşan kanıtlar

Tam çalıştırma şunları üretir:

- her sorgu için CSV sonuçları;
- eksiklik, availability lag ve JOIN için üç PNG grafik;
- bütün sonuçları birleştiren `evidence.json`;
- kimlik içermeyen `ai_evidence_packet.json`;
- veritabanı, SQL ve çıktı özetlerini içeren `provenance.json`.

`ai_evidence_packet.json` yalnızca toplu kanıtları içerir. Satır düzeyindeki
`event_trace` bilerek AI paketine alınmaz. Örnek istem
`examples/presentation_ai_prompt.txt` dosyasındadır. AI açıklama yapabilir;
sayısal kanıtın yerine geçmez.

## Sunumdaki availability-lag grafiği için düzeltme

Sunumdaki mevcut beş sayı, aynı 106.735 kayıt toplamına ulaşsa da açıklanan
aralıklarla yeniden üretilememektedir. Saniye farkına dayalı, sınırları açık
hesap aşağıdaki sonucu verir:

| Aralık (dakika) | Doğrulanmış olay sayısı |
|---|---:|
| `[0,15]` | 11.290 |
| `(15,30]` | 8.875 |
| `(30,60]` | 28.909 |
| `(60,120]` | 37.639 |
| `>120` | 20.022 |

Toplam 106.735'tir. Medyan 65 dakika, en yakın-sıra yöntemiyle 95. yüzdelik
297 dakika ve maksimum 27,75 gündür. Sunumdaki grafiğin sütunları bu değerlerle
değiştirilmelidir. Hazır LaTeX satırı `slide_patch/availability_lag_corrected.tex`
dosyasındadır.

## Otomatik denetim

```text
python -m unittest discover -s tests -v
```

Yeni testler sunumdaki doğrulanabilir iddiaları gerçek Demo v2.2 veritabanına
karşı kontrol eder. Bir sayı veya sorgu değişirse test başarısız olur; bu,
sunum-kod-veri uyumsuzluğunu görünür kılar.
