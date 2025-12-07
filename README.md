# py-clash-bot

**py-clash-bot** is an open-source automation tool that allows you to automate your Clash Royale gameplay on Windows using BlueStacks 5 emulator. The bot uses advanced image recognition, mouse control, and Android emulation to perform a comprehensive range of tasks automatically.

_Join our [Discord server](https://discord.gg/nqKRkyq2UU) for support, updates, and community discussions!_

## ✨ Features

### 🎮 **Battle Automation**

- **Trophy Road 1v1 Battles** - Automatically fight in trophy road ladder matches
- **Path of Legends 1v1 Battles** - Battle in the competitive Path of Legends mode
- **2v2 Battles** - Team up with clan members for 2v2 matches
- **Random Decks** - Randomize your deck selection before each battle
- **Smart Battle Management** - Skip fights when chests are full, disable win/loss tracking

### 🎯 **Battle Strategies**

- **Elixir Management** - Choose between Conservative, Balanced, Aggressive, or Adaptive elixir strategies
- **Push Strategies** - Configure Single Lane, Dual Lane, Counter Push, or Adaptive push tactics
- **Aggression Levels** - Set timing from Defensive to Very Aggressive for different play styles
- **Smart Phase Adaptation** - Automatically adjusts strategy based on battle phase (early/single/double/triple elixir)
- **[Learn More](BATTLE_STRATEGY.md)** - See full documentation with recommended deck combinations

### 🎁 **Rewards & Collection**

- **Card Mastery Rewards** - Collect mastery rewards earned from battles
- **Card Upgrades** - Upgrade your current deck after each battle

### ⚙️ **Settings**

- **BlueStacks 5 Support** - Optimized for BlueStacks 5 emulator with auto-instance management
- **Render Mode Selection** - Choose between OpenGL, DirectX, and Vulkan rendering
- **Real-time Statistics** - Track wins, losses, chests opened, and more
- **Modern UI** - Clean, themed interface with customizable appearance

### 🤖 **AI/ML Model Integration** (Optional)

- **Roboflow Integration** - Enhance card detection with custom ML models
- **Easy Configuration** - Simple setup with API keys and model IDs
- **[Learn More](pyclashbot/detection/README_MODELS.md)** - See documentation for setup

## 🚀 Setup Instructions

### BlueStacks 5 Setup

1. **Download BlueStacks 5** - Get it from https://www.bluestacks.com (ensure BlueStacks 5, not X/10)
2. **Install BlueStacks 5** - Run the BlueStacks 5 installer
3. **Download py-clash-bot** - Get the latest release from [GitHub Releases](https://github.com/pyclashbot/py-clash-bot/releases)
4. **Install py-clash-bot** - Run the installer
5. **Create the instance** - Start the bot, select a render mode (DirectX recommended) and click "Start". The bot will automatically create the "pyclashbot-96" BlueStacks instance
6. **Install Clash Royale** - Install Clash Royale manually on the "pyclashbot-96" emulator via Google Play Store
7. **Complete setup** - Open Clash Royale manually, complete the tutorial, and optionally sign in to your account
8. **Close BlueStacks 5** - Fully close the BlueStacks 5 emulator
9. **Start automation** - Start the bot, select your settings, then click "Start"

### Important Notes

- **Language Setting** - Ensure Clash Royale is set to English for optimal bot performance
- **Tutorial Completion** - The tutorial must be completed manually before starting the bot
- **Account Setup** - Sign in with SuperCell ID or create a new account as needed

## 🔧 Troubleshooting

### BlueStacks 5 Issues

- **Use BlueStacks 5 only** - BlueStacks 10/X are not supported
- **Check installation** - Ensure install path exists: `C:\Program Files\BlueStacks_nxt`
- **Create fresh instance** - If startup fails, create a clean "Pie 64-bit (Android 9)" instance in Multi-Instance Manager, then click Retry in the bot
- **Switch render mode** - Try DirectX, OpenGL, or Vulkan if you see black screens
- **Restart** - Fully close BlueStacks if it becomes unresponsive; the bot will relaunch it

### Common Solutions

- **Black screen** - Switch render mode in the BlueStacks tab
- **Bot not detecting game** - Make sure Clash Royale is set to English
- **Instance not found** - Let the bot create a fresh "pyclashbot-96" instance

## 🎯 Demo

<img src="https://github.com/pyclashbot/py-clash-bot/blob/master/assets/demo-game.gif?raw=true" width="50%" alt="Game Demo"/><img src="https://github.com/pyclashbot/py-clash-bot/blob/master/assets/demo-gui.gif?raw=true" width="50%" alt="GUI Demo"/>

_Left: Bot automation in action | Right: User interface and controls_

## 🤝 Contributing

We welcome contributions from the community! Whether you have ideas for new features, bug reports, or want to help with development:

- **Report Issues** - Open an issue on [GitHub Issues](https://github.com/pyclashbot/py-clash-bot/issues)
- **Feature Requests** - Suggest new automation features or improvements
- **Code Contributions** - Check out our [Contributing Guide](CONTRIBUTING.md)
- **Community Support** - Help other users on our [Discord server](https://discord.gg/nqKRkyq2UU)

## ⚠️ Disclaimer

This tool is designed for educational and automation purposes. Please ensure you comply with Clash Royale's Terms of Service and use responsibly.

---

**Made with ❤️ by the py-clash-bot community**

_Automate your Clash Royale experience and focus on what matters most - strategy and fun!_
