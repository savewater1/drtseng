# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 20:11:21 2020

@author: amits
"""

def get_page(wd, url, max_attempts = 3):
    """
    Attempts a connecttion to url specified for number of attempts specified.
    If the connection is successful, returns True otherwise, returns False.
    ref: https://testdriven.io/blog/building-a-concurrent-web-scraper-with-python-and-selenium/
    """
    
    attempts = 0
    while attempts < max_attempts:
        try:
            wd.get(url)
            return True
        except:
            attempts += 1
            print('Connection Failed!!')
            print('Attempting to reconnect..'+url)
            print('Attempt #{0}'.format(attempts))
    print("Can't connect to "+url)
    return False