# -*- coding: utf-8 -*-
"""
Created on Mon Nov 30 17:23:39 2020

@author: amits
"""

import os
import pandas as pd

if __name__ == '__main__':
    path = 'output'
    outfname = 'contract_word_list.csv'
    outfile = os.path.join(path, outfname)
    subdir = [f.name for f in os.scandir(path) if f.is_dir()]
    contract_file = 'contract.csv'
    df = pd.read_csv(os.path.join(path, contract_file), dtype = str)
    df = df.applymap(str.strip)
    li = []
    for cik in subdir:
        base = os.path.join(path, cik)
        files = os.listdir(base)
        for f in files:
            fdate, ftype, contract_id = f.split('__')
            contract_id = contract_id.replace('.csv', '')
            fpath = os.path.join(base, f)
            se = pd.read_csv(fpath, index_col = 0, squeeze = True)
            se['title'] = se.name
            se['cik'] = cik
            se['contract_id'] = contract_id
            se['ftype'] = ftype
            se['fdate'] = fdate
            li.append(se)
    word_list_df = pd.concat(li, axis = 1)
    word_list_df = word_list_df.T
    word_list_df.reset_index(drop = True, inplace = True) 
    merged_df = word_list_df.merge(df, how = 'inner', on = ['cik', 'ftype', 'fdate', 'contract_id'])
    merged_df.to_csv(outfile)