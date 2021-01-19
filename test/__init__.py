from pixivpy_async.sync import *
import json


username = "user_gacm2743"
password = "tydkzhedwx"
aapi = AppPixivAPI()
aapi.login(username, password)

jsonaa = aapi.search_illust("ff14", search_target='partial_match_for_tags')
print(jsonaa)
