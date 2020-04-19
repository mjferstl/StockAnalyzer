
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
            self.stock = Stock(symbol=stockSymbol,tradingPlace='',switchLoadData=Stock.LOAD_ALL_DATA)

        self.peerDataFrame = None


    def getPeerGroup(self,symbol,extraPeers=[]):

        print('Loading data for peer group\nthis will take a moment...')

        # load the peer group
        peerGroup = FinnhubClient(symbol).getPeerGroup()

        # remove the stock from the peer group list 
        peerGroup.remove(symbol)
        peerGroup.insert(0,symbol)

        # add extra peers selected by the user
        if len(extraPeers) > 0:
            for index,symbol in enumerate(extraPeers):
                peerGroup.insert(index+1,symbol)
        print(symbol + ' peer group: ' + str(peerGroup))

        # load data for all peers
        peerStockList = []
        for iPeer,peer in enumerate(peerGroup):
            # print the status to the console
            print(str(int(iPeer*1.0/len(peerGroup)*100)) + "% - " + peer)

            # load the data from yahoo finance
            try:
                peerStock = Stock(peer)

                # add the stock to the list
                peerStockList.append(peerStock)
            except Exception:
                print('Could not load data for ' + peer)
        print('100%')

        return peerStockList

    def getPeerGroupChangePrc(self,stockList):

        # create an empty data frame
        df = DataFrame()

        referenceDate = npDateTime64_2_str(stockList[0].historicalData.index.values[0])

        for stock in stockList:
            stockSymbol = stock.symbol

            # check if the stock's values start at the same date
            # otherwise no comparison is made
            if (referenceDate in npDateTime64_2_str(stock.historicalData.index.values)):
                # get the stock's value at the reference date
                referenceValue = stock.historicalData.loc[referenceDate,'Close']
            
                # loop over all historical stock values and calculate the 
                # stock's value change in percent
                for date, value in zip(stock.historicalData.index.values, stock.historicalData.loc[:,'Close']):
                    if not np.isnan(value):
                        d = npDateTime64_2_str(date)
                        df.loc[d,stockSymbol] = value/referenceValue*100.0

        return df

    def comparePeerGoupMainValues(self,stockList):
        df = DataFrame()

        attributesList = [Stock.PE_RATIO, Stock.EARNINGS_PER_SHARE, Stock.BOOK_VALUE_PER_SHARE, \
            Stock.DIVIDEND, Stock.DIVIDEND_YIELD]
        for stock in stockList:
            for attribute in attributesList:
                df.loc[attribute,stock.symbol] = stock.getBasicDataItem(attribute)

        return df


    def createLegendName(self,symbol):
        stock = Stock(symbol=symbol,switchLoadData=Stock.LOAD_BASIC_DATA,tradingPlace='')
        stockName = stock.getStockName()
        return '{symbol:s} ({fullname:s})'.format(symbol=symbol,fullname=stockName)



class StockComparePDF():

    FONTSIZE = 8

    def __init__(self,filename):

        # PDF erstellen
        if filename[-4:-1] not in ['.PDF','.pdf']:
            filename = filename + '.pdf'

        self.filename = filename
        self.pdf = PdfPages(filename)


    def addPlot(self,dataFrame,legendPos='upper left',xlabel='Date',ylabel='value',title='',ticksX=True,gridMajor=True,gridMinor=True,FontSize=None):

        if FontSize is None:
            FontSize = self.FONTSIZE

        #FigureSize = (16.3*2 / 2.58, 13.2*2 / 2.58)
        PlotColors = ['tab:blue', 'tab:red', 'tab:green', 'tab:orange',
                    'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray',
                    'tab:olive', 'tab:cyan']

        mpl.rcParams['axes.linewidth'] = 0.7
        mpl.rcParams['xtick.labelsize'] = FontSize
        mpl.rcParams['ytick.labelsize'] = FontSize

        # add a plot
        fig, ax = plt.subplots()

        for columnName in dataFrame.columns.values:
            ax.plot(dataFrame.loc[:,columnName], label=columnName)

        # legend
        ax.legend(loc='upper left')

        if ticksX:
            # x ticks for the first day of every year
            xticks = [dataFrame.index.values[0]]
            for index in dataFrame.index.values:
                if index[0:4] != xticks[-1][0:4]:
                    xticks.append(index)

            plt.xticks(xticks)

        if gridMajor:
            plt.grid(which='major')

        if gridMinor:
            plt.grid(b=True, which='minor', color='r', linestyle='--')

        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)

        fig.tight_layout()
        self.pdf.savefig()
        fig.clf()


    def addTable(self,dataFrame,FontSize=None):

        if FontSize is None:
            FontSize = self.FONTSIZE

        cellText = []
        for row in dataFrame.index.values:
            cellRow = dataFrame.loc[row].copy()

            # substitute NaN values with '-'
            for index,item in enumerate(cellRow):
                if np.isnan(item):
                    cellRow.iloc[index] = '-'

            cellText.append(cellRow)

        plt.table(cellText=cellText, colLabels=cellRow.index, loc='upper left', FontSize=FontSize, rowLabels=dataFrame.index.values)
        plt.axis('off')
        self.pdf.savefig()


    def closePDF(self):
        try:
            self.pdf.close()
            print(self.filename + ' wurde erstellt!')
        except:
            print(self.filename + ' konnte nicht erstellt werden')


    def createPDFDEPREACHED(self,filename):

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