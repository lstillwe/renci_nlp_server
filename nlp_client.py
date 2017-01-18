import sys
import requests

workspacedir = "/renci_nlp_server/scratch/"

event = sys.argv[1]
if ((event == "LAYOFF") or (event == "layoff")):
	event = "Layoff"
elif (event == "ipo"):
	event = "IPO"
html_file = workspacedir + sys.argv[2]

result_file_name = workspacedir + event + "_nlp_results.json"

#biz_html_file = open('/renci_nlp_server/test_files/raw_news_for_ipo_test.html', 'r')
biz_html_file = open(html_file, 'r')
html_content = biz_html_file.read()
#print html_content

# need to get "url" or some equivalent somewhere - input var?
# also need to fill in event - this can probably be an input from CyVerse app

thedata = {'html': html_content,
	'url': 'www.bizjournals.com/austin/blog/techflash/2016/04/dell-cybersecurity-arm-slashes-ipo-price-shares.htm',
        #'event': 'IPO'
        'event': 'event'
        }
r = requests.post('http://127.0.0.1:5000/nlp', data=thedata)

# write to output file here
result_file = open(result_file_name, 'w')
result_file.write(r.text)
#print r.text

# done - close up everything
biz_html_file.close()
result_file.close()
