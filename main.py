from cProfile import run
import pstats
from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient

from JDatabase import JsonDatabase
import zipfile
import os
import infos
import xdlink
import mediafire
import datetime
import time
import requests
from bs4 import BeautifulSoup
import youtube
import NexCloudClient
from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import tlmedia
import S5Crypto
import asyncio
import aiohttp
import moodlews
import moodle_client
from moodle_client import MoodleClient2
from yarl import URL
import re
from draft_to_calendar import send_calendar

def sign_url(token: str, url: URL):
    query: dict = dict(url.query)
    query["token"] = token
    path = "webservice" + url.path
    return url.with_path(path).with_query(query)

def short_url(url):
    api = 'https://shortest.link/es/'
    resp = requests.post(api,data={'url':url})
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text,'html.parser')
        shorten = soup.find('input',{'class':'short-url'})['value']
        return shorten
    return url

def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        name = filename
        nam = name[0:15]
        zip = str(name).split('.')[-1]
        name2 = nam+'.'+zip
        if '7z' in name:     
            name2 = nam+'.7z.'+zip
        filename = name2   
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        name = filename
        nam = name[0:15]
        zip = str(name).split('.')[-1]
        name2 = nam+'.'+zip
        if '7z' in name:     
            name2 = nam+'.7z.'+zip
        filename = name2   
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        err = None
        bot.editMessageText(message,'📡Conectando con el servidor ')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        draftlist=[]
        if cloudtype == 'moodle':
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            repoid = user_info['moodle_repo_id']
            token = moodlews.get_webservice_token(host,user,passw,proxy=proxy)
            if token == None:
                token = moodlews.get_webservice_token(host,user,passw,proxy=proxy)
                if token == None:
                    token = moodlews.get_webservice_token(host,user,passw,proxy=proxy)
            print(token)
            for file in files:
                    data = asyncio.run(moodlews.webservice_upload_file(host,token,file,progressfunc=uploadFile,proxy=proxy,args=(bot,message,filename,thread)))
                    while not moodlews.store_exist(file):pass
                    data = moodlews.get_store(file)
                    if data[0]:
                        urls = moodlews.make_draft_urls(data[0])
                        draftlist.append({'file':file,'url':urls[0]})
                        file_size = None
                        name = file
                        nam = name[0:15]
                        zip = str(name).split('.')[-1]
                        name2 = nam+'.'+zip
                        if '7z' in name:     
                            name2 = nam+'.7z.'+zip
                        file = name2  
                        urls = short_url(urls[0])
                        finishInfo = infos.createFinishUploading(file,file_size,urls,update.message.sender.username)
                        bot.sendMessage(message.chat.id,finishInfo,parse_mode='html')
                    else:
                        err = data[1]
                        print(err)
                        bot.editMessageText(message,'Error\n' + str(err))
        return draftlist,err
    except Exception as ex:
        bot.editMessageText(message,'Error:\n1-Compruebe que la nube esta activa\n2-Verifique su proxy\n3-O revise su cuenta')

def processFile(update,bot,message,file,thread=None,jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        name = file
        data,err = processUploadFiles(name,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        name = file
        data,err = processUploadFiles(name,file_size,[name],update,bot,message,jdb=jdb)
        file_upload_count = 1
    bot.editMessageText(message,'Creando TxT')
    bot.deleteMessage(message.chat.id,message.message_id)
    files = []
    if data:
        for draft in data:
            files.append({'name':draft['file'],'directurl':draft['url']})
    i=0
    while i < len(files):
        if i+1 < len(files):
            print('mas de un link')
        i+=2
    if len(files) > 0:     
        txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
        txtname = txtname.replace(' ','')
        sendTxt(txtname,files,update,bot)
    
    try:

        import urllib

        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        if cloudtype == 'moodle':
            client = MoodleClient(user_info['moodle_user'],
                                user_info['moodle_password'],
                                user_info['moodle_host'],
                                user_info['moodle_repo_id'],
                                proxy=proxy)
        host = user_info['moodle_host']
        user = user_info['moodle_user']
        passw = user_info['moodle_password']
        if getUser['uploadtype'] == 'calendar' or getUser['uploadtype'] == 'draft':
            nuevo = []
            #if len(files)>0:
                #for f in files:
                    #url = urllib.parse.unquote(f['directurl'],encoding='utf-8', errors='replace')
                    #nuevo.append(str(url))
            fi = 0
            for f in files:
                separator = ''
                if fi < len(files)-1:
                    separator += '\n'
                nuevo.append(f['directurl']+separator)
                fi += 1
            urls = asyncio.run(send_calendar(host,user,passw,nuevo))
            loged = client.login()
            if loged:
                token = client.userdata
                modif = token['token']
                client.logout()
            nuevito = []
            for url in urls:
                url_signed = (str(sign_url(modif, URL(url))))
                nuevito.append(url_signed)
            loco = '\n'.join(map(str, nuevito))
            fname = str(txtname)
            with open(fname, "w") as f:
                f.write(str(loco))
            #fname = str(randint(100000000, 9999999999)) + ".txt"
            bot.sendMessage(message.chat.id,'📅Calendar direct link/s🔗')
            bot.sendFile(update.message.chat.id,fname)
        else:
            return
    except:
        bot.sendMessage(message.chat.id,'💢Could not move to calendar💢')
        
def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)

def sendTxt(name,files,update,bot):
                txt = open(name,'w')
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    txt.write(f['directurl']+separator)
                    fi += 1
                txt.close()
                bot.sendFile(update.message.chat.id,name)
                os.unlink(name)

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        #tl_admin_user = os.environ.get('tl_admin_user')

        #set in debug
        tl_admin_user = 'satoshinakamoto3'

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)

        if username == tl_admin_user or user_info:  # validate user
            if user_info is None:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:
            mensaje = "No tienes acceso.\n👨🏻‍💻Dev: @studio_apps_dev\n"
            intento_msg = "💢El usuario @"+username+ "💢"
            bot.sendMessage(update.message.chat.id,mensaje)
            bot.sendMessage(2055672924,intento_msg)
            return

        msgText = ''
        try: msgText = update.message.text
        except:pass

        # comandos de admin
        if '/add' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    msg = '✅ @'+user+' has being added to the bot!'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,f'⚠️Command error /add username')
            else:
                bot.sendMessage(update.message.chat.id,'👮You do not have administrator permissions👮')
            return
        if '/ban' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        bot.sendMessage(update.message.chat.id,'⚠️You can not ban yourself⚠️')
                        return
                    jdb.remove(user)
                    jdb.save()
                    msg = '𝚃𝚑𝚎 𝚞𝚜𝚎𝚛 @'+user+' 𝚑𝚊𝚜 𝚋𝚎𝚒𝚗𝚐 𝚋𝚊𝚗𝚗𝚎𝚍 𝚏𝚛𝚘𝚖 𝚝𝚑𝚎 𝚋𝚘𝚝!'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'⚠️Command error /ban username⚠️')
            else:
                bot.sendMessage(update.message.chat.id,'👮You do not have administrator permissions👮')
            return
        if '/db' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                database = open('database.jdb','r')
                bot.sendMessage(update.message.chat.id,database.read())
                database.close()
            else:
                bot.sendMessage(update.message.chat.id,'👮You do not have administrator permissions👮')
            return
        # end

        # comandos de usuario
        if '/help' in msgText:
            message = bot.sendMessage(update.message.chat.id,'📄Guía de Usuario:')
            tuto = open('tuto.txt','r')
            bot.sendMessage(update.message.chat.id,tuto.read())
            tuto.close()
            return
        if '/myuser' in msgText:
            getUser = user_info
            if getUser:
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
                return
        if '/zips' in msgText:
            getUser = user_info
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = '🗜️Perfect now the zips will be of '+ sizeof_fmt(size*1024*1024)+' the parts📚'
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'⚠️Command error /zips zips_size⚠️')    
                return
        if '/acc' in msgText:
            try:
                account = str(msgText).split(' ',2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'⚠️Command error /acc user,password⚠️')
            return

        if '/host' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'⚠️Command error /host cloud_url⚠️')
            return
        if '/repo' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = int(cmd[1])
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'⚠️Command error /repo moodle_repo_id⚠️')
            return
        if '/uptype' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                type = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'⚠️Command error /uptype (evidence,draft,blog,calendar)⚠️')
            return


        if '/proxy' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    msg = '🧬Perfect, proxy equipped successfuly.'
                    bot.sendMessage(update.message.chat.id,msg)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,'🧬Error equipping proxy.')
            return
                    
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                bot.editMessageText(msg,'🚫Task cancelled🚫')
            except Exception as ex:
                print(str(ex))
            return
        #end

        message = bot.sendMessage(update.message.chat.id,'🎐Analizyng...')

        thread.store('msg',message)

        if '/start' in msgText:
            start_msg = '╭───ⓘ🎐Hola @' + str(username)+'─〄\n│\n'
            start_msg+= '├🔗 Soporto links\n│\n'
            start_msg+= '├👨‍💻Dev: @studio_apps_dev\n│\n'
            start_msg+= '╰ⓘQue disfutes del bot─〄\n'
            bot.editMessageText(message,start_msg)
        elif '/token' in msgText:
            message2 = bot.editMessageText(message,'🤖Getting token, please wait...')

            try:
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                      user_info['moodle_password'],
                                      user_info['moodle_host'],
                                      user_info['moodle_repo_id'],proxy=proxy)
                loged = client.login()
                if loged:
                    token = client.userdata
                    modif = token['token']
                    bot.editMessageText(message2,'🤖Your token is: '+modif)
                    client.logout()
                else:
                    bot.editMessageText(message2,'⚠️The moodle '+client.path+' does not have token⚠️')
            except Exception as ex:
                bot.editMessageText(message2,'⚠️The moodle '+client.path+' does not have token or check out your account⚠️')       
        elif '/delete' in msgText:
            enlace = msgText.split('/delete')[-1]
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged= client.login()
            if loged:
                #update.message.chat.id
                deleted = client.delete(enlace)

                bot.sendMessage(update.message.chat.id, "Archivo eliminado con exito...")

        elif '/uclv' in msgText:
            getUser = user_info
            getUser['moodle_host'] = "https://moodle.uclv.edu.cu/"
            getUser['uploadtype'] =  "calendar"
            getUser['moodle_user'] = "---"
            getUser['moodle_password'] = "---"
            getUser['moodle_repo_id'] = 4
            getUser['zips'] = 399
            jdb.save_data_user(username,getUser)
            jdb.save()
            statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
            bot.editMessageText(message,"✅Uclv configuration loaded")
        elif 'http' in msgText:
            url = msgText
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
        else:
            #if update:
            #    api_id = os.environ.get('api_id')
            #    api_hash = os.environ.get('api_hash')
            #    bot_token = os.environ.get('bot_token')
            #    
                # set in debug
            #    api_id = 7386053
            #    api_hash = '78d1c032f3aa546ff5k176d9ff0e7f341'
            #    bot_token = '5124841893:AAH30p6ljtIzi2oPlaZwBmCfWQ1KelC6KUg'

            #    chat_id = int(update.message.chat.id)
            #    message_id = int(update.message.message_id)
            #    import asyncio
            #    asyncio.run(tlmedia.download_media(api_id,api_hash,bot_token,chat_id,message_id))
            #    return
            bot.editMessageText(message,'⚠️Error analizyng⚠️')
    except Exception as ex:
           print(str(ex))
  

def main():
    bot_token = '5368525823:AAGY4PLJIAWtxTr_3YiSK1qicl1BY71745A'
    

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    bot.run()
    asyncio.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()
