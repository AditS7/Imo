import urllib.request
import re

html_url = "https://adimusic.vercel.app/library"
html_req = urllib.request.Request(html_url)
html_resp = urllib.request.urlopen(html_req).read().decode('utf-8')

js_file_matches = re.findall(r'src="(/assets/index-[^"]+\.js)"', html_resp)
if js_file_matches:
    js_url = "https://adimusic.vercel.app" + js_file_matches[0]
    print(f"JS URL: {js_url}")
    js_req = urllib.request.Request(js_url)
    js_resp = urllib.request.urlopen(js_req).read().decode('utf-8')
    mp3_matches = re.findall(r'"(https://[^"]+\.mp3)"', js_resp)
    print(f"Found {len(mp3_matches)} mp3 files.")
    for mp3 in set(mp3_matches):
        print(mp3)
