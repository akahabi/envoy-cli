# envoy-cli

> A CLI tool for managing and syncing `.env` files across local, staging, and production environments with encrypted storage.

---

## Installation

```bash
pip install envoy-cli
```

Or install from source:

```bash
git clone https://github.com/yourname/envoy-cli.git && cd envoy-cli && pip install .
```

---

## Usage

Initialize envoy in your project:

```bash
envoy init
```

Push your local `.env` to a remote environment:

```bash
envoy push --env staging
```

Pull the latest `.env` from production:

```bash
envoy pull --env production
```

List all tracked environments:

```bash
envoy list
```

All secrets are encrypted at rest using AES-256. Access is controlled via API keys configured during `envoy init`.

---

## Commands

| Command | Description |
|---|---|
| `envoy init` | Initialize envoy in the current project |
| `envoy push` | Encrypt and upload `.env` to a target environment |
| `envoy pull` | Download and decrypt `.env` from a target environment |
| `envoy diff` | Show differences between local and remote `.env` |
| `envoy list` | List all configured environments |

---

## Requirements

- Python 3.8+
- An active envoy account or self-hosted backend

---

## License

[MIT](LICENSE) © 2024 yourname