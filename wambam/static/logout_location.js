function setLogoutPos() {
    var topPos = $("#header").height() / 2;
    console.debug(topPos);
    $("#logoutbutton").css({
        "top": topPos + "px",
    });
}

if (screen.width >= 700) {
    $(window).on('load', function() { setLogoutPos(); });
}
