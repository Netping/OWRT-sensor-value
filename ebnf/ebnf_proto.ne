
#
# Lets describe the rules for protocol, e.g: HTTP, SNMP, CAN, I2C, 1-wire 
#

MAIN 			-> PROTO

PROTO			->	"HTTP"
				| "SNMP"
				| "CAN"
				| "I2C"
				| "1-wire"
					
