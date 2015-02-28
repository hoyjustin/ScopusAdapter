#!flask/bin/python
from flask import Flask, url_for, jsonify, request
from urllib2 import Request, urlopen, URLError
from functools import wraps
import urllib
import urlparse
import json, re

app = Flask(__name__)

# global passphrases
username = 'cmput402'
password = 'qpskcnvb'
apiKey= '6492f9c867ddf3e84baa10b5971e3e3d'

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

@app.route('/api/getAuthor/<authFirst>/<authLast>')
#@requires_auth
def api_getAuthorByFullName(authFirst, authLast):
	if not validName(authFirst) or not validName(authLast):
		return malformedRequest()

	url = 'http://api.elsevier.com:80/content/search/author?query=authfirst(%s)%20and%20authlast(%s)&apiKey=%s' %(authFirst, authLast, apiKey)
	jsonReply = sciverseResponse(url, False)
	return parseAuthor(jsonReply)
    
@app.route('/api/getAuthor/<authLast>')
#@requires_auth
def api_getAuthorByLastName(authLast):
	if not validName(authLast):
		return malformedRequest()

	url = 'http://api.elsevier.com:80/content/search/author?query=authlast(%s)&apiKey=%s' %(authLast, apiKey)
	jsonReply = sciverseResponse(url)
	return parseAuthor(jsonReply)

@app.route('/api/getAffiliation/<affilName>')
@requires_auth
def api_getAffiliation(affilName):
	url = 'http://api.elsevier.com:80/content/search/affiliation?query='
 	url += 'affil(%s)&apiKey=%s' %(affilName, apiKey)
 	try:
 		jsonAffil = sciverseResponse(url)
		return parseAffil(jsonAffil)
	except severError as e:
		return severErrorRequest()
	except malformedError as e:
		return malformedRequest()

@app.route('/api/getDocumentsByAuthorID/<authorID>')
#@requires_auth
def api_getDocumentsByAuthorID(authorID):
	url = 'http://api.elsevier.com:80/content/search/author?query=authfirst(%s)' %authFirst
	url += '%20and%20'
	url += 'authlast(%s)&apiKey=%s' %(authLast, apiKey)
	jsonReply = sciverseResponse(url)
	return parseDocumentsByAuthorID(jsonReply)

@app.route('/api/getDocumentsByTitle/<DocTitle>')
#@requires_auth
def api_getDocumentsByTitle(DocTitle):
	url = 'http://api.elsevier.com:80/content/search/scopus?query=title(%s)' %(DocTitle)
	url += '&apiKey=%s' %(apiKey)
	jsonReply = sciverseResponse(url)
	return parseDocuments(jsonReply)
    
def url_fix(s, charset='utf-8'):
    #"""Sometimes you get an URL by a user that just isn't a real
    #URL because it contains unsafe characters like ' ' and so on.  This
    #function can fix some of the problems in a similar way browsers
    #handle data entered by the user:
    #:param charset: The target charset for the URL if the url was
                    #given as unicode string.
    #"""
    if isinstance(s, unicode):
        s = s.encode(charset, 'ignore')
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
    path = urllib.quote(path, '/%')
    qs = urllib.quote_plus(qs, ':&=')
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))

def sciverseResponse(url, urlfix=True):
	# Get the dataset
        if urlfix:
	    url = url_fix(url)
	request = Request(url)
	try:
		response = urlopen(request)
		reply = response.read()
		jsonReply = json.loads(reply)
		return jsonReply
	except URLError, e:
		return 'No response',e

def parseAuthor(sciverse):
	class Author(object):
	    def __init__(self):
	        self.scopus_eid = ""
	        self.scopus_author_uid = ""
	        self.surname = ""
	        self.given_name = ""
	        self.initials = ""
	        self.document_count = ""
	        self.scopus_affil_uid = ""
	        self.affil_name = ""
	        self.affil_city = ""
	        self.affil_country = ""
	        self.subject_area= []

	
	results = {}
	entry =[]

	if (sciverse.get("search-results")):
		totalResults  = sciverse.get("search-results")
		results["totalResults"] = totalResults.get("opensearch:totalResults")

		if (totalResults != 0):
			for sciverseItem in totalResults.get('entry'):
				author = Author()
				#shortcut names
				sciverseAffiliation = sciverseItem.get('affiliation-current',{} )
				sciverseName = sciverseItem.get('preferred-name',{})
				sciverseSubject = sciverseItem.get('subject-area',{})

				#setinfo
				author.scopus_eid = sciverseItem.get("eid")
				author.scopus_author_uid = sciverseItem.get('dc:identifier')
				author.surname = sciverseName.get('surname')
				author.given_name = sciverseName.get('given-name')
				author.initials = sciverseName.get('initials')
				author.document_count = sciverseItem.get("document-count")
				author.scopus_affil_uid = sciverseAffiliation.get("affiliation-id")
				author.affil_name = sciverseAffiliation.get("affiliation-name")
				author.affil_city = sciverseAffiliation.get("affiliation-city")
				author.affil_country = sciverseAffiliation.get("affiliation-country")
				for sciverseSubject_iter in sciverseSubject:
					setSubject ={}
					setSubject["number-of-document"] = sciverseSubject_iter.get("@frequency")
					setSubject["subject"] = sciverseSubject_iter.get("$")
					#add to subject-area list in json
					author.subject_area.append(setSubject)
				entry.append(author)

	results["authors"] = entry
	return json.dumps(results, indent=4, default=jdefault)
    

def parseDocuments(sciverse):
	class Doc(object):
	    def __init__(self):
	    	self.scopus_document_uid= ""
	        self.scopus_eid = ""
	        self.title= ""
	        self.author= ""
	        self.publicationName = ""
	        self.issn = ""
	        self.volume = ""
	        self.issueIdentifier = ""
	        self.pageRange = 0
	        self.coverDate= ""
	        self.coverDisplayDate = ""
	        self.doi= ""
	        self.citedby_count = 0
	        self.affiliations=[]
	        self.aggregationType =""
	        self.subtypeDescription =""
	        self.links= []

	
	results = {}
	entry =[]

	if (sciverse.get("search-results")):
		totalResults  = sciverse.get("search-results")
		results["totalResults"] = totalResults.get("opensearch:totalResults")

		if (totalResults != 0):
			for sciverseItem in totalResults.get('entry'):
				doc = Doc()
				#shortcut names
				sciverseAffiliation = sciverseItem.get('affiliation',{} )
				sciverseLinks = sciverseItem.get('link',{})
				
				#setinfo
				doc.scopus_document_uid= sciverseItem.get('prism:doi')
				doc.scopus_eid = sciverseItem.get('eid')
				doc.title= sciverseItem.get('dc:title')
				doc.author= sciverseItem.get('dc:creator')			
				doc.publicationName = sciverseItem.get('prism:publicationName')
				doc.issn = sciverseItem.get('prism:issn')
				doc.volume = sciverseItem.get('prism:volume')
				doc.issueIdentifier = sciverseItem.get('prism:issueIdentifier')
				doc.pageRange = sciverseItem.get('prism:pageRange')
				doc.coverDate= sciverseItem.get('prism:coverDate')
				doc.coverDisplayDate = sciverseItem.get('prism:coverDisplayDate')
				doc.doi= sciverseItem.get('dc:title')
				doc.citedby_count = sciverseItem.get('citedby-count')
				for Afill_iter in sciverseAffiliation:
				    setAfills ={} 
				    setAfills["affilname"] = Afill_iter.get("affilname")
				    setAfills["affiliation-city"] = Afill_iter.get("affiliation-city")
				    setAfills["affiliation_country"] = Afill_iter.get("affiliation_country")
				    #add to list in json
				    doc.affiliations.append(setAfills)				
				doc.aggregationType = sciverseItem.get('prism:aggregationType')
				doc.subtypeDescription =sciverseItem.get('subtypeDescription')
				for link_iter in sciverseLinks:
				    setAfills ={} 
				    setAfills["link"] = link_iter.get("@href")
				    #add to list in json
				    doc.links.append(setAfills)	
				entry.append(doc)

	results["entry"] = entry
	return json.dumps(results, indent=4, default=jdefault)

def parseDocumentsByAuthorID(sciverse):
	class AuthorDoc(object):
	    def __init__(self):
	    	self.scopus_document_uid= ""
	        self.scopus_eid = ""
	        self.title= ""
	        self.authors= [ {self.given_name: "",
              				 self.surname: ""}]
	        self.publicationName = ""
	        self.issn = ""
	        self.volume = ""
	        self.issueIdentifier = ""
	        self.pageRange = 0
	        self.coverDate= ""
	        self.coverDisplayDate = ""
	        self.doi= ""
	        self.citedby_count = 0
	        self.affiliation=[]
	        self.aggregationType =""
	        self.subtypeDescription =""
	        self.link=""

	
	results = {}
	entry =[]

	if (sciverse.get("search-results")):
		totalResults  = sciverse.get("search-results")
		results["totalResults"] = totalResults.get("opensearch:totalResults")

		if (totalResults != 0):
			for sciverseItem in totalResults.get('entry'):
				authorDoc = AuthorDoc()
				#shortcut names
				sciverseAffiliation = sciverseItem.get('affiliation-current',{} )
				sciverseName = sciverseItem.get('preferred-name',{})
				sciverseSubject = sciverseItem.get('subject-area',{})

				#setinfo
				authorDoc.scopus_eid = sciverseItem.get("eid")
				authorDoc.scopus_author_uid = sciverseItem.get('dc:identifier')
				authorDoc.surname = sciverseName.get('surname')
				authorDoc.given_name = sciverseName.get('given-name')
				authorDoc.initials = sciverseName.get('initials')
				authorDoc.document_count = sciverseItem.get("document-count")
				authorDoc.scopus_affil_uid = sciverseAffiliation.get("affiliation-id")
				authorDoc.affil_name = sciverseAffiliation.get("affiliation-name")
				authorDoc.affil_city = sciverseAffiliation.get("affiliation-city")
				authorDoc.affil_country = sciverseAffiliation.get("affiliation-country")
				for sciverseSubject_iter in sciverseSubject:
					setSubject ={}
					setSubject["number-of-document"] = sciverseSubject_iter.get("@frequency")
					setSubject["subject"] = sciverseSubject_iter.get("$")
					#add to subject-area list in json
					authorDoc.subject_area.append(setSubject)
				entry.append(authorDoc)

	results["entry"] = entry
	return json.dumps(results, indent=4, default=jdefault)


def parseAffil(jsonAffil):
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
		    totalResults = newJsonAffil['search-results'].get('opensearch:totalResults', 0)
		    res['totalResults'] = totalResults
		    if (totalResults != '0'):
			for item in newJsonAffil['search-results']['entry']:
				affil = Affiliation()
				affilId = item.get('dc:identifier').replace('AFFILIATION_ID:', '', 1)
				affil.scopus_affiliation_id = affilId
				affil.affiliation_name = item.get('affiliation-name', '')
				affil.document_count = item.get('document-count', '')
				affil.author_count = item.get('affiliation-name', '')
				affil.city = item.get('city', '')
				affil.country = item.get('country', '')
				if (item.get('link')):
					for link in item['link']:
						if (link['@ref'] == 'scopus-affiliation'):
							affil.scopus_link = link.get('@href', '')
				try:
					if(affilId != ''):
						parseRetrievalAffil(affil, affilId)
				except Exception as e:
					pass
				entry.append(affil)
			res['affiliations'] = entry
			return json.dumps(res, indent=4, default=jdefault)
	raise malformedError('400 - Bad Request')

def parseRetrievalAffil(affil, affilId):
	authorRetrievalUrl = 'http://api.elsevier.com:80/content/affiliation/affiliation_id/%s?' %affilId
	authorRetrievalUrl += 'apiKey=%s' %apiKey
	jsonAffilRetrieval = sciverseResponse(authorRetrievalUrl)
	newJsonRetrievalAffil = jsonAffilRetrieval.copy()
	if newJsonRetrievalAffil.get('affiliation-retrieval-response'):
		affil.address = newJsonRetrievalAffil['affiliation-retrieval-response'].get('address', '')
		if newJsonRetrievalAffil['affiliation-retrieval-response'].get('institution-profile'):
			affil.postal_code = newJsonRetrievalAffil['affiliation-retrieval-response']['institution-profile'].get('postal-code', '')
			affil.org_URL = newJsonRetrievalAffil['affiliation-retrieval-response']['institution-profile'].get('org-URL', '')

def jdefault(o):
    return o.__dict__

@app.route('/api/getAuthor/')
@app.route('/api/getAffiliation/')
@app.route('/api/getDocumentsByAuthor/')
@app.route('/api/getDocumentsByTitle/')
def malformedRequest():
	return handleError(400, 'Bad Request - The request could not be understood by the server due to malformed syntax')

def severErrorRequest():
	return handleError(500, 'Internal Server Error - The server encountered an unexpected condition which prevented it from fulfilling the request')

@app.errorhandler(404)
def customBadUrl(e):
	return badUrlRequest()

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

def validName(string):
	#check if valid string
	namePattern = re.compile("^([a-zA-Z])+$")
	if not namePattern.match(string):
		return False
	return True

if __name__ == '__main__':
	#To start a local development server for debugging purposes
	app.run(debug=True)
	#app.run(host='0.0.0.0', port=5000)
