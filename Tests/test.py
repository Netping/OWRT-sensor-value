import ubus
import os
import time




def test_conf_existance():
    ret = False

    try:
        if not os.path.isfile("/etc/config/owrt-sensor-value"):
            raise ValueError('Config not found')

        ret = True

    except Exception as ex:
        print(ex)

    assert ret

def test_conf_valid():
    ret = False

    try:
        ubus.connect()

        confvalues = ubus.call("uci", "get", {"config": "owrt-sensor-value"})
        for confdict in list(confvalues[0]['values'].values()):
            #check globals
            if confdict['.name'] == 'globals':
                assert confdict['default_memo'] == 'Sensor'
                assert confdict['status'] == ['0.Норма', '1.Таймаут', '2.Ошибка']
                assert confdict['default_timeout'] == '5'
                assert confdict['default_period'] == '1'

            #check sensor_prototype_snmp
            if confdict['.name'] == 'sensor_prototype_snmp':
                assert confdict['memo'] == 'Sensor'
                assert confdict['precision'] == '0'
                assert confdict['proto'] == 'SNMP'
                assert confdict['community'] == '0'
                assert confdict['address'] == '0'
                assert confdict['port'] == '0'
                assert confdict['oid'] == '0'
                assert confdict['type_oid'] == '0'
                assert confdict['timeout'] == '5'
                assert confdict['period'] == '1'

        ubus.disconnect()

        ret = True

    except Exception as ex:
        print(ex)

    assert ret

def test_running():
    ret = False

    try:
        ubus.connect()

        for l in list(ubus.objects().keys()):
            if l == 'owrt-sensor-value':
                ret = True
                break

        ubus.disconnect()
    except Exception as ex:
        print(ex)

    assert ret

def test_ubus_api():
    ret = False

    try:
        #set config items
        if os.system("uci set owrt-sensor-value.td28933=info"):
            raise ValueError("Can't create new section")

        if os.system("uci set owrt-sensor-value.td28933.memo='Out_temperature'"):
            raise ValueError("Can't set option memo")

        if os.system("uci set owrt-sensor-value.td28933.unit='C'"):
            raise ValueError("Can't set option unit")

        if os.system("uci set owrt-sensor-value.td28933.precision='2'"):
            raise ValueError("Can't set option precision")

        if os.system("uci set owrt-sensor-value.td28933.proto='SNMP'"):
            raise ValueError("Can't set option proto")

        if os.system("uci set owrt-sensor-value.td28933.community='ping32'"):
            raise ValueError("Can't set option community")

        if os.system("uci set owrt-sensor-value.td28933.address='125.227.188.172'"):
            raise ValueError("Can't set option address")

        if os.system("uci set owrt-sensor-value.td28933.oid='.1.3.6.1.4.1.25728.8800.1.1.2.1'"):
            raise ValueError("Can't set option oid")

        if os.system("uci set owrt-sensor-value.td28933.type_oid='Integer'"):
            raise ValueError("Can't set option type_oid")

        if os.system("uci set owrt-sensor-value.td28933.port='31132'"):
            raise ValueError("Can't set option port")

        if os.system("uci set owrt-sensor-value.td28933.timeout='3'"):
            raise ValueError("Can't set option timeout")

        if os.system("uci set owrt-sensor-value.td28933.period='1'"):
            raise ValueError("Can't set option period")

        if os.system("uci set owrt-sensor-value.td28933.period='1'"):
            raise ValueError("Can't set option period")

        if os.system("uci commit owrt-sensor-value"):
            raise ValueError("Can't commit config owrt-sensor-value")

        #send commit signal for module
        if os.system("ubus send commit '{\"config\":\"owrt-sensor-value\"}'"):
            raise ValueError("Can't send commit signal to owrt-sensor-value")

        #wait for sensor getting value
        time.sleep(5)

        ubus.connect()

        result = ubus.call('owrt-sensor-value', 'get_value', {"id_sensor":"td28933","ubus_rpc_session":"1"})[0]

        ubus.disconnect()

        #check result
        expected_keys = [ 'value', 'unit', 'status' ]
        keys_length = len(list(result.keys()))

        if keys_length != 3:
            raise ValueError("Bad key length!")

        for l in list(result.keys()):
            if not l in expected_keys:
                raise ValueError("Bad key \"" + l + "\"")

        ret = True
    except Exception as ex:
        print(ex)

    #delete section from config
    os.system("uci delete owrt-sensor-value.td28933")
    os.system("uci commit owrt-sensor-value")
    os.system("ubus send commit '{\"config\":\"owrt-sensor-value\"}'")

    assert ret
