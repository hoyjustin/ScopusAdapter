from flask import jsonify, request, Response
from functools import wraps
import json

'''
:copyright: (C) 2015 by Nhu Bui, Justin Hoy
#:license:   MIT/X11, see LICENSE for more details.
'''

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
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def authenticate():
    """Sends a 401 response that enables basic auth"""
    data = {
	"errors": [
        	{'message'  : '401 -Unauthorized Request - Please authenticate using a correct user and password combination'}
	]
    }
    js = json.dumps(data)
    return Response(js+"\n", 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def check_auth(usernameInput, passwordInput):
    return (usernameInput == username) and (passwordInput == password)

def malformedRequest():
	return handleError(400, 'Bad Request - The request could not be understood by the server due to malformed syntax')

def customServerError(e):
 	return severErrorRequest()

def severErrorRequest():
	return handleError(500, 'Internal Server Error - The server encountered an unexpected condition which prevented it from fulfilling the request')

def customBadUrl(e):
	return badUrlRequest()

def badUrlRequest():
	return handleError(404, 'Not found - The server has not found anything matching the Request-URL')

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
