import os
import vk_api
import openai
import requests
from django.core.files.temp import NamedTemporaryFile
import time


def get_vk_group_info(link):
    session = vk_api.VkApi(token=os.getenv('Token_vk'))
    vk = session.get_api()

    group_name = vk.groups.getById(group_id=link.split('/')[-1])

    response = requests.get(group_name[0]['photo_100'])
    img_temp = NamedTemporaryFile()
    img_temp.write(response.content)
    img_temp.flush()

    return group_name[0]['name'], img_temp


def get_photo(post, group_id):
    access_token = os.getenv('Token_vk')
    with open(post.photo.path, 'rb') as f:
        image_data = f.read()

    upload_url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {'access_token': access_token, 'v': '5.131', 'group_id': group_id}

    response = requests.get(upload_url, params=params).json()
    upload_url = response['response']['upload_url']

    response = requests.post(upload_url, files={'photo': ('image.jpg', image_data)}).json()
    params = {'v': '5.131',
              'access_token': access_token,
              'server': response['server'],
              'photo': response['photo'],
              'hash': response['hash'],
              'group_id': group_id}
    res = requests.get('https://api.vk.com/method/photos.saveWallPhoto', params=params).json()
    return res['response'][0]


def get_vk_group_json(link):
    access_token = os.getenv('Token_vk')
    url = f"https://api.vk.com/method/groups.getById?group_ids={link.split('/')[-1]}&access_token={access_token}&v=5.131"
    return requests.get(url).json()


def post_vk_group(post):
    access_token = os.getenv('Token_vk')
    group_id = get_vk_group_json(post.group.link)['response'][0]['id']
    message = post.text

    photo = get_photo(post, group_id)

    url = f"https://api.vk.com/method/wall.post?owner_id=-{group_id}" \
          f"&message={message}&access_token={access_token}" \
          f"&v=5.131&from_group=1&publish_date={int(time.mktime(post.date.timetuple()))}" \
          f"&attachments=photo{photo['owner_id']}_{photo['id']}"
    json_data = requests.get(url).json()

    if "error" in json_data:
        # print(f"Error: {json_data['error']['error_msg']}")
        return 0
    return 1


def get_theme_for_post(theme, *args, **kwargs):

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

