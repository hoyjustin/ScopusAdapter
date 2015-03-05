#!flask/bin/python
from flask import Flask, url_for, jsonify, request
import errorHandler, parseInfo
from parseInfo import Response
from errorHandler import requires_auth, apiKey

app = Flask(__name__)

@app.route('/api/getAuthor/<authFirst>/<authLast>')
@requires_auth
def api_getAuthorByFullName(authFirst, authLast):
	url = 'http://api.elsevier.com:80/content/search/author?query=authfirst(%s)' %(authFirst)
	url += '%20and%20' 
	url += 'authlast(%s)&apiKey=%s' %(authLast, apiKey)
	#because sciverse contains urlencoding (ie.%20), we do not urlencode this url
	return Response(url, parseInfo.author, False)

@app.route('/api/getAuthor/<authLast>')
@requires_auth
def api_getAuthorByLastName(authLast):
	url = 'http://api.elsevier.com:80/content/search/author?query=authlast(%s)&apiKey=%s' \
		%(authLast, apiKey)
 	return Response(url, parseInfo.author)

@app.route('/api/getInstitution/<InstitutionName>')
@requires_auth
def api_getInstitution(InstitutionName):
	url = 'http://api.elsevier.com:80/content/search/affiliation?query=affil(%s)&apiKey=%s' \
		%(InstitutionName, apiKey)
 	return Response(url, parseInfo.institute)

@app.route('/api/getDocumentsByAuthorID/<authorID>')
@requires_auth
def api_getDocumentsByAuthorID(authorID):
	url = 'http://api.elsevier.com:80/content/search/scopus?query=AU-ID(%s)' %(authorID)
	url += '&apiKey=%s' %(apiKey)
	return Response(url, parseInfo.documents)

@app.route('/api/getDocumentsByTitle/<DocTitle>')
@requires_auth
def api_getDocumentsByTitle(DocTitle):
	url = 'http://api.elsevier.com:80/content/search/scopus?query=title(%s)&apiKey=%s' %(DocTitle, apiKey)
	return Response(url, parseInfo.documents)
    
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
	# app.run(debug=True)
	
	# For actual deployment purposes
	 app.run(host='0.0.0.0', port=8000)
