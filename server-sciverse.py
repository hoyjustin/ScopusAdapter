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

class severError( Exception ): pass
class gatewayError( Exception ): pass
class gatewayTimedOutError( Exception ): pass

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
@requires_auth
def api_getAuthorByFullName(authFirst, authLast):
	url = 'http://api.elsevier.com:80/content/search/author?query=authfirst(%s)' %(authFirst)
	url += '%20and%20' 
	url += 'authlast(%s)&apiKey=%s' %(authLast, apiKey)
	#because sciverse contains urlencoding (ie.%20), we do not urlencode this url
	return Response(url, "author", False)

@app.route('/api/getAuthor/<authLast>')
@requires_auth
def api_getAuthorByLastName(authLast):
	url = 'http://api.elsevier.com:80/content/search/author?query=authlast(%s)&apiKey=%s' \
		%(authLast, apiKey)
 	return Response(url, "author")

@app.route('/api/getInstitution/<InstitutionName>')
@requires_auth
def api_getInstitution(InstitutionName):
	url = 'http://api.elsevier.com:80/content/search/affiliation?query=affil(%s)&apiKey=%s' \
		%(InstitutionName, apiKey)
 	return Response(url, "institute")

@app.route('/api/getDocumentsByAuthorID/<authorID>')
@requires_auth
def api_getDocumentsByAuthorID(authorID):
	url = 'http://api.elsevier.com:80/content/search/scopus?query=AU-ID(%s)' %(authorID)
	url += '&apiKey=%s' %(apiKey)
	return Response(url, "documents")

@app.route('/api/getDocumentsByTitle/<DocTitle>')
@requires_auth
def api_getDocumentsByTitle(DocTitle):
	url = 'http://api.elsevier.com:80/content/search/scopus?query=title(%s)&apiKey=%s' %(DocTitle, apiKey)
	return Response(url, "documents")
    
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
        #if contained unicode character, fix the url
        if urlfix:
	    url = url_fix(url)
	request = Request(url, headers={"Accept" : "application/json"})
	try:
		response = urlopen(request)
		if(response.getcode() == 0):
			# Internal server error on Scopus API
			raise severError('500 - Internal Server Error')
		if(response.getcode() == 502):
			# Bad gatway error on Scopus API
			raise gatewayError('502 - Bad Gateway Error')
		if(response.getcode() == 504):
			# Timed out error on Scopus API
			raise gatewayTimedOutError('504 - Gateway Timed Out')
		reply = response.read()
		jsonReply = json.loads(reply)
		return jsonReply
	except URLError, e:
		# urllib2 IO Error
		raise severError('500 - Internal Server Error')

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
				auth_uId = sciverseItem.get('dc:identifier').replace('AUTHOR_ID:', '', 1)
				author.scopus_author_uid = auth_uId
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
				docId = sciverseItem.get('dc:identifier').replace('SCOPUS_ID:', '', 1)
				doc.scopus_document_uid = docId
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
				doc.doi= sciverseItem.get('prism:doi')
				doc.citedby_count = sciverseItem.get('citedby-count')
				for Afill_iter in sciverseAffiliation:
				    Afills ={} 
				    Afills["affilname"] = Afill_iter.get("affilname")
				    Afills["affiliation-city"] = Afill_iter.get("affiliation-city")
				    Afills["affiliation_country"] = Afill_iter.get("affiliation_country")
				    #add to list in json
				    doc.affiliations.append(Afills)				
				doc.aggregationType = sciverseItem.get('prism:aggregationType')
				doc.subtypeDescription =sciverseItem.get('subtypeDescription')
				for link_iter in sciverseLinks:
				    Links ={} 
				    Links["link"] = link_iter.get("@href")
				    #add to list in json
				    doc.links.append(Links)	
				entry.append(doc)

	results["entry"] = entry
	return json.dumps(results, indent=4, default=jdefault)

def parseInstitution(jsonInstit):
	class Institution(object):

		def __init__(self):
			self.scopus_Instit_id = ""
			self.Instit_name = ""
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
	newJsonInstit = jsonInstit.copy()
	if newJsonInstit.get('search-results'):
		if newJsonInstit['search-results'].get('opensearch:totalResults'):
			totalResults = newJsonInstit['search-results']['opensearch:totalResults']
			res['totalResults'] = totalResults
			if (totalResults != '0'):
				for item in newJsonInstit['search-results']['entry']:
					Instit = Institution()
					InstitId = item.get('dc:identifier').replace('AFFILIATION_ID:', '', 1)
					Instit.scopus_Instit_id = InstitId
					Instit.Instit_name = item.get('affiliation-name')
					Instit.document_count = item.get('document-count')
					Instit.city = item.get('city')
					Instit.country = item.get('country')
					if (item.get('link')):
						for link in item['link']:
							if (link['@ref'] == 'scopus-affiliation'):
								Instit.scopus_link = link['@href']
					try:
						if(InstitId != ''):
							parseRetrievalInstit(Instit, InstitId)
					except Exception as e:
					 	pass
					entry.append(Instit)
				res['Institutions'] = entry
	return json.dumps(res, indent=4, default=jdefault)

def parseRetrievalInstit(Instit, InstitId):
	InstitRetrievalUrl = 'http://api.elsevier.com/content/affiliation/affiliation_id/%s' %(InstitId)
	InstitRetrievalUrl  += '?apiKey=%s' %(apiKey)
	jsonInstitRetrieval = sciverseResponse(InstitRetrievalUrl)
	newJsonRetrievalInstit = jsonInstitRetrieval.copy()
	
	if newJsonRetrievalInstit.get('affiliation-retrieval-response'):
		Instit.address = newJsonRetrievalInstit['affiliation-retrieval-response'].get('address')
		if newJsonRetrievalInstit['affiliation-retrieval-response'].get('coredata'):
			Instit.author_count = newJsonRetrievalInstit['affiliation-retrieval-response']['coredata'].get('author-count')
		if newJsonRetrievalInstit['affiliation-retrieval-response'].get('institution-profile'):
			Instit.org_URL = newJsonRetrievalInstit['affiliation-retrieval-response']['institution-profile'].get('org-URL')
			if newJsonRetrievalInstit['affiliation-retrieval-response']['institution-profile'].get('address'):
				Instit.postal_code = newJsonRetrievalInstit['affiliation-retrieval-response']['institution-profile']['address'].get('postal-code')
				Instit.state = newJsonRetrievalInstit['affiliation-retrieval-response']['institution-profile']['address'].get('state')

def jdefault(o):
    return o.__dict__

def Response(url, Type, urlEncode=True):
	try:
		jsonReply = sciverseResponse(url, urlEncode)
		if Type == "author":
			return parseAuthor(jsonReply)
		elif Type == "institute":
			return parseInstitution(jsonReply)
		elif Type == "documents":
			return parseDocuments(jsonReply)
		else:
			return severErrorRequest()
	except severError as e1:
		return severErrorRequest()
	except gatewayError as e2:
		return badGatewayRequest()
	except gatewayTimedOutError as e3:
		return gatewayTimeoutRequest()

@app.route('/api/getAuthor/')
@app.route('/api/getInstitution/')
@app.route('/api/getDocumentsByAuthorID/')
@app.route('/api/getDocumentsByTitle/')
def malformedRequest():
	return handleError(400, 'Bad Request - The request could not be understood by the server due to malformed syntax')

@app.errorhandler(500)
def customServerError(e):
 	return severErrorRequest()

def severErrorRequest():
	return handleError(500, 'Internal Server Error - The server encountered an unexpected condition which prevented it from fulfilling the request')

@app.errorhandler(404)
def customBadUrl(e):
	return badUrlRequest()

def badUrlRequest():
	return handleError(404, 'Not found - The server has not found anything matching the Request-URL')

@app.errorhandler(502)
def customBadGateway(e):
	return badGatewayRequest()

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
	# To start a local development server for debugging purposes
	app.run(debug=True)
	
	# For actual deployment purposes
	# app.run(host='0.0.0.0', port=5000)
