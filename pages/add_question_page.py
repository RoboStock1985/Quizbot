import flet as ft
from db import supabase
import os
import io
import uuid


def build_add_question_page(page, categories, selected_category=None, selected_topic="", submitted_by=""):

    # ---------- Image preview ----------
    question_image = ft.Image(src="", width=400, height=300, visible=False, fit="contain")

    # ---------- Notification helper ----------
    def notify(msg):
        snack = ft.SnackBar(ft.Text(msg))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # ---------- File picker ----------
    async def handle_pick_image(e):
        files = await ft.FilePicker().pick_files(
            allow_multiple=False,
            allowed_extensions=["png", "jpg", "jpeg", "gif", "webp"],
        )
        
        if not files:
            return

        file = files[0]
        file_path = file.path
        if not file_path:
            notify("❌ No valid file path found.")
            return

        # Show local preview
        question_image.src = file_path
        question_image.visible = True
        page.update()

        # Upload to Supabase
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            ext = os.path.splitext(file_path)[1]
            file_name = f"{uuid.uuid4()}{ext}"

            # Upload bytes directly, not BytesIO
            res = supabase.storage.from_("quiz-images").upload(file_name, data)
            
            # Get public URL
            public_url = supabase.storage.from_("quiz-images").get_public_url(file_name)
            question_image.data = public_url  # Store for later insertion
            notify("✅ Image uploaded successfully!")

        except Exception as ex:
            question_image.visible = False
            question_image.src = ""
            question_image.data = None
            notify(f"❌ Error uploading image: {ex}")
            page.update()

    upload_btn = ft.ElevatedButton(
        "Upload Image",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=handle_pick_image,
    )

    # ---------- Fields ----------
    question_field = ft.TextField(label="Question", multiline=True, min_lines=3, width=600)
    answer_field = ft.TextField(label="Answer", width=600)
    category_field = ft.Dropdown(
        label="Category",
        options=[ft.dropdown.Option(c) for c in categories],
        width=300,
        value=selected_category,
    )
    topic_field = ft.TextField(label="Topic", width=300, value=selected_topic)
    submitted_by_field = ft.TextField(label="Submitted by", width=300, value=submitted_by)
    feedback = ft.Text(size=14)

    # ---------- Add Question Logic ----------
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
                "image_url": question_image.data if question_image.visible else None,
                "upvotes": 0,
                "downvotes": 0,
            }).execute()

            # Clear only question and answer
            question_field.value = ""
            answer_field.value = ""
            question_image.src = ""
            question_image.visible = False
            question_image.data = None

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
                ft.Divider(thickness=1),
                question_field,
                answer_field,
                upload_btn,
                question_image,
                ft.Row(
                    [category_field, topic_field],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
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

    layout = ft.Container(
        content=form_card,
        expand=True,
        alignment=ft.Alignment(x=0, y=0),
        padding=40,
    )

    return layout