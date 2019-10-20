import wget
import urllib.parse
import json
import re
# import threading
import config

with open('songs-20191009.jsonl') as file:
    for line in file:
        lineJSON = json.loads(line)

        md5_hash = lineJSON['md5_hash']
        url = urllib.parse.unquote(lineJSON['url'])

        domain = re.match(r'.*?://(.*?)/', url).group(1)

        # TODO make downloads asynchronous

        if 'drive.google' in domain:
            # use drive api            
            pass
        else:
            wget.download(urllib.parse.unquote(url), config.saveDir)

        print(f'\ndownloaded {url} to {config.saveDir}')
