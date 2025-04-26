# AuCoffre Scraper

A Python tool to retrieve product listings from **AuCoffre.com**, extract the **premium** (percentage) and detect the **LSP** label, then send an alert via **Pushover** if specified conditions are met.

---

## Features

- 💻 Download the target page with a custom User-Agent header.
- 📄 Save both the raw HTML content and a prettified version:
  - `page_content_raw.html`
  - `page_content_formatted.html`
- 🔍 Extract the **premium** (%) from HTML elements.
- 🏷️ Check for the presence of the **LSP** label.
- 🔔 Send alerts via Pushover when the premium is less than or equal to 5% and the product has the LSP label.
- 🗒️ Detailed logging with **Loguru** in `aucoffre.log`.

## Prerequisites

- Python 3.8 or higher
- [pip](https://pip.pypa.io/) (or another Python package manager)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/aucoffre-scraper.git
cd aucoffre-scraper
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

1. Duplicate the example file `.env.example` or create a new `.env` file in the project root.
2. Add your Pushover credentials:

```ini
PUSHOVER_TOKEN=your_pushover_token
PUSHOVER_USER=your_pushover_user
```

## Usage

Run the main script. By default, it targets AuCoffre’s product page:

```bash
python main.py
```

To use a different URL:

```bash
python main.py "https://your-target-site.com"
```

## Generated Files

- `page_content_raw.html` – Raw HTML of the fetched page.
- `page_content_formatted.html` – The same content, prettified.
- `aucoffre.log` – Execution log with info, error, and success messages.

## Customization

- Adjust thresholds or logic in `main.py` as needed:
- Premium threshold (default: 5%)
- Presence of the LSP label

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push to your branch (`git push origin feature/my-feature`)
5. Open a pull request

## License

This project is licensed under the MIT License. 

