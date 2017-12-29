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
from scoring import get_score, get_interests

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
    def __init__(self, required, nullable):
        self.name = None
        self.required = required
        self.nullable = nullable
        self._type = str

    def __get__(self, instance, cls):
        # print('get', self, instance, cls)
        if instance:
            return self.name
        else:
            return self

    def __set__(self, instance, value):
        # print('set', self, instance, value)
        if instance and isinstance(value, self._type):
            # setattr(instance, self.name, value)
            if not self.nullable and not value:
                raise AttributeError('This value must be not null!')
            self.name = value
        else:
            raise AttributeError('Wrong type of value!')

    def __delete__(self, instance):
        raise AttributeError("Can't delete attribute")


class CharField(BaseField):
    def __init__(self, required, nullable):
        BaseField.__init__(self, required, nullable)
        self._type = (str, unicode)


class ArgumentsField(BaseField):
    def __init__(self, required, nullable):
        # super(BaseField, self).__init__()
        BaseField.__init__(self, required, nullable)
        self._type = dict


class EmailField(CharField):
    def __init__(self, required=False, nullable=False):
        BaseField.__init__(self, required, nullable)
        self._type = (str, unicode)

    def __set__(self, instance, value):
        if '@' in value:
            BaseField.__set__(self, instance, value)
        else:
            raise AttributeError('This field must contain @!')


class PhoneField(CharField):
    pass


class DateField(CharField):
    pass


class BirthDayField(CharField):
    pass


class GenderField(BaseField):
    def __init__(self, required=False, nullable=False):
        BaseField.__init__(self, required, nullable)
        self._type = int


class ClientIDsField(BaseField):
    def __init__(self, required=False, nullable=False):
        BaseField.__init__(self, required, nullable)
        self._type = int


class ClientsInterestsRequest(object):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(object):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def __init__(self, first_name, last_name, email, phone, birthday, gender):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.birthday = birthday
        self.gender = gender

    def view_dict(self):
        print('view', self.__dict__.items(), dir(self), self.__getattribute__('email'))

    def print_instance_attributes(self):
        for attribute, value in self.__dict__.items():
            print(attribute, '=', value)



class Controller(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'path'):
            raise NotImplementedError("'Controller' subclasses should have a 'path' attribute")
        return Controller.__new__(cls, *args, **kwargs)


class MyMeta(type):
    ff = None
    def __call__(meta, name, bases, dct):
        newclass = super(MyMeta, meta).__new__(meta, name, bases, {})
        for key, value in dct.items():
            if not hasattr(meta, key) and key != '__metaclass__':
                try:
                    if value.required:
                        setattr(newclass, key, value)
                except:
                    pass
        from pprint import pprint
        pprint(newclass.__dict__)
        return newclass

    def __init__(cls, name, bases, dct):
        # print cls
        # print dct
        for key, value in dct.items():
            if not hasattr(cls, key) and key not in ['__metaclass__', 'is_admin']:
                try:
                    if value.required:
                        setattr(cls, key, value)
                except:
                    pass
        super(MyMeta, cls).__init__(name, bases, dct)


class MethodRequest(object):
    __metaclass__ = MyMeta

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
    # print(digest)
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code = None, None
    request = request['body']
    if request.method == 'online_score' and request.login != 'admin':
        data = request.arguments
        try:
            obj = OnlineScoreRequest(phone=data.phone,
                                     email=data.email,
                                     birthday=data.birthday,
                                     gender=data.gender,
                                     first_name=data.first_name,
                                     last_name=data.last_name)
            response = get_score(store, obj.phone, obj.email, obj.birthday, obj.gender, obj.first_name, obj.last_name)
            code = OK
        except Exception as ex:
            response = str(ex)
            code = BAD_REQUEST
    elif request.method == 'online_score':
        response = {"score": 42}
        code = OK
    elif request.method == 'clients_interests':
        response = get_interests(store, None)
        code = OK

    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_GET(self):
        print(self.headers)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            from collections import namedtuple
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
        except:
            code = BAD_REQUEST
        print(request)
        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                if check_auth(request):
                    try:
                        print(context, self.store)
                        response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                    except Exception, e:
                        logging.exception("Unexpected error: %s" % e)
                        code = INTERNAL_ERROR
                else:
                    code = FORBIDDEN
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
    # new_req = OnlineScoreRequest('olga', 'bel', 'fff@ddd', '445', '12/12/12', 'f')
    # print(new_req.email)
    # new_req.view_dict()
    # new_req.print_instance_attributes()
    # print(MethodRequest.cls_attr())
    niq_req = MethodRequest('admin22', 'admin', '', {}, 'ff')

    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=7080)
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