#!flask/bin/python
from flask import Flask, url_for
from urllib2 import Request, urlopen, URLError
import json

app = Flask(__name__)

apiKey= '6492f9c867ddf3e84baa10b5971e3e3d'

def jdefault(o):
    return o.__dict__

@app.route('/api/getAuthor/authorFirst=<authFirst> authorLast=<authLast>')
def api_getAuthor(authFirst, authLast):
	url = 'http://api.elsevier.com:80/content/search/author?query=authfirst(%s)' %authFirst
	url += '%20and%20'
	url += 'authlast(%s)&apiKey=%s' %(authLast, apiKey)
	return sciverseResponse(url)

def parseAffiliation(jsonAffil):

	class Affiliation(object):
	    def __init__(self):
	        self.scopus_affiliation_id = ""
	        self.affiliation_name = ""
	        self.document_count = 0
	        self.author_count = 0
	        self.city = ""
	        self.state = ""
	        self.country = ""
	        self.postal_code = ""
	        self.address = ""
	        self.org_URL = ""
	        self.scopus_link = ""

	res = {}
	entry = []
	newJsonAffil = jsonAffil.copy()
	if newJsonAffil.get('search-results'):
		if newJsonAffil['search-results'].get('opensearch:totalResults'):
			totalResults = newJsonAffil['search-results']['opensearch:totalResults']
			res['totalResults'] = totalResults
			if (totalResults != 0):
				for item in newJsonAffil['search-results']['entry']:
					affil = Affiliation()
					affil.scopus_affiliation_id = item.get('dc:identifier')
					affil.affiliation_name = item.get('affiliation-name')
					affil.document_count = item.get('document-count')
					affil.author_count = item.get('affiliation-name')
					affil.city = item.get('city')
					affil.country = item.get('country')
					if (item.get('link')):
						for link in item['link']:
							if (link['@ref'] == 'scopus-affiliation'):
								affil.scopus_link = link['@href']
						entry.append(affil)
				res['affiliations'] = entry

	return json.dumps(res, indent=4, default=jdefault)

@app.route('/api/getAffiliation/<affilName>')
def api_getAffiliation(affilName):
	url = 'http://api.elsevier.com:80/content/search/affiliation?query='
	url += 'affil(%s)&apiKey=%s' %(affilName, apiKey)
	print url
	jsonAffil = sciverseResponse(url)
	return parseAffiliation(jsonAffil)
	

@app.route('/api/getDocumentsByAuthor/<authorID>')
def api_getDocumentsByAuthor(authorID):
		#todo
	return sciverseResponse(url)

@app.route('/api/getDocumentsByTitle/<DocTitle>')
def api_getDocumentsByTitle(DocTitle):
		#todo
	return sciverseResponse(url)

def sciverseResponse(url):
	# Get the dataset
	request = Request(url)
	try:
		response = urlopen(request)
		reply = response.read()
		jsonAffil = json.loads(reply)
		return jsonAffil
	except URLError, e:
		return 'No response',e

if __name__ == '__main__':
	app.run(debug=True)