#
#	Lets define rules for seconds 0..999 and miliseconds: 0.000...0.999
#


MAIN		->	SECONDS ("." MILISECONDS):*


SECONDS		->	[0-9]					# 0..9
			|[1-9] [0-9]				# 10..99
			|[1-9] [0-9] [0-9]		 	# 100..999


MILISECONDS	->	[0-9]					# 0..9
			|[0-9] [0-9]				# 00..99
			|[0-9] [0-9] [0-9]			# 000..999
