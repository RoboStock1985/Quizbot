import flet as ft

from db import supabase
from pages.quiz_page import build_quiz_page
from pages.builder_page import build_builder_page
from pages.add_question_page import build_add_question_page

def main(page: ft.Page):
    page.title = "Trivia on Tap 🍺"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # ---------- Notifications ----------
    def notify(msg):
        snack = ft.SnackBar(ft.Text(msg))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # ---------- Load initial data ----------
    rows = supabase.table("questions").select("*").execute().data or []

    categories = sorted({r["category"] for r in rows if r.get("category")})
    topics = sorted({r["topic"] for r in rows if r.get("topic")})

    selected_categories = set(categories)
    selected_topics = set(topics)

    # ---------- Page container ----------
    content = ft.Column()
    page.add(content)

    # ---------- Navigation ----------
    def show_quiz(e=None):
        content.controls.clear()
        content.controls.extend(
            build_quiz_page(
                page,
                categories,
                topics,
                selected_categories,
                selected_topics,
                notify,
            )
        )
        page.update()

    def show_builder(e=None):
        content.controls.clear()
        content.controls.extend(
            build_builder_page(
                page,
                categories,
                topics,
                selected_categories,
                selected_topics,
                notify,
            )
        )
        page.update()

    def show_add_question(e=None):
        content.controls.clear()
        content.controls.extend([
            build_add_question_page(
                page,
                categories,
            )
        ])
        page.update()

    nav = ft.Row(
        [
            ft.Button("🎮 Play Quiz", on_click=show_quiz),
            ft.Button("🛠️ Quiz Builder", on_click=show_builder),
            ft.Button("➕ Add Question", on_click=show_add_question),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )

    # ---------- Initial layout ----------
    page.controls.clear()
    page.add(nav, content)

    show_quiz()  # default page

if __name__ == "__main__":
    ft.app(target=main, host="0.0.0.0", port=8080)
