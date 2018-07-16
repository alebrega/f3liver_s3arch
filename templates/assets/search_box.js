(function(){

/* Load Script function we may need to load jQuery from the Google's CDN */
/* That code is world-reknown. */
/* One source: http://snipplr.com/view/18756/loadscript/ */

var loadScript = function(url, callback){



  var script = document.createElement("script");
  script.type = "text/javascript";

  // If the browser is Internet Explorer.
  if (script.readyState){
    script.onreadystatechange = function(){
      if (script.readyState == "loaded" || script.readyState == "complete"){
        script.onreadystatechange = null;
        callback();
      }
    };
  // For any other browser.
  } else {
    script.onload = function(){
      callback();
    };
  }

  script.src = url;
/*
  var link = document.createElement("link");
  link.rel = "stylesheet";
  link.integrity="sha384-lKuwvrZot6UHsBSfcMvOkWwlCMgc0TaWr+30HWe3a4ltaBwTZhyTEggF5tJv8tbt";
  link.crossorigin="anonymous";
  link.href="https://use.fontawesome.com/releases/v5.1.0/css/all.css";
*/

  document.getElementsByTagName("head")[0].appendChild(link);


};

var myAppJavaScript = function($){

var span = document.getElementsByClassName("Feliver_close")[0];
span.onclick = function() {
    var modal = document.getElementById('Feliver_myModal');
    modal.style.display = "none";
}
window.onclick = function(event) {
    if (event.target == modal) {
        var modal = document.getElementById('Feliver_myModal');
        modal.style.display = "none";
    }
}

$( "input[name=q]" ).click(function() {
  var modal = document.getElementById('Feliver_myModal');
  modal.style.display = "block";
  let searchParams = new URLSearchParams(window.location.search);
  if (searchParams.has('q')){
    $( "input[name=q]" ).val(searchParams.get('q'));
  }
  $('#Feliver_myModal').focus();
});

/*
  height=$( "input[name=q]" ).css('font-size');
  if (!height || height=='0px' || parseFloat(height)<36 ){
      height = (parseFloat(height)+10)+'px';
  }
  $( "input[name=q]" ).before('<button OnClick="alert(\'hola\');" style="background: none; border: 0px; cursor: pointer; font-size: '+height+'; padding-right: 3%;" class="fas fa-camera">');
  $( "input[name=q]" ).after('</button>');
*/
  /*
  var camera = '<a style="font-size: '+height+'; padding-left: 3%; padding-right: 3%;" href="#" OnClick="alert(\'hola\');"><i class="fas fa-camera"></i></a>';
  if (height=='100%' ){
    $( "input[name=q]" ).css('width','90%');
  }
  $( "input[name=q]" ).after(camera);
*/
};

/* If jQuery has not yet been loaded or if it has but it's too old for our needs,
we will load jQuery from the Google CDN, and when it's fully loaded, we will run
our app's JavaScript. Set your own limits here, the sample's code below uses 1.7
as the minimum version we are ready to use, and if the jQuery is older, we load 1.9. */
if ((typeof jQuery === 'undefined') || (parseFloat(jQuery.fn.jquery) < 1.7)) {
  loadScript('//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js', function(){
    jQuery191 = jQuery.noConflict(true);
    myAppJavaScript(jQuery191);
  });
} else {
  myAppJavaScript(jQuery);
}
})();
