from yahoo_finance import Share
from pandas import *
from numpy import *
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import datetime
from app import app
from flask import render_template,request,send_file,jsonify
from StringIO import StringIO
import time






def correl_computation(ticker1,ticker2,start_date,end_date,window):
    Share1 =Share(ticker1)
    Share2=Share(ticker2)

    Share1_list=Share1.get_historical(start_date, end_date)
    Share2_list=Share2.get_historical(start_date, end_date)

    #dictionaries creation with Date as key
    Share1_dic={}
    Share2_dic={}

    for i in range(len(Share1_list)-1,-1,-1):
        split_date=Share1_list[i]['Date'].split("-")
        date=datetime.datetime(int(split_date[0]),int(split_date[1]),int(split_date[2]))
        Share1_dic[date]=Share1_list[i]
    

    for i in range(len(Share2_list)-1,-1,-1):
        split_date=Share2_list[i]['Date'].split("-")
        date=datetime.datetime(int(split_date[0]),int(split_date[1]),int(split_date[2]))
        Share2_dic[date]=Share2_list[i]


    #Remove the Volume = 0
    for i in Share1_dic.keys():
        if Share1_dic[i]['Volume']=='000':
            print 'deleted Volume=0'
            del Share1_dic[i]

    for i in Share2_dic.keys():
        if Share2_dic[i]['Volume']=='000':
            print 'deleted Volume=0'
            del Share2_dic[i]

    #Data synchronisation
    diffL = [ k for k in Share1_dic if k not in Share2_dic ]
    diffR = [ k for k in Share2_dic if k not in Share1_dic ]

    for i in Share1_dic.keys():
        for j in diffL:
            if i==j:
                print 'deleted Date on Share1_dic'
                del Share1_dic[i]

    for i in Share2_dic.keys():
        for j in diffR:
            if i==j:
                print 'deleted Date on Share2_dic'
                del Share2_dic[i]



    #Ajusted Close fetching
    list=[]
    for i in sorted(Share1_dic):
        list.append(Share1_dic[i]['Adj_Close'])
    
    Share1_AdjClose_array=np.array(list[1:],dtype=float64)
    Share1_AdjClose_array=Share1_AdjClose_array/float(list[0])
    Share1_AdjClose_log_array=np.log(np.array(list,dtype=float64))

    list=[]
    for i in sorted(Share2_dic):
        list.append(Share2_dic[i]['Adj_Close'])

    Share2_AdjClose_array=np.array(list[1:],dtype=float64)
    Share2_AdjClose_array=Share2_AdjClose_array/float(list[0])
    Share2_AdjClose_log_array=np.log(np.array(list,dtype=float64))

    Share1_AdjClose_logReturns_array=Share1_AdjClose_log_array[1:Share1_AdjClose_log_array.size]-Share1_AdjClose_log_array[0:Share1_AdjClose_log_array.size-1]
    Share2_AdjClose_logReturns_array=Share2_AdjClose_log_array[1:Share2_AdjClose_log_array.size]-Share2_AdjClose_log_array[0:Share2_AdjClose_log_array.size-1]

    #correlation computation
    corr_array=rolling_corr(Share1_AdjClose_logReturns_array,Share2_AdjClose_logReturns_array,window=window,pairwise=True)

    #Retrieve the dates list to plot the correlation with respect to the time
    X=[]
    for i in sorted(Share1_dic):
        X.append(i)
    X=X[1:]


    return X, corr_array,Share1_AdjClose_array,Share2_AdjClose_array



def correl_plot(x,y,charttitle):
    fig = plt.figure()
    gs = GridSpec(1,1,bottom=0.18,left=0.18,right=0.82)
    ax = fig.add_subplot(gs[0,0])
    line = ax.plot(x,y,linewidth=2,color="green" ,linestyle="-")
    plt.title(charttitle[:-19].replace('_',' '))

    ax.set_xlabel('')
    ax.set_ylabel('Correlation')

    # Changing the label's font-size
    ax.tick_params(axis='x', labelsize=8)
    labels = ax.get_xticklabels() 
    for label in labels: 
        label.set_rotation(90) 
    return  fig
  
    
def share_plot(x,y1,y2,charttitle,ticker1,ticker2):
    fig = plt.figure()
    gs = GridSpec(1,1,bottom=0.18,left=0.18,right=0.82)
    ax = fig.add_subplot(gs[0,0])
    line1 = ax.plot(x,y1,linewidth=2,color="blue" ,linestyle="-",label=ticker1)
    line2 = ax.plot(x,y2,linewidth=2,color="red" ,linestyle="-",label=ticker2)
    plt.title(charttitle[:-19].replace('_',' '))
    ax.set_xlabel('')
    ax.set_ylabel('Stocks')
    ax.set_yticklabels([])
    plt.legend()

    # Changing the label's font-size
    ax.tick_params(axis='x', labelsize=8)
    labels = ax.get_xticklabels() 
    for label in labels: 
        label.set_rotation(90) 

    return  fig





#-------------------------Flask--------------------

@app.errorhandler(Exception)
def exception_handler(error):
    if  repr(error).startswith("IndexError")==True or str(error).startswith("'NoneType")==True:
        return render_template("error.html",error_str='Inputs Error !')
    else:
        return render_template("error.html",error_str=str(error))



@app.route('/')
def my_form():
    return render_template("index.html")


@app.route('/', methods=['POST'])
def my_form_post():
    ticker1 = request.form['ticker1']
    ticker2 = request.form['ticker2']
    window=int(request.form['window'])
    start_date='{0}-{1}-{2}'.format(request.form['sy'],request.form['sm'],request.form['sd'])
    end_date='{0}-{1}-{2}'.format(request.form['ey'],request.form['em'],request.form['ed'])
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')
    global global_x
    global global_y
    global global_s1
    global global_s2
    global_x,global_y,global_s1,global_s2=correl_computation(ticker1,ticker2,start_date,end_date,window)
    if len(global_x)<=window:
        raise ValueError('The period is to short to compute the correlation') 
    charttitle1='{0}_{1}_Correlation_{2}_{3}_{4}_{5}.svg'.format(ticker1,ticker2,start_date,end_date,window,timestamp)
    charttitle2='{0}_{1}_Stocks_{2}_{3}_{4}.svg'.format(ticker1,ticker2,start_date,end_date,timestamp)

    return output(charttitle1,charttitle2,ticker1,ticker2)

@app.route('/output/<charttitle1>')
def output(charttitle1,charttitle2,ticker1,ticker2):
    return render_template("output.html", title1=charttitle1, title2=charttitle2,tick1=ticker1,tick2=ticker2)

@app.route('/fig1/<charttitle1>')
def fig1(charttitle1):
    fig1=correl_plot(global_x,global_y,charttitle1)
    img1 = StringIO()
    fig1.savefig(img1,format='svg')
    img1.seek(0)
    return send_file(img1, mimetype='image/svg+xml')

@app.route('/fig2/<charttitle2>')
def fig2(charttitle2):
    ticker= charttitle2.split('_', 2 )
    fig2=share_plot(global_x,global_s1,global_s2,charttitle2,ticker[0],ticker[1])
    img2 = StringIO()
    fig2.savefig(img2,format='svg')
    img2.seek(0)
    return send_file(img2, mimetype='image/svg+xml')


 



