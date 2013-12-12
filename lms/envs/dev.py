"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /mitx # The location of this repo
        /log  # Where we're going to write log files
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .common import *
from logsettings import get_logger_config

DEBUG = True
USE_I18N = True
# For displaying the dummy text, we need to provide a language mapping.
LANGUAGES = (
    ('eo', 'Esperanto'),
)
TEMPLATE_DEBUG = True


FEATURES['DISABLE_START_DATES'] = False
FEATURES['ENABLE_SQL_TRACKING_LOGS'] = True
FEATURES['SUBDOMAIN_COURSE_LISTINGS'] = False  # Enable to test subdomains--otherwise, want all courses to show up
FEATURES['SUBDOMAIN_BRANDING'] = True
FEATURES['FORCE_UNIVERSITY_DOMAIN'] = None		# show all university courses if in dev (ie don't use HTTP_HOST)
FEATURES['ENABLE_MANUAL_GIT_RELOAD'] = True
FEATURES['ENABLE_PSYCHOMETRICS'] = False    # real-time psychometrics (eg item response theory analysis in instructor dashboard)
FEATURES['ENABLE_INSTRUCTOR_ANALYTICS'] = True
FEATURES['ENABLE_SERVICE_STATUS'] = True
FEATURES['ENABLE_INSTRUCTOR_EMAIL'] = True     # Enable email for all Studio courses
FEATURES['REQUIRE_COURSE_EMAIL_AUTH'] = False  # Give all courses email (don't require django-admin perms)
FEATURES['ENABLE_HINTER_INSTRUCTOR_VIEW'] = True
FEATURES['ENABLE_INSTRUCTOR_BETA_DASHBOARD'] = True
FEATURES['MULTIPLE_ENROLLMENT_ROLES'] = True
FEATURES['ENABLE_SHOPPING_CART'] = True
FEATURES['AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING'] = True
FEATURES['ENABLE_S3_GRADE_DOWNLOADS'] = True

FEEDBACK_SUBMISSION_EMAIL = "dummy@example.com"

WIKI_ENABLED = True

LOGGING = get_logger_config(ENV_ROOT / "log",
                            logging_env="dev",
                            local_loglevel="DEBUG",
                            dev_env=True,
                            debug=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ENV_ROOT / "db" / "edx.db",
    }
}

CACHES = {
    # This is the cache used for most things.
    # In staging/prod envs, the sessions also live here.
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_loc_mem_cache',
        'KEY_FUNCTION': 'util.memcache.safe_key',
    },

    # The general cache is what you get if you use our util.cache. It's used for
    # things like caching the course.xml file for different A/B test groups.
    # We set it to be a DummyCache to force reloading of course.xml in dev.
    # In staging environments, we would grab VERSION from data uploaded by the
    # push process.
    'general': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'KEY_PREFIX': 'general',
        'VERSION': 4,
        'KEY_FUNCTION': 'util.memcache.safe_key',
    },

    'mongo_metadata_inheritance': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/mongo_metadata_inheritance',
        'TIMEOUT': 300,
        'KEY_FUNCTION': 'util.memcache.safe_key',
    }
}


XQUEUE_INTERFACE = {
    "url": "https://sandbox-xqueue.edx.org",
    "django_auth": {
        "username": "lms",
        "password": "***REMOVED***"
    },
    "basic_auth": ('anant', 'agarwal'),
}

# Make the keyedcache startup warnings go away
CACHE_TIMEOUT = 0

# Dummy secret key for dev
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'


COURSE_LISTINGS = {
    'default': ['BerkeleyX/CS169.1x/2012_Fall',
                'BerkeleyX/CS188.1x/2012_Fall',
                'HarvardX/CS50x/2012',
                'HarvardX/PH207x/2012_Fall',
                'MITx/3.091x/2012_Fall',
                'MITx/6.002x/2012_Fall',
                'MITx/6.00x/2012_Fall'],
    'berkeley': ['BerkeleyX/CS169/fa12',
                 'BerkeleyX/CS188/fa12'],
    'harvard': ['HarvardX/CS50x/2012H'],
    'mit': ['MITx/3.091/MIT_2012_Fall'],
    'sjsu': ['MITx/6.002x-EE98/2012_Fall_SJSU'],
}


SUBDOMAIN_BRANDING = {
    'sjsu': 'MITx',
    'mit': 'MITx',
    'berkeley': 'BerkeleyX',
    'harvard': 'HarvardX',
    'openedx': 'OpenedX',
    'edge': 'Edge'
}

# List of `university` landing pages to display, even though they may not
# have an actual course with that org set
VIRTUAL_UNIVERSITIES = []

# Organization that contain other organizations
META_UNIVERSITIES = {'UTx': ['UTAustinX']}

COMMENTS_SERVICE_KEY = "PUT_YOUR_API_KEY_HERE"

############################## Course static files ##########################
if os.path.isdir(DATA_DIR):
    # Add the full course repo if there is no static directory
    STATICFILES_DIRS += [
        # TODO (cpennington): When courses are stored in a database, this
        # should no longer be added to STATICFILES
        (course_dir, DATA_DIR / course_dir)
        for course_dir in os.listdir(DATA_DIR)
        if (os.path.isdir(DATA_DIR / course_dir) and
            not os.path.isdir(DATA_DIR / course_dir / 'static'))
    ]
    # Otherwise, add only the static directory from the course dir
    STATICFILES_DIRS += [
        # TODO (cpennington): When courses are stored in a database, this
        # should no longer be added to STATICFILES
        (course_dir, DATA_DIR / course_dir / 'static')
        for course_dir in os.listdir(DATA_DIR)
        if (os.path.isdir(DATA_DIR / course_dir / 'static'))
    ]


################################# mitx revision string  #####################

MITX_VERSION_STRING = os.popen('cd %s; git describe' % REPO_ROOT).read().strip()

############################ Open ended grading config  #####################

OPEN_ENDED_GRADING_INTERFACE = {
    'url' : 'http://127.0.0.1:3033/',
    'username' : 'lms',
    'password' : 'abcd',
    'staff_grading' : 'staff_grading',
    'peer_grading' : 'peer_grading',
    'grading_controller' : 'grading_controller'
}

############################## LMS Migration ##################################
FEATURES['ENABLE_LMS_MIGRATION'] = True
FEATURES['ACCESS_REQUIRE_STAFF_FOR_COURSE'] = False   # require that user be in the staff_* group to be able to enroll
FEATURES['USE_XQA_SERVER'] = 'http://xqa:server@content-qa.edX.mit.edu/xqa'

INSTALLED_APPS += ('lms_migration',)

LMS_MIGRATION_ALLOWED_IPS = ['127.0.0.1']

################################ OpenID Auth #################################

FEATURES['AUTH_USE_OPENID'] = True
FEATURES['AUTH_USE_OPENID_PROVIDER'] = True
FEATURES['BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH'] = True

INSTALLED_APPS += ('external_auth',)
INSTALLED_APPS += ('django_openid_auth',)

OPENID_CREATE_USERS = False
OPENID_UPDATE_DETAILS_FROM_SREG = True
OPENID_SSO_SERVER_URL = 'https://www.google.com/accounts/o8/id'  # TODO: accept more endpoints
OPENID_USE_AS_ADMIN_LOGIN = False

OPENID_PROVIDER_TRUSTED_ROOTS = ['*']

######################## MIT Certificates SSL Auth ############################

FEATURES['AUTH_USE_MIT_CERTIFICATES'] = True

################################# CELERY ######################################

# By default don't use a worker, execute tasks as if they were local functions
CELERY_ALWAYS_EAGER = True

################################ DEBUG TOOLBAR ################################

INSTALLED_APPS += ('debug_toolbar',)
MIDDLEWARE_CLASSES += ('django_comment_client.utils.QueryCountDebugMiddleware',
                       'debug_toolbar.middleware.DebugToolbarMiddleware',)
INTERNAL_IPS = ('127.0.0.1',)

DEBUG_TOOLBAR_PANELS = (
   'debug_toolbar.panels.version.VersionDebugPanel',
   'debug_toolbar.panels.timer.TimerDebugPanel',
   'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
   'debug_toolbar.panels.headers.HeaderDebugPanel',
   'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
   'debug_toolbar.panels.sql.SQLDebugPanel',
   'debug_toolbar.panels.signals.SignalDebugPanel',
   'debug_toolbar.panels.logger.LoggingPanel',

#  Enabling the profiler has a weird bug as of django-debug-toolbar==0.9.4 and
#  Django=1.3.1/1.4 where requests to views get duplicated (your method gets
#  hit twice). So you can uncomment when you need to diagnose performance
#  problems, but you shouldn't leave it on.
#  'debug_toolbar.panels.profiling.ProfilingDebugPanel',
)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False
}

#################### FILE UPLOADS (for discussion forums) #####################

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = ENV_ROOT / "uploads"
MEDIA_URL = "/static/uploads/"
STATICFILES_DIRS.append(("uploads", MEDIA_ROOT))
FILE_UPLOAD_TEMP_DIR = ENV_ROOT / "uploads"
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

FEATURES['AUTH_USE_SHIB'] = True
FEATURES['RESTRICT_ENROLL_BY_REG_METHOD'] = True

########################### PIPELINE #################################

PIPELINE_SASS_ARGUMENTS = '--debug-info --require {proj_dir}/static/sass/bourbon/lib/bourbon.rb'.format(proj_dir=PROJECT_ROOT)

########################## ANALYTICS TESTING ########################

ANALYTICS_SERVER_URL = "http://127.0.0.1:9000/"
ANALYTICS_API_KEY = ""

##### segment-io  ######

# If there's an environment variable set, grab it and turn on Segment.io
SEGMENT_IO_LMS_KEY = os.environ.get('SEGMENT_IO_LMS_KEY')
if SEGMENT_IO_LMS_KEY:
    FEATURES['SEGMENT_IO_LMS'] = True

###################### Payment ##############################3

CC_PROCESSOR['CyberSource']['SHARED_SECRET'] = os.environ.get('CYBERSOURCE_SHARED_SECRET', '')
CC_PROCESSOR['CyberSource']['MERCHANT_ID'] = os.environ.get('CYBERSOURCE_MERCHANT_ID', '')
CC_PROCESSOR['CyberSource']['SERIAL_NUMBER'] = os.environ.get('CYBERSOURCE_SERIAL_NUMBER', '')
CC_PROCESSOR['CyberSource']['PURCHASE_ENDPOINT'] = os.environ.get('CYBERSOURCE_PURCHASE_ENDPOINT', '')


########################## USER API ########################
EDX_API_KEY = None


####################### Shoppingcart ###########################
FEATURES['ENABLE_SHOPPING_CART'] = True

#####################################################################
# Lastly, see if the developer has any local overrides.
try:
    from .private import *      # pylint: disable=F0401
except ImportError:
    pass

# Configuration data to support 'microsites' that are bound - in middleware - 
# based on incoming hostname domain
# For local test purposes, let's define a "OpenedX" subdomain brand
MICROSITE_CONFIGURATION = {
    'OpenedX': {
        # A display string that will be displayed when user visits the microsite. Given that we are handling this
        # in configuration, it will not be localizable
        'platform_name': 'Open edX',
        # override for USE_CUSTOM_THEME set otherwhere in config
        'USE_CUSTOM_THEME': True,
        # override for THEME_NAME set otherwhere in config
        'THEME_NAME': 'openedx',
        # allow for microsite to load in an additional .css file that can override
        # the platform's default CSS definitions. For example, swap out the background image.
        'css_overrides_file': 'microsites/openedx/css/openedx.css',
        # what logo file to display, note that we shouldn't check in trademarked logos
        # into the repository, so these images will have to be deployed/managed outside of
        # code pushes
        'logo_image_file': 'open_edX_logo.png',       
        # what filter to use when displaying the course catalog on the landing page     
        'course_org_filter': 'CDX',
        # email from field on outbound emails
        'email_from_address': 'openedx@edx.org',
        'payment_support_email': 'openedx@edx.org',
        'email_templates': {
            'allowed_enroll': ('emails/enroll_email_allowedsubject.txt', 'emails/enroll_email_allowedmessage.txt'),
            'enrolled_enroll': ('emails/enroll_email_enrolledsubject.txt', 'emails/enroll_email_enrolledmessage.txt'),
            'allowed_unenroll': ('emails/unenroll_email_subject.txt', 'emails/unenroll_email_allowedmessage.txt'),
            'enrolled_unenroll': ('emails/unenroll_email_subject.txt', 'emails/unenroll_email_enrolledmessage.txt')
        },
        # override for ENABLE_MKTG_SITE set otherwhere in config
        'ENABLE_MKTG_SITE':  False,
        # setting to hide the "university partner" list on the landing page
        'show_university_partners': False,
        # These 4 following items define the template substitutions to use in the courseware pages
        'header_extra_file': None,
        'header_file': 'navigation.html',
        'google_analytics_file': 'google_analytics.html',
        'footer_file': 'openedx-footer.html',
        # This override is a HTML literal to put as the page footer, unfortunately this HTML becomes
        # non-localizable if we define in configuration. NOTE: This will take presendence over 'footer_file'
        'footer_html': '''
            <div class="wrapper wrapper-footer">
                <footer>
                    <div class="colophon">
                        <div class="colophon-about">
                            <p>Open edX is a non-profit created by founding partners Harvard and MIT whose mission is to bring the best of higher education to students of all ages anywhere in the world, wherever there is Internet access. Open edX's free online MOOCs are interactive and subjects include computer science, public health, and artificial intelligence.</p>
                        </div>
                    </div>
                    <div class="references">
                        <p class="copyright">&#169; 2013 edX, some rights reserved.</p>
                        <nav class="nav-legal">
                            <ul>
                        </nav>
                    </div>
                </footer>
            </div>
        ''',
        # this control whether the home header (the overlay) shows on the homepage
        # for example the overlay which says "The Future of Online Education", has the background image, as well as
        # the top-level promo video
        'show_home_header': False,
        # This controls whether the social sharing links of the course about page should be displayed
        'course_about_show_social_links': True,
        # This is the text on the course index page which is overlaid on top of the background image
        'course_index_overlay_text': 'Explore free courses from leading universities.',
        # This is the logo that displays in the overlay on top of the backgroundimage
        'course_index_overlay_logo_file': '/static/images/edx_bw.png'
    },
    'Edge': {
        # if set will render to different template in the index page
        # if not set, then the default index page will be rendered
        'university_profile_template': 'university_profile/edge.html',
    }
}
