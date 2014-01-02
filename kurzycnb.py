import logging
import webapp2
from webapp2_extras import routes

app = webapp2.WSGIApplication([
    routes.PathPrefixRoute('/v1', [
        webapp2.Route('/aktualni', handler='rates.RatesHandler:get_current', name='current-rates'),
        webapp2.Route('/<year:\d{4}>/<month:\d{1,2}>/<day:\d{1,2}>', handler='rates.RatesHandler:get_historic', name='historic-rates'),
        webapp2.Route('/', handler='rates.RatesHandler:index', name='index')
    ]),
    webapp2.Route('/', handler='rates.RatesHandler:index', name='index')
], debug=True)

def handle_404(request, response, exception):
  logging.exception(exception)
  response.set_status(404)
  response.headers['Content-Type'] = 'text/plain'
  response.write('Ooops! Your request is not appropriate')

def handle_500(request, response, exception):
  logging.exception(exception)
  response.set_status(500)
  response.headers['Content-Type'] = 'text/plain'
  response.write('Ooops! Something went wrong on our side')

app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500
