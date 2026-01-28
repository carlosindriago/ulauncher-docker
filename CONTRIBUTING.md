# Contributing

We welcome contributions! This project follows Git Flow methodology.

## 🌿 Git Flow Branching Model

### Branch Structure

- **`main`**: Production-ready stable releases
- **`develop`**: Integration branch for features and fixes
- **`feature/*`**: Short-lived branches for specific features
- **`bugfix/*`**: Short-lived branches for bug fixes

### Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/carlosindriago/ulauncher-docker-modernized.git
   cd ulauncher-docker-modernized
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Follow the coding standards
   - Add tests if applicable
   - Update documentation

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `security:` for security fixes
   - `docs:` for documentation
   - `refactor:` for code refactoring
   - `style:` for code style changes
   - `test:` for adding tests
   - `chore:` for maintenance tasks

5. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Submit a Pull Request**
   - Go to GitHub
   - Click "Pull Request"
   - Target branch: `develop`
   - Add clear description of your changes

### Important Notes

- **NEVER work directly on `develop`** - Always create feature branches
- **Target PRs to `develop`**, not `main`
- **Keep branches short-lived** - Delete feature branches after merge
- **Write clear commit messages** - Explain WHY, not just WHAT
- **Test before PR** - Ensure your changes work on multiple distributions

## 📋 Coding Standards

- Follow PEP 8 style guidelines
- Add type hints for new functions
- Include docstrings for complex logic
- Sanitize all user inputs (prevent injection attacks)
- Handle errors gracefully (don't crash extension)

## 🔒 Security Best Practices

This extension has been security-hardened. When contributing:

1. **Always sanitize user inputs** with `shlex.quote()` or similar
2. **Validate all inputs** with regex before using them
3. **Escape HTML** in notifications and UI text
4. **Use specific Docker exceptions** (e.g., `docker.errors.NotFound`)
5. **Don't expose sensitive data** in logs or error messages
6. **Limit string lengths** to prevent buffer overflows
7. **Never execute unsanitized commands** - Always validate first

## 🧪 Testing

Test your changes on:

- Ubuntu (latest LTS)
- Debian 12 / MX Linux (for XFCE4 support)
- At least 2 different terminal emulators
- Multiple Docker container states (running, stopped, crashed)

## 📝 Getting Help

- Open an issue with the `bug` label
- Use the `question` label for discussions
- Check existing issues before creating new ones
- Include detailed reproduction steps

Thank you for contributing! 🎉
