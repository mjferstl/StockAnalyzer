
# standard modules
import sys, os
from pandas_datareader import data
from pandas import DataFrame
import numpy as np

# 3rd party modules
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl

# custom modules

from utils.generic import npDateTime64_2_str
from classes.Stock import Stock
from classes.StockAnalyzer import StockAnalyzer
from classes.FinnhubAPI import FinnhubClient


class StockCompare():

    def __init__(self,stockSymbol):
        # load basic information about the stock
        if isinstance(stockSymbol,Stock):
            self.stock = stockSymbol
        else:
            self.stock = Stock(6,stockSymbol,tradingPlace='',switchLoadData=Stock.LOAD_ALL_DATA)

        self.peerDataFrame = None


    def getPeerGroupComparison(self,extraPeers=[]):

        print('Loading data for peer group\nthis will take a moment...')

        # load the peer group
        peerGroup = FinnhubClient(self.stock.symbol).getPeerGroup()

        # create empty data frames for storing stock values
        df,dfPrc = DataFrame(), DataFrame()

        # remove the stock from the peer group list 
        peerGroup.remove(self.stock.symbol)
        peerGroup.insert(0,self.stock.symbol)

        # add extra peers selected by the user
        if len(extraPeers) > 0:
            for index,symbol in enumerate(extraPeers):
                peerGroup.insert(index+1,symbol)
        print(self.stock.symbol + ' peer group: ' + str(peerGroup))

        firstDate = ''
        for peer in peerGroup:
            # get the name of the stock
            # skip it, if the data could not be loaded successfully
            try:
                legendName = self.createLegendName(peer)
            except KeyError:
                print(' +++ Error while loading "{symbol:s}"\n     Skipping this stock...\n'.format(symbol=peer))
                continue

            # load the data from yahoo finance
            peerData = data.DataReader(peer,'yahoo')

            if firstDate is '':
                firstDate = npDateTime64_2_str(peerData.index.values[0])

            # add the daily values to the data frame
            for date,value in zip(peerData.index.values,peerData.loc[:,'Adj Close']):
                df.loc[date,peer] = value

            # get the value of the first entry to calculate the relative growth
            firstValue = df.loc[firstDate,peer]

            # add the relative growth if the data is not NaN
            if not np.isnan(firstValue):
                # append the relative growth for every day to the data frame
                for date,value in zip(peerData.index.values,peerData.loc[:,'Adj Close']):
                    d = npDateTime64_2_str(date)
                    dfPrc.loc[d,legendName] = value/firstValue

        self.peerDataFrame = dfPrc
        return dfPrc


    def createPDF(self,peerDataFrame=None):

        # get the data frame
        # if no data frame is submitted, then try to get it from the object
        if peerDataFrame is None:
            peerDataFrame = self.peerDataFrame

        # if the data frame is still None, then raise an exception
        if peerDataFrame is None:
            raise ValueError('DataFrame missing')

        stockAnalysis = StockAnalyzer(self.stock)
        StockComparePDF(peerDataFrame,stockAnalysis).createPDF(self.stock.symbol + '_peer_group_comparison.pdf')


    def createLegendName(self,symbol):
        stock = Stock(0,symbol,switchLoadData=Stock.LOAD_BASIC_DATA,tradingPlace='')
        stockName = stock.getStockName()
        return '{symbol:s} ({fullname:s})'.format(symbol=symbol,fullname=stockName)



class StockComparePDF():

    def __init__(self,dataFrame,stockAnalysis=None):

        # check if the argument is of the right type
        if not isinstance(dataFrame,DataFrame):
            raise TypeError('Object ' + str(dataFrame) + ' is no instance of class pandas.DataFrame')

        # store the data frame
        self.dataFrame = dataFrame

        self.stockAnalysis = stockAnalysis


    def createPDF(self,filename):

        # PDF erstellen
        if filename[-4:-1] not in ['.PDF','.pdf']:
            filename = filename + '.pdf'

        pdf = PdfPages(filename)
        FigureSize = (16.3*2 / 2.58, 13.2*2 / 2.58)
        PlotColors = ['tab:blue', 'tab:red', 'tab:green', 'tab:orange',
                    'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray',
                    'tab:olive', 'tab:cyan']
        FontSize = 8
        params = []
        mpl.rcParams['axes.linewidth'] = 0.7
        mpl.rcParams['xtick.labelsize'] = 8
        mpl.rcParams['ytick.labelsize'] = 8

        # add a plot comparing the stock's value growth in percent 
        # compared to the stocks of the peer group
        fig, ax = plt.subplots()

        for columnName in self.dataFrame.columns.values:
            ax.plot(self.dataFrame.loc[:,columnName]*100, label=columnName)
            
        # legend
        ax.legend(loc='upper left')

        # x ticks for the first day of every year
        xticks = [self.dataFrame.index.values[0]]
        for index in self.dataFrame.index.values:
            if index[0:4] != xticks[-1][0:4]:
                xticks.append(index)

        plt.xticks(xticks) 
        plt.grid(which='major')
        plt.grid(b=True, which='minor', color='r', linestyle='--')
        plt.xlabel('Date')
        plt.ylabel('stock value growth in percent')
        plt.title('')

        fig.tight_layout()
        pdf.savefig()
        fig.clf()
        
        # Add a table containings the recommendations for the stock
        if self.stockAnalysis is not None:
            recommendations = self.stockAnalysis.getRecommendations()

            fig, ax = plt.subplots()

            cell_text = []
            for row in recommendations.index.values:
                cellRow = recommendations.loc[row].copy()
                cellRow.loc['Date'] = row
                cellRow.drop(labels=['symbol'])
                index = ['Date']

                # change all float values to int values
                for i in cellRow.index:
                    if isinstance(cellRow[i],float):
                        floatValue = cellRow[i]
                        cellRow[i] = int(floatValue)

                for i in cellRow.index:
                    if i is not 'Date':
                        index.append(i) 

                cellRow = cellRow.reindex(index = index)
                cell_text.append(cellRow)

            plt.table(cellText=cell_text, colLabels=cellRow.index, loc='upper left', FontSize=8)
            plt.axis('off')
            pdf.savefig()

        pdf.close()
        print('PDF mit Ergebnissen wurde erstellt!')