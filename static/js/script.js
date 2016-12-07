/*eslint-env jquery */
/*globals currentState */
$(function() {	
	//Locating the DIV on middle-centre
	$(".block").height($(window).height());
	$(window).bind("resize", function() {
		$(".block").height($(window).height());
	});
	
	//Disabling and Enabling buttons
	function disableBtns(){
		$(".statusBtn.btn-group a, .dataActivity.btn-group a").attr("disabled","disabled");	
		$(".statusBtn.btn-group a, .dataActivity.btn-group a").css("pointer-events", "none");	
	}
	
	function enableStartBtn(){
		$(".statusBtn.btn-group a, .dataActivity.btn-group a#startbutton").removeAttr("disabled");	
		$(".statusBtn.btn-group a, .dataActivity.btn-group a#startbutton").css("pointer-events", "auto");			
	}	
	
	function enableStopBtn(){
		$("#stopbutton").removeAttr("disabled");	
		$("#stopbutton").css("pointer-events", "auto");		
	}
	
	function disableStartBtn(){
		$("#startbutton").attr("disabled","disabled");	
		$("#startbutton").css("pointer-events", "none");	
	}
	
	function disableStopBtn(){
		$("#stopbutton").attr("disabled","disabled");	
		$("#stopbutton").css("pointer-events", "none");			
	}
	
	function disableStatusBtn(){
		$(".statusBtn.btn-group a").attr("disabled","disabled");	
		$(".statusBtn.btn-group a").css("pointer-events", "none");
	}
	function enableStatusBtn(){
		$(".statusBtn.btn-group a").removeAttr("disabled");	
		$(".statusBtn.btn-group a").css("pointer-events", "auto");
	}	
	disableBtns();
	
	//Hiding all the notification messages
	$(".started").hide();
	$(".stopped").hide();
	$(".dataError").hide();
	$(".selectedServiceErrorMsg").hide();
	$("#loadingDiv").hide();
	$("#dataStatusLoader").hide();
	$("#tickMark").hide();
	
	//Showing Button's active and Inactive status by UI
	var currentStat = $("#current-state").text();	
	console.log("currentStat: ", currentStat);
	$(".statusBtn a[href=" + currentStat + "]").addClass("active");
	$(".statusBtn.btn-group a").on("click", function(){
		$(".statusBtn .a.active").removeClass("active");
		$(this).addClass("active");
	});
	
	//Disabling Data Model Perameter on when data activity is started
	function checkDataModelingPerameter(){
		if(dataActivityState===1){
			disableStartBtn();
			enableStopBtn();
			$("#ioTServices").attr("disabled","disabled");
	        $("#submit").attr("disabled","disabled");
		}		
	}	
	checkDataModelingPerameter();
	 
	//Validation for "Select IoT Service" drop down
	$("#selectServiceForm").validate({
		rules: {
			agree: "required",
            'selectplat': {
                required: true
             }
		},        
		messages: {
            selectplat: "Please select a service"
		}
	});
	
	//Loader icon 
	/*var $loading = $("#loadingDiv").hide();
	$(document)
	  .ajaxStart(function () {
	    $loading.show();
	  })
	  .ajaxStop(function () {
	    $loading.hide();
	});*/
	
	//Setting connected service in dropdown as selected value
	function setIoTServiceSelected(){
		if(platformChoice>=1){
			if(dataActivityState!==1){
				enableStartBtn();
			}
			$("#ioTServices").val(platformChoice);
		}
	}
	setIoTServiceSelected();
	
	//Loader Icon on click of Connection button
	$("#submit").click(function(e){
		var selectedValue = $("#ioTServices").val();
		if(selectedValue>=1){
			$("#loadingDiv").show();
		}
	})	

	//Taking action on change of IoT Service from dropdown 
	$("#ioTServices").on("change", function(){
		var selectedValue = $("#ioTServices").val();
		var platformChoiceInString = platformChoice.toString();

		if(selectedValue !== platformChoiceInString){
			disableBtns();
		}else if(selectedValue === platformChoiceInString){
			enableStartBtn();
		}
	});	
	
	//Connecting data based on selected IoTF service
	var startButton = $("#startbutton");
	var url1 = startButton.attr("connect");
	startButton.on("click", function (e) {
		disableStartBtn();
		$("#dataStatusLoader").show();
			
		$.ajax({
			url: url1,
			success: function (response, data) {
				//console.log(response, data);
				if (response) {

					enableStopBtn();
					disableStatusBtn();
					$("#ioTServices").attr("disabled","disabled");
					$("#submit").attr("disabled","disabled");
					$(".started").show();
					$(".stopped").hide();
					$(".dataError").hide(500);
					$("#dataStatusLoader").hide();
					$("#tickMark").show();
					$("#tickMark").delay(3000).hide(500);	
					$(".started").delay(3000).hide(500);		
				} else {
					$(".dataError").hide();
				}
			},
			statusCode: {
				500: function() {
					$("#dataStatusLoader").hide();
					$("#tickMark").hide();
					$(".dataError").show();
					$(".dataError").delay(3000).hide(500);	
					enableStartBtn();
				}
			}
		});	
	});
	
	var stopButton = $("#stopbutton");
	var url = stopButton.attr("connect");
	
	stopButton.on("click", function (e) {
		enableStartBtn();
		disableStopBtn();
		
		$.ajax({
			url: url,
			success: function (response, data) {
				console.log(response, data,0000);
				if (response) {
					$("#ioTServices").removeAttr("disabled");
					$("#submit").removeAttr("disabled");					
					$(".started").hide();
					$(".stopped").show();
					$(".dataError").hide();
					$("#tickMark").hide();
					$(".stopped").delay(2000).hide(500);	
				} else {

				}
			}
		});			
    });
});	