import time
from django.core import mail
from django.test import TestCase
from django.http import HttpRequest
from django.contrib.sessions.backends.file import SessionStore
from django.contrib.auth.models import User
from avocado.models import DataQuery
from serrano.forms import ContextForm, QueryForm, ViewForm


class ContextFormTestCase(TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.request.session = SessionStore()
        self.request.session.save()

    def test_session(self):
        form = ContextForm(self.request, {})
        self.assertTrue(form.is_valid())
        self.assertFalse(form.count_needs_update)
        instance = form.save()
        self.assertEqual(instance.user, None)
        self.assertEqual(instance.session_key, self.request.session.session_key)
        self.assertEqual(instance.count, None)

    def test_user(self):
        user = User.objects.create_user(username='test', password='test')
        self.request.user = user

        form = ContextForm(self.request, {})
        self.assertTrue(form.is_valid())
        instance = form.save()
        self.assertEqual(instance.user, user)
        self.assertEqual(instance.session_key, None)


class ViewFormTestCase(TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.request.session = SessionStore()
        self.request.session.save()

    def test_session(self):
        form = ViewForm(self.request, {})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(form.instance.user, None)
        self.assertEqual(form.instance.session_key, self.request.session.session_key)

    def test_user(self):
        user = User.objects.create_user(username='test', password='test')
        self.request.user = user

        form = ViewForm(self.request, {})
        self.assertTrue(form.is_valid())
        self.assertFalse(form.count_needs_update)
        instance = form.save()
        self.assertEqual(instance.user, user)
        self.assertEqual(instance.session_key, None)
        self.assertEqual(instance.count, None)


class QueryFormTestCase(TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.request.session = SessionStore()
        self.request.session.save()

    def test_session(self):
        form = QueryForm(self.request, {})
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(form.instance.user, None)
        self.assertEqual(form.instance.session_key, self.request.session.session_key)

    def test_user(self):
        user = User.objects.create_user(username='test', password='test')
        self.request.user = user

        form = QueryForm(self.request, {})
        self.assertTrue(form.is_valid())
        self.assertFalse(form.count_needs_update)
        instance = form.save()
        self.assertEqual(instance.user, user)
        self.assertEqual(instance.session_key, None)

    def test_with_email(self):
        previous_user_count = User.objects.count()

        form = QueryForm(self.request, {'usernames_or_emails': 'email1@email.com'})
        instance = form.save()
        self.assertEqual(instance.shared_users.count(), 1)

        # Since save sends email asyncronously, wait for a while for the mail
        # to go through.
        time.sleep(5)

        # Make sure the user was created
        self.assertEqual(previous_user_count + 1, User.objects.count())

        # Make sure the mail was sent
        self.assertEqual(len(mail.outbox), 1)

        # Make sure the recipient list is correct
        self.assertSequenceEqual(mail.outbox[0].to, ['email1@email.com'])

    def test_with_user(self):
        user = User.objects.create_user(username='user_1',
            email='user_1@email.com')
        user.save()

        form = QueryForm(self.request, {'usernames_or_emails': 'user_1'})
        instance = form.save()
        self.assertEqual(instance.shared_users.count(), 1)

        # Since save sends email asyncronously, wait for a while for the mail
        # to go through.
        time.sleep(5)

        # Make sure the email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Make sure the recipient list is correct
        self.assertSequenceEqual(mail.outbox[0].to, ['user_1@email.com'])

    def test_with_mixed(self):
        user = User.objects.create_user(username='user_1',
            email='user_1@email.com')
        user.save()

        previous_user_count = User.objects.count()

        form = QueryForm(self.request, {'usernames_or_emails': 'user_1, \
            valid@email.com, invalid+=email@fake@domain@com, '})
        instance = form.save()
        self.assertEqual(instance.shared_users.count(), 2)

        # Since save sends email asyncronously, wait for a while for the mail
        # to go through.
        time.sleep(5)

        # Make sure the user was created
        self.assertEqual(previous_user_count + 1, User.objects.count())

        # Make sure the mail was sent
        self.assertEqual(len(mail.outbox), 1)

        # Make sure the recipient list is correct
        self.assertSequenceEqual(mail.outbox[0].to, ['user_1@email.com',
            'valid@email.com'])

        # Remove a user from the list
        previous_user_count = User.objects.count()
        form = QueryForm(self.request, {'usernames_or_emails': 'user_1'},
            instance=instance)
        instance = form.save()
        self.assertEqual(instance.shared_users.count(), 1)

        # Since save sends email asyncronously, wait for a while for the mail
        # to go through.
        time.sleep(5)

        # Make sure the user count is unaffected
        self.assertEqual(previous_user_count, User.objects.count())

        # Make sure no email was generated as a result
        self.assertEqual(len(mail.outbox), 1)

    def test_no_commit(self):
        previous_user_count = User.objects.count()

        form = QueryForm(self.request,
            {'usernames_or_emails': 'email1@email.com'})
        instance = form.save(commit=False)

        # Since save sends email asyncronously, wait for a while for the mail
        # to go through.
        time.sleep(5)

        # The instance should not be saved and shared_users should be
        # inaccessible on the model instance because the commit flag was False.
        self.assertIsNone(instance.pk)
        self.assertRaises(ValueError, lambda: instance.shared_users)

        # Make sure no users were created and no email was sent
        self.assertEqual(previous_user_count, User.objects.count())
        self.assertEqual(len(mail.outbox), 0)

    def test_with_archive(self):
        previous_query_count = DataQuery.objects.count()

        form = QueryForm(self.request,
            {'usernames_or_emails': 'email@email.com'})
        instance = form.save(archive=True)

        # When passing the archive flag, we should see 2 new DataQuery models
        # in the DB. The one normally created when the commit flag is True
        # and another representing the archive of that model.
        self.assertEqual(previous_query_count + 2, DataQuery.objects.count())
