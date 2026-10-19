# BMED4702 demo eklentisini mevcut PyCharm projesine kurma

Bu paket yeni bir proje oluşturmaz. ZIP içeriğini mevcut
`BMED4702_SQL_Python_AI_FHIR_Labs` klasörüne çıkarın. Paket `data/` klasörünü ve
veritabanını içermez; mevcut `data/mimic_demo.sqlite` dosyanızı silmez ya da
değiştirmez.

## En kısa çalışma yolu

1. PyCharm'da mevcut projeyi açın.
2. `run_table_counts_demo.py` dosyasını açıp yeşil çalıştırma üçgenine basın.
3. Sonra `run_all_demos.py` dosyasını aynı şekilde çalıştırın.
4. Sonuçları `output/presentation_demos/` altındaki en yeni klasörde açın.

Altı konu çalıştırıcısı:

- `run_table_counts_demo.py`
- `run_missingness_demo.py`
- `run_availability_demo.py`
- `run_join_demo.py`
- `run_event_trace_demo.py`
- `run_null_logic_demo.py`

Ana çalıştırıcı `run_all_demos.py`, yedi SQL sorgusunun tamamını yürütür ve aynı
çıktı klasöründe `provenance.json` ile `ai_evidence_packet.json` üretir.

## Beklenen klasörler

```text
BMED4702_SQL_Python_AI_FHIR_Labs/
  data/mimic_demo.sqlite
  sql/01_table_counts.sql ... 09_null_three_valued_logic.sql
  src/presentation_demos.py
  run_table_counts_demo.py
  run_all_demos.py
```

## Otomatik kontrol

PyCharm Terminal içinde proje kökünde çalıştırın:

```text
python -m unittest discover -s tests -v
```

`OK` görülürse sorgular Demo v2.2 için beklenen sayıları üretmiştir.
