import click
import sys

@click.command()
def main():
    '''Send signal when changed config file'''
    try:
        import ubus
    except ImportError:
        print('Failed import ubus.')
        sys.exit(-1)

    if not ubus.connect("/var/run/ubus.sock"):
        print("Failed connect to ubus")
        sys.exit(-1)

    ubus.send("commit", {"config": "owrt_sensor_value"})

if __name__ == "__main__":
    main()
