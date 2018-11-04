window.onload = function() {

	// Define array of polygon points
	var points = [];
	var closed = false;

	// Get the canvas, make a context, set some properties
	var canvas = document.getElementById("drawable");
	var ctx = canvas.getContext("2d");
	canvas.width = 480;
	canvas.height = 640;

	// Function to draw the polygon
	var DrawPolygon = function() {
		console.log(points);
		console.log(closed);

		var ctx = canvas.getContext("2d");

		// Clear the canvas
		ctx.clearRect(0, 0, canvas.width, canvas.height);

		// Draw filling
		if (closed && points.length >= 3) {
			ctx.fillStyle = "#f00";
			ctx.globalAlpha = "0.1";
			ctx.beginPath();
			ctx.moveTo(points[0].x, points[0].y);
			for (var i = 1; i < points.length; i++) {
				ctx.lineTo(points[i].x, points[i].y);
			}
			ctx.closePath();
			ctx.fill();
		}

		// Draw outline
		if (points.length >= 2) {
			ctx.strokeStyle = "#f00";
			ctx.globalAlpha = "1.0";
			ctx.beginPath();
			ctx.moveTo(points[0].x, points[0].y);
			for (var i = 1; i < points.length; i++) {
				ctx.lineTo(points[i].x, points[i].y);
			}
			if (closed) {
				ctx.lineTo(points[0].x, points[0].y);
			}
			ctx.stroke();
		}
	};

	// Get buttons and set event handlers
	var button_clear = document.getElementById("button-clear");
	button_clear.onclick = function() {
		// Completely reset the local data
		points = [];
		closed = false;
		DrawPolygon();
	};
	
	var button_save = document.getElementById("button-save");
	button_save.onclick = function() {
		// Check that there is a valid polygon (i.e. that it is closed)
		if (!closed) {
			alert("The polygon must be closed");
			return;
		}
		
		// Send a POST to the server...
	};

	var button_reload = document.getElementById("button-reload");
	button_reload.onclick = function() {
		// Send a GET to the server...
	};

	// Event handlers for the canvas
	canvas.addEventListener('click', function(event) {

		// If the polygon is already closed, don't do anything
		if (closed) return;

		// Get the coordinates of the click
		var x = event.offsetX;
		var y = event.offsetY;

		// If this is the first or second point, just add
		if (points.length < 3) {
			points.push({"x": x, "y": y});
		}

		// If the click was near the starting point, close the loop
		else {
			var start = points[0];
			if (Math.sqrt((x - start.x) * (x - start.x) + (y - start.y) * (y - start.y)) < 5) {
				closed = true;
			}
			else {
				points.push({"x": x, "y": y});
			}
		}

		// Redraw the points
		DrawPolygon();

	}, false);
};
