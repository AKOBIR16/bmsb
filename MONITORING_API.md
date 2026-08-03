# 📊 Monitoring API

Barcha bolalar musiqa va san'at maktablari (BMSM) saytlarini bitta joydan
kuzatish uchun API. Maktablarning kontenti, faolligi va ma'lumotlari
qanchalik to'liq to'ldirilgani viloyat / tuman / tashkilot kesimida
qaytariladi.

- **Bazaviy manzil:** `https://api.e-bmsm.uz/api/monitoring/`
- **Test:** `https://test-api.e-bmsm.uz/api/monitoring/`
- **Swagger:** `/api/monitoring/swagger/` · **ReDoc:** `/api/monitoring/redoc/`
- **Avtorizatsiya:** talab qilinmaydi
- **`School` headeri:** **kerak emas.** Sayt API'sidan farqli o'laroq monitoring
  barcha maktablar kesimida ishlaydi ([SubdomainMiddleware](apps/main/middleware.py)
  da `/api/monitoring/` prefiksi chetlab o'tilgan).

---

## Ishga tushirish

### 1. Migratsiya

```bash
python manage.py migrate
```

Prod va dev serverlarda bu `entrypoint.sh` orqali avtomatik bajariladi.

> ⚠️ `makemigrations` ni o'ylamasdan ishga tushirmang: `0045` migratsiyasi
> `School.google_verification_code` maydonini qo'shadi, lekin `models.py` da
> u yo'q. Django buni ko'rib, ustunni **o'chiradigan** migratsiya yaratadi.

### 2. Viloyatlar

```bash
python manage.py seed_regions
```

O'zbekistonning 14 ta ma'muriy birligini SOATO kodlari bilan yozadi.
Qayta-qayta ishga tushirish xavfsiz — mavjudlariga tegmaydi.

### 3. Tumanlar

```bash
python manage.py seed_districts
```

Barcha tumanlar va viloyat bo'ysunuvidagi shaharlarni (jami 207 ta) tegishli
viloyatlariga biriktirib yozadi. Qayta ishga tushirish xavfsiz.
Bitta viloyat uchun: `--region toshkent-viloyati`. Tekshirish uchun: `--dry-run`.

> Hududiy bo'linish o'zgarib turadi. Ro'yxat
> [seed_districts.py](apps/main/management/commands/seed_districts.py) ning
> boshidagi `DISTRICTS` lug'atida — rasmiy ma'lumotnoma bilan solishtirib,
> kerak bo'lsa tahrirlang yoki admin panelda tuzating.

#### Muqobil: CSV dan import

Agar o'z ro'yxatingiz bo'lsa (Excel'dan `CSV UTF-8` sifatida saqlanadi):

```csv
region,name,soato
Toshkent viloyati,Chirchiq,1727401
fargona-viloyati,Rishton,1730409
```

`region` ustuniga viloyat **nomi yoki slugi** yozilishi mumkin.

```bash
python manage.py import_districts tumanlar.csv --dry-run   # avval tekshirib olish
python manage.py import_districts tumanlar.csv
```

### 4. Maktablarni hududga biriktirish

```csv
domain,region,district
mk1,Toshkent viloyati,Chirchiq
mk2,fargona-viloyati,Rishton
```

```bash
python manage.py import_school_locations maktablar.csv --dry-run
python manage.py import_school_locations maktablar.csv
```

Komanda oxirida hududi belgilanmagan maktablar sonini aytadi. Bitta-yarim
maktabni admin panelda ham tahrirlash mumkin (`Maktablar → Kontaktlar`).

### 5. Sayt holatini tekshirish (offline maktablar)

```bash
python manage.py check_schools_online
```

Har bir maktab saytiga so'rov yuboradi va natijani `School.is_online`,
`last_checked_at`, `last_online_at` maydonlariga yozadi. Cron orqali
ishga tushiriladi:

```cron
*/10 * * * * cd /path/to/bmsb && python manage.py check_schools_online >> /var/log/bmsm-online.log 2>&1
```

Docker ichida:

```bash
docker compose -f prod.yml exec -T web python manage.py check_schools_online
```

Parametrlar: `--timeout 10` (sekund), `--workers 16` (parallel so'rovlar),
`--domain mk1` (faqat bitta maktab, bir necha marta berilishi mumkin).

Sayt manzili `{domain}.{MONITORING_SITE_BASE_DOMAIN}` shaklida yig'iladi.
Standart qiymat `e-bmsm.uz`, `.env` orqali o'zgartiriladi:

```bash
MONITORING_SITE_BASE_DOMAIN=e-bmsm.uz
MONITORING_SITE_SCHEME=https
```

---

## Umumiy filtrlar

Quyidagilar deyarli barcha endpointlarda ishlaydi:

| Parametr | Tavsif |
|---|---|
| `region` | Viloyat `id` yoki `slug` (`?region=toshkent-viloyati`) |
| `district` | Tuman `id` yoki `slug` |
| `school` | Maktab subdomeni. Vergul bilan bir nechta: `?school=mk1,mk2` |
| `is_online` | `true` / `false` — sayt javob berayotganlari |
| `include_inactive` | `true` bo'lsa, `is_active=false` yozuvlar ham qo'shiladi |
| `date_from`, `date_to` | `YYYY-MM-DD`. Faqat lenta va dinamikada |
| `type` | Kontent turlari, vergul bilan: `?type=news,announcement` |
| `limit`, `offset` | Sahifalash. Standart `limit=50`, maksimum `500` |

Filtrlar **birga ishlaydi**: `region` berilsa o'sha viloyatdagi barcha
maktablar, ustiga `district` qo'shilsa toraytiriladi, `school` berilsa
faqat o'sha tashkilot qoladi.

Noto'g'ri qiymatda `400` va tushunarli xabar qaytadi:

```json
{ "region": "Viloyat topilmadi: mavjud-emas" }
```

---

## Endpointlar

### `GET /regions/` — viloyatlar va tumanlar

Kaskadli filtr (viloyat → tuman) uchun yagona so'rov. Sahifalanmaydi.

```json
[
  {
    "id": 1,
    "name": "Toshkent viloyati",
    "slug": "toshkent-viloyati",
    "soato": "1728",
    "school_count": 23,
    "districts": [
      { "id": 5, "name": "Chirchiq", "slug": "chirchiq", "soato": null, "school_count": 3 }
    ]
  }
]
```

---

### `GET /content-types/` — kontent turlari

`type` filtriga tushadigan qiymatlar. Frontendda filtr ro'yxatini
qo'lda yozib qo'ymaslik uchun.

```json
[
  { "key": "news",         "label": "Yangilik",       "is_post": true },
  { "key": "announcement", "label": "E'lon",          "is_post": true },
  { "key": "teacher",      "label": "Pedagog",        "is_post": false }
]
```

`is_post: false` — bu profil ma'lumoti (pedagoglar, rahbariyat,
yo'nalishlar). Ular postlar lentasiga tushmaydi, lekin sanoqlarda va
to'ldirilganlikda hisobga olinadi.

---

### `GET /overview/` — dashboard plitkalari

Filtrlar: `region`, `district`, `school`, `is_online`, `include_inactive`.

```json
{
  "total_schools": 300,
  "coverage_percent": 96.7,
  "posted_today": 143,
  "posted_today_percent": 47.7,
  "not_posted_today": 157,
  "stale_7_days": 25,
  "stale_30_days": 6,
  "offline_schools": 6,
  "active_percent": 89.6,
  "statuses": [
    { "status": "active",   "label": "Faol",   "count": 269 },
    { "status": "passive",  "label": "Passiv", "count": 25 },
    { "status": "critical", "label": "Kritik", "count": 6 }
  ]
}
```

| Maydon | Ma'nosi |
|---|---|
| `coverage_percent` | Kamida bitta post joylagan maktablar ulushi |
| `posted_today` | Bugun kamida bitta post joylagan maktablar |
| `stale_7_days` | 8–30 kun yangilanmaganlar (passiv) |
| `stale_30_days` | 30 kundan ortiq yangilanmaganlar yoki umuman posti yo'qlar |
| `offline_schools` | Sayti javob bermayotganlar (oxirgi tekshiruv bo'yicha) |
| `active_percent` | `statuses` dagi `active` ulushi — donut markazidagi raqam |

`stale_7_days` va `stale_30_days` **kesishmaydi**, shuning uchun
`active + passive + critical = total_schools`.

---

### `GET /timeseries/` — kunlik dinamika

Chiziqli grafik uchun. Sana berilmasa — oxirgi 30 kun. Oraliq eng ko'pi
bilan 366 kun.

`GET /timeseries/?date_from=2026-06-22&date_to=2026-07-20&region=1`

```json
[
  { "date": "2026-06-22", "posts": 58,  "active_schools": 41 },
  { "date": "2026-06-23", "posts": 152, "active_schools": 118 }
]
```

Postsiz kunlar ham nol qiymat bilan qaytadi — grafikda uzilish bo'lmaydi.

---

### `GET /posts/` — barcha postlar lentasi

Barcha maktablar va barcha kontent turlari bo'ylab yagona lenta.

`GET /posts/?region=toshkent-viloyati&type=news,announcement&date_from=2026-07-01&limit=20`

Qo'shimcha parametrlar: `search` (sarlavha bo'yicha),
`ordering` (`-created_at` standart, `created_at`, `updated_at`, `-updated_at`).

```json
{
  "count": 1843,
  "next": "https://api.e-bmsm.uz/api/monitoring/posts/?limit=20&offset=20",
  "previous": null,
  "results": [
    {
      "type": "news",
      "type_label": "Yangilik",
      "id": 412,
      "title": "Bahorgi konsert bo'lib o'tdi",
      "slug": "bahorgi-konsert",
      "view_count": 87,
      "created_at": "2026-07-25T14:32:11+05:00",
      "updated_at": "2026-07-25T14:32:11+05:00",
      "is_active": true,
      "school":   { "id": 12, "domain": "mk1", "name": "1-son BMSM" },
      "region":   { "id": 1, "name": "Toshkent viloyati", "slug": "toshkent-viloyati" },
      "district": { "id": 5, "name": "Chirchiq", "slug": "chirchiq" },
      "site_url": "https://mk1.e-bmsm.uz/news/bahorgi-konsert"
    }
  ]
}
```

`site_url` — postning maktab saytidagi manzili. Slugi yo'q turlar uchun
bo'lim sahifasiga olib boradi (masalan hujjatlar → `/official-documents`).

> **Cheklov:** lenta bo'ylab eng chuqur nuqta — 5000 yozuv
> (`offset + limit`). Undan narisi uchun sana yoki hudud bo'yicha
> toraytirish kerak. Chegaradan oshsa `400` qaytadi.

---

### `GET /schools/` — monitoring jadvali

Har bir maktab bo'yicha bitta qator. Qo'shimcha parametrlar:

| Parametr | Qiymatlar |
|---|---|
| `search` | Maktab nomi bo'yicha |
| `status` | `active`, `passive`, `critical` |
| `ordering` | `name`, `completeness_percent`, `posts_month`, `last_post_at`, `days_since_last_post`. Oldiga `-` qo'yilsa teskari |

```json
{
  "count": 300,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": 12,
      "domain": "mk1",
      "name": "1-son BMSM",
      "is_active": true,
      "is_online": true,
      "last_checked_at": "2026-07-27T09:10:00+05:00",
      "site_url": "https://mk1.e-bmsm.uz",
      "region":   { "id": 1, "name": "Toshkent viloyati", "slug": "toshkent-viloyati" },
      "district": { "id": 5, "name": "Chirchiq", "slug": "chirchiq" },
      "status": "active",
      "status_label": "Faol",
      "completeness_percent": 77,
      "activity": {
        "posts_today": 2,
        "posts_week": 8,
        "posts_month": 31,
        "last_post_at": "2026-07-20T13:36:00+05:00",
        "last_news_at": "2026-07-20T11:02:00+05:00",
        "days_since_last_post": 0,
        "last_login_at": "2026-07-20T13:36:00+05:00"
      },
      "content_counts": {
        "news": 133, "announcement": 45, "media-image": 24,
        "teacher": 21, "document": 22
      }
    }
  ]
}
```

`content_counts` da faqat **nolga teng bo'lmagan** turlar bo'ladi —
kalit yo'q bo'lsa, u tur bo'yicha kontent yo'q degani.

`last_login_at` — shu maktabga biriktirilgan adminlarning oxirgi tizimga
kirgan vaqti. Maktabga admin akkaunti biriktirilmagan bo'lsa `null`.

---

### `GET /schools/{domain}/` — maktab kartasi

`GET /schools/mk1/`

`/schools/` dagi barcha maydonlar, ustiga **`completeness_sections`**
qo'shiladi:

```json
{
  "domain": "mk1",
  "completeness_percent": 77,
  "completeness_sections": [
    {
      "key": "profile", "label": "Maktab profili", "weight": 20,
      "percent": 92.9,
      "missing": ["logo"]
    },
    {
      "key": "news", "label": "Yangiliklar", "weight": 15,
      "percent": 50.0, "count": 8, "target": 5,
      "last_at": "2026-06-01T10:00:00+05:00",
      "note": "Oxirgi 30 kun ichida yangi kontent joylanmagan"
    },
    {
      "key": "documents", "label": "Hujjatlar", "weight": 5,
      "percent": 0.0, "count": 0, "target": 1
    }
  ]
}
```

Maktab topilmasa `404`.

---

## Holat (status) qoidalari

Oxirgi post joylangan sanadan hisoblanadi:

| Status | Shart | Belgisi |
|---|---|---|
| `active` | oxirgi post ≤ 7 kun | Faol |
| `passive` | 8–30 kun | Kuzatuv ostida |
| `critical` | > 30 kun yoki umuman post yo'q | Kritik |

**Offline** — alohida o'lchov: sayt HTTP so'roviga javob bermayapti
(`is_online: false`). U status bilan kesishadi, ya'ni maktab bir vaqtda
`active` ham, offline ham bo'lishi mumkin.

Chegaralarni o'zgartirish: [apps/monitoring/constants.py](apps/monitoring/constants.py)
dagi `ACTIVE_MAX_DAYS` va `PASSIVE_MAX_DAYS`.

---

## To'ldirilganlik (completeness)

Umumiy foiz — bo'limlarning og'irlik bo'yicha o'rtachasi. Jami 100 ball:

| Bo'lim | Ball | Nima tekshiriladi |
|---|---|---|
| Maktab profili | 20 | 14 ta maydon: tavsif, tashkil topgan yili, sig'imi, o'quvchi/o'qituvchi soni, manzil, telefon, email, koordinatalar, logo, viloyat, tuman |
| Yangiliklar | 15 | Kamida 5 ta + oxirgi 30 kun ichida yangisi bo'lishi |
| Rahbariyat | 10 | Kamida 1 ta |
| Pedagoglar | 10 | Kamida 3 ta |
| Yo'nalishlar | 10 | Kamida 1 ta |
| Galereya | 10 | Kamida 10 ta rasm |
| Hujjatlar | 5 | Kamida 1 ta |
| O'quv reja | 5 | Kamida 1 ta (**fayli yuklangan**) |
| Xizmatlar | 5 | Madaniy xizmat / amaliy / tasviriy san'atdan kamida 1 ta |
| Resurslar | 5 | Fayl yoki video — kamida 1 ta |
| Maktab hayoti | 5 | Kamida 1 ta |

Nozik jihatlar:

- **`fresh_days` bo'lgan bo'limda ballning yarmi miqdorga, yarmi
  yangilanib turishiga beriladi.** Ya'ni 3 yil oldin 50 ta yangilik
  joylab tashlab qo'yilgan sayt 100% olmaydi.
- **Raqamli maydonlarda 0 "to'ldirilmagan" hisoblanadi** — maktab
  yaratilganda `capacity`, `student_count` va boshqalar 0 qilib
  qo'yiladi, ular bepul ball bermasligi kerak.
- **O'quv rejada faqat fayli borlari sanaladi** — maktab yaratilganda
  1–9 sinflar uchun 9 ta bo'sh yozuv avtomatik hosil bo'ladi.

Og'irliklar va mezonlar `COMPLETENESS_SECTIONS` da. O'zgartirish uchun
migratsiya kerak emas.

---

## Kontent turlari

| `type` | Model | Lentada |
|---|---|---|
| `news` | `news.News` (e'lon kategoriyasidan tashqari) | ✅ |
| `announcement` | `news.News` (e'lon kategoriyasi) | ✅ |
| `school-life` | `main.SchoolLife` | ✅ |
| `honor` | `main.Honors` | ✅ |
| `media-image` | `media.MediaImage` | ✅ |
| `document` | `main.Document` | ✅ |
| `vacancy` | `main.Vacancy` | ✅ |
| `resource-file` | `resource.ResourceFile` | ✅ |
| `resource-video` | `resource.ResourceVideo` | ✅ |
| `culture-service` | `service.CultureService` | ✅ |
| `culture-art` | `service.CultureArt` | ✅ |
| `fine-art` | `service.FineArt` | ✅ |
| `teacher` | `main.Teacher` | — |
| `staff` | `main.Staff` | — |
| `leader` | `main.Leader` | — |
| `direction` | `main.DirectionSchool` | — |
| `media-collection` | `media.MediaCollection` | — |
| `timetable` | `main.TimeTable` (fayli borlari) | — |
| `edu-info` | `main.EduInfo` | — |
| `faq` | `main.FAQ` | — |
| `banner` | `main.Banner` | — |

### "E'lonlar" qanday ajratiladi

Alohida model yo'q — e'lonlar `News` ning kategoriyasi orqali ajratiladi.
Kategoriya slugi `ANNOUNCEMENT_CATEGORY_SLUGS` ro'yxatidagilardan biri
bo'lishi kerak:

```python
ANNOUNCEMENT_CATEGORY_SLUGS = ('elonlar', 'e-lonlar', 'elon', 'announcements')
```

Maktablar boshqa nom ishlatgan bo'lsa, shu ro'yxatga qo'shiladi.
`news` turi e'lon kategoriyasidagilarni **chiqarib tashlaydi**, shuning
uchun ikkalasi qo'shilganda ikki marta sanalmaydi.

---

## Ma'lum cheklovlar

1. **Galereya videolari maktab kesimida hisoblanmaydi.** `media.MediaVideo`
   modelida `school` FK yo'q — videolar barcha maktablar uchun umumiy.
   Modelga FK qo'shilgach, `constants.py` da `media-video` uchun
   `school_path='school'` deb yozish kifoya, qolgan hamma joy avtomatik
   ishlaydi.
2. **Hudud ma'lumoti qo'lda to'ldiriladi.** Import qilinmaguncha
   `region`/`district` filtrlari bo'sh natija qaytaradi (xato bermaydi).
3. **Offline holati oxirgi tekshiruv paytidagi holat.** Cron sozlanmagan
   bo'lsa, `is_online` doim `true` bo'lib qoladi (standart qiymat).
4. **Kesh yo'q.** Har bir so'rov jonli hisoblanadi. 300 maktab uchun
   `/schools/` taxminan 35 ta agregat so'rov bajaradi. Yuk sezilarli
   oshsa, `/overview/` va `/timeseries/` javoblarini keshlash tavsiya
   etiladi.

---

## Yangi kontent turini qo'shish

Yagona manba — [apps/monitoring/constants.py](apps/monitoring/constants.py)
dagi `CONTENT_TYPES`. Bitta qator qo'shilsa, lenta ham, sanoqlar ham,
statistika ham uni avtomatik hisobga oladi:

```python
ContentType(
    key='tanlov',                    # API dagi `type` qiymati
    label="Tanlov",                  # ko'rsatiladigan nomi
    model='main.Competition',        # "app_label.ModelName"
    title_field='title',             # sarlavha maydoni
    school_path='school',            # maktabgacha bo'lgan yo'l, None bo'lsa hisobga olinmaydi
    slug_field='slug',               # ixtiyoriy
    view_count_field='view_count',   # ixtiyoriy
    site_path='/tanlovlar/{slug}',   # frontend manzili, ixtiyoriy
    is_post=True,                    # lentaga tushadimi
),
```

Model `BaseModel` dan meros olgan bo'lishi kerak (`created_at`,
`updated_at`, `is_active` maydonlari uchun).

To'ldirilganlikda ham hisobga olinishi kerak bo'lsa,
`COMPLETENESS_SECTIONS` ga bo'lim qo'shiladi va og'irliklar yig'indisi
100 bo'lib qolishi kuzatiladi.

---

## Loyihadagi fayllar

```
apps/monitoring/
├── constants.py              # kontent turlari, holat chegaralari, to'ldirilganlik qoidalari
├── filters.py                # so'rov parametrlarini o'qish va tekshirish
├── serializers.py            # javob formatlari
├── views.py                  # endpointlar
├── urls.py
└── services/
    ├── querysets.py          # umumiy filtrlash qatlami
    ├── feed.py               # postlar lentasi
    ├── stats.py              # sanoqlar, faollik, dinamika
    └── completeness.py       # to'ldirilganlik hisoblagichi

config/swagger/monitoring.py  # alohida Swagger sxemasi
apps/main/models.py           # Region, District + School dagi hudud va holat maydonlari
apps/main/management/commands/
├── seed_regions.py
├── seed_districts.py
├── import_districts.py
├── import_school_locations.py
└── check_schools_online.py
```
