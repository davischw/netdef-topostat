## NetDEF FRR Topotest Result Statistics Tool

### client
Parses a junit xml file and sends the containing test results as a ZeroMQ JSON
data message to the server. It depends on a few environment variables exported
by bamboo-agent. The client resolves DNS server addresses to ipv4/ipv6 addresses
before passing them to the ZeroMQ cython backend to prevent failures.
```
usage: client.py [-h] [-v] [-d] [-c CONFIG] [-a ADDRESS] [-p PORT] [-s SENDER]
                 [-k KEY] [-f FILE] [-l LOG]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         verbose output
  -d, --debug           debug messages
  -c CONFIG, --config CONFIG
                        configuration file
  -a ADDRESS, --address ADDRESS
                        server address
  -p PORT, --port PORT  server tcp port
  -s SENDER, --sender SENDER
                        sender identification
  -k KEY, --key KEY     authentication key
  -f FILE, --file FILE  junit xml file
  -l LOG, --log LOG     log file
```


### server
Receives the test results as ZeroMQ JSON data messages, and verifies and stores
them in a sqlite3 database file. The server is intended to be run as a systemd
service by a user with limited permissions.
```
usage: server.py [-h] [-v] [-d] [-c CONFIG] [-n6] [-a6 IPV6_ADDRESS]
                 [-p6 IPV6_PORT] [-n4] [-a4 IPV4_ADDRESS] [-p4 IPV4_PORT]
                 [-k KEY] [-b DATABASE] [-l LOG]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         verbosity
  -d, --debug           debug messages
  -c CONFIG, --config CONFIG
                        configuration file
  -n6, --no-ipv6        no ipv6 listen address
  -a6 IPV6_ADDRESS, --ipv6-address IPV6_ADDRESS
                        server ipv6 address
  -p6 IPV6_PORT, --ipv6-port IPV6_PORT
                        server ipv6 tcp port
  -n4, --no-ipv4        no ipv4 listen address
  -a4 IPV4_ADDRESS, --ipv4-address IPV4_ADDRESS
                        server ipv4 address
  -p4 IPV4_PORT, --ipv4-port IPV4_PORT
                        server ipv4 tcp port
  -k KEY, --key KEY     authentication key
  -b DATABASE, --database DATABASE
                        sqlite3 database file
  -l LOG, --log LOG     log file
```


### authentication key
The clients need to be configured with the same ``auth_key`` string as the
server. Unauthenticated messages will be rejected by the server. The key does
not get displayed in program output or written to log files. A suitable key can
be generated i.e. with ``pwgen``:
```
pwgen -s1 64
```

### setup on debian and deriverates
#### install packages
```
apt install git python3-pip
python3 -m pip install -U setuptools
python3 -m pip install -U pip
python3 -m pip install pyzmq
python3 -m pip install junitparser
python3 -m pip install pysqlite3
python3 -m pip install pymysql
python3 -m pip install psycopg2
```

#### clone code from git repo
```
git clone --single-branch --depth=1 \
        https://git.netdef.org/scm/netdef/topostat.git topostat
```

#### create topostat user and group
```
adduser --system --disabled-login --shell /bin/false --group \
        --gecos "NetDEF Topotest Results Statistics Tool" \
        --home /home/topostat topostat
```

#### copy files
```
cd topostat/
mkdir -p /usr/local/lib/topostat
cp -rv * /usr/local/lib/topostat/
cp -v config/topostat.conf /etc/topostat.conf
chown -R topostat:topostat /usr/local/lib/topostat /etc/topostat.conf
chmod -R 755 /usr/local/lib/topostat /etc/topostat.conf
```

#### create directories
```
mkdir -p /var/log/topostat
chown -R topostat:topostat /var/log/topostat
chmod -R 744 /var/log/topostat
chmod -R 755 /home/topostat
```

#### edit config file
* set server ip address and port (both)
* set authentication key (both)
* set log file location (both)
* set database location (server only)
* set xml file location (client only)
```
vi /etc/topostat.conf
```

#### install and enable systemd and start service (server only)
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


### troubleshooting
Run the client and the server with the ``-v`` or ``-d`` arguments to get verbose
output and debug messages, and check the logs.


### bamboo environment variables
The client depends on a few environment variables exported by bamboo agent. For
testing and debugging purposes they can be exported before starting the client:
```
export bamboo_planKey="testPlanKey"
export bamboo_buildNumber=1337
export bamboo_shortJobName="testShortJobName"
```
