"""Shared Streamlit theme helpers for the UI layer."""

from __future__ import annotations

import streamlit as st


def render_navigation_link(container, page_path: str, label: str, icon: str, help_text: str) -> None:
    """Render a page link with a text fallback."""
    link_label = f"{icon} {label}"
    if hasattr(container, "page_link"):
        container.page_link(page_path, label=link_label, use_container_width=True, help=help_text)
    else:
        container.markdown(f"**{link_label}**  \n{help_text}")


def render_sidebar_navigation() -> None:
    """Render the single sidebar navigation block used across the app."""
    st.sidebar.markdown("#### 🧭 Navigation")
    render_navigation_link(st.sidebar, "app.py", "Executive Dashboard", "🏠", "Strategische Übersicht und Management-KPIs")
    render_navigation_link(st.sidebar, "pages/Stammdaten_Management.py", "Stammdaten Management", "🛠️", "Team-, Produkt- und Komponentendaten")
    render_navigation_link(st.sidebar, "pages/Projekt_Allocation.py", "Projekt-Allocation", "📅", "Kapazitäten und Allokationen")
    render_navigation_link(st.sidebar, "pages/Finanzielle_Verwaltung.py", "Finanzielle Verwaltung", "💰", "Budget und Kosten")
    st.sidebar.markdown("---")


def get_colors(dark_mode: bool = False) -> dict[str, str]:
    """Return the shared light palette; `dark_mode` is ignored for compatibility."""
    return {
        "primary": "#009999",
        "primary_dark": "#007777",
        "background": "#ffffff",
        "surface": "#f8f9fa",
        "surface_light": "#e6f7ff",
        "text": "#333333",
        "text_secondary": "#666666",
        "border": "#e0e0e0",
        "success": "#52c41a",
        "warning": "#fa8c16",
        "error": "#ff4d4f",
        "info": "#1890ff",
    }


def load_theme(dark_mode: bool = False) -> None:
    """Inject the shared light executive theme into the current Streamlit page."""
    colors = get_colors()
    st.markdown(
        f"""
<style>
    :root {{
        --primary: {colors['primary']};
        --primary-dark: {colors['primary_dark']};
        --background: {colors['background']};
        --surface: {colors['surface']};
        --surface-light: {colors['surface_light']};
        --text: {colors['text']};
        --text-secondary: {colors['text_secondary']};
        --border: {colors['border']};
        --success: {colors['success']};
        --warning: {colors['warning']};
        --error: {colors['error']};
        --info: {colors['info']};
    }}

    body {{
        background-color: {colors['background']} !important;
        color: {colors['text']} !important;
    }}

    .main {{
        background-color: {colors['background']} !important;
    }}

    [data-testid="stSidebarNav"],
    [data-testid="stSidebarNavSeparator"] {{
        display: none !important;
    }}

    .main-header {{
        font-size: 3rem !important;
        color: {colors['primary']} !important;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 700;
    }}

    .metric-card {{
        background: linear-gradient(135deg, {colors['surface_light']} 0%, {colors['surface']} 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid {colors['primary']};
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
        color: {colors['text']};
    }}

    .metric-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }}

    .critical-alert {{
        background: linear-gradient(135deg, {colors['surface']} 0%, {colors['surface_light']} 100%);
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 5px solid {colors['info']};
        margin: 0.8rem 0;
        box-shadow: 0 3px 5px rgba(0, 0, 0, 0.15);
        color: {colors['text']} !important;
    }}

    .critical-alert h4, .critical-alert p, .critical-alert b {{
        color: {colors['text']} !important;
    }}

    .section-header {{
        color: {colors['primary']};
        border-bottom: 2px solid {colors['primary']};
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }}

    .stButton button {{
        background: linear-gradient(135deg, {colors['primary']} 0%, {colors['primary_dark']} 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }}

    .stButton button:hover {{
        background: linear-gradient(135deg, {colors['primary_dark']} 0%, #005555 100%);
        color: white;
    }}

    .delete-btn {{
        background: linear-gradient(135deg, {colors['error']} 0%, #ff7875 100%) !important;
    }}

    .delete-btn:hover {{
        background: linear-gradient(135deg, #ff7875 0%, {colors['error']} 100%) !important;
    }}

    .edit-btn {{
        background: linear-gradient(135deg, {colors['warning']} 0%, #ffa940 100%) !important;
    }}

    .edit-btn:hover {{
        background: linear-gradient(135deg, #ffa940 0%, {colors['warning']} 100%) !important;
    }}

    .product-section {{
        background: linear-gradient(135deg, {colors['primary']} 0%, {colors['primary_dark']} 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }}

    .product-card {{
        background: {colors['surface']};
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        color: {colors['text']};
    }}

    .product-card-header {{
        background: linear-gradient(135deg, {colors['primary']} 0%, {colors['primary_dark']} 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: -1.5rem -1.5rem 1rem -1.5rem;
        font-size: 1.3rem;
        font-weight: 700;
    }}

    .component-item {{
        background: {colors['surface_light']};
        padding: 1rem;
        margin: 0.8rem 0;
        border-left: 4px solid {colors['primary']};
        border-radius: 5px;
        color: {colors['text']};
    }}

    .responsible-item {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.7rem 0;
        background: {colors['surface_light']};
        padding: 0.7rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        color: {colors['text']};
    }}

    .responsible-name {{
        font-weight: 600;
        color: {colors['text']};
    }}

    .critical-warning {{
        background: {colors['error']}22;
        border-left: 4px solid {colors['error']};
        padding: 0.7rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        color: {colors['error']};
        font-weight: 600;
    }}

    .days-to-hire {{
        background: {colors['warning']};
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }}

    .safe-status {{
        background: {colors['success']};
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }}
</style>
        """,
        unsafe_allow_html=True,
    )
