DASHBOARD_PALETTE = [
    "#1E3A8A",  # Longitudinal - deep navy blue
    "#2563EB",  # Transverse - medium blue
    "#1B4F72",  # Alligator - muted dark teal
    "#1565C0",  # Block - calm blue
    "#0F5132",  # Edge - deep forest green
    "#2E7D32",  # Slippage - medium green
    "#BFA32F",  # Reflection - muted gold
    "#A77C1F",  # Joint - soft yellow-brown
    "#D97706",  # Patching Deterioration - muted orange
    "#B45309",  # Rutting - soft deep orange
    "#4B5563",  # Potholes - grayish blue
]

n = len(DASHBOARD_PALETTE)
color_scale = [[i/(n-1), c] for i, c in enumerate(DASHBOARD_PALETTE)]