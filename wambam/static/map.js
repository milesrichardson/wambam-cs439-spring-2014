function setMapSize() {
    var mapHeight = $("body").outerHeight() - $("#buttonbar").outerHeight() - $("#header").outerHeight() - $("#description").outerHeight() - 25;
    $("#map-canvas").height(mapHeight);
}

$(window).on('resize', function() { setMapSize(); });

var map;
function initialize() {
    var mapOptions = {
        zoom: 15,
        center: new google.maps.LatLng(41.3111, -72.9267)
    };

    map = new google.maps.Map(document.getElementById('map-canvas'),
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
    setMapSize();
}

function setupMarkerListener() {
    var marker = null;

    google.maps.event.addListener(map, 'click', function(e) {
        if (marker == null) {
            marker = new google.maps.Marker({
		position: e.latLng,
		map: map,
		title: 'Request Location'
            });
            $("#create_task_button").show(); 
        }
        else {
            marker.setPosition(e.latLng);
        }
        $("#lat").val(e.latLng.lat());
        $("#lng").val(e.latLng.lng());
    });
}

function setupTaskMarkers() {
    console.debug("hi");


    var contentString = '<div id="info_window">'+
        '<h1> {0} ({1}) </h1>'+
        '<table> <tr>'+
        '<td id="info_label">Requester Email:</td>'+
        '<td id="info_content">{3}</td>'+
        '</tr> <tr>'+
        '<td id="info_label">Delivery Location:</td>'+
        '<td id="info_content">{4}</td>'+
        '</tr> <tr>'+
        '<td id="info_label">Expires:</td>'+
        '<td id="info_content">{2}</td>'+
        '</tr> <tr>'+
        '<td id="info_label_details"> Details:</td>'+
        '</tr><td id="info_details" colspan="2"> {5}'+
        '</td> </tr> </table>'+ 
        '<form action="/claimtask" method="POST">'+
        '<input type="submit" value="Claim" id="info_button">'+
        '<input type="hidden" name="id" value="{6}">'+
        '</form> </div>';

    infowindow = new google.maps.InfoWindow({
        content: "foo",
        maxWidth: 400
    });
    
    $.get('get_all_active_tasks', function(data) {
        var activeTasks = data["items"];
        console.debug(activeTasks.length);
        for (var i = 0; i < activeTasks.length; i++) {
            var title = activeTasks[i]["short_title"];
            var bid = activeTasks[i]["bid"];
            var expiration = activeTasks[i]["expiration_datetime"];
            var email = activeTasks[i]["requestor_email"];
            var requestor = activeTasks[i]["requestor_id"];
            var id = activeTasks[i]["id"];
            var location = activeTasks[i]["delivery_location"];
            var description = activeTasks[i]["long_title"];
            var lat = parseFloat(activeTasks[i]["latitude"]);
            var lng = parseFloat(activeTasks[i]["longitude"]);
            var myLatLng = new google.maps.LatLng(lat, lng);
            var info = contentString.format(title,bid,expiration,email, location, description, id);
            console.debug(lat + " " + lng);
            var marker = new google.maps.Marker({
                position: myLatLng,
                map: map,
                html: info
            });
            
            google.maps.event.addListener(marker, 'click', function() {
                infowindow.setContent(this.html);
                infowindow.open(map, this);
            });
        }
    });
}
