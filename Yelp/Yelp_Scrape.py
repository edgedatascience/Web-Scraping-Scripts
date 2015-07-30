# -*- coding: utf-8 -*-

######################################################
#
# Created by Mike Donnalley - 07/30/2015
#
# This is a webs-scraping script that utilizes
# Beautiful Soup to scrape data from Yelp and place
# it neatly into a CSV file.
#
# You have the ability to import the links to scrape
# or crawl through Yelp to collect the links you would
# like to scrape.
#
# To avoid being caught as a robot, there are timers
# placed through out the script to put it to sleep
# for a specific amount of time. You may set these
# timers in the INPUTS section below. If you plan on
# scraping a significant number of pages, set the timers
# so that it takes several hours to run.
#
######################################################

from bs4 import BeautifulSoup
import urllib2
import csv
from pyparsing import makeHTMLTags, withAttribute
import os
import time
from random import randint


def prepare_brand_name(name):
    return name.replace(' ', '+')


# Import list of cities from a txt file. Must be formatted like this:
# arlington,va
# sanfrancisco,ca
# denver,co
# etc...
def import_cities():
    file_path = os.path.join(cities_input_path, cities_input_file)
    with open(file_path) as f:
        input_file = f.read().splitlines()
    return input_file


# Use urllib2 and Beautiful Soup 4 to open, read, and parse html from link
def link_opener(url):
    r = urllib2.urlopen(url).read()
    soup = BeautifulSoup(r, 'html.parser')
    return soup


# This function searches for the specified city and brand and then collects all the links of the search results
# it also removes any links that are not relevant to the brand that you specified or have already been collected.
def create_links(list_of_cities, brand):
    master = []
    brand_name = prepare_brand_name(brand)
    for city in range(len(list_of_cities)):
        time_between_city_search = randint(between_city_search_lower_bound, between_city_search_upper_bound)
        print ""
        print "--- " + list_of_cities[city].upper() + " ---"
        prefix = 'http://www.yelp.com/search?find_desc=' + brand_name + '&find_loc=' + list_of_cities[
            city] + '&ns=1&start='
        # results_count specifies how many search results pages you will crawl through. This is set to 5 pages of 10
        # search results, hence 50.
        results_count = ['0', '10', '20', '30', '40', '50']
        links = []
        cleaned_links = []
        for i in results_count:
            time_between_href_scrapes = randint(between_href_scrape_lower_bound, between_href_scrape_upper_bound)
            search_link = prefix + i
            print search_link
            soup = link_opener(search_link)
            search_results = soup.find_all("span", class_="indexed-biz-name")
            for j in search_results:
                links.append(j.a["href"])
            if not search_results:
                break
            time.sleep(time_between_href_scrapes)
        for k in links:
            if "/biz/" + brand.replace('+', '-') in k:
                cleaned_links.append(k)
                print k, "---> GOOD"
            else:
                print k, "---> CLEANED"
        print ""
        print "De-Duping"
        for clean_link in cleaned_links:
            if clean_link not in master:
                master.append(clean_link)
                print clean_link, "---> ADDED"
            else:
                print clean_link, "---> REMOVED"
        time.sleep(time_between_city_search)
    print ""
    print "--- FINAL LIST ---"
    for generated_link in master:
        print generated_link
    print ""
    print "Links generated and cleaned"
    print ""
    return master


# This function will output the links that you collected into a text file so that you can load these links later
# if you want to scrape data again. Note: the links outputted are in this format: /biz/chipotle-mexican-grill-boulder
def from_list_to_text(output):
    try:
        file_path = os.path.join(links_output_path, links_output_file)
        f = open(file_path, 'w')
        for item in output:
            f.write(item + '\n')
        f.close()
    except IOError as (error_number, strerror):
        print("I/O error({0}): {1}".format(error_number, strerror))

    return


# This function will import links in this format, /biz/chipotle-mexican-grill-boulder, for you to scrape data from
def import_links():
    file_path = os.path.join(links_input_path, links_input_file)
    with open(file_path) as f:
        imported_links_output = f.read().splitlines()
    return imported_links_output


# This function scrapes the following data points from each Yelp page, Street Address, Locality, State, Zip Code,
# Phone Number, Rating, Review. It then outputs all that data to a list that will be pushed to a CSV
def data_scrape(master_list_of_links):
    prefix = 'http://wwww.yelp.com'
    big_list = []
    for i in range(len(master_list_of_links)):
        time_between_big_links = randint(between_big_links_lower_bound, between_big_links_upper_bound)
        big_link = prefix + master_list_of_links[i]
        print big_link
        print "Scrape initiated"
        soup = link_opener(big_link)
        street = soup.find_all("span", itemprop="streetAddress")
        locality = soup.find_all("span", itemprop="addressLocality")
        state = soup.find_all("span", itemprop="addressRegion")
        zip_code = soup.find_all("span", itemprop="postalCode")
        phone = soup.find_all("span", class_="biz-phone")
        suffix = '?start='
        # review_count specifies how many search pages of reviews you will crawl through. This is set to go through at
        # most 320 reviews
        review_count = ['0', '40', '80', '120', '160', '200', '240', '280', '320']
        for j in review_count:
            time_between_review_pages = randint(between_review_pages_lower_bound, between_review_pages_upper_bound)
            print "processing..."
            new_link = big_link + suffix + j
            soup = link_opener(new_link)
            review_content = soup.find_all("div", class_="review-content")
            if not review_content:
                break
            meta_date = makeHTMLTags('meta')[0]
            meta_date.setParseAction(withAttribute(itemprop="datePublished"))
            meta_rating = makeHTMLTags('meta')[0]
            meta_rating.setParseAction(withAttribute(itemprop="ratingValue"))
            for k in review_content:
                indiv_list = [big_link]
                if not street:
                    indiv_list.append("Missing")
                else:
                    indiv_list.append(street[0].text)
                if not locality:
                    indiv_list.append("Missing")
                else:
                    indiv_list.append(locality[0].text)
                if not state:
                    indiv_list.append("DC")
                else:
                    indiv_list.append(state[0].text)
                if not zip_code:
                    indiv_list.append("Missing")
                else:
                    indiv_list.append(zip_code[0].text)
                if not phone:
                    indiv_list.append("Missing")
                else:
                    indiv_list.append(phone[0].text.strip())
                date = next(meta_date.scanString(k))[0]
                indiv_list.append(date.content)
                stars = next(meta_rating.scanString(k))[0]
                indiv_list.append(stars.content)
                indiv_list.append(k.p.text.encode("utf-8"))
                big_list.append(indiv_list)
                del indiv_list[:]
            time.sleep(time_between_review_pages)
        print "Scrape complete!"
        time.sleep(time_between_big_links)
        print ""
    return big_list


# This function takes the list we created in data_scrape and puts it into a nicely formatted CSV file
def from_list_to_csv(data_output):
    headings = ['URL', 'Street', 'Locality', 'State', 'Zip Code', 'Phone', 'Date', 'Rating', 'Review']
    try:
        file_path = os.path.join(output_path, output_file)
        with open(file_path, 'wb') as myCSVFile:
            csv_writer = csv.writer(myCSVFile, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writerow(headings)
            for data in data_output:
                csv_writer.writerow(data)
    except IOError as (error_number, strerror):
        print("I/O error({0}): {1}".format(error_number, strerror))

    return


# Note: link should always look like this:
# 'http://www.yelp.com/search?find_desc=[BRAND]+[NAME]&find_loc=[CITY],[STATE]&ns=1&start=[PAGE NUMBER]'

# OPTIONS ###########################

# use 'y' to select option, use 'n' to deselect option

# Import Cities from TXT?
import_cities_YN = 'y'

# Create Links?
create_links_YN = 'y'

# Export Links to TXT?
export_list_YN = 'y'

# Import Links from TXT?
import_list_YN = 'n'

# Scrape Data?
data_scrape_YN = 'y'

#######################################

# INPUTS ############################

# BRAND
brand = 'chipotle'

# IMPORT CITIES
# Refer to example link at top to see how city should be formatted in the txt file
cities_input_path = 'C:\Users\donnalley\Documents\GitHub\Web Scraping Scripts'
cities_input_file = 'Import_Cities.txt'

# OUTPUT FOR SCRAPE CSV
# Include .csv at end
output_path = 'C:\Users\donnalley\Documents\GitHub\Web Scraping Scripts'
output_file = brand.replace(' ', '_') + '_Yelp_Scrape.csv'

# OUTPUT FOR LINKS LIST
# Include .txt at end
links_output_path = 'C:\Users\donnalley\Documents\GitHub\Web Scraping Scripts'
links_output_file = brand.replace(' ', '_') + '_Yelp_Links.txt'

# IMPORT LIST
links_input_path = 'C:\Users\donnalley\Documents\GitHub\Web Scraping Scripts'
links_input_file = brand.replace(' ', '_') + '_Yelp_Links.txt'

# SLEEP TIMERS
# between_city_search
between_city_search_lower_bound = 5
between_city_search_upper_bound = 10
# between_href_scrapes
between_href_scrape_lower_bound = 20
between_href_scrape_upper_bound = 45
# between_crawl_and_scrape
between_crawl_and_scrape = 0
# between_review_pages
between_review_pages_lower_bound = 10
between_review_pages_upper_bound = 30
# between_big_links
between_big_links_lower_bound = 30
between_big_links_upper_bound = 60

#######################################

print ""
if import_cities_YN == 'y':
    city_list = import_cities()
    print "--- CITY LIST ---"
    print ""
    for element in city_list:
        print element
    print ""
else:
    city_list = []

if create_links_YN == 'y':
    master_list = create_links(city_list, brand)
else:
    master_list = []

if export_list_YN == 'y':
    from_list_to_text(master_list)

if between_crawl_and_scrape > 0:
    print ""
    print "Sleeping for %d seconds" % between_crawl_and_scrape
    time.sleep(between_crawl_and_scrape)

if import_list_YN == 'y':
    master_list = import_links()
    print ""
    print "--- BIG LINKS ---"
    for link in master_list:
        print link
    print ""

if data_scrape_YN == 'y':
    print "Beginning " + brand.upper() + " scrape..."
    print ""
    output_list = data_scrape(master_list)
    from_list_to_csv(output_list)
    print brand.upper() + " scrape completed!"
    print ""
