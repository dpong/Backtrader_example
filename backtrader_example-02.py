#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 20:26:35 2019

@author: dpong
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from datetime import datetime
import backtrader as bt
import backtrader.analyzers
import pyfolio as pf
import pandas as pd
import pandas_datareader as pdr
import support_resistance_bt as rs
import numpy as np

# Create a Stratey
class TestStrategy(bt.Strategy):
    
    params = (
            ('stake',10),
            ('feed_days',40),
    )
    
        #Logging function for this strategy
    def log(self, txt, dt=None, doprint=True):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        if doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        
        # Set the sizer stake from the params
        self.sizer.setsizing(self.params.stake)
       
        # To keep track of pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None
        #起始值
        self.resistance = 0
        self.support = 0
        self.early_res = 0
        self.early_sup = 0
        
        self.rns = rs.Sup_n_res()
        
        
    def notify_order(self, order):
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('Buy Executed Price: %.2f' % order.executed.price
                         +'  Size: %.0f' % order.executed.size +' ID: %.0f\n' % order.ref
                         +'-'*80)
            elif order.issell():
                self.log('Sell Executed Price: %.2f' % order.executed.price 
                         +'  Size: %.0f' % order.executed.size +' ID: %.0f\n' % order.ref
                         +'-'*80)

            self.bar_executed = len(self)

        #elif order.status in [order.Canceled]:
            #self.log('Order Canceled')
        elif order.status in [order.Margin, order.Rejected]:
            self.log('Order Margin/Rejected')

        # Write down: no pending order
        self.order = None
        
    def notify_trade(self, trade):
        if trade.isclosed:

            self.log('Operation Profit, Gross:$ %.2f' % trade.pnl
                     +', Net:$ %.2f\n' % trade.pnlcomm
                     +'-'*80)
        
    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close: %.2f' % self.dataclose[0]+'  Position Size: %.0f' % self.position.size)
        
        #部位控制
        if not self.position.size >= self.params.stake * 10 and not self.position.size <= -self.params.stake * 10:
            #判斷壓力支撐，需要有至少40天以上的資料
            if self.dataclose[-self.params.feed_days]:
                rev_high,rev_low = [],[]
                for i in range(self.params.feed_days):    #backtrader的排序方式要轉換一下順序
                    rev_high.append(self.datahigh[-i])
                    rev_low.append(self.datalow[-i])
                high,low = [],[]
                for price in reversed(rev_high):
                    high.append(price)        
                for price in reversed(rev_low):
                    low.append(price)        
                
                self.rns.high=np.array(high)
                self.rns.low=np.array(low)
                self.rns.identify() 
    
                if self.resistance == 0 and self.rns.last_res:             #0值後第一個有值就取代
                    self.resistance = self.rns.last_res
                if self.support == 0 and self.rns.last_sup:
                    self.support = self.rns.last_sup
                if self.rns.last_res and self.rns.last_res < self.resistance:   #更新
                    self.resistance = self.rns.last_res
                if self.rns.last_sup and self.rns.last_sup > self.support:
                    self.support = self.rns.last_sup
                
                if self.resistance > 0 and self.dataclose[0] > self.resistance:   #價格突破壓力
                    if self.resistance != self.early_res:
                        buy_limit = 1.2 * self.dataclose[0]
                        buy_stop = 0.9 * self.dataclose[0]
                        self.order = self.buy_bracket(stopprice=buy_stop,limitprice=buy_limit,exectype=bt.Order.Limit)
                        self.early_res = self.resistance
                        self.resistance = 0       #突破後壓力值重置                        
                if self.support > 0 and self.dataclose[0] < self.support: #跌破支撐
                    if self.support != self.early_sup:
                        sell_limit = 0.8 * self.dataclose[0]
                        sell_stop = 1.1 * self.dataclose[0]
                        self.order = self.sell_bracket(stopprice=sell_stop,limitprice=sell_limit,exectype=bt.Order.Limit)
                        self.early_sup = self.support
                        self.support = 0
                           
    def stop(self):
        #self.log('(MA Period %2d) Ending Value %.2f' %
        #         (self.params.maperiod, self.broker.getvalue()), doprint=True)
        pass

# Create a cerebro entity
cerebro = bt.Cerebro()

# Set our desired cash start
startcash = 1000000
cerebro.broker.setcash(startcash)

# Add a strategy
cerebro.addstrategy(TestStrategy)
#strats = cerebro.optstrategy(
#        TestStrategy,
#        maperiod=range(10, 31))

# Add the analyzers we are interested in
cerebro.addanalyzer(bt.analyzers.PyFolio)


# Create a Data Feed
df_data = pdr.DataReader('AAPL','yahoo', start='2010-1-1')
data0 = bt.feeds.PandasData(dataname=df_data,timeframe=1,openinterest=None)

# Add the Data Feed to Cerebro
cerebro.adddata(data0)

# Set commision
cerebro.broker.setcommission(commission=0.001)

# Print out the starting conditions
print('Starting Portfolio Value:$ %.2f' % cerebro.broker.getvalue())
print('-'*80)

# Run over everything
strategies = cerebro.run()
strat = strategies[0]
#Collect pyfolio's return
pyfoliozer = strat.analyzers.getbyname('pyfolio')
my_returns, my_positions, my_transactions, my_gross_lev = pyfoliozer.get_pf_items()

#Get final portfolio Value
portvalue = cerebro.broker.getvalue()
pnl = portvalue - startcash

# Print out the final result
print('-'*80)
print('Final Portfolio Value:$ %.2f' % portvalue)
print('Profit & Loss:$ %.2f' % pnl)

# print pyfolio results
#pf.create_full_tear_sheet(my_returns,positions=my_positions,transactions=my_transactions,)  
#plt.show()
# Plot




#figure = cerebro.plot()
#figure.savefig('example.png',dpi=300)