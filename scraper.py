import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
import time
import nltk
import pickle
from collections import defaultdict
from nltk.corpus import stopwords

# Data structures for storing scraped information
visitedURLs = []
words_dict=defaultdict(int)
longest_url=('',0)
subdomains=defaultdict(int)
hashes=[]

nltk.download('stopwords')
stopwords = stopwords.words('english')

def scraper(url, resp):
    links = extract_next_links(url, resp)
    with open('output.pkl', 'wb') as file:  # export global variables with pickle
        pickle.dump([visitedURLs, words_dict, longest_url, subdomains], file)
    return [link for link in links if is_valid(link)]

def computeWordFrequencies(tokens) -> defaultdict:
    """Runtime complexity: O(n) average case where n is the length of tokens"""
    freq = defaultdict(int)
    for i in tokens:  # O(n) iterations, increment is O(1)
        freq[i] += 1  # increments frequency of the selected token by 1, starting at 0 as default
    return freq

def simhash(tokens):
    # Calculates simhash vectors for a given dictionary of tokens and frequncies
    hashed=[]
    for key,value in tokens.items():
        hashed.append(((hash(key)%65536),value))
    for i, num in enumerate(hashed):
        hashed[i] = ([1 if num[0] & (1 << (15 - n)) else 0 for n in range(16)],num[1])
    vector=[]
    index=0
    while index<16:
        temp=0
        for h in hashed:
            if h[0][index]==1:
                temp = temp+h[1]
            else:
                temp = temp+(-1*h[1])
        vector.append(0 if temp<=0 else 1)
        index+=1
    return vector

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    links = []
    if url in visitedURLs:
        return links
    try:
        if 399>=resp.status>=200: # filters out pages with error status codes
            if resp.status < 300:
                visitedURLs.append(url)
            parse_url = urlparse(url)
            if parse_url.netloc == urlparse(visitedURLs[-1]).netloc:
                time.sleep(0.5)
            if resp.status < 300: # filters and specifies domain information collected
                if "ics.uci.edu" in parse_url.netloc:
                    if "https://" + parse_url.netloc in subdomains.keys():
                        subdomains["https://" + parse_url.netloc] += 1
                    elif "http://" + parse_url.netloc in subdomains.keys():
                        subdomains["http://" + parse_url.netloc] += 1
                    else:
                        subdomains[parse_url.scheme + "://" + parse_url.netloc] += 1
            extract_content(url, resp)
            bs = BeautifulSoup(resp.raw_response.content,'html.parser')
            for new_url in bs.find_all('a'):
                try:
                    processed = urldefrag(urljoin(parse_url.scheme + "://" + parse_url.netloc, new_url['href']))[0]
                    if '?' in processed:
                        processed = processed.split("?")[0]
                    links.append(processed)
                except KeyError:
                    print(f'Status Code: {resp.status}\nError: No href')
    except AttributeError:
        print(f'Status Code: {resp.status}\nError: {resp.error}')
    return links

def extract_content(url, resp):
    bs = BeautifulSoup(resp.raw_response.content, 'html.parser')
    for data in bs(['style', 'script']):  # remove all html markup
        data.decompose()  # remove tags
    clean_text = (' '.join(bs.stripped_strings))
    tokens_list = tokenize(clean_text)
    filtered_tokens = [token for token in tokens_list if token not in stopwords]
    filtered_tokens = [token for token in filtered_tokens if len(token) > 2]
    if len(set(filtered_tokens)) > 10000: # threshold for a file to be considered too large
        return
    calc_hash=simhash(computeWordFrequencies(filtered_tokens))
    if calc_hash in hashes: # detects similarity to other files using simhash
        return
    else:
        hashes.append(calc_hash)
    global longest_url
    if len(filtered_tokens)>longest_url[1]:
        longest_url=(url, len(filtered_tokens))
    for token in filtered_tokens:
        words_dict[token]+=1



def tokenize(text) -> list:
    """Runtime complexity: O(n) where n is the number of characters in the file"""
    tokens=[]
    l = re.split('[^0-9A-Za-z]', text.lower()) # split line into a list of substrings using alphanumeric regex
    tokens.extend(l)
    return list(filter(None,tokens))  # remove the empty strings split from the line and cast from filter object to list


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if "pdf" in parsed.path or "zip" in parsed.path:
            return False
        if not re.match( # filters domains outside of the crawlable domains for this assignment
                r".*\.(ics\.uci\.edu"
                + r"|cs\.uci\.edu"
                + r"|informatics\.uci\.edu"
                + r"|stat\.uci\.edu)", parsed.netloc.lower()):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|apk|java|db|txt|ipynb"
            + r"|thmx|mso|arff|rtf|jar|csv|ppsx|sql|war"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|odc"
            + r"|sqlite|vmdk|vhd)$", parsed.path.lower())
        # Updated from starting point to filter even more irrelevant/problematic file types

    except TypeError:
        print ("TypeError for ", parsed)
        raise
