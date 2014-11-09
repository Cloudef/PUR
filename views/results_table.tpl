% page, column, order = options.split(',')
% page = int(page)
% def lsort(x, s):
%    if x != column or order != 'asc':
%       sort = 'asc'
%       symbol = '↑'
%    else:
%       sort = 'desc'
%       symbol = '↓'
%    end
%    if x != column:
%       symbol = '-'
%    end
%    url = '?p={},{},{}'.format(page, x, sort)
%    return '{} {}'.format(link(url, s), symbol)
% end

<table>
    <tr class='header'>
        <th>{{!lsort('pndcategory', _('Category'))}}</th>
        <th>{{!lsort('pkgname', _('Name'))}}</th>
        <th>{{_('Version')}}</th>
        <th>{{_('Description')}}</th>
        <th>{{!lsort('maintainer', _('Maintainer'))}}</th>
    </tr>
    % odd = ''
    % for recipe in recipes:
    <tr class='{{odd}}'>
        <td>{{recipe.get('pndcategory') or _('unknown')}}</td>
        % if not recipe.get('parent'):
        <td>{{!link('/recipe/{}'.format(recipe['pkgname']), recipe['pkgname'])}}</td>
        % else:
        <td>{{!link('/recipe/{}/{}'.format(recipe['pkgname'], recipe['revision']), recipe['pkgname'])}}</td>
        % end
        <td>{{recipe['pkgver']}}</td>
        <td>{{recipe['pkgdesc']}}</td>
        % if recipe['maintainer']:
        <td>{{!link('/user/{}/recipes'.format(recipe['maintainer']), recipe['maintainer'])}}</td>
        % else:
        <td>{{_('abandoned')}}</td>
        % end
    </tr>
    % odd = ('', ' odd')[odd == True]
    % end
</table>

% # vim: set ts=8 sw=4 tw=0 ft=html :
