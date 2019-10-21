import wget
import urllib.parse
import json
import re
import threading
import os
import config
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Google Drive authentication
gauth = GoogleAuth()
# gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

def gDriveDownload(url):
    fileID = re.search(r'//.*(?:folders|d)/([^/,\n]*)', url).group(1)
    driveFile = drive.CreateFile({'id': fileID})

    if 'folder' in driveFile['mimeType']:
        fileList = drive.ListFile({'q': "'{}' in parents and trashed=false".format(fileID)}).GetList()

        nestedDir = f"{config.saveDir}/{driveFile['title']}"

        if not os.path.exists(nestedDir):
            os.makedirs(nestedDir)

        for siblingFile in fileList:
            siblingFile.GetContentFile(f"{nestedDir}/{siblingFile['title']}", mimetype=siblingFile['mimeType'])
        with open('downloaded.txt', 'a') as writeFile:
            writeFile.write(url + '\n')
    else:
        driveFile.GetContentFile(f"{config.saveDir}/{driveFile['title']}", mimetype=driveFile['mimeType'])
        with open('downloaded.txt', 'a') as writeFile:
            writeFile.write(url + '\n')

def download(url):
    wget.download(url, config.saveDir)
    with open('downloaded.txt', 'a') as writeFile:
            writeFile.write(url + '\n')

with open('songs-20191009.jsonl') as file:
    for line in file:
        lineJSON = json.loads(line)

        md5_hash = lineJSON['md5_hash']
        url = urllib.parse.unquote(lineJSON['url'])

        domain = re.search(r'.*?://(.*?)/', url).group(1)

        if 'drive.google' in domain:
            gThread = threading.Thread(target=gDriveDownload, args=[url])
            gThread.start()
        else:
            dThread = threading.Thread(target=download(url), args=[url])
            dThread.start()
