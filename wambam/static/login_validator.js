String.prototype.endsWith = function(suffix) {
    return this.indexOf(suffix, this.length - suffix.length) !== -1;
};

jQuery.validator.addMethod("passwordmatch",
			   function(value) {
			       return value === $("#password").val();
			   }, "Passwords don't match."
			  );

jQuery.validator.addMethod("yaleemail",
			   function(value) {
			       return value.endsWith("@yale.edu")
			   }, "Must register with Yale email address."
			  );

jQuery.validator.addMethod("emailused",
			   function(value) {
			       var email_used = false;
			       var post_data = {};
			       post_data['email'] = value
			       $.ajax({
				   url: 'check_email',
				   type: 'POST',
				   contentType: 'application/json',
				   data: JSON.stringify(post_data),
				   async: false,
				   success: function(data) {
				       email_used = (data["used"] === 'True');
				   }});
			       return !email_used;
			   }, "Email address is already registered."
			  );
jQuery.validator.addMethod("phoneused",
			   function(value) {
			       var phone_used = false;
			       var post_data = {};
			       post_data['phone'] = value
			       $.ajax({
				   url: 'check_phone',
				   type: 'POST',
				   contentType: 'application/json',
				   data: JSON.stringify(post_data),
				   async: false,
				   success: function(data) {
				       phone_used = (data["used"] === 'True');
				   }});
			       return !phone_used;
			   }, "Phone number is already registered."
			  );

$("#registerform").validate({
    rules: {
        firstname: {
            required: true,
            lettersonly: true
        },
        lastname: {
            required: true,
            lettersonly: false
        },
        phone: {
            required: true,
            phoneUS: true,
            phoneused: true
        },
        email: {
            required: true,
            email: true,
            emailused: true,
            yaleemail: true
        },
        password: {

            required: true
        },
        passwordconfirm: {
            required: true,
            passwordmatch: true
        },
    }, 
    errorPlacement: function(error, element) {
        if (element.attr("name") == "firstname" )
            error.appendTo("#firstnameerror");
        else if (element.attr("name") == "lastname" )
            error.appendTo("#lastnameerror");
        else if (element.attr("name") == "phone" )
            error.appendTo("#phoneerror");
        else if  (element.attr("name") == "email" )
            error.appendTo("#emailerror");
        else if  (element.attr("name") == "password" )
            error.appendTo("#passworderror");
        else if  (element.attr("name") == "password" )
            error.appendTo("#passworderror");
        else if  (element.attr("name") == "passwordconfirm" )
            error.appendTo("#passwordconfirmerror");
    }
});

$.validator.messages.required = 'WamBam! needs this information!';
$.validator.messages.phoneUS = 'Please specify a valid phone number';
$.validator.messages.email = 'Please specify a valid Yale email address';
