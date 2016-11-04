import requests

# Test 1
data = {'html': '',
        'url': 'www.bizjournals.com/boston/blog/bioflash/2016/02/cambridge-developer-of-cystic-fibrosis-drugs-joins.html',
        'event': 'None'}

r = requests.post('http://127.0.0.1:5000/nlp', data=data)
print r.text
assert r.text == 'Received data is Empty.'

# Test 2
data1 = {'html': 'a',
         'url': 'aaa',
         'event': 'None'}

r = requests.post('http://127.0.0.1:5000/nlp', data=data1)
print r.text
assert r.text == 'Received html is not compatible with our parsers.'

# Test 3
data2 = {'html': 'a',
         'url': 'www.bizjournals.com/boston/blog/bioflash/2016/02/cambridge-developer-of-cystic-fibrosis-drugs-joins.html',
         'event': 'None'}

r = requests.post('http://127.0.0.1:5000/nlp', data=data2)
print r.text
assert r.text == 'Received html is not compatible with our parsers.'


# Test 4
ipo_file = open('raw_news_for_ipo_test.html', 'r')
html_content = ipo_file.read()
data3 = {'html': html_content,
         'url': 'www.bizjournals.com/austin/blog/techflash/2016/04/dell-cybersecurity-arm-slashes-ipo-price-shares.htm',
         'event': 'IPO'
         }
r = requests.post('http://127.0.0.1:5000/nlp', data=data3)
print r.text

# Test 5
layoff_file = open('raw_news_for_layoff_test.html', 'r')
html_content = layoff_file.read()
data4 = {'html': html_content,
         'url': "www.bizjournals.com/triangle/news/2016/05/06/teleflex-division-to-lay-off-456-in-north-carolina.htm",
         'event': 'Layoff'
         }
r = requests.post('http://127.0.0.1:5000/nlp', data=data4)
print r.text
