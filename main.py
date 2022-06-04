import threading
import requests
from bs4 import BeautifulSoup as bs4
import pandas as pd
import time
import os
from dotenv import load_dotenv

total_start_time = time.time()

load_dotenv()

access_key = os.getenv("ACCESS_KEY")

print(requests.post("https://api.studenc.ml/api/setinactive/", data={"key": access_key}).text)

URL = "https://www.studentski-servis.com/studenti/prosta-dela?kljb=&page=1&isci=1&sort=&dm1s=1&hourly_rate=5.21%3B21"
NUMOFTHREADS = 4

page = requests.get(URL)

soup = bs4(page.content, 'html.parser')

numofpages = int(soup.find_all("div", class_="page-items")[0].find_all("a", class_="page-link")[-1].text)
print("Number of pages: " + str(numofpages))
numperthread = int(numofpages / NUMOFTHREADS)
print("Num. of pages per thread: " + str(numperthread))

class ScraperThread(threading.Thread):
    def __init__(self, threadID, name, start, end):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.start_ = start
        self.end = end
        
    def run(self):
        print("Starting " + self.name + " pages " + str(self.start_) + " to " + str(self.end))
        self.scrape_page()
        print("Exiting " + self.name)
        
    def scrape_page(self):
        cookies = {
            "user_auth": os.getenv("TOKEN")
        }
        
        access_key = os.getenv("ACCESS_KEY")
        
        jobs_done = 0
        for i in range(self.start_, self.end):
            start_time = time.time()
            soup = bs4(requests.get(URL.replace("page=1", "page=" + str(i)), cookies=cookies).content, "html.parser")
            
            results = soup.find(id="results")
            job_items = results.find_all("article", class_="job-item")
            
            times = []
            t2 = time.time()
            for job in job_items:
                
                #print(job.prettify())
                
                title = job.find("h3").text.strip()
                attribs = job.find("ul", class_="job-attributes").find_all("li")
                location = attribs[0].text.strip()
                pay = attribs[1].find("a")
                try:
                    neto = float(pay.find("strong").text.strip().split(" ")[0])
                    bruto = float(pay.text.strip().replace("(", "").replace(")", "").split(" ")[0])
                except:
                    neto = 0
                    bruto = 0
                description = job.find("p", class_="description").text.strip()
                code = job.find("span", class_="job-code mb-0").find("strong").text.strip()
                try:
                    spots = int(job.find("div", class_="col-md").find("ul", class_="job-attributes").find_all("li")[0].find("strong").text.strip())
                except Exception as e:
                    spots = 0
                
                jobdetail = job.find("div", class_="job-detail")
                
                try:
                    data_link = job.find("button", class_="btn btn-link")["link-data"]
                except Exception as e:
                    # print(e)
                    data_link = "f"
                    
                # print(spots, data_link)
                
                email = ""
                phone = ""
                
                if data_link != "f":
                    if data_link.endswith("T"):
                        phone = bs4(requests.get("https://studentski-servis.com" + data_link, cookies=cookies).text, "html.parser").find("a").text.strip()
                    elif data_link.endswith("E"):
                        email = bs4(requests.get("https://studentski-servis.com" + data_link, cookies=cookies).text, "html.parser").find("a").text.strip()

                
                try:       
                    contact = jobdetail.children[0].children[0].find("strong").text.strip()
                except Exception as e:
                    contact = ""
                    
                try:       
                    company = jobdetail.find("ul").find("li").text.strip().replace("Podjetje: ", "")
                except Exception as e:
                    company = ""
                    
                # print("JOB: ", title, location, neto, bruto, code, spots, email, phone, contact, company)
                
                jobdata = {
                    "title": title,
                    "location": location,
                    "description": description,
                    "neto": neto,
                    "bruto": bruto,
                    "code": code,
                    "spots": spots,
                    "email": email,
                    "phone": phone,
                    "contact": contact,
                    "company": company,
                    "key": access_key
                }
                
                # print(company)
                
                company1 = {
                    "name": company,
                    "key": access_key,
                }
                
                respons = requests.post("https://api.studenc.ml/api/postcompany/", data=company1)
                id = respons.json()["id"]
                # print(id)
                
                jobdata["company"] = id
                respons = requests.post("https://api.studenc.ml/api/postjob/", data=jobdata)
                # print(respons.text)
                
                jobs_done += 1
                
                times.append(time.time() - t2)

threads = []

prev_start = 1
for thread in range(1, NUMOFTHREADS+1):
    if thread == NUMOFTHREADS:
        n = prev_start + numperthread
        if n != numofpages:
            threads.append(ScraperThread(thread, "Thread-" + str(thread), prev_start, numofpages))
        else:
            threads.append(ScraperThread(thread, "Thread-" + str(thread), prev_start, n))
    else:
        threads.append(ScraperThread(thread, "Thread-" + str(thread), prev_start, prev_start + numperthread))
        prev_start += numperthread
    
for thread in threads:
    thread.start()

for thread in threads:
    thread.join()
    
print(requests.post("https://api.studenc.ml/api/recordstats/", data={"key": access_key}).text)


print("Total time: " + str(time.time() - total_start_time) + " s")