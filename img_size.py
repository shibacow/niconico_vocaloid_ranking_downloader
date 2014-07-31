#!/usr/bin/env python
# -*- coding:utf-8 -*-
from PIL import  Image
from glob import glob
def main():
    for f in glob('img/*.jpeg'):
        try:
            img=Image.open(f)
            #print img.size
        except IOError,err:
            pass
            print f,err
if __name__=='__main__':main()
