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

import camera


