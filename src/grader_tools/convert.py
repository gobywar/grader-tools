import argparse
import yaml
import json
import re
import csv
from pathlib import Path
from .utils import build_gradix_dict


LEVELS_ORDER = [
    {"label": "Au delà des attentes", "order": 5, "color": "#06D6A0", "critical": False},
    {"label": "Bien", "order": 4, "color": "#06D6A0", "critical": False},
    {"label": "Passable", "order": 3, "color": "#FFD166", "critical": False},
    {"label": "Insuffisant", "order": 2, "color": "#FF6B6B", "critical": False},
    {"label": "Très insuffisant", "order": 1, "color": "#FF6B6B", "critical": False},
    {"label": "Rédhibitoire", "order": 0, "color": "#2E2E2E", "critical": True}
]

def split_full_name(full_name: str):
    """Split a string like 'Firstname(s) LASTNAME(S)' into (firstName, lastName)."""
    parts = full_name.strip().split()
    first_names = [p for p in parts if not p.isupper()]
    last_names = [p for p in parts if p.isupper()]
    return " ".join(first_names), " ".join(last_names)


def parse_latex_questions(tex_content: str):
    """
    Parse LaTeX exam content into a structured JSON-compatible dict.
    Extracts sections, questions, and metadata.
    """
    sections = []
    id_section, id_question = 1, 1

    # Parse metadata (newcommand definitions)
    meta = {}
    for match in re.finditer(r'\\newcommand\{\\(\w+)\}\{(.*?)\}', tex_content):
        meta[match.group(1)] = match.group(2).strip()

    # Split into sections
    split_sections = re.split(r'\\section\{(.+?)\}', tex_content)
    max_score_exam = 0

    for i in range(1, len(split_sections), 2):
        title, content = split_sections[i], split_sections[i + 1]
        questions = []
        max_score = 0

        # Extract questions inside each section
        for match in re.finditer(
            r'\\begin\{question\}.*?\[(?P<points>[0-9\.]+)\]\{(?P<aav>[^\}]+)\}\{(?P<crit>[^\}]+)\}'
            r'(?P<text>.*?)\\end\{question\}',
            content,
            re.S
        ):
            points = float(match.group("points"))
            aav = match.group("aav").strip().lower()
            crit = match.group("crit").strip().lower()
            description = " ".join(line.strip() for line in match.group("text").splitlines()).strip()

            questions.append({
                "id": f"q{id_question}",
                "maxScore": points,
                "outcomeId": aav,
                "criterionId": f"{aav}_{crit}",
                "text": description
            })

            id_question += 1
            max_score += points

        sections.append({
            "id": f"s{id_section}",
            "text": title.strip(),
            "maxScore": max_score,
            "questions": questions
        })

        id_section += 1
        max_score_exam += max_score

    return {
        "id": "e1",
        "meta": meta,
        "maxScore": max_score_exam,
        "normalizedScore": 20,
        "sections": sections
    }


def preprocess_yaml_back(data):
    """
    Normalize YAML rubric definition:
    - Preserve top-level metadata (course, semester, teachers, year)
    - Add IDs to outcomes (modules) and criteria
    - Normalize and order levels according to LEVELS_ORDER
    """

    # Extract metadata (leave them unchanged if present)
    metadata = {
        "course": data.get("course"),
        "semester": data.get("semester"),
        "teachers": data.get("teachers", []),
        "year": data.get("year"),
    }

    processed_outcomes = []
    for outcome in data.get("outcomes", []):
        outcome_id = (outcome.get("name", "")).lower()
        outcome["id"] = outcome_id

        for criterion in outcome.get("criteria", []):
            criterion_name = criterion.get("name", "").lower()
            criterion_id = f"{outcome_id}_{criterion_name}"

            # Index existing levels by name
            levels_map = {
                (lvl.get("name", "")).strip(): {
                    "text": lvl.get("text", ""),
                    "weight": lvl.get("weight", 0),
                }
                for lvl in criterion.get("levels", [])
            }

            # Rebuild normalized levels
            normalized_levels = []
            for level_info in LEVELS_ORDER:
                level_name = level_info["order"]
                level_label = level_info["label"]
                level_dict = levels_map.get(level_label, {"text": "", "weight": 0})

                if level_label in levels_map:
                    normalized_levels.append({
                        "id": f"{criterion_id}_l{level_name}",
                        "name": f"l{level_name}",
                        "order": level_info["order"],
                        "weight": level_dict["weight"],
                        "label": level_label,
                        "text": level_dict["text"],
                        "color": level_info["color"],
                        "critical": level_info["critical"],
                    })

            # add not answered 
            normalized_levels.append({
                        "id": f"{criterion_id}_l_na",
                        "name": f"l_na",
                        "order": -1,
                        "weight": 0,
                        "label": "Non traité",
                        "text": "Non traité",
                        "color": "#FFFFFF",
                        "critical": False
                    })

            criterion["id"] = criterion_id
            criterion["levels"] = normalized_levels

        processed_outcomes.append(outcome)

    # Rebuild normalized YAML with metadata + processed modules
    return {**metadata, "outcomes": processed_outcomes}

def preprocess_yaml(data):
    """
    Normalise un fichier YAML de grille d'évaluation :
    - Conserve les métadonnées (cours, année, enseignant, etc.)
    - Donne des IDs cohérents aux outcomes et critères
    - Conserve les niveaux du YAML dans l’ordre défini
    - Attribue des couleurs progressives selon le poids
    """

    metadata = {
        "course": data.get("course"),
        "semester": data.get("semester"),
        "teachers": data.get("teachers", []),
        "year": data.get("year"),
    }

    def weight_to_color(weight):
        """Détermine une couleur selon le poids"""
        if weight >= 0.9:
            return "#06D6A0"  # vert
        elif weight >= 0.6:
            return "#8ED081"  # vert clair
        elif weight >= 0.4:
            return "#FFD166"  # jaune
        elif weight >= 0.2:
            return "#FF9F1C"  # orange
        else:
            return "#FF6B6B"  # rouge

    processed_outcomes = []

    for outcome in data.get("outcomes", []):
        outcome_id = (outcome.get("name", "")).lower().strip()
        outcome["id"] = outcome_id

        for criterion in outcome.get("criteria", []):
            criterion_name = criterion.get("name", "").lower().strip()
            criterion_id = f"{outcome_id}_{criterion_name}" if criterion_name else outcome_id
            criterion["id"] = criterion_id

            normalized_levels = []
            for i, lvl in enumerate(criterion.get("levels", [])):
                weight = float(lvl.get("weight", 0))
                normalized_levels.append({
                    "id": f"{criterion_id}_l{i}",
                    "name": lvl.get("name", f"Level {i}"),
                    "order": i,
                    "weight": weight,
                    "label": lvl.get("name", f"Level {i}"),
                    "text": lvl.get("text", ""),
                    "color": weight_to_color(weight),
                    "critical": (weight == 0)
                })

            # Ajouter le niveau "Non traité"
            normalized_levels.append({
                "id": f"{criterion_id}_l_na",
                "name": "l_na",
                "order": -1,
                "weight": 0,
                "label": "Non traité",
                "text": "Non traité",
                "color": "#FFFFFF",
                "critical": False
            })

            criterion["levels"] = normalized_levels

        processed_outcomes.append(outcome)

    return {**metadata, "outcomes": processed_outcomes}


def yaml_grid_to_json(yaml_file, json_file):
    """Convert YAML rubric (learning outcomes + criteria) into normalized JSON."""
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    normalized = preprocess_yaml(data)

    if not json_file:
        json_file = yaml_file.with_suffix(".json")

    Path(json_file).parent.mkdir(parents=True, exist_ok=True)
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    # Stats
    outcomes = normalized.get("outcomes", [])
    num_outcomes = len(outcomes)
    num_criteria = sum(len(outcome.get("criteria", [])) for outcome in outcomes)
    num_levels = sum(
        len(criterion.get("levels", [])) 
        for outcome in outcomes 
        for criterion in outcome.get("criteria", [])
    )

    print(f"✅ Rubric grid converted: {yaml_file} → {json_file}")
    print(f"📊 Stats: {num_outcomes} outcomes, {num_criteria} criteria, {num_levels} levels")


def latex_latex_exam_to_json(tex_file, json_file):
    """Convert LaTeX exam source into structured JSON with sections and questions."""

    if not json_file:
        json_file = tex_file.with_suffix(".json")

    tex_content = Path(tex_file).read_text(encoding="utf-8")
    data = parse_latex_questions(tex_content)

    Path(json_file).parent.mkdir(parents=True, exist_ok=True)
    Path(json_file).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Stats
    num_sections = len(data.get("sections", []))
    num_questions = sum(len(sec.get("questions", [])) for sec in data.get("sections", []))
    max_score_exam = data.get("maxScore", 0)

    print(f"✅ Latex exam converted: {tex_file} → {json_file}")
    print(f"📊 Exam parsed: {num_sections} sections, {num_questions} questions, {max_score_exam} total points → {json_file}")


def moodle_student_csv_to_json(csv_file: Path, json_file: Path = None):
    """Convert CSV export of students into normalized JSON."""
    FIELD_MAP = {
        "\ufeffIdentifiant": "id",  # Handle BOM
        "Identifiant": "id",
        "Nom complet": "full_name",
        "Adresse de courriel": "email",
    }

    if json_file is None:
        json_file = csv_file.with_suffix(".json")

    rows = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            # Translate only known fields
            translated = {
                FIELD_MAP[k]: (v if v != "" else None)
                for k, v in row.items()
                if k in FIELD_MAP
            }

            # Split full name into firstName / lastName
            firstName, lastName = split_full_name(translated.pop("full_name"))

            clean_row = {
                "id": int(translated["id"].replace("Participant", "")),
                "email": translated["email"],
                "firstName": firstName,
                "lastName": lastName
            }
            rows.append(clean_row)

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"✅ Student CSV converted: {csv_file} → {json_file}")
    print(f"📊 Student parsed: {len(rows)} students")

def moodle_student_csv_picture_to_json(csv_file: Path,json_file: Path = None,photos_file: Path = None):
    """Convert CSV export of students into normalized JSON, optionally enriched with photos."""

    FIELD_MAP = {
        "\ufeffIdentifiant": "id",  # Handle BOM
        "Identifiant": "id",
        "Nom complet": "full_name",
        "Adresse de courriel": "email",
    }

    if json_file is None:
        json_file = csv_file.with_suffix(".json")

    # --- Étape 1 : Lecture CSV Moodle ---
    rows = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            translated = {
                FIELD_MAP[k]: (v if v != "" else None)
                for k, v in row.items()
                if k in FIELD_MAP
            }

            firstName, lastName = split_full_name(translated.pop("full_name"))
            clean_row = {
                "id": int(translated["id"].replace("Participant", "")),
                "email": translated["email"],
                "firstName": firstName,
                "lastName": lastName
            }
            rows.append(clean_row)

    # --- Étape 2 : Enrichissement via JSON photos ---
    with open(photos_file, "r", encoding="utf-8") as f:
        photos_data = json.load(f)

    for student in rows:
        match = next(
            (
                p for p in photos_data.values()
                if p["firstName"].strip().lower() == student["firstName"].strip().lower()
                and p["lastName"].strip().lower() == student["lastName"].strip().lower()
            ),
            None
        )
        if match:
            student["photo"] = match.get("photo")
            student["group"] = match.get("group")
        else:
            print(f' Problème étudiant {student}')

    # --- Étape 3 : Sauvegarde ---
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"✅ Student CSV converted: {csv_file} → {json_file}")
    print(f"📊 {len(rows)} students parsed")
    if photos_file:
        print(f"🖼️ Photos linked from: {photos_file}")


def json_to_gradix(exam_json: Path, student_json: Path, grid_json: Path, output_json: Path):
    """Load JSON files, construct the gradix file and export it."""
    data_exam = json.loads(Path(exam_json).read_text(encoding="utf-8"))
    student_list = json.loads(Path(student_json).read_text(encoding="utf-8"))
    data_grid = json.loads(Path(grid_json).read_text(encoding="utf-8"))

    merged = build_gradix_dict(data_exam, student_list, data_grid)

    Path(output_json).write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Flat Gradix dataset created: {output_json} ")
    print(f"📊 Flat Grid: {len(merged['outcomes'])} outcomes, {len(merged['criteria'])} criteria")
    print(f"📊 Flat Exam: {len(merged['sections'])} sections, {len(merged['questions'])} questions")
    print(f"📊 Flat Students: {len(merged['students'])} students")
    print(f"📊 Flat Student Questions: {len(merged['studentQuestions'])} questions")

