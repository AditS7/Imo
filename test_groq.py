import urllib.request, json, os
req = urllib.request.Request('https://api.groq.com/openai/v1/models', headers={'Authorization': 'Bearer ' + os.getenv('GROQ_API_KEY', 'fake')})
try:
    resp = urllib.request.urlopen(req)
    print(resp.read())
except Exception as e:
    print(e)
