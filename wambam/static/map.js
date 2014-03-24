function setMapSize() {
    var mapHeight = $("body").outerHeight() - $("#buttonbar").outerHeight() - $("#header").outerHeight() - $("#description").outerHeight();
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
        setMapSize();
    });
    setMapSize();
}

google.maps.event.addDomListener(window, 'load', initialize);
