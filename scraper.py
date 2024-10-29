import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

with open('./stopwords.txt', 'r') as stopwords:
    STOPWORDS = {word.strip() for word in stopwords.readlines()}
    STOPWORDS.remove("")
        
def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def tokenize(file):
    alnum_set = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
    cur_word = ""
    i = 0
    try:
        while True:
            x = file[i]
            if (x in alnum_set):
                cur_word += x
            else:
                if (len(cur_word) > 3 and not (cur_word in STOPWORDS)): # Prevent empty strings
                    yield cur_word.lower() # Need all capitalization removed
                if (x == ''): # Must do this AFTER adding the word in cur_word
                    break
                cur_word = ""
            i += 1
    except IndexError:
        pass


SUBDOMAIN_PAGE_COUNT = {}
SEEN_PAGES = set()

def jaccard_similarity(tokens1, tokens2):
    # Formula from class to detect similarity
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return intersection / union if union != 0 else 0

def is_similar(content_tokens, threshold):
    for seen_tokens in SEEN_PAGES:
        if jaccard_similarity(set(content_tokens), set(seen_tokens)) > threshold:
            return True
    SEEN_PAGES.add(content_tokens)
    with open('./Logs/extracted_tokens.txt', 'a') as token_store:
        for word in content_tokens:
            token_store.write(word + ' ')
        token_store.write('\n')
        token_store.flush()
    return False

def extract_next_links(url, resp):
    global MAX_PAGE
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    MAX_PAGE = [0, '']

    WORD_MIN = 30 # Fewer than this many words is likely not an important site
    THRESHOLD = 0.8
    url_list = []
    if resp.status != 200: # Error on page, skip page
        error = resp.error
        print(error)
        return list()
    if (not resp.raw_response.content):
        return list()
    
    soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
    text = soup.get_text()
    content_tokens = tuple(tokenize(text))
    content_len = len(content_tokens)

    if (content_len > MAX_PAGE[0]):
        MAX_PAGE[0] = content_len
        MAX_PAGE[1] = url
        with open('./Logs/longest_page.txt', 'w') as page_txt:
            page_txt.write(str(MAX_PAGE[0]) + '\n')
            page_txt.write(MAX_PAGE[1])
    
                           
    
    if content_len <= WORD_MIN or is_similar(content_tokens, THRESHOLD): # don't take its links if it's not a "useful" site or a duplicate
        return list()
    
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

            
    return url_list

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    global SUBDOMAIN_PAGE_COUNT
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        # Check for calender traps with regex pattern 4 digits - 2 digits - 2 digits
        if bool(re.search(r'\d{4}-\d{2}', url)):
            return False
        
        # subdomain parsing and counting
        hname_parts = parsed.hostname.split('.')
        if len(hname_parts) > 2:
            domain = '.'.join(hname_parts[-3:])
            if domain != 'ics.uci.edu' and domain != 'cs.uci.edu' and domain != 'informations.uci.edu' and domain != 'stat.uci.edu':
                if domain == 'today.uci.edu':
                    if 'today.uci.edu/department/information_computer_sciences' in url:
                        return False
                else:
                    return False
            hname = '.'.join(hname_parts[:-2])  # Join all parts except the last two (domain and TLD)
        else:
            return False
        try:
            SUBDOMAIN_PAGE_COUNT[hname] += 1
        except KeyError:
            SUBDOMAIN_PAGE_COUNT[hname] = 1

        with open('./Logs/subdomain_page_count.txt', 'w') as subpage_txt:
            for key in SUBDOMAIN_PAGE_COUNT:
                subpage_txt.write(f'{key}, {SUBDOMAIN_PAGE_COUNT[key]}')

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
    except:
        return False
