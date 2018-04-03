import sys
import time
import re
from bs4 import BeautifulSoup
from requests.utils import quote
import requests
import threading


def get_dois_from_journal_issn(issn, rows=500, pub_after=2002, pub_before=2018, query=None):
    ''''''
    dois = []
    if query == None:
        base_url = 'http://api.crossref.org/journals/' + issn + '/works?filter=from-pub-date:' + str(pub_after) + ',until-pub-date:' + str(pub_before)
    else:
        base_url = 'http://api.crossref.org/journals/' + issn + '/works?filter=from-pub-date:' + str(pub_after) + ',until-pub-date:' + str(pub_before) + '&query=' + query
    max_rows = 1000 #Defined by CrossRef API
    headers = {
      'Accept': 'application/json'
    }

    if rows <= max_rows: #No multi-query needed
        search_url = str(base_url) + '&rows=' + str(rows)
        response = requests.get(search_url, headers=headers, timeout=30).json()
        for item in response["message"]["items"]:
            dois.append(item["DOI"])

    else: #Need to split queries
        cursor = "*"
        keep_paging = True
        while (keep_paging):
            time.sleep(1)
            r = requests.get(base_url + "&rows=" + str(max_rows) + "&cursor=" + cursor,
                         headers=headers, timeout=30)
            cursor = quote(r.json()['message']['next-cursor'], safe='')
            if len(r.json()['message']['items']) == 0:
                keep_paging = False

            for item in r.json()['message']['items']:
                dois.append(item['DOI'])

    return list(set(dois))

def make_doi_file(issn, rows, pub_after, pub_before, query):
    '''A file containing all the dois of #issn# since #year# will be created.'''
    doilist = get_dois_from_journal_issn(issn=issn, rows=rows, pub_after=pub_after, pub_before=pub_before, query=query)
    doilist_n = [doi+'\n' for doi in doilist]
    doifile = open('doi_'+str(issn)+'.txt','a',encoding='utf-8')
    doifile.write('#issn# '+str(issn)+'\n')
    doifile.write('#year# '+str(pub_after)+'-'+str(pub_before)+'\n\n')
    doifile.writelines(doilist_n)
    doifile.close()
    return doilist

def get_metadata_from_doi(doi, mode='acs'):
    '''Get abstract'''
    if mode == 'acs':
        try:
            url = 'http://pubs.acs.org/doi/abs/' + doi
            headers = {'User-agent':'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout = 30)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "lxml")
                abstract = soup.find(class_='articleBody_abstractText')
                title = soup.find(class_='hlFld-Title')
                authors = soup.find('div', id='authors')
                affiliations = soup.find('div', class_='affiliations')
                citation = soup.find('div', id = 'citation')
                pubdate = soup.find('div', id = 'pubDate')
                artCopyright = soup.find('div', id = 'artCopyright')
                return [title.text, abstract.text, authors.text, affiliations.text.replace('\r\n', ' '), citation.text, pubdate.text, artCopyright.text]
        except:
            return None

def make_abstract_file(doi, issn, pub_after, pub_before, mode='acs'):
    '''A file containing doi, title, and abstract for each doi will be created.'''
    absfile = open('abs_'+str(issn)+'.txt','a',encoding='utf-8')
    metadata = get_metadata_from_doi(doi, mode='acs')
    if metadata == None:
        return False
    titletxt = metadata[0]
    abstxt = metadata[1]
    authors = metadata[2]
    affiliations = metadata[3]
    citation = metadata[4]
    pubdate = metadata[5]
    artCopyright = metadata[6]
    absfile.write('#doi# '+doi+'\n')
    absfile.write('#title# '+titletxt+'\n')
    absfile.write('#authors# '+authors+'\n')
    absfile.write('#affiliations# '+affiliations+'\n')
    absfile.write('#citation# '+citation+'\n')
    absfile.write('#pubdate# '+pubdate+'\n')
    absfile.write('#artCopyright# '+artCopyright+'\n')
    absfile.write('#abstract# '+abstxt+'\n\n')
    return True

def abs_downloader(issn, rows, pub_after, pub_before, mode='acs', query=None):
    '''
    Three files will be created.
    1. A file containing all the dois of #issn# since #year#.
    2. A file containing doi, title, and abstract for each doi.
    3. A file containing start time, end time, spent time, failed numbers, missing numbers, successed numbers.
    '''
    print('Here we go!')
    doilist = make_doi_file(issn=issn, rows=rows, pub_after=pub_after, pub_before=pub_before, query=query)
    
    listlen = len(doilist)
    fail = 0
    success = 0
    total = 0
    
    start_time = time.time()
    
    for i in range(listlen):
        
        doi = doilist[i]
        absfile = open('abs_'+str(issn)+'.txt','a',encoding='utf-8')

        result = make_abstract_file(doi, issn, pub_after, pub_before, mode='acs')
        
        if result == False:
            fail += 1
        else:
            success += 1

        
        total = fail+success
        
        if total/100 == 0:
            end_time = time.time()
            print('start_time = '+str(time.asctime(time.localtime(start_time)))+'\n'+'end_time = '+str(time.asctime(time.localtime(end_time)))+'\n'+'spent_time = '+str(end_time - start_time)+'s\n'+'fail='+str(fail)+'\n'+'success='+str(success)+'\n'+'total='+str(total))
            
    end_time = time.time()
    resultfile = open('res_'+str(issn)+'.txt','a',encoding='utf-8')
    resultfile.write('#issn# '+str(issn)+'\n')
    resultfile.write('#year# '+str(pub_after)+'-'+str(pub_before)+'\n\n')
    resultfile.write('start_time = '+str(time.asctime(time.localtime(start_time)))+'\n'+'end_time = '+str(time.asctime(time.localtime(end_time)))+'\n'+'spent_time = '+str(end_time - start_time)+'s\n'+'fail='+str(fail)+'\n'+'success='+str(success)+'\n'+'total='+str(total)+'\n\n')
    resultfile.close()
    print(str(issn)+' for '+str(pub_after)+' to '+str(pub_before)+' finished.')
    print('fail:%d ,success:%d, total:%d' %(fail, success, total))
    return print('Congratulations!')







