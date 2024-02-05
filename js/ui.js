
/** Reads current user and then initializes some UI parts based on user settings. */
function ui_init()
{
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
        var lang = user["lang"];
        var role = user["role"]

        if (user["authenticated"])
        {
            $("#btn_username").html(user["name"])
            $("#logged_in").show();
        }
        else
        {
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
        $('#'+containerId).html(data);
        if (callbackFunction !== undefined && callbackFunction !== null) {
            callbackFunction();
        }
    });
}

/** Calls the "e" method with a given object hash */
function o_edit(h) {
    update_content("output", "e?h="+h, null)
}

function o_save() {
    var objects = {};
    $("[h]").each(function(index){
        var h = this.getAttribute('h');
        var p = this.getAttribute('p');
        var v = $(this).val();
        o = objects[h];
        if (o === undefined) {
            o = {};
            objects[h] = o;
        }
        o[p] = v;
    });
    var url = 's';
    s = JSON.stringify(objects);
    $.post(url, {data: s}, function(data, status){
        if (status === 'success') {
            alert(data);
        } else {
            alert("ERROR: " + status);
        }
    });
}