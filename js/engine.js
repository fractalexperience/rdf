
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function update_rdf_object(
    dataTableName, btnId, containerId, className, 
    parentClassName, objectCodeControlId, parentObjectCodeControlId,
    callbackFunction)
{
    var code = $('#'+objectCodeControlId).val(); 
    var parentCode = $('#'+parentObjectCodeControlId).val();  
    var obj = {
        dataTable: dataTableName,
        className: className, 
        parentClassName: parentClassName, 
        code: code, 
        parent: parentCode
    };
    $('#'+containerId).find('input,textarea,select').each(function(k,v) {
        var propertyName = v.getAttribute("id");
        var propertyValue = v.getAttribute("type")=="checkbox" ? v.checked : v.value;
        obj[propertyName] = propertyValue;
    });
    var url = "../api/update_rdf.php";
    var isNew = $("#"+objectCodeControlId).val() === '';
    $.post(url, obj, function(data, status){
        if (status === "success") {
            //alert(data);
            $("#"+objectCodeControlId).val(data);            
        } else {
            alert("ERROR: " + status);
        }
        callbackFunction();
        //clearUnsaved(containerId);        
        //if (isNew)
        //    GotoRDFObject('', className, parentClassName, objectCodeControlId, parentObjectCodeControlId, 'last', containerId);
    });
    
    
    //update_input(btnId, className, parentClassName, objectCodeControlId, parentObjectCodeControlId, obj, containerId);  
}

function delete_rdf_object(
    dataTableName, btnId, containerId, className, 
    parentClassName, objectCodeControlId, parentObjectCodeControlId,
    callbackFunction)
{
    var code = $('#'+objectCodeControlId).val(); 
    var parentCode = $('#'+parentObjectCodeControlId).val();  
    var url = '../api/delete_rdf.php?'
        +'dataTable='+dataTableName
        +'&code='+code
        +'&className='+className
        +(parentClassName !== null ? '&parentClassName=' + parentClassName : '')
        +(parentCode !== null ? '&parentCode='+parentCode : '');
    $.get(url, function(data, status){
        if (status === "success") {
            //alert(data);
            $("#"+objectCodeControlId).val('');
        } else {
            alert("ERROR: " + status);
        }
        callbackFunction();
        //clearUnsaved(containerId);        
        //if (isNew)
        //    GotoRDFObject('', className, parentClassName, objectCodeControlId, parentObjectCodeControlId, 'last', containerId);
    });
}


function isUnsaved(containerId) {
    return $('#'+containerId+'_unsaved').html() === '#';  
}

function raiseUnsaved(containerId) {
    $('#'+containerId+'_unsaved').html('#');    
    calculateUnsaved();
}

function clearUnsaved(containerId) {
    $('#'+containerId+'_unsaved').html('_');  
    calculateUnsaved();
}

function calculateUnsaved() {
    var result = false;
    result = result || $('#input_chronikjahr_unsaved').html() === '#'; 
    result = result || $('#input_media_unsaved').html() === '#'; 
    result = result || $('#input_leitung_unsaved').html() === '#'; 
    result = result || $('#input_lager_unsaved').html() === '#'; 
    result = result || $('#input_veranstaltung_unsaved').html() === '#'; 
    result = result || $('#input_pfadiheim_unsaved').html() === '#'; 
    var html = result ? '#' : '_';
    $('#input_all_unsaved').html(html);
}

function ClearInput(container_id, flag_force_clear) {       
    if (!flag_force_clear 
        && !( !isUnsaved(container_id) 
              || confirm('Sie haben nicht speicherten Daten. Wollen Sie weiterghen ?')))
        return;
    
    $('#'+container_id).find('input').val('');
    $('#'+container_id).find('input').prop('checked', false);
    $('#'+container_id).find('textarea').val('');
    $('#'+container_id).find('img').attr('src', '../img/picture.png');
    $('#'+container_id).find('[data-toggle="position"]').html(''); // clear position indicators
    
    clearUnsaved(container_id);
}

function UpdateInput(btnId, className, parentClassName, objectCodeControlId, parentObjectCodeControlId, obj, containerId) {
    //alert(objectCodeControlId);

    var url = "../api/update_rdf.php";
    var btnContent = $("#"+btnId).html();
    var isNew = $("#"+objectCodeControlId).val() === '';
    $("#"+btnId).html('<img width="20px" src="../img/processing.gif"/>');     
    
    $.post(url, obj, function(data, status){
        if (status === "success") {
            //alert(data);
            $("#"+objectCodeControlId).val(data);            
        } else {
            alert("ERROR: " + status);
        }
        $("#"+btnId).html(btnContent);
        clearUnsaved(containerId);
        
        if (isNew)
            GotoRDFObject('', className, parentClassName, objectCodeControlId, parentObjectCodeControlId, 'last', containerId);
    });
}

function UpdateRDFObject(
    btnId, containerId, className, parentClassName, objectCodeControlId, 
    parentObjectCodeControlId, containerId)
{
    //alert(containerId);
    var code = $('#'+objectCodeControlId).val(); 
    var parentCode = $('#'+parentObjectCodeControlId).val();  
    if (parentCode === '') {
        alert('Kein '+parentClassName+' angegeben!');
        return;
    }

    var obj = {
        className: className,
        parentClassName: parentClassName,
        code: code,
        parentCode: parentCode        
    }
    $('#'+containerId).find('input').each(function(k,v) {
        obj[v.getAttribute("id")] = v.getAttribute("type")=="checkbox" ? v.checked : v.value; 
    }); // single line text
    $('#'+containerId).find('textarea').each(function(k,v) {
        obj[v.getAttribute("id")] = v.value.replace(/[\""]/g, '\\"').replace(/[\n"]/g, '\\n'); 
    }); // multi line text
    
    //alert('-->'+JSON.stringify(obj));
    
    UpdateInput(btnId, className, parentClassName, objectCodeControlId, parentObjectCodeControlId, obj, containerId);  
}

function DeleteRDFObject(
        btnId, className, parentClassName, objectCodeControlId,
        parentObjectCodeControlId, containerId) {
    var msg = 'Soll das Object definitiv gelöscht werden?';
    if (!confirm(msg)) {
        return;
    }
    
    var parentCode = parentObjectCodeControlId === '' ? '' : $('#'+parentObjectCodeControlId).val();
    var code = objectCodeControlId === '' ? '' : $('#'+objectCodeControlId).val();

    var url = '../api/delete_rdf.php'
            +'?className='+className
            +'&parentClassName='+parentClassName
            +'&code='+code
            +"&parentCode="+parentCode;
    //alert(url);
    if (btnId !== '') {
        var btnContent = $('#'+btnId).html();
        $('#'+btnId).html(' <img width="20px" src="../img/processing.gif"/>');
    }
   
    $.get(url, function(data, status) {
        if (status === "success") {
            if (data=="null") {
                //alert("No data found for "+cjCode);
            } else {
                //alert(data);
                var obj = JSON.parse(data);
                ClearInput(containerId);
                alert(obj['message']);
            }
        } else { alert("ERROR: " + status); }
        if (btnId != '') { $('#'+btnId).html(btnContent); }
    });    
}

function GotoRDFObject(btnId, className, parentClassName, objectCodeControlId,
        parentObjectCodeControlId, gotoInstruction, containerId, flag_force_go) {
            
    var parentCode = $('#'+parentObjectCodeControlId).val();
    var code =  $('#'+objectCodeControlId).val();
    var msg = 'Sie haben nicht speicherten Daten. Wollen Sie weiterghen ?';
    if (!flag_force_go
        && !( !isUnsaved(containerId) 
              || confirm(msg)))
        return;
    // TO CHECK!
    ClearInput(containerId, true);

    var url = '../api/rdfobject.php'
            +'?class_name='+className
            +'&parent_class_name='+parentClassName
            +'&code='+code
            +"&parent_code="+parentCode
            +"&goto="+gotoInstruction;

    if (btnId != '') {
        var btnContent = $('#'+btnId).html();
        $('#'+btnId).html(' <img width="20px" src="../img/processing.gif"/>');
    }   
    $.get(url, function(data, status){
        if (status === "success")
        {
            if (data=="null") {
                var msg = 'No data found';
                //alert(msg);
            } else {
                //alert(data);
                var obj = JSON.parse(data);
                if (obj.Name !== null) {
                    
                    var thumb_path = '';
                    var media_path = '';
                    for (var item in obj) {
                        if (item==='thumb_path')
                            thumb_path=obj[item];
                        if (item==='media_path')
                            media_path=obj[item];
                    }
                    
                    for (var item in obj) {
                        if (item === 'Code') {                        
                            $('#'+objectCodeControlId).val(obj[item]);
                        } else {
                            if (item=='position') // Exception - indicate object position
                                $('#'+className+'_position').html(obj[item]);
                            
                            $('#'+item).val(obj[item]);
                            $('#'+item).prop('checked', (obj[item] === 'true'));
                            $('#img_'+item).attr('src',thumb_path+'/'+obj[item]);
                            $('#a_'+item).attr('href',media_path+'/'+obj[item]);
                        }
                    } 
                    clearUnsaved(containerId);
                }
            }
        }
        else { alert("ERROR: " + status); }
        if (btnId != '') { $('#'+btnId).html(btnContent); }
    });
}

function update_input(
        btnId, className, parentClassName, objectCodeControlId, 
        parentObjectCodeControlId, obj, containerId) {
    //alert(objectCodeControlId);
    var url = "../api/update.php";
    var btnContent = $("#"+btnId).html();
    var isNew = $("#"+objectCodeControlId).val() === '';
    $("#"+btnId).html('<img width="20px" src="../img/processing.gif"/>');    
    $.post(url, obj, function(data, status){
        if (status === "success") {
            //alert(data);
            $("#"+objectCodeControlId).val(data);            
        } else {
            alert("ERROR: " + status);
        }
        $("#"+btnId).html(btnContent);
        clearUnsaved(containerId);
        
        if (isNew)
            GotoRDFObject('', className, parentClassName, objectCodeControlId, parentObjectCodeControlId, 'last', containerId);
    });
}


function gen_password( len ) {
    var length = (len)?(len):(10);
    var string = "abcdefghijklmnopqrstuvwxyz"; //to upper 
    var numeric = '0123456789';
    var punctuation = '!@#$%^&*()_+~`|}{[]\:;?><,./-=';
    var password = "";
    var character = "";
    while( password.length<length ) {
        entity1 = Math.ceil(string.length * Math.random()*Math.random());
        entity2 = Math.ceil(numeric.length * Math.random()*Math.random());
        entity3 = Math.ceil(punctuation.length * Math.random()*Math.random());
        hold = string.charAt( entity1 );
        hold = (password.length%2==0)?(hold.toUpperCase()):(hold);
        character += hold;
        character += numeric.charAt( entity2 );
        character += punctuation.charAt( entity3 );
        password = character;
    }
    password=password.split('').sort(function(){return 0.5-Math.random()}).join('');
    return password.substr(0,len);
}


