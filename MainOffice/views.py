from django.shortcuts import render, redirect
from django.core.files import File
from datetime import datetime
import calendar as cal
import locale
from django.views.generic import TemplateView, DetailView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import *
from .utils import *
from .forms import *
import plotly.graph_objs as go


def index(request):
    context = {
        'title': 'Мой Офис',
    }
    return render(request, 'MainOffice/base.html', context)


class Chats(TemplateView):
    template_name = 'MainOffice/UsersChat.html'
    form_class = WriteSms
    chat_id = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Чат'
        context['user_chats'] = Account.objects.filter(groups__name='Smm').exclude(pk__in=[kwargs['pk'], self.chat_id])
        context['form'] = self.form_class()
        context['recipient'] = Account.objects.get(pk=kwargs['sender'])
        context['massages'] = Sms.objects.filter(Q(id_sender=kwargs['sender'], id_recipient=kwargs['pk']) |
                                                 Q(id_sender=kwargs['pk'], id_recipient=kwargs['sender']))[:100]
        return context

    def get(self, request, *args, **kwargs):
        name = request.GET.get('room_name', '').split('_')
        if len(name) == 2:
            name.remove(str(request.user.pk))
            return render(request, self.template_name, self.get_context_data(pk=request.user.pk, sender=name[0]))
        return render(request, self.template_name, self.get_context_data(pk=request.user.pk, sender=self.chat_id))

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            name = request.GET.get('room_name', '').split('_')
            name.remove(str(request.user.pk))
            message.id_recipient = Account.objects.get(pk=int(name[0]))
            message.id_sender = request.user
            message.date = datetime.now()
            message.save()
            if int(name[0]) == self.chat_id:
                text = get_theme_for_post(theme=message.text, chat=True)
                sms = Sms.objects.create(
                    text=text,
                    id_recipient=request.user,
                    id_sender=Account.objects.get(pk=int(name[0])),
                    date=datetime.now(),
                )
                sms.save()

            return render(request, self.template_name, self.get_context_data(pk=request.user.pk, sender=name[0]))


class Profile(DetailView):
    model = Account
    template_name = 'MainOffice/profile.html'
    context_object_name = 'userProfile'
    form_class = GroupAdd

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Профиль'
        context['posts'] = Post.objects.filter(owner=self.request.user, date_of_completion__date=datetime.today())
        context['form'] = self.form_class()
        context['total'] = Post.objects.filter(owner=self.request.user).count()
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        pk = kwargs.get('pk')
        if form.is_valid():
            name, photo = get_vk_group_info(form.cleaned_data['link'])
            group_for_lead = form.save(commit=False)

            group_for_lead.link = form.cleaned_data['link']
            group_for_lead.name = name
            group_for_lead.photo.save(name + '.jpg', File(photo))

            group_for_lead.save()

            temp = SmmGroupLead.objects.create(group=group_for_lead, smm=request.user)
            temp.save()

            return redirect('MainOffice:profile', pk=pk)

        return redirect('MainOffice:profile', pk=pk)


def calendar(request):

    locale.setlocale(locale.LC_TIME, 'ru_RU.utf8')
    today_mouth = cal.HTMLCalendar().formatmonth(datetime.today().year, datetime.today().month)

    context = {
        'title': 'Календарь',
        'calendar': today_mouth,
        'today': datetime.today().strftime('%d %B'),
    }
    return render(request, 'MainOffice/calendar.html', context)


# Получение фото группы по pk
def get_image(request, pk):
    my_model = get_object_or_404(GroupForLead, pk=pk)
    return JsonResponse({'image_url': my_model.photo.url})


class Posts(TemplateView):
    template_name = 'MainOffice/Posts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Генератор Постов'
        context['GenerationTextform'] = PostGenerationTextForm()
        context['changeGroup'] = changeGroupForm()
        context['changeGroup'].fields['change'].queryset = Account.objects.get(pk=kwargs['user'].pk).groups_leader
        context['changeGroup'].fields['text'].initial = kwargs.get('theme')
        return context

    def get(self, request, *args, **kwargs):
        form = PostGenerationTextForm(request.GET)
        if form.is_valid():
            theme = get_theme_for_post(form.cleaned_data['theme'])
            return render(request, self.template_name, self.get_context_data(user=request.user, theme=theme))
        return render(request, self.template_name, self.get_context_data(user=request.user))

    def post(self, request, *args, **kwargs):
        form = changeGroupForm(request.POST, request.FILES)
        if form.is_valid():
            post = Post.objects.create(
                group=form.cleaned_data['change'],
                owner=request.user,
                text=form.cleaned_data['text'],
                photo=form.cleaned_data['photo'],
                date=form.cleaned_data['dateAndTime'],
                date_of_completion=datetime.now(),
            )
            post.save()
            post_vk_group(post)
        return render(request, self.template_name, self.get_context_data(user=request.user))


def tasks(request):
    context = {
        'title': 'Задания',
        'tasks': Task.objects.filter(executor=request.user.pk)
    }
    return render(request, 'MainOffice/Tasks.html', context)


def statistics(request):

    data = Post.objects.filter(owner=request.user.pk)
    now = timezone.now()
    day_data = data.filter(date_of_completion__day=now.day)

    hours = [i for i in range(8, 21)]
    weeks = [i for i in range(1, 8)]
    months = [i for i in range(1, 32)]

    data_day = [go.Scatter(x=hours, y=[1, 3, 5, 4, 7, 2, 1, 5, 4], xaxis='x1', yaxis='y1'),]
    layout_day = go.Layout(xaxis1=dict(title='Время'), yaxis1=dict(title='Кол-во'),)

    data_week = [go.Scatter(x=weeks, y=[1, 3, 5, 4, 7, 2, 1], xaxis='x1', yaxis='y1'),]
    layout_week = go.Layout(xaxis1=dict(title='День'), yaxis1=dict(title='Кол-во'),)

    data_month = [go.Scatter(x=months, y=[1, 5, 7, 3, 5, 2, 3, 4, 7, 8, 9, 4, 2, 3, 5, 6, 7, 8, 9, 2, 1, 4, 5, 6, 3, 2, 8, 6, 5, 4], xaxis='x1', yaxis='y1'),]
    layout_month = go.Layout(xaxis1=dict(title='День'), yaxis1=dict(title='Кол-во'),)

    plot_day = go.Figure(data=data_day, layout=layout_day).to_html(full_html=False)
    plot_week = go.Figure(data=data_week, layout=layout_week).to_html(full_html=False)
    plot_month = go.Figure(data=data_month, layout=layout_month).to_html(full_html=False)
    context = {
        'title': 'Статистика',
        'day': plot_day,
        'week': plot_week,
        'month': plot_month,
    }
    return render(request, 'MainOffice/Statistics.html', context)
