import json
import copy
import numpy as np
from pathlib import Path


def build_gradix_dict(data_exam: dict, student_list: list, data_grid: list) -> dict:
    """Construit un dictionnaire Gradix à partir de données déjà chargées (dict/list)."""
    exam_id = str(data_exam["id"])

    # --- Flat maps ---
    students = {}
    sections = {}
    questions = {}
    studentScoresheets = {}
    studentSections = {}
    studentQuestions = {}

    # --- Students
    for student in student_list:
        sid = str(student["id"])
        students[sid] = {
            "id": sid,
            "firstName": student["firstName"],
            "lastName": student["lastName"],
            "email": student["email"],
        }

    # --- Sections + Questions
    for section in data_exam["sections"]:
        sec_id = f"{exam_id}_{section['id']}"
        sections[sec_id] = {
            "id": sec_id,
            "name": section["id"],
            "text": section["text"],
            "questionIds": [f"{exam_id}_{q['id']}" for q in section["questions"]],
            "score": 0,
            "maxScore": section["maxScore"],
        }

        for q in section["questions"]:
            qid = f"{exam_id}_{q['id']}"
            questions[qid] = {
                "id": qid,
                "name": q["id"],
                "text": q["text"],
                "maxScore": q["maxScore"],
                "outcome": q.get("outcomeId"),
                "criterionId": q.get("criterionId"),
                "sectionId": sec_id,
            }

    # --- StudentScoresheets + StudentSections + StudentQuestions
    for student in student_list:
        sid = str(student["id"])
        ss_id = f"ss_{sid}_{exam_id}"

        studentScoresheets[ss_id] = {
            "id": ss_id,
            "studentId": sid,
            "examId": exam_id,
            "score": 0,
            "comment": "",
            "studentSectionIds": [],
        }

        for section in data_exam["sections"]:
            sec_id = f"{exam_id}_{section['id']}"
            student_section_id = f"ss_{sid}_{sec_id}"

            studentSections[student_section_id] = {
                "id": student_section_id,
                "studentId": sid,
                "sectionId": sec_id,
                "score": 0,
                "comment": "",
                "studentQuestionIds": [],
            }
            studentScoresheets[ss_id]["studentSectionIds"].append(student_section_id)

            for q in section["questions"]:
                qid = f"{exam_id}_{q['id']}"
                student_qid = f"sq_{sid}_{qid}"

                studentQuestions[student_qid] = {
                    "id": student_qid,
                    "studentId": sid,
                    "studentSectionId": student_section_id,
                    "sectionId": sec_id,
                    "questionId": qid,
                    "score": 0,
                    "label": "",
                    "color": "FFFFFF",
                    "comment": "",
                }
                studentSections[student_section_id]["studentQuestionIds"].append(student_qid)

    # --- Rubrics
    outcomes = {}
    criteria = {}
    levels = {}

    for g in data_grid["outcomes"]:
        outcome_id = g["name"].lower()
        outcomes[outcome_id] = {
            "id": outcome_id,
            "name": g["name"],
            "short": g.get("short", ""),
            "text": g.get("text", ""),
            "criterionIds": []
        }

        for crit in g["criteria"]:
            crit_id = f"{outcome_id}_{crit['name']}".lower()
            criteria[crit_id] = {
                "id": crit_id,
                "outcomeId": outcome_id,
                "short": crit.get("short", ""),
                "text": crit.get("text", ""),
                "levelIds": []
            }

            outcomes[outcome_id]["criterionIds"].append(crit_id)

            sorted_levels = sorted(crit["levels"], key=lambda l: -l["weight"])
            for idx, lvl in enumerate(sorted_levels):
                level_id = f"{crit_id}_l{idx}"
                levels[level_id] = {
                    "id": level_id,
                    "criterionId": crit_id,
                    "label": lvl["label"],
                    "text": lvl.get("text", ""),
                    "weight": lvl.get("weight", 0),
                    "color": lvl.get("color", "#999999"),
                    "critical": lvl.get("critical", False)
                }
                criteria[crit_id]["levelIds"].append(level_id)

    # --- Final merge
    current_exam = data_exam
    del current_exam["sections"]
    return {
        "exams": {exam_id: current_exam},
        "students": students,
        "sections": sections,
        "questions": questions,
        "studentScoresheets": studentScoresheets,
        "studentSections": studentSections,
        "studentQuestions": studentQuestions,
        "outcomes": outcomes,
        "criteria": criteria,
        "levels": levels
    }

def group_outcome_grid(gradix: dict) -> dict:
    outcomes= {}
    for outcome_id, outcome in gradix["outcomes"].items():
        
        criteria = {}
        for criterion_id in outcome["criterionIds"]:
            criterion = gradix["criteria"][criterion_id]
            criteria[criterion_id] = {
                    "id": criterion["id"],
                    "short": criterion["short"],
                    "text": criterion["text"],
                    "score": 0,
                    "maxScore": 0
                    }

        outcome_obj = {
            "id": outcome["id"],
            "short": outcome["short"],
            "text": outcome["text"],
            "criteria": criteria
            }

        outcomes[outcome_id] = outcome_obj
    
    return outcomes


def group_scoresheets_by_exam(scoresheets: list) -> dict:

    by_exam = {}
    for scoresheet in scoresheets:
        exam_id = scoresheet["exam"]["id"]
        if exam_id not in by_exam:
            by_exam[exam_id] = {
                "exam": scoresheet["exam"],
                "scoresheets": []
            }
        by_exam[exam_id]["scoresheets"].append(scoresheet)
    return by_exam


def extract_gradix_scoresheets(gradix: dict, outcomes: dict) -> list:

    student_scoresheets = []
    for student_scoresheet_id, student_scoresheet in gradix["studentScoresheets"].items():
        student = gradix["students"][student_scoresheet["studentId"]]
        exam = gradix["exams"][student_scoresheet["examId"]]
        outcomes_scoresheet = copy.deepcopy(outcomes)
        scoresheet_obj = {
            "exam": exam,
            "student": student,
            "comment": student_scoresheet["comment"],
            "date": student_scoresheet.get("date", "Date non spécifiée"),
            "score": student_scoresheet["score"],
            "maxScore": exam["maxScore"],
            "sections": [],
            "outcomes": outcomes_scoresheet
        }
        for index_section, student_section_id in enumerate(student_scoresheet["studentSectionIds"]):
            student_section = gradix["studentSections"][student_section_id]
            section = gradix["sections"][student_section["sectionId"]]
            section_obj = {
                "name": section["name"],
                "text": section["text"],
                "maxScore": section["maxScore"],
                "score": student_section["score"],
                "comment": student_section["comment"],
                "questions": []
            }
            for index_question, student_question_id in enumerate(student_section["studentQuestionIds"]):
                student_question = gradix["studentQuestions"][student_question_id]
                question = gradix["questions"][student_question["questionId"]]
                criterion = gradix["criteria"][question["criterionId"]]
                outcome = gradix["outcomes"][criterion["outcomeId"]]
                question_obj = {
                    "name": question["name"],
                    "text": question["text"],
                    "maxScore": question["maxScore"],
                    "criterion": {"id": criterion["id"], "short": criterion["short"], "text": outcome["text"]},
                    "outcome": {"id": outcome["id"], "name": outcome["name"], "short": outcome["short"], "text": outcome["text"]},
                    "score": student_question["score"],
                    "label": student_question["label"],
                    "comment": student_question["comment"],
                }
                section_obj["questions"].append(question_obj)
                outcomes_scoresheet[outcome["id"]]["criteria"][criterion["id"]]["score"] += student_question["score"]
                outcomes_scoresheet[outcome["id"]]["criteria"][criterion["id"]]["maxScore"] += question["maxScore"]
            scoresheet_obj["sections"].append(section_obj)
        student_scoresheets.append(scoresheet_obj)
    return student_scoresheets


def add_exam_stats(by_exam: dict) -> None:

    for exam_id in by_exam:
        scores = [s["score"] for s in by_exam[exam_id]["scoresheets"]]
        if not scores:
            continue
        scores_array = np.array(scores)
        by_exam[exam_id]["stats"] = {
            "mean": float(np.mean(scores_array)),
            "variance": float(np.var(scores_array)),
            "min": float(np.min(scores_array)),
            "max": float(np.max(scores_array)),
            "count": len(scores_array)
        }


def extract_gradix(gradix: dict) -> dict:

    outcomes = group_outcome_grid(gradix)
    scoresheets = extract_gradix_scoresheets(gradix, outcomes)
    scoresheets_by_exam = group_scoresheets_by_exam(scoresheets)
    add_exam_stats(scoresheets_by_exam)

    return scoresheets_by_exam


