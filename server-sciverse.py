#!flask/bin/python
from flask import Flask, url_for
from urllib2 import Request, urlopen, URLError
import json

app = Flask(__name__)

apiKey= '6492f9c867ddf3e84baa10b5971e3e3d'

@app.route('/api/getAuthor/<authFirst>&<authLast>')
def api_getAuthor(authFirst, authLast):
	url = 'http://api.elsevier.com:80/content/search/author?query=authfirst(%s)' %authFirst
	url += '%20and%20'
	url += 'authlast(%s)&apiKey=%s' %(authLast, apiKey)
	jsonReply = sciverseResponse(url)
	return parseAuthor(jsonReply)

@app.route('/api/getAffiliation/<affilName>')
def api_getAffiliation(affilName):
	url = 'http://api.elsevier.com:80/content/search/affiliation?query='
	url += 'affil(%s)&apiKey=%s' %(affilName, apiKey)
	jsonAffil = sciverseResponse(url)
	return parseAffiliation(jsonAffil)
	

@app.route('/api/getDocumentsByAuthor/<authorID>')
def api_getDocumentsByAuthor(authorID):
		#todo
	return sciverseResponse(url)

@app.route('/api/getDocumentsByTitle/<DocTitle>')
def api_getDocumentsByTitle(DocTitle):
	url = 'http://api.elsevier.com:80/content/search/author?query=authfirst(%s)' %authFirst
	url += '%20and%20'
	url += 'authlast(%s)&apiKey=%s' %(authLast, apiKey)
	jsonReply = sciverseResponse(url)
	return parseAuthor(jsonReply)

def sciverseResponse(url):
	# Get the dataset
	request = Request(url)
	try:
		response = urlopen(request)
		reply = response.read()
		jsonReply = json.loads(reply)
		return jsonReply
	except URLError, e:
		return 'No response',e

def parseAffiliation(jsonAffil):
	del jsonAffil['search-results']['link']
	return json.dumps(jsonAffil)

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


if __name__ == '__main__':
	app.run(debug=True)

