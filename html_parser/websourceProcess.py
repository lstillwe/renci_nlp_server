import psycopg2
from html_parsers import parser1
import os
import sys
from ConfigParser import ConfigParser

config = ConfigParser()
config.read('db_config.ini')


    # result = parser1()
    # if result == None:
    #     print 'Parser does not match with html'
    # # result['url'] = file_url_label[file_name][0]
    # result['label'] = file_url_label[file_name][1]
    # result['path'] = os.path.join(current_folder, file_name)
    # result['doc_id'] =
    # below is to generate data in json file
    # and mapping original html file to another path with the same file name
    # with open(os.path.join(PATH,'IPO_Data.json'),'w') as f:
    # f.write(json.dumps(results))
    # for result in results:
    # map_path = result['path'].replace('IPO_List2','MAP_IPO_List2')
    # with open(map_path,'w') as f:
    # write_data(f,result)




