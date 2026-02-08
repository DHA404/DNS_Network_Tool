# DNS Network Tool

<div align="center">

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)
![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)

**🚀 High-Performance Terminal DNS Resolution & Network Testing Tool**

A professional terminal-based domain name resolution and network testing tool with intelligent DNS server selection, parallel resolution, network performance testing, and automatic hosts file generation.

[中文版本](README.md) | [Quick Start](#quick-start) | [Usage Guide](#usage-guide) | [FAQ](#faq)

</div>

---

## 📋 Project Overview


## 📚 Table of Contents

### 🚀 Quick Start
- [📋 Project Overview](#-project-overview)
- [🌟 Core Features](#-core-features)
- [📥 Download](#-download)
- [📦 Installation](#-installation)
- [🚀 Running the Program](#-running-the-program)
- [🛠️ Quick Start](#-quick-start)

### 📖 Detailed Guide
- [📋 Usage Guide](#-usage-guide)
- [⚙️ Configuration](#️-configuration)
- [📄 Configuration File](#-configuration-file)
- [📝 Log Files](#-log-files)
- [🛠️ Tech Stack](#️-tech-stack)
- [❓ FAQ](#-faq)
- [🏗️ Architecture](#️-architecture)
- [⚡ Performance](#-performance)
- [🛡️ Error Handling](#️-error-handling)
- [🔧 Advanced Usage](#-advanced-usage)
- [🔒 Security](#-security)
- [📄 License](#-license)
- [🤝 Contributing](#-contributing)

## 🌟 Core Features

### 🖥️ Terminal Interface

- 📋 **Structured Interaction Flow** - Clear text guidance and operation hints
- 🎮 **Interactive Menu System** - Keyboard navigation support for easy operation
- 🎨 **Colorful Terminal Output** - Clear information hierarchy with visual appeal
- 📊 **Dynamic Progress Display** - Real-time status updates and progress bars
- ⚡ **Responsive Design** - Adapts to different terminal sizes

### 🌐 Domain Input

- 🎯 **Single Domain Input** - Instant format validation with intelligent error prompts
- 📝 **Batch Domain Input** - Support for `.txt` file import or multi-line paste
- 🔍 **Comprehensive Format Validation** - Strict validation based on RFC 1035 standard
- 🛠️ **Smart Correction Suggestions** - Precise error messages with correction solutions
- 🔄 **Automatic Duplicate Removal** - Avoid duplicate testing for improved efficiency

### 🚀 DNS Resolution

- 🌍 **200+ Public DNS Servers** - Intelligent selection of optimal servers
- ⚙️ **Custom DNS Management** - Add, delete, and priority sorting
- 🔄 **Parallel Resolution Engine** - Up to 50 threads concurrent processing

- ⏱️ **Detailed Performance Statistics** - Resolution time and success rate recording
- 🛡️ **DNS Pollution Detection** - Identify and avoid pollution issues
- ⚡ **Adaptive Timeout Strategy** - 0.8s ~ 5.0s intelligent adjustment
- 🔧 **Circuit Breaker Mechanism** - Exponential backoff retry for stability

### 📡 Network Performance Testing

- 🏓 **Smart Ping Testing** - Dual support for ICMP socket + system commands
- 🌊 **TCP/UDP Speed Testing** - Download + upload bidirectional testing
- 📈 **Multi-dimensional Data Analysis** - Latency, jitter, packet loss, speed
- ⚡ **Parallel IP Testing** - Up to 50 threads concurrent
- 📊 **Intelligent Statistical Analysis** - Multiple test runs with average calculation and outlier removal
- 🏆 **Top N Optimal Recommendations** - Intelligent recommendation of best IP addresses

### 📋 Result Output

- 📊 **Formatted Table Display** - Clear and intuitive result presentation
- 🔄 **Three Sorting Modes** - Latency-first, speed-first, balanced mode
- ⭐ **Smart Recommendation Markers** - Level markers for clear visibility
- 📝 **Hosts File Generation** - Standard format with one-click clipboard copy
- 💾 **Multi-format Export** - Support for `.txt` and `.csv` formats
- 🔍 **Result Filtering and Sorting** - Flexible data filtering functionality

### 🔧 Developer Mode

- 🐛 **Detailed Debug Logs** - Comprehensive debug information output
- 📊 **Performance Monitoring Reports** - Real-time performance analysis and reporting
- ⏱️ **Execution Time Statistics** - Code segment performance analysis
- 🧪 **Performance Benchmark Testing** - Built-in benchmark testing functionality

### ⚡ Advanced Features

- 🏃 **Performance Benchmark Testing** - Comprehensive performance assessment tools
- 🔄 **Configuration Hot Reload** - Configuration updates without restart
- 📝 **Detailed Logging** - Complete operation logs
- 🛡️ **Comprehensive Exception Handling** - Robust error handling mechanisms
- 📊 **Dynamic Progress Indication** - Real-time task progress display

## 📥 Download

### 🚀 Method 1: GitHub Clone (Recommended)

```bash
# Clone the source code repository
git clone https://github.com/DHA404/DNS_Network_Tool.git
cd DNS_Network_Tool
```

### 📦 Method 2: Manual Download

1. 🌐 Visit the project page: [DNS Network Tool](https://github.com/DHA404/DNS_Network_Tool)
2. 📥 Click the "Code" button and select "Download ZIP"
3. 📂 Extract the downloaded archive to local directory

---

### 💡 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Operating System | Windows 7 | Windows 10/11 |
| Python | 3.7+ | 3.9+ |
| Memory | 512MB | 2GB+ |
| Disk Space | 50MB | 100MB+ |

## 📦 Installation

```bash
# Install all dependencies
pip install -r requirements.txt
```

### 📋 Dependency Details

| Package | Version | Purpose |
|---------|---------|---------|
| `dnspython` | `>=2.8.0` | DNS resolution library |
| `requests` | `>=2.32.0` | HTTP request library |
| `colorama` | `>=0.4.6` | Terminal color support |
| `prettytable` | `>=3.10.0` | Table formatting output |
| `psutil` | `>=5.9.0` | System process monitoring |

## 🚀 Running the Program

```bash
# Launch the main program
python main.py
```

## 🛠️ Quick Start

### 🚀 Step 1️⃣: Environment Preparation

Ensure Python 3.7 or higher is installed:

```bash
# Check Python version
python --version

# If not installed, download from https://www.python.org/downloads/
```

### 📦 Step 2️⃣: Install Dependencies

```bash
# Navigate to project directory
cd DNS_Network_Tool

# Install all dependencies
pip install -r requirements.txt
```

### 🚀 Step 3️⃣: Launch the Tool

```bash
# Run the main program
python main.py
```

---

### 🎯 Basic Usage Scenarios

#### 🌐 Scenario 1: Test a Single Domain

```bash
# After starting the program, select from menu:
# 1. Domain Input and Test
# 2. Single Domain Input
# 3. Enter domain (e.g., google.com)
# 4. Program automatically performs DNS resolution and network testing
```

#### 📝 Scenario 2: Batch Test Multiple Domains

```bash
# Create domain list file domains.txt (one domain per line):
google.com
baidu.com
github.com
microsoft.com

# In the program, select:
# 1. Domain Input and Test
# 2. Batch Input
# 3. Import from File
# 4. Select domains.txt
```

#### ⚙️ Scenario 3: Configure Custom DNS Servers

```bash
# In the main menu, select:
# 2. Configure DNS Servers
# 1. Add New DNS Server
# Enter DNS server IP address (e.g., 114.114.114.114)
```

### Basic Usage Scenarios

#### Scenario 1: Test a Single Domain

After starting the program:
1. Select: Domain Input and Test
2. Select: Single Domain Input
3. Enter domain (e.g., `google.com`)
4. Program automatically performs DNS resolution and network testing

#### Scenario 2: Batch Test Multiple Domains

Create domain list file `domains.txt` (one domain per line):
```
google.com
baidu.com
github.com
microsoft.com
```

In the program:
1. Select: Domain Input and Test
2. Select: Batch Input
3. Select: Import from File
4. Select: domains.txt

#### Scenario 3: Configure Custom DNS Servers

In the main menu:
1. Select: Configure DNS Servers
2. Select: Add New DNS Server
3. Enter DNS server IP address (e.g., `114.114.114.114`)

### Detailed Operation Flow

#### Step 1: Launch the Program

```bash
$ python main.py
╔════════════════════════════════════════════════════════════╗
║                    DNS Network Tool                        ║
║         High-Performance DNS Resolution & Network Test     ║
╚════════════════════════════════════════════════════════════╝

    1. Domain Input and Test
    2. Configure DNS Servers
    3. Configure Test Parameters
    4. Enable/Disable Developer Mode
    5. Exit Program

Please enter option number [1-5]: _
```

#### Step 2: Select Test Function

Choose based on your needs:

- **Option 1**: Perform domain resolution and network testing
- **Option 2**: Manage DNS server list
- **Option 3**: Adjust test parameters
- **Option 4**: Enable developer mode for detailed logs
- **Option 5**: Safely exit the program

#### Step 3: Domain Input Method

Two input methods are supported:

**Single Domain Input**:
- Format: `domain` (e.g., `www.example.com`)
- Program validates domain format instantly
- Shows correction suggestions for format errors

**Batch Domain Input**:
- Method 1: Comma-separated (`google.com,baidu.com`)
- Method 2: Multi-line paste (one domain per line)
- Method 3: File import (`.txt` file, one domain per line)

#### Step 4: Select Resolution Mode

**Comprehensive Resolution Mode**:
- All domains resolved simultaneously
- Unified testing of all obtained IP addresses
- Suitable for comparing resolution results across different domains

**Sequential Resolution Mode**:
- Domains resolved one by one
- Separate network testing for each domain
- Suitable for detailed analysis of individual domains

#### Step 5: View Test Results

Multiple result display and export methods are supported:

**View DNS Resolution Results**:
- Display all resolved IP addresses
- Show resolution time and source DNS server
- IP geolocation information display supported

**View Network Test Results**:
- Ping test results (latency, packet loss, jitter)
- Speed test results (download/upload speed)
- Multiple sorting modes supported (latency-first, speed-first, balanced)

**Export Test Results**:
- Export as `.txt` format (table form)
- Export as `.csv` format (importable to Excel)
- Generate hosts file format and copy to clipboard

### Advanced Usage Tips

#### Batch Domain Testing

Create domain list file `domains.txt`:
```
# Popular domestic websites
baidu.com
taobao.com
jd.com
douyin.com

# Popular international websites
google.com
github.com
stackoverflow.com
```

Select batch input in the program and paste the domain list for batch testing.

#### Custom Test Parameters

In the main menu, select "Configure Test Parameters" to adjust:

| Parameter | Recommended Value | Description |
|-----------|------------------|-------------|
| Ping Count | 10-20 | Balance accuracy and test time |
| Ping Timeout | 1.5s | Adjust based on network environment |
| Speed Test Duration | 25s | Recommended 20-30s |
| Packet Size | 1024 bytes | Adjust as needed |
| Concurrent Connections | 12 | Adjust based on network bandwidth |
| DNS Resolution Timeout | 5s | Adjust based on DNS server response |

#### DNS Server Management

The program includes 200+ built-in public DNS servers, supporting:

- View current DNS server list
- Add custom DNS servers (IPv4/IPv6 supported)
- Delete less frequently used DNS servers
- Sort DNS servers by performance
- Set DNS server priority

#### Developer Mode

Enabling developer mode provides:

- Detailed debug logs
- Performance monitoring reports
- Code execution time statistics
- Suitable for troubleshooting and performance optimization

### Common Usage Questions

#### Q1: Program won't start?

**A:** Please check:
- Python version >= 3.7
- All dependencies installed (`pip install -r requirements.txt`)
- Correct working directory (containing `main.py`)
- Port conflicts (some features may use ports)

#### Q2: DNS resolution failed?

**A:** Possible causes and solutions:
- Network connection exception → Check network connection
- DNS server unavailable → Try different DNS servers
- Domain format error → Check domain format
- DNS resolution timeout → Increase DNS resolution timeout

#### Q3: Ping test failed?

**A:** Possible causes:
- Target IP blocks Ping (ICMP disabled)
- Firewall blocks ICMP requests
- Unstable network connection

**Solutions**:
- Try increasing Ping timeout
- Switch to other target IP for testing
- Check local firewall settings

#### Q4: Test results inaccurate?

**A:** Optimization suggestions:
- Increase test count and duration
- Test during low network load
- Take average of multiple tests
- Close other bandwidth-consuming programs

#### Q5: How to export hosts file?

**A:** After testing:
1. View network test results
2. Select "Generate Hosts File"
3. Program automatically copies to clipboard
4. Paste directly to `C:\Windows\System32\drivers\etc\hosts`

### Usage Examples

#### Example 1: Test Google Service Availability

```bash
# Start program
python main.py

# Select 1. Domain Input and Test
# Select single domain input
# Enter: google.com

# Program will automatically:
# 1. Resolve google.com IP addresses
# 2. Perform Ping tests on all IPs
# 3. Conduct speed tests
# 4. Display optimal IP recommendations
# 5. Generate hosts file format
```

#### Example 2: Batch Optimize Hosts File

```bash
# Create domains.txt with domains to optimize
google.com
github.com
raw.githubusercontent.com

# Start program
python main.py

# Select batch import domains.txt
# Program tests all domains
# Generate combined hosts file
# One-click copy to clipboard
```

#### Example 3: Test Custom DNS Servers

```bash
# Add Alibaba DNS
# In main menu select 2. Configure DNS Servers
# Select add new DNS server
# Enter: 223.5.5.5

# Add Tencent DNS
# Enter: 119.29.29.29

# Re-test domains and observe resolution speed changes
```

### Best Practices

1. **Regularly Update DNS Server List**: Remove slow servers, add new high-speed DNS
2. **Use Developer Mode for Troubleshooting**: When test results are abnormal, enable developer mode to view detailed logs
3. **Take Average of Multiple Tests**: For important scenarios, test multiple times and take the best result
4. **Set Test Parameters Reasonably**: Adjust parameters based on network environment, avoid overly long test times
5. **Backup Hosts File Regularly**: Backup original hosts file before modifying

### Technical Support

- **Issue Reporting**: https://github.com/DHA404/DNS_Network_Tool/issues
- **Feature Suggestions**: https://github.com/DHA404/DNS_Network_Tool/discussions

## Usage Guide

### Main Menu

```
1. Domain Input and Test
2. Configure DNS Servers
3. Configure Test Parameters
4. Enable/Disable Developer Mode
5. Exit Program
```

### Feature Description

#### 1. Domain Input and Test

Select this option to enter the domain testing flow:

1. **Select Input Method**
   - Single Domain Input
   - Batch Input (comma-separated or line-by-line paste)

2. **Select Resolution Mode**
   - Comprehensive Resolution: All domains resolved simultaneously, unified testing of all IPs
   - Sequential Resolution: Domains resolved one by one, tested separately

3. **Select IP Mode** (Comprehensive Resolution Mode only)
   - Unique IP Mode: All domains use the same optimal IP
   - Independent IP Mode: Each domain uses its own optimal IP

4. **View Results**
   - View DNS Resolution Results
   - View Network Test Results (Ping/Speed)
   - View Optimal IP List
   - Auto-generate hosts file and copy to clipboard

#### 2. Configure DNS Servers

Manage DNS server list:

- View current DNS server list
- Add new DNS server
- Delete existing DNS server
- DNS server performance sorting

#### 3. Configure Test Parameters

Adjust test-related parameters:

- Ping test count (1-100)
- Ping timeout (0.1-10s)
- Speed test duration (1-60s)
- Packet size (64-8192 bytes)
- Concurrent connections (1-20)
- DNS resolution threads (1-50)
- DNS resolution timeout (1-30s)
- Enable/disable IP geolocation query

#### 4. Enable/Disable Developer Mode

Toggle developer mode:

- Enable: Show detailed debug logs
- Disable: Show only basic information

#### 5. Exit Program

Safely exit program, generate performance report (if developer mode enabled).

### Batch Domain Testing Flow

1. Select "Domain Input and Test"
2. Select "Batch Input"
3. Select input method (file import or multi-line paste)
4. Wait for domain validation to complete
5. Select whether to perform network testing
6. View test results
7. Select whether to export results

## Configuration

### DNS Server Configuration

- **Add DNS Server**: Enter IP address to add new server
- **Delete DNS Server**: Remove server from list
- **View Server List**: Display all configured DNS servers
- **Performance Sorting**: Sort servers by response time

### Test Parameters Configuration

| Parameter | Range | Description |
|-----------|-------|-------------|
| ping_count | 1-100 | Number of Ping tests |
| ping_timeout | 0.1-10s | Ping response timeout |
| test_duration | 1-60s | Speed test duration |
| packet_size | 64-8192 bytes | Packet size |
| concurrent_connections | 1-20 | Concurrent connections |
| dns_threads | 1-50 | DNS resolution threads |
| dns_timeout | 1-30s | DNS resolution timeout |

## Configuration File

The program creates `config.json` on first run:

```json
{
  "dns_servers": [
    "8.8.8.8",
    "1.1.1.1",
    "9.9.9.9",
    "208.67.222.222",
    "4.2.2.1",
    "1.0.0.1",
    "8.8.4.4",
    "208.67.220.220",
    "84.200.69.80",
    "84.200.70.40"
  ],
  "test_params": {
    "ping_count": 7,
    "ping_timeout": 1.5,
    "test_duration": 25,
    "packet_size": 1024,
    "concurrent_connections": 12,
    "max_threads": 50,
    "dns_threads": 50,
    "dns_timeout": 5,
    "geo_query_enabled": true,
    "geo_query_threads": 50,
    "top_n_ips": 10,
    "speed_test_type": "tcp",
    "enable_ipv6": true,
    "output_format": "txt",
    "auto_save_results": false,
    "enable_download_test": true,
    "enable_upload_test": false,
    "speed_test_method": "both",
    "min_data_threshold": 1048576,
    "min_valid_data": 102400,
    "min_speed": 1.0
  },
  "log_level": "INFO",
  "web_interface": {
    "enabled": false,
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

### Configuration Details

#### DNS Server Configuration

- Supports IPv4 and IPv6 addresses
- Up to 200+ DNS servers supported
- Recommended to keep multiple backup servers

#### Test Parameters Configuration

- `ping_count`: Number of packets sent for Ping test
- `ping_timeout`: Timeout waiting for Ping response
- `test_duration`: Duration of speed test (seconds)
- `packet_size`: Packet size for testing (bytes)
- `concurrent_connections`: Concurrent connections for speed test
- `max_threads`: Maximum thread count
- `dns_threads`: DNS resolution thread count
- `dns_timeout`: DNS resolution timeout
- `geo_query_enabled`: Enable IP geolocation query
- `geo_query_threads`: Geolocation query thread count
- `top_n_ips`: Number of optimal IPs to return
- `speed_test_type`: Speed test type (tcp/udp/both)
- `enable_ipv6`: Enable IPv6 support
- `output_format`: Output format
- `auto_save_results`: Auto-save results
- `enable_download_test`: Enable download test
- `enable_upload_test`: Enable upload test
- `speed_test_method`: Speed test method
- `min_data_threshold`: Minimum data threshold (bytes)
- `min_valid_data`: Minimum valid data (bytes)
- `min_speed`: Minimum speed (Mbps)

#### Log Levels

- `DEBUG`: Detailed debug information
- `INFO`: General information
- `WARNING`: Warning information
- `ERROR`: Error information
- `CRITICAL`: Critical errors

## Log Files

The program logs to the `logs` directory:

- Log files named by date (e.g., `2026-01-06.log`)
- Each file max 10MB
- Automatic rotation, keeping last 7 log files
- Automatic cleanup of logs older than 7 days

## Tech Stack

- **Python 3.7+** - Primary development language
- **dnspython** - DNS resolution library
- **requests** - HTTP request library (for IP geolocation)
- **colorama** - Terminal color support
- **prettytable** - Table formatting output
- **psutil** - System process monitoring


## FAQ

### Q1: DNS resolution failed?

**A:** Please check:
- Network connection status
- DNS server availability
- Domain format correctness
- Try switching to other DNS servers

### Q2: Ping test failed?

**A:** Possible causes:
- Target IP doesn't support Ping (ICMP disabled)
- Firewall blocks ICMP requests
- Unstable network connection
- Try increasing ping_timeout parameter

### Q3: Speed test results inaccurate?

**A:** Suggestions:
- Increase test_duration parameter
- Test during low network load
- Take average of multiple tests
- Check for other programs占用带宽



### Q5: How to update configuration file?

**A:** Two methods:
1. **Manual Edit**: Directly modify `config.json`
2. **In-Program Config**: Use "Configure Test Parameters" option in menu

Requires program restart (except for parameters supporting hot reload).

### Q6: What is developer mode?

**A:** Developer mode provides:
- Detailed debug logs
- Performance monitoring reports
- Code execution time statistics
- Suitable for troubleshooting and optimization

### Q7: How to export test results?

**A:** Program supports multiple export methods:
- **TXT Format**: Table-formatted text report
- **CSV Format**: Comma-separated values, importable to Excel
- **Hosts File**: Auto-generated and copied to clipboard

### Q8: How to restore default configuration?

**A:** Select "Restore Default Configuration" in configuration menu, confirm to reset all settings to initial values.

## Architecture

### Overall Architecture

DNS Network Tool uses modular design with the following core modules:

- **Main Control Module** (`main.py`): Program entry point, coordinates all modules
- **DNS Resolution Module** (`dns_utils.py`): Implements DNS resolution with multi-server parallel queries
- **Network Testing Module** (`network_utils.py`): Provides Ping and speed test functionality
- **Configuration Module** (`config_utils.py`): Handles config file I/O and parameter management
- **Logging Module** (`log_utils.py`): Unified logging and management
- **Result Processing Module** (`result_utils.py`): Processes and exports test results
- **Terminal Module** (`terminal_utils.py`): Provides colorful terminal output and interactive interface
- **Session Management Module** (`session_manager.py`): Manages HTTP sessions and connection pool
- **Domain Analysis Module** (`domain_analyzer.py`): Analyzes domain and IP relationships
- **Performance Monitor Module** (`performance_monitor.py`): Monitors program performance metrics

### Core Design Patterns

#### 1. Factory Pattern
- `get_session_manager()`: Singleton pattern for HTTP session management
- `create_process_manager()`: Creates process manager instance

#### 2. Strategy Pattern
- Retry Strategy: Exponential backoff retry mechanism
- Timeout Strategy: Adaptive timeout manager
- Sorting Strategy: Multiple result sorting modes (latency-first, speed-first, balanced)

#### 3. Observer Pattern
- Event System: Supports plugin hook mechanism
- Logging System: Multi-level log output

### DNS Resolution Implementation

#### Intelligent DNS Server Selection
1. **Performance Monitoring**: Real-time monitoring of DNS server response times
2. **Circuit Breaker**: Protection for failed servers
3. **Load Balancing**: Dynamic query load distribution based on server performance
4. **Failover**: Automatic switch to backup DNS servers

#### Parallel Resolution Strategy
- Uses `concurrent.futures.ThreadPoolExecutor` for multi-thread parallel resolution
- Dynamic thread pool size adjustment based on system load
- Supports simultaneous A record and AAAA record queries

#### Adaptive Timeout Mechanism
- Dynamic timeout threshold adjustment based on historical response times
- Five levels: very_fast(0.8s), fast(1.2s), normal(2.0s), slow(3.5s), very_slow(5.0s)

### Network Testing Implementation

#### Ping Testing
- Prefers ICMP raw socket (requires admin privileges)
- Falls back to system ping command (cross-platform compatible)
- Supports IPv4 and IPv6 dual-stack testing

#### Speed Testing
- TCP/UDP protocol support
- Multi-server parallel testing
- Customizable packet size and test duration
- Real-time speed calculation and statistics

### Data Processing Flow

1. **Input Validation**: Domain format validation and preprocessing
2. **DNS Resolution**: Multi-server parallel resolution to get IP list
3. **IP Deduplication**: Merge identical IPs, count source servers
4. **Network Testing**: Ping and speed tests for each IP
5. **Result Sorting**: Sort results based on selected strategy
6. **Output Generation**: Generate tables, hosts files, or export files

## Performance

### Concurrency Handling

#### Thread Pool Management
- **Dynamic Adjustment**: Thread pool size adjusted based on CPU cores and system load
- **Load Balancing**: Calculate optimal thread count based on current system load
- **Resource Monitoring**: Real-time system resource monitoring to prevent overload

#### Asynchronous I/O
- **Non-blocking Operations**: Non-blocking I/O for improved concurrency
- **Event-driven**: Event-based asynchronous processing
- **Connection Reuse**: HTTP and TCP connection pool reuse

#### Batch Processing Optimization
- **Batch Domain Resolution**: Simultaneous DNS resolution requests to multiple servers
- **Batch IP Testing**: Parallel network testing of multiple IPs
- **Result Aggregation**: Efficient aggregation and processing of batch results

### Memory Optimization

#### Object Reuse
- **Object Pool Pattern**: Reuse frequently created network connection objects
- **Connection Pool Management**: HTTP and TCP connection reuse
- **Buffer Reuse**: Pre-allocated fixed-size buffers

#### Memory Management
- **Timely Release**: Ensure resource release to avoid memory leaks
- **GC Optimization**: Reasonable object lifecycle management
- **Caching Strategy**: Intelligent caching balance

### Algorithm Optimization

#### Sorting Algorithms
- **QuickSort**: Optimized sorting for large test result sets
- **Multi-dimensional Sorting**: Support for latency, speed, stability sorting
- **Partial Sorting**: Only fully sort Top N results

#### Search Algorithms
- **Hash Lookup**: O(1) complexity fast lookup using dictionaries and sets
- **Index Optimization**: Index for common queries
- **Deduplication**: Efficient IP deduplication and merging

#### Data Structure Optimization
- **Dictionary Optimization**: Efficient dictionary structure for DNS results
- **List Optimization**: Minimize unnecessary copy and move operations
- **Set Operations**: Efficient set operations for deduplication

### Network Performance Optimization

#### Connection Optimization
- **TCP Parameter Tuning**: Optimize TCP parameters
- **Connection Warmup**: Pre-establish common connections
- **Keep-Alive**: Long connections to reduce overhead

#### Protocol Optimization
- **HTTP/1.1 Optimization**: Connection reuse and pipelining
- **Request Merging**: Reduce network round trips
- **Compression**: Compressed transmission for large data

### System-Level Optimization

#### Resource Scheduling
- **CPU Affinity**: Thread-to-core binding optimization
- **I/O Scheduling**: Disk and network I/O optimization
- **Memory Allocation**: Optimize memory allocation strategy

#### Performance Monitoring
- **Real-time Monitoring**: Real-time performance metrics
- **Performance Analysis**: Built-in analysis tools
- **Optimization Suggestions**: Based on system configuration

## Error Handling

### Exception Architecture

#### Unified Exception Handling
- **Custom Exception Classes**: `DNSResolveException`, `NetworkTestException`, etc.
- **Exception Handler**: Unified `ExceptionHandler` class
- **Error Classification**: Classified handling and logging

#### Layered Exception Handling
- **Module-level**: Internal exception handling
- **Service-level**: Unified business exception handling
- **Application-level**: Uncaught exception handling

### Retry Mechanism

#### Exponential Backoff
- **Dynamic Retry**: Adjust retry interval based on error type and count
- **Max Retries**: Configurable maximum retry limit
- **Backoff Factor**: Exponential backoff factor of 2

#### Retry Strategies
- **Network Error Retry**: Network timeout, connection failures
- **DNS Error Retry**: DNS resolution timeouts
- **Smart Judgment**: Determine if retry needed based on error type

### Circuit Breaker Pattern

#### Circuit Mechanism
- **Failure Counting**: Track consecutive server failures
- **Circuit Threshold**: Auto-circuit when threshold reached
- **Half-Open State**: Periodic attempts to recover

#### Circuit Strategies
- **Fast Fail**: Quick failure for circuit-opened servers
- **Auto Recovery**: Periodic recovery attempts
- **Health Check**: Health checks for recovered servers

### Error Logging

#### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General program status
- **WARNING**: Potential issues
- **ERROR**: Errors without program crash
- **CRITICAL**: Severe errors causing exceptions

#### Log Content
- **Timestamp**: Millisecond-precision timestamps
- **Module Information**: Module and function where error occurred
- **Context Information**: Full context at error time
- **Stack Trace**: Complete stack trace information

### Common Exception Types

#### Network Exceptions
- **ConnectionError**: Network connection error, retry or switch servers
- **TimeoutError**: Network timeout, increase timeout or retry
- **ConnectionResetError**: Connection reset, reconnect
- **ConnectionRefusedError**: Connection refused, check server status

#### DNS Exceptions
- **Resolution Failure**: Try other DNS servers or fallback methods
- **Server Unresponsive**: Mark server as failed
- **Domain Format Error**: Validate and prompt user

#### System Exceptions
- **Insufficient Permissions**: Prompt for admin/root privileges
- **Insufficient Resources**: Reduce concurrency or release resources
- **System Call Failure**: Use fallback methods

## Advanced Usage

### Performance Tuning Parameters
- **Concurrent Connections**: Adjust based on network bandwidth
- **DNS Thread Count**: Adjust based on DNS server count
- **Test Duration**: Balance accuracy and execution time

### Batch Processing Tips
- **Domain List Format**: Support multiple formats
- **Result Filtering**: Filter optimal IPs by latency/speed
- **Automation**: Combine with shell scripts for automated testing

### Advanced Features
- **Developer Mode**: Enable detailed logs and monitoring
- **Custom DNS Servers**: Add private or high-performance servers
- **IPv6 Priority**: Configure IPv6-first resolution strategy

## Security

### Permission Requirements
- **ICMP Ping**: Admin privileges (Windows) or root (Linux/MacOS)
- **Raw Socket**: Special permissions for network operations

### Data Security
- **Privacy Protection**: No collection or upload of user data
- **Local Processing**: All processing done locally
- **Log Security**: Sensitive information not logged

### Network Security
- **Reasonable Usage**: Avoid excessive load on target servers
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **Compliant Testing**: Only test authorized domains and IPs

## License

MIT License

## Contributing

### Development Environment Setup
1. Clone project to local
2. Create virtual environment: `python -m venv .venv`
3. Activate virtual environment: `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`

### Code Standards
- Follow PEP 8 style guide
- Use type hints for code readability
- Write unit tests for code quality
- Run code checks before commit

### Contribution Process
1. Fork the project
2. Create feature branch
3. Submit changes
4. Create Pull Request

## Author

DNS Network Tool - High-Performance Domain Name Resolution & Network Testing Tool
