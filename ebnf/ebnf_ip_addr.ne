
#
# Lets describe the rules for IP address, e.g: 192.168.0.1
#

MAIN 			-> IP

IP 			-> NUMBER "." NUMBER "." NUMBER "." NUMBER

NUMBER 			-> From_0_to_255

From_0_to_255 	-> 	[0-9] 				# 0..9
			| [1-9] [0-9] 			# 10..99
			| "1" [0-9] [0-9] 		# 100..199
			| "2" [0-4] [0-9]		# 200..249
			| "2" "5" [0-5]			# 250..255
