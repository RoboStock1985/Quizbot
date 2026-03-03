import flet as ft
from db import supabase
from pages.quiz_page import build_quiz_page
from pages.builder_page import build_builder_page
from pages.add_question_page import build_add_question_page

def main(page: ft.Page):

    page.title = "Trivia on Tap 🍺"
    page.theme_mode = ft.ThemeMode.DARK
    # page.dark_theme = ft.Theme(color_scheme_seed=ft.Colors.BLACK)
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    def notify(msg):
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    # ---------- Load metadata ONLY ----------
    data = supabase.table("questions").select("category, topic").execute().data or []
    categories = sorted({r["category"] for r in data if r.get("category")})
    topics = sorted({r["topic"] for r in data if r.get("topic")})

    selected_categories = set(categories)
    selected_topics = set(topics)

    content = ft.Column(expand=True)

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
        content.controls.append(
            build_add_question_page(page, categories)
        )
        page.update()

    nav = ft.Row(
        [
            ft.ElevatedButton("🎮 Play Quiz", on_click=show_quiz),
            ft.ElevatedButton("🛠️ Quiz Builder", on_click=show_builder),
            ft.ElevatedButton("➕ Add Question", on_click=show_add_question),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20,
    )

    page.add(nav, content)
    show_quiz()

if __name__ == "__main__":
    ft.app(target=main, host="0.0.0.0", port=8080)
