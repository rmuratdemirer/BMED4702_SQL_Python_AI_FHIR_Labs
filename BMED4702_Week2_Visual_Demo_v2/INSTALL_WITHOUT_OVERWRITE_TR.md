# Mevcut PyCharm projesine güvenli yerleştirme

Hedef proje:

```text
C:\2026-27 Academic Year\BMED 4702 MEDICAL INFORMATION SYSTEMS\BMED4702_SQL_Python_AI_FHIR_Labs
```

## Tek güvenli işlem

ZIP'i önce `Downloads` altında açın. Açılan paketteki şu klasörü bulun:

```text
BMED4702_Week2_Visual_Demo_v2
```

Bu klasörü **klasör olarak** mevcut proje ana klasörüne sürükleyin. Son görünüm:

```text
BMED4702_SQL_Python_AI_FHIR_Labs
├── .venv
├── data
├── output
├── BMED4702_Week1_Visual_Demo
└── BMED4702_Week2_Visual_Demo_v2   <- yeni ve bağımsız klasör
```

Windows "hedefte aynı adlı klasör var" derse işlemi durdurun. Bu uyarı,
Week 2 klasörünün daha önce kopyalandığını gösterir. `Değiştir` seçmeyin.

Bu kurulum `.venv`, `data`, `src`, `sql`, `tests`, Week 1 klasörü ve mevcut
çalışmalarınızın hiçbirini değiştirmez.

## PyCharm'da açma

Yeni proje oluşturmayın. PyCharm'ı kapatmayın. Sol taraftaki mevcut proje
ağacına sağ tıklayıp **Reload from Disk** seçin. Sonra:

```text
BMED4702_Week2_Visual_Demo_v2\run_week2_visual_demo.py
```

dosyasını açın. Kod alanında sağ tıklayıp **Run 'run_week2_visual_demo'** seçin.

Başarılı çalışma sonunda beş grafik, metin çıktıları ve şu klasör oluşur:

```text
output\week2_visual_demo
```
