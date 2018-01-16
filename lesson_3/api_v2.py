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
        BaseField.__init__(self, required, nullable)
        self._type = dict


class EmailField(CharField):
    def __init__(self, required=False, nullable=False):
        CharField.__init__(self, required, nullable)
        self._type = (str, unicode)

    def __set__(self, instance, value):
        if '@' in value:
            CharField.__set__(self, instance, value)
        else:
            raise AttributeError('Email field must contain @!')


class PhoneField(CharField):
    def __set__(self, instance, value):
        if value.startswith('7') and len(value) == 11:
            CharField.__set__(self, instance, value)
        else:
            raise AttributeError('Phone field must starts with 7 with length 11!')


class DateField(CharField):
    def __set__(self, instance, value):
        try:
            datetime.datetime.strptime(value, '%d.%m.%Y')
        except Exception as ex:
            raise AttributeError('Birthday date field must be in format DD.MM.YYYY, error: {}'.format(str(ex)))
        CharField.__set__(self, instance, value)


class BirthDayField(CharField):
    def __set__(self, instance, value):
        try:
            date_now = datetime.datetime.utcnow()
            birth_date = datetime.datetime.strptime(value, '%d.%m.%Y')
            diff_years = (date_now - birth_date).days / 365
        except Exception as ex:
            raise AttributeError('Birthday date field must be in format DD.MM.YYYY, error: {}'.format(str(ex)))
        if diff_years < 70:
            CharField.__set__(self, instance, value)
        else:
            raise AttributeError('Birthday date must be no more than 70 years ago!')


class GenderField(BaseField):
    def __init__(self, required=False, nullable=False):
        BaseField.__init__(self, required, nullable)
        self._type = int

    def __set__(self, instance, value):
        if value in [0, 1, 2]:
            BaseField.__set__(self, instance, value)
        else:
            raise AttributeError('Gender field must be only 0, 1, 2')


class ClientIDsField(BaseField):
    def __init__(self, required=False, nullable=False):
        BaseField.__init__(self, required, nullable)
        self._type = list


class Controller(object):
    def __new__(self, *args, **kwargs):
        for key, value in self.__dict__.items():
            if isinstance(value, BaseField):
                val = kwargs.get(key, None)
                # print key, value, val
                if value.required and val is None:
                    raise Exception('{} attribute is required!'.format(key))
        return super(Controller, self).__new__(self)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class ClientsInterestsRequest(Controller):
    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(Controller):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        # phone-email, first_name-last_name, birthday-gender
        # print not (self.phone and self.email)
        if not (self.phone and self.email) and \
            not (self.first_name and self.last_name) and \
            not (self.birthday and self.gender):
            raise Exception('Have not compare pair of data')


class MethodRequest(Controller):

    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


class RequestAPI(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    # def __getitem__(self, item):
    #     return self.__dict__[item]


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
    request_user = MethodRequest(**vars(request))
    if request.method == 'online_score' and not request_user.is_admin:
        data = request.arguments
        try:
            obj = OnlineScoreRequest(**data)
            obj.validate()
            response = get_score(store, obj.phone, obj.email, obj.birthday, obj.gender, obj.first_name, obj.last_name)
            code = OK
        except Exception as ex:
            response = str(ex)
            code = BAD_REQUEST
    elif request.method == 'online_score':
        response = {"score": 42}
        code = OK
    elif request.method == 'clients_interests':
        clients = ClientsInterestsRequest(**request.arguments)
        response = {}
        for client in clients.client_ids:
            client_response = get_interests(store, client)
            response.update([(str(client), client_response)])
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
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            # request = json.loads(data_string, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))
            dict_data = json.loads(data_string)
            request = RequestAPI(**dict_data)
        except:
            code = BAD_REQUEST
        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                if check_auth(request):
                    try:
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
