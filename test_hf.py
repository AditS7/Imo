import urllib.request, json
req = urllib.request.Request('https://router.huggingface.co/v1/models')
try:
    resp = urllib.request.urlopen(req)
    models = json.loads(resp.read())
    providers = set()
    for m in models['data']:
        for p in m.get('providers', []):
            providers.add(p['provider'])
    print(providers)
except Exception as e:
    pass
