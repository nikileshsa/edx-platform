"""
This command exports a course from CMS to a git repository.
"""

import logging
from optparse import make_option
import os
import subprocess
from urlparse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.translation import ugettext as _

from xmodule.contentstore.django import contentstore
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_exporter import export_to_xml

log = logging.getLogger(__name__)

GIT_REPO_EXPORT_DIR = getattr(settings, 'GIT_REPO_EXPORT_DIR',
                              '/edx/var/edxapp/export_course_repos')
GIT_EXPORT_DEFAULT_IDENT = getattr(settings, 'GIT_EXPORT_DEFAULT_IDENT',
                                   {'name': 'STUDIO_PUSH_TO_LMS',
                                    'email': 'STUDIO_PUSH_TO_LMS@example.com'})
GIT_EXPORT_NO_EXPORT_DIR = -1
GIT_EXPORT_URL_BAD = -2
GIT_EXPORT_URL_NO_AUTH = -3
GIT_EXPORT_CANNOT_PULL = -4
GIT_EXPORT_XML_EXPORT_FAIL = -5
GIT_EXPORT_CANNOT_COMMIT = -6
GIT_EXPORT_BAD_COURSE = -7


def export_to_git(course_loc, repo, user='', rdir=None):
    """Export a course to git."""
    # pylint: disable=R0915

    if course_loc.startswith('i4x://'):
        course_loc = course_loc[6:]

    if not os.path.isdir(GIT_REPO_EXPORT_DIR):
        log.error(_("Path {0} doesn't exist, please create it, "
                    "or configure a different path with "
                    "GIT_REPO_EXPORT_DIR").format(GIT_REPO_EXPORT_DIR))
        return GIT_EXPORT_NO_EXPORT_DIR

    # Check for valid writable git url
    if not repo.endswith('.git') or not (
            repo.startswith('http:') or
            repo.startswith('https:') or
            repo.startswith('file:')):
        log.warn(_('Non writable git url provided: {}. Expecting something '
                   'like git@github.com:mitocw/edx4edx_lite.git').format(repo))
        return GIT_EXPORT_URL_BAD

    # Check for username and password if using http[s]
    if repo.startswith('http:') or repo.startswith('https:'):
        parsed = urlparse(repo)
        if parsed.username is None or parsed.password is None:
            log.error(_('If using http urls, you must provide the username '
                        'and password in the url. Similar to '
                        'https://user:pass@github.com/user/course.'))
            return GIT_EXPORT_URL_NO_AUTH
    if rdir:
        rdir = os.path.basename(rdir)
    else:
        rdir = repo.rsplit('/', 1)[-1].rsplit('.git', 1)[0]

    log.debug("rdir = %s", rdir)

    # Pull or clone repo before exporting to xml
    # and update url in case origin changed.
    rdirp = '{0}/{1}'.format(GIT_REPO_EXPORT_DIR, rdir)
    if os.path.exists(rdirp):
        log.info(_('directory already exists, doing a git reset and pull '
                   'instead of git clone'))
        cwd = '{0}/{1}'.format(GIT_REPO_EXPORT_DIR, rdir)
        # Get current branch
        cmd = ['git', 'rev-parse', '--abbrev-ref', 'HEAD', ]
        branch = subprocess.check_output(cmd, cwd=os.path.abspath(cwd)).strip('\n')
        cmds = [
            ['git', 'remote', 'set-url', 'origin', repo, ],
            ['git', 'fetch', 'origin', ],
            ['git', 'reset', '--hard', 'origin/{0}'.format(branch), ],
            ['git', 'pull', ],
        ]
    else:
        cmds = [['git', 'clone', repo, ], ]
        cwd = GIT_REPO_EXPORT_DIR

    cwd = os.path.abspath(cwd)
    cmd_out = ''
    for cmd in cmds:
        log.debug(_('Command was: {0}. Working directory was: {1}').format(' '.join(cmd), cwd))
        try:
            cmd_out += subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            log.exception(_('Unable to update git repository. Output is: {0}'.format(cmd_out)))
            return GIT_EXPORT_CANNOT_PULL
    log.debug(cmd_out)

    # export course as xml before commiting and pushing
    try:
        location = CourseDescriptor.id_to_location(course_loc)
    except ValueError:
        log.exception(_('Bad course location provided'))
        return GIT_EXPORT_BAD_COURSE

    root_dir = os.path.dirname(rdirp)
    course_dir = os.path.splitext(os.path.basename(rdirp))[0]
    try:
        export_to_xml(modulestore('direct'), contentstore(), location,
                      root_dir, course_dir, modulestore())
    except (EnvironmentError, AttributeError):
        log.exception(_('Unable to export course to xml.'))
        return GIT_EXPORT_XML_EXPORT_FAIL

    # Now that we have fresh xml exported, set identity, add
    # everything to git, commit, and push.
    ident = {}
    try:
        user = User.objects.get(username=user)
        ident['name'] = user.username
        ident['email'] = user.email
    except User.DoesNotExist:
        # That's ok, just use default ident
        ident = GIT_EXPORT_DEFAULT_IDENT
    time_stamp = timezone.now()
    cwd = os.path.abspath(rdirp)
    commit_msg = '({0}) Export from Studio at {1}'.format(user, time_stamp)
    try:
        cmd_out += subprocess.check_output(['git', 'config', 'user.email', ident['email'], ],
                                           cwd=cwd, stderr=subprocess.STDOUT)
        cmd_out += subprocess.check_output(['git', 'config', 'user.name', ident['name'], ],
                                           cwd=cwd, stderr=subprocess.STDOUT)
        cmd_out += subprocess.check_output(['git', 'add', '.'],
                                           cwd=cwd, stderr=subprocess.STDOUT)
        cmd_out += subprocess.check_output(['git', 'commit', '-a', '-m', commit_msg],
                                           cwd=cwd, stderr=subprocess.STDOUT)
        cmd_out += subprocess.check_output(['git', 'push', '-q', ],
                                           cwd=cwd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        log.exception(_('Unable to commit or push changes. Output is: {0}').format(cmd_out))
        return GIT_EXPORT_CANNOT_COMMIT

    log.debug(cmd_out)
    return 0


class Command(BaseCommand):
    """
    Take a course from studio and export it to a git repository.
    """

    option_list = BaseCommand.option_list + (
        make_option('--user', '-u', dest='user',
                    help='Add a user to the commit message.'),
        make_option('--repo_dir', '-r', dest='repo',
                    help='Specify existing git repo directory.'),
    )

    help = _('Take the specified course and attempt to '
             'export it to a git repository\n. Course directory '
             'must already be a git repository. Usage: '
             ' git_export <course_loc> <git_url>')

    def handle(self, *args, **options):
        """
        Checks arguments and runs export function if they are good
        """

        if len(args) != 2:
            raise CommandError(_('This script requires exactly two arguments: '
                                 'course_loc and git_url'))

        retval = export_to_git(
            args[0], args[1],
            options.get('user', ''),
            options.get('rdir', None))

        if retval != 0:
            raise CommandError(_('Course was not exported, check log output '
                                 'for details'))
