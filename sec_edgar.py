#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 28 10:00:02 2020

@author: amits
"""

from bs4 import BeautifulSoup
import datetime
import grequests
import logging
import pandas as pd
from pathlib import Path
import os
import re
import requests
import sys
from utilities.contract import Contract
import warnings
warnings.filterwarnings('ignore')



def checkContract(clink, cik, flink):
    """
    Helper function for function checkFilings.
    
    Given a list of keywords in the global variable keywords, this function
    returns False if any of these keywords are present in the first 500 
    words of the contract at url clink.
    
    Parameters
    ----------
    clink : str
        URL of a contract of interest.
    cik : str
        Unique identifier for a company.
    flink : str
        URL for a filing made by the compnay with SEC.

    Returns
    -------
    tuple(bool, None)
        returns whether a contract passes the negative keyword
        test for keywords specified in the resources folder.
        The output is a tuple to maintain compatibility with
        function getWordCountContract

    """
    try:
        global keywords
        res = requests.get(clink)
        html_page = res.text
        soup = BeautifulSoup(html_page)
        # title = soup.find('title')
        # title_text = title.text if title else 'No Title'
        raw_text = soup.body.get_text(strip = True)
        word_list = text_pattern.findall(raw_text, 0, 4500)
        word_list = word_list[:550]
        str_ = ' '.join(word_list)
        if keywords.search(str_):
            return (False, None)
        else:
            return (True, None)
    except Exception as e:
        company_logger = logging.getLogger('company_failure')
        company_logger.debug('---'.join(['CONTRACT ERROR', cik, flink, clink]))
        company_logger.exception(e)
        return (False, None)


def getWordCountContract(clink, cik, flink):
    """
    Helper function for function checkFilings.
    
    Given a list of keywords in the global variable keywords, this function
    returns the count of each of these keywords in the first 500 words of the
    contract at url clink.
    
    Parameters
    ----------
    clink: str
        URL of a contract of interest.
    cik: str
        Unique identifier for a company.
    flink: str
        URL for a filing made by the compnay with SEC.
    """
    try:
        global keywords
        res = requests.get(clink)
        html_page = res.text
        soup = BeautifulSoup(html_page)
        # title = soup.find('title')
        # title_text = title.text if title else 'No Title'
        raw_text = soup.body.get_text(strip = True)
        word_list = text_pattern.findall(raw_text, 0, 4500)
        word_list = map(str.lower, word_list[:550])
        str_ = ' '.join(word_list)
        count = ','.join([str(sum(1 for m in kw.finditer(str_))) for kw in keywords])
        return (True, count)
    except Exception as e:
        company_logger = logging.getLogger('company_failure')
        company_logger.debug('---'.join(['CONTRACT ERROR', cik, flink, clink]))
        company_logger.exception(e)
        return (False, None)


def checkFilings(*factory_args, **factory_kwargs):
    """
    Decorator function to enable passing of extra arguments to response_hook
    function which is the event hook associated with requests sent by 
    grequests for each filing of interest for a company.
    
    Parameters
    ----------
    *factory_args : list
        Arguments passed to the function.
    **factory_kwargs : dict
        Keyword Arguments passed to the function.

    Returns
    -------
    response_hook : function
        The function containing post-processing logic to execute after a 
        filing page is fetched for a company by grequest.

    """
    def response_hook(response, *request_args, **request_kwargs):
        global contract_search_pattern
        global base_url
        global material_supply_contracts
        global get_counts
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
                    if get_counts:
                        contract_return = getWordCountContract(clink, cik=factory_kwargs['cik'], flink=response.url)
                    else:
                        contract_return = checkContract(clink, cik=factory_kwargs['cik'], flink=response.url)
                    if contract_return[0]:
                        contract_id += 1
                        contract = Contract(contract_id=contract_id, cname=factory_kwargs['cname'], fdate=factory_kwargs['fdate'], cik=factory_kwargs['cik'], link=clink, ftype=factory_kwargs['ftype'], counts=contract_return[1])
                        # list.append is thread safe operation taken care by GIL
                        material_supply_contracts.append(repr(contract)+'\n')
    return response_hook


def exception_handler(*args, **kwargs):
    """

    Parameters
    ----------
    *args : list
        Arguments passed to function.
    **kwargs : dict
        Keyword arguments passed to function.

    Returns
    -------
    handle : function
        Exception Handling logic for response event hook associated with 
        requests sent by grequests for each filing of interest for a company.

    """
    def handle(request, exception):
        company_logger = logging.getLogger('company_failure')
        company_logger.debug('---'.join(['FILING ERROR', kwargs['cik'], flink, 'NONE']))
        company_logger.exception(exception)
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
    company_failure_logger.setLevel(logging.DEBUG)
    ## File Handler to record failures
    failure_file_handler = logging.FileHandler(FAILED)
    failure_file_handler.setLevel(logging.DEBUG)
    company_failure_logger.addHandler(failure_file_handler)
    ##########################################################################
    
    ############################## GLOBAL VARIABLES ##########################
    base_url = 'https://www.sec.gov'
    contract_search_pattern = re.compile(r'EX-10.\d+', re.I)
    filing_search_pattern = re.compile(r'8-K.*|10-K.*|10-Q.*', re.I)
    keywords_file = 'resources/keywords.txt'
    material_supply_contracts = []
    search_url = 'https://www.sec.gov/cgi-bin/browse-edgar'
    text_pattern = re.compile(r'\w+')
    ##########################################################################
    
    # File loading
    try:
        assert len(sys.argv) == 6, "Wrong number of inputs!" 
        infile, outfile, start_date, end_date = sys.argv[1:5]
        get_counts = True if sys.argv[5] in ('y', 'Y') else False
        df = pd.read_csv(infile, dtype = str, nrows = 20)
        # df = pd.DataFrame({'cname': ['AVY'], 'tick': ['AVY'], 'CIK': ['789019']})
    except AssertionError as e:
        module_logger.critical(e)
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
        # Create regular expressions to extract key phrases of interest
        # from contracts
        with open(keywords_file, mode = 'r') as file:
            keywords = file.read().split('\n')
        if get_counts:
            output_header = ['contract_id', 'cname', 'cik', 'ftype', 'fdate', 'link']+keywords
            keywords = [re.compile('\\b'+kw+'\\b', re.I) for kw in keywords]
        else:
            keywords = re.compile('|'.join(['\\b'+kw+'\\b' for kw in keywords]), re.I)
            output_header = ['contract_id', 'cname', 'cik', 'ftype', 'fdate', 'link']
        
        # Creating the output directory
        outpath = Path(outfile)
        os.makedirs(outpath.parent, exist_ok = True)
        
        # Creating the output file
        with open(outfile, mode='w') as csvfile:
            csvfile.write(','.join(output_header)+'\n')
        
        # Payload to be sent with each request to SEC edgar when searching 
        # for filings made by a company
        url_comps = {'action': 'getcompany', 'dateb': '20210101', \
                 'datea': '20151231', 'owner': 'exclude', 'count': '100'}
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
                    if filing_search_pattern.search(ftype): 
                        action_item = grequests.get(flink, callback = checkFilings(ftype=ftype, fdate=fdate, cik=row[2], cname=row[0]))
                        company.append(action_item)
                # End of for
                start += 100
            # End of while
            results = grequests.map(company, size = 5, exception_handler = exception_handler(cik = row[2]))
            with open(outfile, mode = 'a') as csvfile:
                csvfile.writelines(material_supply_contracts)
            material_supply_contracts = []
            company_logger.info(row[2])
    except Exception as e:
        module_logger.critical('Error!')
        module_logger.exception(e)
    finally:
        logging.shutdown()
