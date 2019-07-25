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
#import matplotlib.pyplot as plt


# Create a Stratey
class TestStrategy(bt.Strategy):
    
    params = (
        ('exitbars', 5),
        ('maperiod',20),
        ('stake',10),
        ('printlog',False),
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
        
        # Set the sizer stake from the params
        self.sizer.setsizing(self.params.stake)
        
        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)
        
        # To keep track of pending orders
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        
    def notify_order(self, order):
        #if order.status in [order.Submitted, order.Accepted]:
        # Buy/Sell order submitted/accepted to/by broker - Nothing to do
        #    return
        
        
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

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        #if self.order:
        #    return

        # Check if we are in the market
        if not self.position.size >= 100 and not self.position.size <= -100:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0]:

                # BUY, BUY, BUY!!! (with default parameters)
                self.log('Buy Create: %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                buy_limit = 1.2 * self.dataclose[0]
                buy_stop = 0.9 * self.dataclose[0]
                self.order = self.buy_bracket(stopprice=buy_stop,limitprice=buy_limit,
                                              exectype=bt.Order.Limit)
                #self.order = self.buy_bracket(price=self.dataclose[0],stopprice=stop_price)

        #else:
            # Already in the market ... we might sell
            if self.dataclose[0] < self.sma[0]:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('Sell Create: %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                sell_stop = 1.1 * self.dataclose[0]
                sell_limit = 0.8 * self.dataclose[0]
                self.order = self.sell_bracket(stopprice=sell_stop,limitprice=sell_limit,
                                               exectype=bt.Order.Limit)

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
data0 = bt.feeds.YahooFinanceData(dataname='AAPL', fromdate=datetime(2018, 1, 1),
                                  todate=datetime(2018, 12, 31))
# Add the Data Feed to Cerebro
cerebro.adddata(data0)

# Set commision
cerebro.broker.setcommission(commission=0.001)

# Add a FixedSize sizer according to the stake
#cerebro.addsizer(bt.sizers.FixedSize, stake=10)   #改寫在init裡

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