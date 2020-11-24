# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 20:14:15 2020

@author: amits
"""

from bs4 import BeautifulSoup
from contract import Contract
from datetime import datetime
from driver.chromedriver import get_chrome_driver
import pandas as pd
import pickle
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import sys
from time import sleep
from utilities.page import get_page
import warnings
warnings.filterwarnings('ignore')


def verifyContract():
    pass

def findContract():
    pass

def checkFilings():
    pass

## Flow: For each company look for 10k, 10q and 8k in the main search page. For each filing check for 10

if __name__ == '__main__':
    ## Create loggers
    start_date = datetime.fromisoformat('2017-01-01')
    base_url = 'https://www.sec.gov'
    search_url = 'https://www.sec.gov/cgi-bin/browse-edgar'
    url_comps = {'action': 'getcompany', 'dateb': '20180101', 'owner': 'exclude', 'count': '100'}
    try:
        assert len(sys.argv) == 3, "Wrong number of inputs!" 
        infile, outfile = sys.argv[1:]
        df = pd.read_excel(infile, sheet_name = 'sample')
        wd = get_chrome_driver()
    except AssertionError as e:
        pass
    ## Create custom exception for webdriver error
    try:
        for row in df.iterrows():
            company = []
            flag = 0
            start = 0
            url = search_url + '?' + '&'.join('{}={}' for k, v in {**url_comps, **{'CIK': row[1], 'start': start}})
            while True:
                if wd.get_page(wd, url):
                     # Stopping the process to wait for page to finish loading everything
                    sleep(1)
                    html_page = wd.page_source
                    soup = BeautifulSoup(html_page)
                    content_div = soup.body.find(id = 'seriesDiv')
                    content = list(content_div.table.tbody.children)
                    if len(content) < 3:
                        break
                    for filings in content[2::2]:
                        data = filings.find_all('td', recursive = False)
                        fdate = datetime.fromisoformat(data[-2].text)
                        if fdate < start_date:
                            flag = 1
                            break
                        ftype = data[0].text
                        flink = base_url+data[1].a['href']
                        company.append((ftype, flink, fdate))
                    if not flag:
                        start += 100
                        url = search_url + '?' + '&'.join('{}={}' for k, v in {**url_comps, **{'CIK': row[1], 'start': start}})
                # End of if
            # End of while
            # for each filing look for exhibit 10 and then check the document using given conditions
    
    except:
        pass
    