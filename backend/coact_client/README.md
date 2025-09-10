# Coact Desktop Client

🤖 **Production-ready desktop agent for automated task execution**

Coact Client is a secure, scalable desktop automation agent that connects to the Coact platform to execute tasks on real user devices. Built with Python, it provides comprehensive automation capabilities including screen interaction, file management, shell command execution, and more.

## ✨ Features

### 🔐 **Security First**
- Encrypted credential storage using Fernet encryption
- JWT-based authentication with automatic token refresh
- Device enrollment with rotating security tokens
- Configurable security policies and whitelisting
- Safe shell command execution with blacklisting

### 🚀 **Production Ready**
- Automatic WebSocket reconnection with exponential backoff
- Structured logging with file rotation and remote logging
- Performance monitoring and metrics collection
- Graceful error handling and recovery
- Resource usage monitoring

### 🎯 **Comprehensive Automation**
- **Screen Interaction**: Screenshots, mouse clicks, keyboard input, scrolling
- **File Operations**: Upload/download with presigned URLs
- **Shell Commands**: Secure command execution with safety checks  
- **Cross-Platform**: Windows, macOS, and Linux support
- **Artifact Management**: Automatic upload of screenshots, logs, and files

### 📊 **Monitoring & Observability**
- Real-time performance metrics
- Structured JSON logging
- Remote log aggregation
- Connection state monitoring
- Task execution tracking

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/coact/coact-client
cd coact-client

# Install dependencies
pip install -e .

# Or install from PyPI (when available)
pip install coact-client
```

### Initial Setup

1. **Login to your Coact account:**
```bash
coact login
# Enter your email and password
```

2. **Enroll your device:**
```bash
coact enroll
```

3. **Start the client:**
```bash
coact start
```

### Basic Usage

```bash
# Check status
coact status

# View configuration
coact config

# Monitor performance
coact metrics

# Reset device (if needed)
coact reset
```

## 🔧 Configuration

The client uses environment variables and configuration files for customization:

### Environment Variables

```bash
# Server Configuration
export COACT_SERVER__API_URL="https://api.coact.dev"
export COACT_SERVER__WS_URL="wss://api.coact.dev"

# Security Settings
export COACT_SECURITY__ENABLE_SHELL_COMMANDS="false"
export COACT_SECURITY__REQUIRE_TASK_CONFIRMATION="true"

# Device Settings
export COACT_DEVICE__NAME="my-workstation"
export COACT_DEVICE__MAX_CONCURRENT_TASKS="3"
```

### Configuration File

Create `~/.config/coact-client/config.yaml`:

```yaml
server:
  api_url: "https://api.coact.dev"
  ws_url: "wss://api.coact.dev"
  timeout: 30

device:
  name: "my-workstation"
  platform: "linux"
  max_concurrent_tasks: 3
  capabilities:
    screen_capture: true
    mouse_control: true
    keyboard_control: true
    shell_access: false

security:
  require_task_confirmation: true
  enable_shell_commands: false
  max_file_size_mb: 100
  allowed_file_extensions:
    - ".txt"
    - ".log"
    - ".png"
    - ".jpg"

logging:
  level: "INFO"
  enable_remote_logging: true
  max_file_size_mb: 50
```

## 🎯 Supported Actions

The client supports the following task actions:

### Screen Actions
- `screenshot` - Capture screen or regions
- `click` - Mouse clicks at coordinates
- `type` - Keyboard text input
- `key` - Keyboard key combinations
- `scroll` - Mouse wheel scrolling
- `move_mouse` - Cursor movement

### System Actions  
- `shell` - Execute shell commands (if enabled)
- `system_info` - Gather system information

### File Actions
- `upload_artifact` - Upload files to server
- `upload_screenshot` - Capture and upload screenshots
- `upload_log` - Upload application logs

## 🛡️ Security

### Authentication
- JWT tokens with automatic refresh
- Encrypted credential storage
- Device-specific security tokens

### Command Execution
- Shell command blacklisting
- Whitelisting for allowed commands
- Configurable security policies
- Safe execution environments

### Network Security
- TLS/SSL for all connections
- Certificate verification
- Secure WebSocket connections

## 📊 Monitoring

### Performance Metrics
```bash
coact metrics
```

Shows:
- Task execution times
- WebSocket connection status
- Message processing rates
- Error frequencies

### Logging
- Structured JSON logs in production
- Configurable log levels
- Automatic log rotation
- Optional remote log shipping

### Health Checks
```bash
coact status
```

Displays:
- Authentication status
- Device enrollment status
- WebSocket connection state
- Active task count

## 🔄 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Interface │    │   Main App       │    │  Task Engine    │
│                 │    │                  │    │                 │
│  • login        │───▶│  • Lifecycle     │───▶│  • Execution    │
│  • enroll       │    │  • Coordination  │    │  • Results      │
│  • start/stop   │    │  • Error Handling│    │  • Monitoring   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
         ┌──────────▼──┐  ┌─────▼─────┐  ┌─▼─────────┐
         │   Auth      │  │ WebSocket │  │  Device   │
         │   Client    │  │  Client   │  │  Manager  │
         │             │  │           │  │           │
         │ • JWT Mgmt  │  │ • Real-time│  │ • Enrollment│
         │ • Refresh   │  │ • Reconnect│  │ • Token Mgmt│
         │ • Storage   │  │ • Messages │  │ • Info      │
         └─────────────┘  └───────────┘  └───────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
         ┌──────────▼──┐  ┌─────▼─────┐  ┌─▼─────────┐
         │   Screen    │  │   Shell   │  │ Artifacts │
         │   Module    │  │   Module  │  │  Module   │
         │             │  │           │  │           │
         │ • Screenshots│ │ • Commands│  │ • Uploads │
         │ • Clicks     │  │ • Safety  │  │ • Presign │
         │ • Keyboard   │  │ • Whitelist│  │ • Validation│
         └─────────────┘  └───────────┘  └───────────┘
```

## 🧪 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/coact/coact-client
cd coact-client

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black coact_client/
ruff check coact_client/

# Type checking
mypy coact_client/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=coact_client

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

## 📝 API Reference

### CLI Commands

| Command | Description |
|---------|-------------|
| `coact login` | Authenticate with Coact platform |
| `coact logout` | Clear stored credentials |
| `coact enroll` | Register device with server |
| `coact start` | Start the client daemon |
| `coact status` | Show client status |
| `coact metrics` | Display performance metrics |
| `coact config` | Show configuration |
| `coact reset` | Clear client data |
| `coact version` | Show version info |

### Configuration Options

See the [Configuration](#-configuration) section for detailed settings.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 Email: support@coact.dev
- 💬 Discord: [Coact Community](https://discord.gg/coact)
- 📖 Documentation: [docs.coact.dev](https://docs.coact.dev)
- 🐛 Bug Reports: [GitHub Issues](https://github.com/coact/coact-client/issues)

## 🚀 Roadmap

- [ ] **GUI Application** - Desktop GUI interface
- [ ] **Plugin System** - Custom action plugins
- [ ] **Docker Support** - Containerized deployment
- [ ] **Cloud Deployment** - Cloud instance management
- [ ] **Advanced Security** - Hardware security module integration
- [ ] **Machine Learning** - Intelligent task optimization

---

**Built with ❤️ by the Coact Team**