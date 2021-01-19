from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import traceback
import time
import copy
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def get_image_from_CQ(CQ_text):
    if "url=" in CQ_text:
        tmp = CQ_text
        tmp = tmp[tmp.find("url=") : -1]
        tmp = tmp.replace("url=", "")
        img_url = tmp.replace("]", "")
        return img_url
    return None


def upload_image(img_url, token=""):
    headers = {}
    if token:
        headers = {"Authorization": token}
    original_image = requests.get(url=img_url, timeout=5)
    sm_req = requests.post(
        headers=headers,
        url="https://sm.ms/api/v2/upload",
        files={"smfile": original_image.content},
        timeout=30,
    )
    # print(sm_req.headers)
    return json.loads(sm_req.text)


def delete_image(img_hash):
    sm_req = requests.post(
        url="https://sm.ms/api/v2/delete/{}".format(img_hash), timeout=5
    )
    return sm_req.status_code


def QQCommand_image(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        SMMS_TOKEN = global_config.get("SMMS_TOKEN", "")
        receive = kwargs["receive"]

        receive_msg = receive["message"].replace("/image", "", 1).strip()
        msg_list = receive_msg.split(" ")
        second_command = msg_list[0]
        if second_command == "" or second_command == "help":
            msg = " 禁止上传R18/NSFW图片：\n/image upload $category $image : 给类别$category上传图片\n/image $category : 随机返回一张$category的图片\n/image del $name : 删除名为$name的图片\n查看图库：https://xn--v9x.net/image/\nhttps://tata.cyanclay.xyz/image/\nPowered by https://sm.ms"
        elif second_command == "upload":
            if len(msg_list) < 3:
                msg = "您输入的参数个数不足：\n/image upload $category $image : 给类别$category上传图片, 请注意，category之后，图片之前，需要加一个空格。"
            else:
                (qquser, created) = QQUser.objects.get_or_create(
                    user_id=receive["user_id"]
                )
                if not qquser.able_to_upload_image:
                    msg = "[CQ:at,qq={}] 您由于触犯规则无权上传图片".format(receive["user_id"])
                else:
                    category = msg_list[1].strip()
                    if category.startswith("$"):
                        category = category[1:]
                    CQ_text = msg_list[2].strip()
                    img_url = get_image_from_CQ(CQ_text)
                    if not img_url:
                        msg = "未发现图片信息"
                    elif not category:
                        msg = "请选择上传图片类别"
                    else:
                        img_info = upload_image(img_url, SMMS_TOKEN)
                        if not img_info["success"]:
                            print("img_info:{}".format(json.dumps(img_info)))
                            msg = img_info["message"]
                            if (
                                "Image upload repeated limit, this image exists at: "
                                in msg
                            ):
                                url = msg.replace(
                                    "Image upload repeated limit, this image exists at: ",
                                    "",
                                )
                                o = urlparse(url)
                                path = o.path
                                domain = "{}://{}".format(o.scheme, o.netloc)
                                name = copy.deepcopy(path)
                                while "/" in name:
                                    name = name[name.find("/") + 1 :]
                                try:
                                    img = Image.objects.get(path=path)
                                    msg = '图片"{}"已存在于类别"{}"之中，无法重复上传'.format(
                                        img.name, img.key
                                    )
                                except Image.DoesNotExist:
                                    img = Image(
                                        domain=domain,
                                        key=category,
                                        name=name,
                                        path=path,
                                        img_hash="null",
                                        timestamp=int(time.time()),
                                        add_by=qquser,
                                    )
                                img.save()
                                msg = '图片"{}"上传至类别"{}"成功'.format(img.name, img.key)
                        else:
                            img_info = img_info["data"]
                            url = img_info.get("url", "")
                            o = urlparse(url)
                            path = o.path
                            domain = "{}://{}".format(o.scheme, o.netloc)
                            img = Image(
                                domain=domain,
                                key=category,
                                name=img_info["storename"],
                                path=img_info["path"],
                                img_hash=img_info["hash"],
                                timestamp=img_info.get("timestamp", 0),
                                url=url,
                                add_by=qquser,
                            )
                            img.save()
                            msg = '图片"{}"上传至类别"{}"成功'.format(img.name, img.key)
        elif second_command == "del":
            if len(msg_list) < 2:
                msg = "您输入的参数个数不足：\n/image del $name : 删除名为$name的图片"
            else:
                name = msg_list[1].strip()
                (qquser, created) = QQUser.objects.get_or_create(
                    user_id=receive["user_id"]
                )
                imgs = Image.objects.filter(name=name, add_by=qquser)
                if not imgs.exists():
                    msg = '未找到名为"{}"的图片或您无权删除这张图片'.format(name)
                else:
                    for img in imgs:
                        img.delete()
                    msg = '图片"{}"删除完毕'.format(name)
        else:
            category = msg_list[0].strip()
            if category.startswith("$"):
                category = category[1:]
            get_info = "info" in category
            category = category.replace("info", "", 1)
            if random.random() > 0.5:
                msg, status = load_remote_image(category, get_info)
                if msg is None:
                    msg, status = load_local_image(category, get_info)
            else:
                msg, status = load_local_image(category, get_info)
                if msg is None:
                    msg, status = load_remote_image(category, get_info)
            if msg is None:
                if status == -1:
                    msg = '未找到类别"{}"的图片'.format(category)
                elif status == 404:
                    msg = "本次请求的图片被图床删掉了 = =\n再试一次吧~~"
                else:
                    msg = '出现问题：{}\n5开头的错误是图床服务器错误，请耐心等待。'.format(status)
        msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
        traceback.print_exc()
    return action_list


def load_local_image(category, get_info):
    found = False
    tries = 0
    msg = None
    status = 0
    while not found and tries < 10:
        tries += 1
        imgs = Image.objects.filter(key=category)
        if not imgs.exists():
            msg = None
            status = -1
            found = True
        else:
            img = random.sample(list(imgs), 1)[0]
            img_url = img.get_url()
            r = requests.head(img_url, timeout=3)
            if r.status_code == 404:
                img.delete()
                print("deleting {}".format(img))
                msg = None
                status = 404
            else:
                found = True
                msg = "[CQ:image,cache=0,file={}]\n".format(img_url)
                if get_info:
                    msg += "Name:{}\nCategory:{}\nUploader:{}\n".format(
                        img.name, img.key, img.add_by
                    )
                    msg += "From:Local"
                status = 1
    if status == 0:
        status = -1
    return msg, status


def load_remote_image(category, get_info):
    found = False
    tries = 0
    url = "http://xn--v9x.net/image/"
    msg = None
    status = 0

    payload = "{\"optype\":\"get_images\",\"category\":\"" + category + "\",\"cached_images\":[]}"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': '4ordA2HawT3bFUwfjNTf8OUJ5LdWh3N0de12NHgzAkuYGN8LNNzK7zJmVMLipBdy',
        'Cookie': 'csrftoken=UKuQbNIIkE5TB7M7iRykr78lz6REcJmz3A4Fosh7o5wGC0oDMRePqSXYp7p0khM7; sessionid=2un89owgd5gdsxouhthovvc7eduaiknk',
    }

    response = requests.request("POST", url, headers=headers, data=payload.encode('utf-8'))

    if response.status_code != 200:
        msg = None
        status = response.status_code
    else:
        contents = json.loads(response.text)
        if not contents:
            msg = None
            status = -1
        else:
            while not found and tries < 10 and tries < len(contents['images']):

                img = contents['images'][tries]

                r = requests.head(img['url'], timeout=3)
                if r.status_code == 404:
                    msg = None
                    status = 404
                else:
                    found = True
                    msg = "[CQ:image,cache=0,file={}]\n".format(img['url'])
                    if get_info:
                        msg += img['info']
                        msg += "\nFrom:Remote"
                    status = 1
                tries += 1
        if status == 0:
            status = -1
    return msg, status
