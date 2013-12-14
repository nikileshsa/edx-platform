"""
This views handles the advanced course setting of being able to export
course xml to a git repository.
"""

import logging
import StringIO

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django_future.csrf import ensure_csrf_cookie

from .access import has_access
from edxmako.shortcuts import render_to_response
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
import contentstore.management.commands.git_export as git_export

log = logging.getLogger(__name__)


@ensure_csrf_cookie
@login_required
def push_to_lms(request, org, course, name):
    """
    This method serves up the 'Push to LMS' page
    """
    location = Location('i4x', org, course, 'course', name)
    if not has_access(request.user, location):
        raise PermissionDenied()
    course_module = modulestore().get_item(location)
    failed = False

    log.debug('push_to_lms course_module=%s', course_module)

    msg = ""
    if 'action' in request.GET and course_module.giturl:
        # Hijack the logger to display helpful information to the user and do the push
        output = StringIO.StringIO()
        export_log_handler = logging.StreamHandler(output)
        export_log_handler.setLevel(logging.DEBUG)

        git_export.log.old_level = git_export.log.level
        git_export.log.setLevel(logging.DEBUG)
        git_export.log.addHandler(export_log_handler)

        retval = git_export.export_to_git(
            course_module.id,
            course_module.giturl,
            request.user
        )
        if retval != 0:
            failed = True
        msg = output.getvalue()

        # Undo hijacks
        git_export.log.setLevel(git_export.log.old_level)
        git_export.log.removeHandler(export_log_handler)

    return render_to_response('push_to_lms.html', {
        'context_course': course_module,
        'msg': msg,
        'failed': failed,
    })
