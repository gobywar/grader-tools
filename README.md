# grader-tools

**Grader Tools** is a command-line utility to help educators and examiners manage **criteria grids** and **exams**.  
It provides tools to convert between formats (YAML, JSON, CSV, LaTeX), generate reports (HTML, PDF), and integrate with grading platforms.

## Installation

Clone and install directly from GitHub:

```bash
pip install git+https://github.com/vincentchoqueuse/grader-tools.git
```

> ⚠️ PDF generation requires [Typst](https://typst.app/) installed on your system.

## Usage

```bash
grader-tools [OPTIONS] COMMAND [ARGS]...
```

### Global Options

- `--install-completion` → Install completion for the current shell
- `--show-completion` → Show completion for the current shell
- `--help` → Show this message and exit

## Available Commands

| Command                      | Description                                                          |
| ---------------------------- | -------------------------------------------------------------------- |
| `yaml-grid-to-json`          | Convert **YAML grid** into **JSON**                                  |
| `json-grid-to-html`          | Render a **JSON grid** into an **HTML report**                       |
| `json-grid-to-pdf`           | Render a **JSON grid** into a **Typst PDF report**                   |
| `latex-exam-to-json`         | Parse a **LaTeX exam** into structured **JSON**                      |
| `moodle-student-csv-to-json` | Convert **Moodle CSV export** to **JSON**                            |
| `json-to-gradix`             | Merge exam, student, and grid JSON files into a **GRADIX JSON** file |
| `gradix-to-pdf`              | Generate **PDF reports** from a **GRADIX JSON** file                 |

---

## Example Workflows

### Convert a YAML grid into JSON

```bash
grader-tools yaml-grid-to-json grid.yaml
```

### Generate an HTML report from a JSON grid

```bash
grader-tools json-grid-to-html grid.json -o index.html
```

### Generate a PDF from a JSON grid

```bash
grader-tools json-grid-to-pdf grid.json -o report.pdf
```

### Parse a LaTeX exam into JSON

```bash
grader-tools latex-exam-to-json exam.tex
```

### Convert Moodle CSV export to JSON

```bash
grader-tools moodle-student-csv-to-json students.csv
```

### Merge exam, student, and grid JSON into GRADIX

```bash
grader-tools json-to-gradix exam.json students.json grid.json
```

### Generate PDFs from GRADIX JSON

```bash
grader-tools gradix-to-pdf gradix.json
```

## Requirements

- [Python 3.8+](https://www.python.org/)
- [Typst](https://typst.app/) (for PDF generation)

## License

MIT License. See [LICENSE](./LICENSE) for details.
