#!flask/bin/python
from flask import Flask, url_for, jsonify, request
from urllib2 import Request, urlopen, URLError
from functools import wraps
import urllib, urlparse, json, errorHandler
from parseInfo import parseAuthor, parseInstitution, parseDocuments
from errorHandler import gatewayTimeoutRequest, badGatewayRequest, severErrorRequest, unauthorizedRequest

app = Flask(__name__)

# global passphrases
username = 'cmput402'
password = 'qpskcnvb'
apiKey= '6492f9c867ddf3e84baa10b5971e3e3d'

#names
author = "author"
institute= "insitute"
documents = "documents"

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
	return Response(url, author, False)

@app.route('/api/getAuthor/<authLast>')
@requires_auth
def api_getAuthorByLastName(authLast):
	url = 'http://api.elsevier.com:80/content/search/author?query=authlast(%s)&apiKey=%s' \
		%(authLast, apiKey)
 	return Response(url, author)

@app.route('/api/getInstitution/<InstitutionName>')
@requires_auth
def api_getInstitution(InstitutionName):
	url = 'http://api.elsevier.com:80/content/search/affiliation?query=affil(%s)&apiKey=%s' \
		%(InstitutionName, apiKey)
 	return Response(url, institute)

@app.route('/api/getDocumentsByAuthorID/<authorID>')
@requires_auth
def api_getDocumentsByAuthorID(authorID):
	url = 'http://api.elsevier.com:80/content/search/scopus?query=AU-ID(%s)' %(authorID)
	url += '&apiKey=%s' %(apiKey)
	return Response(url, documents)

@app.route('/api/getDocumentsByTitle/<DocTitle>')
@requires_auth
def api_getDocumentsByTitle(DocTitle):
	url = 'http://api.elsevier.com:80/content/search/scopus?query=title(%s)&apiKey=%s' %(DocTitle, apiKey)
	return Response(url, documents)
    
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

def Response(url, Type, urlEncode=True):
	try:
		jsonReply = sciverseResponse(url, urlEncode)
		if Type == author:
			return parseAuthor(jsonReply)
		elif Type == institute:
			return parseInstitution(jsonReply)
		elif Type == documents:
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
	return errorHandler.malformedRequest()

@app.errorhandler(500)
def customServerError(e):
 	return errorHandler.customServerError(e)


@app.errorhandler(404)
def customBadUrl(e):
	return errorHandler.customBadUrl(e)

@app.errorhandler(502)
def customBadGateway(e):
	return errorHandler.customBadGateway(e)


if __name__ == '__main__':
	# To start a local development server for debugging purposes
	app.run(debug=True)
	
	# For actual deployment purposes
	# app.run(host='0.0.0.0', port=5000)
