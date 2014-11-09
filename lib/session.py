#!/usr/bin/env python3
# pylint: disable=line-too-long
'''light session manager'''

import lib.bottle as bottle
import time, functools, os

def _gen_csrf():
    '''generate csrf token'''
    from binascii import b2a_hex
    return b2a_hex(os.urandom(4)).decode('UTF-8')

def regenerate_csrf(session_manager):
    '''regenerate csrf for session'''
    data = session_manager.get_session()
    data['CSRF'] = _gen_csrf()
    session_manager.save(data)
    return data

def check_csrf(session_manager, cbfunc, method=None):
    '''check csrf token decorator'''
    def decorator(handler, *a, **ka):
        # pylint: disable=unused-argument, missing-docstring
        @functools.wraps(handler)
        def dummy_check_csrf(*a, **ka):
            '''check for valid csrf'''
            if method and bottle.request.method not in method:
                return handler(*a, **ka)
            csrf = ka['csrf'] if 'csrf' in ka else bottle.request.forms.get('CSRF')
            data = session_manager.get_session()
            if not csrf or data.get('CSRF') != csrf:
                cbfunc()
            return handler(*a, **ka)
        return dummy_check_csrf
    return decorator

def valid_session(session_manager, cbfunc):
    '''check for valid session, otherwise redirect'''
    def decorator(handler, *a, **ka):
        # pylint: disable=unused-argument, missing-docstring
        @functools.wraps(handler)
        def dummy_check_auth(*a, **ka):
            data = session_manager.get_session()
            if not data.get('valid'):
                cbfunc()
            if data.get('name'):
                bottle.request.environ['REMOTE_USER'] = data['name']
            return handler(*a, **ka)
        return dummy_check_auth
    return decorator

def make_session_id():
    '''create session id'''
    from uuid import uuid4
    return str(uuid4())

class BaseSession(object):
    # pylint: disable=abstract-class-little-used
    '''
    Base class which implements some of the basic functionality required for
    session managers.  Cannot be used directly.

    :param cookie_expires: Expiration time of session ID cookie, either `None`
            if the cookie is not to expire, a number of seconds in the future,
            or a datetime object.  (default: 30 days)
    '''
    def __init__(self, session_dir='userdata/session', cookie_expires=86400 * 30):
        self.session_dir = session_dir
        self.cookie_expires = cookie_expires

    def load(self, sessionid):
        '''load session internally'''
        raise NotImplementedError

    def remove(self, sessionid):
        '''remove session'''
        raise NotImplementedError

    def save(self, data):
        '''save session'''
        raise NotImplementedError

    def allocate_new_session_id(self):
        '''allocate new session id'''
        #  retry allocating a unique sessionid
        for dummy in range(100):
            sessionid = make_session_id()
            if not self.load(sessionid):
                return sessionid
        raise ValueError('Unable to allocate unique session')

    def regenerate_session(self, data):
        '''regenerate session using new id'''
        if not data:
            raise ValueError('Session does not not exist')
        oldid = data['sessionid']
        data['sessionid'] = self.allocate_new_session_id()
        self.save(data)
        self.remove(oldid)
        bottle.response.set_cookie(
                'sessionid', data['sessionid'], path='/',
                expires=(int(time.time()) + self.cookie_expires))
        return data

    def get_session(self, load_session_id=None):
        '''get or create new session'''
        # existing session requested
        if load_session_id:
            return self.load(load_session_id)

        # should session be saved at end?
        save = False

        #  get existing or create new session identifier
        sessionid = bottle.request.get_cookie('sessionid')
        if not sessionid:
            sessionid = self.allocate_new_session_id()
            bottle.response.set_cookie(
                    'sessionid', sessionid, path='/',
                    expires=(int(time.time()) + self.cookie_expires))

        #  load existing or create new session
        data = self.load(sessionid)
        if not data:
            data = {'sessionid': sessionid, 'valid': False}
            save = True

        # make sure we have CSRF token
        if 'CSRF' not in data:
            data['CSRF'] = _gen_csrf()

        if data['valid']:
            # Cache agent
            data['IP'] = bottle.request.environ.get('REMOTE_ADDR')
            agent = bottle.request.headers.get('User-Agent')
            if agent != data.get('agent'):
                from lib.uasparser import UASparser
                parser = UASparser(self.session_dir)
                data['client'] = parser.parse(agent)
                data['agent'] = agent
                save = True

        # save session if requested
        if save:
            self.save(data)
        return data

class PickleSession(BaseSession):
    '''
        Class which stores session information in the file-system.
    '''

    def __init__(self, *args, **kwargs):
        super(PickleSession, self).__init__(*args, **kwargs)

    def load(self, sessionid):
        import pickle
        fname = os.path.join(self.session_dir, '{}.session'.format(sessionid))
        if not os.path.exists(fname):
            return None
        with open(fname, 'rb') as fle:
            session = pickle.load(fle)
        return session

    def remove(self, sessionid):
        fname = os.path.join(self.session_dir, '{}.session'.format(sessionid))
        if not os.path.exists(fname):
            return None
        os.remove(fname)

    def save(self, data):
        import pickle
        fname = os.path.join(self.session_dir, '{}.session'.format(data['sessionid']))
        tmpname = '{}.tmp'.format(fname)
        with open(tmpname, 'wb') as fle:
            pickle.dump(data, fle)
        os.rename(tmpname, fname)

#  vim: set ts=8 sw=4 tw=0 :
