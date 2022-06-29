import requests

def alet2slack(slack_id, text):

    try:
        # api-endpoint
        URL = "https://slack.com/api/conversations.open"
        auth = {'Authorization': 'Bearer xoxb-1509591762388-1545457494998-BNb4vmOemd5RpKWwPafZggT5'}
        payload = {'users': slack_id, 'pretty': 1}
        # sending get request and saving the response as response object
        r = requests.post(url=URL, headers=auth, params=payload)
        # extracting data in json format
        data = r.json()
        channel = data['channel']['id']
        URL_SEND = 'https://slack.com/api/chat.postMessage'
        payload_SEND = {'channel':channel,'text':text}
        # sending get request and saving the response as response object
        res = requests.post(url = URL_SEND,headers = auth,params=payload_SEND)
    except:
       text = "Not slack_id match or no internet"
       print(text)
