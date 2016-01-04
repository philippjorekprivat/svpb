from django import forms
from datetime import datetime, timedelta
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field
from crispy_forms.bootstrap import (
    PrependedText, PrependedAppendedText, FormActions)
from django.core.exceptions import ValidationError
from gc import disable

DATES = []
d = datetime.now()
DATES.append([d.strftime("%Y-%m-%d"), d.strftime("%A (%Y/%m/%d)")])
d = d + timedelta(days=1)
DATES.append([d.strftime("%Y-%m-%d"), d.strftime("%A (%Y/%m/%d)")])
d = d + timedelta(days=1)
DATES.append([d.strftime("%Y-%m-%d"), d.strftime("%A (%Y/%m/%d)")])
d = d + timedelta(days=1)
DATES.append([d.strftime("%Y-%m-%d"), d.strftime("%A (%Y/%m/%d)")])
d = d + timedelta(days=1)
DATES.append([d.strftime("%Y-%m-%d"), d.strftime("%A (%Y/%m/%d)")])
d = d + timedelta(days=1)
DATES.append([d.strftime("%Y-%m-%d"), d.strftime("%A (%Y/%m/%d)")])
d = d + timedelta(days=1)
DATES.append([d.strftime("%Y-%m-%d"), d.strftime("%A (%Y/%m/%d)")])

TIME = []
TIME.append(["-","-"])
TIME.append(["08:00","08:00"])
TIME.append(["08:30","08:30"])
TIME.append(["09:00","09:00"])
TIME.append(["09:30","09:30"])
TIME.append(["10:00","10:00"])
TIME.append(["10:30","10:30"])
TIME.append(["11:00","11:00"])
TIME.append(["11:30","11:30"])
TIME.append(["12:00","12:00"])
TIME.append(["12:30","12:30"])
TIME.append(["13:00","13:00"])
TIME.append(["13:30","13:30"])
TIME.append(["14:00","14:00"])
TIME.append(["14:30","14:30"])
TIME.append(["15:00","15:00"])
TIME.append(["15:30","15:30"])
TIME.append(["16:00","16:00"])
TIME.append(["16:30","16:30"])
TIME.append(["17:00","17:00"])
TIME.append(["17:30","17:30"])
TIME.append(["18:00","18:00"])
TIME.append(["18:30","18:30"])
TIME.append(["19:00","19:00"])

DURATION = []
DURATION.append(["-","-"])
DURATION.append(["60","1 Stunde"])
DURATION.append(["90","1.5 Stunden"])
DURATION.append(["120","2 Stunden"])

class NewReservationForm(forms.Form):
    res_date = forms.ChoiceField(label="Datum",required=True, widget=forms.Select, choices=DATES)
    res_start = forms.ChoiceField(label="Von",required=True, widget=forms.Select, choices=TIME)
    res_duration = forms.ChoiceField(label="Dauer",required=True, widget=forms.Select, choices=DURATION)
    
    accepted_agb = forms.BooleanField(label="Ich akceptiere <a href='/static/media/SVPB-bedinungen-boote.pdf' target='_blank'>Bedingungen fuer Vereinsboote</a>.", required=True)
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-exampleForm'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'POST'

        self.helper.add_input(Submit('submit', 'Verbindlich reservieren'))
        super(NewReservationForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(NewReservationForm, self).clean()
        res_start = cleaned_data.get("res_start")
        res_duration = cleaned_data.get("res_duration")


class BootIssueForm(forms.Form):    
    res_reported_descr = forms.CharField(label="Beschreibung",required=True,widget= forms.Textarea)    
    
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-exampleForm'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'POST'

        self.helper.add_input(Submit('submit', 'Speichern'))
        super(BootIssueForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(BootIssueForm, self).clean()
        res_reported_descr = cleaned_data.get("res_reported_descr")        
