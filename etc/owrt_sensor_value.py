#!/usr/bin/env python3

import sys
import signal
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


def stop_run(signum, frame):
    global fl_run_main
    journal.WriteLog("OWRT_Sensor_value", "Normal", "notice", "Received termination signal!")
    fl_run_main = False


signal.signal(signal.SIGTERM, stop_run)


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
                    'id_sensor': ubus.BLOBMSG_TYPE_STRING,
                    'ubus_rpc_session': ubus.BLOBMSG_TYPE_STRING
                }
            }
        }
    )


def check_param_basic(param):
    res = True

    try:
        unit = param['unit']
    except KeyError:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                         "check_param_basic() id_sensor: " + param['.name'] + " not found 'unit'")
        res = False

    try:
        precision = param['precision']
    except KeyError:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                         "check_param_basic() id_sensor: " + param['.name'] + " not found 'precision'")
        res = False

    try:
        proto = param['proto']
    except KeyError:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                         "check_param_basic() id_sensor: " + param['.name'] + " not found 'proto'")
        res = False

    return res


def check_param_snmp(param):
    res = True

    try:
        address = param['address']
    except KeyError:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                         "check_param_snmp() id_sensor: " + param['.name'] + " not found 'address'")
        res = False

    try:
        port = param['port']
    except KeyError:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                         "check_param_snmp() id_sensor: " + param['.name'] + " not found 'port'")
        res = False

    try:
        oid = param['oid']
    except KeyError:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                         "check_param_snmp() id_sensor: " + param['.name'] + " not found 'oid'")
        res = False

    try:
        period = param['period']
    except KeyError:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                         "check_param_snmp() id_sensor: " + param['.name'] + " not found 'period'")
        res = False

    try:
        community = param['community']
    except KeyError:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                         "check_param_snmp() id_sensor: " + param['.name'] + " not found 'community'")
        res = False

    try:
        timeout = param['timeout']
    except KeyError:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                         "check_param_snmp() id_sensor: " + param['.name'] + " not found 'timeout'")
        res = False

    return res


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
            if not check_param_basic(confdict):
                journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                                 "parseconfig() error parameters basic " + confdict['.name'])
                continue
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


def diff_param_sensor(config, protodict):
    try:
        if config['unit'] == protodict['unit'] and config['precision'] == protodict['precision'] and \
                config['proto'] == protodict['proto']:
            return False
        else:
            return True
    except KeyError:
        return True


def diff_param_poll_snmp(config, protodict):
    try:
        if config['address'] == protodict['address'] and config['community'] == protodict['community'] and \
                config['oid'] == protodict['oid'] and config['port'] == protodict['port'] and \
                config['timeout'] == protodict['timeout'] and config['period'] == protodict['period']:
            return False
        else:
            return True
    except KeyError:
        return True


def check_edit_sensor(conf_proto):
    for protodict in list(conf_proto[0]['values'].values()):
        if protodict['.type'] == "info":
            config = curr_sensors.get(protodict['.name'])
            if config is not None:
                lock_curr_sensors.acquire()
                if not diff_param_sensor(config, protodict):
                    if protodict['proto'] == "SNMP":
                        if not diff_param_poll_snmp(config, protodict):
                            lock_curr_sensors.release()
                            continue
                    else:
                        lock_curr_sensors.release()
                        continue

                # Edit sensor
                if config['proto'] == "SNMP":
                    snmp_pr.stop_snmp_poll(config['id_task'])
                    journal.WriteLog("OWRT_Sensor_value", "Normal", "notice",
                                     "Edit sensor: stop polling sensor " + config['.name'])
                    del curr_sensors[config['.name']]

                if not check_param_basic(protodict):
                    lock_curr_sensors.release()
                    journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                                     "check_edit_sensor() error parameters basic " + protodict['.name'])
                    continue

                if protodict['proto'] == "SNMP":
                    if not check_param_snmp(protodict):
                        lock_curr_sensors.release()
                        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                                         "check_edit_sensor() error parameters SNMP " + protodict['.name'])
                        continue

                    protodict['status'] = '-1'
                    protodict['value'] = '-999999'
                    curr_sensors[protodict['.name']] = protodict
                    lock_curr_sensors.release()

                    # Run polling thread on SNMP
                    thrd = Thread(target=run_poll_sensor, args=(protodict['.name'],))
                    thrd.start()
                else:
                    lock_curr_sensors.release()


def check_add_sensor(conf_proto):
    for protodict in list(conf_proto[0]['values'].values()):
        if protodict['.type'] == "info":
            config = curr_sensors.get(protodict['.name'])
            if config is None:
                # Add new sensor
                if not check_param_basic(protodict):
                    journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                                     "check_add_sensor() error parameters basic " + protodict['.name'])
                    continue

                if protodict['proto'] == "SNMP":
                    if not check_param_snmp(protodict):
                        journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                                         "check_add_sensor() error parameters SNMP " + protodict['.name'])
                        continue

                    lock_curr_sensors.acquire()
                    protodict['status'] = '-1'
                    protodict['value'] = '-999999'
                    curr_sensors[protodict['.name']] = protodict
                    lock_curr_sensors.release()

                    # Run polling thread on SNMP
                    thrd = Thread(target=run_poll_sensor, args=(protodict['.name'],))
                    thrd.start()


def check_del_sensor(conf_proto):
    lock_curr_sensors.acquire()
    sensors = list(curr_sensors.keys())
    for sensor in sensors:
        sensor_exists = False
        for protodict in list(conf_proto[0]['values'].values()):
            if protodict['.type'] == "info":
                try:
                    if protodict['.name'] == sensor:
                        sensor_exists = True
                        break
                except KeyError:
                    pass

        if sensor_exists == False:
            try:
                # Deleting sensor
                config = curr_sensors.pop(sensor)
                snmp_pr.stop_snmp_poll(config['id_task'])
                journal.WriteLog("OWRT_Sensor_value", "Normal", "notice",
                                 "Deleting sensor: stop polling sensor " + config['.name'])
            except KeyError:
                journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                                 "reparseconfig(): Deleting sensor:  not found " + sensor)
                continue
    lock_curr_sensors.release()


def reparseconfig(event, data):
    global fl_run_main
    if data['config'] == uci_config_sensor:
        try:
            conf_proto = ubus.call("uci", "get", {"config": uci_config_sensor})
        except RuntimeError:
            journal.WriteLog("OWRT_Sensor_value", "Normal", "err",
                             "reparseconfig() error get " + uci_config_sensor)
            fl_run_main = False
            return

        check_add_sensor(conf_proto)
        check_edit_sensor(conf_proto)
        check_del_sensor(conf_proto)


def run_poll_sensor(sensor):
    lock_curr_sensors.acquire()
    config_sensor = curr_sensors.get(sensor)
    if config_sensor is None:
        # sensor delete
        lock_curr_sensors.release()
        return

    if config_sensor['proto'] == "SNMP":
        id_poll = snmp_pr.start_snmp_poll(config_sensor['address'], config_sensor['community'], config_sensor['oid'],
                                          config_sensor['port'], config_sensor['timeout'], config_sensor['period'])
        config_sensor['id_task'] = id_poll
        lock_curr_sensors.release()
        journal.WriteLog("OWRT_Sensor_value", "Normal", "notice", "start polling sensor " + sensor)
    else:
        lock_curr_sensors.release()


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

    ubus.listen(("commit", reparseconfig))

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
        pass
    finally:
        journal.WriteLog("OWRT_Sensor_value", "Normal", "notice", "Stop module!")

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
