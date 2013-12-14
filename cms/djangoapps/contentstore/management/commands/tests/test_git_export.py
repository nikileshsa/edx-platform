"""
Test the ability to export courses to xml from studio using command
"""

import copy
import os
import shutil
import subprocess
from uuid import uuid4

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test.utils import override_settings

from contentstore.tests.utils import CourseTestCase
import contentstore.management.commands.git_export as git_export

FEATURES_WITH_PUSH_TO_LMS = settings.FEATURES.copy()
FEATURES_WITH_PUSH_TO_LMS['ENABLE_PUSH_TO_LMS'] = True
TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
@override_settings(FEATURES=FEATURES_WITH_PUSH_TO_LMS)
class TestGitExport(CourseTestCase):
    """
    Excercise the git_export django management command with various inputs.
    """

    @classmethod
    def tearDownClass(cls):
        """Delete all the artifacts we created"""
        super(TestGitExport, cls).tearDownClass()
        shutil.rmtree(git_export.GIT_REPO_EXPORT_DIR)
        shutil.rmtree('{0}/test_bare.git'.format(
            os.path.abspath(settings.TEST_ROOT)))

    def setUp(self):
        """
        Create/reinitialize bare repo and folders needed
        """
        super(TestGitExport, self).setUp()

        try:
            os.mkdir(git_export.GIT_REPO_EXPORT_DIR)
        except OSError:
            pass

        self.bare_repo_dir = '{0}/test_bare.git'.format(
            os.path.abspath(settings.TEST_ROOT))
        try:
            os.mkdir(self.bare_repo_dir)
        except OSError:
            pass

        bare_repo_dir = '{0}/test_bare.git'.format(
            os.path.abspath(settings.TEST_ROOT)
        )
        subprocess.call(['git', '--bare', 'init', ], cwd=bare_repo_dir)

    def _delete_repo(self):
        """
        Delete the test cloned repo
        """
        shutil.rmtree(git_export.GIT_REPO_EXPORT_DIR)
        os.mkdir(git_export.GIT_REPO_EXPORT_DIR)

    def test_command(self):
        """
        Test that the command interface works
        """
        with self.assertRaises(SystemExit) as ex:
            self.assertRaisesRegexp(CommandError, 'This script requires.*',
                                    call_command('git_export', 'blah', 'blah', 'blah'))
        self.assertEqual(ex.exception.code, 1)

        with self.assertRaises(SystemExit) as ex:
            self.assertRaisesRegexp(CommandError, 'This script requires.*',
                                    call_command('git_export'))
        self.assertEqual(ex.exception.code, 1)

        # Send bad url to get course not exported
        with self.assertRaises(SystemExit) as ex:
            self.assertRaisesRegexp(CommandError, 'Course was not exported.*',
                                    call_command('git_export', 'foo', 'silly'))
        self.assertEqual(ex.exception.code, 1)

    def test_bad_git_url(self):
        """
        Test several bad URLs for validation
        """
        self.assertEqual(git_export.GIT_EXPORT_URL_BAD,
                         git_export.export_to_git('', 'Sillyness'))

        self.assertEqual(git_export.GIT_EXPORT_URL_BAD,
                         git_export.export_to_git('', 'http://blah'))

        self.assertEqual(git_export.GIT_EXPORT_URL_NO_AUTH,
                         git_export.export_to_git('', 'http://blah.git'))

    def test_bad_git_repos(self):
        """
        Test invalid git repos
        """
        self.assertFalse(os.path.isdir('{}/test_repo'.format(git_export.GIT_REPO_EXPORT_DIR)))
        # Test bad clones
        self.assertEqual(
            git_export.GIT_EXPORT_CANNOT_PULL,
            git_export.export_to_git('foo/blah/100',
                                     'https://user:blah@example.com/r.git')
        )
        self.assertFalse(os.path.isdir('{}/test_repo'.format(git_export.GIT_REPO_EXPORT_DIR)))

        # Setup good repo with bad course to test xml export
        self.assertEqual(
            git_export.GIT_EXPORT_XML_EXPORT_FAIL,
            git_export.export_to_git('foo/blah/100', 'file://{0}'.format(self.bare_repo_dir))
        )

        # Test bad git remote after successful clone
        self.assertEqual(
            git_export.GIT_EXPORT_CANNOT_PULL,
            git_export.export_to_git('foo/blah/100', 'https://user:blah@example.com/r.git')
        )

        self._delete_repo()

    def test_bad_course_id(self):
        """
        Test valid git url, but bad course.
        """
        self.assertEqual(
            git_export.GIT_EXPORT_BAD_COURSE,
            git_export.export_to_git('', 'file://{0}'.format(self.bare_repo_dir), '', '/blah')
        )
        self._delete_repo()

    def test_git_ident(self):
        """
        Test valid course with and without user specified.
        """
        retval = git_export.export_to_git(
            self.course.id,
            'file://{0}'.format(self.bare_repo_dir),
            'enigma'
        )
        self.assertEqual(0, retval)
        expect_string = '{0}|{1}\n'.format(
            git_export.GIT_EXPORT_DEFAULT_IDENT['name'],
            git_export.GIT_EXPORT_DEFAULT_IDENT['email']
        )
        cwd = os.path.abspath(git_export.GIT_REPO_EXPORT_DIR / 'test_bare')
        git_log = subprocess.check_output(['git', 'log', '-1', '--format=%an|%ae', ], cwd=cwd)
        self.assertEqual(expect_string, git_log)

        # Make changes to course so there is something commit
        self.populateCourse()
        retval = git_export.export_to_git(
            self.course.id,
            'file://{0}'.format(self.bare_repo_dir),
            self.user.username
        )
        self.assertEqual(0, retval)
        expect_string = '{0}|{1}\n'.format(
            self.user.username,
            self.user.email,
        )
        git_log = subprocess.check_output(['git', 'log', '-1', '--format=%an|%ae', ], cwd=cwd)
        self.assertEqual(expect_string, git_log)

    def test_no_change(self):
        """
        Test response if there are no changes
        """
        retval = git_export.export_to_git(
            'i4x://{0}'.format(self.course.id),
            'file://{0}'.format(self.bare_repo_dir)
        )
        self.assertEqual(0, retval)
        retval = git_export.export_to_git(
            self.course.id, 'file://{0}'.format(self.bare_repo_dir))
        self.assertEqual(git_export.GIT_EXPORT_CANNOT_COMMIT, retval)
