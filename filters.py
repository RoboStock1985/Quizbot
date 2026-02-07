import flet as ft


def build_multiselect_filter(title, all_values, selected_set, page, color_map=None):
    search = ft.TextField(hint_text="Search...", dense=True, text_size=12)
    counter = ft.Text(size=12, color=ft.Colors.WHITE70)
    tags = ft.Row(spacing=6, wrap=True)
    filtered = list(all_values)

    def update_counter():
        counter.value = f"{len(selected_set)} / {len(all_values)} selected"

    def toggle(val):
        if val in selected_set:
            selected_set.remove(val)
        else:
            selected_set.add(val)
        rebuild()

    def rebuild():
        tags.controls.clear()
        for v in filtered:
            selected = v in selected_set
            bg = (
                color_map.get(v, ft.Colors.GREY)
                if selected and color_map
                else ft.Colors.GREY_800
            )
            tags.controls.append(
                ft.Container(
                    content=ft.Text(
                        v,
                        size=12,
                        color=ft.Colors.BLACK if selected else ft.Colors.WHITE,
                    ),
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    border_radius=16,
                    bgcolor=bg,
                    border=ft.border.all(1, ft.Colors.WHITE24),
                    on_click=lambda e, val=v: toggle(val),
                )
            )
        update_counter()
        page.update()

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
            ft.Row(
                [
                    ft.TextButton("Select all", on_click=select_all),
                    ft.TextButton("Deselect all", on_click=deselect_all),
                ],
                spacing=6,
            ),
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

    def toggle(val, state):
        if state:
            selected_set.add(val)
        else:
            selected_set.discard(val)
        update_counter()
        page.update()

    def rebuild():
        list_container.controls.clear()
        for value in filtered:
            list_container.controls.append(
                ft.Checkbox(
                    label=value,
                    value=value in selected_set,
                    on_change=lambda e, val=value: toggle(val, e.control.value),
                )
            )
        update_counter()
        page.update()

    def on_search(e):
        nonlocal filtered
        q = search.value.lower().strip()
        filtered = [v for v in all_values if q in v.lower()]
        rebuild()

    def select_all(e):
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
            ft.Row(
                [
                    ft.TextButton("Select all", on_click=select_all),
                    ft.TextButton("Deselect all", on_click=deselect_all),
                ],
                spacing=6,
            ),
            search,
            list_container,
        ],
        spacing=8,
        width=260,
    )
