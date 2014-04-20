jQuery.validator.addMethod("dollars", function(value) {
    return /^\$?([0-9]{0,9})((\.([0-9]{2}))?)$/.test(value);
}, "Please specify a valid dollar amount"
                          );

$( "#addtaskform" ).validate(
    {
        
        rules: {
            title: {
                required: true,
            },
            location: {
                required: true,
            },
            bid: {
                required: true,
                dollars: true
            }
        }, 
        errorPlacement: function(error, element) {
            if (element.attr("name") == "title" )
                error.appendTo("#titleerror");
            else if  (element.attr("name") == "location" )
                error.appendTo("#locationerror");
            else if  (element.attr("name") == "bid" )
                error.appendTo("#biderror");
        }
    });

$.validator.messages.required = "WamBam! needs this information!";
