<%
header = link('/recipe/{}/{}'.format(pkgname, revision), 'Revision {}'.format(revision))
header = '{} by {}'.format(header, link('/user/{}/recipes'.format(revision_user), revision_user))
right = None
if USER and USER['name'] == maintainer:
   right = referrer_csrf_link('/recipe/accept/{}/{}'.format(pkgname, revision), _('accept'))
   right = '{} | {}'.format(right, referrer_csrf_link('/recipe/reject/{}/{}'.format(pkgname, revision), _('reject')))
elif USER and (USER['name'] == revision_user or USER['level'] >= LEVELS['moderator']):
   right = referrer_csrf_link('/recipe/delete/{}/{}'.format(pkgname, revision), _('delete'))
end
right = '{} | {}'.format(right, datemodify) if right else datemodify
%>

<div class='revision'>
   % diffstr = revision_diff if revision_diff else ''
   % diffstr = '{}\n{}'.format(revision_changes, diffstr)
   {{!js_togglable(header, diff(diffstr), right, True)}}
</div>

% # vim: set ts=8 sw=4 tw=0 ft=html :
