from django.shortcuts import render, redirect
from django.core.files import File
import datetime
import calendar as cal
import locale
from django.views.generic import TemplateView, DetailView, UpdateView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import *
from .utils import *
from .forms import *
import plotly.graph_objs as go
from django.db.models import Count
from django.db.models.functions import Trunc, TruncMonth, TruncHour
from django.urls import reverse_lazy

# Страница после авторизации
def index(request):
    context = {
        'title': 'Мой Офис',
    }
    return render(request, 'MainOffice/base.html', context)


# Чат между пользователями, а так же Gpt
class Chats(TemplateView):
    template_name = 'MainOffice/UsersChat.html'
    form_class = WriteSms

    # id gpt аккаунта в сети
    chat_id = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Чат'
        context['user_chats'] = Account.objects.filter(groups__name='Smm').exclude(pk__in=[kwargs['pk'], self.chat_id])
        context['form'] = self.form_class()
        context['recipient'] = Account.objects.get(pk=kwargs['sender'])
        context['massages'] = Sms.objects.filter(Q(id_sender=kwargs['sender'], id_recipient=kwargs['pk']) |
                                                 Q(id_sender=kwargs['pk'], id_recipient=kwargs['sender']))[:100]
        context['chat_id'] = self.chat_id
        return context

    def get(self, request, *args, **kwargs):
        name = request.GET.get('room_name', '').split('_')
        if len(name) == 2:
            name.remove(str(request.user.pk))
            return render(request, self.template_name, self.get_context_data(pk=request.user.pk, sender=name[0]))
        return render(request, self.template_name, self.get_context_data(pk=request.user.pk, sender=self.chat_id))

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            name = request.GET.get('room_name', '').split('_')
            name.remove(str(request.user.pk))
            message.id_recipient = Account.objects.get(pk=int(name[0]))
            message.id_sender = request.user
            message.date = datetime.datetime.now()
            message.save()
            if int(name[0]) == self.chat_id:
                text = use_gpt(theme=message.text, chat=True)
                sms = Sms.objects.create(
                    text=text,
                    id_recipient=request.user,
                    id_sender=Account.objects.get(pk=int(name[0])),
                    date=datetime.datetime.now(),
                )
                sms.save()

            return render(request, self.template_name, self.get_context_data(pk=request.user.pk, sender=name[0]))


class ProfileUpdateView(UpdateView):
    model = Account
    form_class = ProfileForm
    template_name = 'MainOffice/profile_update.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('MainOffice:profile', kwargs={'pk': self.object.pk})


class Profile(DetailView):
    model = Account
    template_name = 'MainOffice/profile.html'
    context_object_name = 'userProfile'
    form_class = GroupAdd

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Профиль'
        context['posts'] = Post.objects.filter(owner=self.request.user, date_of_completion__date=datetime.datetime.today())
        context['form'] = self.form_class()
        context['total'] = Post.objects.filter(owner=self.request.user).count()
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        pk = kwargs.get('pk')
        if form.is_valid():
            group_data = Vk().get_group_info(form.cleaned_data['link'])

            name, photo = group_data['name'], group_data['photo_100']

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

    now = datetime.datetime.today()
    if request.GET.get('month', ''):
        if 0 < int(request.GET.get('month', '')) < 13:
            year = int(request.GET.get('year', ''))
            month = int(request.GET.get('month', ''))
            if request.GET.get('day', None):
                day = int(request.GET.get('day', ''))
            else:
                day = 1

            now = datetime.datetime(year, month, day)

        elif 0 >= int(request.GET.get('month', '')):
            year = int(request.GET.get('year', '')) - 1
            month = 12
            day = 1

            now = datetime.datetime(year, month, day)

        elif 13 <= int(request.GET.get('month', '')):
            year = int(request.GET.get('year', '')) + 1
            month = 1
            day = 1

            now = datetime.datetime(year, month, day)
    else:
        year = datetime.datetime.today().year
        month = datetime.datetime.today().month
        day = datetime.datetime.today().day

    locale.setlocale(locale.LC_TIME, 'ru_RU.utf8')
    today_mouth = MyCalendar().formatmonth(theyear=now.year, themonth=now.month)
    holidays = holidays_parse()
    today = datetime.datetime(year=year, month=month, day=day).strftime('%d') + '_' + cal.month_name[month].title()

    context = {
        'title': 'Календарь',
        'calendar': today_mouth,
        'today': datetime.datetime.today().strftime('%d %B'),
        'holiday_day': datetime.datetime(year=year, month=month, day=day).strftime('%d %B'),
        'holidays': holidays[today],
        'month': month,
        'year': year,
        'day': day,
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
        context['changeGroup'] = ChangeGroupForm()
        context['changeGroup'].fields['change'].queryset = Account.objects.get(pk=kwargs['user'].pk).groups_leader
        context['changeGroup'].fields['text'].initial = kwargs.get('theme')
        return context

    def get(self, request, *args, **kwargs):
        form = PostGenerationTextForm(request.GET)
        if form.is_valid():
            theme = use_gpt(form.cleaned_data['theme'])
            return render(request, self.template_name, self.get_context_data(user=request.user, theme=theme))
        return render(request, self.template_name, self.get_context_data(user=request.user))

    def post(self, request, *args, **kwargs):
        form = ChangeGroupForm(request.POST, request.FILES)
        if form.is_valid():
            post = Post.objects.create(
                group=form.cleaned_data['change'],
                owner=request.user,
                text=form.cleaned_data['text'],
                photo=form.cleaned_data['photo'],
                date=form.cleaned_data['dateAndTime'],
                date_of_completion=datetime.datetime.now(),
            )
            post.save()
            Vk().create_post_for_group(post)
        return render(request, self.template_name, self.get_context_data(user=request.user))


def tasks(request):
    context = {
        'title': 'Задания',
        'tasks': Task.objects.filter(executor=request.user.pk)
    }
    return render(request, 'MainOffice/Tasks.html', context)


def statistics(request):

    hours_x = [i for i in range(0, 25)]
    hours_y = formation_statistic(Post.objects.annotate(hour=TruncHour('date_of_completion')).values(
        'owner', 'hour').annotate(count=Count('id')), (0, 24))

    weeks_x = [i for i in range(1, 8)]
    start_date = timezone.now() - timezone.timedelta(days=7)
    weeks_y = formation_statistic(Post.objects.filter(owner=request.user, date_of_completion__gte=start_date).annotate(
        week=Trunc('date_of_completion', 'week')).values('week').annotate(count=Count('id')), (1, 7))

    month_x = [i for i in range(1, 32)]
    month_y = formation_statistic(Post.objects.annotate(month=TruncMonth('date_of_completion')).values(
                                    'owner', 'month').annotate(count=Count('id')),
                                    (1, cal.monthrange(datetime.datetime.now().year, datetime.datetime.now().month)[1]))

    data_day = [go.Scatter(x=hours_x, y=hours_y, xaxis='x1', yaxis='y1'),]
    layout_day = go.Layout(dragmode=False, xaxis=dict(
        range=[0, 24], title='Часы'), yaxis1=dict(title='Кол-во'),)

    data_week = [go.Scatter(x=weeks_x, y=weeks_y, xaxis='x1', yaxis='y1'),]
    layout_week = go.Layout(dragmode=False, xaxis=dict(
        range=[1, 7], title='День недели'), yaxis1=dict(title='Кол-во'),)

    data_month = [go.Scatter(x=month_x, y=month_y, xaxis='x1', yaxis='y1'),]
    layout_month = go.Layout(dragmode=False, xaxis=dict(
        range=[1, 32], title='День'), yaxis1=dict(title='Кол-во'),)

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


def push_generator(request):
    return render(request, 'MainOffice/PushGenerator.html')


def mailing_generator(request, *args, **kwargs):
    context = {
        'title': 'Генератор рассылок',
        'show': False,
        'TextInForm': TextForm(),
        'TextOutForm': TextForm(),
        'Error': '',
    }
    if '0' < request.GET.get('day', '') < '8':
        print(True)
    if request.method == "POST":
        form = TextForm(request.POST)
        if form.is_valid():
            try:
                context['TextOutForm'].fields['text'].initial = week_pattern(3, formation_Mail(form.cleaned_data['text']))
                context['show'] = True
            except Exception as e:
                context.update({'Error': e})

    return render(request, 'MainOffice/MailGenerator.html', context)

