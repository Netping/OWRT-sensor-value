SECTION="NetPing modules"
CATEGORY="Base"
TITLE="EPIC OWRT_Sensor_value"

PKG_NAME="OWRT_Sensor_value"
PKG_VERSION="Epic.V0.S1"
PKG_RELEASE=1

CONF_FILES=owrt_sensor_value
CONF_DIR=/etc/config/

ETC_FILES=owrt_sensor_value.py
ETC_FILES_DIR=/etc/netping_sensor_value/

CLI_COMMANDS_DIR=commands
CLI_HELP_FILE=Help
CLI_CONFIGNAME=Configname

EBNF_SRC_DIR=ebnf
EBNF_FILES_DIR=/etc/netping_sensor_value/ebnf/

.PHONY: all install

all: install

install:
	for f in $(CONF_FILES); do cp $${f} $(CONF_DIR); done
	mkdir $(ETC_FILES_DIR)
	for f in $(ETC_FILES); do cp etc/$${f} $(ETC_FILES_DIR); done
	cp -r $(CLI_COMMANDS_DIR) $(CLI_HELP_FILE) $(CLI_CONFIGNAME) $(ETC_FILES_DIR)
	mkdir $(EBNF_FILES_DIR)
	cp $(EBNF_SRC_DIR)/*.py $(EBNF_FILES_DIR)

clean:
	for f in $(CONF_FILES); do rm -f $(CONF_DIR)$${f}; done
	rm -rf $(ETC_FILES_DIR)
