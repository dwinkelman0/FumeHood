from interrupts import Interrupt
import polygon
import server

import numpy as np

def MonitorFrames(camera, interrupt):
	'''Compare current frame to last frame as they are generated'''

	# Storage for frames to compare
	current_frame, last_frame = None, None
	width, height = camera.camera.resolution

	# Generate mask for desired camera range
	mask = None
	try:
		# Try to read polygon from file and build a mask array
		with open("camserver/points.json") as polygon_file:
			print("Starting to create mask...")
			pts_str = polygon_file.read()
			pts = [polygon.Point(i["x"], i["y"]) for i in eval(pts_str)]
			shape = polygon.Polygon(pts)
			mask = shape.GenerateMask(width, height)

			# Slice only the part of the mask/frame that is relevant
			# Huge performance boost for processing
			x_coords, y_coords = [int(i.x) for i in pts], [int(i.y) for i in pts]
			mask_xmin, mask_xmax = min(x_coords), max(x_coords)
			mask_ymin, mask_ymax = min(y_coords), max(y_coords)
			# Ensure the slices are within domain
			mask_xmin, mask_xmax = max(mask_xmin, 0), min(mask_xmax, width - 1)
			mask_ymin, mask_ymax = max(mask_ymin, 0), min(mask_ymax, height - 1)
			mask = mask[mask_ymin:mask_ymax, mask_xmin:mask_xmax]

			mask_weight = np.sum(np.sum(np.sum(mask)))
			print("Created mask")
	except:
		print("Error with creating polygon mask")
		mask_weight = width * height * 3

	while True:
		with camera.stream.cond_newframe:
			# Wait for a new frame
			camera.stream.cond_newframe.wait()
			last_frame = current_frame
			# Cast frame into a numpy array
			current_frame = np.frombuffer(camera.stream.frame, dtype="uint8")

		# Make sure there was data in the buffer
		if current_frame.size != 0:
			current_frame.shape = (height, width, 3)
		else:
			continue

		# Perform sigma delta check
		if mask is not None:
			# Slice only the part of the mask/frame that is relevant
			# Huge performance boost for processing
			current_frame = current_frame[mask_ymin:mask_ymax, mask_xmin:mask_xmax]
			current_frame = np.multiply(current_frame, mask)
		current_frame = current_frame.astype("int32")
		if last_frame is not None and last_frame.size != 0:
			difference = np.square(current_frame - last_frame) # Non-linearity helps bring out meaningful changes
			subtotal = np.sum(np.sum(difference)).astype("int64")
			total = np.sum(subtotal) / mask_weight # Average change per pixel
			activity = total > 15 # Completely arbitrary
			# 15 (with the sqrare function) seems to avoid noise like ambiance/shadows,
			# but still plenty to detect even far-away motion
		else:
			activity = False

		if activity:
			# Send a signal to the state machine
			interrupt.Send(Interrupt.EVENT_ACTIVITY)
