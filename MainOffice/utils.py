import os
import vk_api
import openai
import requests
from django.core.files.temp import NamedTemporaryFile
import time
from .models import *
import calendar
import re


class Vk:
    def __init__(self):
        self.token = os.getenv('Token_vk')
        self.vk = vk_api.VkApi(token=self.token).get_api()

    def get_group_info(self, link: str) -> dict:
        """
        Получение данных группы по ссылке

        ::param link: Ссылка на группу в формате https://vk.com/<name>
        :return: Словарь полученный в результате запроса к vk_api
        """
        try:
            return self.vk.groups.getById(group_id=link.split('/')[-1])[0]
        except Exception:
            raise Exception('Группы по такому адресу не существует')

    def get_market_items(self, link: str, name: str) -> list:
        """
        Получение всех товаров у определенной группы по назаванию

        ::param link: Ссылка на группу в формате https://vk.com/<name>
        ::param name: Название для поиска в товарах.
        :return: Список товаров полученный в результате запроса к vk_api
        """
        if isinstance(self.get_group_info(link), dict):
            group_id = self.get_group_info(link)['id']
            try:
                response = self.vk.market.search(owner_id=-group_id, q=name)['items']
                return response
            except Exception:
                raise Exception('В группе отсутствует магазин')

        raise Exception('Группы по такому адресу не существует')

    def get_group_img(self, link: str):
        """
        Получение фотографии группы в формате для ImageField(TemporaryFile)

        ::param link: Ссылка на группу в формате https://vk.com/<name>
        :return: Формат картинки TemporaryFile
        """
        if isinstance(self.get_group_info(link), dict):
            group = self.get_group_info(link)
            response = requests.get(group['photo_100'])
            img = NamedTemporaryFile()
            img.write(response.content)
            img.flush()
            return img

        raise Exception('Группы по такому адресу не существует')

    def get_photo_for_post(self, post: Post, group_id: int) -> dict:
        """
        Получение Фотографии для генерации поста

        ::param post: class Post
        ::param group_id: id группы вк
        :return: Ответ от сервиса vk
        """

        try:
            with open(post.photo.path, 'rb') as f:
                image_data = f.read()

            response = self.vk.photos.getWallUploadServer(group_id=group_id).json()

            upload_url = response['response']['upload_url']
            response = requests.post(upload_url, files={'photo': ('image.jpg', image_data)}).json()

            response = self.vk.photos.saveWallPhoto(group_id=group_id, server=response['server'], photo=response['photo'],
                                                    hash=response['hash'])
            return response
        except Exception:
            raise Exception('Нет возможности загрузить фото')

    # Создание поста на странице группы
    def create_post_for_group(self, post: Post) -> dict:
        group_id = self.get_group_info(post.group.link)['id']
        photo = self.get_photo_for_post(post, group_id)
        message = post.text
        response = self.vk.wall.post(owner_id=-group_id, message=message, from_group=1,
                                     publish_date=int(time.mktime(post.date.timetuple())),
                                     attachments=f'photo{photo["owner_id"]}_{photo["id"]}')
        return response


def week_pattern(num: int, data: dict):
    with open('static/files/Wednesday.txt', 'r') as f:
        content = f.read()
    for key, value in data.items():
        content = content.replace('{{ ' + key + ' }}', value)

    return content


def formation_Mail_data(link, name):
    response = Vk().get_market_items(link, name)
    # Получение парамет
    prise_old = response[0]['price']['text']
    name = response[0]['title']
    compound, count = '', ''
    temp = response[0]['description'].split("\n")
    for id, part in enumerate(temp):
        if part.find("Состав: ") > 0:
            compound = part[part.find("Состав: ") + len('Состав: '):]
            count = temp[id + 1][2:]
            break

    res = {
        'prise_old': prise_old,
        'name': name,
        'compound': compound,
        'count': count,
    }
    return res


def formation_Mail(text: str) -> dict:
    """
    :param text: текст для парсинга.
    :return: Словарь с данными
    """
    data = code = name = prise_new = link = ''

    patterns = [r'С \d+ по \d+ \w+',
                r'Промокод: \d+',
                r'\w+\s\w+ за \d+ рублей',
                r'Группа - https?://\S+']
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            raise Exception('Не совпадение с шаблоном: <br>' +
                            'С <em>день</em> по <em>день</em> <em>месяц</em><br> Промокод: <em>цифры</em> <br><em>Название</em> за <em>цена</em> рублей<br>Группа - <em>Ссылка</em>')

    match = re.search(patterns[0], text).group()
    data = match[match.find('по ') + len('по '):]

    match = re.search(patterns[1], text).group()
    code = match[match.find('код: ') + len('код: '):]

    match = re.search(patterns[2], text).group()
    temp = match.split(' за ')
    name, prise_new = temp[0], temp[1]

    match = re.search(patterns[3], text).group()
    link = match[match.find(' - ') + len(' - '):]

    response = formation_Mail_data(link, name)
    theme = f'Сформируй завлекающий, продающий заголовок для акции которая заканчивается совсем скоро. Заголовок должен быть длиной не более чем 2 предложения.'
    res = {
        'code': code,
        'data': data,
        'name': name,
        'count': response['count'],
        'compound': response['compound'],
        'prise_new': prise_new,
        'prise_old': response['prise_old'],
        'header': use_gpt(theme=theme),
    }
    return res


def use_gpt(theme: str, **kwargs) -> str:
    """
    Использование Api OpenAI
    :param theme: Вопрос для чата
    :return: Ответ от сервиса
    """
    if 'chat' in kwargs:
        openai.api_key = os.getenv('Api_key_OpenAi_chat')
    else:
        openai.api_key = os.getenv('Api_key_OpenAi')

    response = openai.Completion.create(
        model="text-davinci-003",  # gpt-4
        prompt=theme,
        temperature=0.9,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.6,
        stop=["You:"]
    )
    return response['choices'][0]['text']


def holidays_parse(file='static/files/holidays.txt') -> dict:
    res = {}
    with open(file) as f:
        lines = [line.rstrip() for line in f]
        for line in lines:
            res[line.split(' : ')[0]] = line.split(' : ')[1].split(',')
    return res


class MyCalendar(calendar.HTMLCalendar):
    def formatday(self, day, weekday):
        """
        Return a day as a table cell.
        """
        if day == 0:
            return '<td class="%s">&nbsp;</td>' % self.cssclass_noday
        else:
            return f'<td class="{self.cssclasses[weekday]}"><button value="{day}" name="day" class="btn btn-light d-flex w-100 h-100">{day}</button></td>'


def formation_statistic(data: list[dict], limits: tuple[int, int]) -> list:
    """
    :param data: Список постов со временем.
    :param limits: ограничения дат.
    :return: список состоящий из количества постов в определенный момент.
    """
    res = {i: 0 for i in range(limits[0], limits[1] + 1)}
    for el in data:
        if 'hour' in el:
            if el['hour'].hour in res:
                res[el['hour'].hour] += 1
        elif 'month' in el:
            if el['month'].day in res:
                res[el['month'].day] += 1

        elif 'week' in el:
            if el['week'].day in res:
                res[el['week'].day] += 1
    res = [res[i] for i in range(limits[0], limits[1] + 1)]
    return res


