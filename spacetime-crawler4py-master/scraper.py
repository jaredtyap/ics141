from simhash import Simhash
import re
from urllib.parse import urlparse, urldefrag
import urllib
from bs4 import BeautifulSoup
import operator

crawled = set() # set of urls already crawled
previous=['something to initialize'] #
longestPageLength=['', 0] #url and length of longest page
counter=0  

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    outputLinks=list()
    url=url.lower()
    words=[]

    #urls.txt will contain all
    with open('urls.txt', 'a', encoding='utf8') as file_links, \
         open('text.txt', 'a', encoding='utf8') as file_texts:

        if (resp.status in (200, 201, 202) and  #valid response status check
            crawledCheck(url) and #assert url not crawled previously
            is_valid(url)): #assert url is valid

            splitUrl = urlparse(url)

            web_html = resp.raw_response.content
            soup = BeautifulSoup(web_html, 'html.parser')
            webtext = soup.get_text()
            hamming_dist = Simhash(get_features(webtext)).distance(Simhash(get_features(previous)))
            if hamming_dist < 4:
                counter += 1
                if counter > 50:
                    counter = 0
                    
            else:
                previous.append(webtext)
            for word in webtext.split(' '):
                if word != '' and word.isalnum():
                    words.append(word)
            file_texts.write(url + "\n" + str(words) + "\n")
            
            if (longestPageLength[1] < len(words)):
                longestPageLength[0]=url
                longestPageLength[1]=len(words)

            for path in soup.find_all('a'):
                relative = path.get('href')
                link = urllib.parse.urljoin('https://'+splitUrl.netloc, relative)
                outputLinks.append(urldefrag(link)[0])
                file_links.write((urldefrag(link)[0]+"\n"))

    #file_links.write('Url with the longest page: {} has a word count of {}'.format(longestPageLength[0], longestPageLength[1]))
    file_links.close()
    file_texts.close()
    return outputLinks


def crawledCheck(url): #true if page has not been crawled yet
    if url[-1]=='/':
        url=url[:-1]
    if url in crawled:
        return False
    else:
        crawled.add(url)
        return True

def get_features(s):
    width = 10
    s = s.lower()
    s = re.sub(r'[^\w]+', '', s)
    return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]


def is_valid_domain(url):
    allowedDomains = ["ics.uci.edu",
                      "cs.uci.edu",
                      "stat.uci.edu",
                      "informatics.uci.edu"]

    netloc = url.netloc

    if netloc.startswith("www."):
        netloc = netloc.strip("www.")

    netlist = netloc.split(".")

    subdomain = ".".join(netlist)

    if len(netlist) >= 4:
        subdomain = ".".join(netlist[1:])

    if netloc == "today.uci.edu" and \
            "/department/information_computer_sciences" in url.path:
        return True

    if netloc == "evoke.ics.uci.edu" and '/?replytocom' in url.path:
        return False

    if netloc == "wics.ics.uci.edu" and  "/events" in url.path:
        return False

    if (netloc=="ngs.ics.uci.edu" and
            ('research' and 'teaching' and 'entrepreneur') not in url.path):
        return False

    if netloc == "archive.ics.uci.edu":
        return False

    if netloc == "hack.ics.uci.edu" and \
            "gallery" in url.path:
        return False

    if netloc == "grape.ics.uci.edu":
        return False

    if netloc == "intranet.ics.uci.edu":
        return False

    for domain in allowedDomains:
        if subdomain == domain:
            return True


def is_valid(url):
    try:
        parsed = urlparse(url)

        if not is_valid_domain(parsed):
            return False

        if parsed.scheme not in set(["http", "https"]):
            return False

        dontCrawl = ["css", "js", "bmp", "gif", "jpeg", "ico", "png", "tiff",
                     "mid", "mp2", "mp3", "mp4", "wav", "avi", "mov", "mpeg", "ram",
                     "m4v", "mkv", "ogg", "ogv", "pdf", "ps", "eps", "tex", "ppt",
                     "pptx", "doc", "docx", "xls", "xlsx|names", "data", "dat",
                     "exe", "bz2", "tar", "msi", "bin", "7z", "psd", "dmg", "iso",
                     "epub", "dll", "cnf", "tgz", "sha1", "thmx", "mso", "arff",
                     "rtf", "jar", "csv", "rm", "smil", "wmv", "swf", "wma", "zip",
                     "rar", "gz", "svg", "txt", "py", "rkt", "ss", "scm", "json",
                     "pdf", "wp-content", "calendar", "ical", "war", "img"]

        for n in dontCrawl:
            if (n) in parsed.query or (n) in parsed.path:
                return False

        return not re.match(
            r".*.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise