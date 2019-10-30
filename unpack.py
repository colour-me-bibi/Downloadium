import os, shutil
from pyunpack import Archive
from pathlib import Path

song_dir = '/disks/Benny2TB/db/sanitized/'
rejects_dir = 'disks/Benny2TB/db/rejects/'
zip_exts = ('.rar', '.zip', '.7z')
patool_path = '/home/bibi/.local/lib/python3.7/site-packages/patoolib/configuration.py'

os.chdir(song_dir)

def unpack(dir):

    def getPackedCount(dir):
        packedCount = 0
        for item in os.listdir(dir):
            itemPath = os.path.join(dir, item)

            if itemPath.endswith(zip_exts):
                packedCount += 1

        return packedCount

    packedCount = getPackedCount(dir)

    while packedCount > 0:
        for item in os.listdir(dir):
            itemPath = os.path.join(dir, item)
            if item.endswith(zip_exts):
                try:
                    Archive(itemPath).extractall(Path(song_dir))
                    print(f'extracted {itemPath}')
                    os.remove(itemPath)
                except NotImplementedError:
                    print(f'Cannot unpack {itemPath}')
                    shutil.move(itemPath, rejects_dir)
        packedCount = getPackedCount(dir)

# Make sure no files in root dir
def rmMiscFiles(directory):
    for item in os.listdir(directory):
        itemPath = os.path.join(directory, item)

        if os.path.isdir(itemPath):
            print(f'folder: {item}')
            if not os.listdir(itemPath):
                os.rmdir(itemPath)
            else:
                rmMiscFiles(itemPath)
        else:
            keepFiles = ('.chart', '.mid', '.ini', '.mp3', '.ogg')
            if not item.endswith(keepFiles):
                os.remove(itemPath)

def dirCount(directory):
    dirCount = 0

    for item in os.listdir(directory):
        itemPath = os.path.join(directory, item)

        if os.path.isdir(itemPath):
            dirCount += 1

    return dirCount

def organizeFolders(dir):

    def moveUp(subdir):
        if dirCount(subdir) == 0:
            try:
                shutil.move(subdir, song_dir)
            except:
                print(f'already exists: {subdir}')
                shutil.rmtree(subdir)
        else:
            for subItem in os.listdir(subdir):
                subItemPath = os.path.join(subdir, subItem)

                if os.path.isdir(subItemPath):
                    moveUp(subItemPath)

    def getSubdirCount(dir):
        subdirCount = 0
        for item in os.listdir(dir):
            itemPath = os.path.join(dir, item)
            if os.path.isdir(itemPath):
                subdirCount += dirCount(itemPath)
        return subdirCount

    subdirCount = getSubdirCount(dir)

    while subdirCount > 0:
        for item in os.listdir(dir):
            itemPath = os.path.join(dir, item)

            if os.path.isdir(itemPath) and dirCount(itemPath) != 0:
                moveUp(itemPath)
        subdirCount = getSubdirCount(dir)

def rmEmptyDir(dir):
    for item in os.listdir(dir):
        itemPath = os.path.join(dir, item)
        if os.path.isdir(itemPath) and not os.listdir(itemPath):
            os.rmdir(itemPath)

def rmBadSongs(dir):
    for item in os.listdir(dir):
        itemPath = os.path.join(dir, item)

        hasChart = False
        hasIni = False
        hasSong = False

        for subItem in os.listdir(itemPath):
            # subItemPath = os.path.join(itemPath, subItem)

            if subItem.endswith(('.chart', '.mid')):
                hasChart = True
            elif subItem.endswith('.ini'):
                hasIni = True
            elif subItem.endswith(('.mp3', '.ogg')):
                hasSong = True
        
        if not (hasChart and hasIni and hasSong):
            shutil.rmtree(itemPath)

def fixNames(dir):
    for item in os.listdir(dir):
        itemPath = os.path.join(dir, item)

        for subItem in os.listdir(itemPath):
            subItemPath = os.path.join(itemPath, subItem)

            if subItem == 'Notes.chart':
                print(subItemPath)
                os.rename(subItemPath, itemPath + '/notes.chart')

def renameAnomalies(dir):
    for folder in os.listdir(dir):
        folderPath = os.path.join(dir, folder)

        hasGoodSong = False
        songCount = 0
        hasGoodChart = False
        chartCount = 0

        for item in os.listdir(folderPath):
            itemPath = os.path.join(folderPath, item)

            if item == 'song.mp3' or item == 'song.ogg':
                hasGoodSong = True

            if item.endswith(('.mp3', '.ogg')):
                songCount += 1

            if item == 'notes.chart' or item == 'notes.mid':
                hasGoodChart = True

            if item.endswith(('.chart', '.mid')):
                chartCount += 1
        
        if hasGoodSong:
            for item in os.listdir(folderPath):
                itemPath = os.path.join(folderPath, item)

                if item.endswith(('.mp3', '.ogg')) and item != 'song.mp3' and item != 'song.ogg':
                    print(f'will remove: {itemPath}')
                    os.remove(itemPath)
        elif not hasGoodSong and songCount == 1:
            for item in os.listdir(folderPath):
                itemPath = os.path.join(folderPath, item)

                if item.endswith('.mp3'):
                    print(f'will rename {itemPath} to {folderPath + "/song.mp3"}')
                    os.rename(itemPath, folderPath + '/song.mp3')
                elif item.endswith('.ogg'):
                    print(f'will rename {itemPath} to {folderPath + "/song.ogg"}')
                    os.rename(itemPath, folderPath + '/song.ogg')
        else:
            print(f'weird: {folderPath}')

        if hasGoodChart:
            for item in os.listdir(folderPath):
                itemPath = os.path.join(folderPath, item)

                if item.endswith(('.chart', '.mid')) and item != 'notes.chart' and item != 'notes.mid':
                    print(f'will remove: {itemPath}')
                    os.remove(itemPath)
        elif not hasGoodChart and chartCount == 1:
            for item in os.listdir(folderPath):
                itemPath = os.path.join(folderPath, item)

                if item.endswith('.chart'):
                    print(f'will rename {itemPath} to {folderPath + "/notes.chart"}')
                    os.rename(itemPath, folderPath + '/notes.chart')
                elif item.endswith('.mid'):
                    print(f'will rename {itemPath} to {folderPath + "/notes.mid"}')
                    os.rename(itemPath, folderPath + '/notes.mid')
        else:
            print(f'weird: {folderPath}')

def idAnomalies(dir):
    imperfectFolders = set()

    for folder in os.listdir(dir):
        folderPath = os.path.join(dir, folder)

        for item in os.listdir(folderPath):
            itemPath = os.path.join(folderPath, item)

            if item.endswith('.mid') and item != 'notes.mid':
                imperfectFolders.add(folderPath)
            elif item.endswith('.chart') and item != 'notes.chart':
                imperfectFolders.add(folderPath)
            elif item.endswith('.ogg') and item != 'song.ogg':
                imperfectFolders.add(folderPath)
            elif item.endswith('.mp3') and item != 'song.mp3':
                imperfectFolders.add(folderPath)
            elif item.endswith('.ini') and item != 'song.ini':
                imperfectFolders.add(folderPath)
            elif not item.endswith(('.mid', '.chart', '.ini', '.ogg', '.mp3')):
                print(f'weird: {folderPath}')

    os.chdir('/home/bibi/Projects/ChartBase/')

    with open('imperfect.txt', 'a') as writeFile:
        for e in imperfectFolders:
            writeFile.write(e + '\n')

def idExtra(dir):
    for folder in os.listdir(dir):
        folderPath = os.path.join(dir, folder)

        for item in os.listdir(folderPath):
            itemPath = os.path.join(folderPath, item)

            if item not in ('notes.chart', 'notes.mid', 'song.ini', 'song.mp3', 'song.ogg'):
                print(itemPath)

def idDupeChart(dir):
    for folder in os.listdir(dir):
        folderPath = os.path.join(dir, folder)

        hasChart = False
        hasMid = False

        for item in os.listdir(folderPath):
            itemPath = os.path.join(folderPath, item)

            if item == 'notes.chart':
                hasChart = True
            elif item == 'notes.mid':
                hasMid = True
        
        if hasChart and hasMid:
            print(f'will remove: {folderPath + "/notes.mid"}')
            os.remove(folderPath + '/notes.mid')
        elif not hasChart and not hasMid:
            print(f'has no chart or mid: {folderPath}')

def idDupeSong(dir):
    for folder in os.listdir(dir):
        folderPath = os.path.join(dir, folder)

        hasMp3 = False
        hasOgg = False

        for item in os.listdir(folderPath):
            itemPath = os.path.join(folderPath, item)

            if item == 'song.mp3':
                hasMp3 = True
            elif item == 'song.ogg':
                hasOgg = True
        
        if hasMp3 and hasOgg:
            print(f'will remove: {folderPath + "/song.mp3"}')
            # os.remove(folderPath + '/song.mp3')
        elif not hasMp3 and not hasOgg:
            print(f'has no mp3 or ogg: {folderPath}')

def countFiles(dir):
    for folder in os.listdir(dir):
        folderPath = os.path.join(dir, folder)

        if 'song.mp3' not in os.listdir(folderPath) and 'song.ogg' not in os.listdir(folderPath):
            print(f'no song: {folderPath}')

        if 'notes.chart' not in os.listdir(folderPath) and 'notes.mid' not in os.listdir(folderPath):
            print(f'no chart: {folderPath}')

        if 'song.ini' not in os.listdir(folderPath):
            print(f'no ini: {folderPath}')

if __name__ == '__main__':
    countFiles(song_dir)