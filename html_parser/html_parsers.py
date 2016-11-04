from bs4 import BeautifulSoup
import re
import psycopg2
import psycopg2.extras
import logging

PER_PATT = re.compile('^(http://www.bizjournals.com/)?[\w]*/search/results\?q=.*')
COM_PATT = re.compile('^(http://www.bizjournals.com/)?profiles/company/.*')


# normal news html style
def parser(web_content):
    # initialize
    companies = []
    people = []
    content = None
    title = None
    date = None
    html_sp = BeautifulSoup(web_content, "html.parser")
    # clearing all js and form tag from web source
    for tag in html_sp.find_all('script'):
        tag.replaceWith('')
    for tag in html_sp.find_all('form'):
        tag.replaceWith('')
    try:
        date = html_sp.select("div.detail__meta time")[0].text
        title = html_sp.select("h1.detail__headline")[0].text
    except IndexError:
        date = 'Jan 01, 1910, 07:00am EDT'
        title = 'Cannot find title for article.'

    content_selector = html_sp.select("div.container .content__segment")
    if len(content_selector) == 0:
        content_selector = html_sp.select("div.content .content__segment")
    if len(content_selector) > 0:
        (content, companies, people) = process_elements(content_selector)
        logging.info('Html parsed finished by parser1.')
    else:
        logging.debug('Parser1 Is Not Compatible With Web Source.')
        return parser2(web_content)
    return {'company': companies, 'people': people, 'content': content, 'title': title, 'date': date}


# how-to / bizwoman html style
def parser2(web_content):
    # initialize
    companies = []
    people = []
    content = None
    title = None
    date = None
    html_sp = BeautifulSoup(web_content, "html.parser")
    # clearing all js and form tag from web source
    for tag in html_sp.find_all('script'):
        tag.replaceWith('')
    for tag in html_sp.find_all('form'):
        tag.replaceWith('')

    try:
        date = html_sp.select(".timestamp")[0].text.split('Update')[0].strip(' ').replace('\n', '')
        title = html_sp.select("h1.article__headline")[0].text
    except IndexError:
        date = 'Jan 01, 1910, 07:00am EDT'
        title = 'Cannot find title for article.'
    # date = datetime.strptime(date, '%b %d, %Y, %I:%M%p %Z')
    content_selector = html_sp.select(".article__content")
    if len(content_selector) > 0:
        # filter blank tag
        elements = [elem for elem in content_selector[0].contents if elem.name != None]
        (content, companies, people) = process_elements(elements)
        logging.info('Html parsed finished by parser2.')
    else:
        logging.debug('Parser2 Is Not Compatible With Web Source.')
        return None
    return {'company': companies, 'people': people, 'content': content, 'title': title, 'date': date}


# process news content from several html tags to make it readable
def process_elements(elements):
    companies = set()
    people = set()
    for elem in elements:
        if 'class' in elem.attrs and 'inline-related-links' in elem['class']:
            elem.clear('')
        if elem.name in ['p', 'ul', 'ol']:
            # find href refering person or organization
            for link in elem.findAll('a'):
                if COM_PATT.match(link.get('href')):
                    companies.add(link.get_text())
                elif PER_PATT.match(link.get('href')):
                    people.add(link.get_text())
    content = ''
    for elem in elements:
        if elem.name == 'div':
            continue
        elif elem.name == 'ul' or elem.name == 'ol':
            items = elem.findAll('li')
            if content.endswith(': '):
                for item in items:
                    content += item.text.strip() + ', '
                content = content.strip(', ') + '. '
            else:
                li_offset = 1
                for item in items:
                    content += str(li_offset) + '. ' + item.text.strip() + '. '
                    li_offset += 1
        elif len(elem.text.strip()) > 0:
            if elem.text.strip()[-1] in ['.', '?', '!', '"', ':']:
                content += elem.text.strip() + ' '
            else:
                content += elem.text.strip() + '. '

    elements = content.replace('\n', '').split('.')
    for i in xrange(0, len(elements)):
        if i != 0:
            if elements[i].startswith(' ') or elements[i] == '':
                pass
            elif elements[i][0].isupper():
                elements[i] = ' ' + elements[i]
    content = '.'.join(elements)
    return (content, list(companies), list(people))


# write result to file systems
def write_data(f, result):
    page_content = '<!DOCTYPE html><html><head><meta charset="utf-8">' + \
                   '<title>' + result['title'] + '</title>' + \
                   '</head><body><h1 id="new_title">' + result['title'] + '</h1>' + \
                   '<p id="new_time">' + result['date'] + '</p>' + \
                   '<p id="news_content">' + result['content'] + '</p>' + \
                   '<p> Organizations: <span class=".organization">' + \
                   '</span> - <span class=".organization">'.join(result['company']) + '</span></p>' + \
                   '<p> People: <span class=".person">' + \
                   '</span> - <span class=".organization">'.join(result['people']) + '</span></p>' + \
                   '<p> Reference: ' + result['url'] + '</p></body></html>'
    f.write(page_content.encode('utf-8'))


def update_news_db(result, db_name, username, pwd, host):
    con = None
    try:
        con = psycopg2.connect(database=db_name, user=username, password=pwd, host=host)
        cur = con.cursor()
        sql = 'INSERT INTO raw_news(url, news_text, news_time, news_title, mentioned_org, mentioned_people) \
        VALUES (%(url)s, %(content)s, %(date)s, %(title)s, %(company)s, %(people)s) RETURNING news_id'
        cur.execute(sql, result)
        news_id = cur.fetchone()[0]
        con.commit()
        return news_id
    except psycopg2.DatabaseError, e:
        logging.debug('Error %s' % e)
    finally:
        if con:
            con.close()


def get_news_by_url(url, db_name, username, pwd, host):
    con = None
    try:
        con = psycopg2.connect(database=db_name, user=username, password=pwd, host=host)
        cur = con.cursor()
        sql = 'SELECT news_id FROM raw_news WHERE url = %s'
        cur.execute(sql, (url,))
        news_id = cur.fetchone()
        con.commit()
        if news_id:
            return news_id[0]
        return news_id
    except psycopg2.DatabaseError, e:
        logging.debug('Error %s' % e)
    finally:
        if con:
            con.close()
