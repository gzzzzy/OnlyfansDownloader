import sys
import os
sys.path.append('../')
from OnlyfansDownloader import OnlyfansDownloader

# login
od=OnlyfansDownloader().login(email='gzzzzy9@gmail.com', password='Lyj20020508.')

user_id='coldbeauty'
# get photo urls
# od.get_photo_urls(user_id, './photo_urls.txt')
# get video urls
od.get_video_urls(user_id, './video_urls.txt')

# add headers to act like a browser
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
}
od.add_headers(headers)

# extract photos and videos
os.mkdir('./{}'.format(user_id))
od.get_files_from_urls('./photo_urls.txt','./{}/p'.format(user_id),'jpg')
od.get_files_from_urls('./video_urls.txt','./{}/v'.format(user_id),'mp4')

# once interrupted 
od.rerun_get_files_from_urls(49, './video_urls.txt','./{}/v'.format(user_id),'mp4')