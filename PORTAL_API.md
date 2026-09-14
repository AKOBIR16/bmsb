# 🌐 Portal API (e-bmsm.uz)

e-bmsm.uz bosh sayti uchun API: barcha bolalar musiqa va san'at maktablari
bitta joyda — katalog, xarita, yo'nalishlar, yangiliklar lentasi va reyting.

- **Bazaviy manzil:** `https://api.e-bmsm.uz/api/portal/`
- **Swagger:** `/api/portal/swagger/` · **ReDoc:** `/api/portal/redoc/`
- **Avtorizatsiya:** talab qilinmaydi (login yo'q)
- **`School` headeri:** **kerak emas** — `/api/portal/` prefiksi
  [SubdomainMiddleware](apps/main/middleware.py) da chetlab o'tilgan
- **Til:** `Accept-Language: uz | ru | en`. Tarjima kiritilmagan maydonlarda
  o'zbekcha qiymat qaytadi.

---

## Ishga tushirish

```bash
pip install -r requirements/base.txt   # yangi paket: nh3 (HTML tozalash)
python manage.py migrate
```

Migratsiyalar:

| Migratsiya | Nima qiladi |
|---|---|
| `main.0047_school_portal_fields_direction_details` | `School`: `school_type`, `admission_open`, `employee_count`. `Direction`: `category`, `short_description`, `description`, `duration_years` |
| `news.0005_news_is_important_news_portal_category` | `News`: `portal_category`, `is_important` |
| `portal.0001_initial` | Portal modellari (quyida) |

> ⚠️ `makemigrations` ni o'ylamasdan ishga tushirmang — u
> `School.google_verification_code` ustunini o'chiradigan migratsiya yasaydi
> (batafsil: [MONITORING_API.md](MONITORING_API.md)). 0047 dan bu amal
> ataylab olib tashlangan.

Keyin admin panelda (faqat superadmin, **Portal (e-bmsm.uz)** bo'limi):

1. **Portal sozlamalari** — manzil, telefon, email, ish vaqti, xaritadagi nuqta,
   ijtimoiy tarmoqlar. Bitta yozuv.
2. **Yo'nalishlar** (`Main → Yo'nalishlar`) — har biriga toifa, qisqacha tavsif,
   tavsif va ta'lim muddatini kiriting. Katalog va yo'nalish oynasi shu
   maydonlardan to'ladi.
3. **Savol-javoblar** — "Aloqa" sahifasidagi FAQ.
4. **Reyting** — pastdagi bo'limga qarang.

Maktab adminlari o'z maktabi uchun `Maktab turi`, `Qabul ochiqmi?` va
`Xodimlar soni` ni, har bir yangilik uchun `Portal toifasi` ni to'ldiradi.

---

## Admin panel: Portal bo'limi

Faqat **superadmin** ko'radi. "Maktab Admin" guruhiga huquq berib yuborilsa
ham maktab adminlari kira olmaydi.

| Bo'lim | Vazifasi |
|---|---|
| Reyting davrlari | Yil bo'yicha davr. `E'lon qilingan` belgilanmaguncha portalda ko'rinmaydi |
| Maktablar reytingi | 5 mezon bo'yicha ball (0–100). Ro'yxatning o'zida tahrirlanadi |
| Portal yangiliklari | Barcha maktablar yangiliklari: portal toifasini tuzatish va **Muhim** belgisini qo'yish |
| Murojaatlar | "Aloqa" sahifasidan kelgan murojaatlar. `Ko'rib chiqildi` belgisi |
| Savol-javoblar | FAQ, tartib raqami bilan |
| Portal sozlamalari | Aloqa ma'lumotlari |

### Reyting ballarini kiritish

1. **Reyting davrlari** → yangi davr (masalan `2026`).
2. Ro'yxatda davrni belgilab, **"Barcha faol maktablar uchun bo'sh qatorlar
   yaratish"** amalini bajaring.
3. Davr qatoridagi **"N ta — ballarni kiritish"** havolasi orqali ballar
   sahifasiga o'ting. Ballar ro'yxatning o'zida kiritiladi, pastdagi **Saqlash**
   bilan saqlanadi. Viloyat bo'yicha filtrlab bo'lib-bo'lib to'ldirish mumkin.
4. Tayyor bo'lgach davrni **E'lon qilingan** qiling.

Qoidalar ([constants.py](apps/portal/constants.py)):

| Mezon | Kalit | Og'irlik |
|---|---|---|
| Ta'lim sifati | `quality` | 30% |
| O'quvchi yutuqlari | `achievement` | 25% |
| Pedagog salohiyati | `teachers` | 20% |
| Infratuzilma | `infrastructure` | 15% |
| Ijodiy faollik | `creative` | 10% |

- Umumiy ball saqlashda hisoblanadi. **Birorta mezon bo'sh bo'lsa, umumiy ball
  ham bo'sh** va maktab reytingga tushmaydi — ballarni bosqichma-bosqich
  kiritish mumkin.
- O'rin respublika bo'yicha. Bir xil ball — bir xil o'rin (1, 2, 2, 4).
- Dinamika (`trend`) oldingi e'lon qilingan davrdagi o'rin bilan solishtiriladi.
- Daraja: 90+ A'lo, 85+ Yuqori, 80+ Yaxshi, qolgani Barqaror.

---

## Endpointlar

Ro'yxatlarda sahifalash `limit` / `offset`. Noto'g'ri parametrda `400`:

```json
{ "status_code": 400, "errors": [{ "error": "region_invalid", "message": "Viloyat topilmadi: nope" }] }
```

**Qidiruv** (`search`) o'zbekcha yozuvlarga moslangan: `Farg'ona`, `Farg‘ona`,
`Fargʻona`, `Fargona` bir xil topiladi, kirillcha so'rov (`Фарғона`) ham ishlaydi.

### `GET /stats/` — portal raqamlari

```json
{
  "schools": 266, "regions": 14, "districts": 167, "directions": 14,
  "students": 27871, "teachers": 5372, "employees": 0,
  "admission_open": 0, "located_schools": 17, "news": 322
}
```

`students`/`teachers` — maktablar kiritgan sonlar yig'indisi. `located_schools` —
xaritada ko'rsatsa bo'ladigan (koordinatasi to'g'ri) maktablar. 10 daqiqa keshlanadi.

### `GET /regions/` — viloyatlar va tumanlar

`[{ id, name, slug, soato, school_count, districts: [{ id, name, slug, school_count }] }]`.
Katalog filtrlari (`search`, `direction`, `type`, `admission`, `students_min`,
`students_max`, `has_location`) berilsa, faqat mos maktablar sanaladi — xarita
katalog bilan bir xil sonlarni ko'rsatadi. `region`/`district` bu yerda filtr
emas: xarita barcha hududlarning sonini bilishi kerak. 10 daqiqa keshlanadi.

### `GET /schools/` — maktablar katalogi

| Parametr | Qiymat |
|---|---|
| `search` | Nomi, subdomeni, manzili |
| `region`, `district` | id yoki slug |
| `direction` | Yo'nalish slugi, vergul bilan bir nechta |
| `type` | `bmsm`, `specialized` |
| `admission` | `open`, `closed` |
| `students_min`, `students_max` | O'quvchilar soni oralig'i |
| `has_location` | `true` — faqat xaritaga chiqadiganlar |
| `ordering` | `name`, `-name`, `-students`, `students`, `-teachers`, `-founded`, `founded` |
| `limit` | Standart 12, ko'pi bilan 500 (xarita uchun `limit=500`) |

```json
{
  "id": 43, "domain": "samarqand15", "name": "Samarqand viloyati 15-son BMSM",
  "school_type": "bmsm", "school_type_label": "Bolalar musiqa va san'at maktabi",
  "logo": "https://cdn.e-bmsm.uz/media/...", "site_url": "https://samarqand15.e-bmsm.uz",
  "region": { "id": 8, "name": "Samarqand viloyati", "slug": "samarqand-viloyati" },
  "district": { "id": 103, "name": "Kattaqo'rg'on", "slug": "kattaqorgon" },
  "admission_open": null, "address": "...", "latitude": null, "longitude": null,
  "student_count": 230, "teacher_count": 36, "employee_count": null,
  "capacity": 150, "founded_year": 1966,
  "directions": [{ "slug": "tasviriy-sanat", "name": "Tasviriy san'at" }]
}
```

- `admission_open: null` — maktab qabul holatini kiritmagan (belgi ko'rsatilmaydi).
- `latitude`/`longitude` faqat O'zbekiston hududiga tushsa qaytadi. Bazadagi
  `0,0`, `10,10` kabi qiymatlar `null`.
- Raqamli maydonlarda `0` ham `null` — maktab yaratilganda ular 0 qilib qo'yiladi.

### `GET /schools/{domain}/` — maktab pasporti

Katalogdagi maydonlar, ustiga: `description` (tozalangan HTML), `short_description`,
`phone_number`, `email`, ijtimoiy tarmoqlar, `class_count`, `news_count`,
`latest_news` (4 ta), yo'nalishlar sanog'i bilan va joriy reyting:

```json
"rating": { "year": 2026, "rank": 12, "total": 169, "score": 91.4, "level": "excellent", "level_label": "A'lo" }
```

Reytingda bo'lmasa `rating: null`.

### `GET /directions/` — yo'nalishlar

Parametrlar: `category` (`instrument`, `vocal`, `visual`, `stage`), `search`,
`ordering` (`-schools` standart, `-students`, `-teachers`, `name`).

```json
{
  "total_schools": 266,
  "categories": [{ "key": "instrument", "label": "Cholg'u ijrochiligi", "count": 6 }],
  "count": 14,
  "results": [{
    "slug": "fortepiano-mutaxassisligi", "name": "Fortepiano",
    "category": "instrument", "category_label": "Cholg'u ijrochiligi",
    "short_description": null, "duration_years": null, "icon": "...", "background_image": "...",
    "school_count": 96, "student_count": 4005, "teacher_count": 540, "school_share": 36.1
  }]
}
```

`school_share` — shu yo'nalish mavjud maktablar ulushi (%). 10 daqiqa keshlanadi.

### `GET /directions/{slug}/` — yo'nalish tafsiloti

Ustiga: `description`, `subjects` va `instruments` (maktablarda eng ko'p
uchraydiganlari, `school_count` bilan), `schools` (shu yo'nalish bor maktablar).

### `GET /news/` — yangiliklar lentasi

| Parametr | Qiymat |
|---|---|
| `search` | Sarlavha |
| `region`, `district` | id yoki slug |
| `school` | Subdomen, vergul bilan bir nechta |
| `category` | `qabul`, `tanlov`, `festival`, `talim`, `loyiha`, `tadbir` |
| `important` | `true` / `false` |
| `year`, `month` | Yil, oy (1–12) |
| `ordering` | `-date` (standart), `date`, `-views`, `title`, `-title` |
| `limit` | Standart 12, ko'pi bilan 60 |

Element: `id, title, slug, image, excerpt, category {key, label} | null,
is_important, view_count, created_at, school {domain, name, logo, region, district, site_url}, site_url`.

### `GET /news/meta/` — lenta filtrlari

`{ total, important, categories: [{key, label, count}], years: [2026, 2025] }`.

### `GET /news/{id}/` — yangilik

To'liq `content` (HTML) va `related` (shu maktabning 4 ta boshqa yangiligi).
Har bir so'rov `view_count` ni 1 ga oshiradi.

`content` va maktabning `description` i `nh3` bilan tozalanadi
([apps/portal/html.py](apps/portal/html.py)): portal 266 ta maktab adminining
matnini asosiy domenda ko'rsatadi, shuning uchun `script`, `on*` atributlar,
`javascript:` havolalar va inline stillar olib tashlanadi.

### `GET /rating/` — maktablar reytingi

| Parametr | Qiymat |
|---|---|
| `period` | Yil. Berilmasa — eng so'nggi e'lon qilingan davr |
| `search`, `region`, `district`, `type` | Filtrlar |
| `level` | `excellent`, `high`, `good`, `stable` |
| `trend` | `up`, `down`, `same`, `new` |
| `ordering` | `rank` (standart), `score`, `name`, `-quality`, `-achievement`, `-teachers`, `-infrastructure`, `-creative` |
| `limit` | Masalan bosh sahifadagi TOP-10 uchun |

```json
{
  "period": { "year": 2026, "title": "...", "previous_year": 2025 },
  "periods": [{ "year": 2026, "title": "..." }],
  "criteria": [{ "key": "quality", "label": "Ta'lim sifati", "weight": 30 }],
  "levels": [{ "key": "excellent", "label": "A'lo", "min": 90 }],
  "summary": { "count": 169, "average": 83.3, "max": 95.2, "excellent_count": 24, "improved_count": 84 },
  "count": 21,
  "results": [{
    "rank": 1, "previous_rank": 27, "rank_change": 26, "trend": "up",
    "score": 95.2, "level": "excellent", "level_label": "A'lo",
    "quality": 96.0, "achievement": 95.0, "teachers": 94.0, "infrastructure": 96.0, "creative": 95.0,
    "school": { "domain": "...", "name": "...", "school_type": "bmsm", "region": {}, "district": {}, "student_count": 230 }
  }]
}
```

`summary` filtrlardan qat'i nazar butun davr bo'yicha. E'lon qilingan davr
bo'lmasa `period: null` va bo'sh `results`.

### `GET /settings/` · `GET /faqs/`

Portal aloqa ma'lumotlari (`work_days: [1..7]`, `work_start`, `work_end` —
"Hozir ochiq/yopiq" holati uchun) va savol-javoblar. Sozlamalar kiritilmagan
bo'lsa `/settings/` `null` qaytaradi.

### `POST /appeals/` — murojaat yuborish

```json
{
  "full_name": "Aliyev Vali", "phone_number": "+998 90 123 45 67",
  "email": "vali@mail.uz", "topic": "portal",
  "message": "Murojaat matni...", "agreement": true
}
```

- `topic`: `portal`, `school`, `admission`, `education`, `technical`, `suggestion`, `other`
- Telefon 12 xonali O'zbekiston raqami (`90 123 45 67` ham qabul qilinadi),
  `+998 90 123 45 67` ko'rinishida saqlanadi.
- F.I.Sh. ≥ 3, matn 10–1000 belgi, `agreement: true` majburiy.
- Bitta IP dan soatiga 5 ta murojaat.
- Javob: `201 { "id": 12, "message": "Murojaatingiz qabul qilindi" }`.

---

## Loyihadagi fayllar

```
apps/portal/
├── constants.py      # reyting mezonlari, darajalar, murojaat mavzulari
├── models.py         # PortalSettings, PortalFAQ, Appeal, RatingPeriod, SchoolRating, PortalNews (proxy)
├── admin.py          # faqat superadmin
├── search.py         # tutuq belgisiga befarq qidiruv
├── services.py       # sanoqlar, reyting jadvali
├── filters.py        # so'rov parametrlari
├── html.py           # maktablar kiritgan HTML ni tozalash (nh3)
├── serializers.py
├── views.py
├── urls.py
└── tests.py

config/swagger/portal.py   # alohida Swagger sxemasi
```
