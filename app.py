from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import pymongo
from supportingScripts.flipkartScraper import FlipkartScraper
import os
import json

app =Flask(__name__)
@app.route('/',methods=['POST',"GET"])

def index():

    if request.method == 'POST':
        searchString:str = request.form['content'] # obtaining the search string entered in the form
        searchString = searchString.lower()
        tempSearchStr = searchString
        searchString = searchString.replace(" ","")

        print("User has search for following keyword "+searchString)

        try:

            # Reading the configuration file
            configdict:dict = readConfig()
            print(configdict['configData'])
            dictToUseByProcess = configdict['configData']

            dbConn = pymongo.MongoClient(dictToUseByProcess['databse']['prod_db_url'])  # opening a connection to Mongo
            db = dbConn[dictToUseByProcess['databse']['prod_db_name']]  # connecting to the database called crawlerDB
            reviews = db[searchString].find({})  # searching the collection with the name same as the keyword
            if reviews.count()<=0:
                print("Keyword Not Found in Category")
                query_string_for_search = tempSearchStr.replace(" ", ".*")
                productquery = {"Product": {"$regex": query_string_for_search, '$options' : 'i'}}
                print(productquery)
                for col in db.collection_names():
                    collect = db[col]
                    reviews = collect.find(productquery)
                    if reviews.count() > 0:
                        print("Previous Data Exist in collection "+str(col)+" with row count of "+str(reviews.count()))
                        break

            if reviews.count() > 0:  # if there is a collection with searched keyword and it has records in it
                return render_template('results.html', reviews=reviews)
            else:
                print("No previous data has present, hence scraping the data")
                flipkart = FlipkartScraper(searchString, dictToUseByProcess)
                flipkart.repeatTillLastPage()
            reviews = db[searchString].find({})

            return render_template('results.html', reviews=reviews)
        except:
            return 'something is wrong'
    else:
        return render_template('index.html')

def readConfig():
    configDict: dict = {}
    try:
        processConfigpath = os.path.dirname(__file__) + "/config.json"
        with open(processConfigpath, "r", encoding="utf-8") as jsonString:
            configDict['configData'] = json.load(jsonString)
    except Exception as e:
        print("Exception Occurred Inside readConfig")
        print(str(e))
    return configDict

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')



