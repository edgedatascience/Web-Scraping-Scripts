# -*- coding: utf-8 -*-
import urllib2
import csv
import os

from bs4 import BeautifulSoup


def from_list_to_csv(output_list, output_file_path, output_file, header_type):
    if header_type == 'threads':
        print ""
        print "--- EXPORTING THREADS TO CSV ---"
        headings = ['Source', 'Thread Title', 'Post Date', 'Post Time', 'Post']
    elif header_type == 'upvotes':
        print ""
        print "--- EXPORTING UPVOTES TO CSV ---"
        headings = ['Source', 'Post Date', 'Post Time', 'Title', 'Upvotes', 'Post Count']
    else:
        raise NameError('Invalid header_type')
    try:
        file_path = os.path.join(output_file_path, output_file)
        # use 'ab' to append data; use 'wb' to write from scratch
        with open(file_path, 'wb') as myCSVFile:
            csv_writer = csv.writer(myCSVFile, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writerow(headings)
            for data in output_list:
                csv_writer.writerow(data)
    except IOError as (error_number, strerror):
        print("I/O error({0}): {1}".format(error_number, strerror))
    return


def get_homepage(source_name, option):
    if option == 'most recent':
        first_page = 'http://www.reddit.com/' + source_name
        return first_page
    elif option == 'all time':
        first_page = 'http://www.reddit.com/' + source_name + '/top/?sort=top&t=all'
        return first_page
    else:
        raise NameError('Invalid argument: must be most recent or all time')


def scrape_select(source_name, list_of_page_links, option, output_file_path, upvotes_output_file_name,
                  threads_output_file_name):
    if option == 'threads':
        scrape_threads(list_of_page_links, source_name, output_file_path, threads_output_file_name)
    elif option == 'upvotes':
        scrape_upvotes(list_of_page_links, source_name, output_file_path, upvotes_output_file_name)
    elif option == 'both':
        scrape_upvotes(list_of_page_links, source_name, output_file_path, upvotes_output_file_name)
        scrape_threads(list_of_page_links, source_name, output_file_path, threads_output_file_name)
    else:
        raise NameError('Invalid argument: must be threads, upvotes, or both')
    return


def get_pages(first_page, number_of_pages):
    if number_of_pages >= 40:
        raise NameError("Your specification for number of pages is too large. Must be 39 or less.")
    print "--- COLLECTING PAGE LINKS ---"
    print ""
    list_of_page_links = []
    print first_page
    list_of_page_links.append(first_page)
    counter = 0
    for i in range(0, number_of_pages):
        # Retry until it works
        while True:
            try:
                opener = urllib2.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                r = opener.open(list_of_page_links[counter])
                soup = BeautifulSoup(r)
                next_link = soup.find('a', rel='nofollow next')
                if not next_link:
                    break
                list_of_page_links.append(next_link['href'])
                print next_link['href']
                counter += 1
            except urllib2.HTTPError:
                continue
            break
    print ""
    print "--- PAGE LINKS COLLECTED ---"
    print ""
    return list_of_page_links


def get_thread_links(list_of_page_links):
    thread_links = []
    for page in list_of_page_links:
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        r = opener.open(page)
        soup = BeautifulSoup(r)
        thread_titles = soup.find_all('p', class_='title')
        for thread in thread_titles:
            thread_links.append(thread.a['href'])
    return thread_links


def scrape_threads(list_of_page_links, source_name, output_file_path, threads_output_file_name):
    print ""
    print "--- SCRAPING THREADS ---"
    thread_links = get_thread_links(list_of_page_links)
    big_list = []
    for thread in thread_links:
        prefix = 'https://www.reddit.com'
        link = prefix + thread
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        while True:
            try:
                r = opener.open(link)
            except urllib2.HTTPError:
                continue
            break
        soup = BeautifulSoup(r)
        thread_title = soup.find('a', class_='title may-blank ').text.encode('ascii', errors='ignore')
        print thread_title
        reply_containers = soup.find_all('div', class_='entry unvoted')
        for reply in reply_containers:
            indiv_list = [source_name, thread_title]
            date_time = reply.find('time')
            if not date_time:
                indiv_list.append('')
                indiv_list.append('')
            else:
                try:
                    date_time = date_time['title']
                    year = date_time[-8:-4]
                    post_date = date_time[4:-18] + ' ' + year
                    indiv_list.append(post_date)
                    post_time = date_time[-16:-9]
                    indiv_list.append(post_time)
                except TypeError:
                    indiv_list.append('')
                    indiv_list.append('')
            post_container = reply.find('div', class_='md')
            if post_container is not None:
                post_container = post_container.find_all('p')
                post = ''
                for p in post_container:
                    post += p.text.encode('ascii', errors='ignore')
                indiv_list.append(post)
            elif post_container is None:
                indiv_list.append('')
            big_list.append(indiv_list)
            del indiv_list[:]
    from_list_to_csv(big_list, output_file_path, threads_output_file_name, 'threads')
    return


def scrape_upvotes(list_of_page_links, source_name, output_file_path, upvotes_output_file_name):
    print "--- SCRAPING UPVOTES ---"
    big_list = []
    count = 0
    for page in list_of_page_links:
        print "Page", count + 1
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        r = opener.open(page)
        soup = BeautifulSoup(r)
        thread_links = []
        thread_titles = soup.find_all('p', class_='title')
        for thread in thread_titles:
            thread_links.append(thread.a['href'])
        identifiers = []
        for thread in thread_links:
            thread = thread.replace('/' + source_name + '/comments/', '')
            identifier = 't3_' + thread[:6]
            identifiers.append(identifier)
        for identifier in identifiers:
            indiv_list = []
            title_container = soup.find(attrs={'data-fullname': identifier})
            if title_container is not None:
                indiv_list.append(source_name)
                date_time = title_container.find('time')
                if not date_time:
                    indiv_list.append('')
                    indiv_list.append('')
                else:
                    date_time = date_time['title']
                    year = date_time[-8:-4]
                    post_date = date_time[4:-18] + ' ' + year
                    indiv_list.append(post_date)
                    post_time = date_time[-16:-9]
                    indiv_list.append(post_time)
                    title = title_container.find('a', class_='title may-blank ').text.encode('ascii', errors='ignore')
                    indiv_list.append(title)
                upvotes = title_container.find('div', class_='score unvoted').text.encode('ascii', errors='ignore')
                if upvotes == '':
                    upvotes = upvotes.replace('', '0')
                indiv_list.append(upvotes)
                post_count = title_container.find('li', class_='first').a.text.replace(' comments', '')
                if post_count == 'comment':
                    indiv_list.append('0')
                elif post_count == '1 comment':
                    indiv_list.append(post_count.replace(' comment', ''))
                else:
                    indiv_list.append(post_count)
                big_list.append(indiv_list)
            else:
                continue
        count += 1
    print ""
    from_list_to_csv(big_list, output_file_path, upvotes_output_file_name, 'upvotes')
    return


print ""
print "--- SCRAPE INITIATED ---"
print ""

# case sensitive (actually, not any more...)
source = 'r/smallbusiness'

# 'most recent' or 'all time'
home_page = get_homepage(source, 'most recent')

# number of pages must be <= 39
page_links = get_pages(home_page, 39)

output_path = 'C:\Users\donnalley\Desktop'
upvotes_output_file = 'Reddit_SmallBiz_Upvotes_MostRecent_0806.csv'
threads_output_file = 'Reddit_SmallBiz_Posts_MostRecent_00806.csv'

# threads, upvotes, or both
scrape_object = 'threads'
scrape_select(source, page_links, scrape_object, output_path, upvotes_output_file, threads_output_file)

print ""
print "--- SCRAPE COMPLETE ---"
print ""
