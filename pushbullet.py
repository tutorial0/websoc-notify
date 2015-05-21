from config import *
import urllib.request
import json


def send_push(email: str, title: str, body: str) -> None:
    url = 'https://api.pushbullet.com/v2/pushes'
    auth_handler = urllib.request.HTTPBasicAuthHandler()
    auth_handler.add_password(realm='Pushbullet',
                              uri=url,
                              user=PUSHBULLET_API_TOKEN,
                              passwd=''
                              )
    opener = urllib.request.build_opener(auth_handler)
    urllib.request.install_opener(opener)

    values = {'type' : 'note',
              'title' : title,
              'body' : body,
              'email' : email,
              }
    data = urllib.parse.urlencode(values)
    data = data.encode('utf-8')
    req = urllib.request.Request(url, data)

    with urllib.request.urlopen(req) as response:
        pass
        #response_text = response.read().decode(encoding='utf-8')
