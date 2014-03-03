% rebase('html_base.tpl', title=_('PUR - Upload'))

<section class='box'>
    <form action='/upload/store' method='POST'>
    <header>
        <div style='float:right;'>
            <input type='submit' name='cancel' value="{{_('Cancel')}}"/>
            <input type='submit' name='store' value="{{_('Proceed')}}"/>
        </div>
        <h2>{{_('Describe the changes in revision')}} ({{revision}})</h2>
    </header>
    <article>
            <textarea style='resize:none;height:16em;' name='changes' required></textarea>
            <input type='hidden' name='tgz' value='{{tgz}}'/>
            <input type='hidden' name='revision' value='{{revision}}'/>
            {{!csrf_input()}}
    </article>
    </form>
</section>

% # vim: set ts=8 sw=4 tw=0 ft=html :
