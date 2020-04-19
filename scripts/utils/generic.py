

import numpy as np
from datetime import datetime



def npDateTime64_2_datetime(npDatetime64):
    if isinstance(npDatetime64,list) or isinstance(npDatetime64,np.ndarray):
        return [npDateTime64_2_datetime(dt) for dt in npDatetime64]
    elif isinstance(npDatetime64,np.datetime64):
        ts = (npDatetime64 - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')
        return datetime.utcfromtimestamp(ts)


def npDateTime64_2_str(npDatetime64,format='%Y-%m-%d'):
    if isinstance(npDatetime64,list) or isinstance(npDatetime64,np.ndarray):
        return [npDateTime64_2_datetime(dt).strftime(format) for dt in npDatetime64]
    else:
        return npDateTime64_2_datetime(npDatetime64).strftime(format)


def mergeDataFrame(dataFrame1,dataFrame2):

    # loop over all rows and columns
    for row in dataFrame2.index.values:
        for column in dataFrame2.columns.values:

            # try to covert the column name to a string, if it is a date
            if isinstance(column,np.datetime64):
                columnName = npDateTime64_2_str(column)
            else:
                columnName = column
            
            dataFrame1.loc[row,columnName] = dataFrame2.loc[row,column]

    return dataFrame1