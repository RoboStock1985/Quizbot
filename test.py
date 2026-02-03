import flet as ft

def main(page: ft.Page):
    tabs = ft.Tabs(
        selected_index=0,
        expand=True,
        length=3,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="Tab 1", icon=ft.Icons.SETTINGS_PHONE),
                        ft.Tab(label="Tab 2", icon=ft.Icons.SETTINGS),
                        ft.Tab(
                            label=ft.CircleAvatar(
                                foreground_image_src="https://avatars.githubusercontent.com/u/102273996?s=200&v=4",
                            ),
                        ),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(
                            content=ft.Text("This is Tab 1"),
                            alignment=ft.Alignment(x=0, y=0),
                        ),
                        ft.Container(
                            content=ft.Text("This is Tab 2"),
                            alignment=ft.Alignment(x=0, y=0),
                        ),
                        ft.Container(
                            content=ft.Text("This is Tab 3"),
                            alignment=ft.Alignment(x=0, y=0),
                        ),
                    ],
                ),
            ],
        ),
    )

    page.add(tabs)

if __name__ == "__main__":
    ft.app(target=main)
