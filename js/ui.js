
function dc_view_data()
{
    url = '/html/srcbase.html';
    update_content('output', url);
}

function dc_reports()
{
    url = 'b?cn=custom_report';
    update_content('output', url);
}
function dc_view_reports()
{
    url = 'r?cn=custom_report';
    update_content('output', url);
}

function view_report(h)
{
    url = 'play?h='+h;
    window.open(url);
}

function handle_files(files, h) {
    var file = files[0];
    $('#img_thumb_'+h).attr('src', 'img/loading.gif');

    var formData = new FormData();
    formData.append('file', file);
    $.ajax({
        url: 'uplimg', // Specify the server-side script to handle the upload
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function(response) {
            //alert(response);
            $('#img_data_'+h).val(response);
            $('#img_data_'+h).addClass('rdf-changed');
            var img_data = JSON.parse(response);
            $('#img_thumb_'+h).attr('src', img_data.thumb);
        },
        error: function() {
            // Error handling
        }
    });
}

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

/** Append a sub-form for a nested compound object insidean existing form
    uri: URI of the property
    puri: URI of the parent object
    prop: Name of the property
    parent_id: The id of the panel, where to add teh snippet
    multiple: Flag whether it is allowed to add the property multiple ties
    callback: Callback function to be executed after this one
*/
function add_property_panel(uri, puri, prop, parent_id, multiple, callback) {
    // Check if there is a div panel with the id corresponding to the given uri
    var p = $('#'+uri);
    if (p.length !== 0 && !multiple) {
        alert('Class '+uri+' already instantiated!');
        return;
    }

    var valueReportModal = new bootstrap.Modal(document.getElementById('modal_1'), {});
//    valueReportModal.show();
    //url = '/vrep_per?acronym='+acronym+'&cik='+cik+'&h='+hash+'&capt='+capt;
    //$('#modal_1_title').html(capt);
    //update_content('div_value_report_body', url, null);

    var url = 'f?o=' + uri + '&p=' + puri + '&n=' + prop;
    $.get(url, function(data, status) {
        if (status !== 'success') {
            alert('Error: Cannot read from '+url);
            return;
        }
        $(data).appendTo($("#"+parent_id));
//        $('#modal_1_title').html(data);

        if (callback !== undefined && callback !== null) {
            callback();
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
    update_content("output", "e?h="+h, null);
}

/** Calls the "view" method with a given object hash */
function o_view(h) {
    update_content("output", "view?h="+h, null);
}

function o_new(uri) {
    update_content("output", "n?uri="+uri, null);
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
        //alert(s);
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


// Update class name drop down
function upd_class_name(add_all, callback)
{
    $.get('l?q=complex', function(data, status) {
        if (status === 'success') {
            var enums = JSON.parse(data);
            var arrayLength = enums.length;
            s = add_all ? '<option value="">--- all ---</option>' : '';
            for (var i = 0; i < arrayLength; i++) {
                e = enums[i];
                sel = e[0] == 'item' && !add_all ? ' selected="true" ' : '';
                s += '<option value="'+e[0]+'"'+sel+'">'+e[1]+'</option>';
            }
            $('#class_name').html(s);
            upd_property_name(add_all, callback);
        } else {
            alert("ERROR: " + status);
        }
    });
}

function upd_property_name(add_all, callback)
{
    var class_name = $('#class_name').val();
    $.get('l?q='+class_name+'.properties', function(data, status) {
        if (status === 'success') {
            var enums = JSON.parse(data);
            var arrayLength = enums.length;
            s = add_all ? '<option value="">--- all ---</option>' : '';
            for (var i = 0; i < arrayLength; i++) {
                e = enums[i];
                s += '<option value="'+e[0]+'">'+e[1]+'</option>>';
            }
            $('#property_name').html(s);
            if (callback !== 'undefined')
            {
                callback();
            }
        } else {
            alert("ERROR: " + status);
        }
    });
}