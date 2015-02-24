#!flask/bin/python
from flask import Flask, url_for
from urllib2 import Request, urlopen, URLError

app = Flask(__name__)

apiKey= '6492f9c867ddf3e84baa10b5971e3e3d'

@app.route('/api/getAuthor/authorFirst=<authFirst> authorLast=<authLast>')
def api_getAuthor(authFirst, authLast):
	url = 'http://api.elsevier.com:80/content/search/author?query=authfirst(%s)' %authFirst
	url += '%20and%20'
	url += 'authlast(%s)&apiKey=%s' %(authLast, apiKey)
	return sciverseResponse(url)

@app.route('/api/getAffiliation/<affilName>')
def api_getAffiliation(affilName):
	url = 'http://api.elsevier.com:80/content/search/affiliation?query='
	url += 'affil(%s)&apiKey=%s' %(affilName, apiKey)
	return sciverseResponse(url)

@app.route('/api/getDocumentsByAuthor/<authorID>')
def api_getDocumentsByAuthor(authorID):
    	#todo
	return sciverseResponse(url)

@app.route('/api/getDocumentsByTitle/<DocTitle>')
def api_getDocumentsByTitle(DocTitle):
    	#todo
	return sciverseResponse(url)


def sciverseResponse(url):
    request = Request(url)
    try:
	response = urlopen(request)
	reply = response.read()
	#todo parsing the information
	return reply
    except URLError, e:
	return 'No response',e
	
if __name__ == '__main__':
    app.run(debug=True)

