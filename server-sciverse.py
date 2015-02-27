#!flask/bin/python
from flask import Flask, url_for, jsonify, request
from urllib2 import Request, urlopen, URLError
from functools import wraps
import json

app = Flask(__name__)

# global passphrases
username = 'cmput402'
password = 'qpskcnvb'
apiKey= '6492f9c867ddf3e84baa10b5971e3e3d'

class severError( Exception ): pass
class malformedError( Exception ): pass

# Authenticate for adapter use
# ie) curl -v -u "cmput402:qpskcnvb" http://127.0.0.1:5000/api/getAuthor/<authFirst>&<authLast>
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth: 
            return unauthorizedRequest()
        elif not check_auth(auth.username, auth.password):
            return unauthorizedRequest()
        return f(*args, **kwargs)
    return decorated

def check_auth(usernameInput, passwordInput):
    return (usernameInput == username) and (passwordInput == password)

@app.route('/api/getAuthor/<authFirst>&<authLast>')
@requires_auth
def api_getAuthor(authFirst, authLast):
	url = 'http://api.elsevier.com:80/content/search/author?query=authfirst(%s)' %authFirst
	url += '%20and%20'
	url += 'authlast(%s)&apiKey=%s' %(authLast, apiKey)
	try:
		jsonAffil = sciverseResponse(url)
		return parseAuthor(jsonReply)
	except severError as e:
		return severErrorRequest()
	except malformedError as e:
		return malformedRequest()

@app.route('/api/getAffiliation/<affilName>')
@requires_auth
def api_getAffiliation(affilName):
	url = 'http://api.elsevier.com:80/content/search/affiliation?query='
	url += 'affil(%s)&apiKey=%s' %(affilName, apiKey)
	try:
		jsonAffil = sciverseResponse(url)
		return parseAffiliation(jsonAffil)
	except severError as e:
		return severErrorRequest()
	except malformedError as e:
		return malformedRequest()
	

@app.route('/api/getDocumentsByAuthor/<authorID>')
@requires_auth
def api_getDocumentsByAuthor(authorID):
	try:
		jsonAffil = sciverseResponse(url)
		#todo
		#return parseDocument(jsonAffil)
		return jsonAffil
	except severError as e:
		return severErrorRequest()
	except malformedError as e:
		return malformedRequest()

@app.route('/api/getDocumentsByTitle/<DocTitle>')
@requires_auth
def api_getDocumentsByTitle(DocTitle):
	url = 'http://api.elsevier.com:80/content/search/author?query=authfirst(%s)' %authFirst
	url += '%20and%20'
	url += 'authlast(%s)&apiKey=%s' %(authLast, apiKey)
	try:
		jsonAffil = sciverseResponse(url)
		return parseAuthor(jsonReply)
	except severError as e:
		return severErrorRequest()
	except malformedError as e:
		return malformedRequest()

def sciverseResponse(url):
	# Get the dataset
	request = Request(url)
	try:
		response = urlopen(request)
		if(response.getcode() == 0):
			# Internal server error on Scopus API
			raise severError('500 - Internal Server Error')
		reply = response.read()
		jsonReply = json.loads(reply)
		return jsonReply
	except URLError, e:
		# IO Error with urllib2
		raise severError('500 - Internal Server Error')

def parseAuthor(sciverse):
	authorJson ={"authors": []}

	#find and set number of authors found
	totalResults  = sciverse.get("search-results").get("opensearch:totalResults")
	authorJson["totalResults"] = totalResults 

	sciverseResults = sciverse.get("search-results").get('entry')

	#if sciverseResults
	for x in range(int(totalResults)):
		setAuthorInfo = {"subject-area": []}

		#iterate the author entry in sciverse
		sciverseResults = sciverse["search-results"]['entry'][x]

		#shortcut names
		sciverseAffiliation = sciverseResults.get('affiliation-current',{} )
		sciverseName = sciverseResults.get('preferred-name',{})
		sciverseSubject = sciverseResults.get('subject-area',{})
		
		#setinfo
		setAuthorInfo["scopus-eid"] = sciverseResults.get("eid")
		setAuthorInfo["scopus-author-id"] = sciverseResults.get('dc:identifier')
		setAuthorInfo["surname"] = sciverseName.get('surname')
		setAuthorInfo["given-name"] = sciverseName.get('given-name')
		setAuthorInfo["initials"] = sciverseName.get('initials')
		setAuthorInfo["document-count"] = sciverseResults.get("document-count")
		setAuthorInfo["scopus-affil-id"] = sciverseAffiliation.get("affiliation-id")
		setAuthorInfo["affil-name"] = sciverseAffiliation.get("affiliation-name")
		setAuthorInfo["affil-city"] = sciverseAffiliation.get("affiliation-city")
		setAuthorInfo["affil-country"] = sciverseAffiliation.get("affiliation-country")
		for sciverseSubject_iter in sciverseSubject:
			setSubject ={}
			setSubject["number-of-document"] = sciverseSubject_iter.get("@frequency")
			setSubject["subject"] = sciverseSubject_iter.get("$")

			#add to subject-area list in json
			setAuthorInfo["subject-area"].append(setSubject)

		#TODO
		#for n in Journals:
		#setAuthorInfo["Journals"][0]["title"] =None
		#setAuthorInfo["Journals"][0]["issn"] =None
		#add to journals list in json
		#authorJson["journals"].append(setAuthorInfo)

		#add to authors list in json
		authorJson["authors"].append(setAuthorInfo)



	json_data = json.dumps(authorJson)


	return json_data
	#return json_data

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
			if (totalResults != '0'):
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
					#TODO query other affiliation api
				res['affiliations'] = entry
				return json.dumps(res, indent=4, default=jdefault)
	raise malformedError('400 - Bad Request')

def jdefault(o):
    return o.__dict__

@app.route('/api/getAuthor/')
@app.route('/api/getAffiliation/')
@app.route('/api/getDocumentsByAuthor/')
@app.route('/api/getDocumentsByTitle/')
def malformedRequest():
	return handleError(400, 'Bad Request - The request could not be understood by the server due to malformed syntax')

@app.errorhandler(500)
def severErrorRequest():
	return handleError(500, 'Internal Server Error - The server encountered an unexpected condition which prevented it from fulfilling the request')

def badUrlRequest():
	return handleError(404, 'Not found - The server has not found anything matching the Request-URL')

@app.errorhandler(502)
def badGatewayRequest():
	return handleError(502, 'Bad gateway')

def gatewayTimeoutRequest():
	return handleError(504, 'Gateway timeout')

def unauthorizedRequest():
	return handleError(401, 'Unauthorized Request - Please authenticate using a correct user and password combination')

def handleError(code, message):
	res = {}
	errors = []
	malformedMessage = {
		'message': "{0}{1}".format(code, ' - ' + message),
	}
	errors.append(malformedMessage)
	res['errors'] = errors
	resp = jsonify(res)
	resp.status_code = code
	return resp

if __name__ == '__main__':
	app.run(debug=True)