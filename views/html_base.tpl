<!DOCTYPE html>
<html>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{{title}}</title>
<link rel='shortcut icon' href='/favicon.ico'/>
<link rel='stylesheet' href='/css/style.css'/>
<link rel='stylesheet' href='/css/syntax.css'/>
<link rel='stylesheet' href='/css/{{PURSTYLE}}'/>
<script src='/js/jquery-1.11.0.min.js'></script>
<script src='/js/pur.js'></script>
</head>
<body>
<!--[if lt IE 9 ]>
<div class='topblock'>
<p>Please update your browser (Firefox, Webkit based browsers, IE9 or later)</p>
<p><a href="http://www.mozilla.org/firefox/new/"><img src="/images/firefox.png" alt="firefox"></a></p>
<![endif]-->

<div class='container'>

    <!-- page header -->
    <header class='header clearfix'>
        % include('header')
    </header>

    <!-- navigation -->
    <nav class='navigation clearfix'>
        <%
            sites = []
            for site in PURNAVSITES:
                if site.get('csrf') is True:
                    sites.append(csrf_link(site['url'], site['name']))
                else:
                    sites.append(link(site['url'], site['name']))
                end
            end
            sitenav = ' | '.join(sites)
        %>
        {{!sitenav}}
    </nav>

    <!-- page content -->
    <section class='content clearfix'>
        {{!base}}
    </section>

    <!-- page footer -->
    <footer class='footer clearfix'>
        % include('footer')
    </footer>

</div>

<!--[if lt IE 9 ]>
<script>
$('.container').hide()
</script>
<![endif]-->
</body>
</html>

% # vim: set ts=8 sw=4 tw=0 ft=html :
