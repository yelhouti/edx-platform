from common.djangoapps.student.models import CourseEnrollment, CourseOverview
from edx_ace.recipient import Recipient
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.features.calendar_sync.message_types import CalendarSync
from openedx.features.calendar_sync.tasks import send_calendar_sync_email


def compose_calendar_sync_email_context(course: CourseOverview, update=False):
    """
    Construct all the required params for the calendar
    sync email through celery task
    """

    course_name = course.display_name
    if update:
        calendar_sync_subject = 'Updates for Your {} Schedule'.format(course_name)
        calendar_sync_headline = 'Update Your Calendar'
        calendar_sync_body = 'Your assignment due dates for {} were recently adjusted. Update your calendar with ' \
                             'your new schedule to ensure that you stay on track!'.format(course_name)
    else:
        calendar_sync_subject = 'Stay on Track'
        calendar_sync_headline = 'Mark Your Calendar'
        calendar_sync_body = 'Sticking to a schedule is the best way to ensure that you successfully complete your ' \
                             'self-paced course. This schedule of assignment due dates for {} will help you stay on ' \
                             'track!'.format(course_name)
    return {
        'calendar_sync_subject': calendar_sync_subject,
        'calendar_sync_headline': calendar_sync_headline,
        'calendar_sync_body': calendar_sync_body,
    }


def compose_and_send_calendar_sync_email(user, course: CourseOverview, update=False):
    """
    Construct all the required params and send the activation email
    through celery task

    Arguments:
        user: current logged-in user
        course: course overview object
        update: if this should be an 'update' email
    """
    if not CourseEnrollment.objects.filter(user=user, course=course).exists():
        return

    calendar_sync_email_context = compose_calendar_sync_email_context(user, course, update)
    msg = CalendarSync().personalize(
        recipient=Recipient(user.username, user.email),
        language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
        user_context=calendar_sync_email_context,
    )

    send_calendar_sync_email.delay(str(msg))
