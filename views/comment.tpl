<div class='comment'>
    <header>
        Comment by {{!link('/user/{}/recipes'.format(comment_user), comment_user)}}
        % if USER and (USER['name'] == comment_user or USER['level'] >= LEVELS['moderator']):
        <div style='float:right;'>
            % if not is_revision:
            {{!csrf_link('/comment/delete/{}/{}'.format(pkgname, comment_id), _('delete'))}} | {{comment_date}}
            % else:
            {{!csrf_link('/comment/delete/{}/{}/{}'.format(pkgname, revision, comment_id), _('delete'))}} | {{comment_date}}
            % end
        </div>
        % else:
        <div style='float:right;'>{{comment_date}}</div>
        % end
    </header>
    <article>
        <pre>{{!CL(comment)}}</pre>
    </article>
</div>

% # vim: set ts=8 sw=4 tw=0 ft=html :
