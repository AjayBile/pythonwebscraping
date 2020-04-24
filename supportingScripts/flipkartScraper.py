from bs4 import BeautifulSoup
import requests
import pymongo


class FlipkartScraper():

    def __init__(self, product_category, configDictInAction):
        self.product_category = product_category
        self.configDictInAction = configDictInAction

    def scrapeTheScreen(self, html_page):

        try:
            bigboxes = html_page.findAll("div", {"class": "bhgxx2 col-12-12"})

            temp = html_page.findAll("div", {"class": "_3liAhj"})

            del bigboxes[0:3]

            for product in bigboxes:
                self.processTheProduct(product)
                print("Product Reviews Successfully Scrape, now will go for next product on same page")
                break
        except Exception as e:
            print("Exception Occurred Inside scrapeTheScreen")
            print(str(e))

    def processTheProduct(self, singleProduct):
        mydict = {}
        try:

            print("BOT will process the product here")

            productLink = self.configDictInAction['product']['flipkart_url'] + singleProduct.div.div.div.a['href']
            print("From here BOT will redirect to the review page")
            print(productLink)

            product_name_for_db: str = productLink.split("/")[3]

            print("Name of a product is " + product_name_for_db)
            prodRes = requests.get(productLink)
            prod_html = BeautifulSoup(prodRes.content, 'html.parser')

            print("Page has been successfully scraped")

            sagle_reviews = prod_html.findAll('div', {'class': "swINJg _3nrCtb"})

            if len(sagle_reviews) > 0:
                print("BOT has found multiple reviews, so now lets scrape each page one by one")
                """it means reviews are more"""
                print(sagle_reviews[0].get_text())
                all_reviews_url = self.configDictInAction['product']['flipkart_url'] + str(sagle_reviews[0].find_parent().get('href'))
                print(all_reviews_url)

                print("Now BOT will push all reviews in DB for all the pages of this particular Product")

                self.push_all_reviews(all_reviews_url + "&page=1", product_name_for_db)

            commentboxes = prod_html.findAll('div', {'class': "_3nrCtb"})
            print(len(commentboxes))
            for comment in commentboxes:
                try:
                    name = comment.div.div.findAll('p', {'class': '_3LYOAd _3sxSiS'})[0].text
                except:
                    name = "No Name"
                # print(name)

                try:
                    rating = comment.div.div.div.div.text
                except:
                    rating = "No Rating"
                # print(rating)

                try:
                    commentHead = comment.div.div.div.p.text
                except:
                    commentHead = "No Heading"
                # print(commentHead)

                try:
                    comtag = comment.div.div.find_all('div', {'class': ''})
                    custComment = comtag[0].div.text
                except:
                    custComment = "No Comments"
                # print(custComment)

                mydict = {"Category": self.product_category, "Product": product_name_for_db, "Name": name, "Rating": rating,
                          "CommentHead": commentHead,
                          "Comment": custComment}

                # print(mydict)

                self.insertInMongo(mydict)

        except Exception as e:
            print("Exception Occurred Inside processTheProduct")
            print(str(e))

        return mydict

    def test(self, latest_html):
        data_url = None
        try:

            for_next = latest_html.findAll("div", {"class": "bhgxx2 col-12-12"})

            for i in for_next:
                try:
                    found = i.div.findAll("div", {"class": "_2zg3yZ"})
                    ahead = found[0].nav.findAll("a", {"class": "_3fVaIS"})
                    if len(ahead) < 2:
                        data_url = ahead[0].get('href')
                    else:
                        data_url = ahead[1].get('href')

                except:
                    pass
        except Exception as e:
            print("Exception Occurred Inside test")
            print(str(e))

        return data_url

    def repeatTillLastPage(self):

        try:
            print("START")
            url_to_append = "/search?q="+str(self.product_category).lower()+"&page=1"
            page_counter = 0
            while (page_counter <= 1):
                # we will scrape only first 20 pages
                # in order to scrape all the pages will use this condition - url_to_append != None

                flipkart_url = self.configDictInAction['product']['flipkart_url'] + str(url_to_append)
                req_data = requests.get(flipkart_url)
                flipkart_html = BeautifulSoup(req_data.content, 'html.parser')

                print("Now BOT will scrape the screen for " + flipkart_url)

                self.scrapeTheScreen(flipkart_html)
                url_to_append: str = self.test(flipkart_html)
                page_counter = page_counter + 1
                print(url_to_append)
        except Exception as e:
            print("Exception Occurred Inside repeatTillLastPage")
            print(str(e))

        print("END")

    def insertInMongo(self, mongoDict):

        conn = pymongo.MongoClient(self.configDictInAction['databse']['prod_db_url'])
        db = conn[self.configDictInAction['databse']['prod_db_name']]
        coll = db[str(self.product_category).lower()]
        x = coll.insert_one(mongoDict)
        print("Documet insertion id "+str(x.inserted_id))

    def test_part_2(self, all_reviews_html):
        all_reviews_next_page_url = None
        try:

            all_reviews_next = all_reviews_html.findAll("div", {"class": "_3gijNv col-12-12"})

            for i in all_reviews_next:
                try:
                    founder = i.div.findAll("div", {"class": "_2zg3yZ _3KSYCY"})
                    aheader = founder[0].nav.findAll("a", {"class": "_3fVaIS"})
                    if len(aheader) < 2:
                        all_reviews_next_page_url = aheader[0].get('href')
                    else:
                        all_reviews_next_page_url = aheader[1].get('href')

                except:
                    pass

        except Exception as e:
            print("Exception Occurred Inside test_part_2")
            print(str(e))

        return self.configDictInAction['product']['flipkart_url'] + str(all_reviews_next_page_url)

    def push_all_reviews(self, all_reviews_url, product_name_to_append):

        try:
            print("push  " + all_reviews_url)
            all_reviews_pages = 0
            while (all_reviews_pages < 2):
                # on all reviews page we are scraping only first 3 pages

                # all_reviews_url != None
                all_reviews_raw_page = requests.get(all_reviews_url)
                all_reviews_url_html = BeautifulSoup(all_reviews_raw_page.content, 'html.parser')
                self.scrapeReviewsPerPage(all_reviews_url_html, product_name_to_append)

                all_reviews_url = self.test_part_2(all_reviews_url_html)
                print(all_reviews_url)
                all_reviews_pages += 1

        except Exception as e:
            print("Exception Occurred Inside push_all_reviews")
            print(str(e))

    def scrapeReviewsPerPage(self, data_html_for_page, name_of_product):

        try:
            print("Scraping the page ")

            reviews = data_html_for_page.find_all('div', {'class': '_3gijNv col-12-12'})

            del reviews[0:4]

            for rev in reviews:
                try:
                    commentHead = rev.div.div.div.div.p.text
                except:
                    commentHead = "No Heading"

                try:
                    rating = rev.div.div.div.div.div.text
                except:
                    rating = "No Rating"

                try:
                    comtag = rev.find_all('div', {'class': ''})
                    custComment = comtag[0].div.text
                except:
                    custComment = "No Comments"

                try:
                    name = rev.div.div.findAll('p', {'class': '_3LYOAd _3sxSiS'})[0].text
                except:
                    name = "No Name"

                mydict = {"Category": self.product_category, "Product": name_of_product, "Name": name, "Rating": rating,
                          "CommentHead": commentHead,
                          "Comment": custComment}

                # print(mydict)

                self.insertInMongo(mydict)
        except Exception as e:
            print("Exception Occurred Inside scrapeReviewsPerPage")
            print(str(e))
