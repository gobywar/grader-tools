import json
import yaml
import os
import base64
import importlib.resources as resources
import subprocess
import time
from pathlib import Path
from jinja2 import Template
from .utils import extract_gradix


def _load_template(name: str) -> str:
    with resources.files("grader_tools.templates").joinpath(name).open("r", encoding="utf-8") as f:
        return f.read()


def render_grid_to_html(json_file: Path, out_file: Path = None, logo: Path = None):
    start_time = time.time()

    if out_file is None:
        out_file = json_file.with_suffix(".html")

    if logo:
        with open(logo, "rb") as image_file:
            base64_img = base64.b64encode(image_file.read()).decode('utf-8')
    else:
        base64_img = None

    data = json.loads(Path(json_file).read_text(encoding="utf-8"))
    data["base64_img"] = base64_img
    template_str = _load_template("grid.html")
    template = Template(template_str)
    out = template.render(data)
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    Path(out_file).write_text(out, encoding="utf-8")

    elapsed_time = time.time() - start_time
    print(f"✅ Grid converted: {json_file} → {out_file} in {elapsed_time:.2f} seconds")


def render_grid_to_pdf(json_file: Path, out_file: Path = None, logo: Path = None):
    start_time = time.time()
    
    if out_file is None:
        out_file = json_file.with_suffix(".pdf")
    
    data = json.loads(Path(json_file).read_text(encoding="utf-8"))
    data["logo"] = logo
    template_str = _load_template("grid.typ")
    template = Template(template_str)
    out = template.render(data)
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    Path("grid.typ").write_text(out, encoding="utf-8")

    # build command
    cmd = ["typst", "compile", "grid.typ", out_file]
    subprocess.run(cmd, check=True)

    elapsed_time = time.time() - start_time
    print(f"✅ Grid converted: {json_file} → {out_file} in {elapsed_time:.2f} seconds")


def render_gradix_to_pdf(grix_json_file: Path, logo: Path = None, final_max_score: float = 20):
    start_time = time.time()

    # Load the input JSON file
    with open(grix_json_file, 'r') as file:
        flat_data = json.load(file)

    scoresheets_by_exam = extract_gradix(flat_data)

    # Load the Typst template
    template_str = _load_template('feedback.typ')
    template = Template(template_str)

    # Create the main output directory
    main_directory = "assignments"
    os.makedirs(main_directory, exist_ok=True)

    # Generate a PDF for each scoresheet, including exam stats
    index = 0
    for exam_id, exam in scoresheets_by_exam.items():

        for scoresheet in exam["scoresheets"]:
            student_name = f'{scoresheet["student"]["firstName"]} {scoresheet["student"]["lastName"]}'
            student_directory = os.path.join(main_directory, f'{student_name}_{scoresheet["student"]["id"]}_assignsubmission_file_')
            os.makedirs(student_directory, exist_ok=True)

            # Render the template with both the scoresheet and exam stats
            typst_content = template.render(
                **scoresheet,
                exam_stats=exam["stats"],
                final_score = scoresheet["score"]*final_max_score/scoresheet["maxScore"],
                final_max_score=final_max_score,
                logo=logo 
            )

            typst_file_path = "scoresheet_temp.typ"
            pdf_file_path = os.path.join(student_directory, "scoresheet.pdf")

            # Write and compile the Typst file
            Path(typst_file_path).write_text(typst_content, encoding="utf-8")
            subprocess.run(['typst', 'compile', typst_file_path, pdf_file_path])
            print(f"- create {pdf_file_path} ({round(scoresheet["score"], 2)}/{scoresheet["maxScore"]})")
            index += 1

    elapsed_time = time.time() - start_time
    print(f"✅ {index} pdf exported in {elapsed_time:.2f} seconds")
