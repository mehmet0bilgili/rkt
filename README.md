# rkt
staj
```bash
# Ping specific IPs
python network_ping.py 8.8.8.8 1.1.1.1 192.168.1.1

# Scan an entire network
python network_ping.py -n 192.168.1.0/24

# Read IPs from file
python network_ping.py -f ip_list.txt

# Continuous monitoring every 30 seconds
python network_ping.py -m -i 30 8.8.8.8 1.1.1.1

# Export results to CSV
python network_ping.py 8.8.8.8 1.1.1.1 -o results.csv --format csv
```
