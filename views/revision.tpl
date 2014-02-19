<%
header = link('/recipe/{}/{}'.format(pkgname, revision), 'Revision {}'.format(revision))
header = '{} by {}'.format(header, link('/user/{}/recipes'.format(revision_user), revision_user))
right = None
if USER and USER['name'] == revision_user:
   right = csrf_link('/recipe/delete/{}/{}'.format(pkgname, revision), _('delete'))
end
right = '{} | {}'.format(right, datemodify) if right else datemodify
%>

<% diffstr = \
"""
# diff -u tiedosto1 tiedosto2
--- tiedosto1   2006-05-01 12:01:35.000000000 +0300
+++ tiedosto2   2006-05-01 12:02:00.000000000 +0300
@@ -1,4 +1,4 @@
 Evoluution mekanismeja ovat muun muassa luonnonvalinta, mutaatiot ja
-migraatio. Teorian mukaan luonnonvalinta johtaa population parempaan
+migraatio. Teorian mukaan luonnonvalinta johtaa populaation parempaan
 sopeutumiseen ympäristöönsä, sillä menestyneimmistä yksilöistä tulee
 lopulta vallitseva tyyppi populaatiossa tehokkaamman lisääntymisen myötä.
"""
%>

<div class='revision'>
    {{!js_togglable(header, diff(diffstr), right, True)}}
</div>

% # vim: set ts=8 sw=4 tw=0 ft=html :
