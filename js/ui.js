
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
        update_content('main_menu', url);
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

/** Append a sub-form for a nested compound object insidean existing form */
function add_property_panel(uri, parent_id, multiple, callbackFunction) {
    // Check if there is a div panel with the id corresponding to the given uri
    var p = $('#'+uri);
    if (p.length !== 0 && !multiple) {
        alert('Class '+uri+' already instantiated!');
        return;
    }
    var url = 'f?o='+uri
    $.get(url, function(data, status) {
        if (status !== 'success') {
            alert('Error: Cannot read from '+url);
            return;
        }
        $(data).appendTo($("#"+parent_id));
        if (callbackFunction !== undefined && callbackFunction !== null) {
            callbackFunction();
        }
    });
}

function show_message(m)
{
    $('#message').show();
    $('#message').fadeOut(5000);
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

function o_delete(callback) {
    if (!confirm('Are you sure ?'))
        return;
    var objects = [];

    $('div').each(function(idx) {
        if ($(this).hasClass('rdf-container')) {
            objects.push(this.getAttribute('id'));
        }
    });
    var url = 'd';
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

function o_save(e=null, stack=[], lvl=0, callback=null) {
    // Init
    if (e === null) {
        e = $('#form_object_edit');
    }
    if (stack.length == 0) {
         stack.push({id: 'root', i: null, data:[]});
         console.log('Initializing stack ...', stack.length);
    }
    c = stack[stack.length-1];
    if ($(e).hasClass('rdf-property') && $(e).hasClass('rdf-changed')) {
        var u = $(e).attr('u');
        var p = $(e).attr('p');
        var i = $(e).attr('i');
        var v = $(e).attr('type') == 'checkbox' ? $(e).prop('checked') :  $(e).val();
        c.data.push({p:p,i:i,v:v,u:u});
        console.log('level='+lvl, 'container=',c.id, ' u='+u+', p='+p+', i='+i+', v=', v);
    }
    if ($(e).hasClass('rdf-container')) {
        var id = $(e).attr('id');
        var i = $(e).attr('i');
        var u = $(e).attr('u');
        nc = {id: id, i: i, u: u, lvl: lvl, data: []};
        c.data.push(nc);
        stack.push(nc);
        console.log('Pushing in stack new container ...', stack.length, ' level: ', lvl, ' u=', u);
    }

    // Loop
    var l = $(e).children();
    if (l.length !== 0) {
       for (var i=0; i < l.length; i++) {
           // console.log('Recursin - level', lvl+1)
            o_save(l[i], stack, lvl+1, callback); // Recursion
       }
    }

    if ($(e).hasClass('rdf-container')) {
        stack.pop();
        console.log('Removing old container ...', stack.length, ' level: ', lvl);
    }

    // Finalize
    if (lvl == 0) {
        s = JSON.stringify(stack[0]);
        alert(s);

        url = 's';
        $.post(url, {data: s}, function(data, status){
            if (status === 'success') {
                show_message(data);
                if (callback !== null) { callback();}
            } else {
                alert("Error: " + status);}
        });
    }
}


function o_save_old_2(e=null, c=null, lvl=0, callback=null) {
    // Init
    if (e === null) {
        e = $('#form_object_edit');
    }
    if (c === null) {
         c = {id: 'root', i: null, data:[]};
    }
    nc = c;
    if ($(e).hasClass('rdf-container')) {
        var id = $(e).attr('id');
        var i = $(e).attr('i');
        var u = $(e).attr('u');
        nc = {id: id, i: i, u: u, lvl: lvl, data: []};
        console.log('Container: id='+id+', i='+i+', u=', u);
        c.data.push(nc);
    }
    if ($(e).hasClass('rdf-property')) {
        var u = $(e).attr('u');
        var p = $(e).attr('p');
        var i = $(e).attr('i');
        var v = $(e).attr('type') == 'checkbox' ? $(e).prop('checked') :  $(e).val();
        console.log('u='+u+', p='+p+', i='+i+', v=', v);
        nc.data.push({p:p,i:i,v:v,u:u});
    }
    // Loop
    var l = $(e).children();
    if (l.length !== 0) {

       for (var i=0; i < l.length; i++) {
            // Recursion
            o_save(l[i], nc, lvl+1, callback);
       }
    }
    // Finalize
    if (lvl == 0) {
        s = JSON.stringify(c);
        alert(s);
        url = 's';
        /*
        $.post(url, {data: s}, function(data, status){
            if (status === 'success') {
                show_message(data);
                if (callback !== null) {
                    callback();}
            } else {
                alert("Error: " + status);}
        });
        */
    }
}

function o_save_old(callback) {
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
    alert(s);
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

function o_delete_old(callback) {
    if (!confirm('Are you sure ?'))
        return;
    var objects = [];
    $("[h]").each(function(index){
        var h = this.getAttribute('h');
        objects.push(h);
    });
    var url = 'd';
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
