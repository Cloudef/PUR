% # togglable javascript element

<div class='js_togglable'>
    % if right:
    <div style='float:right;'>{{!right}}</div>
    % end
    <header>
    {{!header}} <button class='js_toggle js_show'>{{'+' if hidden else '-'}}</button>
    </header>
    <article class="{{not hidden or 'js_hide'}}">
    {{!content}}
    </article>
</div>

% # vim: set ts=8 sw=4 tw=0 ft=html :
