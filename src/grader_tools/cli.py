import typer
from pathlib import Path
import json
import yaml

app = typer.Typer(help="Grader Tools - utilities for criteria grids and exams",pretty_exceptions_enable=False)


@app.command()
def yaml_grid_to_json(
    yaml_file: Path = typer.Argument(..., help="YAML grid file"),
    json_file: Path = typer.Option(None, "--output", "-o", help="Output JSON file")
):
    """Convert YAML grid to JSON"""
    from .convert import yaml_grid_to_json as conv
    
    conv(yaml_file, json_file)


@app.command()
def json_grid_to_html(
    json_file: Path = typer.Argument(..., help="Input JSON file"),
    out_file: Path = typer.Option(None, "--output", "-o", help="Output HTML file"),
    logo_file: Path = typer.Option(None, "--logo", "-l", help="logo file")
):
    """Render JSON into HTML report"""
    from .render import render_grid_to_html
    render_grid_to_html(json_file, out_file, logo_file)


@app.command()
def json_grid_to_pdf(
    json_file: Path = typer.Argument(..., help="Input JSON file"),
    out_file: Path = typer.Option(None, "--output", "-o", help="Output Typst file"),
    logo_file: Path = typer.Option(None, "--logo", "-l", help="logo file")
):
    """Render JSON into Typst file"""
    from .render import render_grid_to_pdf
    render_grid_to_pdf(json_file, out_file, logo_file)


@app.command()
def latex_exam_to_json(
    latex_file: Path = typer.Argument(..., help="Input LaTeX exam file"),
    json_file: Path = typer.Option(None, "--output", "-o", help="Output JSON file")
):
    """Parse LaTeX exam into structured JSON"""
    from .convert import latex_latex_exam_to_json
    latex_latex_exam_to_json(latex_file, json_file)


@app.command()
def moodle_student_csv_to_json(
    csv_file: Path = typer.Argument(..., help="Input student CSV file"),
    json_file: Path = typer.Option(None, "--output", "-o", help="Output JSON file"),
):
    """Convert CSV to JSON"""
    from .convert import moodle_student_csv_to_json
    moodle_student_csv_to_json(csv_file, json_file)


@app.command()
def json_to_gradix(
    exam_json: Path = typer.Argument(..., help="exam JSON file"),
    student_json: Path = typer.Argument(..., help="student JSON file"),
    grid_json: Path = typer.Argument(..., help="grid JSON file"),
    output_json: Path = typer.Option("gradix.json", "--output", "-o", help="Output JSON file"),
):
    """Create GRADIX Json file from exam, student and grid json file"""
    from .convert import json_to_gradix
    json_to_gradix(exam_json, student_json, grid_json, output_json)


@app.command()
def gradix_to_pdf(
    grid_json: Path = typer.Argument(..., help="gridx JSON file"),
    logo_file: Path = typer.Option(None, "--logo", "-l", help="logo file"),
    final_max_score: float =  typer.Option(20, "--max_score", "-m", help="final max core")
):
    """Create PDF files from GRADIX json file"""
    from .render import render_gradix_to_pdf
    render_gradix_to_pdf(grid_json, logo_file, final_max_score)


if __name__ == "__main__":
    app()
