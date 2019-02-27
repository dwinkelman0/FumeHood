class Thing:
	
	def a(self):
		return 5

	STATIC_VAR = a

x = Thing
print(x.STATIC_VAR)
