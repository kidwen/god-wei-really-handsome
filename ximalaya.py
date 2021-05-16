import pymysql
import requests
from flask import Flask, render_template,request,make_response
import config
import logging
from urllib import parse
from flask import json
app=Flask(__name__)

#第一个接口，用来请求每个分类下的所有节目
list_page_url='https://www.ximalaya.com/channel/{}/p{}/'# $1分类号，$2页码
list_page_url_new='https://www.ximalaya.com/revision/metadata/v2/group/channels/recommend/albums?groupId={}&pageNum={}&pageSize=5'
home_headers={
    "Host": "www.ximalaya.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
}#通用header
my_detail_url="http://www.vision123.site/audio/source/{}/1"
list_xpath='//*[@id="award"]//ul/li[@class="_qt"]/div'#列表
name_str='./a[1]//text()'#名称
author_str='./a[2]//text()'#作者
program_url='./a[1]/@href'#节目url
img_url='./div[@class="album-wrapper-card kF_"]/a/img/@src'#图片
play_num='./div[@class="album-wrapper-card kF_"]/a/p//text()'#播放量
#第二个接口，用来请求每个节目的音频来源,返回json数据，取src为音频来源url
next_page='//*[@id="award"]/main//nav/ul[@class="pagination-page WJ_"]/li[@class="page-next page-item WJ_"]'
source_url='https://www.ximalaya.com/revision/play/v1/audio?id={}&ptype=1'#$1节目id
detail_data_url='https://www.ximalaya.com/revision/album/v1/getTracksList?albumId={}&pageNum={}&pageSize=10'
#接下来请求音频来源url
headers={
    "Accept":"*/*",
    "Accept-Encoding":"gzip, deflate, br",
    "Host":"www.ximalaya.com",
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",

}#音频请求headers
file_header={
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding":"gzip, deflate, br",
    "Host":"aod.cos.tx.xmcdn.com",
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
}
# @app.route("/audio/list/<int:atype>/<int:page>")
# def get_program_list(atype,page):
#     url=list_page_url.format(atype,page)
#     response=requests.get(url,headers=home_headers)
#     html=etree.HTML(response.text)
#     audio_list=html.xpath(list_xpath)
#     audio_data_list=[]
#     for audio_mess in audio_list:
#         audio_name=audio_mess.xpath(name_str)[0]
#         audio_author=audio_mess.xpath(author_str)[0]
#         audio_url=audio_mess.xpath(program_url)[0]#"/yule/3555870/"
#         print(audio_url)
#         audio_id=re.findall("/(\d+)/",audio_url)[0]
#         audio_source_url=my_detail_url.format(audio_id)
#         audio_img_url=audio_mess.xpath(img_url)[0]
#         audio_play_num=audio_mess.xpath(play_num)[0]
#         audio_data={
#             "audio_name":audio_name,
#             "audio_author":audio_author,
#             "audio_id":audio_id,
#             "audio_source_url":audio_source_url,#详情页url，需要进一步获取音频url
#             "audio_img_url":audio_img_url,
#             "audio_play_num":audio_play_num
#         }
#         audio_data_list.append(audio_data)
#     res={"audio_data_list":audio_data_list}
#     if len(html.xpath(next_page))==0:
#         res["hasNextPage"]=False
#     else:
#         res["hasNextPage"]=True
#     return json.dumps(res)
#获取某个分类下的专辑
@app.route("/audio/list/<int:atype>/<int:page>")
def get_program_list_new(atype,page):
    res_data={}
    url=list_page_url_new.format(atype,page)
    response=requests.get(url,headers=home_headers)
    json_data=response.json()
    res_data["pageNum"]=json_data["data"]["pageNum"]
    res_data["typeNum"]=json_data["data"]["groupId"]
    audio_list=[]
    for data in json_data["data"]["channels"]:
        r_data={
            "model_name":data["channel"]["channelName"]
        }
        d_list=[]
        for d in data["recommendAlbums"]:
            d={
                "audioId":d["albumId"],
                "playCount":d["albumPlayCount"],
                "name":d["albumTitle"],
                "author":d["albumUserNickName"],
                "intro":d["intro"],
                "isPaid":d["isPaid"],
                "url":my_detail_url.format(d["albumId"])
            }
            if not d["isPaid"]:
                d_list.append(d)
        r_data["audio_list"]=d_list
        audio_list.append(r_data)
    res_data["res_data"]=audio_list
    json_data_= json.dumps(res_data,ensure_ascii=False)
    res=make_response(json_data_)
    res.headers['Access-Control-Allow-Origin']='*'
    return res
#获取某个专辑下音频列表
@app.route("/audio/source/<int:id>/<int:page>")
def get_program_data(id,page):
    data_url=detail_data_url.format(id,page)
    print(data_url)
    response=requests.get(data_url,headers=home_headers)
    print(response.status_code)
    json_data=json.loads(response.text)
    data_list=[]
    for data in json_data["data"]["tracks"]:
        res_data={
            "url":get_file_data(data["trackId"]),
            "name":data["title"],
            "playCount":data["playCount"],
            "createDateFormat":data["createDateFormat"],
            "timeLength":data["length"],
        }
        data["url"]=get_file_data(data["trackId"])
        data_list.append(res_data)
    json_data["data"]["tracks"]=data_list
    json_data_ =json.dumps(json_data,ensure_ascii=False)
    res=make_response(json_data_)
    res.headers['Access-Control-Allow-Origin']='*'
    return res
def get_file_data(id):
    file_url=source_url.format(id)
    print(file_url)
    response=requests.get(file_url,headers=headers)
    file_data=json.loads(response.text)
    print(file_data)
    real_url=file_data["data"]["src"]
    return real_url
#根据关键词获取专辑列表
@app.route("/audio/search/<kw>/<page>")
def get_search_res(kw,page):
    kw_quote=parse.quote(kw)
    search_url='https://www.ximalaya.com/revision/search/main?core=album&kw={}&page={}&spellchecker=true&rows=20&condition=relation&device=iPhone&fq=&paidFilter=false'.format(kw_quote,page)
    response=requests.get(search_url,headers=headers)
    json_data=response.json()
    res_data={}
    res_data["kw"]=json_data["data"]["kw"]
    d_list=[]
    for d in json_data["data"]["album"]["docs"]:
        d={
            "audioId":d["albumId"],
            "playCount":d["playCount"],
            "name":d["title"],
            "author":d["nickname"],
            "intro":d["intro"],
            "isPaid":d["isPaid"],
            "url":my_detail_url.format(d["albumId"])
        }
        if not d["isPaid"]:
            d_list.append(d)
    res_data["audio_list"]=d_list
    json_data_= json.dumps(res_data,ensure_ascii=False)
    res=make_response(json_data_)
    res.headers['Access-Control-Allow-Origin']='*'
    return res
#获取所有分类
@app.route("/audio/all")
def get_home_page():
    type_list=[]
    with open("type_list.json","r",encoding="utf-8") as f:
        data_dict=json.load(f)
        for k in data_dict.keys():
            type_list.append({"type_name":k,"url":"http://www.vision123.site/audio/list/{}/1".format(data_dict[k])})
    json_data=json.dumps(type_list,ensure_ascii=False)
    res=make_response(json_data)
    res.headers['Access-Control-Allow-Origin']='*'
    return res

@app.route("/audio/user",methods=["get","delete","put","post"])
def get_user_opetion():
    res_data={"user_status":False}
    user_id= request.args.get('userId')
    select_sql="select user_name,password,phone_number from users where user_id=%"
    conn, cursor1 = get_mysql_conn()
    cursor1.execute(select_sql,user_id.strip())
    data = cursor1.fetchone()
    if data is not None:
        res_data["userStatus"]=True
        res_data["userName"]=data[0]
        res_data["password"]=data[1]
        res_data["phoneNumber"]=data[2]
    else:
        res_data["fail_mes"]="用户不存在"
    if request.method=='POST':
        select_sql="select user_name,password,phone_number from users where user_id=%"
        conn, cursor1 = get_mysql_conn()
        user_id= request.args.get('userId')
        cursor1.execute(select_sql,user_id.strip())
        data = cursor1.fetchone()
        if data is not None:
            res_data["userStatus"]=True
            user_name= request.args.get('userName',data[0])
            password= request.args.get('password',data[1])
            phone_number= request.args.get('phoneNumber',data[2])
            update_sql="update users set user_name=%s,password=%s,phone_number=%s  where user_id=%s"
            res=cursor1.execute(update_sql,(user_id,user_name,password,phone_number))
            conn.commit()
        else:
            res_data["fail_mes"]="用户不存在"
    elif request.method=='DELETE':

    json_data=json.dumps(res_data,ensure_ascii=False)
    res=make_response(json_data)
    res.headers['Access-Control-Allow-Origin']='*'
    return res
def get_mysql_conn():
    conn = None
    cursor1 = None
    try:
        conn = pymysql.connect(host=config.host, port=config.port, user=config.user,
                               passwd=config.passwd,
                               db=config.db, charset='utf8', local_infile=1)
        # 创建游标对象
        cursor1 = conn.cursor()
    except Exception as e:
        logging.log(logging.ERROR,"数据库连接失败")
    return conn, cursor1
if __name__ == '__main__':
    app.run(debug = True,host="127.0.0.1" ,port=8886)