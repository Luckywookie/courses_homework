#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from scoring import get_score

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class BaseField(object):
    def __init__(self, required=False, nullable=False):
        self.name = None
        self.required = required
        self.nullable = nullable
        self._type = str

    def __get__(self, instance, cls):
        print('get', self, instance, cls)
        if instance:
            return self.name
        else:
            return self

    def __set__(self, instance, value):
        print('set', self, instance, value)
        if instance and isinstance(value, self._type):
            setattr(instance, self.name, value)
        else:
            raise AttributeError('Wrong type of value!')

    def __delete__(self, instance):
        raise AttributeError("Can't delete attribute")


class Field(object):
    def __init__(self, name, required=False, nullable=False):
        # self.name = self.__dict__['name']
        self.name = "_" + name
        self.required = required
        self.nullable = nullable
        self._type = str

    def __get__(self, instance, cls):
        print('get', self, instance, cls)
        print(instance.__dict__)
        print(instance.__dict__[self.name])
        return getattr(instance, self.name)

    def __set__(self, instance, value):
        print('set', self, instance, value)
        if type(value) is self._type:
            setattr(instance, self.name, value)
        else:
            raise AttributeError('This field must be string')

    def __delete__(self, instance):
        raise AttributeError("Can't delete attribute")


class CharField(BaseField):
    def __init__(self, required=False, nullable=False):
        super(BaseField, self).__init__()
        self._type = str


class ArgumentsField(BaseField):
    def __init__(self, required=False, nullable=False):
        super(BaseField, self).__init__()
        self._type = dict


class EmailField(CharField):
    pass


class PhoneField(Field):
    pass


class DateField(Field):
    pass


class BirthDayField(Field):
    pass


class GenderField(Field):
    pass


class ClientIDsField(Field):
    pass


# class ClientsInterestsRequest(object):
#     client_ids = ClientIDsField(required=True)
#     date = DateField(required=False, nullable=True)
#
#
# class OnlineScoreRequest(object):
#     first_name = CharField(required=False, nullable=True)
#     last_name = CharField(required=False, nullable=True)
#     email = EmailField(required=False, nullable=True)
#     phone = PhoneField(required=False, nullable=True)
#     birthday = BirthDayField(required=False, nullable=True)
#     gender = GenderField(required=False, nullable=True)


class MethodRequest(object):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    def __init__(self, account, login, token, arguments, method):
        self.account = account
        self.login = login
        self.token = token
        self.arguments = arguments
        self.method = method

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code = None, None
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler,
        "get_score": (get_score(5, 'phone', 'email'), 'ok')
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_GET(self):
        print(self.headers)

    def do_POST(self):
        # print(MethodRequest.account)
        niq_req = MethodRequest('admin22', 'admin', '', {}, 'get_score')
        print(niq_req.account)
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            print(path)
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    print({"body": request, "headers": self.headers}, context, self.store)
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception, e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return

if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
