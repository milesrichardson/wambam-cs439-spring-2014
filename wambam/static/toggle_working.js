function setToggleWork(value, send) {
    $('#toggle_work').data("online", value);
    $('#toggle_work').text(value ? "Turn OFF sms alerts for new tasks" : "Turn ON sms alerts for new tasks");
    if (send) {
        if (value) {
            $.ajax({
                type: 'POST',
                url: 'set_online',
                async: true
            });
        }
        else {
            $.ajax({
                type: 'POST',
                url: 'set_offline',
                async: true
            });
        }
    }
}

$.ajax({
    url: 'get_online',
    type: 'GET',
    contentType: 'application/json',
    async: false,
    success: function(data) {
        setToggleWork(data["online"], false);
    }
});


$('#toggle_work').click(function() {setToggleWork(! $('#toggle_work').data("online"), true)});
