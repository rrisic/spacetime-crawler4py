from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time

def print_final_info():
    global MAX_PAGE, SUBDOMAIN_PAGE_COUNT
    with open('./Logs/count.txt', 'r') as count_txt:
        count = int(count_txt.read())

    with open('./Logs/extracted_tokens.txt', 'r') as file_info:
        words_map = {}
        while True:
            line = file_info.readline()
            if (line == ''):
                break
            words = line.split(' ')
            for word in words:
                try:
                    words_map[word] += 1
                except KeyError:
                    words_map[word] = 1

    count = 0
    for key in sorted(words_map, key = lambda abc: (-words_map[abc], abc)):
        if (count == 50):
            break
        print(f'{count + 1}. Key: {key} has value {words_map[key]}')
        count += 1

    print(f'Max page link: {MAX_PAGE[1]} has length of {MAX_PAGE[0]}')

    print('\n\nSubdomain Page Counts: ')

    with open('./Logs/subdomain_page_count.txt') as subpage_txt:
            SUBDOMAIN_PAGE_COUNT = {}
            while True:
                new_line = subpage_txt.readline().split(', ')
                if (new_line == [""]):
                    break
                SUBDOMAIN_PAGE_COUNT[new_line[0]] = int(new_line[1])

    for key in sorted(SUBDOMAIN_PAGE_COUNT, key = lambda abc: (-SUBDOMAIN_PAGE_COUNT[abc], abc)):

        print(f'{key}, {SUBDOMAIN_PAGE_COUNT[key]}')

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        global COUNT, MAX_PAGE
        with open('./Logs/count.txt', 'r') as count_txt:
            try:
                COUNT = int(count_txt.read())
            except ValueError:
                COUNT = 0
        with open('./Logs/longest_page.txt') as page_txt:
            MAX_PAGE = [0, '']
            MAX_PAGE[0] = int(page_txt.readline())
            MAX_PAGE[1] = page_txt.readline()
        with open('./Logs/subdomain_page_count.txt') as subpage_txt:
            SUBDOMAIN_PAGE_COUNT = {}
            while True:
                new_line = subpage_txt.readline().split(', ')
                if (new_line == [""]):
                    break
                SUBDOMAIN_PAGE_COUNT[new_line[0]] = new_line[1]
        while True:
            tbd_url = self.frontier.get_tbd_url()
            with open('./Logs/count.txt', 'w') as count_txt_write:
                count_txt_write.write(str(COUNT)) # with 'w', it overwrites the previous number
                count_txt_write.flush()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                print_final_info()
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            if (resp.status == 200):
                COUNT += 1
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
