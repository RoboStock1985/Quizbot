import random
import flet as ft
from db import supabase
from config import CATEGORY_COLORS
from helpers import normalise, fuzzy_match, wrap_text, safe_data
from filters import build_multiselect_filter, build_topic_checkbox_filter


def build_quiz_page(
    page,
    categories,
    topics,
    selected_categories,
    selected_topics,
    notify,
):

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

    # ---------------- State ----------------
    asked_ids = set()
    score = {"correct": 0, "total": 0}
    voted_set = set()
    current_q = {}
    question_pool = []

    # ---------------- Quiz UI ----------------
    progress = ft.ProgressBar(width=600)
    progress_label = ft.Text()
    question_text = ft.Text(
        size=30,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
    )
    question_container = ft.Container(
        content=question_text,
        height=120,
        width=600,
        alignment=ft.Alignment(0, 0),
    )

    question_image = ft.Image(src="", width=600, height=350, fit="contain", visible=False)
    image_container = ft.Container(
        content=question_image,
        height=350,
        width=600,
        alignment=ft.Alignment(0, 0),
    )

    category_box = ft.Container(padding=6, border_radius=6)
    submitted_by = ft.Text(italic=True)
    answer = ft.TextField(label="Your answer", width=600)
    feedback = ft.Text(size=16, height=30)
    submit_btn = ft.ElevatedButton("Submit")
    next_btn = ft.TextButton("Next", visible=False)
    final_score = ft.Text(size=42, weight=ft.FontWeight.BOLD, visible=False)

    upvote_btn = ft.IconButton(icon=ft.Icons.THUMB_UP, icon_color=ft.Colors.GREEN)
    downvote_btn = ft.IconButton(icon=ft.Icons.THUMB_DOWN, icon_color=ft.Colors.RED)
    vote_label = ft.Text()
    voting_row = ft.Row([upvote_btn, downvote_btn, vote_label], alignment=ft.MainAxisAlignment.CENTER)

    start_quiz_btn = ft.ElevatedButton("▶️ Start New Quiz", visible=False)
    initial_start_btn = ft.ElevatedButton("▶️ Start New Quiz", visible=True)

    quiz_block = ft.Column(
        [
            progress,
            progress_label,
            ft.Row([category_box], alignment=ft.MainAxisAlignment.CENTER),
            question_container,
            image_container,
            submitted_by,
            answer,
            submit_btn,
            feedback,
            voting_row,
            next_btn,
            final_score,
            start_quiz_btn,
        ],
        visible=False,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
    )

    # ---------------- Helper Functions ----------------
    def notify_vote(msg):
        notify(msg)

    def vote(val):
        qid = current_q.get("question_id")
        if not qid:
            notify_vote("No active question")
            return
        if qid in voted_set:
            notify_vote("You already voted on this question")
            return

        field = "upvotes" if val == 1 else "downvotes"
        try:
            supabase.table("questions").update(
                {field: current_q.get(field, 0) + 1}
            ).eq("question_id", qid).execute()

            current_q[field] = current_q.get(field, 0) + 1
            voted_set.add(qid)

            upvote_btn.disabled = True
            downvote_btn.disabled = True

            show_vote_stats(current_q)
            notify_vote("Thanks for voting 👍" if val == 1 else "Vote recorded 👎")
            page.update()
        except Exception as e:
            notify_vote(f"Vote failed: {e}")

    upvote_btn.on_click = lambda e: vote(1)
    downvote_btn.on_click = lambda e: vote(-1)

    # ---------------- Optimized: Lazy question fetch ----------------
    def get_questions():
        query = supabase.table("questions").select("*")

        if selected_categories and len(selected_categories) != len(categories):
            query = query.in_("category", list(selected_categories))
        if selected_topics and len(selected_topics) != len(topics):
            query = query.in_("topic", list(selected_topics))

        try:
            limit = int(max_questions.value)
        except ValueError:
            limit = 100  # default

        fetch_limit = max(limit * 3, 100)  # fetch extra for randomness
        query = query.limit(fetch_limit)

        result = query.execute().data or []

        random.shuffle(result)
        return result[:limit]

    def show_vote_stats(q):
        ups, downs = q.get("upvotes", 0), q.get("downvotes", 0)
        total = ups + downs
        vote_label.value = "No votes yet" if total == 0 else f"👍 {ups} / 👎 {downs}"
        page.update()

    # ---------------- Quiz Logic ----------------
    def load_question():
        available = [q for q in question_pool if q["question_id"] not in asked_ids]
        if not available:
            final_score.value = f"Final Score: {score['correct']} / {score['total']}"
            final_score.visible = True
            start_quiz_btn.visible = True
            page.update()
            return

        q = random.choice(available)
        asked_ids.add(q["question_id"])
        current_q.clear()
        current_q.update(q)

        upvote_btn.disabled = False
        downvote_btn.disabled = False

        question_text.value = wrap_text(q.get("question", ""))
        if q.get("image_url"):
            question_image.src = q["image_url"]
            question_image.visible = True
        else:
            question_image.src = ""
            question_image.visible = False

        category_box.content = ft.Text(q.get("category",""), weight=ft.FontWeight.BOLD)
        category_box.bgcolor = CATEGORY_COLORS.get(q.get("category"), ft.Colors.GREY)

        answer.value = ""
        answer.disabled = False
        feedback.value = ""
        next_btn.visible = False
        final_score.visible = False
        start_quiz_btn.visible = False

        progress.value = len(asked_ids) / len(question_pool)
        progress_label.value = f"Question {len(asked_ids)} of {len(question_pool)}"
        submitted_by.value = f"Submitted by: {safe_data(q.get('submitted_by'))}"

        show_vote_stats(q)
        page.update()

    def check_answer(e):
        user = normalise(answer.value)
        correct = normalise(current_q.get("answer",""))
        ok = user == correct or fuzzy_match(user, correct)

        score["total"] += 1
        if ok:
            score["correct"] += 1
            feedback.value = "✅ Correct!"
            feedback.color = ft.Colors.GREEN
        else:
            feedback.value = f"❌ Wrong — {current_q.get('answer','')}"
            feedback.color = ft.Colors.RED

        answer.disabled = True
        next_btn.visible = True
        page.update()

    def start_quiz(e):
        nonlocal question_pool
        question_pool = get_questions()
        if not question_pool:
            notify("No matching questions")
            return
        asked_ids.clear()
        score.update(correct=0, total=0)
        initial_start_btn.visible = False
        quiz_block.visible = True
        load_question()

    submit_btn.on_click = check_answer
    next_btn.on_click = lambda e: load_question()
    initial_start_btn.on_click = start_quiz
    start_quiz_btn.on_click = start_quiz

    # ---------------- Filter Sidebar ----------------
    filters_visible = True
    def toggle_filters(e):
        nonlocal filters_visible
        filters_visible = not filters_visible
        filters_container.visible = filters_visible
        page.update()

    filters_container = ft.Container(
        width=280,
        padding=10,
        bgcolor=ft.Colors.BLACK,
        alignment=ft.Alignment(-1, -1),
        content=ft.Column(
            [
                ft.Row([
                    ft.Text("Filters", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ]),
                ft.Container(height=25),
                max_questions,
                category_filter,
                topic_filter,
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    show_filters_btn = ft.FloatingActionButton(
        icon=ft.Icons.FILTER_LIST,
        on_click=toggle_filters,
        tooltip="Show/Hide Filters",
    )

    # ---------------- Layout ----------------
    return [
        ft.Row(
            [
                ft.Stack(
                    [
                        filters_container,
                        ft.Container(
                            content=show_filters_btn,
                            alignment=ft.Alignment(1, -1),  # top-right corner of filters
                            padding=ft.Padding(5, 0, 0, 5),
                        ),
                    ],
                ),
                ft.VerticalDivider(width=2),
                ft.Container(
                    expand=True,
                    padding=10,
                    alignment=ft.Alignment(0, -1),
                    content=ft.Column(
                        [
                            initial_start_btn,
                            quiz_block,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    ]