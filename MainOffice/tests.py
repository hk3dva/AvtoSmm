from django.test import TestCase
from .utils import Vk
from django.core.files.temp import TemporaryFile
from .models import *


class VkApiUtilsTest(TestCase):
    def setUp(self):
        self.vk = Vk()

    def test_get_group_info_correct(self):
        link = 'https://vk.com/chosushi_nchk'

        group_info = self.vk.get_group_info(link)

        self.assertIsInstance(group_info, dict)
        self.assertEqual(group_info['name'], '«Чё, Суши?» | Роллы, суши с доставкой')

    def test_get_group_info_void_link(self):
        link = ''

        with self.assertRaises(Exception):
            self.vk.get_group_info(link)

    def test_get_group_info_incorrecr_link(self):
        link = 'https://vk.com/chosushi_nchk1'

        with self.assertRaises(Exception):
            self.vk.get_group_info(link)

    def test_get_market_items_correct(self):
        link = 'https://vk.com/chosushi_nchk'
        name = 'Сет Юджин'

        market_info = self.vk.get_market_items(link, name)

        self.assertIsInstance(market_info, list)
        self.assertIsInstance(market_info[0], dict)

    def test_get_market_items_void_link_void_name(self):
        link = ''
        name = ''

        with self.assertRaises(Exception):
            self.vk.get_market_items(link, name)

    def test_get_market_items_incorrect_link_correct_name(self):
        link = 'https://vk.com/chosushi_nchk1'
        name = 'Сет Юджин'

        with self.assertRaises(Exception):
            self.vk.get_market_items(link, name)

    def test_get_market_items_correct_link_incorrect_name(self):
        link = 'https://vk.com/chosushi_nchk'
        name = 'Сет Юджин1'

        market_info = self.vk.get_market_items(link, name)

        self.assertIsInstance(market_info, list)
        self.assertEqual(len(market_info), 0)

    def test_get_market_items_correct_link_void_name(self):
        link = 'https://vk.com/chosushi_nchk'
        name = ''

        market_info = self.vk.get_market_items(link, name)

        self.assertIsInstance(market_info, list)
        self.assertGreater(len(market_info), 0)

    def test_get_group_img_correct(self):
        link = 'https://vk.com/chosushi_nchk'

        group_photo = self.vk.get_group_img(link)

        self.assertIsInstance(group_photo, TemporaryFile)

    def test_get_group_img_void_link(self):
        link = ''

        with self.assertRaises(Exception):
            self.vk.get_group_img(link)

    def test_get_group_img_incorrecr_link(self):
        link = 'https://vk.com/chosushi_nchk1'

        with self.assertRaises(Exception):
            self.vk.get_group_img(link)

    def test_get_photo_for_post_correcr_link(self):
        post = Post.object.create(photo='static/img/logo.png')
        group_id = self.vk.get_group_info(post.group.link)['id']

        photo = self.vk.get_photo_for_post(post, group_id)

        self.assertIsInstance(photo, str)



