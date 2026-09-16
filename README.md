# PDF Text Search

A GUI application ([Flask](https://flask.palletsprojects.com/) + [pywebview](https://pywebview.flowrl.com/))  that searches for a term across all PDFs in a folder (including subfolders), displays the matching documents, and opens a PDF directly to the relevant page.

## Download
 
Prebuilt versions are available on the [Releases page](https://github.com/thomas-brl/pdf-text-search/releases/latest)

- **Windows x64:** Download `pdf-search-vX-win-x64.exe` and double-click it to run the application.

- **macOS arm64:** Download `pdf-search-vX-macos-arm64.zip`, extract the archive, and open the application inside.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/thomas-brl/pdf-text-search.git
```

2. Navigate to the app directory:

```bash
cd pdf-search
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python pdf_search.py
```

Then choose the folder containing the PDF files and enter the text you want to search for.

## Features

- Recursively searches for text across all PDFs in a folder.
- Groups results by document, with a list of the pages containing the searched term.
- Opens a document directly in the application at the relevant page.

## Requirements

- Python 3.9+
- Flask
- PDFplumber
- PyWebView

## Limitations

This tool searches text that can be extracted from PDFs. Scanned PDFs or PDFs containing images of text may require OCR before they can be searched.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
