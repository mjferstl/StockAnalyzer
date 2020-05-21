
import requests
import numpy as np
from datetime import datetime
from pandas import DataFrame


class FinnhubClient():

    APIkey = "bq8r88frh5rc96c0kjf0"
    baseUrl = "https://finnhub.io/api/v1/"

    def __init__(self,symbol):
        self.symbol = symbol
        self.getPeerGroup()


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

        # get reported financial data
        data = self.getFinancialsAsReported(quarterly=quarterly)

        # if no data is available, then an empty DataFrame is returned
        # the reason for receiving no data is perhaps, that the company is not from the US
        if len(data) == 0:
            return DataFrame()

        df = DataFrame()

        for d in data:
            date = self.__getDateFromTime(d['endDate'])
            #print(date)

            # run over all entries in the balance sheet
            balanceSheet = d['report']['bs']
            for bselem in balanceSheet:
                df.loc[bselem,date] = balanceSheet[bselem]

            # run over all entires in the income statement
            incomeStatement = d['report']['ic']
            for icelem in incomeStatement:
                df.loc[icelem,date] = incomeStatement[icelem]

            # run over all entires in the statement of cash flows
            statementOfCashFlows = d['report']['cf']
            for cfelem in statementOfCashFlows:
                df.loc[cfelem,date] = statementOfCashFlows[cfelem]

            # Calculate the free cash flow
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
                    df.loc['freeCashFlow',date] = cashFlowFromOperations - capitalSpending
                else:
                    df.loc['freeCashFlow',date] = cashFlowFromOperations

        return df


    def __getDateFromTime(self,dateTimeString,format='%Y-%m-%d %H:%M:%S'):
        return datetime.strptime(dateTimeString,format).strftime('%Y-%m-%d')


    def getCompanyProfile(self):
        r = requests.get(self.baseUrl + 'stock/profile2?symbol=' + self.symbol + '&freq=annual&token=' + self.APIkey)
        if r.ok:
            return r.json()
        else:
            return []
