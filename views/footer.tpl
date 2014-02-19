<%
    styles = []
    for style in PURSTYLES:
        styles.append(csrf_link('/style/{}'.format(style), style))
    end

    langs = []
    for lang in PURTRANSLATIONS:
        langs.append(csrf_link('/lang/{}'.format(lang), lang))
    end

    stylenav = ' | '.join(styles)
    langnav = ' | '.join(langs)
%>

<div class='langnav'>{{!langnav}}</div>
<div class='stylenav'>{{!stylenav}}</div>
PUR {{PURVERSION}}<br/>
PND recipes are user produced content. Any use of the provided files is at your own risk.

% # vim: set ts=8 sw=4 tw=0 ft=html :
