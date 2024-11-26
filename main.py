import requests
import os
import datetime
import time
import pytz

tz = pytz.timezone('Asia/Shanghai')

app_id = os.environ.get('APP_ID')
app_secret = os.environ.get('APP_SECRET')
app_token = os.environ.get('APP_TOKEN')
table_id = os.environ.get('TABLE_ID')
admin_chat_id = os.environ.get('ADMIN_CHAT_ID')

def get_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json().get('tenant_access_token')

def get_user_info(tenant_access_token, app_token, table_id):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search?page_size=20"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }
    response = requests.post(url, headers=headers, json={}).json()
    res_data = response.get('data')
    while res_data.get('has_more'):
        next_page_token = res_data.get('page_token')
        response = requests.post(url + f"&page_token={next_page_token}", headers=headers, json={}).json()
        res_data['items'] += response.get('data').get('items')
        res_data['has_more'] = response.get('data').get('has_more')
        info_list = []
        for user in res_data['items']:
            fields = user.get('fields')
            if '人员' in fields and '日期' in fields and '部门' in fields:
                info_list.append([fields['人员'][0], fields['日期'], fields['部门']])
    return info_list

def send_message(tenant_access_token, user_id, message_info):
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }
    card_body = "{\"type\":\"template\",\"data\":{\"template_id\":\"AAqjHFTuPWC3T\",\"template_version_name\":\"1.0.1\",\"template_variable\":{\"person\":\"" + message_info["person"] + "\",\"date\":\"" + message_info["date"] + "\",\"team\":\"" + message_info["team"] + "\"}}}"
    data = {
        "receive_id": user_id,
        "content": card_body,
        "msg_type": "interactive"
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def send_admin_message(tenant_access_token, message_info):
    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tenant_access_token}"
    }
    card_body = "{\"type\":\"template\",\"data\":{\"template_id\":\"AAqjHFTuPWC3T\",\"template_version_name\":\"1.0.1\",\"template_variable\":{\"person\":\"" + message_info["person"] + "\",\"date\":\"" + message_info["date"] + "\",\"team\":\"" + message_info["team"] + "\"}}}"
    data = {
        "receive_id": admin_chat_id,
        "content": card_body,
        "msg_type": "interactive"
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def main():
    while True:
        # 每天早上8点和晚上20点发送消息
        now = datetime.datetime.now(tz)
        if (now.hour != 0 or now.minute != 0) and (now.hour != 20 or now.minute != 0):
            time.sleep(1)
            continue
        tenant_access_token = get_access_token(app_id, app_secret)
        user_info = get_user_info(tenant_access_token, app_token, table_id)
        for user in user_info:
            if user[1] < int(time.time() * 1000) and user[1] > int((time.time() - 86400) * 1000):
                message_info = {
                    "person": user[0]["name"],
                    "date": datetime.datetime.fromtimestamp(int(user[1] / 1000), tz).strftime('%Y-%m-%d'),
                    "team": user[2][0]["text"]
                }
                print(send_message(tenant_access_token, user[0]["id"], message_info))
        time.sleep(60)

if __name__ == "__main__":
    main()