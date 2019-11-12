import wget
import urllib.parse
import json
import re
import threading
import os
import hashlib
import shutil
import sqlite3
import glob
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pyunpack import Archive
from pyunpack import PatoolError
from random import randint


def startDownloads(songsFolder):
    gauth = GoogleAuth()  # Google Drive authentication
    gauth.LocalWebserverAuth()  # Needed only for initial auth
    drive = GoogleDrive(gauth)

    connection = sqlite3.connect('../ChartBase.db')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM links WHERE downloaded=0')

    links = cursor.fetchall()

    for link in links:
        url = link[0]
        source = link[1]
        urlDecoded = urllib.parse.unquote(url)

        domain = re.search(r'.*?://(.*?)/', urlDecoded).group(1)

        tmpFolder = os.path.join(songsFolder, 'tmp/')

        if not os.path.exists(tmpFolder):
            os.mkdir(tmpFolder)

        if 'drive.google' in domain:
            try:
                print(f'downloading from gDrive: {url}')
                gDriveDownload(drive, urlDecoded, tmpFolder)
            except (KeyboardInterrupt, SystemExit):
                if os.path.exists(tmpFolder):
                    print(f'removing tmpFolder due to sysexit: {tmpFolder}')
                    shutil.rmtree(tmpFolder)

                raise
            except:
                cursor.execute(
                    f'UPDATE links SET downloaded=-1 WHERE url="{url}"')
                connection.commit()

                if os.path.exists(tmpFolder):
                    print(f'removing tmpFolder due to except: {tmpFolder}')
                    shutil.rmtree(tmpFolder)

            if os.path.exists(tmpFolder):
                print(f'importing: {url}')
                importDownloaded(songsFolder, url, source, connection)

                print(f'updating in db: {url}')
                cursor.execute(
                    f'UPDATE links SET downloaded=1 WHERE url="{url}"')
                connection.commit()
        else:
            try:
                print(f'downloading: {url}')
                _ = wget.download(urlDecoded, tmpFolder)
            except (KeyboardInterrupt, SystemExit):
                if os.path.exists(tmpFolder):
                    print(f'removing tmpFolder due to sysexit: {tmpFolder}')
                    shutil.rmtree(tmpFolder)

                raise
            except:
                cursor.execute(
                    f'UPDATE links SET downloaded=-1 WHERE url="{url}"')
                connection.commit()

                if os.path.exists(tmpFolder):
                    print(f'removing tmpFolder due to except: {tmpFolder}')
                    shutil.rmtree(tmpFolder)

            if os.path.exists(tmpFolder):
                print(f'importing: {url}')
                importDownloaded(songsFolder, url, source, connection)

                print(f'updating in db: {url}')
                cursor.execute(
                    f'UPDATE links SET downloaded=1 WHERE url="{url}"')
                connection.commit()


def gDriveDownload(drive, url, folderPath):
    fileID = re.search(r'//.*(?:/folders|/d)/([^/,\n]*)', url).group(1)

    driveFile = drive.CreateFile({'id': fileID})

    if 'folder' in driveFile['mimeType']:
        fileList = drive.ListFile(
            {'q': "'{}' in parents and trashed=false".format(fileID)}).GetList()

        nestedDir = folderPath + driveFile['title']

        if not os.path.exists(nestedDir):
            os.makedirs(nestedDir)

        for siblingFile in fileList:
            if 'folder' not in siblingFile['mimeType']:
                siblingFile.GetContentFile(
                    f"{nestedDir}/{siblingFile['title']}", mimetype=siblingFile['mimeType'])

    else:
        driveFile.GetContentFile(
            folderPath + driveFile['title'], mimetype=driveFile['mimeType'])


def importDownloaded(songsFolder, url, source, connection):
    cursor = connection.cursor()

    unpackAll(songsFolder)
    bringFoldersUp(songsFolder)
    clean(songsFolder)

    def isGoodSong(folderPath):
        hasChart = False
        hasSong = False

        for item in os.listdir(folderPath):
            if item == 'notes.chart' or item == 'notes.mid':
                hasChart = True
            elif item == 'song.mp3' or item == 'song.ogg':
                hasSong = True

        return True if hasChart and hasSong else False

    tmpFolder = os.path.join(songsFolder, 'tmp/')

    for folder in os.listdir(tmpFolder):
        folderPath = os.path.join(tmpFolder, folder)
        if isGoodSong(folderPath):
            folderHash, folderPath = appendHashToFolder(
                os.path.join(tmpFolder, folder))

            downloadedFolder = songsFolder + 'downloaded/'
            if not os.path.exists(downloadedFolder):
                os.mkdir(downloadedFolder)

            newFolderPath = os.path.join(
                downloadedFolder, os.path.basename(folderPath))

            try:
                cursor.execute('INSERT INTO songs VALUES (?, ?, ?, ?, ?)',
                               (folder, url, source, folderHash, newFolderPath))
                connection.commit()

                shutil.move(folderPath, downloadedFolder)
            except sqlite3.IntegrityError:
                print(f'removing due to sql exception: {folderPath}')
                shutil.rmtree(folderPath)
        else:
            rejectsFolder = os.path.join(songsFolder, 'rejects/')

            if not os.path.exists(rejectsFolder):
                os.mkdir(rejectsFolder)

            print(f'moving to rejects due to bad song: {folderPath}')

            if not os.path.exists(os.path.join(rejectsFolder, folder)):
                shutil.move(folderPath, rejectsFolder)
            else:
                shutil.rmtree(folderPath)

    shutil.rmtree(tmpFolder)


def unpackAll(songsFolder):
    tmpFolder = os.path.join(songsFolder, 'tmp/')

    os.chdir(tmpFolder)

    zips = getZipsRecursively(tmpFolder)

    while len(zips) > 0:
        for zipFile in zips:
            try:
                print(f'extracting: {zipFile} -> {os.path.dirname(zipFile)}')
                Archive(zipFile).extractall(os.path.dirname(zipFile))

                print(f'removing extracted: {zipFile}')
                os.remove(zipFile)
            except (PatoolError, OSError, NotImplementedError):
                rejectsFolder = os.path.join(songsFolder, 'rejects/')

                if not os.path.exists(rejectsFolder):
                    os.mkdir(rejectsFolder)

                if os.path.exists(os.path.join(rejectsFolder, os.path.basename(zipFile))):
                    print(
                        f'removing zip, already exists in rejects: {zipFile}')
                    os.remove(zipFile)
                else:
                    print(f'cannot unzip, rejecting: {zipFile}')
                    shutil.move(zipFile, rejectsFolder)
        zips = getZipsRecursively(tmpFolder)


def getZipsRecursively(folder):
    zips = glob.glob(folder + '**/*.zip', recursive=True)
    zips.extend(glob.glob(folder + '**/*.rar', recursive=True))
    zips.extend(glob.glob(folder + '**/*.7z', recursive=True))
    return zips


def bringFoldersUp(songsFolder):
    tmpFolder = os.path.join(songsFolder, 'tmp/')

    os.chdir(tmpFolder)

    for item in os.listdir(tmpFolder):
        itemPath = os.path.join(tmpFolder, item)

        if os.path.isdir(itemPath):

            for subItem in os.listdir(itemPath):
                subItemPath = os.path.join(itemPath, subItem)

                if os.path.isdir(subItemPath):
                    subdirList = [x[0] for x in os.walk(subItemPath)]
                    subdirList.reverse()

                    for subdir in subdirList:
                        print(f'moving: {subdir} -> {tmpFolder}')

                        try:
                            shutil.move(subdir, tmpFolder)
                        except shutil.Error:
                            newName = f'{subdir} ({str(randint(1, 1000000))})'

                            print(
                                f'renaming already exists: {subdir} -> {newName}')
                            os.rename(subdir, newName)

                            print(
                                f'moving newly named: {newName} -> {tmpFolder}')
                            shutil.move(newName, tmpFolder)


# Removes extra files, empty folders, and renames what's possible
def clean(songsFolder):
    tmpFolder = os.path.join(songsFolder, 'tmp/')

    os.chdir(tmpFolder)

    for songFolder in os.listdir(tmpFolder):
        songFolderPath = os.path.join(tmpFolder, songFolder)

        # Remove files in root folder
        if not os.path.isdir(songFolderPath):
            print(f'removing file in root folder: {songFolderPath}')
            os.remove(songFolderPath)
        # Remove empty folders
        elif os.path.isdir(songFolderPath) and not os.listdir(songFolderPath):
            print(f'removing empty folder: {songFolderPath}')
            shutil.rmtree(songFolderPath)
        elif isWeird(songFolderPath):
            for item in os.listdir(songFolderPath):
                itemPath = os.path.join(songFolderPath, item)

                # Remove unwanted filetypes basic renaming
                if not item.endswith(('.chart', '.mid', '.ini', '.mp3', '.ogg')):
                    print(f'removing misc file: {itemPath}')
                    os.remove(itemPath)
                elif item != 'notes.chart' and item.lower() == 'notes.chart':
                    print(
                        f'renaming due to case: {itemPath} -> {os.path.join(songFolderPath, "notes.chart")}')
                    os.rename(itemPath, os.path.join(
                        songFolderPath, 'notes.chart'))
                elif item != 'notes.mid' and item.lower() == 'notes.mid':
                    print(
                        f'renaming due to case: {itemPath} -> {os.path.join(songFolderPath, "notes.mid")}')
                    os.rename(itemPath, os.path.join(
                        songFolderPath, 'notes.mid'))
                elif item != 'song.ini' and item.lower() == 'song.ini':
                    print(
                        f'renaming due to case: {itemPath} -> {os.path.join(songFolderPath, "song.ini")}')
                    os.rename(itemPath, os.path.join(
                        songFolderPath, 'song.ini'))
                elif item != 'song.mp3' and item.lower() == 'song.mp3':
                    print(
                        f'renaming due to case: {itemPath} -> {os.path.join(songFolderPath, "song.mp3")}')
                    os.rename(itemPath, os.path.join(
                        songFolderPath, 'song.mp3'))
                elif item != 'song.ogg' and item.lower() == 'song.ogg':
                    print(
                        f'renaming due to case: {itemPath} -> {os.path.join(songFolderPath, "song.ogg")}')
                    os.rename(itemPath, os.path.join(
                        songFolderPath, 'song.ogg'))

                # Remove bad ini files
                if item.endswith('.ini') and item != 'song.ini':
                    print(f'removing bad ini: {itemPath}')
                    os.remove(itemPath)

    for songFolder in os.listdir(tmpFolder):
        songFolderPath = os.path.join(tmpFolder, songFolder)

        # Try to fix cases of multiple wrongly named files
        if isWeird(songFolderPath):
            oggCount = 0
            mp3Count = 0
            chartCount = 0
            midCount = 0
            hasGoodAudio = False
            hasGoodChart = False

            for item in os.listdir(songFolderPath):
                if item.endswith('.ogg'):
                    oggCount += 1
                elif item.endswith('.mp3'):
                    mp3Count += 1
                elif item.endswith('.chart'):
                    chartCount += 1
                elif item.endswith('.mid'):
                    midCount += 1

                if item == 'song.ogg' or item == 'song.mp3':
                    hasGoodAudio = True
                elif item == 'notes.chart' or item == 'notes.mid':
                    hasGoodChart = True

            if hasGoodAudio:
                hasGoodOogFile = False
                hasGoodMp3File = False

                for item in os.listdir(songFolderPath):
                    itemPath = os.path.join(songFolderPath, item)

                    if item == 'song.ogg':
                        hasGoodOogFile = True
                    elif item == 'song.mp3':
                        hasGoodMp3File = True

                if hasGoodOogFile:
                    for item in os.listdir(songFolderPath):
                        itemPath = os.path.join(songFolderPath, item)

                        if item.endswith('.mp3'):
                            print(f'removing dupe audio: {itemPath}')
                            os.remove(itemPath)
                        elif item.endswith('.ogg') and item != 'song.ogg':
                            print(f'removing dupe ogg: {itemPath}')
                            os.remove(itemPath)
                elif hasGoodMp3File:
                    for item in os.listdir(songFolderPath):
                        itemPath = os.path.join(songFolderPath, item)

                        if item.endswith('.ogg'):
                            print(f'removing dupe audio: {itemPath}')
                            os.remove(itemPath)
                        elif item.endswith('.mp3') and item != 'song.mp3':
                            print(f'removing dupe mp3: {itemPath}')
                            os.remove(itemPath)
            elif oggCount + mp3Count == 1:
                for item in os.listdir(songFolderPath):
                    itemPath = os.path.join(songFolderPath, item)

                    if item.endswith('.ogg'):
                        print(
                            f'renaming lone audio file: {itemPath} -> {os.path.join(songFolderPath, "song.ogg")}')
                        os.rename(itemPath, os.path.join(
                            songFolderPath, 'song.ogg'))
                    elif item.endswith('.mp3'):
                        print(
                            f'renaming lone audio file: {itemPath} -> {os.path.join(songFolderPath, "song.mp3")}')
                        os.rename(itemPath, os.path.join(
                            songFolderPath, 'song.mp3'))
            elif oggCount + mp3Count == 2:
                previewFilePath = None

                for item in os.listdir(songFolderPath):
                    itemPath = os.path.join(songFolderPath, item)

                    if item.lower() == 'preview.ogg' or item.lower() == 'preview.mp3':
                        previewFilePath = itemPath

                if previewFilePath is not None:
                    print(f'removing preview: {previewFilePath}')
                    os.remove(previewFilePath)

                    for item in os.listdir(songFolderPath):
                        itemPath = os.path.join(songFolderPath, item)

                        if item.endswith(('.ogg', '.mp3')):
                            newFileName = os.path.join(
                                songFolderPath, 'song' + os.path.splitext(item)[1])
                            print(
                                f'renaming other than preview: {itemPath} -> {newFileName}')
                            os.rename(itemPath, newFileName)

            if hasGoodChart:
                hasGoodChartFile = False
                hasGoodMidFile = False

                for item in os.listdir(songFolderPath):
                    itemPath = os.path.join(songFolderPath, item)

                    if item == 'notes.chart':
                        hasGoodChartFile = True
                    elif item == 'notes.mid':
                        hasGoodMidFile = True

                if hasGoodChartFile:
                    for item in os.listdir(songFolderPath):
                        itemPath = os.path.join(songFolderPath, item)

                        if item.endswith('.mid'):
                            print(f'removing dupe mid: {itemPath}')
                            os.remove(itemPath)
                        elif item.endswith('.chart') and item != 'notes.chart':
                            print(f'removing dupe chart: {itemPath}')
                            os.remove(itemPath)
                elif hasGoodMidFile:
                    for item in os.listdir(songFolderPath):
                        itemPath = os.path.join(songFolderPath, item)

                        if item.endswith('.chart'):
                            print(f'removing dupe chart: {itemPath}')
                            os.remove(itemPath)
                        elif item.endswith('.mid') and item != 'notes.mid':
                            print(f'removing dupe mid: {itemPath}')
                            os.remove(itemPath)
            elif chartCount + midCount == 1:
                for item in os.listdir(songFolderPath):
                    itemPath = os.path.join(songFolderPath, item)

                    if item.endswith('.chart'):
                        print(
                            f'renaming lone chart file: {itemPath} -> {os.path.join(songFolderPath, "notes.chart")}')
                        os.rename(itemPath, os.path.join(
                            songFolderPath, 'notes.chart'))
                    elif item.endswith('.mid'):
                        print(
                            f'renaming lone chart file: {itemPath} -> {os.path.join(songFolderPath, "notes.mid")}')
                        os.rename(itemPath, os.path.join(
                            songFolderPath, 'notes.mid'))


def isWeird(folderPath):
    os.chdir(folderPath)

    songCount = 0
    chartCount = 0

    for item in os.listdir(folderPath):
        if item == 'song.ogg' or item == 'song.mp3':
            songCount += 1
        elif item == 'notes.chart' or item == 'notes.mid':
            chartCount += 1
        if item not in ('notes.chart', 'notes.mid', 'song.ini', 'song.mp3', 'song.ogg'):
            return True

    if songCount != 1 or chartCount != 1:
        return True

    return False


# Appends hash of chart or mid file to folder name, returns a tuple of the hash and folderPath
def appendHashToFolder(folderPath):
    chart = None
    mid = None
    folderHash = None

    for item in os.listdir(folderPath):
        if item.endswith('.chart'):
            chart = item
        elif item.endswith('.mid'):
            mid = item

    if chart == None and mid == None:
        print(f'no file to hash exists in {folderPath}')
    elif chart == None:
        hasher = hashlib.md5()

        with open(os.path.join(folderPath, mid), 'rb') as hashFile:
            buf = hashFile.read()
            hasher.update(buf)

        folderHash = hasher.hexdigest()
    else:
        hasher = hashlib.md5()

        with open(os.path.join(folderPath, chart), 'rb') as hashFile:
            buf = hashFile.read()
            hasher.update(buf)

        folderHash = hasher.hexdigest()

    newFolderName = folderPath + ' md5=' + folderHash
    os.rename(folderPath, newFolderName)

    return (folderHash, newFolderName)


def updateDB():
    connection = sqlite3.connect('../ChartBase.db')
    cursor = connection.cursor()

    cursor.execute('SELECT hash, path FROM songs')

    songs = cursor.fetchall()

    for song in songs:
        songHash = song[0]
        path = song[1]

        if not os.path.exists(path):
            print(f'does not exist, removing {path}')

            cursor.execute(f'DELETE FROM songs WHERE hash="{songHash}"')
            connection.commit()


def removeBadSongs(badsongsTxt, cloneheroPath, songsFolder):

    CHSongsPath = os.path.join(cloneheroPath, 'Songs/')
    downloadedFolder = os.path.join(songsFolder, 'downloaded/')

    with open(badsongsTxt) as badsongs:
        for badsong in badsongs:

            realPath = badsong.strip('\n').replace(
                CHSongsPath, downloadedFolder)

            print(f'removing: {realPath}')
            shutil.rmtree(realPath)

    updateDB()


def resetDownloads():
    connection = sqlite3.connect('../ChartBase.db')
    cursor = connection.cursor()

    cursor.execute('UPDATE links SET downloaded=0 WHERE downloaded=1')
    cursor.execute('DELETE FROM songs')
    connection.commit()
