from urllib2 import Request, urlopen, URLError
import urllib, urlparse, json, errorHandler
from errorHandler import gatewayTimeoutRequest, badGatewayRequest, severErrorRequest, requires_auth, apiKey

'''
:copyright: (C) 2015 by Nhu Bui, Justin Hoy
#:license:   MIT/X11, see LICENSE for more details.
'''

#names
author = "author"
institute= "insitute"
documents = "documents"

class severError( Exception ): pass
class gatewayError( Exception ): pass
class gatewayTimedOutError( Exception ): pass

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
				Id= sciverseItem.get('dc:identifier','')
				
				#setinfo
				doc.scopus_document_uid = Id.replace('SCOPUS_ID:', '', 1)
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
			self.parent_Affil_id =""

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
					InstitId = item.get('dc:identifier', '').replace('AFFILIATION_ID:', '', 1)
					Instit.scopus_Instit_id = InstitId
					if (item.get('link')):
						for link in item['link']:
							if (link['@ref'] == 'scopus-affiliation'):
								Instit.scopus_link = link['@href']
					try:
						if(InstitId != ''):
							parseInstitByID(Instit, InstitId)
					except Exception as e:
					 	pass
					entry.append(Instit)
				res['Institutions'] = entry
	return json.dumps(res, indent=4, default=jdefault)

def parseInstitByID(Instit, InstitId):
	InstitRetrievalUrl = 'http://api.elsevier.com/content/affiliation/affiliation_id/%s' %(InstitId)
	InstitRetrievalUrl  += '?apiKey=%s' %(apiKey)
	jsonInstitRetrieval = sciverseResponse(InstitRetrievalUrl)
	newJsonRetrievalInstit = jsonInstitRetrieval.copy()
	
	#shortcut names
	entry = newJsonRetrievalInstit.get('affiliation-retrieval-response', {})
	institProfile = entry.get('institution-profile',{})
	institCoreData = entry.get('coredata',{})
	institAddress = institProfile.get('address',{})

	#setinfo
	Instit.address = entry.get('address')
	Instit.Instit_name = entry.get('affiliation-name')
	Instit.author_count = institCoreData.get('author-count')
	Instit.parent_Affil_id = institCoreData.get('parent-affiliation-id')
	Instit.document_count = institCoreData.get('document-count')
	Instit.org_URL = institProfile.get('org-URL')
	Instit.postal_code = institAddress.get('postal-code')
	Instit.state = institAddress.get('state')
	Instit.city = institAddress.get('city')
	Instit.country = institAddress.get('country')


def jdefault(o):
    return o.__dict__


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

