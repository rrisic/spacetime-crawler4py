import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


SUBDOMAIN_PAGE_COUNT = {}
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

    url_list = []
    if resp.status != 200: # Error on page, skip page
        error = resp.error
        print(error)
        return list()
    
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    links = [tag['href'] for tag in soup.find_all('a', href=True)]
    for link in links:
        if is_valid(link):
            try:  
                # filter out queries
                idx = link.index('?')
                url_list.append(link[0:idx])
            except ValueError:
                # no query found, filter out frags
                frag = urlparse(link).fragment
                if (not frag):
                    url_list.append(link)
                else:
                    url_list.append(link[0:link.rfind('#')])    
    return url_list

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        # Check for calender traps with regex pattern 4 digits - 2 digits - 2 digits
        if bool(re.search(r'\d{4}-\d{2}-\d{2}', url)):
            return False
        
        # subdomain counting
        try:
            SUBDOMAIN_PAGE_COUNT[parsed.hostname] += 1
        except KeyError:
            SUBDOMAIN_PAGE_COUNT[parsed.hostname] = 1

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
