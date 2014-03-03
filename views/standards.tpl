% rebase('html_base.tpl', title=_('PUR - Standards'))

<div class='content-left clearfix'>
    <section class='box'>
        <header>
            <h2>{{_('PNDBUILDs')}}</h2>
        </header>
        <article>
            <p>
            {{!_ML('Why should I...')}}
            </p>
        </article>
    </section>
    <section class='box'>
        <header>
            <h2>{{_('PND Containers')}}</h2>
        </header>
        <article>
            <p>
            {{!_ML('...even care...')}}
            </p>
        </article>
    </section>
</div>

% include('statsaside.tpl')

% # vim: set ts=8 sw=4 tw=0 ft=html :
