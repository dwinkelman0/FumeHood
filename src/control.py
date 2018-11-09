###############################################################################
# TEAM FUME HOOD
# Production Control Program
#
# Daniel Winkelman <ddw30@duke.edu>
# Duke University
# EGR 101
#
# Summary:
#   This is the central program responsible for the control flow of the fume
#   hood sash closing device. It monitors a camera for motion within a defined
#   region for motion. After a period where there is no motion, it powers a
#   motor to close the sash while continuing to monitor the region for motion
#   as well as keeping track of the sash's position. It also interacts with a
#   manual override mechanism.

from camera import Camera
import threading
import time

def MonitorFrames(camera, cond_callback):
	'''Compare current frame to last frame as they are generated'''
	current_frame, last_frame = None, None
	t0 = time.time()
	n_frames = 0
	while True:
		with camera.stream.cond_newframe:
			n_frames += 1
			print(n_frames / (time.time() - t0))
			camera.stream.cond_newframe.wait()
			last_frame = current_frame
			current_frame = camera.stream.frame
		if not last_frame is None:
			# Perform sigma delta check
			pass
			"""activity = False
			if activity:
				with cond_callback:
					cond_callback.notify_all()"""

def Main():
	# Create a camera with an enclosed frame stream
	camera = Camera()

	# Start the thread for camera frame capture
	threading.Thread(target=camera.GetFrames).start()

	# Start the frames processing thread
	threading.Thread(target=MonitorFrames, args=(camera, None)).start()

if __name__ == "__main__":
	Main()
