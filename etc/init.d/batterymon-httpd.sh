#!/bin/sh
### BEGIN INIT INFO
# Provides:          batterymon-httpd
# Required-Start:    $network
# Required-Stop:     $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: batterymon HTTPd
### END INIT INFO

# Settings
HTTPD_PORT='8443'
HTTPD_ADDR='[::]'
USER='nobody'
GROUP='nogroup'
BATTERYMON_HTTPD="$(readlink -f "${0}")"; BATTERYMON_HTTPD="${BATTERYMON_HTTPD%/*}/../.."

[ -f "${BATTERYMON_HTTPD}/etc/default/batterymon-httpd" ] && . "${BATTERYMON_HTTPD}/etc/default/batterymon-httpd"

PIDFILE='/var/run/batterymon-httpd.pid'
DAEMON='/usr/bin/env'
DAEMON_OPTS='PYTHONPYCACHEPREFIX=/tmp/.batterymon-httpd-pyc '"${BATTERYMON_HTTPD}"'/bin/batterymon-httpd.py '"${HTTPD_PORT} ${HTTPD_ADDR}"

PATH=/sbin:/bin:/usr/sbin:/usr/bin

. /lib/lsb/init-functions

case "$1" in
	'start')
		log_daemon_msg 'Starting batterymon http server' 'batterymon-httpd'

		if [ ! -e '/tmp/.batterymon-httpd-pyc' ]; then
			mkdir '/tmp/.batterymon-httpd-pyc'
			chown "${USER}:${GROUP}" '/tmp/.batterymon-httpd-pyc'
			chmod 700 '/tmp/.batterymon-httpd-pyc'
		fi

		start-stop-daemon --start --quiet --background --chuid $USER:$GROUP --make-pidfile --pidfile $PIDFILE --exec $DAEMON -- $DAEMON_OPTS && log_end_msg 0 || log_end_msg 1
	;;
	'stop')
		log_daemon_msg 'Stopping batterymon http server' 'batterymon-httpd'
		if [ -e $PIDFILE ]; then
			daemon_pid=$(cat ${PIDFILE})
			start-stop-daemon --stop --quiet --pidfile $PIDFILE && rm $PIDFILE && \
			log_end_msg $?
		else
			log_end_msg 1
		fi
	;;
	'status')
		status_of_proc -p $PIDFILE $DAEMON "batterymon-httpd" && exit 0 || exit $?
	;;
	*)
		echo 'batterymon-httpd.sh start|stop|status'
		exit 1
	;;
esac

exit 0
