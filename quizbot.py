import os
import random
import difflib
import string
import flet as ft
from supabase import create_client, Client
from dotenv import load_dotenv

# ================= ENV =================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials missing")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= CONFIG =================
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

# ================= HELPERS =================
def normalise(text):
    return text.lower().strip().translate(str.maketrans("", "", string.punctuation))

def fuzzy_match(user, correct):
    return difflib.SequenceMatcher(None, user, correct).ratio() >= FUZZY_THRESHOLD

def wrap_text(text, length=WRAP_LENGTH):
    if not text:
        return ""
    words, lines, line = str(text).split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 <= length:
            line += (" " if line else "") + w
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return "\n".join(lines)

def safe_data(field, default=""):
    return field if field else default

# ================= FILTER BUILDERS =================
def build_multiselect_filter(title, all_values, selected_set, page, color_map=None):
    search = ft.TextField(hint_text="Search...", dense=True, text_size=12)
    counter = ft.Text(size=12, color=ft.Colors.WHITE70)
    tags = ft.Row(spacing=6, wrap=True)
    filtered = list(all_values)

    def update_counter():
        counter.value = f"{len(selected_set)} / {len(all_values)} selected"

    def rebuild():
        tags.controls.clear()
        for v in filtered:
            selected = v in selected_set
            bg = color_map.get(v, ft.Colors.GREY) if selected and color_map else (ft.Colors.GREY_800 if not selected else ft.Colors.GREY)
            tags.controls.append(
                ft.Container(
                    content=ft.Text(v, size=12, color=ft.Colors.BLACK if selected else ft.Colors.WHITE),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    border_radius=16,
                    bgcolor=bg,
                    border=ft.border.all(1, ft.Colors.WHITE24),
                    on_click=lambda e, val=v: toggle(val),
                )
            )
        update_counter()
        page.update()

    def toggle(val):
        if val in selected_set:
            selected_set.remove(val)
        else:
            selected_set.add(val)
        rebuild()

    def on_search(e):
        nonlocal filtered
        q = search.value.lower().strip()
        filtered = [v for v in all_values if q in v.lower()]
        rebuild()

    def select_all(e):
        selected_set.clear()
        selected_set.update(all_values)
        rebuild()

    def deselect_all(e):
        selected_set.clear()
        rebuild()

    search.on_change = on_search
    rebuild()

    return ft.Column(
        [
            ft.Text(title, weight=ft.FontWeight.BOLD),
            counter,
            ft.Row([ft.TextButton("Select all", on_click=select_all),
                    ft.TextButton("Deselect all", on_click=deselect_all)], spacing=6),
            search,
            tags,
        ],
        spacing=8,
        width=260,
    )

def build_topic_checkbox_filter(title, all_values, selected_set, page, height=300):
    search = ft.TextField(hint_text="Search...", dense=True, text_size=12)
    list_container = ft.ListView(spacing=4, height=height)
    counter = ft.Text(size=12, color=ft.Colors.WHITE70)
    filtered = list(all_values)

    def update_counter():
        counter.value = f"{len(selected_set)} / {len(all_values)} selected"

    def rebuild():
        list_container.controls.clear()
        for value in filtered:
            checked = value in selected_set
            list_container.controls.append(
                ft.Checkbox(label=value, value=checked, on_change=lambda e, val=value: toggle(val, e.control.value))
            )
        update_counter()
        page.update()

    def toggle(val, state):
        if state:
            selected_set.add(val)
        else:
            selected_set.discard(val)
        update_counter()
        page.update()

    def select_all(e):
        selected_set.update(all_values)
        rebuild()

    def deselect_all(e):
        selected_set.clear()
        rebuild()

    def on_search(e):
        nonlocal filtered
        q = search.value.lower().strip()
        filtered = [v for v in all_values if q in v.lower()]
        rebuild()

    search.on_change = on_search
    rebuild()

    return ft.Column(
        [
            ft.Text(title, weight=ft.FontWeight.BOLD),
            counter,
            ft.Row([ft.TextButton("Select all", on_click=select_all),
                    ft.TextButton("Deselect all", on_click=deselect_all)], spacing=6),
            search,
            list_container,
        ],
        spacing=8,
        width=260,
    )

# ================= APP =================
def main(page: ft.Page):
    page.title = "Trivia on Tap 🍺"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # ---------- Helpers ----------
    def notify(msg):
        snack = ft.SnackBar(ft.Text(msg))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # ---------- Load DB ----------
    try:
        res = supabase.table("questions").select("*").execute()
        rows = res.data if res.data else []
    except Exception as e:
        page.add(ft.Text(f"❌ Error loading questions: {e}", color=ft.Colors.RED))
        return

    categories = sorted({r.get("category") for r in rows if r.get("category")})
    topics = sorted({r.get("topic") for r in rows if r.get("topic")})

    selected_categories, selected_topics = set(categories), set(topics)

    # ---------- Page container ----------
    current_page = ft.Ref[ft.Column]()
    page_container = ft.Column()
    current_page.current = page_container

    # ---------- Page Switch ----------
    def show_quiz_page(e=None):
        current_page.current.controls.clear()
        current_page.current.controls.extend(build_quiz_page())
        page.update()

    def show_builder_page(e=None):
        current_page.current.controls.clear()
        current_page.current.controls.extend(build_builder_page())
        page.update()

    nav = ft.Row([
        ft.ElevatedButton("🎮 Play Quiz", on_click=show_quiz_page),
        ft.ElevatedButton("🛠️ Quiz Builder", on_click=show_builder_page)
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)

    page.add(nav, current_page.current)

    # ================== QUIZ PAGE ==================
    def build_quiz_page():
        # Filters
        category_filter = build_multiselect_filter("Categories", categories, selected_categories, page, CATEGORY_COLORS)
        topic_filter = build_topic_checkbox_filter("Topics", topics, selected_topics, page)
        max_questions = ft.Dropdown(
            label="Max Questions",
            options=[ft.dropdown.Option(str(x)) for x in [1,10,20,50,100]] + [ft.dropdown.Option("All")],
            value="All",
            width=200
        )

        # State
        asked_ids, current_q = set(), {}
        score, voted_set = {"correct":0, "total":0}, set()
        question_pool = []

        # ---------- Quiz UI Elements ----------
        progress = ft.ProgressBar(width=600, value=0.0)
        progress_label = ft.Text("", size=14)
        question_text = ft.Text(size=30, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        category_box = ft.Container(padding=6, border_radius=6)
        submitted_by = ft.Text(size=14, italic=True)
        answer = ft.TextField(label="Your answer", width=600)
        feedback = ft.Text(size=16)
        submit_btn = ft.ElevatedButton("Submit")
        next_btn = ft.TextButton("Next", visible=False)
        final_score = ft.Text(size=42, weight=ft.FontWeight.BOLD, visible=False)
        upvote_btn = ft.IconButton(icon=ft.Icons.THUMB_UP, icon_color=ft.Colors.GREEN)
        downvote_btn = ft.IconButton(icon=ft.Icons.THUMB_DOWN, icon_color=ft.Colors.RED)
        vote_label = ft.Text("")
        voting_row = ft.Row([upvote_btn, downvote_btn, vote_label], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

        quiz_block = ft.Column(
            [
                progress,
                progress_label,
                ft.Row([question_text, category_box], alignment=ft.MainAxisAlignment.CENTER),
                submitted_by,
                answer,
                submit_btn,
                feedback,
                voting_row,
                next_btn,
                final_score
            ],
            spacing=10,
            visible=False,
            width=900,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # ---------- Quiz Logic ----------
        def get_questions():
            query = supabase.table("questions").select("*")
            if selected_categories and len(selected_categories) != len(categories):
                query = query.in_("category", list(selected_categories))
            if selected_topics and len(selected_topics) != len(topics):
                query = query.in_("topic", list(selected_topics))
            limit = None
            if max_questions.value != "All":
                try: limit = int(max_questions.value)
                except: pass
            try:
                result = query.limit(limit if limit else 10000).execute()
                data = result.data or []
                random.shuffle(data)
                if limit: data = data[:limit]
                return data
            except Exception as e:
                notify(f"Error loading questions: {e}")
                return []

        def show_vote_stats(q):
            ups, downs = q.get("upvotes",0), q.get("downvotes",0)
            total = ups + downs
            if total == 0:
                vote_label.value = "No votes yet"
            else:
                percent = f"{int((ups/total)*100)}%"
                vote_label.value = f"👍 {ups} / 👎 {downs} ({percent} positive)"
            page.update()

        def vote(val):
            qid = current_q.get("question_id")
            if not qid or qid in voted_set: 
                notify("Already voted") 
                return
            voted_set.add(qid)
            field = "upvotes" if val==1 else "downvotes"
            try:
                supabase.table("questions").update({field: current_q.get(field,0)+1}).eq("question_id", qid).execute()
                current_q[field] = current_q.get(field,0)+1
                show_vote_stats(current_q)
                notify("Thanks! 👍" if val==1 else "Thanks! 👎")
                upvote_btn.disabled=True
                downvote_btn.disabled=True
                page.update()
            except Exception as e:
                notify(f"Error submitting vote: {e}")

        upvote_btn.on_click = lambda e: vote(1)
        downvote_btn.on_click = lambda e: vote(-1)

        def load_question():
            available = [q for q in question_pool if q.get("question_id") not in asked_ids]
            if not available:
                final_score.value = f"Final Score: {score['correct']} / {score['total']}"
                final_score.visible=True
                quiz_block.update()
                return
            q = random.choice(available)
            asked_ids.add(q.get("question_id"))
            current_q.clear()
            current_q.update(q)

            question_text.value = wrap_text(safe_data(q.get("question")))
            category_box.content = ft.Text(safe_data(q.get("category")), weight=ft.FontWeight.BOLD)
            category_box.bgcolor = CATEGORY_COLORS.get(q.get("category"), ft.Colors.GREY)

            answer.value=""
            answer.disabled=False
            feedback.value=""
            next_btn.visible=False
            final_score.visible=False
            upvote_btn.disabled=False
            downvote_btn.disabled=False

            progress.value = len(asked_ids)/len(question_pool) if question_pool else 0
            progress_label.value=f"Question {len(asked_ids)} of {len(question_pool)}"
            submitted_by.value = f"Submitted by: {safe_data(q.get('submitted_by'))}"
            show_vote_stats(q)
            page.update()

        def check_answer(e):
            user, correct = normalise(answer.value), normalise(current_q.get("answer",""))
            ok = user==correct or fuzzy_match(user, correct)
            score["total"] += 1
            if ok:
                score["correct"] +=1
                feedback.value = "✅ Correct!" if user==correct else f"✅ Close enough — {current_q['answer']}"
                feedback.color = ft.Colors.GREEN
            else:
                feedback.value = f"❌ Wrong — {current_q['answer']}"
                feedback.color = ft.Colors.RED
            answer.disabled=True
            next_btn.visible=True
            page.update()

        def start_quiz(e=None):
            nonlocal question_pool
            question_pool = get_questions()
            if not question_pool:
                notify("No matching questions")
                return
            asked_ids.clear()
            score.update(correct=0,total=0)
            quiz_block.visible=True
            load_question()

        submit_btn.on_click = check_answer
        next_btn.on_click = lambda e: load_question()

        play_btn = ft.ElevatedButton("▶️ Start Quiz", on_click=start_quiz)

        # Layout
        left_sidebar = ft.Column([ft.Text("Filters", weight=ft.FontWeight.BOLD), category_filter, topic_filter, max_questions], spacing=10)
        return [
            ft.Row([
                ft.Container(width=280,padding=10,content=left_sidebar),
                ft.VerticalDivider(width=1),
                ft.Container(expand=True,padding=10,content=ft.Column([play_btn, quiz_block],spacing=10))
            ])
        ]

    # ================== BUILDER PAGE ==================
    def build_builder_page():
        # Filters
        category_filter = build_multiselect_filter("Categories", categories, selected_categories, page, CATEGORY_COLORS)
        topic_filter = build_topic_checkbox_filter("Topics", topics, selected_topics, page)

        # Question list
        question_list = ft.Column(spacing=8, scroll=True)
        builder_questions = []

        # Load questions
        def load_questions(e):
            nonlocal builder_questions
            query = supabase.table("questions").select("*")
            if selected_categories and len(selected_categories)!=len(categories):
                query = query.in_("category", list(selected_categories))
            if selected_topics and len(selected_topics)!=len(topics):
                query = query.in_("topic", list(selected_topics))
            builder_questions = query.execute().data or []
            rebuild()

        def rebuild():
            question_list.controls.clear()
            for i,q in enumerate(builder_questions):
                q_card = build_question_card(i,q)
                question_list.controls.append(q_card)
            page.update()

        def build_question_card(idx,q):
            q_field = ft.TextField(label=f"Q{idx+1}", value=q.get("question",""), multiline=True, width=600)
            a_field = ft.TextField(label="Answer", value=q.get("answer",""), multiline=True, width=400)
            up_btn = ft.IconButton(icon=ft.Icons.ARROW_UPWARD, tooltip="Move up", on_click=lambda e: move(idx,-1))
            down_btn = ft.IconButton(icon=ft.Icons.ARROW_DOWNWARD, tooltip="Move down", on_click=lambda e: move(idx,1))
            def on_change(e): q["question"]=q_field.value; q["answer"]=a_field.value
            q_field.on_change=on_change
            a_field.on_change=on_change
            return ft.Container(content=ft.Row([ft.Text(f"{idx+1}. "),q_field,a_field,up_btn,down_btn]), border=ft.border.all(1,ft.Colors.WHITE24), border_radius=6, padding=10)

        def move(idx,delta):
            new_idx = idx+delta
            if 0<=new_idx<len(builder_questions):
                builder_questions[idx], builder_questions[new_idx] = builder_questions[new_idx], builder_questions[idx]
                rebuild()

        def export_pdf(e):
            import fpdf
            if not builder_questions:
                notify("No questions to export")
                return
            pdf_q = fpdf.FPDF()
            pdf_q.add_page()
            pdf_q.set_font("Helvetica", size=12)
            pdf_q.cell(0,10,"QUIZ QUESTIONS",ln=True,align="C")
            pdf_q.ln(8)
            for i,q in enumerate(builder_questions,1):
                pdf_q.multi_cell(0,8,f"{i}. {q['question']}\n")
            pdf_q.output("quiz_questions.pdf")

            pdf_a = fpdf.FPDF()
            pdf_a.add_page()
            pdf_a.set_font("Helvetica",size=12)
            pdf_a.cell(0,10,"QUIZ ANSWERS",ln=True,align="C")
            pdf_a.ln(8)
            for i,q in enumerate(builder_questions,1):
                pdf_a.multi_cell(0,8,f"{i}. {q['question']}\nAnswer: {q['answer']}\n")
            pdf_a.output("quiz_answers.pdf")
            notify("PDFs generated!")

        load_btn = ft.ElevatedButton("📥 Load Filtered Questions", width=250, on_click=load_questions)
        export_btn = ft.ElevatedButton("📄 Export to PDF", width=250, on_click=export_pdf)

        left_sidebar = ft.Column([ft.Text("Filters", weight=ft.FontWeight.BOLD), category_filter, topic_filter], spacing=10)
        builder_content = ft.Column([ft.Row([load_btn,export_btn]), question_list], spacing=10)

        return [
            ft.Row([
                ft.Container(width=280,padding=10,content=left_sidebar),
                ft.VerticalDivider(width=1),
                ft.Container(expand=True,padding=10,content=builder_content)
            ])
        ]

    # Show quiz page by default
    show_quiz_page()

# ================= RUN =================
if __name__ == "__main__":
    ft.app(target=main, host="0.0.0.0", port=8080)
