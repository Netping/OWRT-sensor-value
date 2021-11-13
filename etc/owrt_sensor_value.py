#!/usr/bin/env python3

import sys
from owrt_snmp_protocol import snmp_protocol
from threading import Thread, Lock
from journal import journal

try:
    import ubus
except ImportError:
    journal.WriteLog("OWRT_Sensor_value", "Normal", "err", "Failed import ubus")
    sys.exit(-1)

fl_run_main = True
curr_sensors = {}
snmp_pr = snmp_protocol()
uci_config_sensor = "owrt_sensor_value"
lock_curr_sensors = Lock()


def ubus_init():
    def get_value_callback(event, data):
        ret_val = {}
        sect = data['id_sensor']
        lock_curr_sensors.acquire()
        try:
            sensor_dict = curr_sensors[sect]
        except KeyError:
            # poll sensor with id_sensor not found
            journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                             "get_value_callback() id_sensor " + sect + " not found")
            ret_val["value"] = '-999999'
            ret_val["unit"] = ''
            ret_val["status"] = '-2'
        else:
            # set the number of decimal places to result
            ret_val["value"] = f"{sensor_dict['value']:.{int(sensor_dict['precision'])}f}"
            ret_val["unit"] = sensor_dict['unit']
            ret_val["status"] = sensor_dict['status']
        finally:
            lock_curr_sensors.release()
            event.reply(ret_val)

    ubus.add(
        'owrt_sensor_value', {
            'get_value': {
                'method': get_value_callback,
                'signature': {
                    'id_sensor': ubus.BLOBMSG_TYPE_STRING
                }
            }
        }
    )


def check_param_snmp(param):
    try:
        address = param['address']
        port = param['port']
        oid = param['oid']
        period = param['period']
        community = param['community']
        timeout = param['timeout']
    except KeyError:
        return False
    return True


def parseconfig():
    lock_curr_sensors.acquire()
    curr_sensors.clear()
    lock_curr_sensors.release()
    try:
        confvalues = ubus.call("uci", "get", {"config": uci_config_sensor})
    except RuntimeError:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                         "parseconfig() error get " + uci_config_sensor)
        sys.exit(-1)

    for confdict in list(confvalues[0]['values'].values()):
        if confdict['.type'] == "info":
            if confdict['proto'] == "SNMP":
                if not check_param_snmp(confdict):
                    journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                                     "parseconfig() error parameters SNMP " + confdict['.name'])
                    continue

                confdict['status'] = '-1'
                confdict['value'] = '-999999'
                lock_curr_sensors.acquire()
                curr_sensors[confdict['.name']] = confdict
                lock_curr_sensors.release()


def run_poll_sensor(sensor):
    lock_curr_sensors.acquire()
    config_sensor = curr_sensors.get(sensor)
    if config_sensor is None:
        # sensor delete
        lock_curr_sensors.release()
        return

    if config_sensor['proto'] == "SNMP":
        if not check_param_snmp(config_sensor):
            del curr_sensors[sensor]
            lock_curr_sensors.release()
            return

    id_poll = snmp_pr.start_snmp_poll(config_sensor['address'], config_sensor['community'], config_sensor['oid'],
                                      config_sensor['port'], config_sensor['timeout'], config_sensor['period'])
    config_sensor['id_task'] = id_poll
    lock_curr_sensors.release()
    journal.WriteLog("OWRT_Sensor_value", "Normal", "notice", "start polling sensor " + sensor)


def poll_value(sensor):
    lock_curr_sensors.acquire()
    config_sensor = curr_sensors.get(sensor)
    if config_sensor is None:
        # sensor delete
        lock_curr_sensors.release()
        return

    try:
        id_poll = config_sensor['id_task']
    except KeyError:
        lock_curr_sensors.release()
        return

    value, status = snmp_pr.get_snmp_poll(id_poll)

    config_sensor['value'] = float(value)
    config_sensor['status'] = status

    lock_curr_sensors.release()


if __name__ == '__main__':
    if not ubus.connect("/var/run/ubus.sock"):
        journal.WriteLog("OWRT_Sensor_value", "Normal", "err", "Failed connect to ubus")
        sys.exit(-1)

    journal.WriteLog("OWRT_Sensor_value", "Normal", "notice", "Start module!")

    ubus_init()
    parseconfig()

    lock_curr_sensors.acquire()
    sensors = list(curr_sensors.keys())
    lock_curr_sensors.release()
    for sensor in sensors:
        th = Thread(target=run_poll_sensor, args=(sensor,))
        th.start()

    try:
        while fl_run_main:
            ubus.loop(1)
            lock_curr_sensors.acquire()
            sensors = list(curr_sensors.keys())
            lock_curr_sensors.release()
            for sensor in sensors:
                poll_value(sensor)
                ubus.loop(1)
    except KeyboardInterrupt:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "notice", "Stop module!")
    finally:
        if not lock_curr_sensors.locked():
            lock_curr_sensors.acquire()
        sensors = list(curr_sensors.keys())
        for sensor in sensors:
            try:
                config = curr_sensors.pop(sensor)
                snmp_pr.stop_snmp_poll(config['id_task'])
                journal.WriteLog("OWRT_Sensor_value", "Normal", "notice", "stop polling sensor " + sensor)
            except KeyError:
                continue
        lock_curr_sensors.release()

    ubus.disconnect()
