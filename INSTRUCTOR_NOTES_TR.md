# Eğitmen kısa notu

## SQL nereye kuruluyor?

Bu laboratuvarda PostgreSQL veya MySQL sunucusu kurulmaz. SQLite veritabanı tek bir dosyadır: `data/mimic_demo.sqlite`.

PyCharm iki farklı erişim yolu sağlar:

1. Python kodu `sqlite3.connect(...)` ile dosyayı açar ve SQL çalıştırır.
2. PyCharm Database penceresi aynı dosyaya görsel olarak bağlanır ve bir SQL konsolu açar.

İki yol aynı veriyi kullanır. Öğrenci önce SQL konsolunda sorguyu inceler, sonra Python ile otomatikleştirir.

## Provenance nedir?

Provenance, bir veri ürününün soy kütüğüdür. Yalnızca "CSV'den geldi" demek yeterli değildir. Şu soruların yanıtı kaydedilir:

- Hangi veri dosyası ve sürümü kullanıldı?
- Dosyanın hash değeri neydi?
- Hangi SQL sorgusu ve parametreler çalıştı?
- Hangi Python dosyası ve sürümü kullanıldı?
- Çıktı ne zaman üretildi?
- Hangi kişi veya yazılım etkinlikten sorumluydu?

W3C PROV yaklaşımında üç temel sınıf vardır:

- **Entity:** veritabanı, SQL dosyası, CSV sonuç, grafik.
- **Activity:** sorgulama, doğrulama, grafik üretme.
- **Agent:** öğrenci, eğitmen, Python programı veya kurum.

`output/provenance.json` bu yapıyı somutlaştırır.

## AI nasıl birleştiriliyor?

AI ham tabloyu sorgulamaz ve klinik karar üretmez. Akış şöyledir:

```text
SQLite -> doğrulanmış SQL -> Python evidence_summary.json -> AI açıklaması -> sayısal doğrulama
```

Bu yapı, metinden SQL üreten EHRSQL ve kod çalıştıran EHRAgent çalışmalarının eğitim düzeyinde güvenli bir karşılığıdır. İlk hafta AI yalnızca açıklayıcı katmandır. İlerleyen haftalarda öğrenci doğal dil sorusundan aday SQL üretebilir; ancak sorgu çalıştırılmadan önce izin verilen tablolar, satır limiti, salt-okunur bağlantı ve beklenen row-grain testleri uygulanmalıdır.

## Doğal dil SQL modülü nasıl korunuyor?

`run_safe_nl_sql.py` önce sorudan bir aday SQL üretir; aday doğrudan
çalıştırılmaz. Tek sorgu ve salt SELECT kuralı, tehlikeli sözcük denetimi,
SQLite authorizer izin listesi, salt-okunur URI, `query_only`, satır sınırı ve
zaman aşımı birlikte uygulanır. Yetkisiz bir kolonun SELECT ile istenmesi bile
reddedilir. Bütün karar `output/query_audit.json` içine yazılır.

## FHIR laboratuvarının kritik öğretim noktası

Kaynak alan ile hedef FHIR alanı her zaman bire bir değildir:

- `fluid=Blood` olduğu için serum/plazma kodu 2160-0 yerine kan kreatinin LOINC
  kodu 38483-4 kullanılır;
- MIMIC zamanı saat dilimi taşımadığı için seçilen ofset bir varsayımdır ve
  açıkça kaydedilir;
- sonuç statüsü kaynakta bulunmadığından `final` uydurulmaz ve
  `Observation.status=unknown` kullanılır;
- `charttime` klinik olay zamanı, `storetime` ise yayımlanma/kullanılabilirlik
  zamanı olarak ayrı korunur.
