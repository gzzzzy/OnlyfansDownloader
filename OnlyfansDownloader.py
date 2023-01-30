import numpy as np
import tqdm
import time
import os
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import InvalidSessionIdException, ElementClickInterceptedException
from selenium.webdriver import ActionChains

sys.path.append('./')


class OnlyfansDownloader(object):
    """ A class for downloading onlyfans photos and videos
        Only test on Chromedriver
    """

    def __init__(self):
        self.driver = webdriver.Chrome(service=Service("chromedriver.exe"))
        self.driver.maximize_window()
        self.headers = None

    def login(self, email: str, password: str):
        """Log into Onlyfans.com

        Args:
            email (str): email
            password (str): password

        Returns:
            OnlyfansDownloader: object itself
        """
        self.driver.get('https://onlyfans.com')
        email_input = WebDriverWait(self.driver, 10, 1).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        email_input.click()
        email_input.send_keys(email)
        time.sleep(5)
        password_input = self.driver.find_element(By.NAME, 'password')
        password_input.click()
        password_input.send_keys(password)
        time.sleep(5)
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(10)
        return self

    def get_photo_urls(self, user_id: str, output_file: str):
        """Get all photo urls and write them into output file. 

        Args:
            user_id (str): user whose photos to be got
            output_file (str): output file containing photo urls
        """
        self.driver.get('https://onlyfans.com/{}/photos'.format(user_id))
        photo_div = WebDriverWait(self.driver, 10, 0.5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='b-photos g-negative-sides-gaps']")
            )
        )
        total = int(self.driver.find_element(
            By.XPATH, "//a[contains(@class,'b-tabs__nav__item') and @aria-current='page']"
        ).text.split()[-1])
        # drag scrollbar to the end
        while len(photo_div.find_elements(By.CSS_SELECTOR, 'img.b-photos__item__img')) != total:
            self.driver.execute_script(
                "window.scrollTo(0,document.body.scrollHeight)")
        # drag scrollbar to the front
        self.driver.execute_script(
            "window.scrollTo(0,-document.body.scrollHeight)")
        # collect photo urls
        img_urls = []
        print('Start collecting photo urls......')
        for img in tqdm.tqdm(photo_div.find_elements(By.CSS_SELECTOR, 'img.b-photos__item__img')):
            self.driver.execute_script("arguments[0].scrollIntoView();", img)
            img.click()
            urls = WebDriverWait(self.driver, 5, 1).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'img.pswp__img')
                )
            )
            img_urls.append(urls[1].get_attribute('src'))
            self.driver.find_element(
                By.CSS_SELECTOR, 'button.pswp__button--close').click()

        # drop duplicates
        img_urls_unique, idxs = np.unique(img_urls, return_index=True)
        img_urls = img_urls_unique[np.argsort(idxs)]

        # save url list for convinience
        with open(output_file, 'w') as f:
            f.writelines([url+'\n' for url in img_urls])

    def get_video_urls(self, user_id: str, output_file: str):
        """Get all video urls(Quality: original) and write them into output file. 

        Args:
            user_id (str): user whose videos to be got
            output_file (str): output file containing video urls
        """
        self.driver.get('https://onlyfans.com/{}'.format(user_id))
        posts_cnt_a = WebDriverWait(self.driver, 10, 0.5).until(EC.presence_of_element_located(
            (By.XPATH, "//a[@aria-current='page']")
        ))
        # drag scroll bar to the end
        posts_cnt = int(posts_cnt_a.text.split()[0])
        while len(self.driver.find_elements(By.CSS_SELECTOR, "div.vue-recycle-scroller__item-view")) != posts_cnt:
            self.driver.execute_script(
                "window.scrollTo(0,document.body.scrollHeight)")
        # click all play buttons at once
        self.driver.execute_script(
            "window.scrollTo(0,-document.body.scrollHeight)")
        videos_cnt = len(self.driver.find_elements(
            By.CSS_SELECTOR, 'div.video-js'))
        print('Start clicking play buttons......')
        for idx in tqdm.trange(videos_cnt):
            self.driver.execute_script(
                "arguments[0].scrollIntoView();",
                self.driver.find_elements(By.CSS_SELECTOR, 'div.video-js')[idx]
            )
            self.driver.find_elements(
                By.CSS_SELECTOR,
                'button.vjs-big-play-button'
            )[idx].click()
        # change video quanlity to original
        self.driver.execute_script(
            "arguments[0].scrollIntoView();",
            self.driver.find_elements(By.CSS_SELECTOR, 'div.video-js')[0]
        )
        quality_selector = self.driver.find_element(
            By.CSS_SELECTOR,
            'div.vjs-quality-selector'
        )
        quality_selector.click()
        quality_selector.find_elements(
            By.CSS_SELECTOR,
            'li.vjs-menu-item'
        )[-1].click()
        # collect video urls
        self.driver.execute_script(
            "window.scrollTo(0,-document.body.scrollHeight)")
        print('Start collecting video urls......')
        video_urls = [element.get_attribute('src') for element in tqdm.tqdm(
            self.driver.find_elements(By.TAG_NAME, 'video'))]
        # output file
        with open(output_file, 'w') as f:
            f.writelines([url+'\n' for url in video_urls])

    def add_headers(self, headers: dict):
        """Add headers to function urlopen to better simulate browser behavior. 

        Args:
            headers (dict): Request headers.
        """
        self.headers = headers

    def get_files_from_urls(self, urls_file: str, target_dir: str, extension_name: str):
        """Get photos/videos from urls.

        Args:
            urls_file (str): file with urls generated from function `get_photo_urls`/`get_video_urls`.
            target_dir (str): directory where storedphotos/videos are stored
            extension_name (str): file extension name
        """
        if not os.path.exists(urls_file):
            raise FileNotFoundError("url file not exists")
        with open(urls_file, 'r') as f:
            urls = [url.strip() for url in f.readlines()]
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
        format_pattern = '{:0'+str(len(str(len(urls))))+'d}.{}'
        print('Start collecting files......')
        for idx, url in tqdm.tqdm(list(enumerate(urls))):
            with open(os.path.join(target_dir, format_pattern.format(idx+1, extension_name)), 'wb') as f:
                f.write(urlopen(Request(url, headers=self.headers)).read())

    def rerun_get_files_from_urls(self, restart: int, urls_file: str, target_dir: str, extension_name: str):
        """_summary_

        Args:
            restart (int): index where function `get_files_from_urls` interrupted for unknown reason
            urls_file (str): the same with argument in function `get_files_from_urls`
            target_dir (str): the same with argument in function `get_files_from_urls`
            extension_name (str): the same with argument in function `get_files_from_urls`
        """
        if not os.path.exists(urls_file):
            raise FileNotFoundError("url file not exists")
        with open(urls_file, 'r') as f:
            urls = [url.strip() for url in f.readlines()]
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
        format_pattern = '{:0'+str(len(str(len(urls))))+'d}.{}'
        print('Start collecting files......')
        pbar = tqdm.tqdm(
            list(zip(range(restart, len(urls)),urls[restart:])))
        for idx, url in pbar:
            pbar.set_description('Processing {}'.format(idx))
            with open(os.path.join(target_dir, format_pattern.format(idx+1, extension_name)), 'wb') as f:
                f.write(urlopen(Request(url, headers=self.headers)).read())

    def close(self):
        self.driver.close()
