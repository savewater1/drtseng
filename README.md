# drtseng
### Web-Scrapping SEC EDGAR
#### Directory Structure
* driver: Contains chromedriver (windows) to use Selenium for scraping -- not needed and will be removed in future verison
* resources: Contains data files used by scraper
* utilites: Functions and classes used by scrapper

#### Pre-requisites
* Python 3.6+
* Install necessary packages using pip install -r requirements.txt

#### How to Run
Run the script sec_edgar.py with following command line arguments, in that order:
1. Name of the input file that contains data about companies for which contracts are being scraper. Format (cname, tick, cik)
2. Name of the output file (must be .csv) where scraped data will be stored (Eg: output/results.csv)
3. Start date for scraping in format yyyymmdd (start date is not included)
4. End date for scraping in format yyyymmdd (end date is not included)
5. return_counts \in ['y', 'n']. Indicates whether to store count of keywords for each contract in the output
