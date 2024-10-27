
/** Invokes display of login dialog */
function do_login()
{
    update_content("output", "chunk?name=login", null);
}

/** Invokes display of "Change password" dialog */
function handle_forgot_password() {
    update_content("output", "chunk?name=forgot_password", null);
}

/** Handles user credentials during login */
function handle_login() {
    var msg = '';
    var username = $('#login_username').val();
    if (!is_valid_user_name(username)) {
        msg += 'Invalid username<br/>';
    }
    var pwd = $('#login_pwd').val();
    if (pwd === '') {
        msg += 'Empty password</br>';
    }
    $('#login_message').html(msg);
    if (msg === '') {
        var url = 'user';
        var obj = {usr: username, pwd: pwd};
        $.post(url, obj, function(data, status){
            if (status === 'success') {
                var user = JSON.parse(data);
                if (user === null || !user["authenticated"]) {
                    msg += 'User name or password not recognized!';
                    $('#login_message').html(msg);
                } else {
                    location.reload();
                }
            } else {
                alert("ERROR: " + status);
            }
        });
    }
}

/** Request logout (destroying user session) */
function handle_logout()
{
    var url = 'logout';
    $.get(url, function(data, status) {
    if (status === 'success') {
        location.reload();
    }});
}

/** Requests display of user settings dialog */
function handle_settings() {
    update_content('output', 'chunk?name=user_settings', function() {
        $.get('user', function(data, status) {
            if (status === 'success') {
                var user = JSON.parse(data);
                if (user === null || !user["authenticated"]) {
                    msg += 'Not authenticated!';
                    $('#login_message').html(msg);
                } else {
                    $('#User_Full_Name').val(user.name.split('|')[0]);
                    $('#User_Email').val(user.email.split('|')[0]);

                    $('#User_Full_Name').attr('p', 'Name');
                    $('#User_Email').attr('p', 'Email');

                    $('#User_Full_Name').attr('h', user.hash);
                    $('#User_Email').attr('h', user.hash);

                    $('#User_Full_Name').attr('i', user.name.includes('|') ? user.name.split('|')[1] : null);
                    $('#User_Email').attr('i', user.email.includes('|') ? user.email.split('|')[1] : null);
                }
            } else {
                alert("ERROR: " + status);
            }
        });
    })
}
/** Requests display of user settings dialog */
function handle_org_settings() {
    update_content('output', 'chunk?name=org_settings', function() {
        var msg = '';
        $.get('org', function(data, status) {
            if (status === 'success') {
                alert(data);
                var org = JSON.parse(data);
                if (org === null) {
                    msg += 'Unknown organization!';
                    $('#login_message').html(msg);
                } else {
                    $('#Org_Full_Name').val(org.name.split('|')[0]);
                    $('#Org_Description').val(org.description.split('|')[0]);

                    $('#Org_Children').val(org.children.split('|')[0]);
                    $('#Org_Children').attr('checked', org.children.split('|')[0]);

                    $('#Org_Wheelchair').val(org.wheelchair.split('|')[0]);
                    $('#Org_Cafe').val(org.cafe.split('|')[0]);
                    $('#Org_WC').val(org.wc.split('|')[0]);
                    $('#Org_Parking').val(org.parking.split('|')[0]);
                    $('#Org_Card').val(org.card.split('|')[0]);

                    $('#Org_Address1').val(org.address1.split('|')[0]);
                    $('#Org_Address2').val(org.address2.split('|')[0]);
                    $('#Org_City').val(org.city.split('|')[0]);
                    $('#Org_ZIP').val(org.zip.split('|')[0]);
                    $('#Org_Country').val(org.country.split('|')[0]);

                    $('#Org_Full_Name').attr('p', 'Name');
                    $('#Org_Description').attr('p', 'Description');
                    $('#Org_Children').attr('p', 'Suitable for children');
                    $('#Org_Wheelchair').attr('p', 'Wheelchair accessible');
                    $('#Org_Cafe').attr('p', 'Restaurant/Cafe');
                    $('#Org_WC').attr('p', 'WC');
                    $('#Org_Parking').attr('p', 'Parking');
                    $('#Org_Card').attr('p', 'Museums Card');
                    $('#Org_Address1').attr('p', 'Address line 1');
                    $('#Org_Address2').attr('p', 'Address line 2');
                    $('#Org_City').attr('p', 'City');
                    $('#Org_ZIP').attr('p', 'ZIP code');
                    $('#Org_Country').attr('p', 'Country');

                    $('#Org_Full_Name').attr('u', 'name');
                    $('#Org_Description').attr('u', 'description');
                    $('#Org_Children').attr('h', org.hash);
                    $('#Org_Wheelchair').attr('h', org.hash);
                    $('#Org_Cafe').attr('h', org.hash);
                    $('#Org_WC').attr('h', org.hash);
                    $('#Org_Parking').attr('h', org.hash);
                    $('#Org_Card').attr('h', org.hash);
                    $('#Org_Address1').attr('h', org.hash);
                    $('#Org_Address2').attr('h', org.hash);
                    $('#Org_City').attr('h', org.hash);
                    $('#Org_ZIP').attr('h', org.hash);
                    $('#Org_Country').attr('h', org.hash);

                    $('#Org_Full_Name').attr('i', org.name.includes('|') ? org.name.split('|')[1] : null);
                    $('#Org_Description').attr('i', org.description.includes('|') ? org.description.split('|')[1] : null);
                    $('#Org_Children').attr('i', org.children.includes('|') ? org.children.split('|')[1] : null);
                    $('#Org_Wheelchair').attr('i', org.wheelchair.includes('|') ? org.wheelchair.split('|')[1] : null);
                    $('#Org_Cafe').attr('i', org.cafe.includes('|') ? org.cafe.split('|')[1] : null);
                    $('Org_WC').attr('i', org.wc.includes('|') ? org.wc.split('|')[1] : null);
                    $('Org_Parking').attr('i', org.parking.includes('|') ? org.parking.split('|')[1] : null);
                    $('Org_Card').attr('i', org.card.includes('|') ? org.card.split('|')[1] : null);
                    $('Org_Address1').attr('i', org.address1.includes('|') ? org.address1.split('|')[1] : null);
                    $('Org_Address2').attr('i', org.address2.includes('|') ? org.address2.split('|')[1] : null);
                    $('Org_City').attr('i', org.city.includes('|') ? org.city.split('|')[1] : null);
                    $('Org_ZIP').attr('i', org.zip.includes('|') ? org.zip.split('|')[1] : null);
                    $('Org_Country').attr('i', org.country.includes('|') ? org.country.split('|')[1] : null);
                }
            } else {
                alert("ERROR: " + status);
            }
        });
    })
}

function save_user_settings() {
    o_save();
}
function save_org_settings() {
    o_save();
}

/** Requests displays of change password dialog */
function handle_change_password() {
    update_content('output', 'chunk?name=change_password', null);
}

function change_password() {
    var old_pwd =  $('#old_password').val();
    var new_pwd =  $('#new_password').val();
    var new_pwd2 =  $('#new_password_retype').val();

    if (old_pwd === "") {
        $('#message').html(format_message('Error: Old password empty'));
        return;
    }
    if (new_pwd === "") {
        $('#message').html(format_message('Error: New password empty'));
        return;
    }
    if (new_pwd !== new_pwd2) {
        $('#message').html(format_message('Error: New password doesn\'t match'));
        return;
    }
    $('#message').html('')
    update_content('message', 'umscp?p='+old_pwd+'&np='+new_pwd);
}


function handle_reset_password() {
    alert('to do');
}

function manage_organizations() {
    show_message('');
    update_content("output", "b?cn=org", null)
}

function manage_users() {
    show_message('');
    update_content("output", "b?cn=user", null)
}

function sa_list_orgs() {
    show_message('');
    update_content("output", "r?cn=org", null)
}

function sa_list_users() {
    show_message('');
    update_content("output", "r?cn=user", null)
}

function gen_pwd(len) {
    var length = (len)?(len):(10);
    var string = "abcdefghijklmnopqrstuvwxyz"; //to upper
    var numeric = '0123456789';
    var punctuation = '!@#$%^*()_+~|}{[]:;?,./-=';
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

