#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 22:50:26 2019

@author: dpong
"""

import numpy as np

class Sup_n_res():
    def __init__(self):
        self.high = None
        self.low = None
        
    def identify(self,n=20,min_touches=2, stat_likeness_percent=2,bounce_percent=5):
    # Collapse into dataframe
        sup_list = np.full([len(self.low)],np.nan)
        res_list = np.full([len(self.low)],np.nan)
        
        for x in range((n-1)+n, len(sup_list)):
        # Split into defined timeframes for analysis
            temphigh = self.high[x-n:x+1]
            templow = self.low[x-n:x+1]
        # Setting default values for support and resistance to None
            sup ,res = None, None
        # Identifying local high and local low
            maxima = np.max(temphigh)       
            minima = np.min(templow)
        # Calculating distance between max and min (total price movement)
            move_range = maxima - minima
        # Calculating bounce distance and allowable margin of error for likeness
            move_allowance = move_range * (stat_likeness_percent / 100)
            bounce_distance = move_range * (bounce_percent / 100)
        # Test resistance by iterating through data to check for touches delimited by bounces
            touchdown = 0
            awaiting_bounce = False
            for y in range(0, len(temphigh)):
                if abs(maxima - temphigh[y]) < move_allowance and not awaiting_bounce:
                    touchdown = touchdown + 1
                    awaiting_bounce = True
                elif abs(maxima - temphigh[y]) > bounce_distance:
                    awaiting_bounce = False
            if touchdown >= min_touches:
                res = maxima
                touchdown = 0
                awaiting_bounce = False
            for y in range(0, len(templow)):
                if abs(templow[y] - minima) < move_allowance and not awaiting_bounce:
                    touchdown = touchdown + 1
                    awaiting_bounce = True
                elif abs(templow[y] - minima) > bounce_distance:
                    awaiting_bounce = False
            if touchdown >= min_touches:
                sup = minima
            if sup:
                sup_list[x]=sup   #一排是sup,另一排是res
            if res:
                res_list[x]=res   

        self.res_list = res_list[~np.isnan(res_list)]
        self.sup_list = sup_list[~np.isnan(sup_list)]
        
        if self.res_list.size > 0:
            if self.res_list.size == 1:
                self.last_res = self.res_list[0]
            else:
                self.last_res = self.res_list[-1]
        else:
            self.last_res = None
        if self.sup_list.size > 0:
            if self.sup_list.size == 1:
                self.last_sup = self.sup_list[0]
            else:
                self.last_sup = self.sup_list[-1]
        else:
            self.last_sup = None
        











