#!/usr/bin/env python
# -*- coding:utf-8 -*-

from ConfigParser import SafeConfigParser
import sys, os, re, cgi, urllib, urllib2, cookielib, xml.dom.minidom, time, logging, socket, datetime,csv,re
from stat import *
import easygui as g
logging.basicConfig(level=logging.DEBUG,filename='test.log',filnemode='w')
socket.setdefaulttimeout(20)
conf=SafeConfigParser()
conf.read('config.ini')

smdic={}
dllist=[]

def getconnection(**kwd):
    userid = kwd['userid']
    password = kwd['password']
    conn = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
    req = urllib2.Request("https://secure.nicovideo.jp/secure/login")
    req.add_data( urllib.urlencode( {"mail":userid, "password":password} ))
    res = conn.open(req)
    return conn

def getids_rss(url,conn):
    if not re.search('\?rss=2\.0$',url):
        url=url+'?rss=2.0'
    ret = []
    data = conn.open(url).read()
    dTree = xml.dom.minidom.parseString(data)
    def getTitle(dTree):
        tl=dTree.getElementsByTagName('title')[0]
        tl=tl.firstChild.data
        s=re.search('#([\d]+)',tl)
        sl=''
        if s:
            sl=int(s.group(1))
        else:
            sl='2009_01'
        return sl
    def getOrder(dTree):
        order=32
        s=itree.toxml()
        k=re.search(u'"nico-memo">([\d]+)位</p>',s)
        if k and len(k.groups())>=1:
            order=int(k.group(1))
        return order
      
    sl=getTitle(dTree)
    for i,itree in enumerate(dTree.getElementsByTagName('item')):
        smid = itree.getElementsByTagName('link')[0].firstChild.data.strip().split('/')[-1]
        order=getOrder(itree)
        ret.append((smid,i+1))
    return (sl,ret)
    
def getids_file(filepath,conn):
    ret = []
    ifh = open(filepath,"r")
    for line in ifh:
        if re.match(r"^..\d+\s*$",line):
            ret.append(line.strip())
    return ret

def getids_smid(smid,conn):
    return [ smid.strip(), ]
def _getThumbNail(conn,url,smid):
    data = conn.open(url)
    if not os.path.exists('img'):
        os.mkdir('img')
    img='img'+os.sep+smid+'.jpeg'
    out=open(img,'wb')
    out.write(data.read())
    out.close()
    
def _download(sl,(smid,order),conn):
    global smdic
    data = conn.open("http://www.nicovideo.jp/api/getthumbinfo/"+smid).read()
    pTree = xml.dom.minidom.parseString(data)
    videoTitle = pTree.getElementsByTagName("title")[0].firstChild.data
    thumbNail = pTree.getElementsByTagName('thumbnail_url')[0].firstChild.data
    _getThumbNail(conn,thumbNail,smid)
    getflv='http://www.nicovideo.jp/api/getflv/%s' % smid
    res = conn.open("http://www.nicovideo.jp/api/getflv/"+smid).read()
    videoURL= cgi.parse_qs(res)["url"][0]

    conn.open("http://www.nicovideo.jp/watch/"+smid)
    if re.search('smile\?s=',videoURL):
        videoURL+='as3'
    print videoURL
    time.sleep(4)
    res = conn.open(videoURL)
    data = res.read()
    ext = res.info().getsubtype()
    if ext == "x-shockwave-flash":
        ext = "swf"
    if re.search(r"low$",videoURL):
        videoTitle = "(LOW)"+videoTitle
    dst=smid+"."+ext
    dstpath='s%s' % str(sl)
    if not os.path.exists(dstpath):
        os.mkdir(dstpath)
    dst=dstpath+os.sep+dst
    ofh = open(dst,"wb")
    ofh.write(data)
    ofh.close()
    def chutf8(c):
        if isinstance(c,str):
            return unicode(c,'utf-8')
        elif isinstance(c,unicode):
            return c
    smdic[chutf8(dst)]=[chutf8(smid),chutf8(videoTitle),chutf8(thumbNail),sl,order]
    logging.info("Downloaded: %s" % smid)
    dllist.append(dst+',0\n')

def _isregistered(smid):
    ret = False
    scanfiles=[]
    for f in os.listdir("."):
        mode = os.stat(f)[ST_MODE]
        if S_ISDIR(mode):
            scanfiles.extend( os.listdir(f) )
        if S_ISREG(mode):
            scanfiles.append(f)
    for f in scanfiles:
        try:
            if len(f.split("."))<2:
                continue
            if re.search('\.jpe?g',f):
                continue
            if re.search('\.mp3',f):
                continue
            fsmid = f.split(".")[-2]
            if fsmid == smid:
                ret = True
        except:
            pass
    return ret

def _readcsv(fname):
    global smdic
    if os.path.exists(fname):
        reader=csv.reader(open(fname))
        for row in reader:
            k=row[0]
            smdic[k]=row[1:]
def _writecsv(fname):
    writer=csv.writer(open(fname,"wb"))
    for k in smdic:
        l=smdic[k]
        l.insert(0,k)
        p=[]

        for k in l:
            if isinstance(k,unicode):
                p.append(k.encode('utf-8'))
            else:
                p.append(k)
        writer.writerow(p)
def _writelog(fname):
    out=open(fname,'a')
    out.writelines(dllist)
    out.close()

def repeart_download(sl,smid,conn,ofh):
    stat='NG'
    try:
        _download(sl,smid,conn)
        stat="OK"
    except Exception, e:
        print e
        logging.warn("cannnot download %s %s " % (smid, e.message))
    finally:
        ofh.write("%s [%s]:%s\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M"), stat, smid) )
        ofh.flush()
    return stat

def main():
    global conn
    userid=conf.get('Auth','user')
    password=conf.get('Auth','password')

    conn  = getconnection(userid=userid,password=password)
    _readcsv('@@dl.csv')
    smids=None
    info=None

    try:
        rep = g.buttonbox(choices=('smid','rss','file'))
        if rep == 'rss':
            info = g.enterbox(msg="feed url?  (ex. http://www.nicovideo.jp/mylist/3900779?rss=2.0 )",)
            smids = getids_rss(info,conn)
        elif rep == 'file':
            info = g.fileopenbox(msg="smid list?",default="./*.txt",filetypes=['*.txt'])
            smids = getids_file(info,conn)
        elif rep == 'smid':
            info = g.enterbox(msg="smid? (ex. sm32123)",)
            smids = getids_smid(info,conn)
        else:
            sys.exit()
    except Exception, e:
        g.textbox(msg='', title='Error', text="Error while getting smids from your input."+e.message, codebox=0)
        sys.exit()
    #info='http://www.nicovideo.jp/mylist/3900779?rss=2.0'
    #info="http://www.nicovideo.jp/mylist/3409323?rss=2.0"
    #info='http://www.nicovideo.jp/mylist/3165526?rss=2.0'
    #smids= getids_rss(info,conn)

    logging.info("DownloadList:%s" % '\n'.join([sm[0] for sm in smids[1]]) )
    ofh = open("@@-download.log","w+")
    sl=smids[0]
    print 'size=%d' % len(smids[1])
    for smid in smids[1]:
        if _isregistered(smid[0]):
            stat = "%s ok" % smid[0]
            ofh.write("%s [%s]:%s\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M"), stat, smid) )
            ofh.flush()
            continue    
        time.sleep(2)
        stat='NG'
        count=1
        while(stat=='NG' and count<5):
            time.sleep(2)
            print 'retry smid=%s count=%d' % (smid,count)
            stat=repeart_download(sl,smid,conn,ofh)
            count+=1
            if(stat == 'NG'):
                userid=conf.get('Auth','user')
                password=conf.get('Auth','password')
                conn  = getconnection(userid=userid,password=password)


    ofh.seek(0)
    g.textbox(msg='', title='download report', text=ofh.read(), codebox=0) 
    ofh.close()
    _writecsv('@@dl.csv')
    _writelog('@@conv.log')
            
if __name__ == '__main__':
    main()
