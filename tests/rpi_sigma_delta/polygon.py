# Resources:
# https://www.geeksforgeeks.org/how-to-check-if-a-given-point-lies-inside-a-polygon

import numpy as np

class Point(object):
	def __init__(self, x, y):
		self.x, self.y = float(x), float(y)

	def __repr__(self):
		return "(%.3f, %.3f)" % (self.x, self.y)

class Equation(object):
	def __init__(self, p1, p2):
		# ax + by = c
		# Transform point-slope form into standard form (for use in matrices)
		# y - y0 = (dy/dx)(x - x0) ---> (dx)y - (dy)x = (dx)y0 - (dy)x0
		dx, dy = p2.x - p1.x, p2.y - p1.y
		self.A, self.B, self.C = -dy, dx, dx * p1.y - dy * p1.x
		self.xmin, self.xmax = min(p1.x, p2.x), max(p1.x, p2.x)
		self.ymin, self.ymax = min(p1.y, p2.y), max(p1.y, p2.y)

	def __repr__(self):
		return "%.3fx + %.3fy = %.3fc" % (self.A, self.B, self.C)

	@staticmethod
	def Intersection(eq1, eq2):
		# Solve [A] * [X] = [C] for [X]
		A = np.array([[eq1.A, eq1.B], [eq2.A, eq2.B]])
		B = np.array([[eq1.C], [eq2.C]])
		solution = np.linalg.inv(A).dot(B)
		x, y = solution[0][0], solution[1][0]
		if all([
			eq1.xmin <= x, x <= eq1.xmax, eq2.xmin <= x, x <= eq2.xmax,
			eq1.ymin <= y, y <= eq1.ymax, eq2.ymin <= y, y <= eq2.ymax]):
			return Point(x, y)
		else:
			return None

class Polygon(object):
	def __init__(self, points_str):
		#points_list = eval(points_str)
		points_list = points_str
		# Add 0.5 to each point to center it in the box of the pixel
		# Switch x and y to match 90 degree rotation in configuration web page
		self.points = [Point(i.x + 0.5, i.y + 0.5) for i in points_list]

	def Contains(self, point):
		# The point is inside the polygon
		None

	def GenerateMask(self, width, height):
		# Make the data type 8 bit unsigned integer to match the output of the camera stream
		mask = np.zeros((height, width), dtype="uint8")

		# Encode the points into linear equations
		equations = [Equation(p1, p2)
			for p1, p2 in zip(self.points, self.points[1:] + self.points[:1])]

		# For each row (y), find the (x) values where there is an intersection with a polygon line
		#     (this also means checking the domain of the polygon line)
		# For each interval, determine if inside or outside, and fill mask accordingly
		for y in range(height):
			# Define the equation for the horizontal line
			intersections = []
			hor_eq = Equation(Point(0, y), Point(width, y))
			for eq in equations:
				intersection = Equation.Intersection(hor_eq, eq)
				if intersection is not None:
					intersections.append(intersection)
			intersections = sorted(intersections, key=lambda intersection: intersection.x)

			print intersections

			fill = 0
			index = 0
			for intersection in [round(i.x) for i in intersections] + [width]:
				while index < intersection:
					mask[y, index] = fill
					index += 1
				fill = int(not fill)
		print mask
		

pts = [Point(1, 1), Point(6, 7), Point(1, 18)]
polygon = Polygon(pts)
polygon.GenerateMask(10, 20)
