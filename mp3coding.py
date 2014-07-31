#!/usr/bin/env python
# -*- coding:utf-8 -*-
from glob import glob
from subprocess import check_call,CalledProcessError
import os,eyed3,csv


dstdir='music'
smdic={}
dllist=[]
def _readCsv(fname):
    global smdic
    reader=csv.reader(open(fname))
    for row in reader:
        f=unicode(row[0],'utf-8')
        smid=unicode(row[1],'utf-8')
        title=unicode(row[2],'utf-8')
        if row[4] !='':
            sl=row[4]
        else:
            sl='0'
        if row[5] !='':
            order=int(row[5])
        else:
            order=0
        smdic[smid]=[title,f,sl,order]
def _readLog(fname):
    global dllist
    for l in open(fname).readlines():
        l=l.strip()
        l=l.split(',')
        dllist.append(l)
def _writeLog(fname):
    l=[]
    for k in dllist:
        q=','.join(k)
        q+='\n'
        l.append(q)
    out=open(fname,'w')
    out.writelines(l)
    out.close()
    
def addIDS():
    for mp3 in  glob("music\*.mp3"):
        b=os.path.basename(mp3)
        k=b.split('.')[0]
        if k in smdic:
            tag = eyed3.Tag()
            tag.link(mp3)
            tag.header.setVersion(eyed3.ID3_V2_3)
            tag.setTextEncoding( eyed3.UTF_16_ENCODING )
            img='img/%s.jpeg' % k
            print img
            if os.path.exists(img):
                tag.removeImages()
                tag.addImage( eyed3.frames.ImageFrame.FRONT_COVER ,img)
            #gn=eyeD3.Genre()
            #tag.setGenre(gn.parse(u"Vocaloid"))
            tag.setAlbum(u'VocaloidRanking_%s' % str(smdic[k][-2]))
            tag.setArtist(u'Vocaloid')
            title='%02d_%s' % (smdic[k][-1],smdic[k][0])
            tag.setTitle(title)
            tag.update()
            

dk={
    'flv':'bin\\ffmpeg -y -i %s -acodec copy %s',
    'mp4':"bin\\ffmpeg -y -i %s -ar 44100 -ab 192000 %s",
    'swf':'bin\\swfextract -m %s -o %s'
}

def convMP3():
    def _chname(g):
        f=os.path.basename(g)
        f=f.split('.')[:-1]
        f=''.join(f)
        f=f+".mp3"
        return dstdir+os.sep+f
    print dllist
    for i,k in enumerate(dllist):
        if int(k[1])!=0:
            continue
        f=k[0]
        print f
        if os.path.exists(f):
            ex=f.split('.')[-1]
            cmd=dk[ex]
            print 'cmd1',cmd
            g=_chname(f)
            cmd=cmd % (f,g)
            print 'cmd2',cmd
            try:
                check_call(cmd,shell=True)
                dllist[i][1]='1'
                print dllist[i]
            except CalledProcessError,err:
                print err
def main():
    _readCsv('@@dl.csv')
    _readLog('@@conv.log')
    #convMP3()
    addIDS()
    #_writeLog('@@conv.log')
if __name__=='__main__':main()


