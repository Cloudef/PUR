<table>
    <tr class='header'>
        <th><a href="#">{{_('Category')}}</a></th>
        <th><a href="#">{{_('Name')}}</a></th>
        <th>{{_('Version')}}</th>
        <th>{{_('Description')}}</th>
        <th><a href="#">{{_('Maintainer')}}</a></th>
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
        <td>{{!link('/user/{}/recipes'.format(recipe['maintainer']), recipe['maintainer'])}}</td>
    </tr>
    % odd = ('', ' odd')[odd == True]
    % end
</table>

% # vim: set ts=8 sw=4 tw=0 ft=html :
