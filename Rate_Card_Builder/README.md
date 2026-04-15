# Rate Card Builder

A standalone GUI application for creating and managing rate cards in the Automation Suite.

## Features

- **Modern UI**: Built with customtkinter for a sleek, modern interface
- **Standalone**: Runs independently for thorough testing before integration
- **Extensible**: Modular design ready for integration into One Stop Shop

## Project Structure

```
Rate_Card_Builder/
├── __init__.py                    # Package initialization
├── rate_card_builder_main.py      # Main GUI application
├── README.md                      # This file
├── requirements.txt              # Python dependencies
└── [Additional modules to be added]
```

## Requirements

- Python 3.8+
- customtkinter
- tkinter (included with Python)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python rate_card_builder_main.py
```

## Development Roadmap

### Phase 1: GUI Framework (Current)
- [x] Main window with customtkinter
- [x] "Create a new rate card" button
- [ ] Additional UI components

### Phase 2: Core Functionality
- [ ] Rate card creation workflow
- [ ] Data input forms
- [ ] Validation logic

### Phase 3: Testing & Refinement
- [ ] Unit tests
- [ ] Integration tests
- [ ] User acceptance testing

### Phase 4: Integration
- [ ] Integration with One Stop Shop
- [ ] Configuration management
- [ ] Data persistence

## License

Part of the Automation Suite
