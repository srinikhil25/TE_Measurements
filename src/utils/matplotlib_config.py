"""
Matplotlib configuration utilities for CJK font support
"""
import matplotlib
import matplotlib.font_manager as fm
import warnings


def configure_cjk_fonts():
    """
    Configure matplotlib to use a font that supports CJK (Chinese, Japanese, Korean) characters.
    Tries common CJK-capable fonts in order of preference.
    """
    # List of CJK-capable fonts to try (in order of preference)
    cjk_fonts = [
        'Microsoft YaHei',      # Windows Chinese font
        'SimHei',                # Windows Chinese font (黑体)
        'SimSun',                # Windows Chinese font (宋体)
        'Noto Sans CJK SC',      # Google Noto Sans CJK
        'Noto Sans CJK TC',
        'Noto Sans CJK JP',
        'Noto Sans CJK KR',
        'WenQuanYi Micro Hei',   # Linux Chinese font
        'WenQuanYi Zen Hei',     # Linux Chinese font
        'Arial Unicode MS',      # Windows Unicode font
    ]
    
    # Get available font families
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # Find the first available CJK font
    selected_font = None
    for font_name in cjk_fonts:
        if font_name in available_fonts:
            selected_font = font_name
            break
    
    if selected_font:
        # Configure matplotlib to use the selected font
        matplotlib.rcParams['font.sans-serif'] = [selected_font] + matplotlib.rcParams['font.sans-serif']
        matplotlib.rcParams['axes.unicode_minus'] = False  # Fix minus sign rendering
        # Suppress the specific font warnings we're fixing
        warnings.filterwarnings('ignore', category=UserWarning, message='.*Glyph.*missing from font.*')
        return selected_font
    else:
        # If no CJK font is found, at least suppress the warnings
        warnings.filterwarnings('ignore', category=UserWarning, message='.*Glyph.*missing from font.*')
        return None

