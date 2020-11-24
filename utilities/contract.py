# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 21:40:12 2020

@author: amits
"""

from dataclasses import dataclass


@dataclass
class Contract:
    """
    Dataclass(Base) used to store contract information. Extend, if necessary, to
    add more fields
    """
    contract_id: int
    cname: str
    fdate: str
    cik: str
    link: str
    inCIKsampl: str
    
    def __repr__(self):
        return '{}, {}, {}, {}, {}, {}'.format(self.contract_id, self.cname, self.fdate, self.cik, self.link, self.inCIKsampl)