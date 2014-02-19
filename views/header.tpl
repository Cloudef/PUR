<div class='content-left'>
   <h1>
      {{_('PND User Repository')}}
      % if PURBETA:
      <div style='display:inline;font-size:x-small;color:red;'>βeta</div>
      % end
   </h1>
</div>
<div class='content-right'>
   % if USER:
   <div style='display:none;' class='progressbar-container'>
      <div class='progressbar-error'></div>
      <div class='progressbar'>
         <div class='progressbar-overlay'></div>
      </div>
   </div>
   % end
   <div class='col_33'>
         % if USER:
         <form action='/upload' method='POST' enctype='multipart/form-data'>
            <input type='submit' class='upload' value="{{_('Upload')}}"/>
            <noscript><input type='file' name='recipe'/></noscript>
            {{!csrf_input()}}
         </form>
         % else:
         <form action='/login' method='GET'>
            <input type='submit' class='login' value="{{_('Login')}}"/>
         </form>
         % end
   </div>
   <div class='col_33'>
      <form action='/search' method='GET'>
         <input class='search' name='q'/>
         <input type='submit' style='visibility:hidden; position:fixed;'/>
      </form>
   </div>
   <div class='clearfix'></div>
</div>

% # vim: set ts=8 sw=4 tw=0 ft=html :
