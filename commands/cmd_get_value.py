import click
import sys

@click.command()
@click.option('-s', '--sensor', default='', help='Unique identifier of the sensor')
def main(sensor):
    '''Get value and status sensor'''
    try:
        import ubus
    except ImportError:
        print('Failed import ubus.')
        sys.exit(-1)

    if not ubus.connect("/var/run/ubus.sock"):
        print("Failed connect to ubus")
        sys.exit(-1)

    print(ubus.call("owrt_sensor_value", "get_value", {"id_sensor":sensor}))

if __name__ == "__main__":
    main()
