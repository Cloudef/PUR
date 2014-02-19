#!/usr/bin/env python3
# pylint: disable=line-too-long
'''light user manager'''

from lib.db.table import Sqlite3Table, Sqlite3Query

def hash_password(password, csrf):
    '''hash password with salt using csrf token as base salt'''
    from os import urandom
    from hashlib import sha512
    from binascii import b2a_hex
    salt = csrf + b2a_hex(urandom(24)).decode('UTF-8')
    return {'salt': salt,
            'password': sha512(password.encode('UTF-8') + salt.encode('UTF-8')).hexdigest()}

class Sqlite3User(object):
    '''
    SQLite3 User database
    '''
    def __init__(self, db_file='userdata/db/users.db', *args, **kwargs):
        super(Sqlite3User, self).__init__(*args, **kwargs)
        self.database = db_file
        serialize = ['sessions']
        columns = ['name', 'password', 'salt', 'session', 'sessions', 'email']
        self.users = Sqlite3Table('users', columns, serialize, db_file)

    def test_password(self, username, password):
        '''test password against password in database'''
        data = self.get_user(username)
        if not data:
            return False
        from hashlib import sha512
        return data['password'] == sha512(password.encode('UTF-8') + data['salt'].encode('UTF-8')).hexdigest()

    def set_user(self, user, data):
        '''set user data to database'''
        return self.users.set(data, Sqlite3Query('WHERE name = ?', (user,)))

    def get_user(self, user, session=None, pass_csrf=None, email=None):
        '''get, update or create user in database'''
        save = False
        query = Sqlite3Query('WHERE name = ?', (user,))
        data = self.users.get_one(query)
        if not data:
            if session and pass_csrf:
                self.users.insert({'name': user, 'session': session})
                data = self.users.get_one(query)
                if not data:
                    raise IOError('Failed to insert user')
                save = True
            else:
                return None

        if session and session != data['session']:
            data['session'] = session
            save = True

        if session and (not data['sessions'] or session not in data['sessions']):
            if not data['sessions']:
                data['sessions'] = [session]
            else:
                data['sessions'].append(session)

        if pass_csrf:
            pass_salt = hash_password(pass_csrf[0], pass_csrf[1])
            if data['password'] != pass_salt['password'] and \
               data['salt'] != pass_salt['salt']:
                data['salt'] = pass_salt['salt']
                data['password'] = pass_salt['password']
                save = True

        if email and data['email'] != email:
            data['email'] = email

        if save:
            self.set_user(user, data)
        return data

    def get_user_count(self):
        '''get number of users from database'''
        return self.users.count

    def search_users(self, query):
        '''search users from database'''
        return self.users.get(Sqlite3Query('WHERE name MATCH ?', (query,)))

#  vim: set ts=8 sw=4 tw=0 :
