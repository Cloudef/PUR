<%
    styles = []
    for style in PURSTYLES:
        if not USER and style == 'moe':
            continue
        end
        styles.append(referrer_csrf_link('/style/{}'.format(style), style))
    end

    langs = []
    for lang in PURTRANSLATIONS:
        langs.append(referrer_csrf_link('/lang/{}'.format(lang), lang))
    end

    stylenav = ' | '.join(styles)
    langnav = ' | '.join(langs)
%>

<div class='langnav'>{{!langnav}}</div>
<div class='stylenav'>{{!stylenav}}</div>
PUR {{PURVERSION}}<br/>
PND recipes are user produced content. Any use of the provided files is at your own risk.

% # vim: set ts=8 sw=4 tw=0 ft=html :
