var lats = [];
var lons = [];
var ids = [];
var maps = [];
var locs =[]

function addStuff(lat, lon, id) {
    lats.push(lat)
    lons.push(lon)
    ids.push(id)
}

$(document).ready(function(){
    $("#accordion").accordion({
        activate: function (event, ui) {
            var active = $("#accordion").accordion( "option", "active" );
            console.debug(active);
            google.maps.event.trigger(maps[active], "resize");
            maps[active].setCenter(locs[active]);
        }
    });
});

function initialize() {
    for (var i = 0; i < lats.length; i++) {
        var map;
        var mapOptions = {
            zoom: 15,
            center: new google.maps.LatLng(lats[i], lons[i])
        };

        map = new google.maps.Map(document.getElementById(ids[i]),
                                  mapOptions);

        map.setOptions({styles: [
            {
                featureType: "poi",
                elementType: "labels",
                stylers: [
                    { visibility: "off" }
                ]
            }
        ]});
        var myLatLng = new google.maps.LatLng(lats[i], lons[i]);
        var marker = new google.maps.Marker({
            position: myLatLng,
            map: map,
        });
        maps.push(map);
        locs.push(myLatLng);
    }

    for (var i = 0; i < ids.length; i++) {

    }  
}

google.maps.event.addDomListener(window, 'load', initialize);


var div_id = "";
var task_id = "";

$(function() {
    $( "#accordion" ).accordion();
    $( "#accordion input[type=image]" ).click(
        function(event) {
            var form = $(this).parents('form:first');
            var input_id = $(this).attr("id");
            task_id = input_id.substring(2)
            div_id = "#d" + task_id;
            console.debug(div_id);
            if (form.attr("id") == "thumbs_up_form") {
                console.debug("thumbs up");
                $.ajax({
                    url: "add_feedback/" + task_id + "/positive",
                    type: 'POST',
                    async: false,
                    success: function(data) {
                        var map = $("#map-canvas" + task_id)

                        $(data).insertAfter(div_id)
                        var new_head = $(div_id).next("h3")
                        var new_div = new_head.next("div")

                        var div = $(div_id)
                        var head = div.prev("h3")
                        div.remove();
                        head.remove();
                        $("#map-canvas" + task_id).replaceWith(map);
                        $("#accordion").accordion("destroy").accordion({
                            activate: function (event, ui) {
                                var active = $("#accordion").accordion( "option", "active" );
                                console.debug(active);
                                google.maps.event.trigger(maps[active], "resize");
                                maps[active].setCenter(locs[active]);
                            }
                        });
                    }
                })
            }
            if (form.attr("id") == "thumbs_down_form") {
                $.ajax({
                    url: "add_feedback/" + task_id + "/negative",
                    type: 'POST',
                    async: false,
                    success: function(data) {
                        var map = $("#map-canvas" + task_id)

                        $(data).insertAfter(div_id)
                        var new_head = $(div_id).next("h3")
                        var new_div = new_head.next("div")

                        var div = $(div_id)
                        var head = div.prev("h3")
                        div.remove();
                        head.remove();
                        $("#map-canvas" + task_id).replaceWith(map);
                        $("#accordion").accordion("destroy").accordion({
                            activate: function (event, ui) {
                                var active = $("#accordion").accordion( "option", "active" );
                                console.debug(active);
                                google.maps.event.trigger(maps[active], "resize");
                                maps[active].setCenter(locs[active]);
                            }
                        });
                    }
                })
            }
            else {                
                form.submit();
            }
        })
    $( "#accordion input[type=submit]" ).click(
        function(event) {
            var form = $(this).parents('form:first');
            var input_id = $(this).attr("id");
            task_id = input_id.substring(1)
            div_id = "#d" + task_id;
            console.debug(div_id);
            if (form.attr("id") == "cancel_form") {
                console.debug("Cancel request");
                $.ajax({
                    url: "cancel_task/" + task_id,
                    type: 'POST',
                    async: false,
                    success: function(data) {
                        var map = $("#map-canvas" + task_id)

                        $(data).insertAfter(div_id)
                        var new_head = $(div_id).next("h3")
                        var new_div = new_head.next("div")

                        var div = $(div_id)
                        var head = div.prev("h3")
                        div.remove();
                        head.remove();
                        $("#map-canvas" + task_id).replaceWith(map);
                        $("#accordion").accordion("destroy").accordion({
                            activate: function (event, ui) {
                                var active = $("#accordion").accordion( "option", "active" );
                                console.debug(active);
                                google.maps.event.trigger(maps[active], "resize");
                                maps[active].setCenter(locs[active]);
                            }
                        });
                    }
                })
            }
            else {                
                form.submit();
            }
        })
});
