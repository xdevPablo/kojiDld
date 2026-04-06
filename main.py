import flet as ft
from core import YoutubeDownloaderCore
import urllib.parse

def main(page: ft.Page):
    # --- WINDOW CONFIGURATION ---
    page.title = "kojiDld"
    page.window.icon = "logo.png"
    page.window.width = 800 
    page.window.height = 780
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 40
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = "#0A0A0A"
    page.scroll = ft.ScrollMode.AUTO

    # --- BIG LOGO ---
    header_image = ft.Image(
        src="logo.png",
        width=250, # Reduzi levemente para caber o novo painel sem apertar
        height=250,
        fit=ft.BoxFit.CONTAIN,
    )

    header_view = ft.Column([
        header_image
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # --- DYNAMIC BATCH INPUTS LOGIC ---
    url_inputs = [] 
    url_container = ft.Column(spacing=10)

    def generate_inputs(count):
        url_inputs.clear()
        url_container.controls.clear()
        for i in range(count):
            tf = ft.TextField(
                label=f"Target URL {i+1}" if count > 1 else "Target URL (YouTube, TikTok, Instagram...)",
                hint_text="Paste the link here...",
                prefix_icon=ft.Icons.LINK,
                border_radius=10,
                expand=True,
                border_color="#262626",
                focused_border_color="#DC2626"
            )
            url_inputs.append(tf)
            url_container.controls.append(tf)
        page.update()

    def on_batch_change(e):
        val = str(batch_dropdown.value)
        count = int(val.split(" ")[0])
        generate_inputs(count)

    batch_dropdown = ft.Dropdown(
        label="Batch Mode",
        options=[
            ft.dropdown.Option("1 Link"),
            ft.dropdown.Option("3 Links"),
            ft.dropdown.Option("5 Links"),
            ft.dropdown.Option("10 Links"),
        ],
        value="1 Link",
        width=130,
        border_radius=10,
        border_color="#262626",
        on_select=on_batch_change  # type: ignore  
    )

    format_dropdown = ft.Dropdown(
        label="Format",
        options=[
            ft.dropdown.Option("Video (MP4)"),
            ft.dropdown.Option("Audio (MP3)"),
        ],
        value="Video (MP4)",
        width=140,
        border_radius=10,
        border_color="#262626"
    )

    quality_dropdown = ft.Dropdown(
        label="Quality",
        options=[
            ft.dropdown.Option("High (Default)"),
            ft.dropdown.Option("Medium (720p)"),
            ft.dropdown.Option("Low (Eco)"),
        ],
        value="High (Default)",
        width=160,
        border_radius=10,
        border_color="#262626"
    )

    settings_row = ft.Row(
        [batch_dropdown, format_dropdown, quality_dropdown], 
        alignment=ft.MainAxisAlignment.CENTER
    )

    input_card = ft.Container(
        content=ft.Column([settings_row, ft.Container(height=5), url_container]),
        bgcolor="#171717",
        padding=20,
        border_radius=15,
        border=ft.Border(
            top=ft.BorderSide(1, "#262626"), right=ft.BorderSide(1, "#262626"),
            bottom=ft.BorderSide(1, "#262626"), left=ft.BorderSide(1, "#262626")
        ),
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=20, color=ft.Colors.with_opacity(0.4, "black"))
    )

    generate_inputs(1)

    # --- NOVO DASHBOARD DE PROGRESSO ---
    progress_bar = ft.ProgressBar(color="#DC2626", bgcolor="#262626", value=0.0)
    status_text = ft.Text("System Standby", color="#737373", weight=ft.FontWeight.W_600)
    percent_text = ft.Text("0%", color="#F5F5F5", size=30, weight=ft.FontWeight.W_900)
    details_text = ft.Text("Size: -- MB | Speed: -- | ETA: --", color="#A3A3A3", size=13)

    # Painel estiloso que só aparece durante a extração
    dashboard_card = ft.Container(
        content=ft.Column([
            ft.Row([status_text, percent_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            progress_bar,
            ft.Container(height=2),
            details_text
        ]),
        bgcolor="#171717",
        padding=20,
        border_radius=15,
        border=ft.Border(
            top=ft.BorderSide(1, "#262626"), right=ft.BorderSide(1, "#262626"),
            bottom=ft.BorderSide(1, "#262626"), left=ft.BorderSide(1, "#262626")
        ),
        visible=False # Escondido por padrão
    )

    def show_error(msg):
        snack = ft.SnackBar(content=ft.Text(msg, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD), bgcolor="#B91C1C")
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def on_status(msg, is_error=False):
        status_text.value = msg
        status_text.color = "#EF4444" if is_error else "#DC2626"
        if is_error:
            progress_bar.value = 0
            progress_bar.color = "#EF4444"
            unlock_ui()
        page.update()

    # O Novo motor de porcentagem recebendo a velocidade
    def on_progress(percent, eta, size_str, speed_str):
        progress_bar.value = percent
        percent_text.value = f"{int(percent * 100)}%"
        details_text.value = f"Size: {size_str}  |  Speed: {speed_str}  |  ETA: {eta}"
        page.update()

    def on_complete():
        status_text.value = "Extraction Complete."
        status_text.color = "#10B981"
        percent_text.value = "100%"
        progress_bar.value = 1.0
        progress_bar.color = "#10B981"
        details_text.value = "All files successfully saved in destination."
        unlock_ui()
        page.update()

    # NOVO RELATÓRIO DO SCANNER PROFISSIONAL
    def on_analysis(scan_data):
        scan_content = ft.Column([
            ft.ListTile(leading=ft.Icon(ft.Icons.DNS, color="#A3A3A3"), title=ft.Text("Target Host", color="#737373", size=12), subtitle=ft.Text(scan_data['domain'], color="white")),
            ft.ListTile(leading=ft.Icon(ft.Icons.ROUTER, color="#A3A3A3"), title=ft.Text("Public IP", color="#737373", size=12), subtitle=ft.Text(scan_data['ip'], color="white")),
            ft.ListTile(leading=ft.Icon(ft.Icons.STORAGE, color="#A3A3A3"), title=ft.Text("Server Architecture", color="#737373", size=12), subtitle=ft.Text(scan_data['server'], color="white")),
            ft.Container(height=15),
            ft.Container(
                content=ft.Text(f"FINAL VERDICT: {scan_data['status']}", weight=ft.FontWeight.W_900, color="white"),
                bgcolor=scan_data['color'], padding=15, border_radius=8, alignment=ft.alignment.Alignment(0,0)
            )
        ], width=450, tight=True, spacing=0)

        dlg = ft.AlertDialog(
            title=ft.Row([ft.Icon(ft.Icons.SECURITY, color="#DC2626"), ft.Text("Forensic Security Report", color="white")]),
            content=scan_content,
            bgcolor="#171717",
            shape=ft.RoundedRectangleBorder(radius=12),
            on_dismiss=lambda e: unlock_ui()
        )
        page.overlay.append(dlg)
        dlg.open = True
        status_text.value = "Analysis complete."
        page.update()

    core = YoutubeDownloaderCore(on_status, on_progress, on_complete, on_analysis)

    def lock_ui():
        btn_download.disabled = True
        btn_analyze.disabled = True
        batch_dropdown.disabled = True
        format_dropdown.disabled = True
        quality_dropdown.disabled = True
        for tf in url_inputs:
            tf.disabled = True
        
        # Revela o Dashboard e formata as cores
        dashboard_card.visible = True
        progress_bar.color = "#DC2626"
        percent_text.value = "0%"
        details_text.value = "Preparing connection..."
        page.update()

    def unlock_ui():
        btn_download.disabled = False
        btn_analyze.disabled = False
        batch_dropdown.disabled = False
        format_dropdown.disabled = False
        quality_dropdown.disabled = False
        for tf in url_inputs:
            tf.disabled = False
        page.update()

    def is_valid_url(url):
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except ValueError:
            return False

    def click_download(e):
        urls = [str(tf.value).strip() for tf in url_inputs if tf.value and str(tf.value).strip()]
        
        if not urls:
            show_error("INPUT ERROR: Please insert at least one link.")
            return
            
        for u in urls:
            if not is_valid_url(u):
                show_error(f"INPUT ERROR: Invalid link detected ({u[:30]}...).")
                return

        lock_ui()
        core.start_download(urls, quality_dropdown.value, format_dropdown.value)

    def click_analyze(e):
        urls = [str(tf.value).strip() for tf in url_inputs if tf.value and str(tf.value).strip()]
        
        if not urls:
            show_error("INPUT ERROR: Please insert a link for scanning.")
            return
            
        first_url = urls[0]
        if not is_valid_url(first_url):
            show_error("INPUT ERROR: Invalid link for scanning.")
            return
            
        if len(urls) > 1:
            show_error("WARNING: The Scanner verifies only the first link in Batch Mode.")
            
        lock_ui()
        status_text.value = "Establishing secure connection to server..."
        core.start_analysis(first_url)

    btn_download = ft.ElevatedButton(
        "START DOWNLOAD", 
        icon=ft.Icons.DOWNLOAD_ROUNDED, 
        on_click=click_download,
        style=ft.ButtonStyle(
            bgcolor="#B91C1C", color=ft.Colors.WHITE, padding=20, shape=ft.RoundedRectangleBorder(radius=8)
        )
    )
    
    btn_analyze = ft.ElevatedButton(
        "SECURITY SCAN", 
        icon=ft.Icons.SHIELD_ROUNDED, 
        on_click=click_analyze,
        style=ft.ButtonStyle(
            bgcolor="#262626", color=ft.Colors.WHITE, padding=20, shape=ft.RoundedRectangleBorder(radius=8)
        )
    )

    btn_folder = ft.TextButton(
        "Open Destination Folder", 
        icon=ft.Icons.FOLDER_OPEN_ROUNDED,
        icon_color="#737373",
        on_click=lambda e: core.open_download_folder()
    )

    page.add(
        header_view,
        input_card,
        ft.Container(height=10),
        ft.Row([btn_analyze, btn_download], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(height=5),
        btn_folder,
        dashboard_card # O novo painel gigante entra aqui embaixo
    )

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")