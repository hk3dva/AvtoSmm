from django import forms
from django.forms import ModelForm, Form
from .models import *
from bootstrap_datepicker_plus.widgets import DateTimePickerInput


class PostGenerationTextForm(Form):
    theme = forms.CharField(label='theme',
                            widget=forms.TextInput(attrs={'class': 'form-control',
                                                          'type': "text",
                                                          'placeholder': "Напишите тему"}),
                            )


class GroupAdd(ModelForm):
    class Meta:
        model = GroupForLead
        fields = ['link']
        widgets = {
            'text': forms.TextInput(attrs={'type': "text",
                                           'placeholder': "Вставь ссылку",
                                           'id': 'message',
                                           'name': 'message'}),
        }


class changeGroupForm(forms.Form):
    change = forms.ModelChoiceField(queryset=GroupForLead.objects.all(),
                                    to_field_name='pk',

                                    empty_label=None,
                                    initial=GroupForLead.objects.all()[0],
                                    widget=forms.Select(attrs={'class': 'text-white',
                                                               'id': 'change_id',
                                                               'style': 'background-color: transparent;'
                                                                        'border: none;'
                                                                        'color:#6ca2da;'
                                                                        'font-size: 13px'}))

    dateAndTime = forms.DateTimeField(widget=DateTimePickerInput(range_from='start_date',
                                                                 options={
                                                                     'format': 'DD MMM YYYY HH:mm',
                                                                     'locale': 'ru',
                                                                 },
                                                                 attrs={
                                                                        'style': 'font-size: 13px; color:#5d5d5d;'
                                                                                 'background-color: transparent;'
                                                                                 'border: none;'
                                                                        }),
                                      )

    text = forms.CharField(widget=forms.Textarea(attrs={'style': 'background-color: transparent;'
                                                                 'border: none;'
                                                                 'font-size: 13px;'
                                                                 'line-height: 1.462;',
                                                        'class': 'text-white form-control',
                                                        'rows': "1",
                                                        })
                           )
    photo = forms.ImageField(widget=forms.FileInput(attrs={'class': 'text-white form-control',
                                                           'accept': "image/*",
                                                           'type': "file",
                                                           'placeholder': 'Установить изображение'}))

    def __init__(self, *args, **kwargs):
        self.current_photo = kwargs.pop('current_photo', None)
        super().__init__(*args, **kwargs)


class WriteSms(ModelForm):
    class Meta:
        model = Sms
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'type': "text",
                                           'placeholder': "Введите сообщение",
                                           'class': 'd-flex, w-100',
                                           'id': 'message',
                                           'name': 'message'}),
        }
