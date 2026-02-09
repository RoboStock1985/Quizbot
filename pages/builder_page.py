import os
import random
import flet as ft
from db import supabase
from filters import build_multiselect_filter, build_topic_checkbox_filter
from config import CATEGORY_COLORS
from fpdf import FPDF
import tempfile
import asyncio

# -------------------------------
# Unicode-safe PDF
# -------------------------------
class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        self.set_font("DejaVu", "", 12)

# -------------------------------
# Builder Page
# -------------------------------
def build_builder_page(page, categories, topics, selected_categories, selected_topics, notify):

    # ---------------- Filters ----------------
    category_filter = build_multiselect_filter(
        "Categories", categories, selected_categories, page, CATEGORY_COLORS
    )
    topic_filter = build_topic_checkbox_filter(
        "Topics", topics, selected_topics, page
    )

    max_questions = ft.Dropdown(
        label="Max Questions",
        options=[ft.dropdown.Option(str(x)) for x in [10, 20, 50, 100]],
        value="10",
        width=200,
    )

    question_list = ft.Column(spacing=8, scroll=True)
    builder_questions = []

    # -------------------------------
    # Rebuild question list UI
    # -------------------------------
    def rebuild():
        question_list.controls.clear()
        for i, q in enumerate(builder_questions):
            question_list.controls.append(build_question_card(i, q))
        page.update()

    # -------------------------------
    # Load questions (lazy)
    # -------------------------------
    def load_questions(e):
        nonlocal builder_questions

        query = supabase.table("questions").select("*")
        if selected_categories and len(selected_categories) != len(categories):
            query = query.in_("category", list(selected_categories))
        if selected_topics and len(selected_topics) != len(topics):
            query = query.in_("topic", list(selected_topics))

        try:
            limit = int(max_questions.value)
        except ValueError:
            limit = 100

        fetch_limit = max(limit * 3, 100)  # fetch extra for randomness
        query = query.limit(fetch_limit)
        builder_questions = query.execute().data or []

        random.shuffle(builder_questions)
        builder_questions = builder_questions[:limit]  # cap to max

        rebuild()
        notify(f"Loaded {len(builder_questions)} questions")

    # -------------------------------
    # Build individual question card
    # -------------------------------
    def build_question_card(idx, q):
        # Expandable text fields
        q_field = ft.TextField(value=q["question"], multiline=True, expand=True)
        a_field = ft.TextField(value=q["answer"], multiline=True, expand=True)

        # Buttons
        up_btn = ft.IconButton(ft.Icons.ARROW_UPWARD)
        down_btn = ft.IconButton(ft.Icons.ARROW_DOWNWARD)
        refresh_btn = ft.IconButton(ft.Icons.REFRESH)

        # Callbacks
        def move_up(e):
            if idx == 0:
                return
            builder_questions[idx], builder_questions[idx-1] = builder_questions[idx-1], builder_questions[idx]
            rebuild()

        def move_down(e):
            if idx == len(builder_questions)-1:
                return
            builder_questions[idx], builder_questions[idx+1] = builder_questions[idx+1], builder_questions[idx]
            rebuild()

        def refresh_question(e):
            cat = q.get("category")
            query = supabase.table("questions").select("*").eq("category", cat)
            result = query.execute().data or []
            # Exclude questions already in the list
            result = [r for r in result if r["question_id"] not in {q["question_id"] for q in builder_questions}]
            if result:
                builder_questions[idx] = random.choice(result)
                rebuild()
            else:
                notify("No other questions available in this category")

        up_btn.on_click = move_up
        down_btn.on_click = move_down
        refresh_btn.on_click = refresh_question

        def on_change(e):
            q["question"] = q_field.value
            q["answer"] = a_field.value

        q_field.on_change = on_change
        a_field.on_change = on_change

        # Row: text fields expand, buttons fixed size
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(f"{idx+1}."),          # Index
                    q_field,                        # Expands
                    a_field,                        # Expands
                    ft.Row([up_btn, down_btn, refresh_btn], spacing=10)  # Buttons compact
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            border=ft.border.all(1, ft.Colors.WHITE24),
            border_radius=6,
            padding=10,
        )


    # -------------------------------
    # PDF Export
    # -------------------------------
    async def export_pdf(page: ft.Page, builder_questions, notify):
        if not builder_questions:
            notify("No questions to export")
            return

        pdf = PDF()
        pdf.add_page()
        for i, q in enumerate(builder_questions, 1):
            pdf.multi_cell(0, 8, f"{i}. {q['question']}\nAnswer: {q['answer']}\n")

        temp_path = os.path.join(tempfile.gettempdir(), "quiz_export.pdf")
        pdf.output(temp_path)

        file_picker = ft.FilePicker()
        save_path = await file_picker.save_file(file_name="quiz_export.pdf", allowed_extensions=["pdf"])

        if save_path:
            if not save_path.lower().endswith(".pdf"):
                save_path += ".pdf"
            try:
                with open(temp_path, "rb") as src, open(save_path, "wb") as dst:
                    dst.write(src.read())
                notify("✅ PDF exported successfully!")
            except Exception as ex:
                notify(f"❌ Error saving PDF: {ex}")
        else:
            notify("Export cancelled")

        if os.path.exists(temp_path):
            os.remove(temp_path)

    # -------------------------------
    # Layout
    # -------------------------------
    return [
        ft.Row(
            [
                ft.Container(
                    width=280,
                    padding=10,
                    alignment=ft.Alignment(-1, -1),
                    content=ft.Column(
                        [
                            ft.Text("Filters", weight=ft.FontWeight.BOLD),
                            max_questions,
                            category_filter,
                            topic_filter,
                        ],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ),
                ft.VerticalDivider(),
                ft.Container(
                    expand=True,
                    padding=10,
                    content=ft.Column(
                        [
                            ft.Row([
                                ft.ElevatedButton("📥 Load Questions", on_click=load_questions),
                                ft.ElevatedButton(
                                    "📄 Export PDF",
                                    on_click=lambda e: asyncio.create_task(export_pdf(page, builder_questions, notify))
                                ),
                            ]),
                            question_list,
                        ],
                    ),
                ),
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    ]
