import wget
import urllib.parse

# TODO read file line by line as JSON objects
# TODO determine if GDrive url
# TODO if Gdrive url 

url = 'http://rehosts.fightthe.pw/csc-2019-05/Joe%20Satriani%20-%20Killer%20Bee%20Bop.zip'
decodedUrl = urllib.parse.unquote(url)
saveDir = '/disks/Benny2TB/db/Songs/'
wget.download(decodedUrl, saveDir)
print(f'\ndownloaded {decodedUrl} to {saveDir}')