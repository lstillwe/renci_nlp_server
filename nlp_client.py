import sys
import requests

biz_html_file = open('/renci_nlp_server/test_files/raw_news_for_ipo_test.html', 'r')
html_content = biz_html_file.read()
#print html_content

# need to get "url" or some equivalent somewhere - input var?
# also need to fill in event - this can probably be an input from CyVerse app

thedata = {'html': html_content,
	'url': 'www.bizjournals.com/austin/blog/techflash/2016/04/dell-cybersecurity-arm-slashes-ipo-price-shares.htm',
        'event': 'IPO'
        }
r = requests.post('http://127.0.0.1:5000/nlp', data=thedata)

# write to output file here
print r.text
