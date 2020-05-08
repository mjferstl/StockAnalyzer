

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl



def createPlot(x_data_list,y_data_list,legend_list=None):

    # add a plot
    fig, ax = plt.subplots()

    #colormap = plt.get_cmap('tab10')
    #print(x_data_list,yData/10**9)
    if isinstance(x_data_list[0],list):
        for i in range(len(x_data_list)):
            if legend_list is None or legend_list[i] is None:
                ax.plot(x_data_list[i],y_data_list[i], marker='o', linestyle='None')
            else:
                ax.plot(x_data_list[i],y_data_list[i], marker='o', linestyle='None',label=legend_list[i])
    else:
        ax.plot(x_data_list,y_data_list, marker='o', linestyle='None')

    # legend
    if legend_list is not None:
        ax.legend(loc='upper left')

    #plt.xlabel(xlabel)
    #plt.ylabel(ylabel)
    #plt.title(title)

    fig.tight_layout()

    plt.show()