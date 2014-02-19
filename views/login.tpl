% rebase('html_base.tpl', title=_('PUR - Login'))

<section class='box login content-center clearfix'>
    <header>
        <a style='float:right; margin-top:8px;' href='/register'>{{_('Not registered?')}}</a>
        <h2>{{_('Login')}}</h2>
    </header>
    <article>
        % for error in errors:
        <span>{{error}}</span>
        % end
        <form id='register' class='width_33' method='post'>
            <input class='username' name='username' placeholder="{{_('Username')}}" required/>
            <input class='password' type='password' name='password' placeholder="{{_('Password')}}" required/>
            <input class='button' type='submit' value="{{_('Login')}}"/>
            {{!csrf_input()}}
        </form>
    </article>
</section>

% # vim: set ts=8 sw=4 tw=0 ft=html :
