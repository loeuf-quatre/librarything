# reticulate::use_condaenv("base")

import itertools
import pandas as pd
import re
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from siuba import arrange, _


os.environ["SELENIUM_SERVER_JAR"] = "./misc/selenium-server-4.7.1.jar"

browser = webdriver.Chrome()
browser.get("https://www.librarything.com/catalog/Keiras_lip_balm")

# Activate frame
frame = browser.find_element(By.NAME, "bottom")
browser.switch_to.frame(frame)

# Switch to view with LC classification and ISBN i.e. Style E
views = browser.find_elements(By.CLASS_NAME, "ltbtn-body")
views = [i for i in views if i.text == "C"]
views[0].click()

# Get page numbers in library
pages = browser.find_elements(By.CLASS_NAME, "show")
for p in pages:
  index = pages.index(p)
  pages[index] = p.text
pages = [re.sub("[^0-9]", "", i) for i in pages]
pages = int(max(pages))

def scrape_books():
  pids = [] # Page IDs
  ids = browser.find_elements("xpath", '//*[@id]') # ID tags
  for i in ids:
    attrs = i.get_attribute('id')
    pids.append(attrs)
  book_rows = re.compile("catrow")
  book_rows = [i for i in pids if book_rows.match(i)]
  md = []
  for b in book_rows:
    book = browser.find_element(By.ID, b)
    try:
      title = book.find_element(By.CLASS_NAME, "lt-title")
      title = title.text
    except:
      title = "NONE"
    try:
      lc = book.find_element(By.CLASS_NAME, "workdata")
      lc = lc.text
    except:
      lc = "NONE"
    try:
      author = book.find_element(By.CLASS_NAME, "lt-author")
      author = author.text
    except:
      author = "NONE"
    md.append([title, lc, author])
  return(md)
  

p = 1
mds = []
while(p <= pages):
  mds.append(scrape_books())
  p = p + 1
  try:
    next_page = browser.find_elements(By.CLASS_NAME, "pageShuttleButton")
    next_page_text = [np.text for np in next_page]
    index_pos = next_page_text.index("next page")
    next_page[index_pos].click()
  except:
    pass


mds = list(itertools.chain.from_iterable(mds))
df = pd.DataFrame(mds, columns=["title", "lc", "author"])
df["lc_class"] = [re.sub("[0-9]", "", i[:2]) for i in df["lc"].tolist()]

df = (
  df >>
    arrange(
      _.lc_class,
      _.lc
    )
)

df.to_csv("./output/klb.csv", index=False)
print(df.to_markdown())
