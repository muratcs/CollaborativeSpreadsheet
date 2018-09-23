

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


function setName() {
    var url = '/controlJSON/setName/';
	var data = $("#form01").serialize() ;
	$.post(url, data , function (data) {
	    $("#sheetname").text(data.sname);
	    $("#response").text(data.response);
		});

}

function setCellValue() {
    var url = '/controlJSON/setCellValue/';
    var data = $("#form02").serialize();
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
        for (var i in  data.rows){
	        $("tr[id='"+data.rows[i]+"'] td[id='"+data.cols[i]+"']").text(data.contents[i]);
        }
        // var row = data.row;
        // var col = data.col;
        // var content = data.content;
        // $("tr[id='"+row+"'] td[id='"+col+"']").text(data.content)
		});
}

function getCell() {
    var url = '/controlJSON/getCell/';
	var data = $("#form03").serialize() ;
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
		});
}

function getCells() {
    var url = '/controlJSON/getCells/';
    var data = $("#form04").serialize() ;
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
		});
}

function evaluate() {
    var url = '/controlJSON/evaluate/';
    var data = $("#form05").serialize() ;
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
	    for (var i in  data.rows){
	        $("tr[id='"+data.rows[i]+"'] td[id='"+data.cols[i]+"']").text(data.contents[i]);
        }
		});
}


function cutRange() {
    var url = '/controlJSON/cutRange/';
    var data = $("#form11").serialize() ;
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
	    for (var i in  data.rows){
	        $("tr[id='"+data.rows[i]+"'] td[id='"+data.cols[i]+"']").text(data.contents[i]);
        }
		});
}

function copyRange() {
    var url = '/controlJSON/copyRange/';
    var data = $("#form12").serialize() ;
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
		});
}

function pasteRange() {
    var url = '/controlJSON/pasteRange/';
    var data = $("#form13").serialize() ;
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
	    for (var i in  data.rows){
	        $("tr[id='"+data.rows[i]+"'] td[id='"+data.cols[i]+"']").text(data.contents[i]);
        }
		});
}

function updatecells(cells, cellcolls) {

    var body = $('#cellsbody');
    // $('tr').remove();
    body.html('');
    body.append('<tr id="headrow" class="header">');
    var row = body.find("tr:last");
    row.append('<td id="headrowcols" class="header"> # </td>');

    for (var i in cellcolls){
        row.append('<td id="headrowcols" class="header"> (' + cellcolls[i] + ') </td>');
    }

    for (i in cells){
        body.append('<tr id="'+i+'" >');
        row = body.find("tr:last");
        row.append('<td id="headcol" class="header"> ('+(+i+1)+') </td>');
        for (var j in cells[0]){
            row.append('<td id="'+j+'"  onclick="cellclickfunc(this)"' +
                ' onmousedown="cellclickfunc2(this)" onmouseup="cellclickfunc3(this)"  > '+ cells[i][j] +' </td>');
        }
    }
}

function cellclickfunc(x) {
    var i = x.parentNode.id;
    var j = x.id;
    var url = '/encodeJSON/'+ +i +'/'+ +j  +'/';
    $.get(url, function (response) {
        var addr = response.encoded;
        $('[placeholder = "CellAddr"]').attr('value', addr);
        // $('[placeholder = "CellRange"]').attr('value', addr + ':');

    })
}

function cellclickfunc2(x) {
    var i = x.parentNode.id;
    var j = x.id;
    var url = '/encodeJSON/'+ +i +'/'+ +j  +'/';
    $.get(url, function (response) {
        addr = response.encoded;
    })
}

function cellclickfunc3(x) {
    var i = x.parentNode.id;
    var j = x.id;
    var url = '/encodeJSON/'+ +i +'/'+ +j  +'/';
    $.get(url, function (response) {
        var addr2 = response.encoded;
        $('[placeholder = "CellRange"]').attr('value', addr + ':' + addr2);

    })
}




function upload() {

    $.ajax({
        url : '/uploadJSON/',
        type: 'POST',

        data: new FormData($('#form14')[0]),

        cache: false,
        contentType: false,
        processData: false,

        xhr: function() {
            var myXhr = $.ajaxSettings.xhr();
            if (myXhr.upload) {
                myXhr.upload.addEventListener('progress', function(e) {
                    if (e.lengthComputable) {
                        $('progress').attr({
                            value: e.loaded,
                            max: e.total
                        });
                    }
                } , false);
            }
            return myXhr;
        },

        success: function (response) {
            $('#sheetid').text(response.sid);
            $('#sheetname').text(response.sname);
            $('#response').text("Upload method called.");
            // $('#notf').clear();

            updatecells(response.cells, response.cellcolls)

        }

    });
}

function list() {
    var url = '/controlJSON/list/';
    var data = $("#form21").serialize() ;
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
		});
}

function listmem() {
    var url = '/controlJSON/listmem/';
    var data = $("#form22").serialize() ;
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
		});
}

function save() {
    var url = '/controlJSON/save/';
    var data = $("#form23").serialize() ;
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
		});
}

function load() {
    var url = '/controlJSON/load/';
    var data = $("#form24").serialize() ;
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
	    for (var i in  data.rows){
	        $("tr[id='"+data.rows[i]+"'] td[id='"+data.cols[i]+"']").text(data.contents[i]);
        }
		});
}

function delete1() {
    var url = '/controlJSON/delete/';
    var data = $("#form25").serialize() ;
	$.post(url, data , function (data) {
	    $("#response").text(data.response);
	    if (data.issame){
	        $('#controlpanel').fadeOut();
        }
		});
}

function refresh() {
    var url = '/updatesJSON/';
    $.get(url, function (data) {
        if (data.result === "Success"){
            // $("#test").fadeIn();

            for (var i in  data.rows){
                $("tr[id='"+data.rows[i]+"'] td[id='"+data.cols[i]+"']")
                    .fadeOut(500).fadeIn(1000).text(data.contents[i]);
                // $("tr[id='"+data.rows[i]+"'] td[id='"+data.cols[i]+"']")
                //     .fadeOut(500, 'swing', function () {
                //         $(this).fadeIn(1000).text(data.contents[i])
                //     });


            }
            $("#sheetname").text(data.sname);

            for (var i in data.updates){
                $.notify(data.updates[i], "info");
            }

        }
        // else{
        //     $("#test").fadeOut();
        // }
    });
}


function create() {
    var url = '/createJSON/create/';
    var data = $("#form1").serialize() ;
	$.post(url, data , function (response) {
	    $("#response").text(response.response);
	    if (response.result === 'Success'){
	        $("#controlpanel").fadeIn();
	        $('#sheetid').text(response.sid);
            $('#sheetname').text(response.sname);
            $('[id=phfields]').attr('placeholder', "ID = " + response.sid);

            updatecells(response.cells, response.cellcolls)

        }
		});
}

function attach() {
    var url = '/createJSON/attach/';
    var data = $("#form2").serialize() ;
	$.post(url, data , function (response) {
	    $("#response").text(response.response);
	    if (response.result === 'Success'){
	        $("#controlpanel").fadeIn();
	        $('#sheetid').text(response.sid);
            $('#sheetname').text(response.sname);
            $('[id=phfields]').attr('placeholder', "ID = " + response.sid);

            updatecells(response.cells, response.cellcolls)

        }
		});
}



$(document).ready(function(){

    $.ajaxSetup({beforeSend: function(xhr, settings) {
			xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
			}});


    $("#setName").click(function() {
        setName();
        return false;
    });

    $("#setCellValue").click(function() {
        setCellValue();
        return false;
    });

    $("#getCell").click(function() {
        getCell();
        return false;
    });

    $("#getCells").click(function() {
        getCells();
        return false;
    });

    $("#evaluate").click(function() {
        evaluate();
        return false;
    });

    $("#cutRange").click(function() {
        cutRange();
        return false;
    });

    $("#copyRange").click(function() {
        copyRange();
        return false;
    });

    $("#pasteRange").click(function() {
        pasteRange();
        return false;
    });

    $("#upload").click(function() {
        upload();
        return false;
    });

    $("#list").click(function() {
        list();
        return false;
    });

    $("#listmem").click(function() {
        listmem();
        return false;
    });

    $("#save").click(function() {
        save();
        return false;
    });

    $("#load").click(function() {
        load();
        return false;
    });

    $("#delete").click(function() {
        delete1();
        return false;
    });

    $("#oldbuttons").click(function () {
        $("#container2").fadeToggle();
        return false;
    });

    $("#create").click(function () {
        create();
        return false;
    });

    $("#attach").click(function () {
        attach();
        return false;
    });




    // update();
    setInterval(refresh, 5000);



});