
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
                        msg += 'Lot authenticated!';
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

function save_user_settings() {
    o_save();
}

/** Requests displays of change password dialog */
function handle_change_password() {
    update_content('output', 'chunk?name=change_password', null);
}

function change_password() {
    alert('to do');
}


function handle_reset_password() {
    alert('to do');
}

function manage_organizations() {
    update_content("output", "b?cn=org", null)
}

function manage_users() {
    update_content("output", "b?cn=user", null)
}