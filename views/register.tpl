% rebase('html_base.tpl', title=_('PUR - Register'))

<section class='box login content-center clearfix'>
    <header>
        <a style='float:right; margin-top:8px;' href='/login'>{{_('Already registered?')}}</a>
        <h2>{{_('Register')}}</h2>
    </header>
    <article>
        % if content:
        {{!content}}
        % else:
        % for error in errors:
        <span>{{error}}</span>
        %end
        <form class='js_register width_33' method='post'>
            <input class='username' name='username' placeholder="{{_('Username')}}" required/>
            <input class='email' name='email' placeholder="{{_('alien@ufo.com')}}" required/>
            <input id='password' class='password' type='password' name='password' placeholder="{{_('Password')}}" required/>
            <input class='password' type='password' name='confirm_password' placeholder="{{_('Password')}}" required/>
            <input class='button' type='submit' value="{{_('Register')}}"/>
            {{!csrf_input()}}
        </form>
        % end
    </article>
</section>

% # vim: set ts=8 sw=4 tw=0 ft=html :
