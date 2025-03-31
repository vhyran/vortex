# Vortex: A Lightweight MySQL Client-Compatible Database

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Alpha-yellow.svg)

Vortex is a lightweight, MySQL client-compatible database implemented entirely in Python. It provides an embeddable SQL engine designed for structured data management, offering developers a flexible alternative to traditional database systems without the overhead of external dependencies.

## Key Features

- **MySQL Client Compatibility**: Works with existing MySQL client libraries and tools
- **Pure Python**: No external database engine required
- **Lightweight**: Minimal resource footprint, ideal for embedded applications
- **Flexible**: Fine-grained control over data management
- **Embeddable**: Easily integrate into Python projects
- **SQL Support**: Implements core SQL functionality compatible with MySQL syntax

## Installation

You can install Vortex via pip:

```bash
pip install vortex
```

Or, to install from source:

```bash
git clone https://github.com/vhyran/vortex.git
cd vortex
pip install .
```

For development:
```bash
pip install -e .[dev]
```

## Requirements

- Python 3.8 or higher
- `sqlparse>=0.4.4`
- `anyio>=3.5.0`

## Quick Start

```python
from vortex import Vortex

# Initialize the database
db = Vortex()

# Execute MySQL-compatible queries
db.execute("CREATE TABLE users (id INT, name VARCHAR(255))")
db.execute("INSERT INTO users (id, name) VALUES (1, 'Alice')")

# Query data
results = db.execute("SELECT * FROM users")
print(results)
```

## Usage Examples

### Connecting with MySQL Clients
Vortex can be used with standard MySQL client libraries:

```python
import mysql.connector

# Connect using MySQL connector
conn = mysql.connector.connect(
    host="localhost",
    user="vortex_user",
    password="",
    database="vortex_db"
)

cursor = conn.cursor()
cursor.execute("SHOW TABLES")
print(cursor.fetchall())
```

### CLI Usage
If implemented, use the command-line interface:

```bash
vortex --help
```

## Project Structure

```
vortex/
├── src/
│   ├── __init__.py
│   ├── vortex.py
│   └── # other implementation files
├── setup.py
└── README.md
```

## Development

To contribute or modify Vortex:

1. Clone the repository:
```bash
git clone https://github.com/vhyran/vortex.git
cd vortex
```

2. Install development dependencies:
```bash
pip install -e .[dev]
```

3. Run tests:
```bash
pytest
```

## Status

Vortex is currently in **Alpha** stage. Features and APIs may change as development progresses.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details (TBD).

## License

Vortex is released under the [MIT License](LICENSE).

---

Built with ❤️ by vhyran for developers who need a simple, embeddable database solution.
