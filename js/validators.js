function is_valid_year(year)
{
    var pattern = new RegExp("[1-3][0-9][0-9][0-9]");
    return pattern.test(year) && year >= 1900 && year <= 3000;
}

function is_valid_user_name(username)
{
    var pattern = new RegExp("^[_@\.a-zA-Z0-9]+$");
    return pattern.test(username);    
}

function is_valid_email(email) {
  var pattern = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return pattern.test(email);
}