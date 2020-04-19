
# standard modules
import sys, os
from pandas_datareader import data
from pandas import DataFrame
import numpy as np

# 3rd party modules
from matplotlib.backends.backend_pdf import PdfPages, PdfFile
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

        # create an empty data frame
        df = DataFrame()

        # list of all attributes for the table
        attributesList = [Stock.MARKET_PRICE, Stock.PE_RATIO, Stock.EARNINGS_PER_SHARE, \
            Stock.BOOK_VALUE_PER_SHARE, Stock.DIVIDEND, Stock.DIVIDEND_YIELD]
        
        # add all attributes with their values for every stock to the data frame
        for stock in stockList:
            df.loc['Name',stock.symbol] = stock.name

            # analyze the stock
            stockAnalysis = StockAnalyzer(stock)

            # add all attributes to the data frame
            for attribute in attributesList:
                df.loc[attribute,stock.symbol] = stock.getBasicDataItem(attribute)
                if attribute == Stock.EARNINGS_PER_SHARE:
                    meanEps, years = stockAnalysis.getMeanWeightedEPS()
                    df.loc['avg. ' + Stock.EARNINGS_PER_SHARE,stock.symbol] = '{eps:.2f} ({y:.0f}y)'.format(eps=meanEps,y=years)
            
            # add analysis data
            df.loc['fair value',stock.symbol] = stockAnalysis.getFairValue()
            df.loc['Graham number',stock.symbol] = stockAnalysis.getGrahamNumber()

            # add recommendations
            latestRecommendation = stockAnalysis.getLatestRecommendations()
            formatString = '{v:.0f} ({prc:.0f}%)'
            numRecommendations = sum(latestRecommendation)
            for rec in ['strongBuy','buy','hold','sell','strongSell']:
                df.loc['latest ' + rec,stock.symbol] = formatString.format(v=latestRecommendation[rec],prc=latestRecommendation[rec]/numRecommendations*100)

            #ax = latestRecommendation[['strongBuy','buy','hold','sell','strongSell']].plot(kind='bar', title ="buy", legend=True, fontsize=12)
            #ax.set_xlabel("a", fontsize=12)
            #ax.set_ylabel("b", fontsize=12)
            #plt.show()

        return df


    def createLegendName(self,symbol):
        stock = Stock(symbol=symbol,switchLoadData=Stock.LOAD_BASIC_DATA,tradingPlace='')
        stockName = stock.getStockName()
        return '{symbol:s} ({fullname:s})'.format(symbol=symbol,fullname=stockName)



class StockComparePDF():

    # size in pt
    FONTSIZE = 12

    # default figure size in inches
    # DIN A4
    FIGURE_WIDTH = 29.7/2.54
    FIGURE_HEIGHT = 21.0/2.54

    def __init__(self,filename):

        # PDF erstellen
        if filename[-4:] not in ['.PDF','.pdf']:
            filename = filename + '.pdf'

        self.filename = filename
        self.pdf = PdfPages(filename)


    def addPlot(self,dataFrame,legendPos='upper left',xlabel='Date',ylabel='value',title='',ticksX=True,gridMajor=True,gridMinor=True,FontSize=None):

        # define fontsize
        if FontSize is None:
            FontSize = self.FONTSIZE

        # linewidth for the axes
        mpl.rcParams['axes.linewidth'] = 0.7

        # labels are 70% of the fontsize
        mpl.rcParams['xtick.labelsize'] = int(FontSize*0.7)
        mpl.rcParams['ytick.labelsize'] = int(FontSize*0.7)

        # add a plot
        fig, ax = plt.subplots()

        colormap = plt.get_cmap('tab10')
        for index,columnName in enumerate(dataFrame.columns.values):
            ax.plot(dataFrame.loc[:,columnName], label=columnName, color=colormap(index))

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

        fig = plt.gcf()
        fig.set_size_inches(self.FIGURE_WIDTH, self.FIGURE_HEIGHT)

        self.pdf.savefig()
        fig.clf()


    def addTable(self,dataFrame,FontSize=None):

        if FontSize is None:
            FontSize = self.FONTSIZE #int(self.FONTSIZE*0.7)

        cellText = []
        for row in dataFrame.index.values:
            cellRow = dataFrame.loc[row].copy()

            # formatting
            for index,item in enumerate(cellRow):
                # substitute NaN values with '-'
                if (not isinstance(item,str)) and np.isnan(item):
                    cellRow.iloc[index] = '-'
                # format float values
                elif isinstance(item,float) or isinstance(item,int):
                    cellRow.iloc[index] = '{val:.2f}'.format(val=item)

            cellText.append(cellRow)

        # print the table to the document
        plt.table(cellText=cellText, colLabels=cellRow.index, loc='upper left', FontSize=FontSize, rowLabels=dataFrame.index.values)
        plt.axis('off')

        # adjust size of the figure and the page
        fig = plt.gcf()
        fig.set_size_inches(self.FIGURE_WIDTH, self.FIGURE_HEIGHT)

        fig.tight_layout()

        self.pdf.savefig()

    def addBarChart(self,dataFrame,FontSize=None):

        if FontSize is None:
            FontSize = self.FONTSIZE

        # add a plot
        fig, ax = plt.subplots()
        
        # plot data frame
        dataFrame.plot(kind='bar', title ="buy", legend=True, fontsize=FontSize)
        ax.set_xlabel("a", fontsize=12)
        ax.set_ylabel("b", fontsize=12)
        plt.xticks(rotation=45)

        fig = plt.gcf()
        fig.set_size_inches(self.FIGURE_WIDTH, self.FIGURE_HEIGHT)

        self.pdf.savefig()
        fig.clf()


    def closePDF(self):
        try:
            self.pdf.close()
            print(self.filename + ' wurde erstellt!')
        except:
            print(self.filename + ' konnte nicht erstellt werden')
