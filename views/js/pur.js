// PND User Repository Javascript
// Enchances PUR exprience when javascript is enabled
// pur.js

function _validate_forms(forms, strings) {
   $.getScript("/js/jquery.validate.min.js", function() {
      forms.validate({
         rules: {
           username: {
               required: true,
               minlength: 3,
           },
           email: {
               required: true,
               email: true,
           },
           password: {
               minlength: 8,
           },
           confirm_password: {
               equalTo: '#password'
           }
         },
         messages: {
              username: {
                  required: jQuery.format(strings['username_length'], 3),
                  minlength: jQuery.format(strings['username_length'])
              },
              password: {
                  required: jQuery.format(strings['password_length'], 8),
                  minlength: jQuery.format(strings['password_length'])
              },
              confirm_password: {
                  equalTo: strings['password_confirm']
              },
              email: {
                  required: strings['email'],
                  email: strings['email']
              }
         },
         errorElement: "span",
      });
   });
}

function validate_forms(forms)
{
   if (!forms.length)
      return;
   $.getJSON("/js/translations/register", function(strings) {
      _validate_forms(forms, strings);
   });
}

function _recipe_upload(buttons, strings)
{
   $.getScript("/js/SimpleAjaxUploader.min.js", function() {
      pbar = $('.progressbar')
      pbarerror = $('.progressbar-error')
      pbarcontainer = $('.progressbar-container')
      var uploader = new ss.SimpleUpload({
            button: buttons,
            url: '/upload',
            data: {'CSRF': strings['CSRF']},
            name: 'recipe',
            responseType: 'json',
            multipart: true,
            maxSize: 8192,
            accept: 'application/x-gzip',
            onSizeError: function(filename, fileSize) {
               pbarcontainer.slideDown(200);
               pbarcontainer.delay(2400).slideUp(200);
               pbarerror.show().text(strings['file_size']);
            },
            onSubmit: function(filename, ext) {
               pbar.show();
               pbarerror.hide();
               pbarcontainer.dequeue().slideDown(200);
               this.setProgressBar(pbar);
               this.setPctBox($('.progressbar-overlay'));
            },
            startXHR: function(filename, fileSize, uploadBtn) {
               $(uploadBtn).val(strings['cancel'])
               this.setAbortBtn(uploadBtn)
            },
            endXHR: function(filename, uploadBtn) {
               $(uploadBtn).val(strings['upload']);
            },
            onAbort: function(filename, uploadBtn) {
               $(uploadBtn).val(strings['upload']);
               pbar.hide();
               pbarcontainer.delay(2400).slideUp(200);
               pbarerror.show().text(strings['upload_cancel']);
            },
            onError: function(filename, errorType, status, statusText, response, uploadBtn) {
               $(uploadBtn).val(strings['upload']);
               pbar.hide();
               if (response) {
                  pbarerror.show().html(response.msg);
               } else {
                  pbarerror.show().text(status + ' ' + statusText);
               }
            },
            onComplete: function(filename, response) {
               pbar.hide();
               if (!response || (response.success === false && response.msg)) {
                  pbarerror.show().text(strings['no_response']);
                  return false;
               } else if (response.success === false) {
                  pbarerror.show().text(response.msg);
                  return false;
               }
               window.location.href = response.url;
            }
      });
   });
}

function recipe_upload(buttons)
{
   if (!buttons.length)
      return;
   $.getJSON("/js/translations/upload", function(strings) {
      _recipe_upload(buttons, strings);
   });
}

function recipe_search(searchBars)
{
   if (!searchBars.length)
      return;

   $.getScript("/js/typeahead.bundle.min.js", function() {
      // create recipes model
      var recipes = new Bloodhound({
         datumTokenizer: function(d) { return Bloodhound.tokenizers.whitespace(d.pkgname); },
         dupDetector: function(r, l) { return r.pkgname == l.pkgname; },
         queryTokenizer: Bloodhound.tokenizers.whitespace,
         limit: 10,
         // remote: '/search/%QUERY',
         prefetch: '/recipes'
      });

      // do the magic
      recipes.initialize();
      searchBars.typeahead(null, {
         displayKey: 'pkgname',
         source: recipes.ttAdapter()
      }).on("typeahead:selected", function(event, data, dataset) {
         window.location.href = "/recipe/" + encodeURIComponent(data.pkgname);
      });

      // setup keybinding
      $(document).keypress(function(e) {
         if (e.charCode == 102 && $('textarea:focus').length == 0 && $('input:focus').length == 0) {
            searchBars[0].focus();
            e.preventDefault();
         }
      });
   });
}

function hide_elements(elements)
{
   if (!elements.length)
      return;
   elements.hide();
}

function show_elements(elements)
{
   if (!elements.length)
      return;
   elements.show();
}

function togglable_elements(elements)
{
   if (!elements.length)
      return;

   elements.click(function(e) {
       ob = $(e.target)
       element = ob.parent().parent().find('article')
       if (ob.text() == '+') {
           ob.text('-');
           element.slideDown(200);
       } else {
           ob.text('+');
           element.slideUp(200);
       }
   });
}

function setup_pur()
{
   // no autocrap from mobile devices
   $(document).on('focus', ':input', function() {
       $(this).attr('autocomplete', 'off');
       $(this).attr('autocorrect', 'off');
       $(this).attr('autocapitalize', 'off');
   });

   // setup validation for registeration form
   validate_forms($('.js_register'));

   // setup recipe search for search inputs
   recipe_search($('input.search'));

   // setup ajax recipe upload
   recipe_upload($('.upload'));

   // hide elements
   hide_elements($('.js_hide'));

   // show elements
   show_elements($('.js_show'));

   // make elements togglable
   togglable_elements($('.js_toggle'));
}

$(document).ready(setup_pur);

// vim: set ts=8 sw=3 tw=0 :
