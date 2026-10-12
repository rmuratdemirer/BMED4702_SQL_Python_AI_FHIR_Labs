# React ve TypeScript kurulum ve entegrasyon notu

## Kısa karar

React ve TypeScript işletim sistemine ayrı masaüstü programları olarak kurulmaz.
Arayüz laboratuvarını çalıştıracak bilgisayarda Node.js bulunur. `npm install`
komutu `package.json` içindeki React, TypeScript, Vite ve diğer paketleri yalnızca
proje klasöründeki `node_modules` dizinine indirir.

SQL ve Python laboratuvarı için Node.js gerekmez. React arayüz laboratuvarı için
gerekir.

## Önerilen yazılım ayrımı

| Ders etkinliği | Gerekli yazılım |
| --- | --- |
| SQLite ve Python laboratuvarı | Python 3.11 veya üzeri ve PyCharm |
| PyCharm içinden görsel SQL konsolu | PyCharm Pro Database Tools veya DB Browser for SQLite |
| React ve TypeScript arayüzü | Node.js ve proje içi npm paketleri |
| Tek IDE ile bütün sistem | PyCharm Pro |
| İki IDE ile çalışma | PyCharm backend ve WebStorm frontend |

PyCharm Pro; Python, JavaScript, TypeScript, React ve veritabanı araçlarını aynı
projede kullanabilir. PyCharm sürümünde JavaScript ve TypeScript özellikleri yoksa
Python backend PyCharm'da, React frontend WebStorm'da açılabilir.

## Kurulacak tek sistem bileşeni

Node.js LTS kurulmalıdır. Güncel Vite sürümü Node.js 20.19 veya 22.12 ve üzerini
gerektirir. Kurulumdan sonra kontrol:

```bash
node --version
npm --version
```

React veya TypeScript'i global kurmak gerekli değildir. Hazırlanmış proje için:

```bash
cd frontend
npm install
npm run dev
```

`npm install`, kilit dosyasındaki sürümleri proje içine kurar. Bu yaklaşım tüm
öğrencilerin aynı bağımlılık sürümlerini kullanmasını sağlar.

Yeni ve boş bir React TypeScript projesi yalnızca eğitmen tarafından oluşturulacaksa:

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm run dev
```

Öğrenciler hazırlanmış projeyi kullanırken `npm create` komutunu çalıştırmamalıdır;
yalnızca `npm install` ve `npm run dev` yeterlidir.

## Katmanların görevleri

```text
MIMIC-IV Demo CSV
        |
        v
SQLite teaching database
        |
        v
Python SQL and validation layer
        |
        v
FastAPI typed endpoints
        |
        v
React and TypeScript interface
        |
        +--> creatinine chart
        +--> evidence and provenance panel
        +--> FHIR Observation view
        `--> guarded natural language query screen
```

SQL sorguları yalnızca Python backend içinde çalışır. React doğrudan SQLite
dosyasına erişmez. React yalnız FastAPI'nin doğrulanmış JSON yanıtlarını alır.

## TypeScript neden kullanılıyor

TypeScript, API ile arayüz arasındaki sözleşmeyi görünür yapar:

```typescript
export type CreatinineEvidence = {
  event_count: number;
  minimum: number;
  maximum: number;
  unit: "mg/dL";
  mean_availability_minutes: number;
  interpretation_boundary: string;
};
```

Bu tür tanımı geliştirme sırasında yanlış alan adlarını ve beklenmeyen null
değerlerini yakalamaya yardım eder. Ancak ağdan gelen JSON'u tek başına doğrulamaz;
runtime şema doğrulaması yine gereklidir.

## Derste önerilen çalıştırma sırası

Birinci terminal:

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

İkinci terminal:

```bash
cd frontend
npm install
npm run dev
```

Tarayıcı `http://localhost:5173` adresini açar. React, örneğin
`http://localhost:8000/api/evidence/creatinine` uç noktasından veri alır.

## Ders planı kararı

- İlk SQL ve Python laboratuvarında React kurulumu zorunlu tutulmamalıdır.
- React ve TypeScript kurulumu arayüz haftasından önce tamamlanmalıdır.
- Ders sırasında paket indirmek yerine önceden hazırlanmış proje ve kilit dosyası
  dağıtılmalıdır.
- Eğitmen bilgisayarında uçtan uca demo; öğrenci bilgisayarında önce çekirdek SQL
  ve Python görevi çalıştırılmalıdır.

## Kaynaklar

- React installation and build tools: https://react.dev/learn/build-a-react-app-from-scratch
- Vite getting started: https://vite.dev/guide/
- TypeScript installation: https://www.typescriptlang.org/download/
- PyCharm React support: https://www.jetbrains.com/help/pycharm/react.html
