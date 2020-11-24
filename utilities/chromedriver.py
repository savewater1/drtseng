# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 20:03:20 2020

@author: amits
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_chrome_driver():
    """
    Gets the chrome driver to be used for for testing environment.
    Modify/Add options/configurations as required
    """
    chromedriver_path = '../driver/chromedriver'
    options = Options()
    # Use this option to specify path to chrome binary if it's not on system path
    # options.binary_location = "/path/to/chrome/binary"
    # options.headless = True
    prefs = {'profile.managed_default_content_settings.images':2}
    options.add_experimental_option('prefs', prefs)
    wd = webdriver.Chrome(chromedriver_path, options = options)
    return wd