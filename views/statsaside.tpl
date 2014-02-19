<!-- statistics at right side of page -->
<aside class='content-right'>
    <section class='box recent clearfix'>
        <h3>Recent Updates</h3>
        % for recipe in recipes:
        <div class='col_50'>
            {{!link('/recipe/{}'.format(recipe['pkgname']), recipe['pkgname'])}}
        </div>
        <div class='col_50'>
            {{recipe['datemodify']}}
        </div>
        <div class='clearfix'></div>
        % end
    </section>
    <section class='box statistics clearfix'>
        <h3>Statistics</h3>
        <div class='col_75'>{{_('Recipes')}}</div>
        <div class='col_25'>{{num_recipes}}</div>
        <div class='clearfix'></div>
        <div class='col_75'>{{_('Contributors')}}</div>
        <div class='col_25'>{{num_users}}</div>
        <div class='clearfix'></div>
        <div class='col_75'>{{_('Moderators')}}</div>
        <div class='col_25'>{{num_users}}</div>
        <div class='clearfix'></div>
        <div class='col_75'>{{_('Registered users')}}</div>
        <div class='col_25'>{{num_users}}</div>
        <div class='clearfix'></div>
    </section>
</aside>

% # vim: set ts=8 sw=4 tw=0 ft=html :
