% rebase('html_base.tpl', title=_('PUR - Home'))

<div class='content-left clearfix'>
    <section class='box'>
        <header>
            <h2>{{header or _('PUR Home')}}</h2>
        </header>
        <article>
            % if content:
            {{!content}}
            % else:
            <p>{{_('Welcome to the PUR!')}}</p>
            <p>{{!_ML('Contributed PNDBUILDs __must__ conform to the [PNDPS:PND Packaging Standards] otherwise they will be deleted!')}}</p>
            %end
        </article>
    </section>
</div>

% include('statsaside.tpl')

% # vim: set ts=8 sw=4 tw=0 ft=html :
