
/** Reads current user and then initializes some UI parts based on user settings. */
function ui_init() {
    $.getJSON( "../assets/mlang.json", function( ml ) {
        var items = [];
        data = ml["root"];
        mlang = ml;
        $.each( data, function( key, val ) {
            items.push( "<button class=\"btn btn-light btn-sm\" onclick=\"ui_mlang('"+key+"')\" type=\"button\"><img src=\"../img/"+key+".svg\" width=\"30px\" height=\"30px\"/></button>" );
        });
        $("#pane_mlang").html(items.join( "" ));
    });
    $.getJSON( "/user", function( user ) {
        var lang = user["lang"].split('|')[0];
        var role = user["role"].split('|')[0];
        var username = user["name"].split('|')[0];
        if (user["authenticated"]) {
            $("#btn_username").html(username);
            $("#logged_in").show();
        } else {
            $("#logged_out").show();
        }
        // Inject menu
        url = '/html/menu_'+role+'.html';
        update_content('main_menu', url)
        // Refresh multilanguage strings
        ui_mlang(lang);
    });
}

/** Sets multi language strings to UI controls */
function ui_mlang(lang)
{
    if (lang === undefined) {
        lang = $('#status_mlang').html(); // reads lang value from UI
    } else {
        $('#status_mlang').html(lang); // sets an explicit lang value
    }
    $("h1,h2,h3,h4,h5,span,button,a,label,p").each(function(index){
        var key = this.getAttribute('mlang');
        if(key !== '' && key !== null) {
            if (mlang[key] !== null && mlang[key] !== undefined) {
                var txt = mlang[key][lang];
                if (txt !== '')
                    this.innerHTML = txt;
            }
        }
    });
}

/** Injects HTMl content into a specific container element. The content is taken from the given URL. */
function update_content(containerId, url, callbackFunction)
{
    $('#'+containerId).html('<img src="../img/loading.gif" />');
    $.get(url, function(data, status) {
        if (status !== 'success') {
            $('#'+containerId).html('<div style="background-color: Red; color: White;">Error: Cannot read from '+url+'</div>');
            return;
        }
        $('#'+containerId).html(format_message(data));
        if (callbackFunction !== undefined && callbackFunction !== null) {
            callbackFunction();
        }
    });
}

function show_message(m)
{
    $('#message').html(format_message(m));
}

function format_message(m) {
    if (m.toLowerCase().startsWith('error'))
        return '<div style="background-color: #f0a0a0;">'+m+'</div>';
    if (m.toLowerCase().startsWith('>'))
        return '<div style="background-color: #a0f0a0;">'+m.substring(1,m.length)+'</div>';
    return m;
}

/** Calls the "e" method with a given object hash */
function o_edit(h) {
    update_content("output", "e?h="+h, null)
}

function o_new(uri) {
    update_content("output", "n?uri="+uri, null)
}

function o_save(callback) {
    var objects = [];
    $("[h]").each(function(index){
        var h = this.getAttribute('h');
        var p = this.getAttribute('p');
        var i = this.getAttribute('i');
        var u = this.getAttribute('u');
        var v = $(this).val();
        objects.push([p,h,i,v,u]);
    });
    var url = 's';
    s = JSON.stringify(objects);
    $.post(url, {data: s}, function(data, status){
        if (status === 'success') {
            show_message(data);
            if (callback !== null) {
                callback();
            }
        } else {
            alert("Error: " + status);
        }
    });
}