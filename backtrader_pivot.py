#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 20:26:35 2019

@author: dpong
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from datetime import datetime
from data import *
import backtrader as bt
import backtrader.analyzers
import pandas as pd
import pandas_datareader as pdr
import support_resistance_bt as rs
import numpy as np
import sys, warnings


if not sys.warnoptions:
    warnings.simplefilter("ignore")


# Create a Stratey
class MyStrategy(bt.Strategy):
    params = (
            ('stake',10),)

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
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=21)
        
        
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
        if not self.position:
            if self.rsi < 30:
                self.buy()
        else:
            if self.rsi > 70:
                self.sell()
        
                           
    def stop(self):
        #self.log('(MA Period %2d) Ending Value %.2f' %
        #         (self.params.maperiod, self.broker.getvalue()), doprint=True)
        pass




if __name__=='__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Set our desired cash start
    startcash = 1000000
    cerebro.broker.setcash(startcash)

    # Add a strategy
    cerebro.addstrategy(MyStrategy)
    # strats = cerebro.optstrategy(
    #        TestStrategy,
    #        maperiod=range(10, 31))

    # Add the analyzers we are interested in


    # Create a Data Feed
    frequency = 'day'  # day, minute, hour
    ticker = 'BTC'
    data_quantity = 1000  # max limit
    df = get_crypto_from_api(ticker, data_quantity, frequency)
    data0 = bt.feeds.PandasData(dataname=df, timeframe=1, openinterest=None)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data0)

    # Set commision
    cerebro.broker.setcommission(commission=0.001)

    # Print out the starting conditions
    print('Starting Portfolio Value:$ %.2f' % cerebro.broker.getvalue())
    print('-'*80)

    # Add the analyzers we are interested in
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='mydrawdown')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='mysqn')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='mytradeanaly')

    # Run over everything
    strategies = cerebro.run()
    strat = strategies[0]

    #Get final portfolio Value
    portvalue = cerebro.broker.getvalue()
    pnl = portvalue - startcash

    # Print out the final result
    print('-'*80)
    print('Final Portfolio Value:$ %.2f' % portvalue)
    print('Profit & Loss:$ %.2f' % pnl)
    # Handling perfomance data
    x = list(strat.analyzers.mysharpe.get_analysis().items())
    print('Sharpe Ratio: %.2f' % x[0][-1])
    x = list(strat.analyzers.mydrawdown.get_analysis().items())
    maxd = list(x[3][1].items())
    print('MaxDrawDown: %.1f%%' % maxd[1][1], ' MaxDrawDown Lenght:', maxd[0][1])
    x = list(strat.analyzers.mysqn.get_analysis().items())
    print('SystemQualityNumber: %.2f' % x[0][-1])
    x = list(strat.analyzers.mytradeanaly.get_analysis().items())
    total = list(x[0][1].items())
    print('Total Traded:', total[0][1], ' Open:', total[1][1], ' Close:', total[2][1])
    win = list(x[3][1].items())
    lose = list(x[4][1].items())
    longs = list(x[5][1].items())
    shorts = list(x[6][1].items())
    winrate = 100 * win[0][1] / (win[0][1] + lose[0][1])
    print('Long:', longs[0][1], ' Short:', shorts[0][1])
    print('Win:', win[0][1], ' Lose:', lose[0][1], ' WinRate: %.1f%%' % winrate)
    win = list(win[1][1].items())
    lose = list(lose[1][1].items())
    print('Max Win: %.2f' % win[2][1], ' Avg Win: %.2f' % win[1][1])
    print('Max Lose: %.2f' % lose[2][1], ' Avg Lose: %.2f' % win[1][1])
    
    # Plot
    cerebro.plot(style='candlestick')
