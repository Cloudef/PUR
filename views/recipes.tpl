% rebase('html_base.tpl', title=_('PUR - Recipes'))

<section class='box'>
    % if user:
    <header>
        <h2>{{_('Recipes by')}} {{user}}</h2>
    </header>
    % end
    <article>
        % if recipes:
        % include('recipes_table.tpl', recipes=recipes)
        % else:
        <p>{{_('No recipes')}}</p>
        % end
    </article>
</section>
% if recipes:
<div class='clearfix'>
<div style='float:right;'>1</div>
<div style='float:left;'>{{len(recipes)}} recipes found. Page 1 of 1</div>
</div>
% end

% if user and revisions:
<section class='box'>
    <header>
        <h2>{{_('Revisions by')}} {{user}}</h2>
    </header>
    <article>
    % include('recipes_table.tpl', recipes=revisions)
    </article>
</section>
% end

% if user and contributions:
<section class='box'>
    <header>
        <h2>{{_('Contributions by')}} {{user}}</h2>
    </header>
    <article>
    % include('recipes_table.tpl', recipes=contributions)
    </article>
</section>
% end

% # vim: set ts=8 sw=4 tw=0 ft=html :
