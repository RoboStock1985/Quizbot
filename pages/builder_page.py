import flet as ft
from db import supabase
from filters import build_multiselect_filter, build_topic_checkbox_filter
from config import CATEGORY_COLORS
import fpdf
import io
from fpdf import FPDF

import flet as ft
from fpdf import FPDF
import tempfile
import os




def build_builder_page(page, categories, topics, selected_categories, selected_topics, notify):

    save_picker = ft.FilePicker()
    page.overlay.append(save_picker)

    category_filter = build_multiselect_filter(
        "Categories", categories, selected_categories, page, CATEGORY_COLORS
    )
    topic_filter = build_topic_checkbox_filter(
        "Topics", topics, selected_topics, page
    )

    question_list = ft.Column(spacing=8, scroll=True)
    builder_questions = []

    def load_questions(e):
        nonlocal builder_questions
        query = supabase.table("questions").select("*")
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

    def export_pdf(e):
        if not builder_questions:
            notify("No questions to export")
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        for i, q in enumerate(builder_questions, 1):
            pdf.multi_cell(
                0,
                8,
                f"{i}. {q['question']}\nAnswer: {q['answer']}\n",
            )

        # Write PDF to a temp file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf.output(tmp.name)
        tmp.close()

        def on_save_result(e: ft.FilePickerResultEvent):
            if e.path:
                with open(tmp.name, "rb") as src, open(e.path, "wb") as dst:
                    dst.write(src.read())
                notify("PDF downloaded")
            os.unlink(tmp.name)

        save_picker.on_result = on_save_result
        save_picker.save_file(
            file_name="quiz_export.pdf",
            allowed_extensions=["pdf"],
        )


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
                                    ft.ElevatedButton("📄 Export PDF", on_click=export_pdf),
                                ]
                            ),
                            question_list,
                        ]
                    ),
                ),
            ]
        )
    ]
