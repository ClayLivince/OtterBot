from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
from bs4 import BeautifulSoup
import urllib
import logging
import time
import traceback


def search_word(word):
    urlword = urllib.parse.quote(word)
    url = "http://127.0.0.1:3000/search?keywords={}".format(urlword)
    r = requests.get(url=url)
    jres = json.loads(r.text)
    status_code = jres["code"]
    if int(status_code) == 200:
        songs = jres["result"]["songs"]
        song = songs[0]
        song_id = song["id"]
        album_id = song["album"]["id"]
        album_r = requests.get(url="http://127.0.0.1:3000/album?id={}".format(album_id))
        album_data = json.loads(album_r.text)
        pic = album_data["songs"][0]["al"]["picUrl"]

        '''
        url = "https://127.0.0.1:3000/song/url?id={}".format(song_id)
        r = requests.get(url=url)
        song_res = json.loads(r.text)
        song_data = song_res["data"][0]
        '''
        '''
        msg = [
            {
                "type": "music",
                "data": {
                    "type": "163",
                    "id": "{}".format(song_id)
                },
            }
        ]
        "type": "share",
        "data": {
            "url": "https://y.music.163.com/m/song/{}".format(song_id),
            "title": song["name"],
            "content": song["artists"][0]["name"],
            "image": song["artists"][0]["img1v1Url"],
        }  
        '''
        msg = [
            {
                "type": "xml",
                "data": {
                    "data": "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>" +
                            "<msg serviceID=\"2\" templateID=\"1\" action=\"web\" brief=\"[分享] " +
                            song["name"] +
                            " - 网易云音乐\" sourceMsgId=\"0\" url=\"" +
                            "https://y.music.163.com/m/song/{}".format(song_id) +
                            "\" flag=\"0\" adverSign=\"0\" multiMsgFlag=\"0\">" +
                            "<item layout=\"2\">" +
                            "<audio cover=\"" +
                            pic + "\" src=\"http://music.163.com/song/media/outer/url?id={}\"/>".format(song_id) +
                            "<title>" + song["name"] + " - " + song["artists"][0]["name"] +
                            "</title><summary>獭獭点歌</summary></item>" + "<source name=\"网易云音乐\" icon=\"https://s1.music.126.net/style/favicon.ico\" url=\"http://url.cn/5pl4kkd\" action=\"app\" a_actionData=\"com.netease.cloudmusic\" i_actionData=\"tencent100495085://\" appid=\"100495085\" />" +
                            "</msg>"
                }
            }
        ]
    else:
        msg = '未能找到"{}"对应歌曲'.format(word)
    return msg


def QQCommand_music(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        FF14WIKI_API_URL = global_config["FF14WIKI_API_URL"]
        FF14WIKI_BASE_URL = global_config["FF14WIKI_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]

        bot = kwargs["bot"]
        
        message_content = receive["message"].replace("/music", "", 1).strip()
        msg = "default msg"
        if message_content.find("help") == 0 or message_content == "":
            msg = (
                "/music $name : 搜索关键词$name的歌曲\n" + "Powered by https://music.cyanclay.xyz"
            )
        else:
            word = message_content
            msg = search_word(word)

        if type(msg) == str:
            msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        logging.error(e)
        traceback.print_exc()
