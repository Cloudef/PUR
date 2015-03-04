% rebase('html_base.tpl', title=_('PUR - My Account'))

<section class='box errors'>
    <header>
        <h2>
            {{_('My Account')}}
            % titles = {LEVELS['moderator']: 'moderator', LEVELS['admin']: 'admin'}
            % if USER['level'] in titles:
            ({{titles[USER['level']]}})
            % end
        </h2>
    </header>
    <article>
        % for error in errors:
        <span>{{error}}</span>
        % end
        <form class='content-center js_register' method='POST'>
            <input class='email' name='email' placeholder="{{_('E-Mail')}}" value="{{USER['email']}}" required/>
            <input type='password' class='password' name='password' placeholder="{{_('New Password')}}"/>
            <input type='password' class='password' name='password_confirm' placeholder="{{_('New Password')}}"/>
            <input type='submit' class='button' value="{{_('Update Information')}}"/>
            {{!csrf_input()}}
        </form>
        <h3 class='header'>{{_('Sessions')}}</h3>
        <div class='sessions'>
        <%
        for session in USER.get('sessions'):
            data = get_session(session)
            if not data:
                continue
            end
            client = data.get('client')
        %>
        <div class='session'>
            <header>
                % if session == USER['session']:
                <strong>{{_('Current')}}</strong>
                % else:
                {{!referrer_csrf_link('/revoke/{}'.format(session), _('Revoke'))}}
                %end
                <div style='float:right;'>IP: {{data.get('IP') or _('Unknown IP')}}</div>
            </header>
            <article>
            </article>
        </div>
        % end
        </div>
    </article>
</section>

% # vim: set ts=8 sw=4 tw=0 ft=html :
