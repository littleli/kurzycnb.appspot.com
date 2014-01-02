import webapp2
import datetime
import json

from google.appengine.ext import ndb
from google.appengine.api import urlfetch

class Rates(ndb.Expando):
  issue_no = ndb.IntegerProperty(indexed=True)
  issue_date = ndb.DateProperty(indexed=True)
  issue_request = ndb.DateProperty(indexed=True)

class DateEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, datetime.date):
      return obj.isoformat()
    else:
      return json.JSONDecoder.default(self, obj)


class Fetcher(object):
  cnb_url = 'http://www.cnb.cz/cs/financni_trhy/devizovy_trh/kurzy_devizoveho_trhu/denni_kurz.txt'

  def parse_data(self, content, request_date):
    lines = content.split("\n")
    date_str, issue_str = lines[0].strip().split(" #")
    d, m, y = date_str.split(".")
    rates = Rates()
    setattr(rates, "issue_request", request_date)
    setattr(rates, "issue_date", datetime.date(int(y), int(m), int(d)))
    setattr(rates, "issue_no", int(issue_str))
    for line in lines[2:]:
      values = line.strip().split("|")
      if len(values) == 5:
        units = int(values[2])
        if units == 1:
          format_string = "{:.3f}"
        elif units == 100:
          format_string = "{:.5f}"
        elif units == 1000:
          format_string = "{:.6f}"
        else:
          continue
        setattr(rates, values[3], format_string.format(float(values[4].replace(',','.')) / units))
    return rates
  
  def fetch_latest(self):
    today = datetime.date.today()
    results = Rates.query(Rates.issue_request == today).fetch(1)
    if len(results) > 0:
      return results[0]
    else:
      result = urlfetch.fetch(self.cnb_url)
      if result.status_code == 200:
        rates = self.parse_data(result.content, today)
        rates.put()
        return rates
      else:
        return None
  
  def fetch_date(self, date):
    results = Rates.query(Rates.issue_request == date).fetch(1)
    if len(results) > 0:
      return results[0]
    else:
      result = urlfetch.fetch("%s?date=%d.%d.%d" % (self.cnb_url, date.day, date.month, date.year))
      if result.status_code == 200:
        rates = self.parse_data(result.content, date)
        rates.put()
        return rates
      else:
        return None


class RatesHandler(webapp2.RequestHandler):
  fetcher = Fetcher()
  
  def add_headers(self):
    self.response.headers['Content-Type'] = 'application/json'
    self.response.headers['Access-Control-Allow-Origin'] = '*'    
  
  def get_current(self):
    self.add_headers()
    fetched = self.fetcher.fetch_latest()
    if fetched == None:
      self.response.write(json.dumps({}))
    else:
      self.response.write(json.dumps(fetched.to_dict(), cls=DateEncoder))
    
  def get_historic(self, year, month, day):
    self.add_headers()
    today = datetime.date.today()
    try:
      query_date = datetime.date(int(year), int(month), int(day))
    except:
      self.response.set_status(400)
      self.response.write(json.dumps({"error":"Incorrect date"}))
      return
    if query_date > today:
      self.response.set_status(404)
      self.response.write(json.dumps({"error":"Ooops! Don't ask me about future"}))
    elif query_date < datetime.date(2009, 1, 1):
      self.response.set_status(404)
      self.response.write(json.dumps({"error":"Ooops! Data older then 2009 are not provided"}))
    else:
      fetched = self.fetcher.fetch_date(query_date)
      self.add_headers()
      if fetched == None:
        self.response.write(json.dumps({}))        
      else:
        self.response.write(json.dumps(fetched.to_dict(), cls=DateEncoder))
  
  def index(self):
    self.response.headers['Location'] = "https://kurzycnb.appspot.com/index.html"
    self.response.set_status(302)
