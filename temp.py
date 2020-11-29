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
import datetime
import grequests
import logging
import pandas as pd
import os
import re
import requests
import sys
from utilities.contract import Contract
import warnings
warnings.filterwarnings('ignore')


# Store the keyword list and count in folder cik/file fdate-ftype-contract_id.csv

def verifyContract(clink, cik, flink):
    """
    Accepts a link to html document
    """
    try:
        global title_search_pattern
        global text_pattern
        global pos_search_pattern
        global neg_search_pattern
        res = requests.get(clink)
        html_page = res.text
        soup = BeautifulSoup(html_page)
        title_text = soup.find('title').text
        if title_search_pattern.search(title_text):
            return True
        raw_text = soup.body.get_text()
        word_list = text_pattern.findall(raw_text, 0, 4500)
        text = ' '.join(word_list)
        if neg_search_pattern.search(text):
            return False
        elif pos_search_pattern.search(text):
            return True
        return False
    except Exception as e:
        company_logger = logging.getLogger('company_failure')
        company_logger.debug('---'.join(['CONTRACT ERROR', cik, flink, clink]))
        return False
        pass


def checkFilings(*factory_args, **factory_kwargs):
    def response_hook(response, *request_args, **request_kwargs):
        global contract_search_pattern
        global base_url
        contract_id = 0
        html_page = response.text
        soup = BeautifulSoup(html_page)
        content_div = soup.body.find(id = 'contentDiv')
        content = list(content_div.find('table', {'class': 'tableFile'}).children)
        if len(content) > 3:
            for exhibit in content[3::2]:
                data = exhibit.find_all('td', recursive = False)
                if contract_search_pattern.search(data[3].get_text()):
                    clink = base_url+data[2].a['href']
                    is_material_supply_contract = verifyContract(clink, factory_kwargs['cik'], response.url)
                    if is_material_supply_contract:
                        contract_id += 1
                        contract = Contract(contract_id=contract_id, cname=factory_kwargs['cname'], fdate=factory_kwargs['fdate'], cik=factory_kwargs['cik'], link=factory_kwargs['clink'])
                        # list.append is thread safe operation taken care by GIL
                        global material_supply_contracts
                        material_supply_contracts.append(repr(contract))
    return response_hook


def exception_handler(*args, **kwargs):
    def handle(request, exception):
        company_logger = logging.getLogger('company_failure')
        company_logger.debug('---'.join(['FILING ERROR', kwargs['cik'], flink, 'NONE']))
    return handle


if __name__ == '__main__':
    ############################### Logging ##################################
    # Creating log directory
    current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    LOG_DIR = os.path.join(os.path.dirname("logs/" + current_time + "/"))
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_FILE = os.path.join(LOG_DIR, 'secEdgarScrape.log')
    PROCESSED = os.path.join(LOG_DIR, 'processed.log')
    FAILED = os.path.join(LOG_DIR, 'fail.log')
    # Module Level logger
    module_logger = logging.getLogger(__name__)
    module_logger.setLevel(logging.DEBUG)
    ## Formatter for stream handler
    stream_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    ## Stream Handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.CRITICAL)
    stream_handler.setFormatter(stream_formatter)
    module_logger.addHandler(stream_handler)
    ## Formatter for file handler
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
    ## File Handler for logging
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    module_logger.addHandler(file_handler)
    ## Logger to record comapnys processed by scraper
    company_logger = logging.getLogger('company')
    company_logger.setLevel(logging.INFO)
    ## Formatter for file handler
    company_formatter = logging.Formatter('%(message)s')
    ## File Handler to record companys processed by scrapper
    processed_file_handler = logging.FileHandler(PROCESSED)
    processed_file_handler.setLevel(logging.INFO)
    company_logger.addHandler(processed_file_handler)
    ## Logger to record failures
    company_failure_logger = logging.getLogger('company_failure')
    company_failure_logger.setLevel(logging.INFO)
    ## File Handler to record failures
    failure_file_handler = logging.FileHandler(FAILED)
    failure_file_handler.setLevel(logging.INFO)
    company_failure_logger.addHandler(failure_file_handler)
    ##########################################################################
    
    ############################## GLOBAL VARIABLES ##########################
    base_url = 'https://www.sec.gov'
    contract_search_pattern = re.compile('EX-10.\d+', re.I)
    filings_of_interest = set(('8-K', '10-K', '10-Q'))
    material_supply_contracts = []
    search_url = 'https://www.sec.gov/cgi-bin/browse-edgar'
    text_pattern = re.compile('\w+', re.I)
    url_comps = {'action': 'getcompany', 'dateb': '20180101', \
                 'datea': '20170101', 'owner': 'exclude', 'count': '100'}
    ##########################################################################
    
    # File loading
    try:
        assert len(sys.argv) == 3, "Wrong number of inputs!" 
        infile, outfile = sys.argv[1:]
        df = pd.read_csv(infile, dtype = str)
    except AssertionError as e:
        module_logger.critical(e.msg)
        logging.shutdown()
        sys.exit()
    except FileNotFoundError:
        module_logger.critical('Could not find the input file!')
        logging.shutdown()
        sys.exit()
    except pd.errors.ParserError as e:
        module_logger.critical('Error while parsing input file. See the log for more info..')
        module_logger.exception(e)
        logging.shutdown()
        sys.exit()
    except Exception as e:
        module_logger.critical('Error!')
        module_logger.exception(e)
        logging.shutdown()
        sys.exit()
    
    # Scraping
    try:
        with open('resource/title_indicators.txt', mode = 'r') as file:
            title_wl = file.read().split()
        with open('resource/neg_indicators.txt', mode = 'r') as file:
            neg_wl = file.read().splitlines()
        with open('resource/pos_indicators_pre.txt', mode = 'r') as file:
            pos_pre = file.read().splitlines()
        with open('resource/pos_indicators_su.txt', mode = 'r') as file:
            pos_su = file.read().splitlines()
        title_pattern = '|'.join(title_wl)
        title_search_pattern = re.compile(title_pattern, re.I)
        neg_pattern = '|'.join(neg_wl)
        neg_search_pattern = re.compile(neg_pattern, re.I)
        pos_pattern = '(' + '|'.join(pos_pre) + ')' + ' ' + '(' + '|'.join(pos_su) + ')'
        pos_search_pattern = re.compile(pos_pattern, re.I)
        # df = pd.DataFrame({'cname': ['FORD MOTOR CO'], 'TIK': ['F'], 'CIK': ['1000045']})
        for _, row in df.iterrows():
            company = []
            start = 0
            while True:
                payload = {**url_comps, **{'CIK': row[2], 'start': start}}
                response = requests.get(search_url, params = payload)
                html_page = response.text
                soup = BeautifulSoup(html_page)
                content_div = soup.body.find(id = 'seriesDiv')
                if not content_div:
                    break
                content = list(content_div.find('table', {'class': 'tableFile2'}).children)
                if len(content) <= 3:
                    break
                for filing in content[3::2]:
                    data = filing.find_all('td', recursive = False)
                    fdate = data[-2].get_text()
                    ftype = data[0].get_text()
                    flink = base_url+data[1].a['href']
                    if ftype in filings_of_interest: 
                        action_item = grequests.get(flink, callback = checkFilings(ftype=ftype, fdate=fdate, cik=row[2], cname=row[0]))
                        company.append(action_item)
                # End of for
                start += 100
            # End of while
            results = grequests.map(company, size = 3, exception_handler = exception_handler(cik = row[2]))
            with open(outfile, mode = 'a', newline = '\n') as csvfile:
                csvfile.writelines(material_supply_contracts)
            material_supply_contracts = []
            company_logger.info(row[2])
    except FileNotFoundError as e:
        print(e.filename)
        module_logger.critical('Could not find the file: ', e.filename)
    except Exception as e:
        module_logger.critical('Error!')
        module_logger.exception(e)
    finally:
        logging.shutdown()
