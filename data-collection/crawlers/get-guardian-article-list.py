#!/usr/bin/env python

BASE_URL="https://www.theguardian.com/world?page="
N_ARTICLE_LINK_PAGES = 1900
OUTPUT_FILE = './guardian-article-urls.json'
WORKER_THREADS = 32

import json
import datetime
import dateutil.parser
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from datetime import datetime
from newspaper import Article
from bs4 import BeautifulSoup
from typing import List
from queue import Queue
from threading import Thread
from requests import get


@dataclass_json
@dataclass
class GuardianArticleUrl:
    url: str
    title: str

class WriteThread(Thread):
    def __init__(self, queue: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue

    def run(self):
        with open(OUTPUT_FILE, 'a') as output_file:
            output_file.write("[\n")
            first_entry = True

            while True:
                article = self.queue.get()

                if article is None:
                    output_file.write("\n]")
                    break

                article_json = article.to_json(indent=4)

                if first_entry:
                    first_entry = False
                else:
                    output_file.write(",\n")

                output_file.write(article_json)


class ScrapeThread(Thread):
    def __init__(self, chunk, queue: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chunk = chunk
        self.queue = queue

    def run(self):
        for i in self.chunk:
            try:
                print(f'Getting articles from list page {i}')
                article_list_page = get(f"{BASE_URL}{i}")
                soup = BeautifulSoup(article_list_page.text, "html5lib")
                links = soup.find_all('a', {'class': 'fc-item__link'})
                for link in links: 
                    title = link.find('span', {'class': 'js-headline-text'})
                    article_url = GuardianArticleUrl(url=link['href'], title=str(title.string) or '')
                    self.queue.put(article_url)
            except Exception as e: # Best effort
                print(i)
                print(f'Something went wrong when scraping: {e}')
                print("------------------------------------------")



if __name__ == '__main__':
    queue = Queue()

    write_thread = WriteThread(queue)
    write_thread.start()

    worker_threads = []
    chunk_size =  N_ARTICLE_LINK_PAGES // WORKER_THREADS
    for i in range(0, N_ARTICLE_LINK_PAGES+1, chunk_size):
        chunk = range(i,i+chunk_size)
        worker_threads.append(ScrapeThread(chunk, queue))

    for thread in worker_threads:
        thread.start()

    for thread in worker_threads:
        thread.join()

    # Signal end of jobs to write thread
    queue.put(None)

    print('Done.')
    write_thread.join()


