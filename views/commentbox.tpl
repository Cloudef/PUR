% if not is_revision:
<form action="/comment/{{pkgname}}" method='POST'>
% else:
<form action="/comment/{{pkgname}}/{{revision}}" method='POST'>
% end
    <header>
        <div style='float:right;'><input type='submit' class='comment' value="{{_('Send')}}"/></div>
        <h2>{{_('Comment')}}</h2>
    </header>
    <textarea class='comment' name='comment'></textarea>
    {{!csrf_input()}}
</form>

% # vim: set ts=8 sw=4 tw=0 ft=html :
