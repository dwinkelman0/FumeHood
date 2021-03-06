// References:
// https://stackoverflow.com/questions/6396101

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

		// Draw circles for each point
		for (var i = 0; i < points.length; i++) {
			ctx.strokeStyle = "#f00";
			ctx.globalAlpha = "1.0";
			ctx.beginPath();
			ctx.arc(points[i].x, points[i].y, 10, 0, 2 * Math.PI);
			ctx.stroke();
		}
	};

	function ClearPolygon() {
		// Completely reset the local data
		points = [];
		closed = false;
	}

	function LoadPolygon() {
		// Send a GET to the server...
		var xhr = new XMLHttpRequest();
		xhr.onreadystatechange = function() {
			if (this.readyState != 4) return;
			if (this.status == 200) {
				var polygon = JSON.parse(this.responseText);
				points = polygon;
				if (points.length >= 3) closed = true;
				else closed = false;
				DrawPolygon();
			}
		}
		xhr.open("GET", "polygon.json", true);
		xhr.send();
	}

	function SavePolygon() {
		// Check that there is a valid polygon (i.e. that it is closed)
		if (!closed) {
			alert("The polygon must be closed");
			return;
		}
		
		// Send a POST to the server...
		var xhr = new XMLHttpRequest();
		xhr.open("POST", "save-polygon", true);
		xhr.setRequestHeader("Content-Type", "text/json");
		xhr.send(JSON.stringify(points));
	}

	// Get buttons and set event handlers
	var button_clear = document.getElementById("button-clear");
	button_clear.onclick = function() {
		ClearPolygon();
		DrawPolygon();
	}
	
	var button_save = document.getElementById("button-save");
	button_save.onclick = function() {
		SavePolygon();
	};

	var button_reload = document.getElementById("button-reload");
	button_reload.onclick = function() {
		ClearPolygon();
		LoadPolygon();
	};

	// Event handlers for the canvas
	canvas.addEventListener("click", function(event) {

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
			if (Math.sqrt((x - start.x) * (x - start.x) + (y - start.y) * (y - start.y)) < 10) {
				closed = true;
			}
			else {
				points.push({"x": x, "y": y});
			}
		}

		// Redraw the points
		DrawPolygon();

	}, false);

	// Initialization on page load
	LoadPolygon();
	DrawPolygon();
};
