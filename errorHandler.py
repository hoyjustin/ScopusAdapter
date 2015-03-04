from flask import jsonify


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
