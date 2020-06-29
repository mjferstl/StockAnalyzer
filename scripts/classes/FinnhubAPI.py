
import os
import requests
import numpy as np
from datetime import datetime
from pandas import DataFrame
import json

from utils.generic import npDateTime64_2_str
from classes.GlobalVariables import *


class FinnhubClient():

    _APIkey = None
    baseUrl = "https://finnhub.io/api/v1/"

    NOT_DATA_VALUE = np.nan

    def __init__(self,symbol):
        self.symbol = symbol
        self.getPeerGroup()
        self._APIkey = None

    @property
    def APIkey(self):
        if self._APIkey is None:
            currentFolder = os.path.dirname(os.path.abspath(__file__))
            with open(currentFolder + '/FinnhubAccountData.json') as f:
                self._APIkey = json.load(f)['APIkey']
        return self._APIkey


    def getData(self):
        print('Open and close data')
        r = requests.get(self.baseUrl + 'quote?symbol=' + self.symbol + '&token=' + self.APIkey)
        if r.ok:
            return r.json()
        else:
            return ''


    def getDividend(self,startDate="2015-04-01",endDate="2020-04-01"):
        print('Dividend')
        r = requests.get(self.baseUrl + 'stock/dividend?symbol=' + self.symbol + '&from=' + startDate + '&to=' + endDate + '&token=' + self.APIkey)
        if r.ok:
            return r.json()
        else: 
            return ''


    def getPeerGroup(self):
        r = requests.get(self.baseUrl + 'stock/peers?symbol=' + self.symbol + '&token=' + self.APIkey)
        if not r.ok:
            return ''
        else:
            return r.json()


    def getMetricsPerShare(self):
        print('Metrics per share')
        r = requests.get(self.baseUrl + 'stock/metric?symbol=' + self.symbol + '&metric=perShare&token=' + self.APIkey)
        if r.ok:
            return r.json()
        else:
            return ''


    def getRecommendations(self):
        r = requests.get(self.baseUrl + 'stock/recommendation?symbol=' + self.symbol + '&token=' + self.APIkey)
        if r.ok:
            return r.json()
        else:
            return ''


    def getRecommendationsDataFrame(self):
        # get the recommandations 
        recommendations = self.getRecommendations()

        # create an empty data frame
        df = DataFrame()

        # check if the received data is not empty
        if recommendations is not '':

            # add all items to the data frame
            for recommendation in recommendations:
                date = recommendation['period']

                # get all key names exept 'date'
                dataKeys = list(recommendation.keys())
                dataKeys.remove('period')

                for key in dataKeys:
                    df.loc[date,key] = recommendation[key]

        # return the data frame
        return df


    def getEpsEstimates(self):
        r = requests.get(self.baseUrl + 'stock/eps-estimate?symbol=' + self.symbol + '&freq=annual&token=' + self.APIkey)
        if r.ok:
            return r.json()['data']
        else:
            return []


    def getFinancialsAsReported(self,quarterly=False):
        r = requests.get(self.baseUrl + 'stock/financials-reported?symbol=' + self.symbol + '&freq=annual&token=' + self.APIkey)
        if r.ok:
            return r.json()['data']
        else:
            return []

    def getFinancialsAsReportedDataFrame(self,quarterly=False):

        df_fullData = DataFrame()
        df_mainData = DataFrame()

        # get reported financial data
        data = self.getFinancialsAsReported(quarterly=quarterly)

        # if no data is available, then an empty DataFrame is returned
        # the reason for receiving no data is perhaps, that the company is not from the US
        if len(data) == 0:
            return df_fullData, df_mainData

        for d in data:
            date = self.__getDateFromTime(d['endDate'])
            #print(date)

            # run over all entries in the balance sheet
            balanceSheet = d['report']['bs']
            for index, bselem in enumerate(balanceSheet):
                df_fullData.loc[bselem['concept'],date] = balanceSheet[index]['value']

            # run over all entires in the income statement
            incomeStatement = d['report']['ic']
            for index, icelem in enumerate(incomeStatement):
                df_fullData.loc[icelem['concept'],date] = incomeStatement[index]['value']

            # run over all entires in the statement of cash flows
            statementOfCashFlows = d['report']['cf']
            for index, cfelem in enumerate(statementOfCashFlows):
                df_fullData.loc[cfelem['concept'],date] = statementOfCashFlows[index]['value']

            ## Free cash flow
            cashFlowFromOperations = None 
            if ('NetCashProvidedByUsedInOperatingActivities' in statementOfCashFlows):
                cashFlowFromOperations = statementOfCashFlows['NetCashProvidedByUsedInOperatingActivities']
            elif ('NetCashProvidedByUsedInOperatingActivitiesContinuingOperations' in statementOfCashFlows):
                cashFlowFromOperations = statementOfCashFlows['NetCashProvidedByUsedInOperatingActivitiesContinuingOperations']
            
            capitalSpending = None
            if ('PaymentsToAcquirePropertyPlantAndEquipment' in statementOfCashFlows):
                capitalSpending = statementOfCashFlows['PaymentsToAcquirePropertyPlantAndEquipment']

            if ('PaymentsToAcquireIntangibleAssets' in statementOfCashFlows) and (capitalSpending is not None):
                if not np.isnan(statementOfCashFlows['PaymentsToAcquireIntangibleAssets']):
                    capitalSpending += statementOfCashFlows['PaymentsToAcquireIntangibleAssets']

            if (cashFlowFromOperations is not None):
                # e.g. for bank companies there is no capitalSpending in the statement of cashflows
                if (capitalSpending is not None):
                    df_mainData.loc[FREE_CASH_FLOW,date] = cashFlowFromOperations - capitalSpending
                else:
                    df_mainData.loc[FREE_CASH_FLOW,date] = cashFlowFromOperations

            ## Net income
            df_mainData.loc[NET_INCOME,date] = self._getValueFromDict(incomeStatement,'NetIncomeLoss')

            ## Revenues/Sales
            key = 'Revenues'
            key2 = 'RevenueFromContractWithCustomerExcludingAssessedTax'
            df_mainData.loc[REVENUES,date] = self._getValueFromDict(incomeStatement,[key,key2])

            ## Stock Holders Equity
            df_mainData.loc[STOCKHOLDERS_EQUITY,date] = self._getValueFromDict(balanceSheet,'StockholdersEquity')

            ## Assets
            df_mainData.loc[ASSETS,date] = self._getValueFromDict(balanceSheet,'Assets')

            ## Cash from operating activities
            key = 'NetCashProvidedByUsedInOperatingActivities'
            key2 = 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'
            df_mainData.loc[CASH_FROM_OPERATING_ACTIVITIES,date] = self._getValueFromDict(statementOfCashFlows,[key,key2])

            ## Number of diluted average shares
            df_mainData.loc[DILUTED_AVERAGE_SHARES,date] = self._getValueFromDict(incomeStatement,'WeightedAverageNumberOfDilutedSharesOutstanding')

            ## Operating income
            df_mainData.loc[OPERATING_INCOME,date] = self._getValueFromDict(incomeStatement,'OperatingIncomeLoss')

            ## Ebit
            df_mainData.loc[EBIT,date] = self._getValueFromDict(incomeStatement,'OperatingIncomeLoss')
            
        return df_fullData, df_mainData


    def __getDateFromTime(self,dateTimeString,format='%Y-%m-%d %H:%M:%S'):
        return datetime.strptime(dateTimeString,format).strftime('%Y-%m-%d')


    def getCompanyProfile(self):
        r = requests.get(self.baseUrl + 'stock/profile2?symbol=' + self.symbol + '&freq=annual&token=' + self.APIkey)
        if r.ok:
            return r.json()
        else:
            return []


    def _getValueFromDict(self,statement,keys):

        if isinstance(keys,str):
            keys = [keys]

        for key in keys:
            for item in statement:
                if item['concept'] == key:
                    return item['value']
        
        return self.NOT_DATA_VALUE
