"""
Network Ping Monitor Script
Pings IP addresses and checks device availability in the network.
"""

import subprocess
import sys
import threading
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import ip_address, ip_network, AddressValueError
import json
import csv
from datetime import datetime

class NetworkPinger:
    def __init__(self, timeout=3, count=1):
        """
        Initialize the NetworkPinger.
        
        Args:
            timeout (int): Ping timeout in seconds
            count (int): Number of ping packets to send
        """
        self.timeout = timeout
        self.count = count
        self.results = {}
        
    def ping_single_ip(self, ip):
        """
        Ping a single IP address.
        
        Args:
            ip (str): IP address to ping
            
        Returns:
            dict: Ping result with status, response time, etc.
        """
        try:
            # ping i işletim sistemine göre belirle
            if sys.platform.startswith('win'):
                cmd = ['ping', '-n', str(self.count), '-w', str(self.timeout * 1000), str(ip)]
            else:
                cmd = ['ping', '-c', str(self.count), '-W', str(self.timeout), str(ip)]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 5)
            end_time = time.time()
            
            response_time = round((end_time - start_time) * 1000, 2)  # milisaniye cinsinden
            
            if result.returncode == 0:
                # cevap alındıysa, çıktıyı ayrıştır
                if sys.platform.startswith('win'):
                    # Windows ping çıktısı ayrıştırma
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'time=' in line or 'time<' in line:
                            try:
                                time_part = line.split('time')[1].split('ms')[0]
                                if '<' in time_part:
                                    parsed_time = float(time_part.replace('<', '').replace('=', ''))
                                else:
                                    parsed_time = float(time_part.replace('=', ''))
                                response_time = parsed_time
                                break
                            except (ValueError, IndexError):
                                pass
                else:
                    # Unix/Linux ping çıktısı ayrıştırma
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'time=' in line:
                            try:
                                time_part = line.split('time=')[1].split(' ')[0]
                                response_time = float(time_part)
                                break
                            except (ValueError, IndexError):
                                pass
                
                return {
                    'ip': ip,
                    'status': 'online',
                    'response_time': response_time,
                    'timestamp': datetime.now().isoformat(),
                    'raw_output': result.stdout.strip()
                }
            else:
                return {
                    'ip': ip,
                    'status': 'offline',
                    'response_time': None,
                    'timestamp': datetime.now().isoformat(),
                    'error': result.stderr.strip() if result.stderr else 'Host unreachable'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'ip': ip,
                'status': 'timeout',
                'response_time': None,
                'timestamp': datetime.now().isoformat(),
                'error': f'Ping timeout after {self.timeout} seconds'
            }
        except Exception as e:
            return {
                'ip': ip,
                'status': 'error',
                'response_time': None,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def ping_multiple_ips(self, ip_list, max_workers=50):
        """
        Ping multiple IP addresses concurrently.
        
        Args:
            ip_list (list): List of IP addresses to ping
            max_workers (int): Maximum number of concurrent threads
            
        Returns:
            dict: Results dictionary with IP as key and result as value
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # tüm ping tasklerini başlat
            future_to_ip = {executor.submit(self.ping_single_ip, ip): ip for ip in ip_list}
            
            for future in as_completed(future_to_ip):
                result = future.result()
                results[result['ip']] = result
                
        return results
    
    def ping_network_range(self, network, max_workers=50):
        """
        Ping all hosts in a network range.
        
        Args:
            network (str): Network in CIDR notation (e.g., '192.168.1.0/24')
            max_workers (int): Maximum number of concurrent threads
            
        Returns:
            dict: Results dictionary
        """
        try:
            net = ip_network(network, strict=False)
            ip_list = [str(ip) for ip in net.hosts()]
            
            # /24 ağındaki 256 hostu rangele
            if len(ip_list) > 254:
                print(f"Warning: Network {network} contains {len(ip_list)} hosts. This may take a while...")
            
            return self.ping_multiple_ips(ip_list, max_workers)
            
        except AddressValueError as e:
            print(f"Invalid network range: {e}")
            return {}
    
    def continuous_monitor(self, ip_list, interval=60, duration=None):
        """
        Continuously monitor IP addresses.
        
        Args:
            ip_list (list): List of IP addresses to monitor
            interval (int): Time between ping cycles in seconds
            duration (int): Total monitoring duration in seconds (None for infinite)
        """
        start_time = time.time()
        cycle = 1
        
        try:
            while True:
                print(f"\n=== Monitoring Cycle {cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
                
                results = self.ping_multiple_ips(ip_list)
                self.print_results(results)
                
                if duration and (time.time() - start_time) >= duration:
                    print(f"\nMonitoring completed after {duration} seconds")
                    break
                
                cycle += 1
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\nMonitoring stopped by user after {cycle-1} cycles")
    
    def print_results(self, results, show_details=False):
        """
        Print ping results in a formatted table.
        
        Args:
            results (dict): Results from ping operations
            show_details (bool): Whether to show detailed information
        """
        if not results:
            print("No results to display")
            return
        
        # Sort IP address
        sorted_results = sorted(results.items(), key=lambda x: ip_address(x[0]))
        
        online = sum(1 for r in results.values() if r['status'] == 'online')
        offline = sum(1 for r in results.values() if r['status'] == 'offline')
        errors = sum(1 for r in results.values() if r['status'] in ['timeout', 'error'])
        
        print(f"\n{'IP Address':<15} {'Status':<10} {'Response Time':<15} {'Timestamp':<20}")
        print("-" * 65)
        
        for ip, result in sorted_results:
            status = result['status'].upper()
            response_time = f"{result['response_time']:.2f}ms" if result['response_time'] else "N/A"
            timestamp = result['timestamp'][:19].replace('T', ' ')
            
            status_display = status
            if result['status'] == 'online':
                status_display = f"✓ {status}"
            elif result['status'] == 'offline':
                status_display = f"✗ {status}"
            else:
                status_display = f"⚠ {status}"
            
            print(f"{ip:<15} {status_display:<10} {response_time:<15} {timestamp:<20}")
            
            if show_details and 'error' in result:
                print(f"{'':>15} Error: {result['error']}")
        
        print(f"\nSummary: {online} online, {offline} offline, {errors} errors/timeouts")
    
    def export_results(self, results, filename, format_type='json'):
        """
        Export results to file.
        
        Args:
            results (dict): Results to export
            filename (str): Output filename
            format_type (str): Export format ('json' or 'csv')
        """
        try:
            if format_type.lower() == 'json':
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
            
            elif format_type.lower() == 'csv':
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['IP', 'Status', 'Response_Time_ms', 'Timestamp', 'Error'])
                    
                    for ip, result in results.items():
                        writer.writerow([
                            ip,
                            result['status'],
                            result.get('response_time', ''),
                            result['timestamp'],
                            result.get('error', '')
                        ])
            
            print(f"Results exported to {filename}")
            
        except Exception as e:
            print(f"Error exporting results: {e}")

def validate_ip(ip_str):
    """Validate if string is a valid IP address."""
    try:
        ip_address(ip_str)
        return True
    except AddressValueError:
        return False

def main():
    parser = argparse.ArgumentParser(description='Network Ping Monitor - Check device availability')
    parser.add_argument('targets', nargs='*', help='IP addresses or network ranges to ping')
    parser.add_argument('-t', '--timeout', type=int, default=3, help='Ping timeout in seconds (default: 3)')
    parser.add_argument('-c', '--count', type=int, default=1, help='Number of ping packets (default: 1)')
    parser.add_argument('-w', '--workers', type=int, default=50, help='Max concurrent threads (default: 50)')
    parser.add_argument('-n', '--network', help='Network range in CIDR notation (e.g., 192.168.1.0/24)')
    parser.add_argument('-f', '--file', help='Read IP addresses from file (one per line)')
    parser.add_argument('-o', '--output', help='Export results to file')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format (default: json)')
    parser.add_argument('-m', '--monitor', action='store_true', help='Continuous monitoring mode')
    parser.add_argument('-i', '--interval', type=int, default=60, help='Monitoring interval in seconds (default: 60)')
    parser.add_argument('-d', '--duration', type=int, help='Monitoring duration in seconds')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output')
    
    args = parser.parse_args()
    
    # Initialize pinger
    pinger = NetworkPinger(timeout=args.timeout, count=args.count)
    
    ip_list = []
    
    if args.targets:
        for target in args.targets:
            if validate_ip(target):
                ip_list.append(target)
            else:
                print(f"Warning: '{target}' is not a valid IP address")
    
    # network range
    if args.network:
        print(f"Scanning network range: {args.network}")
        results = pinger.ping_network_range(args.network, args.workers)
        pinger.print_results(results, args.verbose)
        
        if args.output:
            pinger.export_results(results, args.output, args.format)
        return
    
    # dosyadan
    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_ips = [line.strip() for line in f if line.strip() and validate_ip(line.strip())]
                ip_list.extend(file_ips)
                print(f"Loaded {len(file_ips)} IP addresses from {args.file}")
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found")
            return
    
    # ip kullanılmadıysa lokal ip adreslerini al
    if not ip_list:
        print("No IP addresses specified. Use -h for help.")
        print("Example usage:")
        print("  python ping_monitor.py 8.8.8.8 1.1.1.1")
        print("  python ping_monitor.py -n 192.168.1.0/24")
        print("  python ping_monitor.py -f ip_list.txt")
        return
    
    print(f"Pinging {len(ip_list)} IP addresses...")
    
    if args.monitor:
        print(f"Starting continuous monitoring (interval: {args.interval}s)")
        if args.duration:
            print(f"Duration: {args.duration}s")
        pinger.continuous_monitor(ip_list, args.interval, args.duration)
    else:
        # Single ping cycle
        results = pinger.ping_multiple_ips(ip_list, args.workers)
        pinger.print_results(results, args.verbose)
        
        if args.output:
            pinger.export_results(results, args.output, args.format)

if __name__ == "__main__":
    main()