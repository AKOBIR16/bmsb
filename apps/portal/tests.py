from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from apps.main.models import Region, School
from apps.news.models import Category, News
from apps.portal.html import clean_html
from apps.portal.models import Appeal, RatingPeriod, SchoolRating
from apps.portal.search import loose_pattern


def make_school(domain, **extra):
    return School.objects.create(domain=domain, name=extra.pop('name', domain), slug=domain, **extra)


def rate(period, school, value):
    return SchoolRating.objects.create(
        period=period, school=school,
        quality=value, achievement=value, teachers=value, infrastructure=value, creative=value,
    )


class ScoreTests(TestCase):
    def test_score_is_weighted_sum(self):
        period = RatingPeriod.objects.create(year=2026, is_published=True)
        rating = SchoolRating.objects.create(
            period=period, school=make_school('mk1'),
            quality=100, achievement=80, teachers=60, infrastructure=40, creative=20,
        )
        # 30*100 + 25*80 + 20*60 + 15*40 + 10*20 = 7000 -> 70.00
        self.assertEqual(rating.score, Decimal('70.00'))

    def test_score_stays_empty_until_every_criterion_is_filled(self):
        period = RatingPeriod.objects.create(year=2026, is_published=True)
        rating = SchoolRating.objects.create(period=period, school=make_school('mk1'), quality=90)
        self.assertIsNone(rating.score)


class CleanHtmlTests(TestCase):
    def test_scripts_handlers_and_inline_styles_are_removed(self):
        dirty = (
            '<p style="font-family: Times" onclick="steal()">Matn <strong>qalin</strong></p>'
            '<script>alert(1)</script><a href="javascript:alert(1)">havola</a>'
            '<img src="https://cdn.e-bmsm.uz/a.jpg" alt="rasm" onerror="steal()">'
        )
        clean = clean_html(dirty)
        for fragment in ('script', 'onclick', 'onerror', 'javascript:', 'style='):
            self.assertNotIn(fragment, clean)
        self.assertIn('<strong>qalin</strong>', clean)
        self.assertIn('src="https://cdn.e-bmsm.uz/a.jpg"', clean)


class SearchTests(TestCase):
    def test_apostrophe_variants_and_cyrillic_match(self):
        make_school('fargona1', name="Farg‘ona viloyati 1-son BMSM")
        for query in ("fargona", "Farg'ona", "фарғона"):
            with self.subTest(query=query):
                pattern = loose_pattern(query)
                self.assertTrue(School.objects.filter(name_uz__iregex=pattern).exists())

    def test_blank_query_builds_no_pattern(self):
        self.assertIsNone(loose_pattern("   "))


class PortalApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.region = Region.objects.create(name="Samarqand viloyati", slug="samarqand-viloyati")
        self.school = make_school('samarqand1', region=self.region, latitude=Decimal('39.65'), longitude=Decimal('66.96'))
        self.hidden = make_school('yopiq', is_active=False)
        self.bad_coords = make_school('xato', latitude=Decimal('10'), longitude=Decimal('10'))

    def test_works_without_school_header_and_hides_inactive_schools(self):
        response = self.client.get('/api/portal/schools/', {'limit': 50})
        self.assertEqual(response.status_code, 200)
        domains = {row['domain'] for row in response.data['results']}
        self.assertIn('samarqand1', domains)
        self.assertNotIn('yopiq', domains)

    def test_invalid_coordinates_are_not_exposed(self):
        response = self.client.get('/api/portal/schools/xato/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['latitude'])

        located = self.client.get('/api/portal/schools/', {'has_location': 'true'})
        self.assertEqual([row['domain'] for row in located.data['results']], ['samarqand1'])

    def test_region_filter_accepts_slug(self):
        response = self.client.get('/api/portal/schools/', {'region': 'samarqand-viloyati'})
        self.assertEqual([row['domain'] for row in response.data['results']], ['samarqand1'])

    def test_region_counts_follow_catalog_filters(self):
        make_school('samarqand2', region=self.region, admission_open=True)
        self.school.admission_open = False
        self.school.save()

        def samarqand_count(**params):
            cache.clear()
            response = self.client.get('/api/portal/regions/', params)
            return next(row['school_count'] for row in response.data if row['slug'] == 'samarqand-viloyati')

        self.assertEqual(samarqand_count(), 2)
        self.assertEqual(samarqand_count(admission='open'), 1)
        self.assertEqual(samarqand_count(has_location='true'), 1)
        # The region itself is not a filter here: the map needs every region's count
        self.assertEqual(samarqand_count(region='boshqa'), 2)

    def test_news_feed_skips_inactive_schools(self):
        for school in (self.school, self.hidden):
            category = Category.objects.create(school=school, name="Yangiliklar", slug="yangiliklar")
            News.objects.create(
                school=school, category=category, title=f"{school.domain} xabari",
                slug=f"{school.domain}-xabari", content="<p>Matn</p>", portal_category='tanlov',
            )
        response = self.client.get('/api/portal/news/', {'category': 'tanlov'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['school']['domain'], 'samarqand1')

    def test_rating_ranks_ties_and_trend(self):
        old = RatingPeriod.objects.create(year=2025, is_published=True)
        new = RatingPeriod.objects.create(year=2026, is_published=True)
        second = make_school('samarqand2', region=self.region)
        third = make_school('samarqand3', region=self.region)

        rate(old, self.school, 95)
        rate(old, second, 80)
        rate(new, self.school, 85)
        rate(new, second, 90)
        rate(new, third, 85)

        response = self.client.get('/api/portal/rating/')
        self.assertEqual(response.data['period']['year'], 2026)
        rows = {row['school']['domain']: row for row in response.data['results']}
        self.assertEqual(rows['samarqand2']['rank'], 1)
        self.assertEqual(rows['samarqand2']['trend'], 'up')
        # 85 va 85 - ikkalasi ham 2-o'rinda
        self.assertEqual(rows['samarqand1']['rank'], 2)
        self.assertEqual(rows['samarqand3']['rank'], 2)
        self.assertEqual(rows['samarqand1']['trend'], 'down')
        self.assertEqual(rows['samarqand3']['trend'], 'new')

    def test_unpublished_period_is_hidden(self):
        RatingPeriod.objects.create(year=2026, is_published=False)
        response = self.client.get('/api/portal/rating/')
        self.assertIsNone(response.data['period'])
        self.assertEqual(response.data['results'], [])

    def test_appeal_normalises_phone_and_requires_consent(self):
        payload = {
            'full_name': "Aliyev Vali", 'phone_number': '90 123 45 67',
            'topic': 'portal', 'message': "Portal bo'yicha savolim bor.",
        }
        rejected = self.client.post('/api/portal/appeals/', {**payload, 'agreement': False}, format='json')
        self.assertEqual(rejected.status_code, 400)

        accepted = self.client.post('/api/portal/appeals/', {**payload, 'agreement': True}, format='json')
        self.assertEqual(accepted.status_code, 201)
        self.assertEqual(Appeal.objects.get().phone_number, '+998 90 123 45 67')
