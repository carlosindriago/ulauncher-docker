<div align="center">

# 🐳 Ulauncher Docker Extension (Modernized)

[![Maintenance](https://img.shields.io/badge/Maintenance-Active-success.svg)](https://github.com/carlosindriago/ulauncher-docker)
[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://python.org)
[![Ulauncher](https://img.shields.io/badge/Ulauncher-v5-orange.svg)](https://ulauncher.io)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

**Manage your Docker containers from Ulauncher - Refactored for 2026**
*Maintained by Carlos Indriago*

</div>

---

## 📸 Demo

![Demo](https://github.com/carlosindriago/ulauncher-docker/blob/main/demo.gif)

The extension in action - listing containers, managing lifecycle, viewing logs, and more:

- **Quick Access**: Type `dk ` to instantly see all running containers
- **Lifecycle Management**: Start, stop, or restart containers directly from Ulauncher
- **Shell Access**: Open a terminal shell (`sh`) into any container with one click
- **Log Monitoring**: Tail logs in your preferred terminal
- **Network Info**: Copy container IP addresses to clipboard

---

## 🚀 Why this Fork? (Key Changes)

The original [brpaz/ulauncher-docker](https://github.com/brpaz/ulauncher-docker) repository has been unmaintained since 2019, with outdated dependencies and several issues preventing it from working on modern Linux distributions. This fork addresses those issues with significant technical improvements:

### Technical Improvements

- **Migration to Docker SDK 7.x+**
  - Upgraded from deprecated `docker~=5.0.3` to modern `docker>=7.0.0`
  - Full compatibility with Docker Engine API v1.45+
  - Maintains security and performance improvements from the latest Docker Python SDK

- **Expanded Terminal Support**
  - Added native support for **XFCE4 Terminal**, **Alacritty**, **Kitty**, **Konsole**, **Terminator**, and **XTerm**.
  - Auto-detects terminal type and applies correct flags (e.g., `-x` for XFCE/Terminator, `--` for Kitty, `-e` for others).

- **Robust Error Handling**
  - Extension no longer crashes if Docker Daemon is not running at startup
  - Graceful fallback with user-friendly notifications
  - Better error recovery and logging

- **Security Hardening**
  - Input sanitization to prevent command injection
  - Safe handling of notification text to prevent XSS-like issues
  - Regex validation for container IDs and names

---

## ✨ Features

- 📋 **List running containers** - View all active Docker containers with one command
- 🖥️ **Start/Stop/Restart** - Manage container lifecycle directly from Ulauncher
- 📜 **View logs** - Tail container logs in your preferred terminal
- 🐚 **Open shell** - Get instant shell access (`sh`) to any container
- 📋 **Copy IP/Ports** - Quick access to container networking information
- 🧹 **Prune system** - Cleanup unused containers and images
- 📚 **Documentation search** - Quick access to Docker docs
- 🎯 **Multi-terminal support** - Works with GNOME Terminal, Tilix, XFCE4 Terminal, Alacritty, Kitty, Konsole, Terminator, XTerm.

---

## 📋 Prerequisites

Before using this extension, ensure you have:

- **Ulauncher 5.0+** installed and running
- **Docker** installed and daemon running (`systemctl status docker`)
- **Python 3.x** with `pip` package manager
- **Docker permissions** for your user:

  ```bash
  # Add your user to the docker group
  sudo usermod -aG docker $USER
  
  # Log out and back in for changes to take effect
  ```

---

## 🛠️ Installation

### 1. Clone the Repository

```bash
cd ~/.local/share/ulauncher/extensions/
git clone https://github.com/carlosindriago/ulauncher-docker.git com.github.brpaz.ulauncher-docker
```

### 2. Install Python Dependencies

```bash
cd ~/.local/share/ulauncher/extensions/com.github.brpaz.ulauncher-docker

# For standard systems:
pip3 install -r requirements.txt

# ⚠️ For Debian 12 / MX Linux / Ubuntu 24.04+ (if you get "externally-managed-environment" error):
pip3 install -r requirements.txt --break-system-packages
```

### 3. Restart Ulauncher

```bash
killall ulauncher
ulauncher -v
```

### Verify Installation

Open Ulauncher and type `dk ` (with trailing space). You should see a list of running containers.

---

## ⚙️ Configuration

### Select Your Terminal

The extension supports multiple terminals. To change it:

1. Open Ulauncher Preferences (`Ctrl+Alt+Space`, then Preferences)
2. Go to **Extensions** tab
3. Find **Docker** extension
4. Set **Default Terminal** to your preference:

| Terminal | Value | Notes |
|----------|--------|--------|
| GNOME Terminal | `gnome-terminal` | Default on Ubuntu/Fedora |
| Tilix | `tilix` | Modern terminal emulator |
| XFCE4 Terminal | `xfce4-terminal` | Uses `-x` flag |
| Alacritty | `alacritty` | Uses `-e` flag |
| Kitty | `kitty` | Uses `--` flag |
| Konsole | `konsole` | KDE Terminal |
| Terminator | `terminator` | Uses `-x` flag |
| XTerm | `xterm` | Classic terminal |

---

## 💻 Usage

Open Ulauncher and type one of the following commands:

### Basic Commands

| Command | Description |
|----------|-------------|
| `dk ` (with space) | List all running Docker containers |
| `dk:info ` | Show Docker Daemon version and system info |
| `dk:prune ` | Cleanup unused containers, networks, and images |
| `dk:docs ` | Search Docker documentation |

### Container Actions

When you select a container from the list:

- **Enter** - View container details (IP, ports, status)
- **Start** - Start a stopped container
- **Stop** - Stop a running container
- **Restart** - Restart container (graceful)
- **Open Shell** - Open a new terminal with `docker exec -it <id> sh`
- **View Logs** - Open terminal with `docker logs -f <id>`
- **Copy IP** - Copy container IP address to clipboard

> **Tip:** Pressing `Space` after `dk` is required to activate the extension. Without it, Ulauncher shows general search results.

---

## 🤝 How to Contribute

We welcome contributions from the community! This is an open-source project maintained by volunteers.

### Areas Where We Need Help

- **Bug Reports**: If you find issues on your specific distribution, please file a bug report with:
  - Linux distribution and version (`cat /etc/os-release`)
  - Ulauncher version (`ulauncher --version`)
  - Terminal you're using
  - Steps to reproduce

- **Code Improvements**: Feel free to submit pull requests for:
  - New container actions
  - UI enhancements
  - Performance optimizations
  - Additional Docker features (compose, swarm, etc.)

### Contribution Workflow

1. **Fork** this repository
2. **Create a branch** for your feature/fix (`git checkout -b feature/my-feature`)
3. **Commit** your changes (`git commit -m 'Add my feature'`)
4. **Push** to your fork (`git push origin feature/my-feature`)
5. **Open a Pull Request** with a clear description of your changes

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Credits

- **Original Author**: [Bruno Paz](https://github.com/brpaz) - Created the original `ulauncher-docker` extension (2019)
- **Current Maintainer**: [Carlos Indriago](https://github.com/carlosindriago) - Modern fork maintainer (2026)
- **Community**: All contributors who improve this extension

---

## 🙏 Acknowledgments

- The [Ulauncher](https://ulauncher.io/) team for the excellent launcher platform
- [Docker](https://www.docker.com/) for the containerization technology
- Original `ulauncher-docker` contributors for the foundational work

---

## 📞 Support

If you encounter issues:

1. Check out **Usage** section for proper command syntax
2. Verify Docker is running: `systemctl status docker`
3. Verify user permissions: `groups $USER` (should include `docker`)
4. Check Ulauncher logs: `ulauncher -v` and look for extension errors
5. [Open an issue](https://github.com/carlosindriago/ulauncher-docker/issues) with details

---

*Last updated: January 2026*  
*Maintained with ❤️ by [Carlos Indriago](https://github.com/carlosindriago)*
