#!/usr/bin/env python3
# pylint: disable=line-too-long
'''sqlite3 table wrapper'''

import sqlite3

class Sqlite3Query(object):
    '''
    Class representing SQLite query
    '''

    def __init__(self, query=None, qargs=None, *args, **kwargs):
        super(Sqlite3Query, self).__init__(*args, **kwargs)
        self.query = query
        self.qargs = qargs

    def set(self, query, qargs):
        '''set query'''
        self.query = query
        self.qargs = qargs
        return self

    def append(self, query, qargs=None):
        '''append to query'''
        self.query = query if not self.query else '{} {}'.format(self.query, query)
        if qargs:
            self.qargs = qargs if not self.qargs else self.qargs + qargs
        return self

    def append_with_clause(self, clause, query, qargs=None):
        '''append with clause if there was nothing before'''
        if clause not in query:
            self.append(clause)
        return self.append(query, qargs)

    def prepend(self, query, qargs=None):
        '''prepend to query'''
        self.query = query if not self.query else '{} {}'.format(query, self.query)
        if qargs:
            self.qargs = qargs if not self.qargs else qargs + self.qargs
        return self

    def execute(self, cur):
        '''execute query'''
        print(self.query)
        cur.execute(self.query, self.qargs if self.qargs else ())

    def copy(self):
        '''copy query'''
        return Sqlite3Query(self.query, self.qargs)

def _dict_factory(cur, row):
    '''generate dictionary from sql query'''
    dic = {}
    for idx, col in enumerate(cur.description):
        dic[col[0]] = row[idx]
    return dic

def _match_pattern(subvalue, value):
    '''MATCH override'''
    if not subvalue or not value:
        return False
    subvalue = subvalue.lower()
    value = value.lower()
    if subvalue in value:
        return True
    for split in subvalue.split():
        if split in value:
            return True
    return False

class Sqlite3Table(object):
    '''
    Class representing SQLite3 table
    '''

    def __init__(self, name, columns, serialize, db_file, *args, **kwargs):
        super(Sqlite3Table, self).__init__(*args, **kwargs)
        if len(name) > 4 and name[-4:] == '_tmp':
            raise ValueError('name should not end with _tmp suffix')
        self.name = name
        self.columns = columns
        self.serialize = serialize
        self.database = db_file
        self.count = 0
        self._initialize_table()
        self._update_count()

    def _update_count(self):
        '''update count of rows in table'''
        con = sqlite3.connect(self.database)
        cur = con.cursor()
        cur.execute('SELECT Count(*) FROM {}'.format(self.name))
        ret = cur.fetchone()
        self.count = ret[0] if ret else 0
        con.close()

    def _should_update(self):
        '''
        check if table should be updated
        returns list of columns that should be carried over if update is needed
        '''
        oldcolumns = []
        con = sqlite3.connect(self.database)
        cur = con.cursor()
        cur.execute('PRAGMA table_info({})'.format(self.name))
        for column in cur.fetchall():
            oldcolumns.append(column[1])
        for name in self.columns:
            if name not in oldcolumns:
                return [x for x in oldcolumns if x in self.columns]
        for name in oldcolumns:
            if name not in self.columns:
                return [x for x in oldcolumns if x in self.columns]
        con.close()
        return None

    def _initialize_table(self):
        '''initialize table'''
        con = sqlite3.connect(self.database)
        cur = con.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS {} ({})'.format(self.name, ','.join(self.columns)))
        con.close()

        updatecolumns = self._should_update()
        if updatecolumns:
            print('==> updating {} ({})'.format(self.name, ', '.join(updatecolumns)))
            con = sqlite3.connect(self.database)
            cur = con.cursor()
            cur.execute('ALTER TABLE {} RENAME TO {}_tmp'.format(self.name, self.name))
            cur.execute('CREATE TABLE {} ({})'.format(self.name, ','.join(self.columns)))
            try:
                updatecolumns = ','.join(updatecolumns)
                cur.execute('INSERT INTO {} ({}) SELECT {} from {}_tmp'.format(self.name, updatecolumns, updatecolumns, self.name))
                cur.execute('DROP TABLE {}_tmp'.format(self.name))
            except sqlite3.OperationalError as exc:
                print('==> {}: reverting...'.format(exc))
                cur.execute('DROP TABLE {}'.format(self.name))
                cur.execute('ALTER TABLE {}_tmp RENAME TO {}'.format(self.name, self.name))
            con.commit()
            con.close()

    def _deserialize(self, data):
        '''deserialize data from sql query'''
        if not data:
            return data
        import ast
        for key in self.serialize:
            if not data[key]:
                continue
            data[key] = ast.literal_eval(data[key])
        return data

    def _serialize_insert(self, data):
        '''serialize data to insert sql query'''
        args = []
        keys = []
        values = []
        for key, value in data.items():
            if key not in self.columns:
                continue
            if key in self.serialize:
                value = '{}'.format(value)
            args.append('?')
            keys.append(key)
            values.append(value)
        return (args, keys, values)

    def delete(self, query):
        '''delete row from table'''
        query = query.copy().prepend('DELETE FROM {}'.format(self.name))
        con = sqlite3.connect(self.database)
        cur = con.cursor()
        query.execute(cur)
        con.commit()
        con.close()
        self._update_count()

    def insert(self, data):
        '''insert new row to table'''
        ret = self._serialize_insert(data)
        query = Sqlite3Query('INSERT INTO {} ({}) VALUES ({})'.format(self.name, ','.join(ret[1]), ','.join(ret[0])), ret[2])
        con = sqlite3.connect(self.database)
        cur = con.cursor()
        query.execute(cur)
        con.commit()
        con.close()
        self.count += 1

    def set(self, data, query):
        '''set row data in table'''
        save = False
        matches = self.get(query)
        if len(matches) == 1:
            data = {k: v for k, v in data.items() if k not in matches[0] or matches[0][k] != v}

        con = sqlite3.connect(self.database)
        cur = con.cursor()
        for key, value in data.items():
            if key not in self.columns:
                continue
            if key in self.serialize:
                value = '{}'.format(value)
            nquery = query.copy().prepend('UPDATE {} SET {} = ?'.format(self.name, key), (value,))
            nquery.execute(cur)
            save = True

        if save:
            con.commit()
        con.close()

    def get(self, query, result_fun=None):
        '''get row data in table'''
        query = query.copy().prepend('SELECT * FROM {}'.format(self.name))
        con = sqlite3.connect(self.database)
        con.create_function('match', 2, _match_pattern)
        con.row_factory = _dict_factory
        cur = con.cursor()
        query.execute(cur)
        ret = []
        while 1:
            data = cur.fetchone()
            if not data:
                break
            if result_fun:
                ret.append(result_fun(self._deserialize(data)))
            else:
                ret.append(self._deserialize(data))
        con.close()
        return ret

    def get_one(self, query):
        '''get first row data in table'''
        data = self.get(query.copy().append('LIMIT 1'))
        return data[0] if data else None

#  vim: set ts=8 sw=4 tw=0 :
