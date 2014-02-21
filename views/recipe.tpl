% rebase('html_base.tpl', title=_('PUR - {}'.format(recipe['pkgname'])))
% is_revision = True if recipe.get('parent') else False

<section class='box'>
    <header>
        % if not is_revision:
        <h2>{{recipe['pkgname']}}</h2>
        % else:
        <div style='float:right;'>{{!link('/recipe/{}'.format(recipe['pkgname']), _('parent'))}}</div>
        <h2>{{recipe['pkgname']}} ({{recipe['revision']}})</h2>
        % end
    </header>
    <div class='box actions'>
        <h3>Recipe Actions</h3>
        {{!link(recipe['recipepath'], _('View PNDBUILD'))}}
        {{!link(recipe['tarpath'], _('Download tarball'))}}
        % if is_revision and USER and USER['name'] == recipe['maintainer']:
        {{!referrer_csrf_link('/recipe/accept/{}/{}'.format(recipe['pkgname'], recipe['revision']), _('Accept revision'))}}
        {{!referrer_csrf_link('/recipe/reject/{}/{}'.format(recipe['pkgname'], recipe['revision']), _('Reject revision'))}}
        % end
    </div>
    <article id='recipebox'>
        <p>
        <div class='col_25'><strong>{{_('Description')}}:</strong></div>
        <div class='col_25'>{{recipe['pkgdesc']}}</div>
        <div class='clearfix'></div>
        <div class='col_25'><strong>{{_('Upstream URL')}}:</strong></div>
        <div class='col_25'>{{!link(recipe['url'])}}</div>
        <div class='clearfix'></div>
        <div class='col_25'><strong>{{_('Category')}}:</strong></div>
        <div class='col_25'>{{recipe.get('pndcategory') or _('unknown')}}</div>
        <div class='clearfix'></div>
        <div class='col_25'><strong>{{_('License')}}:</strong></div>
        <div class='col_25'>{{', '.join(recipe['license'])}}</div>
        <div class='clearfix'></div>
        % if not is_revision:
        <div class='col_25'><strong>{{_('Maintainer')}}:</strong></div>
        <div class='col_25'>{{!link('/user/{}/recipes'.format(recipe['maintainer']), recipe['maintainer'])}}</div>
        % if recipe['contributors']:
            <div class='clearfix'></div>
            <div class='col_25'><strong>{{_('Contributors')}}:</strong></div>
            <div class='col_25'>
            % links = []
            % for ctrb in recipe['contributors']:
            % links.append(link('/user/{}/recipes'.format(ctrb), ctrb))
            % end
            {{!', '.join(links)}}
            </div>
        % end
        % else:
        <div class='col_25'><strong>{{_('Contributor')}}:</strong></div>
        <div class='col_25'>{{!link('/user/{}/recipes'.format(recipe['user']), recipe['user'])}}</div>
        % end
        <div class='clearfix'></div>
        <div class='col_25'><strong>{{_('Last Updated')}}:</strong></div>
        <div class='col_25'>{{recipe['datemodify']}}</div>
        <div class='clearfix'></div>
        % num1 = len(recipe['depend']) if recipe['depend'] else 0
        % num2 = len(recipe['makedepend']) if recipe['makedepend'] else 0
        % if num1 or num2:
        <div class='col_50 wrap'>
            <h3 class='header'>{{_('Dependencies')}} ({{num1}})</h3>
            % if recipe['depend']:
            <ul>
                % for dep in recipe['depend']:
                <li>{{dep}}</li>
                % end
            </ul>
            % end
        </div>
        <div class='col_50 wrap'>
            <h3 class='header'>{{_('Build Dependencies')}} ({{num2}})</h3>
            % if recipe['makedepend']:
            <ul>
                % for dep in recipe['makedepend']:
                <li>{{dep}}</li>
                % end
            </ul>
            % end
        </div>
        <div class='clearfix'></div>
        % end
        % num1 = len(recipe['source']) if recipe['source'] else 0
        % num2 = len(recipe['pndexec']) if recipe['pndexec'] else 0
        % if num1 or num2:
        <div class='col_50 wrap'>
            <h3 class='header'>{{_('Sources')}} ({{num1}})</h3>
            % if recipe['source']:
            <ul>
                % for src in recipe['source']:
                % src = linkify(src, True)
                <li>{{!src}}</li>
            </ul>
            % end
        </div>
        <div class='col_50 wrap'>
            <h3 class='header'>{{_('Applications')}} ({{num2}})</h3>
            % if recipe['pndexec']:
            <ul>
                % for exe in recipe['pndexec']:
                <li>{{exe}}</li>
                % end
            </ul>
            % end
        </div>
        <div class='clearfix'></div>
        % end
        </p>
    </article>
</section>

<script>
$.get("{{recipe['recipepath']}}?syntax=1", function(data) {
    $('#recipebox').append('<p class="js_togglable"> \
        <header> \
        <h3 style="display:inline;">PNDBUILD</h3> \
        <button id="toggle_pndbuild" class="js_toggle">-</button> \
        </header> \
        <article>' + data + '</article> \
        </p>');
    togglable_elements($('#toggle_pndbuild'));
});
</script>

% if not is_revision and recipe['revisions']:
<section class='box'>
    % for revision in recipe['revisions']:
    % include('revision', pkgname=recipe['pkgname'], maintainer=recipe['maintainer'], revision=revision['revision'], datemodify=revision['datemodify'], revision_user=revision['user'])
    % end
</section>
% end

% if USER:
<section class='box'>
    % include('commentbox', pkgname=recipe['pkgname'], revision=recipe['revision'], is_revision=is_revision)
</section>
% end

<section class='box'>
    % for comment in comments:
    % include('comment', pkgname=recipe['pkgname'], revision=recipe['revision'], comment_id=comment['id'], comment_user=comment['user'], comment=comment['comment'], comment_date=comment['date'], is_revision=is_revision)
    % end
</section>

% # vim: set ts=8 sw=4 tw=0 ft=html :
