import urllib.request

urls = ['http://127.0.0.1:8000/', 'http://127.0.0.1:8000/shop/']
for u in urls:
    try:
        r = urllib.request.urlopen(u, timeout=5)
        b = r.read().decode('utf-8', errors='ignore')
        print(u, 'OK', len(b), 'chars', 'NoReverseMatch' in b)
    except Exception as e:
        print(u, 'ERROR', e)
