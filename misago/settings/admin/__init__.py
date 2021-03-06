from django.conf.urls import patterns, include, url
from django.utils.translation import ugettext_lazy as _
from misago.admin import AdminSection, AdminAction

ADMIN_SECTIONS=(
    AdminSection(
                 id='system',
                 name=_("System"),
                 icon='cog',
                 after='permissions',
                 ),
)

ADMIN_ACTIONS=(
   AdminAction(
               section='system',
               id='settings',
               name=_("Settings"),
               help=_("Change your forum configuration"),
               icon='wrench',
               route='admin_settings',
               urlpatterns=patterns('misago.settings.admin.views',
                        url(r'^$', 'settings', name='admin_settings'),
                        url(r'^search/$', 'settings_search', name='admin_settings_search'),
                        url(r'^(?P<group_slug>([a-z0-9]|-)+)-(?P<group_id>\d+)/$', 'settings', name='admin_settings')
                    ),
               ),
)