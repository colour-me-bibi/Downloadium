import wget
import urllib.parse
import json
import re
import threading
import config
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Google Drive authentication
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

def gDriveDownload(url):
    fileID = re.search(r'//.*(?:folders|d)/([^/,\n]*)', url).group(1)
    print(fileID)
    driveFile = drive.CreateFile({'id': fileID})
    print('title: %s, mimeType: %s' % (driveFile['title'], driveFile['mimeType']))
    # pass

def download(url):
    pass
    # wget.download(url, config.saveDir)
    # print(f'\ndownloaded {url} to {config.saveDir}')

with open('songs-20191009.jsonl') as file:
    for line in file:
        lineJSON = json.loads(line)

        md5_hash = lineJSON['md5_hash']
        url = urllib.parse.unquote(lineJSON['url'])

        domain = re.search(r'.*?://(.*?)/', url).group(1)

        # TODO thread downloads

        if 'drive.google' in domain:
            gDriveDownload(url)
            # gThread = threading.Thread(target=gDriveDownload, args=[url])
            # gThread.start()
        else:
            dThread = threading.Thread(target=download(url), args=[url])
            dThread.start()
