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
    # pylint: disable=too-many-public-methods

    def __init__(self, db_file='userdata/db/recipes.db', *args, **kwargs):
        super(Sqlite3Recipe, self).__init__(*args, **kwargs)
        self.database = db_file
        self.recipe_copy_over = ['contributors', 'revisions', 'revision']
        self.revision_copy_over = ['revision']
        self.accept_copy_over = ['revision', 'directory', 'datemodify',
                'pkgname', 'pndcategory', 'pkgver', 'pkgrel', 'pkgdesc', 'url', 'license', 'depend',
                'makedepend', 'pndexec', 'source']

        shared_serialize = ['license', 'depend', 'makedepend', 'pndexec', 'source']
        shared_columns = ['maintainer', 'user', 'revision', 'directory', 'datemodify', 'md5',
                          'pkgname', 'pndcategory', 'pkgver', 'pkgrel', 'pkgdesc', 'url', 'license', 'depend',
                          'makedepend', 'pndexec', 'source']

        columns = ['contributors', 'revisions'] + shared_columns
        serialize = ['contributors', 'revisions'] + shared_serialize
        self.recipes = Sqlite3Table('recipes', columns, serialize, self.database)

        columns = ['diff', 'changes', 'parent'] + shared_columns
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

    def remove_recipe(self, recipe, remove_revisions=False, remove_comments=False):
        '''remove recipe from disk and db'''
        data = self.get_recipe(recipe)
        if not data:
            raise Exception('No such recipe to remove')

        query = Sqlite3Query('WHERE pkgname = ? and revision = ?', (data['pkgname'], data['revision']))
        if remove_revisions:
            rev_query = Sqlite3Query('WHERE pkgname = ?', (data['pkgname'],))
            self.remove_revisions(rev_query)

        if remove_comments:
            self.comments.delete(query)

        self.recipes.delete(query)
        _delete_recipedir(data['recipedir'])

    def remove_revision(self, recipe, revision, remove_comments=False):
        '''remove revision from disk and db'''
        data = self.get_revision(recipe, revision)

        if not data:
            raise Exception('No such revision to remove')

        query = Sqlite3Query('WHERE pkgname = ? and revision = ?', (data['pkgname'], data['revision']))
        self.remove_revision_from_parent(data['pkgname'], data['revision'])

        if remove_comments:
            self.comments.delete(query)

        self.revisions.delete(query)
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
        revdic = {'revision': data['revision'], 'datemodify': data['datemodify'], 'user': data['user'],
                  'changes': data['changes'], 'diff': data['diff']}
        if parent['revisions'] and revdic not in parent['revisions']:
            parent['revisions'].append(revdic)
        else:
            parent['revisions'] = [revdic]
        self.set_recipe(recipe, parent)

    def accept_revision(self, recipe, revision):
        '''accept revision of recipe'''
        revision = self.get_revision(recipe, revision)
        if not revision or not revision.get('parent'):
            raise Exception('no such revision')
        parent = self.get_recipe(recipe)
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

    def create_recipe(self, user, revision, data, md5):
        '''insert recipe in database'''
        import time
        data['user'] = user
        data['contributors'] = [user]
        data['revision'] = revision
        data['directory'] = revision
        data['datemodify'] = time.strftime("%Y-%m-%d %H:%M", time.strptime(revision, "%Y%m%d%H%M%S"))
        data['md5'] = md5

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
            data = self.get_revision(data['pkgname'], data['revision'])
        else:
            data['maintainer'] = user
            self.recipes.insert(data)
            data = self.get_recipe(data['pkgname'])

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

    def get_recipe(self, recipe):
        '''get recipe from database'''
        data = self.recipes.get_one(Sqlite3Query('WHERE pkgname = ?', (recipe,)))
        return _populate_recipe_dynamic_values(data) if data else None

    def get_revision_count(self):
        '''get number of revisions from database'''
        return self.revisions.count

    def get_revision(self, recipe, revision):
        '''get revision from database'''
        data = self.revisions.get_one(Sqlite3Query('WHERE pkgname = ? and revision = ?', (recipe, revision)))
        return _populate_recipe_dynamic_values(data) if data else None

    def get_comment(self, recipe, revision, cid):
        '''get comment from recipe'''
        query = Sqlite3Query('WHERE pkgname = ? AND revision = ? and id = ?', (recipe, revision, cid))
        return self.comments.get_one(query)

    def get_comment_count(self):
        '''get number of comments from database'''
        return self.comments.count

    def query_recipes(self, fmt, args=None):
        '''query recipes from database'''
        return self.recipes.get(Sqlite3Query(fmt, args), _populate_recipe_dynamic_values)

    def query_recipes_count(self, fmt, args=None):
        '''get count for query'''
        return self.recipes.qcount(Sqlite3Query(fmt, args))

    def query_revisions(self, fmt, args=None):
        '''query revisions from database'''
        return self.revisions.get(Sqlite3Query(fmt, args), _populate_recipe_dynamic_values)

    def query_revisions_count(self, fmt, args=None):
        '''get count for query'''
        return self.revisions.qcount(Sqlite3Query(fmt, args))

    def query_comments(self, fmt, args=None):
        '''query comments from database'''
        return self.comments.get(Sqlite3Query(fmt, args))

    def query_comments_count(self, fmt, args=None):
        '''get count for query'''
        return self.comments.qcount(Sqlite3Query(fmt, args))

    def md5_duplicate_exists(self, md5):
        '''check for duplicate recipes'''
        if self.query_recipes('WHERE md5 = ? LIMIT 1', (md5,)):
            return True
        if self.query_revisions('WHERE md5 = ? LIMIT 1', (md5,)):
            return True
        return False

#  vim: set ts=8 sw=4 tw=0 :
