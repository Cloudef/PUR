% rebase('html_base.tpl', title='PUR - {}'.format(title))
% sclass = ''
% if not user and results:
%    sclass = 'recipes'
% end
%
% page, column, order = options.split(',')
% page = int(page)
% def lpage(x, s):
%    url = '?p={},{},{}'.format(x, column, order)
%    return link(url, s)
% end

<section class='{{sclass}} box'>
    % if user:
    <header>
        <div style='float:right;'>
            {{!link('/user/{}/contributions'.format(user), _('contributions'))}} |
            {{!link('/user/{}/revisions'.format(user), _('revisions'))}} |
            {{!link('/user/{}/recipes'.format(user), _('recipes'))}}
        </div>
        <h2>{{title}}</h2>
    </header>
    % end
    <article>
        % if results:
        % include('results_table.tpl', recipes=results, options=options)
        % else:
        <p>{{_('No results')}}</p>
        % end
    </article>
</section>

% if matches:
<div class='clearfix'></div>
<div style='float:right;'>
% if page > 1 and page <= pages:
{{!lpage(1, '<<')}}
{{!lpage(page - 1, '<')}}
% end
{{page}}
% if page < pages:
{{!lpage(page + 1, '>')}}
{{!lpage(pages, '>>')}}
% end
</div>
<div style='float:left;'>{{matches}} matches found. Page {{page}} of {{pages}}</div>
% end

% # vim: set ts=8 sw=4 tw=0 ft=html :
