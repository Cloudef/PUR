% rebase('html_base.tpl', title=_('PUR - My Account'))

<section class='box'>
    <header>
        <h2>{{_('My Account')}}</h2>
    </header>
    <article>
        <form action='/user/{{USER['name']}}/edit'>
            <input class='email' name='email' placeholder="{{_('E-Mail')}}" value="{{USER['email']}}"/><br/>
            <input class='password' name='password' placeholder="{{_('New Password')}}"/><br/>
            <input class='password' name='password_confirm' placeholder="{{_('New Password')}}"/><br/>
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
            geodata = data.get('geodata')
        %>
        <div class='session'>
            <header>
                % if client and client.get('ua_icon'):
                <img src="/images/ua/{{client.get('ua_icon')}}" alt="User-Agent"/>
                % end
                % if client and client.get('os_icon'):
                <img src="/images/os/{{client.get('os_icon')}}" alt="OS"/>
                % end
                % if session == USER['session']:
                <strong>{{_('Current')}}</strong>
                % else:
                {{!referrer_csrf_link('/revoke/{}'.format(session), _('Revoke'))}}
                %end
                <div style='float:right;'>IP: {{data.get('IP') or _('Unknown IP')}}</div>
            </header>
            <article>
                % if client:
                {{client.get('ua_name')}} on {{client.get('os_name')}}<br/>
                % if data.get('agent'):
                {{data.get('agent')}}<br/>
                % end
                % else:
                {{_('Unknown Client')}}<br/>
                % end
                % if geodata and geodata.get('city'):
                {{geodata['city']}}, {{geodata['country_name']}}
                % else:
                {{_('Unknown Location')}}
                % end
            </article>
        </div>
        % end
        </div>
    </article>
</section>

% # vim: set ts=8 sw=4 tw=0 ft=html :
