#!/usr/bin/env python3
# pylint: disable=line-too-long
'''PND user repository'''

import os, re
import lib.bottle as bottle
import lib.session as session
import lib.pndbuild as pndbuild
import lib.replace as replace
from lib.header import supported_request, supported_language
from lib.db.user import Sqlite3User
from lib.db.recipe import Sqlite3Recipe
from lib.bottle import abort
from lib.bottle import route, hook, redirect
from lib.bottle import request
from lib.bottle import BaseTemplate, template, static_file

# settings
ACCEPT = ['text/html', 'application/json']
TRANSLATIONS = ['en']
VERSION = 'v1.0.0'
STYLES = ['moe', 'light', 'dark']
LEVELS = {'user': 0, 'contributor': 1, 'moderator': 98, 'admin': 99}
OPT = {'style': 'dark', 'server': 'auto', 'port': 9002}
BETA = True

# session managment
SESSION = None
SESSIONMANAGER = session.PickleSession()

# user managment
USER = None
USERMANAGER = Sqlite3User()

# recipe managment
RECIPEMANAGER = Sqlite3Recipe()

# markup
MLURLTABLE = {'PNDPS': '/standards'}

# regex
PKGNAMEREX = re.compile("^[a-z0-9@._+-]*$")

try:
    # pylint: disable=import-error
    import config
    if 'server' in config.__dict__:
        OPT['server'] = config.server
    if 'port' in config.__dict__:
        OPT['port'] = config.port
except ImportError as exc:
    print("Configuration module was not loaded!")

# setup gettext
_ = None
def set_language(lang):
    '''set language for page'''
    # pylint: disable=global-statement
    global _
    if lang == 'en' or lang not in TRANSLATIONS:
        lang = 'en'
        _ = lambda x: x
    else:
        import gettext
        try:
            locale = gettext.translation('messages', 'locale', [lang])
            if locale:
                _ = locale.gettext
        except IOError:
            _ = lambda x: x

    # translate site navigation links
    navsites = []
    navsites.append({'name': _('PUR Home'), 'url': '/'})
    navsites.append({'name': _('Recipes'), 'url': '/recipes'})
    if not USER:
        navsites.append({'name': _('Register'), 'url': '/register'})
        navsites.append({'name': _('Login'), 'url': '/login'})
    else:
        navsites.append({'name': _('My Recipes'), 'url': '/user/{}/recipes'.format(USER['name'])})
        navsites.append({'name': _('My Account'), 'url': '/user/{}/edit'.format(USER['name'])})
        navsites.append({'name': _('Logout'), 'url': '/logout', 'csrf': True})
    BaseTemplate.defaults['PURNAVSITES'] = navsites

def js_translations(key):
    '''request javascript translations'''
    js_strings = {
        'register': {
            'username_length': _('Username must have at least {0} characters'),
            'password_length': _('Password must have at least {0} characters'),
            'password_confirm': _('Passwords must match'),
            'email': _('Enter a valid e-mail')
        },
        'upload': {
            'CSRF': SESSION['CSRF'],
            'file_size': _('File is too big. (8MB max)'),
            'upload': _('Upload'),
            'cancel': _('Cancel'),
            'upload_cancel': _('Upload canceled'),
            'no_response': _('No response from server...'),
        },
    }
    return js_strings.get(key)

def js_togglable(header, content, right=None, hidden=False):
    '''create togglable element'''
    return bottle.template('togglable', header=header, content=content, right=right, hidden=hidden)

def is_json_request():
    '''is json request?'''
    if 'Accept' in request.headers and supported_request(request.headers['Accept'], ACCEPT) == 'application/json':
        return True
    return False

def is_ajax_request():
    '''is ajax request?'''
    if 'X-Requested-With' in request.headers and request.headers['X-Requested-With'] == 'XMLHttpRequest':
        return True
    return False

def replace_togglable_code(expr, start, end, data):
    '''replace code block found by iter_callback'''
    lang = expr.group(1)
    code = expr.group(2)
    header = '{} {}'.format(lang, _('code')) if lang else _('Code')
    return replace.replace_range(data, start, end, '</pre>{}<pre>'.format(js_togglable(header, replace.syntax(code, lang), hidden=True)))

def replace_recipe(expr, start, end, data):
    '''replace recipe block found by iter_callback'''
    recipe = expr.group(1)
    if RECIPEMANAGER.get_recipe(recipe):
        return replace.replace_range(data, start, end, replace.html_link('/recipe/{}'.format(recipe), recipe))
    return data

def comment_markup(data, escape=True):
    '''parse comment markup'''
    if escape:
        data = replace.html_escape(data)
    data = replace.iter_replace(r'\[([^\]]+)\]', data, replace_recipe)
    data = replace.iter_replace_compiled(replace.LINKREX, data, replace.replace_link)
    data = replace.iter_replace(r'```([^\n]+)\n([^`]+)\n```', data, replace_togglable_code, re.M)
    data = replace.iter_replace(r'```([^`]+)```', data, replace.replace_block, re.M)
    data = replace.iter_replace(r'~~([^~]+)~~', data, replace.replace_strike, re.M)
    data = replace.iter_replace(r'\b__([^_]+)__\b', data, replace.replace_strong, re.M)
    data = replace.iter_replace(r'\b_([^_]+)_\b', data, replace.replace_italic, re.M)
    return data

def markup(data):
    '''parse content markup'''
    def replace_urltable(expr, start, end, data):
        '''replace data from urltable'''
        parse = expr.group(1).split(':')
        if parse and parse[0] in MLURLTABLE:
            data = replace.replace_range(data, start, end, '<a href="{}">{}</a>'.format(MLURLTABLE[parse[0]], parse[1]))
        return data
    replace.html_escape(data)
    data = replace.iter_replace(r'\[([^\]]+)\]', data, replace_urltable)
    return comment_markup(data, False)

def check_recipe(data):
    '''check that recipe is all right'''
    ret = True
    msg = []

    if not data.get('pkgname'):
        ret = False
        msg.append(_('pkgname does not exist'))

    if isinstance(data['pkgname'], list):
        data['pkgname'] = data['pkgname'][0]

    if not isinstance(data['pkgname'], str) or data['pkgname'][0] == '-' or not PKGNAMEREX.match(data['pkgname']):
        ret = False
        msg.append(_('pkgname is not valid'))

    if data.get('pndcategory'):
        if isinstance(data['pndcategory'], list):
            data['pndcategory'] = data['pndcategory'][0]

        if not isinstance(data['pndcategory']):
            msg.append(_('pndcategory is not valid'))

    if not isinstance(data['pkgver'], str) or not data.get('pkgver') or data['pkgver'].find('-') != -1:
        ret = False
        msg.append(_('pkgver should exist and not contain any hyphen'))

    if not isinstance(data['pkgrel'], str) or not data.get('pkgrel') or int(data['pkgrel']) <= 0:
        ret = False
        msg.append(_('pkgrel should be >= 1'))

    if not isinstance(data['license'], list) or not data.get('license') or not isinstance(data['license'][0], str) or not data['license'][0]:
        ret = False
        msg.append(_('should contain license array. if unknown or no license, set unknown'))

    if data.get('source') and (not isinstance(data['source'], list) or not isinstance(data['source'][0], str) or not data['source'][0]):
        ret = False
        msg.append(_('source should be a array'))

    if data.get('url') and not isinstance(data['url'], str):
        ret = False
        msg.append(_('url should be a string'))

    return (ret, msg) # success/failure, error messages

def dump_json(dic):
    '''dump json data'''
    import json
    bottle.response.content_type = 'application/json'
    return json.dumps(dic)

def status_json_ok():
    '''return ok status as json response'''
    return dump_json({'status': 'ok'})

def lastpage():
    '''return path for last page (using, post or query value)'''
    referrer = '/'
    if 'REFERRER' in request.forms and request.forms['REFERRER']:
        referrer = request.forms['REFERRER']
    elif 'REFERRER' in request.query and request.forms['REFERRER']:
        referrer = request.query['REFERRER']
    return referrer

def md5sum(path, block_size=2**20):
    '''get md5sum for file'''
    import hashlib
    md5 = hashlib.md5()
    with open(path, 'rb') as fle:
        while True:
            data = fle.read(block_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def search(fun, cfun, fmt=None, args=None):
    '''search database'''
    fmt = '' if not fmt else fmt

    if request.query.get('p'):
        page, column, order = request.query['p'].split(',')
        page = int(page)
    else:
        page = 1
        column = 'pkgname'
        order = 'asc'

    if column not in ['pkgname', 'pndcategory', 'maintainer']:
        column = 'pkgname'
    if order not in ['desc', 'asc']:
        order = 'asc'

    results = fun('{} ORDER BY {} COLLATE NOCASE {} LIMIT {}, 100'.format(fmt, column, order, page - 1), args)
    matches = cfun(fmt, args)
    pages = round(matches / 100) if matches > 100 else 1
    options = '{},{},{}'.format(page, column, order)
    return (results, matches, pages, options)

def not_valid_csrf_cb():
    '''callback for csrf_check'''
    bottle.abort(403, _('wrong CSRF token supplied'))

def not_valid_session_cb():
    '''callback for non valid session'''
    if is_json_request() or is_ajax_request():
        abort(401, _('not authorized'))
    redirect('/login')

@route('/')
def index_page(header=None, content=None):
    '''main page with information'''
    if is_json_request():
        return dump_json({'CSRF': SESSION['CSRF']})
    recipes = RECIPEMANAGER.query_recipes('ORDER BY datemodify DESC LIMIT 10')
    num_recipes = RECIPEMANAGER.get_recipe_count()
    num_users = USERMANAGER.get_user_count()
    num_contributors = USERMANAGER.query_users_count('WHERE level >= ?', (LEVELS['contributor'],))
    num_moderators = USERMANAGER.query_users_count('WHERE level >= ?', (LEVELS['moderator'],))
    return template('index', header=header, content=content, recipes=recipes, num_recipes=num_recipes, num_users=num_users, num_moderators=num_moderators, num_contributors=num_contributors)

@route('/standards')
def standards_page():
    '''standards page'''
    recipes = RECIPEMANAGER.query_recipes('ORDER BY datemodify DESC LIMIT 10')
    num_recipes = RECIPEMANAGER.get_recipe_count()
    num_users = USERMANAGER.get_user_count()
    num_contributors = USERMANAGER.query_users_count('WHERE level >= ?', (LEVELS['contributor'],))
    num_moderators = USERMANAGER.query_users_count('WHERE level >= ?', (LEVELS['moderator'],))
    return template('standards', recipes=recipes, num_recipes=num_recipes, num_users=num_users, num_moderators=num_moderators, num_contributors=num_contributors)

@route('/search/<query>')
def search_recipes(query=None):
    '''search recipes'''
    if is_json_request():
        return dump_json(RECIPEMANAGER.query_recipes('WHERE pkgname MATCH ? ORDER BY pkgname', (query,)))
    results, matches, pages, options = search(RECIPEMANAGER.query_recipes, RECIPEMANAGER.query_recipes_count, 'WHERE pkgname MATCH ?', (query,))
    if len(results) == 1:
        return redirect('/recipe/{}'.format(results[0]['pkgname']))
    elif not results:
        users = USERMANAGER.query_users('WHERE name MATCH ? LIMIT 1', (query,))
        if users:
            return redirect('/user/{}/recipes'.format(users[0]['name']))
    return template('results', title=_('Search'), user=None, results=results, pages=pages, matches=matches, options=options)

@route('/search')
def search_recipes_query():
    '''redirect query syntaxed search to pretty syntax search'''
    if is_json_request():
        abort(400, _('use /search/<query> instead'))
    query = request.query.get('q')
    if not query:
        return template('recipes', user=None, results=[])
    return redirect('/search/{}'.format(query))

@route('/recipes')
# chromium does not follow Vary: header and browsers suck at caching
# we use this for search result js
@route('/recipes.json')
def recipes_page():
    '''recipes page'''
    if is_json_request():
        cachepath = 'userdata/cache/recipes.json'
        if not os.path.exists(cachepath) or os.path.getmtime(cachepath) < RECIPEMANAGER.modified():
            with open(cachepath, 'w') as fle:
                import json
                recipes = RECIPEMANAGER.query_recipes('ORDER BY pkgname')
                fle.write(json.dumps(recipes))
        return static_file('recipes.json', 'userdata/cache')
    results, matches, pages, options = search(RECIPEMANAGER.query_recipes, RECIPEMANAGER.query_recipes_count)
    return template('results', title=_('Recipes'), user=None, results=results, pages=pages, matches=matches, options=options)

@route('/recipe/<pkgname>/<revision>')
def recipe_revision_page(pkgname=None, revision=None):
    '''recipe revision page'''
    if revision:
        recipe = RECIPEMANAGER.get_revision(pkgname, revision)
    else:
        recipe = RECIPEMANAGER.get_recipe(pkgname)
    if not recipe:
        abort(404)
    comments = RECIPEMANAGER.query_comments('WHERE pkgname = ? AND revision = ?', (pkgname, recipe['revision']))
    if is_json_request():
        del recipe['recipedir']
        recipe['comments'] = comments
        return dump_json(recipe)
    return template('recipe', recipe=recipe, comments=comments)

@route('/recipe/<pkgname>')
def recipe_page(pkgname=None):
    '''recipe page'''
    return recipe_revision_page(pkgname)

@route('/recipe/abandon/<pkgname>', ['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def abandon_recipe(pkgname=None):
    '''abandon recipe'''
    recipe = RECIPEMANAGER.get_recipe(pkgname)
    if not recipe:
        abort(400, _('recipe must exist'))
    if not USER or USER['name'] != recipe['user']:
        abort(403)
    RECIPEMANAGER.set_maintainer(pkgname, '')
    if is_json_request():
        return status_json_ok()
    return redirect('/recipe/{}'.format(pkgname))

@route('/recipe/adopt/<pkgname>', ['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def adopt_recipe(pkgname=None):
    '''adopt recipe'''
    recipe = RECIPEMANAGER.get_recipe(pkgname)
    if not recipe:
        abort(400, _('recipe must exist'))
    if recipe['maintainer']:
        abort(403, _('this recipe is not abadoned'))
    RECIPEMANAGER.set_maintainer(pkgname, USER['name'])
    if is_json_request():
        return status_json_ok()
    return redirect('/recipe/{}'.format(pkgname))

@route('/recipe/delete/<pkgname>/<revision>', ['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def delete_recipe_revision(pkgname=None, revision=None):
    '''delete recipe revision'''
    if revision:
        recipe = RECIPEMANAGER.get_revision(pkgname, revision)
    else:
        recipe = RECIPEMANAGER.get_recipe(pkgname)
    if not recipe:
        abort(400, _('recipe and revision must exist'))
    if not USER or (USER['level'] < LEVELS['moderator'] and USER['name'] != recipe['user']):
        abort(403)
    if revision:
        RECIPEMANAGER.remove_revision(pkgname, recipe['revision'], remove_comments=True)
    else:
        RECIPEMANAGER.remove_recipe(pkgname, remove_revisions=True, remove_comments=True)
    if is_json_request():
        return status_json_ok()
    if recipe.get('parent'):
        return redirect('/recipe/{}'.format(pkgname))
    return redirect('/user/{}/recipes'.format(USER['name']))

@route('/recipe/delete/<pkgname>', ['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def delete_recipe(pkgname=None):
    '''delete recipe'''
    return delete_recipe_revision(pkgname)

@route('/recipe/reject/<pkgname>/<revision>', ['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def reject_recipe_revision(pkgname=None, revision=None):
    '''reject recipe revision'''
    recipe = RECIPEMANAGER.get_revision(pkgname, revision)
    if not recipe or not recipe.get('parent'):
        abort(400, _('recipe and revision must exist'))
    if not USER or USER['name'] != recipe['maintainer']:
        abort(403)
    RECIPEMANAGER.remove_revision(pkgname, recipe['revision'], remove_comments=True)
    if is_json_request():
        return status_json_ok()
    if revision:
        return redirect('/recipe/{}'.format(pkgname))
    return redirect('/user/{}/recipes'.format(USER['name']))

@route('/recipe/accept/<pkgname>/<revision>', ['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def accept_recipe_revision(pkgname=None, revision=None):
    '''reject recipe revision'''
    recipe = RECIPEMANAGER.get_revision(pkgname, revision)
    if not recipe or not recipe.get('parent'):
        abort(400, _('recipe and revision must exist'))
    if not USER or USER['name'] != recipe['maintainer']:
        abort(403)
    RECIPEMANAGER.accept_revision(pkgname, revision)
    user = USERMANAGER.get_user(recipe['user'])
    if user and user['level'] < LEVELS['contributor']:
        user['level'] = LEVELS['contributor']
        USERMANAGER.set_user(user['name'], user)
    if is_json_request():
        return status_json_ok()
    if revision:
        return redirect('/recipe/{}'.format(pkgname))
    return redirect('/user/{}/recipes'.format(USER['name']))

@route('/user/<user>/recipes')
def user_recipes(user=None):
    '''user recipes page'''
    if is_json_request():
        return dump_json(RECIPEMANAGER.query_recipes('WHERE user = ? ORDER BY pkgname', (user,)))
    results, matches, pages, options = search(RECIPEMANAGER.query_recipes, RECIPEMANAGER.query_recipes_count, 'WHERE user = ?', (user,))
    return template('results', title='{} by {}'.format(_('Recipes'), user), user=user, results=results, pages=pages, matches=matches, options=options)

@route('/user/<user>/revisions')
def user_revisions(user=None):
    '''user revisions page'''
    if is_json_request():
        return dump_json(RECIPEMANAGER.query_revisions('WHERE user = ? ORDER BY pkgname', (user,)))
    results, matches, pages, options = search(RECIPEMANAGER.query_revisions, RECIPEMANAGER.query_revisions_count, 'WHERE user = ?', (user,))
    return template('results', title='{} by {}'.format(_('Revisions'), user), user=user, results=results, pages=pages, matches=matches, options=options)

@route('/user/<user>/contributions')
def user_contributions(user=None):
    '''user contributions page'''
    if is_json_request():
        return dump_json(RECIPEMANAGER.query_recipes('WHERE user != ? AND contributors MATCH ? ORDER BY pkgname', (user, "'{}'".format(user),)))
    results, matches, pages, options = search(RECIPEMANAGER.query_recipes, RECIPEMANAGER.query_recipes_count, 'WHERE user != ? AND contributors MATCH ?', (user, "'{}'".format(user),))
    return template('results', title='{} by {}'.format(_('Contributions'), user), user=user, results=results, pages=pages, matches=matches, options=options)

@route('/comment/<pkgname>/<revision>', ['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def create_comment_for_revision(pkgname=None, revision=None):
    '''create comment for recipe revision'''
    comment = request.forms.get('comment')
    if not comment:
        abort(400, _('comment field must be provided'))
    if revision:
        recipe = RECIPEMANAGER.get_revision(pkgname, revision)
    else:
        recipe = RECIPEMANAGER.get_recipe(pkgname)
    if not recipe:
        abort(400, _('recipe and revision must exist'))
    RECIPEMANAGER.create_comment(pkgname, recipe['revision'], USER['name'], comment)
    if is_json_request():
        return status_json_ok()
    if revision:
        return redirect('/recipe/{}/{}'.format(pkgname, revision))
    return redirect('/recipe/{}'.format(pkgname))

@route('/comment/<pkgname>', ['POST'])
def create_comment(pkgname=None):
    '''create comment for recipe'''
    return create_comment_for_revision(pkgname, None)

@route('/comment/delete/<pkgname>/<revision>/<cid>', ['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def delete_comment_from_revision(pkgname=None, revision=None, cid=None):
    '''delete comment from recipe revision'''
    if revision:
        recipe = RECIPEMANAGER.get_revision(pkgname, revision)
    else:
        recipe = RECIPEMANAGER.get_recipe(pkgname)
    if not recipe:
        abort(400, _('recipe and revision must exist'))
    comment = RECIPEMANAGER.get_comment(pkgname, recipe['revision'], cid)
    if not comment:
        abort(400, _('comment must exist'))
    if not USER or (USER['level'] < LEVELS['moderator'] and USER['name'] != comment['user']):
        abort(403)
    RECIPEMANAGER.remove_comment(pkgname, recipe['revision'], cid)
    if revision:
        return redirect('/recipe/{}/{}'.format(pkgname, revision))
    return redirect('/recipe/{}'.format(pkgname))

@route('/comment/delete/<pkgname>/<cid>', ['POST'])
def delete_comment(pkgname=None, cid=None):
    '''delete comment from recipe'''
    return delete_comment_from_revision(pkgname, None, cid)

@route('/user/<user>/edit', ['GET', 'POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
def user_account(user=None):
    '''user account page'''
    # pylint: disable=too-many-branches

    if USER['name'] != user:
        abort(403)

    def gather_errors():
        '''validate edit'''
        errors = []
        jsstr = js_translations('register')
        email = request.forms.get('email')
        password1 = request.forms.get('password')
        password2 = request.forms.get('password_confirm')

        if password1 != password2:
            errors.append(jsstr['password_confirm'])
        if not email or not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            errors.append(jsstr['email'])

        if not errors:
            if password1:
                ret = USERMANAGER.get_user(user, SESSION['sessionid'], (password1, SESSION['CSRF']), email)
            else:
                ret = USERMANAGER.get_user(user, SESSION['sessionid'], email=email)
            if not ret:
                errors.append(_('Database error: Failed to create user into database'))
            if password1:
                logout()

        return errors

    if request.method == 'POST':
        errors = gather_errors()
        if not errors:
            if is_json_request():
                return status_json_ok()
            return redirect('/user/{}/edit'.format(user))
        else:
            if is_json_request():
                return dump_json({'status': 'fail', 'errors': errors})
            return template('useredit', errors=errors)

    if is_json_request():
        sessions = []
        key_filter = ['CSRF', 'valid']
        for sid in USER.get('sessions'):
            data = SESSIONMANAGER.get_session(sid)
            if not data:
                continue
            for key in key_filter:
                if key in data:
                    del data[key]
            sessions.append(data)
        return dump_json({'sessions': sessions})
    return template('useredit', errors=[])

@route('/revoke/<sessionid>', ['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def revoke(sessionid=None):
    '''revoke session'''
    revoke_session = SESSIONMANAGER.load(sessionid)
    if not revoke_session:
        abort(400, _('revoked session must exist'))
    if revoke_session['name'] != USER['name']:
        abort(403)
    USER['sessions'].remove(sessionid)
    SESSIONMANAGER.remove(sessionid)
    USERMANAGER.set_user(USER['name'], USER)
    if is_json_request():
        return status_json_ok()
    return redirect(lastpage())

@route('/logout', ['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def logout():
    '''logout'''
    USER['sessions'].remove(SESSION['sessionid'])
    SESSION['name'] = ''
    SESSION['valid'] = False
    SESSIONMANAGER.save(SESSION)
    if is_json_request():
        return status_json_ok()
    return redirect('/login')

@route('/login', ['GET', 'POST'])
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb, method=['POST'])
def login():
    '''login page'''
    # pylint: disable=too-many-return-statements

    if USER:
        if is_json_request():
            return status_json_ok()
        return redirect('/')

    # regenerate CSRF token
    if request.method == 'GET':
        # pylint: disable=global-statement
        global SESSION
        SESSION = session.regenerate_csrf(SESSIONMANAGER)

    def gather_errors():
        '''validate login'''
        username = request.forms.get('username')
        password = request.forms.get('password')
        if not USERMANAGER.test_password(username, password):
            return [_('Invalid username or password')]
        return []

    if request.method == 'POST':
        errors = gather_errors()
        if not errors:
            SESSION['valid'] = True
            SESSION['name'] = request.forms.get('username')
            SESSIONMANAGER.regenerate_session(SESSION)
            if is_json_request():
                return status_json_ok()
            return redirect('/')
        else:
            if is_json_request():
                return dump_json({'status': 'fail', 'errors': errors})
            return template('login', errors=errors)

    if is_json_request():
        return abort(400, _('username and password fields missing as POST request'))
    return template('login', errors=[])

@route('/register', ['GET', 'POST'])
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb, method=['POST'])
def register():
    '''register page'''
    # pylint: disable=too-many-branches, too-many-return-statements

    if USER:
        if is_json_request():
            abort(400, _('already registered'))
        return redirect('/')

    # regenerate CSRF token
    if request.method == 'GET':
        # pylint: disable=global-statement
        global SESSION
        SESSION = session.regenerate_csrf(SESSIONMANAGER)

    def gather_errors():
        '''validate registeration'''
        username = request.forms.get('username')
        email = request.forms.get('email')
        password1 = request.forms.get('password')
        password2 = request.forms.get('confirm_password')

        errors = []
        jsstr = js_translations('register')
        if len(username) < 3:
            errors.append(jsstr['username_length'].format(3))
        if len(password1) < 8:
            errors.append(jsstr['password_length'].format(8))
        if password1 != password2:
            errors.append(jsstr['password_confirm'])
        if not email or not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            errors.append(jsstr['email'])

        # create user
        if not errors:
            user = USERMANAGER.get_user(username)
            if user:
                errors.append(_('Username already in use'))
            else:
                user = USERMANAGER.get_user(username, SESSION['sessionid'], (password1, SESSION['CSRF']), email)
                if not user:
                    errors.append(_('Database error: Failed to create user into database'))

        return errors

    if request.method == 'POST':
        errors = gather_errors()
        if not errors:
            if is_json_request():
                return status_json_ok()
            # content = '<p>{}<br/>{}</p>'.format(_('Thank you for registering!'),
            #                                     _('We have sent verification mail to your e-mail.'))
            content = '<p>{}<br/>{}</p>'.format(_('Thank you for registering!'),
                                                _('You can now proceed to the login page.'))
            return template('register', content=content, errors=[])
        else:
            if is_json_request():
                return dump_json({'status': 'fail', 'errors': errors})
            return template('register', content=None, errors=errors)

    if is_json_request():
        return abort(400, _('username and password fields missing as POST request'))
    return template('register', content=None, errors=[])

@route('/lang/<lang>', ['POST'])
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def change_language(lang=None):
    '''change language'''
    if lang not in TRANSLATIONS:
        abort(404, _('Unfortunately we do not have translation for {} locale').format(lang))
    SESSION['lang'] = lang
    SESSIONMANAGER.save(SESSION)
    if is_json_request():
        return status_json_ok()
    return redirect(lastpage())

@route('/style/<style>', ['POST'])
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def change_style(style=None):
    '''change style'''
    if style not in STYLES:
        abort(404)
    SESSION['style'] = style
    SESSIONMANAGER.save(SESSION)
    if is_json_request():
        return status_json_ok()
    return redirect(lastpage())

@route('/js/translations/<key>')
def get_js_translations(key=None):
    '''fetch js translations'''
    return js_translations(key)

@route('/js/<jsf>')
def get_js(jsf=None):
    '''fetch js script'''
    return static_file(jsf, root='views/js')

@route('/css/<css>')
def get_css(css=None):
    '''fetch css'''
    return static_file(css, root='views/css')

@route('/images/<image>')
@route('/images/<sub>/<image>')
def get_image(image=None, sub=None):
    '''fetch image'''
    if image == 'moe':
        import random
        image = random.choice(os.listdir('views/images/moe'))
        return static_file(image, root=('views/images/moe'))
    if sub:
        from os.path import join as path_join
        return static_file(image, root=path_join('views/images', sub))
    return static_file(image, root='views/images')

@route('/favicon.ico')
def get_favicon():
    '''fetch favicon'''
    return static_file('favicon.ico', root='.')

@route('/dl/<pkgname>/<revision>/<recipefile>')
def get_recipe_revision_file(pkgname=None, revision=None, recipefile=None):
    '''fetch recipe revision file'''
    if revision:
        recipe = RECIPEMANAGER.get_revision(pkgname, revision)
    else:
        recipe = RECIPEMANAGER.get_recipe(pkgname)
    if not recipe:
        abort(404)
    path = os.path.join('userdata/recipes', recipe['pkgname'], recipe['directory'])
    if recipefile == 'PNDBUILD':
        if request.query.get('syntax'):
            data = None
            with open(os.path.join(path, recipefile), 'r') as fle:
                data = fle.read()
            if not data:
                abort(404, _('PNDBUILD file not found'))
            syntax = replace.syntax(data, 'bash')
            return syntax if is_ajax_request() else template('syntax', title='PNDBUILD', syntax=syntax)
        return static_file(recipefile, root=path, mimetype='text/plain')
    return static_file(recipefile, root=path, download=True, mimetype='application/octet-stream')

@route('/dl/<pkgname>/<recipefile>')
def get_recipe_file(pkgname=None, recipefile=None):
    '''fetch recipe file'''
    return get_recipe_revision_file(pkgname, None, recipefile)

class UploadJSONFailure(Exception):
    '''Exception raised when saving uploaded file failed'''
    def __init__(self, message, httpcode):
        Exception.__init__(self, message)
        self.httpcode = httpcode

def upload_fail(httpcode, msg):
    '''return failure for upload'''
    bottle.response.status = httpcode
    bottle.response.content_type = 'application/json'
    raise UploadJSONFailure(msg, httpcode)

@route('/upload', method=['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def post_upload():
    '''recipe upload'''
    # pylint: disable=too-many-branches

    jsstr = js_translations('upload')
    data = request.files.get('recipe')
    name = request.query.get('recipe')
    if not name:
        name = request.forms.get('recipe')
    if data and not name:
        name = data.filename

    if 'tgz' in SESSION:
        path = os.path.join('userdata/tmp', SESSION['tgz'])
        if os.path.exists(path):
            os.remove(path)

    def check_upload(name, data):
        '''check that upload is ok'''
        if not data or not data.file:
            upload_fail(400, _('File data is missing'))
        if data.content_length > 8192 * 1024:
            upload_fail(413, jsstr['file_size'])
        if not name:
            upload_fail(400, _('POST/QUERY field named "recipe" is missing'))
        if len(name) > 11 and name[-11:] != '.src.tar.gz':
            upload_fail(400, _('Filename should end in .src.tar.gz'))
        if name == 'PNDBUILD' or name.find('/') != -1:
            upload_fail(400, _('Invalid filename'))

    try:
        check_upload(name, data)
    except UploadJSONFailure as exc:
        abort(exc.httpcode, str(exc))

    revision = RECIPEMANAGER.allocate_revision()
    name = '{}-{}'.format(revision, name)
    path = os.path.join('userdata/tmp', name)
    data.save(path)

    md5 = md5sum(path)
    if RECIPEMANAGER.md5_duplicate_exists(md5):
        os.remove(path)
        abort(409, _('This recipe is duplicate'))

    recipe, pndbuild_data = parse_recipe(path)
    parent = RECIPEMANAGER.get_recipe(recipe['pkgname'])
    if parent:
        from distutils.version import LooseVersion
        pver = '{}.{}'.format(parent['pkgver'], parent['pkgrel'])
        rver = '{}.{}'.format(recipe['pkgver'], recipe['pkgrel'])
        if LooseVersion(rver) < LooseVersion(pver):
            os.remove(path)
            abort(400, _('Recipe is older version'))
        if USER['name'] != parent['maintainer']:
            SESSION['tgz'] = name
            SESSIONMANAGER.save(SESSION)
            content = template('revisionupload', tgz=name, revision=revision)
            if is_json_request() or is_ajax_request():
                return dump_json({'status': 'ok', 'content': content})
            return content

    return save_recipe(path, recipe, pndbuild_data, revision)

@route('/upload/store', method=['POST'])
@session.valid_session(SESSIONMANAGER, not_valid_session_cb)
@session.check_csrf(SESSIONMANAGER, not_valid_csrf_cb)
def store_recipe():
    '''recipe store request from UI'''
    name = request.forms.get('tgz')
    revision = request.forms.get('revision')
    changes = request.forms.get('changes')
    if not name or not revision or not changes:
        abort(400, 'name, revision and changes must not be empty')

    if 'tgz' in SESSION:
        del SESSION['tgz']
        SESSIONMANAGER.save(SESSION)

    path = os.path.join('userdata/tmp', name)
    if request.forms.get('cancel'):
        os.remove(path)
        return redirect('/')

    recipe, pndbuild_data = parse_recipe(path)
    parent = RECIPEMANAGER.get_recipe(recipe['pkgname'])
    if not parent:
        os.remove(path)
        abort(400, 'this package is not a revision')

    original_data = None
    origpath = os.path.join('userdata/recipes', parent['pkgname'], parent['directory'], 'PNDBUILD')
    with open(origpath, 'r') as fle:
        original_data = fle.read()

    if not original_data:
        os.remove(path)
        abort(400, 'failed to read parent PNDBUILD')

    from difflib import unified_diff
    recipe['diff'] = '\n'.join(unified_diff(original_data.split('\n'), pndbuild_data.split('\n'), lineterm='')).strip()
    recipe['changes'] = changes
    return save_recipe(path, recipe, pndbuild_data, revision)

def parse_recipe(path):
    '''parse recipe data from tgz file'''

    def read_recipe(path):
        '''read recipe data from tar.gz'''
        try:
            ret = pndbuild.readgz(path)
        except pndbuild.PNDBUILDException as exc:
            upload_fail(500, exc)
        recipe = ret[0]
        pndbuild_data = ret[1]
        if not pndbuild_data:
            upload_fail(500, _('PNDBUILD data is missing'))
        check = check_recipe(recipe)
        if not check[0]:
            if is_json_request():
                upload_fail(400, '\n'.join(check[1]))
            else:
                upload_fail(400, '<br/>'.join(check[1]))
        return ret

    try:
        ret = read_recipe(path)
    except UploadJSONFailure as exc:
        os.remove(path)
        abort(exc.httpcode, str(exc))

    return ret

def save_recipe(path, recipe, pndbuild_data, revision):
    '''save recipe to disk'''
    # pylint: disable=too-many-branches

    def move_to_recipe_directory(path, revision, recipe, pndbuild_data, md5):
        '''move recipe to recipe storage directory'''
        recipedir = os.path.join('userdata/recipes', recipe['pkgname'], revision)
        dirname = os.path.dirname(recipedir)

        def cleanup():
            '''cleanup failed save'''
            import shutil
            if os.path.exists(path):
                os.remove(path)
            if os.path.exists(recipedir):
                shutil.rmtree(recipedir)
            if os.path.exists(dirname) and not os.listdir(dirname):
                shutil.rmtree(dirname)

        if not os.path.exists(dirname):
            os.mkdir(dirname)
        if not os.path.exists(recipedir):
            os.mkdir(recipedir)
        else:
            cleanup()
            upload_fail(500, _('Attempted to overwrite file'))

        name = '{}-{}-{}.src.tar.gz'.format(recipe['pkgname'], recipe['pkgver'], recipe['pkgrel'])
        os.rename(path, os.path.join(recipedir, name))
        with open(os.path.join(recipedir, 'PNDBUILD'), 'w') as fle:
            fle.write(pndbuild_data)

        try:
            RECIPEMANAGER.create_recipe(USER['name'], revision, recipe, md5)
        except Exception as exc:
            cleanup()
            raise exc

    md5 = md5sum(path)
    if RECIPEMANAGER.md5_duplicate_exists(md5):
        os.remove(path)
        abort(409, _('This recipe is duplicate'))

    try:
        move_to_recipe_directory(path, revision, recipe, pndbuild_data, md5)
    except UploadJSONFailure as exc:
        abort(exc.httpcode, str(exc))

    recipe = RECIPEMANAGER.get_recipe(recipe['pkgname'])
    if not recipe:
        recipe = RECIPEMANAGER.get_revision(recipe['pkgname'], revision)
    if not recipe:
        abort(500, _('Something went wrong with database'))

    url = '/recipe/{}'.format(recipe['pkgname'])
    if recipe.get('parent'):
        url = '{}/{}'.format(url, recipe['revision'])
    elif USER['level'] < LEVELS['contributor']:
        USER['level'] = LEVELS['contributor']
        USERMANAGER.set_user(USER['name'], USER)

    if is_json_request() or is_ajax_request():
        return dump_json({'status': 'ok', 'url': url})
    return redirect(url)

@bottle.error(400)
@bottle.error(403)
@bottle.error(404)
@bottle.error(409)
@bottle.error(413)
@bottle.error(500)
def error_handler(error):
    '''error handler'''
    if is_json_request() or is_ajax_request():
        return dump_json({'status': 'fail', 'msg': error.body})
    if _ is None:
        return '{}'.format(error.status)
    return index_page('{}'.format(error.status), '<p>{}</p>'.format(error.body))

@hook('before_request')
def before_request():
    '''run before routing requests'''

    # filter out setup for paths we don't need session for
    nosession = ['/js', '/css', '/images', '/images/os', '/images/ua']
    if os.path.dirname(request.path) in nosession:
        return

    # special session handling for non html requests
    if is_json_request() or is_ajax_request():
        nosession = ['/search', '/recipes']
        if request.path in nosession:
            return

    # get session
    # pylint: disable=global-statement
    global SESSION, USER
    USER = None
    SESSION = SESSIONMANAGER.get_session()
    if SESSION['valid']:
        USER = USERMANAGER.get_user(SESSION['name'], SESSION['sessionid'])
        if not USER:
            SESSION['name'] = ''
            SESSION['valid'] = False
            SESSIONMANAGER.save(SESSION)

    # set language
    lang = SESSION.get('lang')
    if not lang and 'Accept-Langauge' in request.headers:
        lang = supported_language(request.headers['Accept-Language'], TRANSLATIONS)
    set_language(lang)

    # set style
    style = SESSION.get('style')
    if not style:
        style = OPT['style']

    # request template globals
    BaseTemplate.defaults['_'] = _
    BaseTemplate.defaults['PURSTYLE'] = '{}.css'.format(style)
    BaseTemplate.defaults['USER'] = USER

    # avoid json caches
    bottle.response.set_header('Vary', 'accept')

def main():
    '''main method'''
    bottle.run(server=OPT['server'], host='0.0.0.0', port=OPT['port'])

def setup():
    '''setup method'''
    # set template globals
    BaseTemplate.defaults['PURVERSION'] = VERSION
    BaseTemplate.defaults['PURSTYLES'] = STYLES
    BaseTemplate.defaults['PURTRANSLATIONS'] = TRANSLATIONS
    BaseTemplate.defaults['PURBETA'] = BETA
    BaseTemplate.defaults['LEVELS'] = LEVELS

    # template functions
    csrf_input = lambda: '<input type="hidden" name="CSRF" value="{}"/>'.format(SESSION['CSRF'])
    referrer_input = lambda: '<input type="hidden" name="REFERRER" value="{}"/>'.format(request.path)
    BaseTemplate.defaults['CL'] = comment_markup
    BaseTemplate.defaults['ML'] = markup
    BaseTemplate.defaults['_ML'] = lambda x: markup(_(x))
    BaseTemplate.defaults['get_session'] = SESSIONMANAGER.get_session
    BaseTemplate.defaults['js_togglable'] = js_togglable
    BaseTemplate.defaults['linkify'] = replace.html_linkify_and_escape
    BaseTemplate.defaults['link'] = replace.html_link
    BaseTemplate.defaults['csrf_input'] = csrf_input
    BaseTemplate.defaults['referrer_input'] = referrer_input
    BaseTemplate.defaults['csrf_link'] = lambda x, y: '<form class="link" action="{}" method="POST"><input type="submit" class="link" value="{}"/>{}</form>'.format(x, x if not y else y, csrf_input())
    BaseTemplate.defaults['referrer_csrf_link'] = lambda x, y: '<form class="link" action="{}" method="POST"><input type="submit" class="link" value="{}"/>{}{}</form>'.format(x, x if not y else y, csrf_input(), referrer_input())
    BaseTemplate.defaults['diff'] = lambda x: replace.syntax(x, 'diff')

setup()
if __name__ == "__main__":
    main()
else:
    # pylint: disable=invalid-name
    application = bottle.default_app()
    application.catchall = False

#  vim: set ts=8 sw=4 tw=0 ft=python :
