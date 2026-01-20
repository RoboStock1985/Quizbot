import flet as ft
import csv
import random
import string
import difflib
import winsound

CSV_PATH = "questions.csv"
FUZZY_THRESHOLD = 0.8
WRAP_LENGTH = 40

CATEGORY_COLORS = {
    "Geography": ft.Colors.BLUE,
    "Entertainment": ft.Colors.PINK,
    "History": ft.Colors.YELLOW,
    "Arts & Literature": ft.Colors.PURPLE,
    "Science & Nature": ft.Colors.GREEN,
    "Sports & Leisure": ft.Colors.ORANGE,
    "Technology": ft.Colors.CYAN,
    "Film": ft.Colors.RED,
    "Music": ft.Colors.LIGHT_BLUE,
    "Food & Drink": ft.Colors.BROWN,
    "Miscellaneous": ft.Colors.GREY,
}


def load_questions(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalise(text: str) -> str:
    text = text.lower().strip()
    return text.translate(str.maketrans("", "", string.punctuation))


def fuzzy_match(user: str, correct: str) -> bool:
    return difflib.SequenceMatcher(None, user, correct).ratio() >= FUZZY_THRESHOLD


def wrap_text(text, line_length=WRAP_LENGTH):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= line_length:
            if current_line:
                current_line += " "
            current_line += word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)


def main(page: ft.Page):
    page.title = "Trivia on Tap 🍺"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 30
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    questions = load_questions(CSV_PATH)
    current_question = {}
    score = {"correct": 0, "total": 0}
    asked_question_ids = set()

    # --- UI Elements ---
    title = ft.Text("🍺 Trivia on Tap", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER)
    score_text = ft.Text(size=14, opacity=0.8)

    question_text = ft.Text(size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.LEFT)
    category_box = ft.Container(padding=5, border_radius=5)
    submitted_by_text = ft.Text(size=14, italic=True, color=ft.Colors.GREY)

    answer_input = ft.TextField(label="Your answer", autofocus=True, on_submit=lambda e: check_answer(e))
    feedback_text = ft.Text(size=16)

    submit_button = ft.ElevatedButton(content=ft.Text("Submit"), width=150)
    next_button = ft.TextButton(content=ft.Text("Next question"), visible=False)

    # Add question controls (hidden)
    new_q_field = ft.TextField(label="New question")
    new_a_field = ft.TextField(label="Answer")
    new_category_dropdown = ft.Dropdown(
        label="Category",
        options=[ft.dropdown.Option(c) for c in CATEGORY_COLORS.keys()]
    )
    new_submitted_by = ft.TextField(label="Submitted by")
    add_q_button = ft.ElevatedButton(content=ft.Text("Add Question"))
    message_text = ft.Text(size=14, color=ft.Colors.LIGHT_GREEN)

    add_question_column = ft.Column(
        controls=[
            ft.Text("Add a new question", weight=ft.FontWeight.BOLD),
            new_q_field,
            new_a_field,
            new_category_dropdown,
            new_submitted_by,
            add_q_button,
            message_text
        ],
        visible=False
    )

    toggle_add_button = ft.TextButton(content=ft.Text("➕ Add Question"))

    def toggle_add_question(e):
        add_question_column.visible = not add_question_column.visible
        page.update()

    toggle_add_button.on_click = toggle_add_question

    # --- Logic ---
    def update_score():
        score_text.value = f"Score: {score['correct']} / {score['total']}"

    def load_random_question():
        remaining_questions = [q for q in questions if q["question_id"] not in asked_question_ids]
        if not remaining_questions:
            feedback_text.value = "🏁 All questions completed!"
            question_text.value = ""
            category_box.visible = False
            submitted_by_text.value = ""
            page.update()
            return

        q = random.choice(remaining_questions)
        current_question.clear()
        current_question.update(q)
        asked_question_ids.add(q["question_id"])

        question_text.value = wrap_text(q["question"])
        # Category box
        category_name = q.get("category", "")
        category_color = CATEGORY_COLORS.get(category_name, ft.Colors.GREY)
        category_box.content = ft.Text(category_name, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
        category_box.bgcolor = category_color
        category_box.visible = bool(category_name)

        # Submitted by
        submitted_by_text.value = f"Submitted by: {q['submitted_by']}" if q.get("submitted_by") else ""

        answer_input.value = ""
        feedback_text.value = ""
        next_button.visible = False
        page.update()

    def handle_result(correct: bool):
        score["total"] += 1
        if correct:
            score["correct"] += 1
            feedback_text.value = f"✅ Correct!\nAnswer: {current_question['answer']}"
            feedback_text.color = ft.Colors.GREEN
            winsound.PlaySound("sounds/correct.wav", winsound.SND_ASYNC)
        else:
            feedback_text.value = f"❌ Wrong\nAnswer: {current_question['answer']}"
            feedback_text.color = ft.Colors.RED
            winsound.PlaySound("sounds/wrong.wav", winsound.SND_ASYNC)

        update_score()
        next_button.visible = True
        page.update()

    def check_answer(e):
        user = normalise(answer_input.value)
        correct_answer = normalise(current_question["answer"])
        is_correct = user == correct_answer or fuzzy_match(user, correct_answer)
        handle_result(correct=is_correct)

    def add_question(e):
        q_text = new_q_field.value.strip()
        a_text = new_a_field.value.strip()
        category_text = new_category_dropdown.value or ""
        submitted_by = new_submitted_by.value.strip()
        if not q_text or not a_text:
            message_text.value = "❌ Question and answer cannot be empty!"
        else:
            max_id = max((int(q["question_id"]) for q in questions), default=0)
            new_entry = {
                "question_id": str(max_id + 1),
                "question": q_text,
                "answer": a_text,
                "category": category_text,
                "submitted_by": submitted_by
            }
            with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["question_id", "question", "answer", "category", "submitted_by"])
                writer.writerow(new_entry)
            questions.append(new_entry)
            new_q_field.value = ""
            new_a_field.value = ""
            new_category_dropdown.value = None
            new_submitted_by.value = ""
            message_text.value = "✅ Question added!"
        page.update()

    # --- Connect buttons ---
    submit_button.on_click = check_answer
    next_button.on_click = lambda e: load_random_question()
    add_q_button.on_click = add_question

    # Initial load
    update_score()
    load_random_question()

    # --- Layout ---
    page.add(
        ft.Card(
            elevation=10,
            content=ft.Container(
                width=650,
                padding=25,
                content=ft.Column(
                    spacing=20,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        title,
                        score_text,
                        ft.Row(
                            controls=[question_text, category_box],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10
                        ),
                        submitted_by_text,
                        answer_input,
                        submit_button,
                        feedback_text,
                        next_button,
                        ft.Divider(),
                        toggle_add_button,
                        add_question_column
                    ],
                ),
            ),
        )
    )


# if __name__ == "__main__":
#     ft.app(target=main)


# if __name__ == "__main__":
#     ft.app(
#         target=main,
#         host="0.0.0.0",  # listen on all network interfaces
#         port=60411,
#         view=None  # do not open a local desktop window
#     )

ft.run(main)

# ft.app(host="0.0.0.0", port=60411, target=main, view=ft.WEB_BROWSER)
