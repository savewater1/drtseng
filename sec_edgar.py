# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 20:14:15 2020

@author: amits
"""

from bs4 import BeautifulSoup
from datetime import datetime
import grequests
import pandas as pd
import pickle
import re
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import sys
from time import sleep
from utilities.chromedriver import get_chrome_driver
from utilities.contract import Contract
from utilities.page import get_page
import warnings
warnings.filterwarnings('ignore')


def verifyContract():
    
    pass


def checkFilings(wd, base_url, company, pattern, cik, cname):
    contract_id = 0
    material_supply_contracts = []
    for ftype, flink, fdate in company:
        if get_page(wd, flink):
            sleep(1)
            html_page = wd.page_source
            soup = BeautifulSoup(html_page)
            content_div = soup.body.find(id = 'contentDiv')
            content = list(content_div.find('table', {'class': 'tableFile'}).tbody.children)
            if len(content) < 3:
                break
            for exhibit in content[2::2]:
                data = exhibit.find_all('td', recursive = False)
                if re.search(pattern, data[3].get_text()):
                    clink = base_url+data[2].a['href']
                    is_material_supply_contract = verifyContract(wd, clink)
                    if is_material_supply_contract:
                        contract_id += 1
                        contract = Contract(contract_id=contract_id, cname=cname, fdate=fdate, cik=cik, link=clink, inCIKsampl=cname)
                        material_supply_contracts.append(repr(contract))
    return material_supply_contracts

## Flow: For each company look for 10k, 10q and 8k in the main search page. For each filing check for 10

if __name__ == '__main__':
    ## Create loggers
    base_url = 'https://www.sec.gov'
    chromedriver_path = 'driver/chromedriver'
    filings_of_interest = set(('8-K', '10-K', '10-Q'))
    search_url = 'https://www.sec.gov/cgi-bin/browse-edgar'
    search_pattern = 'EX-10.\d+'
    start_date = datetime.fromisoformat('2017-01-01')
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
            while True:
                url = search_url + '?' + '&'.join('{}={}'.format(k, v) for k, v in {**url_comps, **{'CIK': row[2], 'start': start}}.items())
                if get_page(wd, url):
                     # Stopping the process to wait for page to finish loading everything
                    sleep(1)
                    html_page = wd.page_source
                    soup = BeautifulSoup(html_page)
                    content_div = soup.body.find(id = 'seriesDiv')
                    content = list(content_div.find('table', {'class': 'tableFile2'}).tbody.children)
                    if len(content) < 3:
                        break
                    for filing in content[2::2]:
                        data = filing.find_all('td', recursive = False)
                        fdate = datetime.fromisoformat(data[-2].get_text())
                        if fdate < start_date:
                            flag = 1
                            break
                        ftype = data[0].text
                        flink = base_url+data[1].a['href']
                        if ftype in filings_of_interest: 
                            company.append((ftype, flink, fdate))
                    if flag:
                        break
                    start += 100
                # End of if
            # End of while
            # for each filing look for exhibit 10 and then check the document using given conditions
            out = checkFilings(wd, base_url, company, search_pattern, row[2], row[0])
            with open(outfile, 'a', newline = '\n') as csvfile:
                csvfile.write(out)
            # Code to record company's CIK for which the contract has been obtained and verified
            # to keep track of all the companies that are done
    except:
        pass
    