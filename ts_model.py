import pandas as pd
import numpy as np
import os
from prophet import Prophet
import plotly
import plotly.express as px
import json
import pickle

path = os.getcwd()
def preprocessing(region):
    regions_list = ["CAL", "CAR", "CENT", "FLA", "MIDA", "MIDW", "NE", "NW", "NY", "SE", "SW", "TEN", "TEX"]
    regions_dict = {}
    for i,regions in enumerate(regions_list):
        regions_dict[regions] = i

    if len(os.listdir(path+'/Data/New/'))!=0:
        combined_regions_df=[pd.DataFrame() for i in range(1)]
        for filename in os.listdir(path+'/Data/New/'):
            if filename==region+'.csv':
                with open(os.path.join(path+'/Data/New/', filename), 'r') as f:
                    combined_regions_df[0]=pd.concat([combined_regions_df[0],pd.read_csv(f)],axis=0,ignore_index=False)
        combined_regions_df[0]=combined_regions_df[0].set_index('UTC Time at End of Hour')
        return combined_regions_df
    else:
        combined_regions_df=[pd.DataFrame() for i in range(13)]
        cols_to_int = ['Demand (MW)', 'Net Generation (MW)']
        combined_regions_df_names = ["CAL", "CAR", "CENT", "FLA", "MIDA", "MIDW", "NE", "NW", "NY", "SE", "SW", "TEN", "TEX"]
        ct=0
        for filename in os.listdir(path+"./Data/Stage/"):
            with open(os.path.join(path+"./Data/Stage/", filename), 'r') as f:
                t=pd.read_csv(f).loc[:, ['Balancing Authority', 'UTC Time at End of Hour', 'Demand (MW)', 'Net Generation (MW)', 'Region']]
                for column in cols_to_int:
                    t[column] = t[column].str.replace(',', '').astype('float')
                t['UTC Time at End of Hour'] = pd.to_datetime(t['UTC Time at End of Hour'])
                t.set_index('UTC Time at End of Hour', inplace = True)

                df = [value for key, value in t.groupby('Region')]

                for i in range(13):
                    combined_regions_df[i]=pd.concat([combined_regions_df[i],df[i]],axis=0,ignore_index=False)
                    ids_to_drop = combined_regions_df[i].loc[(combined_regions_df[i]['Demand (MW)'] < 0)].index
                    combined_regions_df[i].drop(ids_to_drop, axis = 0, inplace = True)
                    combined_regions_df[i]['Demand (MW)'].fillna(method="ffill",inplace=True)

                    ids_to_drop = combined_regions_df[i].loc[(combined_regions_df[i]['Net Generation (MW)'] < 0)].index
                    combined_regions_df[i].drop(ids_to_drop, axis = 0, inplace = True)
                    combined_regions_df[i]['Net Generation (MW)'].fillna(method="ffill",inplace=True)

                    combined_regions_df[i]=combined_regions_df[i].resample('D').sum()

                    q3_percentile_demand = np.percentile(combined_regions_df[i]['Demand (MW)'], 99)
                    for j in range(len(combined_regions_df[i]['Demand (MW)'])):
                        if combined_regions_df[i]['Demand (MW)'][j] > q3_percentile_demand:
                            combined_regions_df[i]['Demand (MW)'][j] = q3_percentile_demand 

                    q1_percentile_demand = np.percentile(combined_regions_df[i]['Demand (MW)'], 5)
                    for j in range(len(combined_regions_df[i]['Demand (MW)'])):
                        if combined_regions_df[i]['Demand (MW)'][j] < q1_percentile_demand:
                            combined_regions_df[i]['Demand (MW)'][j] = q1_percentile_demand 


                    q3_percentile_demand = np.percentile(combined_regions_df[i]['Net Generation (MW)'], 99)
                    for j in range(len(combined_regions_df[i]['Net Generation (MW)'])):
                        if combined_regions_df[i]['Net Generation (MW)'][j] > q3_percentile_demand:
                            combined_regions_df[i]['Net Generation (MW)'][j] = q3_percentile_demand 

                    q1_percentile_demand = np.percentile(combined_regions_df[i]['Net Generation (MW)'], 5)
                    for j in range(len(combined_regions_df[i]['Net Generation (MW)'])):
                        if combined_regions_df[i]['Net Generation (MW)'][j] < q1_percentile_demand:
                            combined_regions_df[i]['Net Generation (MW)'][j] = q1_percentile_demand 

        for i in range(len(combined_regions_df)):
            combined_regions_df[i].to_csv(path+"/Data/New/"+combined_regions_df_names[i]+".csv")

        return combined_regions_df[regions_dict[region]]


def plotss(combined_regions_df,predictions,region,name):
    fig = px.line(combined_regions_df[0], x=combined_regions_df[0].index , y=name+" (MW)",title=region)
    fig.data[0].name = 'Original'
    fig.update_traces(showlegend=True)
    fig.add_scatter(x = predictions['ds'],y=predictions['yhat'],mode='lines',name='forecasted')
    graphJSON = json.dumps(fig,cls=plotly.utils.PlotlyJSONEncoder)
    
    return graphJSON

def prediction(region):

    combined_regions_df = preprocessing(region)
    print(region)
    if len(os.listdir(path+'/Data/models/'))==0:
        prophet(combined_regions_df)
    demand = pforecast(100,'Demand',region)
    net_generation = pforecast(100,'Net Generation',region)
    
    graphJSON = plotss(combined_regions_df,demand,region,'Demand')
    graphJSON1 = plotss(combined_regions_df,net_generation,region,'Net Generation')
    
    return graphJSON,graphJSON1

def prophet(combined_regions_df):
    regions_list = ["CAL", "CAR", "CENT", "FLA", "MIDA", "MIDW", "NE", "NW", "NY", "SE", "SW", "TEN", "TEX"]
    regions_dict = {}
    for i,regions in enumerate(regions_list):
        regions_dict[regions] = i
    models = []
    for i in range(0,13):
        temp_demand = pd.DataFrame(combined_regions_df[i]['Demand (MW)'])
        temp_gen = pd.DataFrame(combined_regions_df[i]['Net Generation (MW)'])
        temp_demand = temp_demand.reset_index()
        temp_gen = temp_gen.reset_index()
        temp_demand = temp_demand.rename(columns={'UTC Time at End of Hour':'ds','Demand (MW)':'y'})
        temp_gen = temp_gen.rename(columns={'UTC Time at End of Hour':'ds','Net Generation (MW)':'y'})
        exec(regions_list[i] + '_demand' + '=' + 'Prophet()')
        exec(regions_list[i] + '_gen' + '=' + 'Prophet()')
        exec('models.append(' + regions_list[i] + '_demand' + ')')
        exec('models.append(' + regions_list[i] + '_gen' + ')')
        exec(regions_list[i] + '_demand' + '.fit(temp_demand)')
        exec(regions_list[i] + '_gen' + '.fit(temp_demand)')
        filename1 = regions_list[i] + '_demand'
        filename2 = regions_list[i] + '_gen'
        path1 = path + '/Data/models/' + regions_list[i] + '_demand.pckl'
        path2 = path + '/Data/models/' + regions_list[i] + '_gen.pckl'
        with open(path1,'wb') as fout1:
          exec('pickle.dump(' + filename1 + ',fout1)')
        with open(path2,'wb') as fout2:
          exec('pickle.dump(' + filename2 + ',fout2)')

def pforecast(number_of_days,type,region):
  if type == 'Demand':
    paths =path+'/Data/models/' + region + '_demand.pckl'
    with open(paths,'rb') as fin:
      demand_model = pickle.load(fin)
    future_demand = demand_model.make_future_dataframe(periods=number_of_days)
    forecast = demand_model.predict(future_demand)
    return forecast[['ds','yhat']].tail(number_of_days+1)
  elif type == 'Net Generation':
    paths =path+'/Data/models/' + region + '_gen.pckl'
    with open(paths,'rb') as fin:
      gen_model = pickle.load(fin)
    future_demand = gen_model.make_future_dataframe(periods=number_of_days)
    forecast = gen_model.predict(future_demand)
    return forecast[['ds','yhat']].tail(number_of_days+1)