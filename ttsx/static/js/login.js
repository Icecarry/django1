/**
 * Created by python on 18-4-20.
 */
$(function () {
    var user_error = false;
    var pwd_error = false;
    var check_error = false;

    // $('.name_input').blur(function() {
	// 	check_name_pwd();
	// });
    //
	// $('.pass_input').blur(function() {
	// 	check_pwd();
	// });

    $('.input_submit').click(function () {
       check_name_pwd();
    });

    function check_name_pwd() {
        var len = $('.name_input').val().length;
		if(len<5||len>20)
		{
			check_error = true;
		}
		else
		{
			//验证用户名是否存在
			$.get('/user/user_name', {'uname': $('.name_input').val()}, function (data) {
				if (data.result == 1) {
					check_error = false;
				} else {
					$('.name_input').next().hide();
					check_error = true;
				}
            })
		}
    }

});
