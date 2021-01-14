# netdef-topostat
NetDEF FRR Topotest Result Statistics Tool

## client
Parses a junit xml file and sends the containing test results as a ZeroMQ JSON data message to the server.
It depends on a few environment variables exported by bamboo-agent.
```
usage: client.py [-h] [-v] [-d] [-c CONFIG] [-a ADDRESS] [-p PORT] [-k KEY]
                 [-f FILE] [-l LOG]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         verbosity
  -d, --debug           debug messages
  -c CONFIG, --config CONFIG
                        configuration file
  -a ADDRESS, --address ADDRESS
                        server address
  -p PORT, --port PORT  server tcp port
  -k KEY, --key KEY     authentication key
  -f FILE, --file FILE  junit xml file
  -l LOG, --log LOG     log file
```

## server
Receives the test results as ZeroMQ JSON data messages, and verifies and stores them in a sqlite3 database file.
The server should be run as a systemd service.
```
usage: server.py [-h] [-v] [-d] [-c CONFIG] [-a ADDRESS] [-p PORT] [-k KEY]
                 [-b DATABASE] [-l LOG]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         verbosity
  -d, --debug           debug messages
  -c CONFIG, --config CONFIG
                        configuration file
  -a ADDRESS, --address ADDRESS
                        server address
  -p PORT, --port PORT  server tcp port
  -k KEY, --key KEY     authentication key
  -b DATABASE, --database DATABASE
                        sqlite3 database file
  -l LOG, --log LOG     log file
```

## authentication key
The clients need to be configured with the same ``auth_key`` string as the server.
Unauthenticated messages will be rejected by the server.
A suitable key can be generated i.e. with ``pwgen``:
```
pwgen -s1 64
```

## setup on debian and deriverates
### install packages
```
apt install git python3-pip
python3 -m pip install pyzmq
python3 -m pip install junitparser
python3 -m pip install pysqlite3
```

### clone code from git repo
```
git clone --single-branch --depth=1 \
        https://git.netdef.org/scm/netdef/topostat.git topostat
```

### create topostat user and group
```
adduser --system --disabled-login --shell /bin/false --group \
        --gecos "NetDEF Topotest Results Statistics Tool" \
        --home /var/lib/topostat topostat
```

### copy files
```
cd topostat/
mkdir -p /usr/lib/topostat
cp -rv * /usr/lib/topostat/
cp -v config/topostat.conf /etc/topostat.conf
chown -R topostat:topostat /usr/lib/topostat /etc/topostat.conf
chmod -R 755 /usr/lib/topostat /etc/topostat.conf
```

### create directories
```
mkdir -p /var/log/topostat
chown -R topostat:topostat /var/log/topostat
chmod -R 744 /var/log/topostat
chmod -R 755 /var/lib/topostat
```

### edit config file
* set server ip address and port (both)
* set authentication key (both)
* set log file location (both)
* set database location (server only)
* set xml file location (client only)
```
vi /etc/topostat.conf
```

### install and enable systemd and start service (server only)
```
cp -v init/topostat.service /etc/systemd/system/topostat.service
chmod 644 /etc/systemd/system/topostat.service
systemctl daemon-reload
systemctl enable topostat
systemctl start topostat
```
check the service status and log for errors
```
systemctl status topostat
journalctl -u topostat
less /var/log/topostat/server.log
```

## troubleshooting
Run the client and the server with the ``-v`` and ``-d`` arguments to get verbose output and debug messages and check the logs.

## bamboo environment variables
The client depends on a few environment variables exported by bamboo agent.
For testing and debugging purposes they can be exported before starting the client:
```
export bamboo_planKey="testPlanKey"
export bamboo_buildNumber="testBuildNumber"
export bamboo_shortJobName="testShortJobName"
/usr/bin/env python3 /usr/lib/topostat/client.py
```
