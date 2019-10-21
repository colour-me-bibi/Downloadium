import json
import urllib.parse

# Remove downloaded songs from the master list
with open('downloaded.txt') as masterFile:
    for masterLine in masterFile:
        with open('songs-20191009.jsonl', 'r') as readFile:
            lines = readFile.readlines()
        with open('songs-20191009.jsonl', 'w') as writeFile:
            for line in lines:
                lineJSON = json.loads(line)
                if masterLine.strip('\n') != urllib.parse.unquote(lineJSON['url']):
                    writeFile.write(line)
