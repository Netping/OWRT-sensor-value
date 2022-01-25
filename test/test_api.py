import ubus
import os




def get_package_info():
    ret = dict()

    with open('../Makefile.inf') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()

            if not line:
                continue

            if line.startswith('PKG_NAME='):
                line = line.replace('PKG_NAME=', '')

                if line[0] == '"' or line[0] == "'":
                    line = line[1:]

                if line[len(line) - 1] == '"' or line[len(line) - 1] == "'":
                    line = line[:-1]

                ret['name'] = line
                continue

            if line.startswith('PKG_VERSION='):
                line = line.replace('PKG_VERSION=', '')

                if line[0] == '"' or line[0] == "'":
                    line = line[1:]

                if line[len(line) - 1] == '"' or line[len(line) - 1] == "'":
                    line = line[:-1]

                ret['version'] = line
                continue

            if line.startswith('PKG_RELEASE='):
                line = line.replace('PKG_RELEASE=', '')

                if line[0] == '"' or line[0] == "'":
                    line = line[1:]

                if line[len(line) - 1] == '"' or line[len(line) - 1] == "'":
                    line = line[:-1]

                ret['release'] = line
                continue

    return ret

def print_header():
    info = get_package_info()
    print('\n')
    print('Testing ' + info['name'] + " version " + info['version'] + " release " + info['release'] + "\n...")
    print('\n')

print_header()

def test_conf_existance():
    ret = False

    try:
        if not os.path.isfile("/etc/config/owrt_sensor_value"):
            raise ValueError('Config not found')

        ret = True

    except Exception as ex:
        print(ex)

    assert ret

def test_conf_valid():
    ret = False

    try:
        ubus.connect()

        confvalues = ubus.call("uci", "get", {"config": "owrt_sensor_value"})
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
            if l == 'owrt_sensor_value':
                ret = True
                break

        ubus.disconnect()
    except Exception as ex:
        print(ex)

    assert ret

def test_ubus_api():
    ret = False

    try:
        ubus.connect()

        ubus.call('owrt_sensor_value', 'get_value', {"id_sensor":"td28933"})

        ubus.disconnect()

        ret = True
    except Exception as ex:
        print(ex)

    assert ret
