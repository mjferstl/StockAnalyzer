
from pandas import DataFrame

import yfinance as yf

from utils.yfinance_extension import loadExtraIncomeStatementData, load_CashFlow
from utils.generic import mergeDataFrame


class YFinanceClient():

    def __init__(self,symbol):
        # initialize variables
        self.initVariables()

        self.symbol = symbol

    def initVariables(self):
        self._ticker = None
        self._symbol = None

    
    @property
    def Ticker(self):
        if self._ticker is not None:
            return self._ticker
        elif self.symbol is not None:
            self._ticker = yf.Ticker(self.symbol)
            return self._ticker
        else:
            raise ValueError('Stock symbol missing.')

    @Ticker.setter
    def Ticker(self,ticker):
        if not isinstance(ticker,yf.Ticker):
            raise TypeError('The ticker "' + str(ticker) + '" is no instance of yfinance.Ticker')
        else:
            self._ticker = ticker

    
    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self,symbol):
        self._symbol = symbol


    def getFinancialStatements(self):
        df = DataFrame()
        df = self.getBalanceSheet()
        df = mergeDataFrame(df, self.getIncomeStatement())
        df = mergeDataFrame(df, self.getCashflowStatement())
        return df


    def getBalanceSheet(self):
        return self.Ticker.balance_sheet


    def getIncomeStatement(self):

        # load income statement with yfinance module
        income = self.Ticker.financials

        # load extra data, which yfinance module does not load
        df = loadExtraIncomeStatementData(self.symbol)
        
        # add the data to the financialData data frame
        return mergeDataFrame(income,df)
         

    def getCashflowStatement(self):

        # load statement of cashflows with yfinance module
        cashflow = self.Ticker.cashflow

        # load extra data, which yfinance module does not load
        df = load_CashFlow(self.symbol)

        return mergeDataFrame(cashflow,df)