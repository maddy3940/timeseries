import pandas as pd
import numpy as np
from flask import Flask,request,render_template,url_for,redirect
import pickle
import ts_model as t
import os
from flask import send_file
import plotly
import plotly.express as px
import json

app = Flask(__name__,template_folder = 'template')

region1 = ''

#Home Page
@app.route('/')
def home():
    return(render_template('index.html'))

@app.route('/compare',methods=['GET','POST'])
def compare():

    region1=request.args.get('region1','NW')
    region2=request.args.get('region2','CAL')

    name=request.args.get('name','Demand')
    print("########################")
    print(region1)
    print(region2)
    print("########################")
    
    graphJSON00,graphJSON01 = t.prediction(region1)

    graphJSON10,graphJSON11 = t.prediction(region2)
    
    if name=='Demand':
        graphJSON0=graphJSON00
        graphJSON1=graphJSON10
    else:
        graphJSON0=graphJSON01
        graphJSON1=graphJSON11

    #print(address)
    return(render_template('compare.html',graphJSON0=graphJSON0,graphJSON1=graphJSON1,Name=name,Region1=region1,Region2=region2))

@app.route('/plot',methods=['GET','POST'])
def plot():
    # print(request)
    region1=request.args.get('region',None)
    # print(region1)
    
    if request.method == 'POST':
        return(redirect(url_for('plot_selection',Region=region1)))
    else:
        return(render_template('plot.html'))
    

@app.route('/plot_selection',methods=['GET','POST'])
def plot_selection():
    
    # print(region1)
    # if request.method == 'POST':
    #     return(redirect(url_for('plot_selection',Region=region1)))

    region1=request.args.get('region',None)

    graphJSON,graphJSON1 = t.prediction(region1)
 
    return(render_template('plot_selection.html',graphJSON=graphJSON,graphJSON1=graphJSON1,Region=region1))

@app.route('/about-us')
def about():
    return(render_template('about-us.html'))

if __name__ == '__main__':
    app.run()