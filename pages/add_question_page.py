import flet as ft
from db import supabase

def build_add_question_page(page, categories, selected_category=None, selected_topic="", submitted_by=""):
    # ---------- Fields ----------
    question_field = ft.TextField(
        label="Question",
        multiline=True,
        min_lines=3,
        width=600,
        border_color=ft.Colors.WHITE,
    )

    answer_field = ft.TextField(
        label="Answer",
        width=600,
        border_color=ft.Colors.WHITE,
    )

    category_field = ft.Dropdown(
        label="Category",
        options=[ft.dropdown.Option(c) for c in categories],
        width=300,
        border_color=ft.Colors.WHITE,
        value=selected_category,
    )

    topic_field = ft.TextField(
        label="Topic",
        width=300,
        border_color=ft.Colors.WHITE,
        value=selected_topic,
    )

    submitted_by_field = ft.TextField(
        label="Submitted by",
        width=300,
        border_color=ft.Colors.WHITE,
        value=submitted_by,
    )

    feedback = ft.Text(size=14)

    # ---------- Logic ----------
    def add_question(e):
        if not question_field.value or not answer_field.value or not category_field.value:
            feedback.value = "❌ Question, answer, and category are required"
            feedback.color = ft.Colors.RED
            page.update()
            return

        try:
            supabase.table("questions").insert({
                "question": question_field.value.strip(),
                "answer": answer_field.value.strip(),
                "category": category_field.value,
                "topic": topic_field.value.strip(),
                "submitted_by": submitted_by_field.value.strip() or "Anonymous",
                "upvotes": 0,
                "downvotes": 0,
            }).execute()

            # clear only question & answer
            question_field.value = ""
            answer_field.value = ""

            feedback.value = "✅ Question added!"
            feedback.color = ft.Colors.GREEN
            page.update()

        except Exception as ex:
            feedback.value = f"❌ Error: {ex}"
            feedback.color = ft.Colors.RED
            page.update()

    # ---------- Card Layout ----------
    form_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("➕ Add a Question", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(thickness=1, color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),

                question_field,
                answer_field,

                # category and topic on same row
                ft.Row(
                    [category_field, topic_field],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                # submitted by underneath
                submitted_by_field,

                ft.ElevatedButton("Add Question", on_click=add_question),
                feedback,
            ],
            spacing=18,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=30,
        border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.WHITE)),
        border_radius=12,
        width=700,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
    )

    # ---------- Fullscreen Center Container ----------
    page_container = ft.Container(
        content=form_card,
        expand=True,  # ensures it fills the whole screen
        alignment=ft.Alignment(x=0, y=0),  # centers content horizontally + vertically
    )

    return page_container
