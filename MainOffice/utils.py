import os
import vk_api
import openai
import requests
from django.core.files.temp import NamedTemporaryFile
import time
from .models import Post
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

            response = self.vk.photos.getWallUploadServer(group_id=group_id)

            upload_url = response['upload_url']
            response = requests.post(upload_url, files={'photo': ('image.jpg', image_data)}).json()

            response = self.vk.photos.saveWallPhoto(group_id=group_id, server=response['server'],
                                                    photo=response['photo'], hash=response['hash'])

            return response[0]
        except Exception as e:
            raise Exception('Нет возможности загрузить фото')

    # Создание поста на странице группы
    def create_post_for_group(self, post: Post) -> dict:
        try:
            group_id = self.get_group_info(post.group.link)['id']
            photo = self.get_photo_for_post(post, group_id)
            message = post.text
            response = self.vk.wall.post(owner_id=-group_id, message=message, from_group=1,
                                         publish_date=int(time.mktime(post.date.timetuple())),
                                         attachments=f'photo{photo["owner_id"]}_{photo["id"]}')
            return response
        except Exception as e:
            raise e


def week_pattern(num: int, data: dict) -> str:
    if num == 1:
        text = 'Monday.txt'
    elif num == 3:
        text = 'Wednesday.txt'
    elif num == 5:
        text = 'Friday.txt'
    else:
        text = 'Monday.txt'
    with open('static/files/' + text, 'r') as f:
        content = f.read()
    for key, value in data.items():
        content = content.replace('{{ ' + key + ' }}', value)

    return content


class MailFormation:
    def __init__(self):
        self.days = dict()
        name = ''
        self.days['1'] = [[r'С (\d+) по (\d+) (\w+)',
                           r'Промокод: (\d+)',
                           r'(\w+\s\w+) за (\d+) рублей',
                           r'Группа - (https?://\S+)'], 'Сформируй завлекающий, продающий заголовок для акции которая только что началась. Заголовок должен быть длиной не более чем 2 предложения.']
        self.days['2'] = [[r'', r'',
                           r'(\w+\s\w+) за (\d+) рублей',
                           r'Группа - (https?://\S+)'], f'Сформируй завлекающий, продающий заголовок для того что бы преложить {name}. Заголовок должен быть длиной не более чем 2 предложения.']
        self.days['3'] = [[r'С (\d+) по (\d+) (\w+)',
                           r'Промокод: (\d+)',
                           r'(\w+\s\w+) за (\d+) рублей',
                           r'Группа - (https?://\S+)'], 'Сформируй завлекающий, продающий заголовок для акции которая заканчивается совсем скоро. Заголовок должен быть длиной не более чем 2 предложения.']
        self.days['4'] = [[r'С (\d+) по (\d+) (\w+)',
                           r'Промокод: (\d+)',
                           r'(\w+\s\w+) за (\d+) рублей',
                           r'Группа - (https?://\S+)'], 'Сформируй завлекающий, продающий заголовок который говорил бы о том что акция сгорает сегодня. Заголовок должен быть длиной не более чем 2 предложения.']
        self.days['5'] = [[r'С (\d+) по (\d+) (\w+)',
                           r'Промокод: (\d+)',
                           r'(\w+\s\w+) в подарок!',
                           r'Группа - (https?://\S+)'], 'Сформируй завлекающий, продающий заголовок для акции которая будет длится только в выходные. Заголовок должен быть длиной не более чем 2 предложения.']
        self.days['6'] = [[r'', r'', r'', r''], '']
        self.days['7'] = [[r'', r'', r'', r''], '']

    @staticmethod
    def __replaceReg(text: list) -> str:
        """
        :param text: Текст для замены паттерна
        :return: замененные значения паттерна
        """
        return '\n'.join(text).\
               replace(r'\d+', '<em>день</em>').\
               replace(r'\w+\s\w+', '<em>название ролла/пиццы</em>').\
               replace(r'\w+', '<em>месяца</em>').\
               replace(r'\S+', 'ссылка на группу').\
               replace('\n', '<br>').\
               replace('(', '').replace(')', '')

    def isMatch(self, text: str, patternlist: list[str]) -> bool:
        """
        :param text: Текст который надо проверить.
        :param patternlist: Регулярное выражение для проверки.
        :return: Соответствие теста регулярному выражению.
        """
        for pattern in patternlist:
            match = re.search(pattern, text)
            if not match:
                raise Exception('Не совпадение с шаблоном: <br>' + self.__replaceReg(patternlist))
        return True

    @staticmethod
    def getFoodData(name: str, link: str) -> dict:
        """
        :param name: Название товара
        :param link: ссылка на группу
        :return: Словарь данных про товар
        """
        try:
            response = Vk().get_market_items(link, name)
            if len(response) == 0:
                response = Vk().get_market_items(link, name[name.find(' ') + 1:])
        except Exception as e:
            raise e
        if len(response) == 0:
            raise Exception('Не удалось найти товар')
        res = dict()
        res['prise_old'] = response[0]['price']['text']
        res['name'] = response[0]['title']

        for index, part in enumerate(response[0]['description'].split("\n")):
            if part.find("Состав: ") > 0:
                res['compound'] = part[part.find("Состав: ") + len('Состав: '):]
                res['count'] = response[0]['description'].split("\n")[index + 1][2:]
                break
        return res

    def getMailData(self, day: int, text: str) -> dict:
        """
        :param day: Номер дня недели.
        :param text: Текст который необходимо проверить по паттернам.
        :return: словарь для заполнения шаблона.
        """
        try:
            if self.isMatch(text, self.days[str(day)][0]):

                res = dict()
                days_pattern = self.days[str(day)][0]

                if days_pattern[0] != days_pattern[1]:
                    res['data'] = re.search(days_pattern[0], text).group(2) + ' ' + re.search(days_pattern[0],
                                                                                              text).group(3)
                    res['code'] = re.search(days_pattern[1], text).group(1)

                res['name'] = re.search(days_pattern[2], text).group(1)
                res['link'] = re.search(days_pattern[3], text).group(1)

                if len(re.findall(days_pattern[2], text)) == 2:
                    res['prise_new'] = re.search(days_pattern[2], text).group(2)
                else:
                    res['prise_new'] = ''

                res['header'] = use_gpt(theme=self.days[str(day)][1].format(name=res['name']))

                res.update(self.getFoodData(res['name'], res['link']))

                return res
        except Exception as e:
            raise e


class PushFormation(MailFormation):
    def __init__(self):
        super().__init__()
        self.pattern = [[r'Название: (\w+\s\w+)',
                         r'Промокод: (\d+)',
                         r'При покупке от: (\d+)',
                         r'Группа - (https?://\S+)']]

        self.theme = 'Напиши push-уведомление которое говорит о "{name}", при заказе от {prise} рублей,' \
                     ' при использовании промокода "{code}" сделай его живым и заманчивым и длиной не более 3' \
                     ' предложений. Можешь так же использовать эту информацию {info}'

    @staticmethod
    def __replaceReg(text: list) -> str:
        """
        :param text: Текст для замены паттерна
        :return: замененные значения паттерна
        """
        return '\n'.join(text).\
               replace(r'\d+', '<em>цена/промокод</em>').\
               replace(r'\w+\s\w+', '<em>название ролла/пиццы</em>').\
               replace(r'\S+', 'ссылка на группу').\
               replace('\n', '<br>').\
               replace('(', '').replace(')', '')

    def getPushData(self, text: str) -> dict:
        """
        :param text: Текст который необходимо проверить по паттернам.
        :return: словарь для заполнения шаблона.
        """
        try:
            if self.isMatch(text, self.pattern[0]):

                res = dict()
                days_pattern = self.pattern[0]

                res['name'] = re.search(days_pattern[0], text).group(1)
                res['code'] = re.search(days_pattern[1], text).group(1)
                res['prise_new'] = re.search(days_pattern[2], text).group(1)
                res['link'] = re.search(days_pattern[3], text).group(1)
                res['info'] = self.getFoodData(res['name'], res['link'])

                res['text'] = use_gpt(theme=self.theme.format(name=res['name'],
                                                              code=res['code'],
                                                              prise=res['prise_new'],
                                                              info=res['info']
                                                              ))

                return res
        except Exception as e:
            raise e


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
            return f'<td class="{self.cssclasses[weekday]}"><button value="{day}"' \
                   f' name="day" class="btn btn-light d-flex w-100 h-100">{day}</button></td>'


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
