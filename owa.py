#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: yang 
# Created: 2017-04-21 14:22:37

import os
import time
import json
from pyweb import ctx, get, put, post, jsonapi, badrequest, notfound

import base64
import hashlib


@jsonapi
@get("/wopi/files/:fileid")
def fileinfo(fileid):
    access_token = ctx.request.params.get("access_token")
    if not access_token:
        raise badrequest()
    if not os.path.exists(fileid):
        raise notfound()

    content = open(fileid).read()
    sha256 = base64.b64encode(hashlib.sha256(content).digest())

    return {"SHA256": sha256, "OwnerId":"27135603461040-164", "Version": sha256, "Size": len(content), "BaseFileName": fileid}


@get("/wopi/files/:fileid/contents")
def filecontent(fileid):
    access_token = ctx.request.params.get("access_token")
    if not access_token:
        raise badrequest()
    if not os.path.exists(fileid):
        raise notfound()
    content = open(fileid).read()
    return content


def preview():
    word_preview = "http://192.168.1.176/wv/wordviewerframe.aspx?WOPISrc=http://192.168.1.80:10010/wopi/files/dv.docx&access_token=abcd"
    ppt_preview = "http://192.168.1.206/p/PowerPointFrame.aspx?PowerPointView=ReadingView?WOPISrc=http://192.168.1.80:10010/wopi/files/dv.ppt&access_token=abcd"
    excel_preview = "http://192.168.1.206/x/_layouts/xlviewerinternal.aspx?WOPISrc=http://192.168.1.80:10010/wopi/files/dv.xlsx&access_token=abcd"
    pdf_perview = "http://192.168.1.206/wv/wordviewerframe.aspx?PdfMode=1&WOPISrc=http://192.168.1.80:10010/wopi/files/dv.pdf&access_token=abcd"
    pdf_image_perview = "http://192.168.1.206/wv/WordPreviewHandler.aspx?PdfMode=1&WOPISrc=http://192.168.1.80:10010/wopi/files/dv.pdf&access_token=abcd"
    print word_preview

if __name__ == "__main__":
    preview()
