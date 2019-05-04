function urlencodeFormData(fd){
    var s = '';
    function encode(s){ return encodeURIComponent(s).replace(/%20/g,'+'); }
    for(var pair of fd.entries()){
        if(typeof pair[1]=='string'){
            s += (s?'&':'') + encode(pair[0])+'='+encode(pair[1]);
        }
    }
    return s;
}

function login() {
    var form = new FormData();
    form.append("username", "c2@gmail.com");
    form.append("password", "321ołsah");
    
    var settings = {
        "async": true,
        "url": document.location.origin + "/api/login",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
            "Postman-Token": "c78300f2-0ba2-4132-ae5c-b01e78a32826"
        },
        "processData": false,
        "contentType": false,        
        "data": urlencodeFormData(form)
    }
    
    $.ajax(settings)
    .done(function (response) {
        console.log(response);
    })
    .fail(function (response) {
        console.log(response);
    });
}

function logout() {    
    var settings = {
        "async": true,
        "url": document.location.origin + "/api/logout",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
            "Postman-Token": "c78300f2-0ba2-4132-ae5c-b01e78a32826"
        },
        "processData": false,
        "contentType": false,        
    }
    
    $.ajax(settings)
    .done(function (response) {
        console.log(response);
    })
    .fail(function (response) {
        console.log(response);
    });
}

function add_run() {    
    var form = new FormData();
    form.append("distance", 10);
    form.append("date", "2018-06-21");
    form.append("time", "12:12");
    form.append("privacy", "all");
    form.append("runners", 10);
    
    var settings = {
        "async": true,
        "url": document.location.origin + "/api/runs/create",
        "method": "POST",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cache-Control": "no-cache",
            "Postman-Token": "c78300f2-0ba2-4132-ae5c-b01e78a32826"
        },
        "processData": false,
        "contentType": false,        
        "data": urlencodeFormData(form)
    }
    
    $.ajax(settings)
    .done(function (response) {
        console.log(response);
    })
    .fail(function (response) {
        console.log(response);
    });
}