# real_performance_test.py - Real PAM System Performance Testing
import requests
import time
import statistics
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import sys
from datetime import datetime

class PAMPerformanceTester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {}
        
    def test_operation_response_times(self, operation_name, url, method="GET", data=None, iterations=50):
        """Test response times for a specific operation"""
        
        print(f"🔄 Testing {operation_name}...")
        times = []
        success_count = 0
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                if method == "GET":
                    response = self.session.get(url, timeout=10)
                elif method == "POST":
                    response = self.session.post(url, json=data, timeout=10)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if response.status_code in [200, 302, 401, 403]:  # Accept redirects and auth errors
                    times.append(response_time)
                    success_count += 1
                
                # Small delay between requests
                time.sleep(0.05)
                
            except Exception as e:
                print(f"   Request {i+1} failed: {str(e)[:50]}...")
                continue
        
        if times:
            avg_time = statistics.mean(times)
            p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
            max_time = max(times)
            min_time = min(times)
            
            self.results[operation_name] = {
                'average_ms': avg_time,
                'p95_ms': p95_time,
                'max_ms': max_time,
                'min_ms': min_time,
                'success_rate': (success_count / iterations) * 100,
                'total_requests': iterations
            }
            
            print(f"   ✅ {operation_name}: {avg_time:.1f}ms avg, {p95_time:.1f}ms p95, {max_time:.1f}ms max")
        else:
            print(f"   ❌ {operation_name}: All requests failed")
    
    def run_comprehensive_response_time_tests(self):
        """Run response time tests for all PAM system operations"""
        
        print("=" * 70)
        print("🚀 REAL PAM SYSTEM RESPONSE TIME TESTING")
        print("=" * 70)
        print()
        
        # Test different operations
        operations = [
            ("Dashboard Load", f"{self.base_url}/", "GET"),
            ("Login Page Load", f"{self.base_url}/login", "GET"),
            ("Portal Access", f"{self.base_url}/portal", "GET"),
            ("User Info API", f"{self.base_url}/api/user_info", "GET"),
            ("Active Sessions", f"{self.base_url}/api/active_sessions", "GET"),
            ("Settings API", f"{self.base_url}/api/settings", "GET"),
            ("All Events API", f"{self.base_url}/api/all_events", "GET"),
            ("Risk Analysis", f"{self.base_url}/analyze", "POST", {
                "hour": 12, "ip_is_local": 1, "event_type": "DB_CONNECT", "user_role": "Database Admin"
            }),
            ("Action Logging", f"{self.base_url}/execute_action", "POST", {
                "action": "DB_CONNECT", "details": {"target_db": "test"}
            })
        ]
        
        for operation_name, url, method, *data in operations:
            request_data = data[0] if data else None
            self.test_operation_response_times(operation_name, url, method, request_data)
            time.sleep(0.5)  # Brief pause between different operations
        
        return self.results
    
    def create_response_time_chart(self):
        """Create a professional response time analysis chart"""
        
        if not self.results:
            print("❌ No results to chart")
            return
        
        # Prepare data for plotting
        operations = []
        averages = []
        p95s = []
        maxes = []
        
        for op_name, metrics in self.results.items():
            operations.append(op_name.replace(" ", "\n"))  # Multi-line labels
            averages.append(metrics['average_ms'] / 1000)  # Convert to seconds
            p95s.append(metrics['p95_ms'] / 1000)
            maxes.append(metrics['max_ms'] / 1000)
        
        # Create the chart
        fig, ax = plt.subplots(figsize=(14, 8))
        
        x = range(len(operations))
        width = 0.25
        
        bars1 = ax.bar([i - width for i in x], averages, width, label='Average', 
                      color='#2E86AB', alpha=0.8)
        bars2 = ax.bar(x, p95s, width, label='95th Percentile', 
                      color='#A23B72', alpha=0.8)
        bars3 = ax.bar([i + width for i in x], maxes, width, label='Maximum', 
                      color='#F18F01', alpha=0.8)
        
        # Customize the chart
        ax.set_xlabel('Operations', fontsize=14, fontweight='bold')
        ax.set_ylabel('Response Time (seconds)', fontsize=14, fontweight='bold')
        ax.set_title('PAM System - Response Time Analysis', fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(operations, fontsize=10, rotation=45, ha='right')
        ax.legend(fontsize=12, loc='upper right')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        def add_value_labels(bars):
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{height:.2f}s', ha='center', va='bottom', fontsize=9)
        
        add_value_labels(bars1)
        add_value_labels(bars2)
        add_value_labels(bars3)
        
        plt.tight_layout()
        plt.savefig('figure_6_22_response_times.png', dpi=300, bbox_inches='tight')
        plt.savefig('figure_6_22_response_times.pdf', dpi=300, bbox_inches='tight')
        
        print("✅ Response time chart saved as 'figure_6_22_response_times.png'")
        plt.show()
    
    def print_response_time_table(self):
        """Print formatted response time table for thesis"""
        
        print("\n" + "=" * 80)
        print("📊 RESPONSE TIME ANALYSIS RESULTS")
        print("=" * 80)
        
        print(f"{'Operation':<25} | {'Average':<8} | {'95th %ile':<10} | {'Maximum':<8}")
        print("-" * 70)
        
        for op_name, metrics in self.results.items():
            avg = f"{metrics['average_ms']/1000:.2f}s"
            p95 = f"{metrics['p95_ms']/1000:.2f}s"
            max_time = f"{metrics['max_ms']/1000:.2f}s"
            
            print(f"{op_name:<25} | {avg:<8} | {p95:<10} | {max_time:<8}")
        
        print("-" * 70)
        print()

class PAMLoadTester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        
    def run_apache_bench_tests(self):
        """Run comprehensive load testing with Apache Bench"""
        
        print("=" * 70)
        print("🔥 REAL PAM SYSTEM LOAD TESTING")  
        print("=" * 70)
        print()
        
        # Test different concurrent user loads
        test_scenarios = [
            (10, 100, "Light Load"),
            (25, 200, "Medium Load"), 
            (50, 300, "Heavy Load"),
            (75, 200, "Stress Test")
        ]
        
        results = {}
        
        for concurrent_users, total_requests, scenario_name in test_scenarios:
            print(f"🧪 Testing {scenario_name}: {concurrent_users} concurrent users, {total_requests} requests")
            
            # Test main dashboard endpoint
            cmd = f'ab -n {total_requests} -c {concurrent_users} -g ab_results.dat {self.base_url}/'
            
            try:
                import subprocess
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    output = result.stdout
                    # Parse key metrics from Apache Bench output
                    metrics = self.parse_ab_output(output)
                    results[scenario_name] = metrics
                    
                    print(f"   ✅ {scenario_name}: {metrics['requests_per_sec']:.1f} req/sec, "
                          f"{metrics['mean_response']:.0f}ms avg")
                else:
                    print(f"   ❌ {scenario_name}: Test failed")
                    
            except Exception as e:
                print(f"   ❌ {scenario_name}: {str(e)}")
            
            time.sleep(2)  # Brief pause between tests
        
        return results
    
    def parse_ab_output(self, output):
        """Parse Apache Bench output to extract key metrics"""
        
        metrics = {
            'requests_per_sec': 0,
            'mean_response': 0,
            'success_rate': 0,
            'failed_requests': 0,
            'total_requests': 0
        }
        
        lines = output.split('\n')
        
        for line in lines:
            if 'Requests per second:' in line:
                metrics['requests_per_sec'] = float(line.split()[3])
            elif 'Time per request:' in line and 'mean' in line:
                metrics['mean_response'] = float(line.split()[3])
            elif 'Failed requests:' in line:
                metrics['failed_requests'] = int(line.split()[2])
            elif 'Complete requests:' in line:
                metrics['total_requests'] = int(line.split()[2])
        
        if metrics['total_requests'] > 0:
            metrics['success_rate'] = ((metrics['total_requests'] - metrics['failed_requests']) / 
                                     metrics['total_requests']) * 100
        
        return metrics
    
    def create_load_testing_chart(self, results):
        """Create load testing results chart"""
        
        if not results:
            print("❌ No load testing results to chart")
            return
        
        scenarios = list(results.keys())
        req_per_sec = [results[s]['requests_per_sec'] for s in scenarios]
        response_times = [results[s]['mean_response'] for s in scenarios]
        success_rates = [results[s]['success_rate'] for s in scenarios]
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))
        
        # Requests per second
        ax1.bar(scenarios, req_per_sec, color='#2E86AB', alpha=0.8)
        ax1.set_title('Requests Per Second by Load Scenario', fontweight='bold')
        ax1.set_ylabel('Requests/sec')
        ax1.grid(True, alpha=0.3)
        
        # Response times
        ax2.bar(scenarios, response_times, color='#A23B72', alpha=0.8)
        ax2.set_title('Average Response Time by Load Scenario', fontweight='bold')
        ax2.set_ylabel('Response Time (ms)')
        ax2.grid(True, alpha=0.3)
        
        # Success rates
        ax3.bar(scenarios, success_rates, color='#F18F01', alpha=0.8)
        ax3.set_title('Success Rate by Load Scenario', fontweight='bold')
        ax3.set_ylabel('Success Rate (%)')
        ax3.set_ylim(0, 105)
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('figure_6_23_load_testing.png', dpi=300, bbox_inches='tight')
        plt.savefig('figure_6_23_load_testing.pdf', dpi=300, bbox_inches='tight')
        
        print("✅ Load testing chart saved as 'figure_6_23_load_testing.png'")
        plt.show()

def run_system_monitoring():
    """Monitor system resources during testing"""
    
    print("💻 System Resource Monitoring:")
    print(f"   CPU Usage: {psutil.cpu_percent(interval=1):.1f}%")
    print(f"   Memory Usage: {psutil.virtual_memory().percent:.1f}%")
    print(f"   Disk Usage: {psutil.disk_usage('/').percent:.1f}%")
    
    return {
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent
    }

def main():
    """Main performance testing function"""
    
    print("🎯 REAL PAM SYSTEM PERFORMANCE TESTING")
    print("=" * 50)
    print()
    
    # Check if PAM system is running
    try:
        response = requests.get("http://127.0.0.1:5000/login", timeout=5)
        print("✅ PAM system is accessible")
    except:
        print("❌ PAM system not accessible at http://127.0.0.1:5000")
        print("   Please start your PAM system first: python app.py")
        return
    
    # Monitor system resources
    system_info = run_system_monitoring()
    
    # Run response time testing
    print("\n🔬 Starting Response Time Testing...")
    response_tester = PAMPerformanceTester()
    response_results = response_tester.run_comprehensive_response_time_tests()
    
    if response_results:
        response_tester.print_response_time_table()
        response_tester.create_response_time_chart()
    
    # Run load testing (if Apache Bench available)
    print("\n🔥 Starting Load Testing...")
    try:
        load_tester = PAMLoadTester()
        load_results = load_tester.run_apache_bench_tests()
        
        if load_results:
            load_tester.create_load_testing_chart(load_results)
    except Exception as e:
        print(f"❌ Load testing failed: {e}")
        print("   Make sure Apache Bench (ab) is installed")
    
    # Save all results
    all_results = {
        'response_times': response_results,
        'system_info': system_info,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('pam_performance_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Results saved to 'pam_performance_results.json'")
    print("📊 Charts saved as PNG and PDF files")
    print("✅ Performance testing complete!")

if __name__ == '__main__':
    main()