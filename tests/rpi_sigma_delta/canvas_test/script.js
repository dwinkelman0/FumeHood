window.onload = function() {	
	// Get the canvas and make a context
	var canvas = document.getElementById("drawable");
	var ctx = canvas.getContext("2d");

	// Set canvas properties
	canvas.width = 480;
	canvas.height = 640;

	// Draw some sample stuff
	ctx.fillStyle = "red";
	ctx.fillRect(160, 240, 40, 40);
	ctx.fillText("Region of motion detection", 30, 30);
}
