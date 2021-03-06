from datetime import timedelta
from django import forms
from django.utils import timezone as tz
from django.utils.translation import ugettext_lazy as _
from misago.forms import Form

class GenerateStatisticsForm(Form):
    provider_model = forms.ChoiceField()
    date_start = forms.DateField(initial=tz.now() - timedelta(days=7))
    date_end = forms.DateField(initial=tz.now())
    stats_precision = forms.ChoiceField(choices=(('day', _('For each day')), ('week', _('For each week')), ('month', _('For each month')), ('year', _('For each year'))))
    
    layout = (
              (None, (
                        ('provider_model', {'label': _('Report Type'), 'help_text': _('Select statistics provider.')}),
                        ('nested', (
                            ('date_start', {'label': _('Time'), 'help_text': _('Enter start and end date for time period you want to take data from to use in graph.'), 'attrs': {'placeholder': _('Start Date: YYYY-MM-DD')}, 'width': 50}),
                            ('date_end', {'attrs': {'placeholder': _('End Date: YYYY-MM-DD')}, 'width': 50}),
                        )),
                        ('stats_precision', {'label': _('Graph Precision')}),
                      )),
              )
    
    def __init__(self, *args, **kwargs):
        provider_choices = kwargs.get('provider_choices')
        del kwargs['provider_choices']
        super(GenerateStatisticsForm, self).__init__(*args, **kwargs)
        self.fields['provider_model'] = forms.ChoiceField(choices=provider_choices)