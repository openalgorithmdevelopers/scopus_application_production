# -*- coding: utf-8 -*-
"""
Created on Thu Oct 21 12:12:26 2021

@author: bhupendra.singh
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import time  #replace with selenium wait

from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
from tqdm.notebook import tqdm
from datetime import datetime


from flask import Flask, send_file, render_template, url_for, request, flash
app = Flask(__name__)

@app.route('/', methods =["GET", "POST"])
def home():
    userInfo = list()
  #return "Hello World! yes"
    if request.method == "POST":
       # getting input with name = fname in HTML form
       userIP = request.remote_addr
       timeString = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
       
       print("User address = " + str(userIP))
       print("time string = " + timeString)
       userInfo.append(str(userIP) + "," + timeString)
       #userInfo.append(timeString)
       df = pd.DataFrame(userInfo)
       df.to_csv("usage_report.csv", mode="a", index=False)
       
       author_id = request.form.get("MERGE1")
       startDate = request.form.get("startDate")
       endDate = request.form.get("endDate")

       csvDF, message = getData(int(author_id), startDate, endDate)
       if(message == -1):
           print("reached here")
           flash("the provided author id = " + str(author_id) + " is incorrect.")
       #send_file("usage_report.csv"a, ttachment_filename= str(author_id) + "_scopus_publications.csv")
       return send_file("final_report.csv", as_attachment=True, attachment_filename= str(author_id) + "_scopus_publications.csv")
       #return render_template("index.html")
    return render_template("index.html")

def getData(authorId, startDate, endDate):
    
    #os.chdir('C:/Users/bhupendra.singh/Documents/GitHub/scopus_data_web_application')
    #authorId = 57188978923
    #authorId = 57210953023  #bhupendra singh
    #authorId = 57221459727 #D K Awasthi
    url = "https://www.scopus.com/authid/detail.uri?authorId=" + str(authorId)
    
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(ChromeDriverManager().install() , options=options)
    
    print("reached before try")
    try:
        print("reached try")
        driver.get(url)
        print("try successful")
        message = 1
    except ValueError:
        message = -1
    
    driver.refresh()
    time.sleep(15)
    print("title of the page = " + driver.title)
    
    
    dataRows = []
    singleRow = []
    
    articles = driver.find_elements(By.XPATH,  '//els-paginator[@totalamount]') 
    a = articles[0].text
    b = a.split()
    c = b.index('Next')
    numberOfNext = b[c-1]
    numberOfNext = int(numberOfNext)
    if(numberOfNext > 80):
        numberOfNext = 80
    
    #for currentPage in range(numberOfNext):       #provide here the number of next clicks avaiable
    for currentPage in tqdm(range(numberOfNext)):       #provide here the number of next clicks avaiable
        currentPage = currentPage + 1
        #print("current page = " + str(currentPage))
        articleAndJournalNameWebElementList = driver.find_elements(By.XPATH, '//a[@title="Show document details"]') #Article and journal name
        articleTypeWebElementList = driver.find_elements(By.XPATH,  '//div[@data-component="document-type"]') #article or + open, conference paper
        
        articleInformationWebElementList = driver.find_elements(By.XPATH,  '//span[@class="text-meta"]') #year, vol, issue, page nos, article no/
        citationsCountWebElementList = driver.find_elements(By.XPATH,  '//div[@class="sc-els-info-field"]') #Citations count
        
        #players = driver.find_elements(By.XPATH,  '//div[@data-component="document-authors"]') #article or + open, conference paper
        authorsWebElementList = driver.find_elements(By.XPATH,  '//div[@class="author-list"]') #Authors lists
        for i in range(len(articleTypeWebElementList)):
            singleRow = []
            articleType = articleTypeWebElementList[i].text
            articleType.replace("Open Access", "")
            singleRow.append(articleType)
            singleRow.append(articleAndJournalNameWebElementList[2*i].text)
            singleRow.append(articleAndJournalNameWebElementList[2*i + 1].text)
            
            #singleRow.append(articleInformationWebElementList[i].text)
            articleInformation = articleInformationWebElementList[i].text
            
            #separatedInfo = articleInformation.split()        #splits the information into year, vol, issue, page_nos
            # extract year, volume, issue, pages number
            yearInfo = articleInformation[0:4]
            if( len(articleInformation) > 4):
                volumeIssuePageNosInfo = articleInformation[5:len(articleInformation)]
            else:
                volumeIssuePageNosInfo = ""
            
            singleRow.append(yearInfo)
            singleRow.append(volumeIssuePageNosInfo)
            singleRow.append(citationsCountWebElementList[i].text)
            singleRow.append(authorsWebElementList[i].text)
            dataRows.append(singleRow)
            del singleRow
        #singleRow.clear()
        if numberOfNext > 1 and  currentPage < numberOfNext:
            a = driver.find_element_by_xpath("//span[contains(@class,'button__text sc-els-paginator') and contains(text(), 'Next')]").click()
            #print("reached")
            time.sleep(5)
    #     
    # =============================================================================
    df = pd.DataFrame(dataRows)
    df.columns=["Article Type", "Title", "Journal/Conference/Book chapter Name", "Year", "Vol/Issue/pages", "citations" , "Authors"]
    
    ########### apply the date range logic here ####################
    if(startDate == "" and endDate == ""):
        pass
    elif(startDate == ""):
        df = df[df["Year"] <= endDate]
    elif(endDate == ""):
        df = df[df["Year"] >= startDate] 
    else:
        df = df[df["Year"] <= endDate]
        df = df[df["Year"] >= startDate]
    
    ##################################################
    
    numberOfRecords = df.shape[0]
    indexColumn = list(range(1, numberOfRecords+1))
    df.insert(0, "SNo.", indexColumn)
    df.to_csv("final_report.csv", index = False)
    
    driver.quit()
    return df, message

if __name__ == "__main__":
  app.run()