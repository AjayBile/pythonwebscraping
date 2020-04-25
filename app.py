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

            # Default mongoDB url is of Dev environment
            mongo_url = "mongodb://localhost:27017/"
            mongo_db_name = "testDB"
            is_prod = os.environ.get('IS_HEROKU', None)
            if is_prod:
                mongo_url: str = os.environ.get('MONGODB_URL', None)
                mongo_url = mongo_url+"?retryWrites=true&w=majority"
                mongo_db_name = "reviewsDB"

            # set the base url
            base_url = "https://www.flipkart.com"

            configdict = {}

            configdict['mongourl'] = mongo_url
            configdict['mongodbname'] = mongo_db_name
            configdict['baseurl'] = base_url

            print(configdict)

            dbConn = pymongo.MongoClient(mongo_url)  # opening a connection to Mongo
            db = dbConn[mongo_db_name]  # connecting to the database called crawlerDB
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
                flipkart = FlipkartScraper(searchString, configdict)
                flipkart.repeatTillLastPage()
            reviews = db[searchString].find({})

            return render_template('results.html', reviews=reviews)
        except:
            return 'something is wrong'
    else:
        return render_template('index.html')

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='127.0.0.1')



