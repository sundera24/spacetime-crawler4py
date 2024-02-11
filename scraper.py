import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup

visited_urls = set()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

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
    try:
        if 399>=resp.status>=200: # redirects are code 301, 302; decide whether to limit to 300>=status
            parse_url = urlparse(url)
            bs = BeautifulSoup(resp.raw_response.content,'html.parser')
            for new_url in bs.find_all('a'):
                try:
                    processed = urldefrag(urljoin(parse_url.scheme+"://"+parse_url.netloc,new_url['href']))[0]
                    if '?' in processed:
                        processed = processed.split("?")[0]
                    # Do we need to filter queries??
                    if processed not in visited_urls:
                        visited_urls.add(processed)
                        links.append(processed)
                except KeyError:
                    print(f'Status Code: {resp.status}')
    except AttributeError:
        print(f'Status Code: {resp.status}\nError: {resp.error}')
    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        if not re.match(
                r".*\.(ics\.uci\.edu"
                + r"|cs\.uci\.edu"
                + r"|informatics\.uci\.edu"
                + r"|stat\.uci\.edu)", parsed.netloc.lower()):
            return False
        
        # Potentially temporarily filter out swiki just to examine the rest of the functionality

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|apk|db|java"
            + r"|thmx|mso|arff|rtf|jar|csv|sql|war"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())
            # Added db, apk, ppsx (powerpoint variant), sql, war, java

    except TypeError:
        print ("TypeError for ", parsed)
        raise