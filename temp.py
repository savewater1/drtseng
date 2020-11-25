# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 20:14:15 2020

@author: amits
"""

# Note:
    # Optimizations: 
        # 1) LXML parser instead of BeautifulSoup
        # 2) Try different ways to multithread/multiprocessing other than grequests
        # 3) Logging to file bottleneck

from bs4 import BeautifulSoup
import grequests
import pandas as pd
import re
import requests
import sys
from time import sleep
from utilities.contract import Contract
import warnings
warnings.filterwarnings('ignore')


def verifyContract(clink, titleWL, negWL, posWL):
    """
    Accepts a link to html document
    """
    res = requests.get(clink)
    html_page = res.text
    soup = BeautifulSoup(html_page)
    
    text = soup.body.get_text()
    return True
    pass


def checkFilings(*factory_args, **factory_kwargs):
    def response_hook(response, *request_args, **request_kwargs):
        contract_id = 0
        html_page = response.text
        soup = BeautifulSoup(html_page)
        content_div = soup.body.find(id = 'contentDiv')
        content = list(content_div.find('table', {'class': 'tableFile'}).children)
        if len(content) > 2:
            for exhibit in content[3::2]:
                data = exhibit.find_all('td', recursive = False)
                if re.search(factory_kwargs['pattern'], data[3].get_text()):
                    clink = factory_kwargs['base_url']+data[2].a['href']
                    is_material_supply_contract = verifyContract(clink)
                    if is_material_supply_contract:
                        contract_id += 1
                        contract = Contract(contract_id=contract_id, cname=factory_kwargs['cname'], fdate=factory_kwargs['fdate'], cik=factory_kwargs['cik'], link=factory_kwargs['clink'])
                        # list.append is thread safe operation taken care by GIL
                        global material_supply_contracts
                        material_supply_contracts.append(repr(contract))
    return response_hook



if __name__ == '__main__':
    ## Create loggers
    ############################### GLOBAL VARIABLES ###########################
    base_url = 'https://www.sec.gov'
    filings_of_interest = set(('8-K', '10-K', '10-Q'))
    material_supply_contracts = []
    search_url = 'https://www.sec.gov/cgi-bin/browse-edgar'
    search_pattern = 'EX-10.\d+'
    url_comps = {'action': 'getcompany', 'dateb': '20180101', 'datea': '20170101', 'owner': 'exclude', 'count': '100'}
    #############################################################################
    
    # File loading
    try:
        assert len(sys.argv) == 3, "Wrong number of inputs!" 
        infile, outfile = sys.argv[1:]
        df = pd.read_excel(infile, sheet_name = 'sample')
    except AssertionError as e:
        pass
    except FileNotFoundError as e:
        pass
    except pd.errors.ParserError as e:
        pass
    except Exception as e:
        pass
    
    # Scraping
    try:
        for _, row in df.iterrows():
            company = []
            start = 0
            while True:
                payload = {**url_comps, **{'CIK': row[2], 'start': start}}
                response = requests.get(search_url, params = payload)
                html_page = response.text
                # Stopping the process to wait for page to finish loading everything
                sleep(1)
                soup = BeautifulSoup(html_page)
                content_div = soup.body.find(id = 'seriesDiv')
                content = list(content_div.find('table', {'class': 'tableFile2'}).children)
                if len(content) < 3:
                    break
                for filing in content[3::2]:
                    data = filing.find_all('td', recursive = False)
                    fdate = data[-2].get_text()
                    ftype = data[0].get_text()
                    flink = base_url+data[1].a['href']
                    if ftype in filings_of_interest: 
                        action_item = grequests.get(flink, callback = checkFilings(ftype=ftype, fdate=fdate, base_url=base_url, search_pattern=search_pattern, cik=row[2], cname=row[0]))
                        company.append(action_item)
                # End of for
                start += 100
            # End of while
            # for each filing look for exhibit 10 and then check the document using given conditions
            # out = checkFilings(base_url, company, search_pattern, row[2], row[0])
            results = grequests.map(company, size = 5)
            # with open(outfile, 'a', newline = '\n') as csvfile:
                # csvfile.write(out)
                # pass
            # Code to record company's CIK for which the contract has been obtained and verified
            # to keep track of all the companies that are done
    # except:
    #     pass
    