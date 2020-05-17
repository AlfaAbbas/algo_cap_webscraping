from flask import Flask, render_template 
import pandas as pd
import requests
from bs4 import BeautifulSoup 
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import dateparser

app = Flask(__name__)

def scrap(url):
    #This function is for scrapping
    url_get = requests.get(url)
    soup = BeautifulSoup(url_get.content,"html.parser")
    
    #Find the key to get the information
    table = soup.find('table', attrs={'class':'centerText newsTable2'}) 
    tr = table.find_all('tr')

    temp = [] #initiating a tuple

    for i in range(1, len(tr)):
        row = table.find_all('tr')[i]
        #use the key to take information here
        #name_of_object = row.find_all(...)[0].text
        #get tanggal
        tanggal = row.find_all('td')[0].text
        tanggal = tanggal.strip() #remove excess whitespace
        tanggal = tanggal.replace(u'\xa0', u' ')
        
        #get kurs_jual (ask)
        kurs_jual = row.find_all('td')[1].text
        kurs_jual = kurs_jual.strip() #remove excess whitespace
        
        #get kurs_beli (bid)
        kurs_beli = row.find_all('td')[2].text
        kurs_beli = kurs_beli.strip() #remove excess whitespace

        temp.append((tanggal, kurs_jual, kurs_beli)) #append the needed information 
    
    temp = temp[::-1] #reverse tuple to sort 'tanggal' from start of the year (January)

    df = pd.DataFrame(temp, columns = ('tanggal', 'kurs_jual', 'kurs_beli')) #creating the dataframe

    #data wrangling - try to change the data type to right data type

    #replace all commas in kurs_jual and kurs_beli into periods to allow data type conversion into float64
    df['kurs_jual'] = df['kurs_jual'].str.replace(",",".")
    df['kurs_beli'] = df['kurs_beli'].str.replace(",",".")

    #convert date format from Indonesian string into datetime
    df['tanggal'] = df['tanggal'].apply(lambda x: dateparser.parse(x))

    #convert kurs_jual and kurs_beli data type from string to float64
    df[['kurs_jual', 'kurs_beli']] = df[['kurs_jual', 'kurs_beli']].astype('float64')

    #add new column 'periode' to represent month period from 'tanggal'
    df['periode'] = df['tanggal'].dt.to_period('M')

    #set dataframe to group by 'period' and aggregate average (mean) value of kurs_jual and kurs_beli
    df = df.groupby('periode').mean().round(2)

    #end of data wrangling

    return df

@app.route("/")
def index():
    df = scrap("https://monexnews.com/kurs-valuta-asing.htm?kurs=JPY&searchdatefrom=01-01-2019&searchdateto=31-12-2019") #insert url here

    #This part for rendering matplotlib
    fig = plt.figure(figsize=(5,2),dpi=300)
    df.plot()
    
    #Do not change this part
    plt.savefig('plot1',bbox_inches="tight") 
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result = str(figdata_png)[2:-1]
    #This part for rendering matplotlib

    #this is for rendering the table
    df = df.to_html(classes=["table table-bordered table-striped table-dark table-condensed"])

    return render_template("index.html", table=df, result=result)


if __name__ == "__main__": 
    app.run()
