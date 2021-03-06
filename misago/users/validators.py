import re
from django.core.exceptions import ValidationError
from django.utils.translation import ungettext, ugettext_lazy as _
from misago.banning.models import check_ban
from misago.settings.settings import Settings

def validate_username(value):
    value = unicode(value).strip()
    if len(value) < 3:
        raise ValidationError(_("Username cannot be shorter than 3 characters."))
    if len(value) > 12:
        raise ValidationError(_("Username cannot be longer than 12 characters."))
    if not re.search('^[0-9a-zA-Z]+$', value):
        raise ValidationError(_("Username can only contain letters and digits."))
    if check_ban(username=value):
        raise ValidationError(_("This username is forbidden."))
        

def validate_password(value):
    value = unicode(value).strip()
    db_settings = Settings()
    if len(value) < db_settings['password_length']:
        raise ValidationError(ungettext(
            'Correct password has to be at least one character long.',
            'Correct password has to be at least %(count)d characters long.',
            db_settings['password_length']
        ) % {
            'count': db_settings['password_length'],
        })
    for test in db_settings['password_complexity']:
        if test in ('case', 'digits', 'special'):
            if not re.search('[a-zA-Z]', value):
                raise ValidationError(_("Password must contain alphabetical characters."))
            if test == 'case':
                if not (re.search('[a-z]', value) and re.search('[A-Z]', value)):
                    raise ValidationError(_("Password must contain characters that have different case."))
            if test == 'digits':
                if not re.search('[0-9]', value):
                    raise ValidationError(_("Password must contain digits in addition to characters."))
            if test == 'special':
                if not re.search('[^0-9a-zA-Z]', value):
                    raise ValidationError(_("Password must contain special (non alphanumerical) characters."))


def validate_email(value):
    value = unicode(value).strip()
    if check_ban(email=value):
        raise ValidationError(_("This board forbids registrations using this e-mail address."))