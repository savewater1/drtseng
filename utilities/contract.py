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
    ftype: str
    cik: str
    link: str
    counts: str=None
    
    def __repr__(self):
        if self.counts:
            str_ = '{},{},{},{},{},{},{}'.format(self.contract_id, self.cname, self.cik, self.ftype, self.fdate, self.link, self.counts)
        else:
            str_ = '{},{},{},{},{},{}'.format(self.contract_id, self.cname, self.cik, self.ftype, self.fdate, self.link)
        return str_