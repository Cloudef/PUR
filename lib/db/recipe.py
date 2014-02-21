#!/usr/bin/env python3
# pylint: disable=line-too-long
"""light recipe manager"""

from lib.db.table import Sqlite3Table, Sqlite3Query

def _delete_recipedir(recipedir):
    '''delete recipe directory on filesystem'''
    import os, shutil
    dirname = os.path.dirname(recipedir)
    if os.path.exists(recipedir):
        shutil.rmtree(recipedir)
    if os.path.exists(dirname) and not os.listdir(dirname):
        shutil.rmtree(dirname)

def _populate_recipe_dynamic_values(data):
    '''populate recipe object with dynamic values'''
    prefix = data['pkgname']
    if data.get('parent'):
        prefix = '{}/{}'.format(prefix, data['revision'])
    data['recipepath'] = '/dl/{}/PNDBUILD'.format(prefix)
    data['tarpath'] = '/dl/{}/{}-{}-{}.src.tar.gz'.format(prefix, data['pkgname'], data['pkgver'], data['pkgrel'])
    data['recipedir'] = 'userdata/recipes/{}/{}'.format(data['pkgname'], data['directory'])
    return data

class Sqlite3Recipe(object):
    '''
    SQLite3 Recipe database
    '''
    def __init__(self, db_file='userdata/db/recipes.db', *args, **kwargs):
        super(Sqlite3Recipe, self).__init__(*args, **kwargs)
        self.database = db_file
        self.recipe_copy_over = ['contributors', 'revisions', 'revision']
        self.revision_copy_over = ['revision']
        self.accept_copy_over = ['revision', 'directory', 'datemodify',
                'pkgname', 'pndcategory', 'pkgver', 'pkgrel', 'pkgdesc', 'url', 'license', 'depend',
                'makedepend', 'pndexec', 'source']

        shared_serialize = ['license', 'depend', 'makedepend', 'pndexec', 'source']
        shared_columns = ['maintainer', 'user', 'revision', 'directory', 'datemodify',
                          'pkgname', 'pndcategory', 'pkgver', 'pkgrel', 'pkgdesc', 'url', 'license', 'depend',
                          'makedepend', 'pndexec', 'source']

        columns = ['contributors', 'revisions'] + shared_columns
        serialize = ['contributors', 'revisions'] + shared_serialize
        self.recipes = Sqlite3Table('recipes', columns, serialize, self.database)

        columns = ['parent'] + shared_columns
        serialize = shared_serialize
        self.revisions = Sqlite3Table('revisions', columns, serialize, self.database)

        self.comments = Sqlite3Table('comments', ['id', 'pkgname', 'revision', 'user', 'date', 'comment'], [], self.database)

    def modified(self):
        '''get modified time of database'''
        import os
        return os.path.getmtime(self.database)

    def allocate_revision(self):
        '''return revision number (fs friendly time)'''
        # pylint: disable=no-self-use
        import time
        return time.strftime("%Y%m%d%H%M%S")

    def remove_revision_from_parent(self, recipe, revision):
        '''remove revision from parent recipe'''
        data = self.get_recipe(recipe)
        if not data:
            raise Exception('No such recipe')
        data['revisions'] = [x for x in data['revisions'] if x['revision'] != revision]
        self.set_recipe(recipe, data)

    def remove_revisions(self, query, delete_comments=True, delete_dir=True):
        '''remove revisions using query'''
        revisions = self.revisions.get(query)
        self.revisions.delete(query)
        for rev in revisions:
            rev = _populate_recipe_dynamic_values(rev)
            if delete_comments:
                query = Sqlite3Query('WHERE pkgname = ? and revision = ?', (rev['pkgname'], rev['revision']))
                self.comments.delete(query)
            if delete_dir:
                _delete_recipedir(rev['recipedir'])
            self.remove_revision_from_parent(rev['pkgname'], rev['revision'])

    def remove_recipe(self, recipe, revision=None, remove_revisions=False, remove_comments=False):
        '''remove recipe from disk and db'''
        data = self.get_recipe(recipe, revision)
        if not data:
            raise Exception('No such recipe to remove')

        query = Sqlite3Query('WHERE pkgname = ? and revision = ?', (data['pkgname'], data['revision']))
        if data.get('parent'):
            self.remove_revision_from_parent(data['pkgname'], data['revision'])
        elif remove_revisions:
            rev_query = Sqlite3Query('WHERE pkgname = ?', (data['pkgname'],))
            self.remove_revisions(rev_query)

        if remove_comments:
            self.comments.delete(query)

        if data.get('parent'):
            self.revisions.delete(query)
        else:
            self.recipes.delete(query)
        _delete_recipedir(data['recipedir'])

    def remove_comment(self, recipe, revision, cid):
        '''remove comment from recipe by comment id'''
        query = Sqlite3Query('WHERE pkgname = ? and id = ?', (recipe, cid))
        if revision:
            query.append('and revision = ?', (revision,))
        self.comments.delete(query)

    def create_comment(self, pkgname, revision, user, comment):
        '''create new comment'''
        # pylint: disable=unused-argument, too-many-arguments
        import time
        dic = locals()
        del dic['self']
        dic['id'] = self.allocate_revision()
        dic['date'] = time.strftime("%Y-%m-%d %H:%M")
        self.comments.insert(dic)

    def recipe_add_revision(self, recipe, data):
        '''add revision to recipe'''
        parent = self.get_recipe(recipe)
        if not parent:
            raise Exception('No such recipe')
        revdic = {'revision': data['revision'], 'datemodify': data['datemodify'], 'user': data['user']}
        if parent['revisions'] and revdic not in parent['revisions']:
            parent['revisions'].append(revdic)
        else:
            parent['revisions'] = [revdic]
        self.set_recipe(recipe, parent)

    def accept_revision(self, recipe, revision):
        '''accept revision of recipe'''
        revision = self.get_recipe(recipe, revision)
        if not revision or not revision.get('parent'):
            raise Exception('no such revision')
        parent = self.get_recipe(recipe, revision['parent'])
        if not parent:
            raise Exception('parent was not found')

        _delete_recipedir(parent['recipedir'])

        query = Sqlite3Query('WHERE pkgname = ? and revision = ?', (parent['pkgname'], parent['revision']))
        self.comments.set({'revision':revision['revision']}, query)

        query = Sqlite3Query('WHERE pkgname = ?', (parent['pkgname'],))
        self.remove_revisions(query, delete_comments=False, delete_dir=False)

        for key in self.accept_copy_over:
            parent[key] = revision[key]
        parent['revisions'] = None

        if parent['contributors'] and revision['user'] not in parent['contributors']:
            parent['contributors'].append(revision['user'])
        else:
            parent['contributors'] = [revision['user']]

        self.set_recipe(recipe, parent)

    def create_recipe(self, user, revision, data):
        '''insert recipe in database'''
        import time
        data['user'] = user
        data['revision'] = revision
        data['directory'] = revision
        data['datemodify'] = time.strftime("%Y-%m-%d %H:%M", time.strptime(revision, "%Y%m%d%H%M%S"))

        parent = self.get_recipe(data['pkgname'])
        if parent and parent['maintainer'] == user:
            for key in self.recipe_copy_over:
                data[key] = parent[key]
            self.remove_recipe(parent['pkgname'])
            parent = None

        if parent:
            query = Sqlite3Query('WHERE pkgname = ? and user = ?', (data['pkgname'], user))
            oldrev = self.revisions.get_one(query)
            if oldrev:
                for key in self.revision_copy_over:
                    data[key] = oldrev[key]
                self.remove_revisions(query)
            data['maintainer'] = parent['maintainer']
            data['parent'] = parent['revision']
            self.revisions.insert(data)
            data = self.get_recipe(data['pkgname'], data['revision'])
        else:
            data['maintainer'] = user
            self.recipes.insert(data)
            data = self.get_recipe(data['pkgname'], None)

        if not data:
            raise IOError('Failed to insert recipe')

        if parent:
            self.recipe_add_revision(parent['pkgname'], data)
        return data

    def set_maintainer(self, recipe, maintainer):
        '''set maintainer for recipe'''
        query = Sqlite3Query('WHERE pkgname = ?', (recipe,))
        self.recipes.set({'maintainer': maintainer, 'user': maintainer}, query)
        self.revisions.set({'maintainer': maintainer}, query)

    def set_recipe(self, recipe, data):
        '''set recipe data in database'''
        query = Sqlite3Query('WHERE pkgname = ?', (recipe,))
        return self.recipes.set(data, query)

    def set_revision(self, recipe, revision, data):
        '''set recipe revision data in database'''
        query = Sqlite3Query('WHERE pkgname = ? and revision = ?', (recipe, revision))
        return self.revisions.set(data, query)

    def get_recipe_count(self):
        '''get number of recipes from database'''
        return self.recipes.count

    def get_recipe(self, recipe, revision=None):
        '''get recipe from database'''
        data = None
        query = Sqlite3Query('WHERE pkgname = ? and revision = ?', (recipe, revision))
        if revision:
            data = self.revisions.get_one(query)
        if not data:
            data = self.recipes.get_one(query.set('WHERE pkgname = ?', (recipe,)))
        return _populate_recipe_dynamic_values(data) if data else None

    def get_comment(self, recipe, revision, cid):
        '''get comment from recipe'''
        query = Sqlite3Query('WHERE pkgname = ? AND revision = ? and id = ?', (recipe, revision, cid))
        return self.comments.get_one(query)

    def get_recipes(self, user=None, contrib=None, limit=None):
        '''get recipes from database'''
        query = Sqlite3Query()
        if user:
            query.append_with_clause('WHERE', 'user = ?', (user,))
        if contrib:
            query.append_with_clause('WHERE', 'contributors MATCH ?', ("'{}'".format(contrib),))
        query.append('ORDER BY pkgname')
        if limit:
            query.append('LIMIT ?', (limit,))
        return self.recipes.get(query, _populate_recipe_dynamic_values)

    def get_revisions(self, user=None):
        '''get revisions from database'''
        query = Sqlite3Query()
        if user:
            query.append_with_clause('WHERE', 'user = ?', (user,))
        query.append('ORDER BY pkgname')
        return self.revisions.get(query, _populate_recipe_dynamic_values)

    def get_comments(self, recipe, revision=None, limit=None):
        '''get comments from database'''
        query = Sqlite3Query('WHERE pkgname = ?', (recipe,))
        if revision:
            query.append('and revision = ?', (revision,))
        query.append('ORDER BY id DESC')
        if limit:
            query.append('LIMIT ?', (limit,))
        return self.comments.get(query)

    def search_recipes(self, query):
        '''search recipes from database'''
        query = Sqlite3Query('WHERE pkgname MATCH ? or pkgdesc MATCH ?', (query, query))
        query.append('ORDER BY pkgname')
        return self.recipes.get(query, _populate_recipe_dynamic_values)

#  vim: set ts=8 sw=4 tw=0 :
