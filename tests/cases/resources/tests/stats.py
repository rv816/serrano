import json
from avocado.models import DataCategory
from avocado.events.models import Log
from .base import BaseTestCase


class StatsResourceTestCase(BaseTestCase):
    def setUp(self):
        super(StatsResourceTestCase, self).setUp()

    def test_get(self):
        response = self.client.get('/api/stats/',
                                   HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('_links' in json.loads(response.content))


class CountStatsResourceTestCase(BaseTestCase):
    def setUp(self):
        super(CountStatsResourceTestCase, self).setUp()

    def test_get(self):
        response = self.client.get('/api/stats/counts/',
                                   HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(json.loads(response.content), [{
            'app_name': 'tests',
            'model_name': 'project',
            'verbose_name': 'Project',
            'verbose_name_plural': 'Projects',
            'count': 3,
        }, {
            'app_name': 'tests',
            'model_name': 'title',
            'verbose_name': 'Title',
            'verbose_name_plural': 'Titles',
            'count': 7,
        }])

    def test_post_aware(self):
        context = {
            'field': 'tests.title.salary',
            'operator': 'gt',
            'value': 15000,
        }

        response = self.client.post('/api/stats/counts/?aware=true',
                                   data=json.dumps({'context': context}),
                                   content_type='application/json',
                                   HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(json.loads(response.content), [{
            'app_name': 'tests',
            'model_name': 'project',
            'verbose_name': 'Project',
            'verbose_name_plural': 'Projects',
            'count': 3,
        }, {
            'app_name': 'tests',
            'model_name': 'title',
            'verbose_name': 'Title',
            'verbose_name_plural': 'Titles',
            'count': 3,
        }])