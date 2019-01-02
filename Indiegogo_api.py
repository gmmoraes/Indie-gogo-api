import flask
import os
import requests
import sys
import time
import pandas as pd
import json
from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from multiprocessing import Process
from multiprocessing import Process
from flask import request, jsonify

url = 'https://www.indiegogo.com/explore/video-games?project_type=campaign&project_timing=all&sort=trending'

def get_info():
    # instantiate a chrome options object so you can set the size and headless preference
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--incognito")
    # current directory

    # 1 - WINDOWS
    #chrome_driver = os.getcwd() +"\chromedriver.exe"
    #driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=chrome_driver)
    
    # 2 - MAC
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver")


    driver = webdriver.Chrome(executable_path = DRIVER_BIN)


    driver.get(url)

    for i in range(6):
        driver.find_element_by_class_name('exploreMore').click()
        time.sleep( 1 )


    time.sleep( 5 )

    # Wait for the dynamically loaded elements to show up
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "discoverableCard-title")))


    # And grab the page HTML source
    html_page = driver.page_source


    driver.quit()


    #discoverableCard-title
    soup = BeautifulSoup(html_page, 'html.parser')
    non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
    #print(soup.prettify().translate(non_bmp_map))
    titles = soup.findAll("div", {"class": "discoverableCard-title"})
    percentages = soup.findAll("div", {"class": "discoverableCard-percent"})
    total_value = soup.findAll("div", {"class": "discoverableCard-balance"})
    currencies = soup.findAll("div", {"class": "discoverableCard-unitsRaised"})
    #dates = soup.findAll("span", {"class": "discoverableCard-formattedDate"})
    dates = soup.findAll("span", {'class':['discoverableCard-formattedDate', 'discoverableCard-InDemandHover']})
    #urls = soup.findAll("div", {"class": "discoverableCard"}).findChildren("a" , href=True) #####pegar
    urls = soup.select(".discoverableCard > a")

    title_list = []
    percentage_list = []
    total_value_list = []
    currencies_list = []
    dates_list = []
    amount_list = []
    url_list = []

    for title in titles:
        title_list.append(title.text)


    for percentage in percentages:
        percentage_list.append(percentage.text.strip())
    

    for value in total_value:
        total_value_list.append(value.text[1:].strip())

    for currency in currencies:
        if(currency.text[-6:] == 'raised'):
            currencies_list.append(currency.text[:len(currency.text)-6].strip())
        else:
            currencies_list.append(currency.text)

    for date in dates:
        if(date.text[-9:] == 'days left'):
            dates_list.append(date.text[:len(date.text)-9])
            amount_list.append('days')
        elif(date.text[-10:] == 'hours left'):
            dates_list.append(date.text[:len(date.text)-11])
            amount_list.append('hours')
        elif(date.text[-11:] == 'minutes left'):
            dates_list.append(date.text[:len(date.text)-12])
            amount_list.append('minutes')
        else:
           dates_list.append(date.text)
           amount_list.append('.')
        #print(date.text[-10:])

    for a in urls:
        url_list.append(a['href'])


    d = {'titles':title_list,'percentages':percentage_list,'total_value':total_value_list,'currencies':currencies_list,'dates':dates_list,'amount':amount_list,'url_list':url_list}
    return d
    convert_to_json(d)

def create_df(d):
    df = pd.DataFrame(d)
    pd.set_option('display.max_columns', None)
    return df

def print_as_df(d):
    df = create_df(d)
    print(df)

def convert_to_json(df):
    #with open('data.json', 'wb') as outfile:
    #   str_ = json.dumps(d, ensure_ascii=False)
    #  outfile.write(str_.encode('utf-8').strip())
    df = create_df(d)
    with open('temp.json', 'w', encoding='utf-8') as f:
        #f.write(df.to_json(orient='records', lines=True, force_ascii=False))
        f.write(df.to_json(orient='index',force_ascii=False))
    
#print_as_df(d)
get_info()

with open('temp.json', encoding='utf-8') as data_file:
    data = json.loads(data_file.read())


app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/', methods=['GET'])
def home():
    return '''<h1>Distant Reading Archive</h1>
<p>A prototype API for distant reading of science fiction novels.</p>'''

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()



@app.route('/api/v1/campaigns/all', methods=['GET'])
def api_all():
    return jsonify(data)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

#app.run()
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
