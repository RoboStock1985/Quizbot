import os
import flet as ft
from db import supabase
from filters import build_multiselect_filter, build_topic_checkbox_filter
from config import CATEGORY_COLORS
from fpdf import FPDF
import tempfile
import asyncio

# -------------------------------
# PDF subclass for Unicode support
# -------------------------------
class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # Use a built-in font that supports Unicode
        self.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        self.set_font("DejaVu", "", 12)

# -------------------------------
# Builder Page
# -------------------------------
def build_builder_page(page, categories, topics, selected_categories, selected_topics, notify):

    category_filter = build_multiselect_filter(
        "Categories", categories, selected_categories, page, CATEGORY_COLORS
    )
    topic_filter = build_topic_checkbox_filter(
        "Topics", topics, selected_topics, page
    )

    question_list = ft.Column(spacing=8, scroll=True)
    builder_questions = []

    # -------------------------------
    # Lazy load questions
    # -------------------------------
    def load_questions(e):
        nonlocal builder_questions
        query = supabase.table("questions").select("*").limit(100)
        if selected_categories and len(selected_categories) != len(categories):
            query = query.in_("category", list(selected_categories))
        if selected_topics and len(selected_topics) != len(topics):
            query = query.in_("topic", list(selected_topics))
        builder_questions = query.execute().data or []
        rebuild()

    def rebuild():
        question_list.controls.clear()
        for i, q in enumerate(builder_questions):
            question_list.controls.append(build_question_card(i, q))
        page.update()

    def build_question_card(idx, q):
        q_field = ft.TextField(value=q["question"], multiline=True, width=600)
        a_field = ft.TextField(value=q["answer"], multiline=True, width=400)

        def on_change(e):
            q["question"] = q_field.value
            q["answer"] = a_field.value

        q_field.on_change = on_change
        a_field.on_change = on_change

        return ft.Container(
            content=ft.Row([ft.Text(f"{idx+1}."), q_field, a_field]),
            border=ft.border.all(1, ft.Colors.WHITE24),
            border_radius=6,
            padding=10,
        )

    # -------------------------------
    # Async PDF export
    # -------------------------------
    async def export_pdf(page: ft.Page, builder_questions, notify):

        if not builder_questions:
            notify("No questions to export")
            return

        # -----------------------------
        # Create PDF in memory
        # -----------------------------
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("DejaVu", size=12)  # Unicode-safe font

        for i, q in enumerate(builder_questions, 1):
            pdf.multi_cell(0, 8, f"{i}. {q['question']}\nAnswer: {q['answer']}\n")

        # -----------------------------
        # Save to temporary file
        # -----------------------------
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, "quiz_export.pdf")
        pdf.output(temp_path)

        # -----------------------------
        # Let user choose save location
        # -----------------------------
        file_picker = ft.FilePicker()

        save_path = await file_picker.save_file(
            file_name="quiz_export.pdf",
            allowed_extensions=["pdf"],
        )

        # -----------------------------
        # Copy temp file to chosen location
        # -----------------------------
        if save_path:
            # Ensure the save_path ends with .pdf
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

        # -----------------------------
        # Clean up temp file
        # -----------------------------
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # -------------------------------
    # UI
    # -------------------------------
    return [
        ft.Row(
            [
                ft.Container(
                    width=280,
                    padding=10,
                    content=ft.Column(
                        [
                            ft.Text("Filters", weight=ft.FontWeight.BOLD),
                            category_filter,
                            topic_filter,
                        ]
                    ),
                ),
                ft.VerticalDivider(),
                ft.Container(
                    expand=True,
                    padding=10,
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.ElevatedButton("📥 Load Questions", on_click=load_questions),
                                    ft.ElevatedButton(
                                        "📄 Export PDF",
                                        on_click=lambda e: asyncio.create_task(export_pdf(page, builder_questions, notify))
                                    ),
                                ]
                            ),
                            question_list,
                        ]
                    ),
                ),
            ]
        )
    ]
