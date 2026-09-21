import json
import base64
import os

JSON_PATH = '/home/gtu-itr/iic-cell-gtu-itr-/static/sih_2026_results_data.json'
with open(JSON_PATH) as f:
    teams_data = json.load(f)

# Ensure no phone numbers exist in the data and determine photo flags
for t in teams_data:
    t.pop('leader_phone', None)
    t['has_photo'] = bool(t.get('photo_url'))

photo_count_str = str(sum(1 for t in teams_data if t.get('has_photo')))
total_count_str = str(len(teams_data))

teams_json_str = json.dumps(teams_data, indent=2)

# Load GTU University Seal Base64
with open('/home/gtu-itr/iic-cell-gtu-itr-/static/gtu_uni_seal_300.png', 'rb') as f:
    gtu_uni_b64 = base64.b64encode(f.read()).decode('utf-8')
gtu_uni_uri = 'data:image/png;base64,' + gtu_uni_b64

# Load GTU-ITR R&D Seal Base64
with open('/home/gtu-itr/iic-cell-gtu-itr-/static/gtu_rnd_seal_300.png', 'rb') as f:
    gtu_rnd_b64 = base64.b64encode(f.read()).decode('utf-8')
gtu_rnd_seal_uri = 'data:image/png;base64,' + gtu_rnd_b64
gtu_rnd_uri = gtu_rnd_seal_uri


html_code = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
  <title>SIH 2026 — Official Internal Hackathon Results & Rankings | GTU-ITR IIC</title>
  
  <!-- Fonts & Icons -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@600;700;800;900&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/lucide@latest"></script>
  <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>

  <style>
    /* ============================================================
       GTU-ITR IIC & R&D Portal Design System — SIH 2026 Results
       Matches official portal color palette (Sapphire, Crimson, Trophy Gold)
       ============================================================ */
    :root {
      /* Brand Primary Colors (Aligned with IIC Portal style.css) */
      --primary: #0f52ba;
      --primary-light: #2563eb;
      --primary-dark: #1e3a8a;
      --primary-rgb: 15, 82, 186;

      /* GTU Emblem Crimson Accent */
      --accent: #d62828;
      --accent-light: #e63946;
      --accent-dark: #9b1c1c;
      --accent-rgb: 214, 40, 40;

      /* SIH Trophy Gold */
      --gold: #f59e0b;
      --gold-light: #fbbf24;
      --gold-dark: #d97706;
      --gold-rgb: 245, 158, 11;

      /* Semantic Status Colors */
      --success: #10b981;
      --success-dark: #059669;
      --warning: #f59e0b;
      --danger: #ef4444;

      /* Neutrals & Surfaces - Official GTU-ITR IIC Light Theme */
      --bg-body: #f8fafc;
      --bg-card: #ffffff;
      --bg-card-hover: #ffffff;
      --bg-surface-elevated: #f1f5f9;
      --bg-topbar: rgba(255, 255, 255, 0.94);

      --border-color: #e2e8f0;
      --border-card: rgba(15, 82, 186, 0.12);
      --border-subtle: #f1f5f9;

      --text-main: #0f172a;
      --text-muted: #475569;
      --text-dim: #64748b;

      --shadow-sm: 0 2px 8px rgba(15, 82, 186, 0.05);
      --shadow-md: 0 6px 20px -2px rgba(15, 82, 186, 0.08);
      --shadow-lg: 0 16px 36px -6px rgba(15, 82, 186, 0.12);
      --shadow-card: 0 4px 18px -2px rgba(15, 82, 186, 0.07), 0 2px 6px -1px rgba(0, 0, 0, 0.04);
      --shadow-glow: 0 0 18px rgba(15, 82, 186, 0.25);
    }

    [data-theme="dark"] {
      --bg-body: #0b1528;
      --bg-card: #111d33;
      --bg-card-hover: #172642;
      --bg-surface-elevated: #1a2b4a;
      --bg-topbar: rgba(11, 21, 40, 0.92);

      --border-color: rgba(56, 189, 248, 0.18);
      --border-card: rgba(56, 189, 248, 0.22);
      --border-subtle: rgba(255, 255, 255, 0.07);

      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;

      --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.35);
      --shadow-md: 0 8px 24px -4px rgba(0, 0, 0, 0.45);
      --shadow-lg: 0 16px 36px -6px rgba(0, 0, 0, 0.6);
      --shadow-card: 0 10px 30px -8px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(56, 189, 248, 0.2);
      --shadow-glow: 0 0 20px rgba(56, 189, 248, 0.3);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: var(--bg-body);
      background-image: 
        radial-gradient(circle at 10% 12%, rgba(15, 82, 186, 0.06) 0%, transparent 45%),
        radial-gradient(circle at 90% 20%, rgba(214, 40, 40, 0.04) 0%, transparent 40%),
        radial-gradient(circle at 50% 85%, rgba(15, 82, 186, 0.04) 0%, transparent 55%);
      background-attachment: fixed;
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      padding-bottom: 60px;
      overflow-x: hidden;
      transition: background-color 0.25s ease, color 0.25s ease;
    }

    [data-theme="dark"] body {
      background-image: 
        radial-gradient(circle at 10% 12%, rgba(15, 82, 186, 0.25) 0%, transparent 45%),
        radial-gradient(circle at 90% 20%, rgba(214, 40, 40, 0.14) 0%, transparent 40%),
        radial-gradient(circle at 50% 85%, rgba(15, 82, 186, 0.15) 0%, transparent 55%);
    }

    /* Top Institutional Header */
    .topbar {
      background: var(--bg-topbar);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-color);
      position: sticky;
      top: 0;
      z-index: 100;
      transition: background 0.25s ease, border-color 0.25s ease;
    }
    .topbar__inner {
      max-width: 1320px;
      margin: 0 auto;
      padding: 12px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
    }
    .brand-group {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      color: inherit;
      min-width: 0;
    }
    .brand-logo {
      width: 44px;
      height: 44px;
      object-fit: contain;
      filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15));
      flex-shrink: 0;
    }
    .brand-text {
      min-width: 0;
    }
    .brand-text h1 {
      font-family: 'Outfit', sans-serif;
      font-size: 1.15rem;
      font-weight: 800;
      color: var(--primary-dark);
      line-height: 1.2;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    [data-theme="dark"] .brand-text h1 {
      color: #38bdf8;
    }
    .brand-text p {
      font-size: 12px;
      color: var(--text-dim);
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .nav-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 9px 18px;
      border-radius: 10px;
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      white-space: nowrap;
      user-select: none;
    }
    .btn--primary {
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
      color: #ffffff;
      box-shadow: 0 4px 14px rgba(15, 82, 186, 0.3);
    }
    .btn--primary:hover {
      background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%);
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(15, 82, 186, 0.4);
    }
    .btn--gold {
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      color: #ffffff;
      box-shadow: 0 4px 14px rgba(245, 158, 11, 0.35);
    }
    .btn--gold:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(245, 158, 11, 0.45);
    }
    .btn--secondary {
      background: var(--bg-surface-elevated);
      color: var(--text-muted);
      border-color: var(--border-color);
    }
    .btn--secondary:hover {
      background: rgba(15, 82, 186, 0.08);
      color: var(--primary);
      border-color: var(--primary-light);
    }
    .btn--outline {
      background: transparent;
      border-color: var(--border-color);
      color: var(--text-muted);
    }
    .btn--outline:hover {
      background: var(--bg-surface-elevated);
      color: var(--text-main);
      border-color: var(--primary);
    }

    /* Main Container */
    .container {
      max-width: 1320px;
      margin: 0 auto;
      padding: 24px 20px 0;
      width: 100%;
    }

    /* Hero Banner - Elegant Institutional Accent */
    .hero-banner {
      background: linear-gradient(135deg, #0a1628 0%, #1e3a8a 50%, #0f52ba 100%);
      border: 2px solid rgba(15, 82, 186, 0.35);
      border-radius: 24px;
      padding: 30px 34px;
      position: relative;
      overflow: hidden;
      box-shadow: 0 16px 36px -8px rgba(15, 82, 186, 0.22);
      margin-bottom: 24px;
    }
    .hero-banner::after {
      content: '';
      position: absolute;
      top: -40px;
      right: -40px;
      width: 220px;
      height: 220px;
      background: radial-gradient(circle, rgba(245, 158, 11, 0.25) 0%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
    }
    .hero-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 14px;
      background: rgba(245, 158, 11, 0.2);
      border: 1px solid rgba(245, 158, 11, 0.5);
      border-radius: 9999px;
      color: #fbbf24;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
    }
    .hero-title {
      font-family: 'Outfit', sans-serif;
      font-size: clamp(1.6rem, 3.2vw, 2.3rem);
      font-weight: 900;
      color: #ffffff;
      line-height: 1.2;
      margin-bottom: 8px;
    }
    .hero-subtitle {
      color: #e2e8f0;
      font-size: 14px;
      max-width: 820px;
      line-height: 1.55;
      margin-bottom: 20px;
    }
    .hero-actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }

    /* Metric Cards (KPIs) */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-top: 24px;
    }
    .metric-card {
      background: var(--bg-card);
      border: 1.5px solid var(--border-card);
      border-radius: 16px;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 14px;
      transition: all 0.2s ease;
      box-shadow: var(--shadow-sm);
    }
    .metric-card:hover {
      border-color: var(--primary);
      transform: translateY(-2px);
      box-shadow: var(--shadow-md);
    }
    .metric-icon {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .metric-val {
      font-family: 'Outfit', sans-serif;
      font-size: 1.6rem;
      font-weight: 900;
      color: var(--text-main);
      line-height: 1;
    }
    .metric-label {
      font-size: 11.5px;
      color: var(--text-dim);
      margin-top: 4px;
      font-weight: 600;
      line-height: 1.25;
    }

    /* Tab Controls */
    .controls-panel {
      background: var(--bg-card);
      border: 1.5px solid var(--border-card);
      border-radius: 20px;
      padding: 16px 20px;
      margin-bottom: 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      box-shadow: var(--shadow-sm);
    }
    .tabs-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 12px;
    }
    .tab-btn {
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 10px 18px;
      border-radius: 11px;
      font-size: 13.5px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s ease;
      user-select: none;
    }
    .tab-btn:hover {
      background: rgba(15, 82, 186, 0.08);
      color: var(--primary);
      border-color: var(--primary-light);
    }
    .tab-btn.active {
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
      color: #ffffff;
      border-color: var(--primary);
      box-shadow: 0 4px 14px rgba(15, 82, 186, 0.35);
    }
    .tab-badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 9999px;
      background: rgba(0, 0, 0, 0.15);
      font-weight: 800;
    }
    .tab-btn.active .tab-badge {
      background: rgba(255, 255, 255, 0.25);
      color: #ffffff;
    }

    /* Search and Filters */
    .filter-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
      flex-wrap: wrap;
    }
    .search-box {
      flex: 1;
      min-width: 240px;
      position: relative;
    }
    .search-box input {
      width: 100%;
      background: var(--bg-surface-elevated);
      border: 1.5px solid var(--border-color);
      border-radius: 10px;
      padding: 10px 14px 10px 38px;
      color: var(--text-main);
      font-size: 13px;
      font-weight: 500;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    .search-box input:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(15, 82, 186, 0.15);
      background: var(--bg-card);
    }
    .search-box i, .search-box svg {
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-dim);
      width: 16px;
      height: 16px;
    }
    .filter-actions-bar {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .filter-pills {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .pill-btn {
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 7px 14px;
      border-radius: 8px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.2s;
      user-select: none;
    }
    .pill-btn:hover {
      border-color: var(--primary-light);
      color: var(--primary);
    }
    .pill-btn.active {
      background: var(--primary);
      border-color: var(--primary);
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(15, 82, 186, 0.25);
    }

    .view-toggles {
      display: flex;
      gap: 6px;
    }
    .icon-toggle {
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      padding: 6px 10px;
      height: 38px;
      border-radius: 8px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .icon-toggle:hover {
      border-color: var(--primary-light);
      color: var(--primary);
    }
    .icon-toggle.active {
      background: var(--primary);
      border-color: var(--primary);
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(15, 82, 186, 0.3);
    }

    /* Card Grid System */
    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 20px;
      width: 100%;
    }
    
    .team-card {
      background: var(--bg-card);
      border: 1.5px solid var(--border-card);
      border-radius: 18px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
      box-shadow: var(--shadow-card);
      min-width: 0;
    }
    .team-card:hover {
      transform: translateY(-4px);
      border-color: var(--primary);
      box-shadow: 0 14px 30px -4px rgba(15, 82, 186, 0.16);
    }
    .team-card.gold-tier {
      border-color: rgba(245, 158, 11, 0.45);
    }
    .team-card.gold-tier:hover {
      border-color: #fbbf24;
      box-shadow: 0 14px 30px -4px rgba(245, 158, 11, 0.25);
    }

    /* Card Header / Rank Badge */
    .card-topbar {
      padding: 10px 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-surface-elevated);
      border-bottom: 1px solid var(--border-color);
    }
    .rank-pill {
      font-family: 'Outfit', sans-serif;
      font-size: 12px;
      font-weight: 800;
      padding: 3px 9px;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }
    .rank-pill.rank-1 {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: #ffffff;
      font-weight: 900;
      box-shadow: 0 2px 6px rgba(245, 158, 11, 0.35);
    }
    .rank-pill.rank-2 {
      background: linear-gradient(135deg, #94a3b8, #64748b);
      color: #ffffff;
      box-shadow: 0 2px 6px rgba(100, 116, 139, 0.35);
    }
    .rank-pill.rank-3 {
      background: linear-gradient(135deg, #d97706, #b45309);
      color: #ffffff;
      box-shadow: 0 2px 6px rgba(217, 119, 6, 0.35);
    }
    .rank-pill.rank-top {
      background: rgba(15, 82, 186, 0.12);
      border: 1px solid rgba(15, 82, 186, 0.28);
      color: var(--primary);
    }
    .rank-pill.rank-eval {
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      color: var(--text-dim);
    }

    .category-badge {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 3px 8px;
      border-radius: 6px;
    }
    .category-badge.software {
      background: #eff6ff;
      color: #1d4ed8;
      border: 1px solid #bfdbfe;
    }
    .category-badge.hardware {
      background: #fff7ed;
      color: #c2410c;
      border: 1px solid #fed7aa;
    }
    [data-theme="dark"] .category-badge.software {
      background: rgba(15, 82, 186, 0.2);
      color: #60a5fa;
      border: 1px solid rgba(56, 189, 248, 0.35);
    }
    [data-theme="dark"] .category-badge.hardware {
      background: rgba(249, 115, 22, 0.15);
      color: #fb923c;
      border: 1px solid rgba(249, 115, 22, 0.3);
    }

    /* Card Photo Box */
    .card-photo-wrapper {
      position: relative;
      width: 100%;
      height: 185px;
      background: var(--bg-surface-elevated);
      overflow: hidden;
      cursor: pointer;
    }
    .card-photo {
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center 25%;
      transition: transform 0.35s ease;
    }
    .card-photo-wrapper:hover .card-photo {
      transform: scale(1.05);
    }
    .photo-tag {
      position: absolute;
      bottom: 8px;
      left: 8px;
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(6px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 10px;
      font-weight: 700;
      color: #34d399;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .photo-zoom-hint {
      position: absolute;
      bottom: 8px;
      right: 8px;
      background: rgba(0, 0, 0, 0.75);
      color: #ffffff;
      padding: 3px 7px;
      border-radius: 6px;
      font-size: 9.5px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      opacity: 0.85;
    }

    /* Placeholder when no selfie */
    .photo-placeholder {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, var(--bg-surface-elevated) 0%, var(--bg-body) 100%);
      color: var(--text-dim);
      gap: 6px;
    }
    .placeholder-avatar {
      width: 50px;
      height: 50px;
      border-radius: 14px;
      background: rgba(15, 82, 186, 0.12);
      border: 1.5px solid rgba(15, 82, 186, 0.25);
      color: var(--primary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Outfit', sans-serif;
      font-size: 1.35rem;
      font-weight: 800;
    }

    /* Card Content */
    .card-body {
      padding: 14px;
      display: flex;
      flex-direction: column;
      flex-grow: 1;
      gap: 10px;
      min-width: 0;
    }
    .team-heading {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 8px;
      min-width: 0;
    }
    .team-name {
      font-family: 'Outfit', sans-serif;
      font-size: 1.12rem;
      font-weight: 800;
      color: var(--text-main);
      line-height: 1.25;
      word-break: break-word;
      overflow-wrap: break-word;
    }
    .team-reg {
      font-size: 11px;
      color: var(--primary);
      font-family: monospace;
      margin-top: 3px;
      display: inline-block;
      background: rgba(15, 82, 186, 0.08);
      padding: 2px 6px;
      border-radius: 4px;
    }

    /* Score Badge */
    .score-badge {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      flex-shrink: 0;
    }
    .score-num {
      font-family: 'Outfit', sans-serif;
      font-size: 1.28rem;
      font-weight: 900;
      color: var(--primary);
      line-height: 1;
    }
    .score-num.gold { color: #d97706; }
    .score-num.emerald { color: #059669; }
    .score-num.muted { color: var(--text-dim); font-size: 1rem; }
    [data-theme="dark"] .score-num.gold { color: #fbbf24; }
    [data-theme="dark"] .score-num.emerald { color: #34d399; }
    .score-sub {
      font-size: 9.5px;
      font-weight: 700;
      color: var(--text-dim);
      text-transform: uppercase;
      margin-top: 2px;
    }

    /* Details Info List (No phone numbers shown) */
    .info-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 8px 11px;
      font-size: 11.5px;
    }
    .info-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .info-label {
      color: var(--text-dim);
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 11px;
      font-weight: 500;
      flex-shrink: 0;
    }
    .info-val {
      color: var(--text-main);
      font-weight: 700;
      text-align: right;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* SSIP Tag */
    .ssip-ribbon {
      background: linear-gradient(135deg, #fffbeb, #fef3c7);
      border: 1px solid #fde68a;
      border-radius: 8px;
      padding: 6px 10px;
      font-size: 11px;
      font-weight: 700;
      color: #b45309;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    [data-theme="dark"] .ssip-ribbon {
      background: linear-gradient(135deg, rgba(217, 119, 6, 0.22), rgba(245, 158, 11, 0.12));
      border-color: rgba(245, 158, 11, 0.45);
      color: #fbbf24;
    }

    /* Card Footer Action Buttons */
    .card-footer-actions {
      display: flex;
      gap: 8px;
      margin-top: auto;
      padding-top: 10px;
      border-top: 1px solid var(--border-color);
    }
    .btn-poster-action {
      flex: 1;
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      border: none;
      color: #ffffff;
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      user-select: none;
      box-shadow: 0 2px 6px rgba(245, 158, 11, 0.3);
    }
    .btn-poster-action:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
    }
    .btn-photo-action {
      padding: 8px 12px;
      border-radius: 8px;
      font-size: 12px;
      background: var(--bg-surface-elevated);
      border: 1.5px solid var(--border-color);
      color: var(--primary);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      user-select: none;
      font-weight: 600;
    }
    .btn-photo-action:hover {
      background: rgba(15, 82, 186, 0.1);
      border-color: var(--primary);
      color: var(--primary-dark);
    }

    /* Table View */
    .table-wrapper {
      background: var(--bg-card);
      border: 1.5px solid var(--border-card);
      border-radius: 16px;
      overflow-x: auto;
      box-shadow: var(--shadow-card);
      -webkit-overflow-scrolling: touch;
    }
    .results-table {
      width: 100%;
      min-width: 680px;
      border-collapse: collapse;
      font-size: 13px;
    }
    .results-table th {
      background: var(--bg-surface-elevated);
      color: var(--text-dim);
      font-weight: 700;
      font-size: 11.5px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 14px 16px;
      text-align: left;
      border-bottom: 2px solid var(--border-color);
    }
    .results-table td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-color);
      color: var(--text-main);
      vertical-align: middle;
    }
    .results-table tr:hover td {
      background: rgba(15, 82, 186, 0.04);
    }
    .table-thumb {
      width: 48px;
      height: 38px;
      border-radius: 6px;
      object-fit: cover;
      cursor: pointer;
      border: 1px solid var(--border-color);
      transition: transform 0.2s;
    }
    .table-thumb:hover {
      transform: scale(1.12);
      border-color: var(--primary);
    }

    /* Lightbox & Poster Modals */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.75);
      backdrop-filter: blur(8px);
      z-index: 1000;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 16px;
    }
    .modal-overlay.open { display: flex; }
    .modal-box {
      background: var(--bg-card);
      border: 1.5px solid var(--border-card);
      border-radius: 20px;
      max-width: 720px;
      width: 100%;
      overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(0,0,0,0.4);
      animation: zoomIn 0.2s ease-out;
    }
    @keyframes zoomIn {
      from { opacity: 0; transform: scale(0.96); }
      to { opacity: 1; transform: scale(1); }
    }
    .modal-header {
      padding: 16px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border-color);
      background: var(--bg-surface-elevated);
    }
    .modal-img-wrap {
      width: 100%;
      max-height: 480px;
      background: #000;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    .modal-img {
      max-width: 100%;
      max-height: 480px;
      object-fit: contain;
    }
    .modal-footer {
      padding: 14px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-surface-elevated);
      border-top: 1px solid var(--border-color);
    }

    /* Poster Specific Modal Elements */
    .poster-modal-dialog {
      background: var(--bg-card);
      border: 1.5px solid var(--border-card);
      border-radius: 20px;
      max-width: 860px;
      width: 100%;
      max-height: 94vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
      animation: zoomIn 0.2s ease-out;
    }
    .poster-canvas-box {
      max-width: 440px;
      width: 100%;
      box-shadow: 0 16px 36px rgba(0,0,0,0.4);
      border-radius: 14px;
      overflow: hidden;
      border: 1.5px solid var(--border-color);
      background: #060a12;
      position: relative;
    }
    .poster-canvas-box canvas {
      width: 100%;
      height: auto;
      display: block;
    }

    .spin {
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    /* Print Styles */
    @media print {
      body { background: #fff !important; color: #000 !important; padding: 0 !important; }
      .topbar, .controls-panel, .nav-actions, .photo-zoom-hint, .card-footer-actions { display: none !important; }
      .hero-banner { background: #f8fafc !important; color: #000 !important; border: 1px solid #ccc !important; box-shadow: none !important; padding: 20px !important; }
      .hero-title, .hero-title span { color: #000 !important; -webkit-text-fill-color: #000 !important; }
      .metric-card { border: 1px solid #ddd !important; background: #fff !important; }
      .team-card { border: 1px solid #ccc !important; background: #fff !important; break-inside: avoid; }
      .team-name { color: #000 !important; }
      .info-list { background: #f1f5f9 !important; border: 1px solid #e2e8f0 !important; }
      .info-label, .info-val { color: #334155 !important; }
    }

    /* Responsive Media Queries */
    @media (max-width: 960px) {
      .cards-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
      }
      .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    @media (max-width: 768px) {
      .hero-banner {
        padding: 22px 18px;
      }
      .controls-panel {
        padding: 14px 12px;
        border-radius: 16px;
        gap: 12px;
      }
      .tabs-row {
        flex-wrap: nowrap;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        gap: 8px;
        padding-bottom: 6px;
      }
      .tabs-row::-webkit-scrollbar { display: none; }
      .tab-btn {
        flex-shrink: 0;
        white-space: nowrap;
        padding: 8px 14px;
        font-size: 12.5px;
      }
      .filter-row {
        flex-direction: column;
        align-items: stretch;
      }
      .filter-actions-bar {
        width: 100%;
        justify-content: space-between;
      }
      .filter-pills {
        flex-wrap: nowrap;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        padding-bottom: 4px;
      }
      .filter-pills::-webkit-scrollbar { display: none; }
      .pill-btn {
        flex-shrink: 0;
        white-space: nowrap;
      }
    }

    /* SMARTPHONE ORIENTED RESPONSIVE GRID (<= 640px) */
    @media (max-width: 640px) {
      .container {
        padding: 12px 10px 0;
      }
      .topbar__inner {
        padding: 10px 12px;
        gap: 8px;
      }
      .brand-logo {
        width: 36px;
        height: 36px;
      }
      .brand-text h1 {
        font-size: 0.95rem;
      }
      .nav-actions {
        gap: 6px;
      }
      .nav-actions .btn {
        padding: 6px 9px;
        font-size: 11.5px;
        border-radius: 8px;
      }
      .btn--print {
        display: none !important;
      }
      .hero-banner {
        padding: 18px 14px;
        border-radius: 18px;
        margin-bottom: 14px;
      }
      .hero-title {
        font-size: 1.35rem;
      }
      .hero-subtitle {
        font-size: 12px;
        line-height: 1.5;
        margin-bottom: 14px;
      }
      .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin-top: 14px;
      }
      .metric-card {
        padding: 10px 12px;
        gap: 10px;
        border-radius: 12px;
      }
      .metric-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
      }
      .metric-icon svg, .metric-icon i {
        width: 18px;
        height: 18px;
      }
      .metric-val {
        font-size: 1.35rem;
      }
      .metric-label {
        font-size: 10px;
        line-height: 1.2;
      }
      
      /* TRUE 2-COLUMN GRID ON MOBILE BY DEFAULT ("properly grid me dikhe") */
      .cards-grid {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 10px !important;
      }
      .team-card {
        border-radius: 14px;
      }
      .card-topbar {
        padding: 6px 8px;
      }
      .rank-pill {
        font-size: 10.5px;
        padding: 2px 6px;
      }
      .category-badge {
        font-size: 9px;
        padding: 2px 5px;
      }
      .card-photo-wrapper {
        height: 112px;
      }
      .photo-tag {
        font-size: 8.5px;
        padding: 2px 5px;
        bottom: 5px;
        left: 5px;
      }
      .photo-zoom-hint {
        display: none;
      }
      .placeholder-avatar {
        width: 38px;
        height: 38px;
        font-size: 1.1rem;
      }
      .card-body {
        padding: 10px 8px;
        gap: 6px;
      }
      .team-heading {
        flex-direction: column;
        align-items: flex-start;
        gap: 3px;
      }
      .team-name {
        font-size: 0.88rem;
        line-height: 1.25;
        min-height: 2.5em;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      .team-reg {
        font-size: 9.5px;
        padding: 1px 4px;
      }
      .score-badge {
        flex-direction: row;
        align-items: center;
        gap: 4px;
      }
      .score-num {
        font-size: 1.1rem;
      }
      .score-sub {
        font-size: 8.5px;
      }
      .ssip-ribbon {
        font-size: 9px;
        padding: 4px 6px;
        gap: 4px;
        border-radius: 6px;
      }
      .ssip-ribbon i, .ssip-ribbon svg {
        width: 11px;
        height: 11px;
      }
      .info-list {
        padding: 6px 8px;
        font-size: 10.5px;
        gap: 4px;
        border-radius: 6px;
      }
      .info-row {
        font-size: 10.5px;
      }
      .info-label {
        font-size: 10px;
        gap: 3px;
      }
      .info-label i, .info-label svg {
        width: 10px;
        height: 10px;
      }
      .info-val {
        font-size: 10.5px;
      }
      .card-footer-actions {
        padding-top: 6px;
        gap: 4px;
      }
      .btn-poster-action {
        padding: 6px 4px;
        font-size: 10px;
        gap: 3px;
        border-radius: 6px;
      }
      .btn-poster-action i, .btn-poster-action svg {
        width: 11px;
        height: 11px;
      }
      .btn-photo-action {
        padding: 6px 6px;
        font-size: 10px;
        border-radius: 6px;
      }
      .btn-photo-action i, .btn-photo-action svg {
        width: 11px;
        height: 11px;
      }

      /* 1-COLUMN FULL WIDTH LIST VIEW (When chosen by user) */
      .cards-grid.list-view {
        grid-template-columns: 1fr !important;
        gap: 14px !important;
      }
      .cards-grid.list-view .card-photo-wrapper {
        height: 185px;
      }
      .cards-grid.list-view .team-name {
        font-size: 1.15rem;
      }
      .cards-grid.list-view .card-body {
        padding: 14px;
        gap: 10px;
      }
      .cards-grid.list-view .btn-poster-action {
        padding: 9px 14px;
        font-size: 12px;
      }
    }

    @media (max-width: 380px) {
      .topbar__inner {
        padding: 8px 10px;
      }
      .brand-text h1 {
        font-size: 0.85rem;
      }
      .nav-actions .btn span {
        display: none;
      }
      .nav-actions .btn {
        padding: 6px 8px;
      }
    }
  </style>
</head>
<body>

  <!-- Hidden DOM Preload for GTU Logos -->
  <img id="domGtuUniSeal" src="/static/gtu_uni_seal_300.png" style="display:none;" alt="GTU Seal">
  <img id="domGtuRndSeal" src="/static/gtu_rnd_seal_300.png" style="display:none;" alt="GTU R&D Seal">

  <!-- Top Bar -->
  <header class="topbar">
    <div class="topbar__inner">
      <a href="/" class="brand-group">
        <img src="/static/gtu_uni_seal_300.png" alt="GTU Logo" class="brand-logo" onerror="this.src='/static/gtu_logo.png'">
        <div class="brand-text">
          <h1>GTU-ITR IIC &amp; R&amp;D Cell</h1>
          <p>Smart India Hackathon (SIH 2026) Official Results</p>
        </div>
      </a>
      <div class="nav-actions">
        <!-- Light / Dark Theme Switcher -->
        <button onclick="toggleTheme()" class="btn btn--outline" id="themeToggleBtn" title="Toggle Light / Dark Theme">
          <i id="themeIcon" data-lucide="moon" style="width:15px;height:15px;"></i>
          <span id="themeLabel">Dark</span>
        </button>
        <button onclick="triggerConfetti()" class="btn btn--gold" title="Celebrate Winners">
          <i data-lucide="sparkles" style="width:15px;height:15px;"></i>
          <span>Celebrate</span>
        </button>
        <button onclick="window.print()" class="btn btn--outline btn--print" title="Print Official Result Sheet">
          <i data-lucide="printer" style="width:15px;height:15px;"></i>
          <span>Print Sheet</span>
        </button>
        <a href="/" class="btn btn--primary">
          <i data-lucide="home" style="width:15px;height:15px;"></i>
          <span>Portal Home</span>
        </a>
      </div>
    </div>
  </header>

  <main class="container">

    <!-- Hero Announcement Banner -->
    <section class="hero-banner">
      <div class="hero-badge">
        <i data-lucide="award" style="width:14px;height:14px;"></i>
        <span>Official Internal Results Declared</span>
      </div>
      <h2 class="hero-title">
        Smart India Hackathon (SIH 2026) Results
      </h2>
      <p class="hero-subtitle">
        Hearty congratulations to all participants! The <strong>Top 20 Teams Selected for SIH 2026 Nationals</strong> and <strong>15 Projects Recommended for ₹2,50,000 SSIP Funding</strong> have been declared with official jury rankings and verified hackathon photos.
      </p>

      <div class="hero-actions">
        <button onclick="openPosterModal(ALL_TEAMS[0].team_name)" class="btn btn--gold" style="padding: 10px 18px; border-radius: 12px; font-weight: 800;">
          <i data-lucide="sparkles" style="width:16px;height:16px;"></i>
          <span>Create Team Posters</span>
        </button>
        <button onclick="switchTab('top20')" class="btn btn--primary" style="padding: 10px 18px; border-radius: 12px;">
          <i data-lucide="trophy" style="width:16px;height:16px;"></i>
          <span>Top 20 Winners</span>
        </button>
        <button onclick="switchTab('ssip')" class="btn btn--secondary" style="padding: 10px 18px; border-radius: 12px;">
          <i data-lucide="coins" style="width:16px;height:16px;"></i>
          <span>SSIP ₹2.5L Grant Teams</span>
        </button>
      </div>

      <!-- KPI Metrics -->
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-icon" style="background:rgba(15, 82, 186, 0.12); color:#0f52ba;">
            <i data-lucide="trophy" style="width:24px;height:24px;"></i>
          </div>
          <div>
            <div class="metric-val" id="metricTop20">20</div>
            <div class="metric-label">Top 20 Teams (Selected)</div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon" style="background:rgba(245, 158, 11, 0.15); color:#d97706;">
            <i data-lucide="coins" style="width:24px;height:24px;"></i>
          </div>
          <div>
            <div class="metric-val" id="metricSsip">15</div>
            <div class="metric-label">SSIP Recommended (₹2.5L)</div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon" style="background:rgba(168, 85, 247, 0.15); color:#9333ea;">
            <i data-lucide="camera" style="width:24px;height:24px;"></i>
          </div>
          <div>
            <div class="metric-val" id="metricPhotos">""" + photo_count_str + """</div>
            <div class="metric-label">Verified Venue Selfies</div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon" style="background:rgba(16, 185, 129, 0.15); color:#059669;">
            <i data-lucide="layers" style="width:24px;height:24px;"></i>
          </div>
          <div>
            <div class="metric-val" id="metricTotal">""" + total_count_str + """</div>
            <div class="metric-label">Total Projects Evaluated</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Controls Panel -->
    <section class="controls-panel">
      <!-- Tabs -->
      <div class="tabs-row">
        <button class="tab-btn active" onclick="switchTab('top20')" id="tabBtnTop20">
          <i data-lucide="trophy" style="width:16px;height:16px;"></i>
          <span>Top 20 Teams (Selected for SIH)</span>
          <span class="tab-badge" id="badgeTop20">20</span>
        </button>

        <button class="tab-btn" onclick="switchTab('ssip')" id="tabBtnSsip">
          <i data-lucide="sparkles" style="width:16px;height:16px;"></i>
          <span>SSIP Recommended Projects (₹2.5L)</span>
          <span class="tab-badge" id="badgeSsip">15</span>
        </button>

        <button class="tab-btn" onclick="switchTab('all')" id="tabBtnAll">
          <i data-lucide="list-ordered" style="width:16px;height:16px;"></i>
          <span>Complete Leaderboard (All Teams)</span>
          <span class="tab-badge" id="badgeAll">36</span>
        </button>
      </div>

      <!-- Filters & Search -->
      <div class="filter-row">
        <div class="search-box">
          <i data-lucide="search"></i>
          <input type="text" id="searchInput" placeholder="Search by Team Name, Leader, PSID..." oninput="handleSearch()">
        </div>

        <div class="filter-actions-bar">
          <div class="filter-pills">
            <button class="pill-btn active" onclick="setCategoryFilter('all', this)">All Domains</button>
            <button class="pill-btn" onclick="setCategoryFilter('Software', this)">💻 Software</button>
            <button class="pill-btn" onclick="setCategoryFilter('Hardware', this)">⚙️ Hardware</button>
            <button class="pill-btn" onclick="setPhotoFilter(this)">📸 With Selfie</button>
          </div>

          <div class="view-toggles">
            <button class="icon-toggle active" id="btnViewGrid" onclick="setViewMode('grid')" title="Grid View (2-Column on Mobile, 3-Column on Desktop)">
              <i data-lucide="layout-grid" style="width:16px;height:16px;"></i>
              <span style="font-size:11.5px;">Grid</span>
            </button>
            <button class="icon-toggle" id="btnViewList" onclick="setViewMode('list')" title="1-Column Full Card List">
              <i data-lucide="rows" style="width:16px;height:16px;"></i>
              <span style="font-size:11.5px;">List</span>
            </button>
            <button class="icon-toggle" id="btnViewTable" onclick="setViewMode('table')" title="Table Sheet View">
              <i data-lucide="table" style="width:16px;height:16px;"></i>
              <span style="font-size:11.5px;">Table</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Results Display Section -->
    <section id="resultsContent">
      <div id="cardsView" class="cards-grid"></div>
      <div id="tableView" class="table-wrapper" style="display:none;"></div>
    </section>

  </main>

  <!-- Image Lightbox Modal -->
  <div class="modal-overlay" id="photoModal" onclick="if(event.target===this) closePhotoModal()">
    <div class="modal-box">
      <div class="modal-header">
        <div>
          <h3 id="modalTeamName" style="font-family:'Outfit'; font-size:1.15rem; color:var(--primary); font-weight:800;">Team Selfie</h3>
          <p id="modalSub" style="font-size:12px; color:var(--text-dim);">GTU-ITR Internal Hackathon Venue Capture</p>
        </div>
        <button onclick="closePhotoModal()" style="background:none; border:none; color:var(--text-dim); cursor:pointer;">
          <i data-lucide="x" style="width:20px;height:20px;"></i>
        </button>
      </div>
      <div class="modal-img-wrap">
        <img id="modalImg" src="" alt="Team Group Selfie" class="modal-img">
      </div>
      <div class="modal-footer">
        <span id="modalMeta" style="font-size:12px; color:var(--text-muted); font-weight:600;"></span>
        <div style="display: flex; gap: 8px;">
          <button onclick="openPosterModalFromCurrentPhoto()" class="btn btn--gold" style="padding:6px 14px; font-size:12px;">
            <i data-lucide="sparkles" style="width:13px;height:13px;"></i>
            <span>Social Poster</span>
          </button>
          <a id="modalDownload" href="#" download="sih-team-photo.jpg" class="btn btn--primary" style="padding:6px 14px; font-size:12px;">
            <i data-lucide="download" style="width:13px;height:13px;"></i>
            <span>Download</span>
          </a>
        </div>
      </div>
    </div>
  </div>

  <!-- Direct Photo Upload Modal -->
  <div class="modal-overlay" id="uploadPhotoModal" onclick="if(event.target===this) closeUploadModal()">
    <div class="modal-box" style="max-width: 500px; width: 95%;">
      <div class="modal-header">
        <div>
          <h3 id="uploadModalTitle" style="font-family:'Outfit'; font-size:1.15rem; color:var(--primary); font-weight:800; display:flex; align-items:center; gap:8px;">
            <i data-lucide="camera" style="width:18px;height:18px;"></i>
            <span>Upload Team Hackathon Photo</span>
          </h3>
          <p id="uploadModalSub" style="font-size:12px; color:var(--text-dim);">Attach official group photo or selfie for Results &amp; Social Poster</p>
        </div>
        <button onclick="closeUploadModal()" style="background:none; border:none; color:var(--text-dim); cursor:pointer;">
          <i data-lucide="x" style="width:20px;height:20px;"></i>
        </button>
      </div>

      <div style="padding: 18px; background: var(--bg-card); display: flex; flex-direction: column; gap: 14px;">
        <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-color); border-radius: 10px; padding: 10px 14px;">
          <div style="font-size: 14px; font-weight: 800; color: var(--text-main);" id="uploadModalTeamName"></div>
          <div style="font-size: 12px; color: var(--text-dim); margin-top: 3px;" id="uploadModalDetails"></div>
        </div>

        <div id="uploadPreviewArea" style="width: 100%; height: 210px; border: 2px dashed var(--primary-light); border-radius: 12px; background: var(--bg-surface-elevated); display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; position: relative;">
          <img id="uploadPreviewImg" src="" style="width: 100%; height: 100%; object-fit: cover; display: none;">
          <div id="uploadPrompt" style="text-align: center; padding: 16px;">
            <i data-lucide="image-plus" style="width: 40px; height: 40px; color: var(--primary); margin: 0 auto 8px; display: block;"></i>
            <span style="font-size: 13px; color: var(--text-main); font-weight: 600;">Choose Photo or Take Selfie</span>
            <p style="font-size: 11px; color: var(--text-dim); margin-top: 4px;">Supports JPG, PNG, WEBP</p>
          </div>
        </div>

        <div style="display: flex; gap: 10px;">
          <label class="btn btn--secondary" style="flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 6px; cursor: pointer; padding: 9px 12px; font-size: 12.5px;">
            <i data-lucide="camera" style="width: 15px; height: 15px;"></i>
            <span>Take Selfie</span>
            <input type="file" id="cameraUploadInput" accept="image/*" capture="user" style="display: none;" onchange="handleDirectPhotoSelect(this)">
          </label>
          <label class="btn btn--secondary" style="flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 6px; cursor: pointer; padding: 9px 12px; font-size: 12.5px;">
            <i data-lucide="upload" style="width: 15px; height: 15px;"></i>
            <span>Gallery / File</span>
            <input type="file" id="fileUploadInput" accept="image/*" style="display: none;" onchange="handleDirectPhotoSelect(this)">
          </label>
        </div>

        <div id="uploadProgressBox" style="display: none; align-items: center; gap: 10px; padding: 10px; background: rgba(15, 82, 186, 0.1); border-radius: 8px; color: var(--primary); font-size: 12.5px; font-weight: 600;">
          <div class="spinner"></div>
          <span>Uploading and updating live results...</span>
        </div>

        <div id="uploadAlertBox" style="display: none; padding: 10px; border-radius: 8px; font-size: 12.5px;"></div>

        <button id="btnSubmitPhotoUpload" onclick="submitDirectPhotoUpload()" class="btn btn--primary" style="width: 100%; padding: 11px; font-weight: 800; font-size: 13.5px; display: inline-flex; align-items: center; justify-content: center; gap: 8px;" disabled>
          <i data-lucide="check-circle" style="width: 16px; height: 16px;"></i>
          <span>Save &amp; Update Photo</span>
        </button>

        <div style="text-align: center; margin-top: -2px;">
          <a id="uploadAttendanceLink" href="/attendance" target="_blank" style="font-size: 11.5px; color: var(--text-dim); text-decoration: underline;">
            Or open Team Attendance Portal &rarr;
          </a>
        </div>
      </div>
    </div>
  </div>

  <!-- Social Achievement Poster Generator Modal -->
  <div class="modal-overlay" id="posterModal" onclick="if(event.target===this) closePosterModal()">
    <div class="poster-modal-dialog">
      <div class="modal-header" style="padding: 14px 20px;">
        <div>
          <h3 id="posterModalTitle" style="font-family:'Outfit'; font-size:1.2rem; color:var(--primary); font-weight:800; display:flex; align-items:center; gap:8px;">
            <i data-lucide="sparkles" style="width:18px;height:18px;"></i>
            <span>Team Achievement Poster</span>
          </h3>
          <p style="font-size:12px; color:var(--text-dim);">Instagram Story / Post Ready • Tag <strong>@gtu_itr_official</strong></p>
        </div>
        <button onclick="closePosterModal()" style="background:none; border:none; color:var(--text-dim); cursor:pointer;">
          <i data-lucide="x" style="width:20px;height:20px;"></i>
        </button>
      </div>

      <div style="display: flex; flex-direction: column; md:flex-row; padding: 16px 20px; gap: 20px; overflow-y: auto; background: var(--bg-card);">
        <!-- Aspect Ratio Switcher -->
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
          <span style="font-size: 12.5px; font-weight: 700; color: var(--text-main);">Poster Format:</span>
          <div style="display: flex; gap: 8px;">
            <button id="btnAspectPortrait" onclick="setPosterAspectRatio('portrait')" class="pill-btn active">
              <i data-lucide="smartphone" style="width: 13px; height: 13px;"></i>
              <span>Portrait 4:5 (Story / Reel)</span>
            </button>
            <button id="btnAspectSquare" onclick="setPosterAspectRatio('square')" class="pill-btn">
              <i data-lucide="square" style="width: 13px; height: 13px;"></i>
              <span>Square 1:1 (Post Feed)</span>
            </button>
          </div>
        </div>

        <!-- Canvas Area -->
        <div style="display: flex; justify-content: center; align-items: center; width: 100%;">
          <div class="poster-canvas-box">
            <canvas id="posterCanvas"></canvas>
            <div id="posterLoading" style="position: absolute; inset: 0; background: rgba(11, 17, 32, 0.85); backdrop-filter: blur(4px); display: none; align-items: center; justify-content: center; flex-direction: column; gap: 10px; color: #38bdf8;">
              <i data-lucide="loader-2" class="spin" style="width: 32px; height: 32px;"></i>
              <span style="font-size: 13px; font-weight: 600;">Rendering HD Poster with GTU Seal...</span>
            </div>
          </div>
        </div>

        <!-- Social Caption Preview & Actions -->
        <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-color); border-radius: 14px; padding: 14px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 11.5px; font-weight: 800; color: var(--primary); text-transform: uppercase;">Instagram &amp; LinkedIn Caption</span>
            <button onclick="copyPosterCaption()" class="btn btn--secondary" style="padding: 4px 10px; font-size: 11px; border-radius: 6px;">
              <i data-lucide="copy" style="width: 12px; height: 12px;"></i>
              <span id="copyCaptionText">Copy Caption</span>
            </button>
          </div>
          <p id="posterCaptionPreview" style="font-size: 12px; color: var(--text-muted); line-height: 1.5; margin: 0; white-space: pre-line; user-select: all; font-family: sans-serif;"></p>
        </div>
      </div>

      <div class="modal-footer" style="padding: 12px 20px; background: var(--bg-surface-elevated);">
        <button onclick="closePosterModal()" class="btn btn--secondary" style="padding: 8px 16px; font-size: 12.5px;">Close</button>
        <div style="display: flex; gap: 10px;">
          <button onclick="sharePoster()" id="btnSharePoster" class="btn btn--secondary" style="padding: 8px 16px; font-size: 12.5px; border-radius: 8px; display: inline-flex; align-items: center; gap: 6px;">
            <i data-lucide="share-2" style="width: 14px; height: 14px;"></i>
            <span>Share</span>
          </button>
          <button onclick="downloadPosterImage()" class="btn btn--gold" style="padding: 8px 18px; font-size: 12.5px; font-weight: 800; border-radius: 8px; display: inline-flex; align-items: center; gap: 6px;">
            <i data-lucide="download" style="width: 14px; height: 14px;"></i>
            <span>Download Poster (PNG)</span>
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Application Logic -->
  <script>
    // Embedded Data with GTU University and R&D Seals (NO PHONE NUMBERS)
    const GTU_UNI_SEAL_URI = '""" + gtu_uni_uri + """';
    const GTU_RND_SEAL_URI = '""" + gtu_rnd_seal_uri + """';
    const ALL_TEAMS = """ + teams_json_str + """;

    // Application State
    let currentTab = 'top20';
    let currentCategory = 'all';
    let filterWithPhotoOnly = false;
    let currentView = 'grid'; // 'grid' (2-col mobile, 3-col desktop), 'list' (1-col), 'table'
    let searchQuery = '';

    // Poster Modal State
    let currentPosterTeam = null;
    let currentPosterAspect = 'portrait';
    let photoCache = {};

    // Upload Modal State
    let currentUploadTeam = null;
    let selectedPhotoBase64 = null;
    let currentPhotoTeamName = null;

    // Theme Management (Light matching IIC Portal as default, optional Dark Mode)
    function initTheme() {
      const saved = localStorage.getItem('sih_theme') || 'light';
      document.documentElement.setAttribute('data-theme', saved);
      updateThemeUI(saved);
    }

    function toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('sih_theme', next);
      updateThemeUI(next);
    }

    function updateThemeUI(theme) {
      const icon = document.getElementById('themeIcon');
      const label = document.getElementById('themeLabel');
      if (icon) {
        icon.setAttribute('data-lucide', theme === 'dark' ? 'sun' : 'moon');
      }
      if (label) {
        label.textContent = theme === 'dark' ? 'Light' : 'Dark';
      }
      if (window.lucide) lucide.createIcons();
    }

    function init() {
      initTheme();

      // Check URL hash or localStorage for tab
      const hash = window.location.hash.replace('#', '').toLowerCase();
      const savedTab = localStorage.getItem('sih_default_tab');
      if (hash === 'ssip' || savedTab === 'ssip') {
        currentTab = 'ssip';
        localStorage.removeItem('sih_default_tab');
      } else if (hash === 'all') {
        currentTab = 'all';
      }

      updateTabUI();
      render();

      // Background silent auto-poll for new attendance selfies
      setInterval(syncLivePhotosSilently, 20000);
    }

    async function syncLivePhotosSilently() {
      try {
        const res = await fetch('/api/sih-results?t=' + Date.now(), { cache: 'no-store' });
        if (!res.ok) return;
        const freshTeams = await res.json();
        if (!Array.isArray(freshTeams)) return;

        let changed = false;
        freshTeams.forEach(fresh => {
          const local = ALL_TEAMS.find(t => t.team_name === fresh.team_name || t.reg_id === fresh.reg_id);
          if (local) {
            if (fresh.photo_url && fresh.photo_url !== local.photo_url) {
              local.photo_url = fresh.photo_url;
              local.has_photo = true;
              changed = true;
            }
          }
        });

        if (changed) {
          render();
        }
      } catch (err) {
        // silent fail
      }
    }

    function switchTab(tab) {
      currentTab = tab;
      updateTabUI();
      render();
    }

    function updateTabUI() {
      document.querySelectorAll('.tabs-row .tab-btn').forEach(btn => btn.classList.remove('active'));
      if (currentTab === 'top20') document.getElementById('tabBtnTop20').classList.add('active');
      if (currentTab === 'ssip') document.getElementById('tabBtnSsip').classList.add('active');
      if (currentTab === 'all') document.getElementById('tabBtnAll').classList.add('active');
    }

    function setCategoryFilter(cat, btn) {
      currentCategory = cat;
      document.querySelectorAll('.filter-pills .pill-btn').forEach(b => {
        if (b.innerText.includes('Software') || b.innerText.includes('Hardware') || b.innerText.includes('All Domains')) {
          b.classList.remove('active');
        }
      });
      btn.classList.add('active');
      render();
    }

    function setPhotoFilter(btn) {
      filterWithPhotoOnly = !filterWithPhotoOnly;
      btn.classList.toggle('active', filterWithPhotoOnly);
      render();
    }

    function setViewMode(mode) {
      currentView = mode;
      document.getElementById('btnViewGrid').classList.toggle('active', mode === 'grid');
      document.getElementById('btnViewList').classList.toggle('active', mode === 'list');
      document.getElementById('btnViewTable').classList.toggle('active', mode === 'table');
      render();
    }

    function handleSearch() {
      searchQuery = (document.getElementById('searchInput').value || '').trim().toLowerCase();
      render();
    }

    function getFilteredTeams() {
      return ALL_TEAMS.filter(t => {
        // Tab Filter
        if (currentTab === 'top20' && !t.is_top_20) return false;
        if (currentTab === 'ssip' && !t.is_ssip) return false;

        // Category Filter
        if (currentCategory !== 'all' && t.category !== currentCategory) return false;

        // Photo Filter
        const hasPhoto = Boolean(t.has_photo || t.photo_url);
        if (filterWithPhotoOnly && !hasPhoto) return false;

        // Search Filter
        if (searchQuery) {
          const term = searchQuery;
          const matchName = (t.team_name || '').toLowerCase().includes(term);
          const matchLeader = (t.leader_name || '').toLowerCase().includes(term);
          const matchPsid = (t.psid || '').toLowerCase().includes(term);
          const matchReg = (t.reg_id || '').toLowerCase().includes(term);
          if (!matchName && !matchLeader && !matchPsid && !matchReg) return false;
        }

        return true;
      });
    }

    function render() {
      const photoCount = ALL_TEAMS.filter(t => t.has_photo || t.photo_url).length;
      const elMetricPhotos = document.getElementById('metricPhotos');
      if (elMetricPhotos) elMetricPhotos.textContent = photoCount;
      const elMetricTotal = document.getElementById('metricTotal');
      if (elMetricTotal) elMetricTotal.textContent = ALL_TEAMS.length;

      const teams = getFilteredTeams();
      const cardsContainer = document.getElementById('cardsView');
      const tableContainer = document.getElementById('tableView');

      if (currentView === 'grid' || currentView === 'list') {
        cardsContainer.style.display = 'grid';
        tableContainer.style.display = 'none';
        if (currentView === 'list') {
          cardsContainer.classList.add('list-view');
        } else {
          cardsContainer.classList.remove('list-view');
        }
        renderCards(teams, cardsContainer);
      } else {
        cardsContainer.style.display = 'none';
        tableContainer.style.display = 'block';
        renderTable(teams, tableContainer);
      }

      if (window.lucide) {
        lucide.createIcons();
      }
    }

    function renderCards(teams, container) {
      if (teams.length === 0) {
        container.innerHTML = `
          <div style="grid-column: 1/-1; padding: 60px 20px; text-align: center; color: var(--text-dim);">
            <i data-lucide="search-x" style="width: 44px; height: 44px; margin: 0 auto 12px; display: block; opacity: 0.5;"></i>
            <h3 style="font-size: 1.1rem; color: var(--text-main); margin-bottom: 6px;">No teams match the filter</h3>
            <p style="font-size: 13px;">Try selecting another category or clearing your search term.</p>
          </div>
        `;
        return;
      }

      container.innerHTML = teams.map(t => {
        let rankClass = 'rank-eval';
        let rankBadge = `#${t.rank}`;
        if (t.rank === 1) { rankClass = 'rank-1'; rankBadge = '🥇 #1 Winner'; }
        else if (t.rank === 2) { rankClass = 'rank-2'; rankBadge = '🥈 #2 Runner'; }
        else if (t.rank === 3) { rankClass = 'rank-3'; rankBadge = '🥉 #3'; }
        else if (t.is_top_20) { rankClass = 'rank-top'; rankBadge = `⭐ Top 20 (#${t.rank})`; }

        let scoreClass = 'muted';
        if (t.rank <= 3) scoreClass = 'gold';
        else if (t.is_top_20) scoreClass = 'emerald';

        const isGoldCard = t.rank <= 3;
        const hasPhoto = Boolean(t.has_photo || t.photo_url);

        return `
          <div class="team-card ${isGoldCard ? 'gold-tier' : ''}" data-team="${escapeHtml(t.team_name)}">
            
            <!-- Card Top Bar: Rank & Category -->
            <div class="card-topbar">
              <span class="rank-pill ${rankClass}">${rankBadge}</span>
              <span class="category-badge ${t.category.toLowerCase()}">${t.category}</span>
            </div>

            <!-- Card Photo Wrapper -->
            <div class="card-photo-wrapper" onclick="${hasPhoto && t.photo_url ? `openPhotoModal('${escapeHtml(t.team_name)}', '${t.photo_url}', '${escapeHtml(t.leader_name)}', '${t.score_str}', '${t.rank}')` : `openUploadModal('${escapeHtml(t.team_name)}', '${t.reg_id || ''}', ${t.team_no || 'null'})`}">
              ${hasPhoto && t.photo_url ? `
                <img src="${t.photo_url}" class="card-photo" alt="${escapeHtml(t.team_name)} Selfie" loading="lazy">
                <span class="photo-tag"><i data-lucide="check-circle" style="width:11px;height:11px;"></i> Verified Selfie</span>
                <span class="photo-zoom-hint"><i data-lucide="maximize-2" style="width:10px;height:10px;"></i> View</span>
              ` : `
                <div class="photo-placeholder">
                  <div class="placeholder-avatar">${escapeHtml(t.team_name.charAt(0).toUpperCase())}</div>
                  <span style="font-size:11px; font-weight:600; color:var(--primary); display:inline-flex; align-items:center; gap:4px;">
                    <i data-lucide="camera" style="width:12px;height:12px;"></i> Upload Team Selfie
                  </span>
                </div>
              `}
            </div>

            <!-- Card Body Content (NO CONTACT NUMBERS) -->
            <div class="card-body">
              
              <div class="team-heading">
                <div style="min-width:0;">
                  <h3 class="team-name">${escapeHtml(t.team_name)}</h3>
                  <div class="team-reg">${t.reg_id || 'GTU-SIH'} • PSID: #${t.psid}</div>
                </div>
                <div class="score-badge">
                  <span class="score-num ${scoreClass}">${t.score_str}</span>
                  <span class="score-sub">Jury Marks</span>
                </div>
              </div>

              ${t.is_ssip ? `
                <div class="ssip-ribbon">
                  <i data-lucide="coins" style="width:14px;height:14px;flex-shrink:0;"></i>
                  <span><strong>SSIP Recommended:</strong> ₹2.5L Grant Support</span>
                </div>
              ` : ''}

              <!-- Team Info (Clean & Privacy Compliant) -->
              <div class="info-list">
                <div class="info-row">
                  <span class="info-label"><i data-lucide="crown" style="width:12px;height:12px;"></i> Team Leader</span>
                  <span class="info-val">${escapeHtml(t.leader_name)}</span>
                </div>
                <div class="info-row">
                  <span class="info-label"><i data-lucide="check-circle-2" style="width:12px;height:12px;"></i> SIH Status</span>
                  <span class="info-val" style="color:${t.is_top_20 ? 'var(--success-dark)' : 'var(--text-dim)'}; font-weight:700;">
                    ${t.is_top_20 ? 'Selected for SIH 2026' : (t.status === 'HONORABLE_MENTION' ? 'Honorable Mention' : 'Evaluated')}
                  </span>
                </div>
              </div>

              <!-- Card Action Buttons -->
              <div class="card-footer-actions">
                <button onclick="openPosterModal('${escapeHtml(t.team_name)}')" class="btn-poster-action" title="Create Achievement Poster">
                  <i data-lucide="sparkles" style="width:14px;height:14px;"></i>
                  <span>Social Poster</span>
                </button>
                ${hasPhoto && t.photo_url ? `
                <button onclick="openPhotoModal('${escapeHtml(t.team_name)}', '${t.photo_url}', '${escapeHtml(t.leader_name)}', '${t.score_str}', '${t.rank}')" class="btn-photo-action" title="View Venue Selfie">
                  <i data-lucide="eye" style="width:14px;height:14px;"></i>
                </button>
                ` : `
                <button onclick="openUploadModal('${escapeHtml(t.team_name)}', '${t.reg_id || ''}', ${t.team_no || 'null'})" class="btn-photo-action" style="border-color:var(--primary-light); color:var(--primary);" title="Upload Team Photo">
                  <i data-lucide="upload" style="width:14px;height:14px;"></i>
                </button>
                `}
              </div>

            </div>
          </div>
        `;
      }).join('');
    }

    function renderTable(teams, container) {
      if (teams.length === 0) {
        container.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-dim);">No teams match the filter.</div>';
        return;
      }

      container.innerHTML = `
        <table class="results-table">
          <thead>
            <tr>
              <th style="width:60px; text-align:center;">Rank</th>
              <th style="width:70px; text-align:center;">Photo</th>
              <th>Team Name</th>
              <th>Category</th>
              <th>PSID</th>
              <th>Team Leader</th>
              <th style="text-align:right;">Score</th>
              <th>Nominations &amp; Grants</th>
              <th style="width:120px; text-align:center;">Action</th>
            </tr>
          </thead>
          <tbody>
            ${teams.map(t => {
              const hasPhoto = Boolean(t.has_photo || t.photo_url);
              let thumbHtml = hasPhoto && t.photo_url 
                ? `<img src="${t.photo_url}" class="table-thumb" alt="Selfie" onclick="openPhotoModal('${escapeHtml(t.team_name)}', '${t.photo_url}', '${escapeHtml(t.leader_name)}', '${t.score_str}', '${t.rank}')">`
                : `<button onclick="openUploadModal('${escapeHtml(t.team_name)}', '${t.reg_id || ''}', ${t.team_no || 'null'})" style="font-size:10.5px; color:var(--primary); background:rgba(15,82,186,0.1); border-radius:5px; border:1px solid rgba(15,82,186,0.3); padding:3px 8px; cursor:pointer;" title="Upload Team Photo">📸 Upload</button>`;

              let rankBadge = `<strong style="font-size:14px;color:var(--text-main);">#${t.rank}</strong>`;
              if (t.rank === 1) rankBadge = '🥇 #1';
              if (t.rank === 2) rankBadge = '🥈 #2';
              if (t.rank === 3) rankBadge = '🥉 #3';

              return `
                <tr>
                  <td style="text-align:center; font-weight:700;">${rankBadge}</td>
                  <td style="text-align:center;">${thumbHtml}</td>
                  <td>
                    <div style="font-weight:800; color:var(--text-main); font-size:14px;">${escapeHtml(t.team_name)}</div>
                    <div style="font-size:11px; color:var(--primary); font-family:monospace;">${t.reg_id}</div>
                  </td>
                  <td>
                    <span class="category-badge ${t.category.toLowerCase()}">${t.category}</span>
                  </td>
                  <td><code style="background:var(--bg-surface-elevated); padding:3px 7px; border-radius:5px; color:var(--primary); font-weight:700; border:1px solid var(--border-color);">${t.psid}</code></td>
                  <td>
                    <div style="font-weight:700; color:var(--text-main); font-size:13.5px;">${escapeHtml(t.leader_name)}</div>
                  </td>
                  <td style="text-align:right;">
                    <strong style="font-size:14px; color:${t.rank<=3 ? 'var(--gold-dark)' : 'var(--success-dark)'};">${t.score_str}</strong>
                  </td>
                  <td>
                    <div style="display:flex; flex-direction:column; gap:4px;">
                      ${t.is_top_20 ? '<span style="color:var(--success-dark); font-size:11.5px; font-weight:700;">⭐ Selected for SIH 2026</span>' : ''}
                      ${t.is_ssip ? '<span style="color:var(--gold-dark); font-size:11px; font-weight:700;">💰 SSIP ₹2,50,000/- Grant</span>' : ''}
                    </div>
                  </td>
                  <td style="text-align:center;">
                    <button onclick="openPosterModal('${escapeHtml(t.team_name)}')" class="btn-poster-action" style="padding:6px 12px; font-size:11.5px;">
                      <i data-lucide="sparkles" style="width:12px;height:12px;"></i>
                      <span>Poster</span>
                    </button>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      `;
    }

    // Photo Lightbox Modal
    function openPhotoModal(teamName, photoUrl, leaderName, score, rank) {
      currentPhotoTeamName = teamName;
      document.getElementById('modalTeamName').textContent = `${teamName} (Rank #${rank})`;
      document.getElementById('modalSub').textContent = `Team Leader: ${leaderName} • Score: ${score}`;
      document.getElementById('modalImg').src = photoUrl;
      document.getElementById('modalMeta').textContent = `Official Internal Hackathon Venue Selfie • ${teamName}`;
      document.getElementById('modalDownload').href = photoUrl;
      document.getElementById('modalDownload').download = `SIH_${teamName.replace(/\s+/g, '_')}_Selfie.jpg`;
      document.getElementById('photoModal').classList.add('open');
      if (window.lucide) lucide.createIcons();
    }

    function closePhotoModal() {
      document.getElementById('photoModal').classList.remove('open');
    }

    function openPosterModalFromCurrentPhoto() {
      closePhotoModal();
      if (currentPhotoTeamName) {
        openPosterModal(currentPhotoTeamName);
      }
    }

    // Direct Upload Modal
    function openUploadModal(teamName, regId, teamNo) {
      currentUploadTeam = { team_name: teamName, reg_id: regId, team_no: teamNo };
      selectedPhotoBase64 = null;
      document.getElementById('uploadModalTeamName').textContent = teamName;
      document.getElementById('uploadModalDetails').textContent = `${regId || 'GTU-ITR'} • Team #${teamNo || 'N/A'}`;
      document.getElementById('uploadPreviewImg').style.display = 'none';
      document.getElementById('uploadPrompt').style.display = 'block';
      document.getElementById('btnSubmitPhotoUpload').disabled = true;
      document.getElementById('uploadAlertBox').style.display = 'none';
      document.getElementById('uploadProgressBox').style.display = 'none';

      const attLink = document.getElementById('uploadAttendanceLink');
      if (attLink && teamNo) {
        attLink.href = `/static/attendance.html?team=${teamNo}`;
      }

      document.getElementById('uploadPhotoModal').classList.add('open');
      if (window.lucide) lucide.createIcons();
    }

    function closeUploadModal() {
      document.getElementById('uploadPhotoModal').classList.remove('open');
    }

    function handleDirectPhotoSelect(input) {
      if (!input.files || !input.files[0]) return;
      const file = input.files[0];

      const reader = new FileReader();
      reader.onload = function(e) {
        selectedPhotoBase64 = e.target.result;
        const img = document.getElementById('uploadPreviewImg');
        img.src = selectedPhotoBase64;
        img.style.display = 'block';
        document.getElementById('uploadPrompt').style.display = 'none';
        document.getElementById('btnSubmitPhotoUpload').disabled = false;
        document.getElementById('uploadAlertBox').style.display = 'none';
      };
      reader.readAsDataURL(file);
    }

    async function submitDirectPhotoUpload() {
      if (!currentUploadTeam || !selectedPhotoBase64) return;

      const progressBox = document.getElementById('uploadProgressBox');
      const alertBox = document.getElementById('uploadAlertBox');
      const submitBtn = document.getElementById('btnSubmitPhotoUpload');

      progressBox.style.display = 'flex';
      submitBtn.disabled = true;
      alertBox.style.display = 'none';

      try {
        const res = await fetch('/api/sih-results/upload-photo', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            team_name: currentUploadTeam.team_name,
            reg_id: currentUploadTeam.reg_id,
            photo: selectedPhotoBase64
          })
        });

        const data = await res.json();
        progressBox.style.display = 'none';

        if (data.success) {
          alertBox.style.display = 'block';
          alertBox.style.background = 'rgba(16, 185, 129, 0.15)';
          alertBox.style.border = '1px solid #10b981';
          alertBox.style.color = '#059669';
          alertBox.innerHTML = `✅ Photo saved! Updated results live.`;

          const local = ALL_TEAMS.find(t => t.team_name === currentUploadTeam.team_name);
          if (local && data.photo_url) {
            local.photo_url = data.photo_url;
            local.has_photo = true;
          }

          render();
          triggerConfetti();

          setTimeout(() => {
            closeUploadModal();
            openPosterModal(currentUploadTeam.team_name);
          }, 1200);
        } else {
          alertBox.style.display = 'block';
          alertBox.style.background = 'rgba(239, 68, 68, 0.15)';
          alertBox.style.border = '1px solid #ef4444';
          alertBox.style.color = '#dc2626';
          alertBox.innerHTML = `❌ Upload failed: ${escapeHtml(data.error || 'Unknown error')}`;
          submitBtn.disabled = false;
        }
      } catch (err) {
        progressBox.style.display = 'none';
        submitBtn.disabled = false;
        alertBox.style.display = 'block';
        alertBox.style.background = 'rgba(239, 68, 68, 0.15)';
        alertBox.style.border = '1px solid #ef4444';
        alertBox.style.color = '#dc2626';
        alertBox.innerHTML = `❌ Error: ${escapeHtml(err.message)}`;
      }
    }

    // =========================================================================
    // POSTER GENERATOR ENGINE (HTML5 CANVAS WITH DUAL OFFICIAL GTU LOGOS)
    // =========================================================================

    function openPosterModal(teamName) {
      const team = ALL_TEAMS.find(t => t.team_name === teamName) || ALL_TEAMS[0];
      if (!team) return;

      currentPosterTeam = team;
      document.getElementById('posterModalTitle').innerHTML = `
        <i data-lucide="sparkles" style="width:18px;height:18px;"></i>
        <span>${escapeHtml(team.team_name)} — Official Achievement Poster</span>
      `;
      document.getElementById('posterModal').classList.add('open');
      updatePosterCaption();
      renderPosterCanvas();
      if (window.lucide) lucide.createIcons();
    }

    function closePosterModal() {
      document.getElementById('posterModal').classList.remove('open');
    }

    function setPosterAspectRatio(aspect) {
      currentPosterAspect = aspect;
      document.getElementById('btnAspectPortrait').classList.toggle('active', aspect === 'portrait');
      document.getElementById('btnAspectSquare').classList.toggle('active', aspect === 'square');
      renderPosterCanvas();
    }

    function getPosterCaption(team) {
      const rankText = team.is_top_20 ? `Top 20 Selection (Rank #${team.rank})` : `Rank #${team.rank}`;
      const ssipText = team.is_ssip ? `\\n💰 Recommended for ₹2,50,000/- SSIP Innovation Grant!` : '';
      return `🎉 Proud moment! Our team "${team.team_name}" has officially been evaluated at the GTU-ITR Internal Smart India Hackathon 2026! 🚀\\n\\n` +
             `🏆 Status: ${rankText}\\n` +
             `⭐ Score: ${team.score_str}\\n` +
             `💡 Category: ${team.category} Edition | PSID: #${team.psid}\\n` +
             `👑 Team Leader: ${team.leader_name}${ssipText}\\n\\n` +
             `Huge gratitude to Gujarat Technological University (GTU) and the Institution's Innovation Council (IIC) for this opportunity! 🎓\\n\\n` +
             `Tagging official handle: @gtu_itr_official 📸\\n` +
             `#SIH2026 #GTUITR #GTU #SmartIndiaHackathon #Innovation #SSIP #StudentInnovators #ProudMoment`;
    }

    function updatePosterCaption() {
      if (!currentPosterTeam) return;
      const caption = getPosterCaption(currentPosterTeam);
      document.getElementById('posterCaptionPreview').textContent = caption;
    }

    function copyPosterCaption() {
      if (!currentPosterTeam) return;
      const text = getPosterCaption(currentPosterTeam);
      navigator.clipboard.writeText(text).then(() => {
        const btnText = document.getElementById('copyCaptionText');
        if (btnText) {
          btnText.textContent = 'Copied!';
          setTimeout(() => { btnText.textContent = 'Copy Caption'; }, 2000);
        }
      });
    }

    // Bulletproof Image Loader
    function loadImageAsync(src) {
      return new Promise((resolve) => {
        if (!src) return resolve(null);
        if (photoCache[src] && photoCache[src].naturalWidth > 0) return resolve(photoCache[src]);

        const img = new Image();
        let resolved = false;

        const finish = (result) => {
          if (resolved) return;
          resolved = true;
          if (result && result.naturalWidth > 0) photoCache[src] = result;
          resolve(result && result.naturalWidth > 0 ? result : null);
        };

        img.onload = () => finish(img);
        img.onerror = () => finish(null);
        setTimeout(() => finish(null), 3500);

        img.src = src;
        if (img.complete && img.naturalWidth > 0) {
          finish(img);
        }
      });
    }

    function drawRoundedRect(ctx, x, y, width, height, radius) {
      ctx.beginPath();
      ctx.moveTo(x + radius, y);
      ctx.lineTo(x + width - radius, y);
      ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
      ctx.lineTo(x + width, y + height - radius);
      ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
      ctx.lineTo(x + radius, y + height);
      ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
      ctx.lineTo(x, y + radius);
      ctx.quadraticCurveTo(x, y, x + radius, y);
      ctx.closePath();
    }

    async function renderPosterCanvas() {
      const team = currentPosterTeam;
      if (!team) return;

      const loader = document.getElementById('posterLoading');
      if (loader) loader.style.display = 'flex';

      const canvas = document.getElementById('posterCanvas');
      const ctx = canvas.getContext('2d');

      const isPortrait = currentPosterAspect === 'portrait';
      const W = 1080;
      const H = isPortrait ? 1350 : 1080;

      canvas.width = W;
      canvas.height = H;

      // Fail-safe Parallel Load GTU University Seal, GTU R&D Seal, and Team Photo
      const [rawUniImg, rawRndImg, teamImg] = await Promise.all([
        loadImageAsync(GTU_UNI_SEAL_URI).catch(() => null),
        loadImageAsync(GTU_RND_SEAL_URI).catch(() => null),
        team.photo_url ? loadImageAsync(team.photo_url).catch(() => null) : Promise.resolve(null)
      ]);

      const domUni = document.getElementById('domGtuUniSeal');
      const domRnd = document.getElementById('domGtuRndSeal');

      const uniLogoImg = (rawUniImg && rawUniImg.naturalWidth > 0) ? rawUniImg :
                         (domUni && domUni.complete && domUni.naturalWidth > 0) ? domUni :
                         await loadImageAsync('/static/gtu_uni_seal_300.png').catch(() => null);

      const rndLogoImg = (rawRndImg && rawRndImg.naturalWidth > 0) ? rawRndImg :
                         (domRnd && domRnd.complete && domRnd.naturalWidth > 0) ? domRnd :
                         await loadImageAsync('/static/gtu_rnd_seal_300.png').catch(() => null);

      // 1. Cosmic Dark Background for High-Contrast Institutional Poster
      const bgGrad = ctx.createLinearGradient(0, 0, W, H);
      bgGrad.addColorStop(0, '#040711');
      bgGrad.addColorStop(0.35, '#0b162c');
      bgGrad.addColorStop(0.7, '#071020');
      bgGrad.addColorStop(1, '#020409');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, W, H);

      // Radial Ambient Glows
      const radial1 = ctx.createRadialGradient(W * 0.15, H * 0.15, 20, W * 0.15, H * 0.15, 520);
      radial1.addColorStop(0, 'rgba(15, 82, 186, 0.35)');
      radial1.addColorStop(1, 'transparent');
      ctx.fillStyle = radial1;
      ctx.fillRect(0, 0, W, H);

      const radial2 = ctx.createRadialGradient(W * 0.85, H * 0.25, 20, W * 0.85, H * 0.25, 480);
      radial2.addColorStop(0, 'rgba(214, 40, 40, 0.22)');
      radial2.addColorStop(1, 'transparent');
      ctx.fillStyle = radial2;
      ctx.fillRect(0, 0, W, H);

      // Outer Decorative Border
      ctx.strokeStyle = team.is_top_20 ? 'rgba(245, 158, 11, 0.45)' : 'rgba(56, 189, 248, 0.35)';
      ctx.lineWidth = 4;
      drawRoundedRect(ctx, 24, 24, W - 48, H - 48, 28);
      ctx.stroke();

      if (isPortrait) {
        // =====================================================================
        // PORTRAIT (4:5 STORY / POST)
        // =====================================================================

        const uniLogoSize = 110;
        const uniLogoX = 65;
        const uniLogoY = 56;

        if (uniLogoImg) {
          ctx.save();
          ctx.shadowColor = 'rgba(245, 158, 11, 0.5)';
          ctx.shadowBlur = 18;
          ctx.drawImage(uniLogoImg, uniLogoX, uniLogoY, uniLogoSize, uniLogoSize);
          ctx.restore();
        }

        const rndLogoSize = 110;
        const rndLogoX = W - 65 - rndLogoSize;
        const rndLogoY = 56;

        if (rndLogoImg) {
          ctx.save();
          ctx.shadowColor = 'rgba(56, 189, 248, 0.5)';
          ctx.shadowBlur = 18;
          ctx.drawImage(rndLogoImg, rndLogoX, rndLogoY, rndLogoSize, rndLogoSize);
          ctx.restore();
        }

        ctx.textAlign = 'center';
        ctx.font = '800 20px Inter, sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.letterSpacing = '1px';
        ctx.fillText('GUJARAT TECHNOLOGICAL UNIVERSITY', W / 2, 82);

        ctx.font = '900 28px Outfit, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('INSTITUTE OF TECHNOLOGY & RESEARCH', W / 2, 115);

        ctx.font = '800 15px Inter, sans-serif';
        ctx.fillStyle = '#38bdf8';
        ctx.fillText("INSTITUTION'S INNOVATION COUNCIL (IIC) & R&D CELL", W / 2, 142);

        const ribW = 820;
        const ribH = 50;
        const ribX = W / 2 - ribW / 2;
        const ribY = 175;

        let bannerText = team.is_top_20 
          ? `🏆 SELECTED FOR SIH 2026 NATIONALS • RANK #${team.rank}`
          : `🌟 EVALUATED PARTICIPANT • RANK #${team.rank}`;

        const rGrad = ctx.createLinearGradient(ribX, 0, ribX + ribW, 0);
        rGrad.addColorStop(0, team.is_top_20 ? '#d97706' : '#1e3a8a');
        rGrad.addColorStop(1, team.is_top_20 ? '#f59e0b' : '#0f52ba');
        ctx.fillStyle = rGrad;
        drawRoundedRect(ctx, ribX, ribY, ribW, ribH, 12);
        ctx.fill();

        ctx.font = '900 22px Outfit, sans-serif';
        ctx.fillStyle = team.is_top_20 ? '#111827' : '#ffffff';
        ctx.fillText(bannerText, W / 2, ribY + 33);

        const pBoxX = 75;
        const pBoxY = 246;
        const pBoxW = W - 150;
        const pBoxH = 515;
        const pRadius = 22;

        if (teamImg) {
          ctx.save();
          drawRoundedRect(ctx, pBoxX, pBoxY, pBoxW, pBoxH, pRadius);
          ctx.clip();
          
          const scale = Math.max(pBoxW / teamImg.width, pBoxH / teamImg.height);
          const sW = teamImg.width * scale;
          const sH = teamImg.height * scale;
          const sX = pBoxX + (pBoxW - sW) / 2;
          const sY = pBoxY + (pBoxH - sH) / 2;
          ctx.drawImage(teamImg, sX, sY, sW, sH);

          const vGrad = ctx.createLinearGradient(0, pBoxY + pBoxH - 120, 0, pBoxY + pBoxH);
          vGrad.addColorStop(0, 'transparent');
          vGrad.addColorStop(1, 'rgba(6, 10, 18, 0.7)');
          ctx.fillStyle = vGrad;
          ctx.fillRect(pBoxX, pBoxY + pBoxH - 120, pBoxW, 120);

          ctx.restore();

          ctx.strokeStyle = team.is_top_20 ? '#fbbf24' : '#38bdf8';
          ctx.lineWidth = 4;
          drawRoundedRect(ctx, pBoxX, pBoxY, pBoxW, pBoxH, pRadius);
          ctx.stroke();

          drawRoundedRect(ctx, pBoxX + 16, pBoxY + 16, 190, 34, 8);
          ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
          ctx.fill();
          ctx.strokeStyle = 'rgba(52, 211, 153, 0.6)';
          ctx.lineWidth = 1;
          ctx.stroke();

          ctx.textAlign = 'left';
          ctx.font = '800 13px Inter, sans-serif';
          ctx.fillStyle = '#34d399';
          ctx.fillText('📸 Verified Venue Selfie', pBoxX + 28, pBoxY + 38);
        } else {
          ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
          drawRoundedRect(ctx, pBoxX, pBoxY, pBoxW, pBoxH, pRadius);
          ctx.fill();
          ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
          ctx.lineWidth = 2;
          ctx.stroke();

          ctx.beginPath();
          ctx.arc(W / 2, pBoxY + 200, 75, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(56, 189, 248, 0.12)';
          ctx.fill();
          ctx.strokeStyle = '#38bdf8';
          ctx.lineWidth = 3;
          ctx.stroke();

          ctx.textAlign = 'center';
          ctx.font = '900 78px Outfit, sans-serif';
          ctx.fillStyle = '#38bdf8';
          ctx.fillText(team.team_name.charAt(0).toUpperCase(), W / 2, pBoxY + 228);

          ctx.font = '800 20px Outfit, sans-serif';
          ctx.fillStyle = '#94a3b8';
          ctx.fillText('OFFICIAL SIH 2026 INNOVATOR TEAM', W / 2, pBoxY + 320);
        }

        const cBoxX = 75;
        const cBoxY = 790;
        const cBoxW = W - 150;
        const cBoxH = 270;
        ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
        drawRoundedRect(ctx, cBoxX, cBoxY, cBoxW, cBoxH, 20);
        ctx.fill();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.textAlign = 'center';
        let teamNameSize = 44;
        ctx.font = `900 ${teamNameSize}px Outfit, sans-serif`;
        while (ctx.measureText(team.team_name).width > (cBoxW - 60) && teamNameSize > 24) {
          teamNameSize -= 2;
          ctx.font = `900 ${teamNameSize}px Outfit, sans-serif`;
        }
        ctx.fillStyle = '#ffffff';
        ctx.fillText(team.team_name, W / 2, cBoxY + 56);

        ctx.font = '800 18px Inter, sans-serif';
        ctx.fillStyle = '#38bdf8';
        const domainText = `[ ${team.category.toUpperCase()} EDITION ]  •  PSID: #${team.psid}`;
        ctx.fillText(domainText, W / 2, cBoxY + 98);

        ctx.font = '600 21px Inter, sans-serif';
        ctx.fillStyle = '#e2e8f0';
        ctx.fillText(`👑 Team Leader: ${team.leader_name}`, W / 2, cBoxY + 144);

        const scW = 380;
        const scH = 46;
        const scX = W / 2 - scW / 2;
        const scY = cBoxY + 164;
        drawRoundedRect(ctx, scX, scY, scW, scH, 10);
        ctx.fillStyle = 'rgba(245, 158, 11, 0.16)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(245, 158, 11, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.font = '900 23px Outfit, sans-serif';
        ctx.fillStyle = '#fbbf24';
        ctx.fillText(`⭐ JURY SCORE: ${team.score_str}`, W / 2, scY + 32);

        if (team.is_ssip) {
          ctx.font = '800 16px Outfit, sans-serif';
          ctx.fillStyle = '#34d399';
          ctx.fillText('💰 RECOMMENDED FOR SSIP ₹2,50,000/- FUNDING GRANT', W / 2, cBoxY + 242);
        }

        const igW = 760;
        const igH = 68;
        const igX = W / 2 - igW / 2;
        const igY = 1085;

        const igGrad = ctx.createLinearGradient(igX, 0, igX + igW, 0);
        igGrad.addColorStop(0, '#f09433');
        igGrad.addColorStop(0.25, '#e6683c');
        igGrad.addColorStop(0.5, '#dc2743');
        igGrad.addColorStop(0.75, '#cc2366');
        igGrad.addColorStop(1, '#bc1888');

        ctx.save();
        ctx.shadowColor = 'rgba(220, 39, 67, 0.45)';
        ctx.shadowBlur = 18;
        ctx.fillStyle = igGrad;
        drawRoundedRect(ctx, igX, igY, igW, igH, 34);
        ctx.fill();
        ctx.restore();

        ctx.textAlign = 'center';
        ctx.font = '900 24px Outfit, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('📸 Tag  @gtu_itr_official  on Instagram', W / 2, igY + 43);

        ctx.font = '700 17px Inter, sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('#SIH2026   #GTUITR   #GTU   #SmartIndiaHackathon   #SSIP   #Innovation', W / 2, 1190);

        if (uniLogoImg) {
          ctx.drawImage(uniLogoImg, 75, 1236, 40, 40);
        }

        ctx.font = '600 14px Inter, sans-serif';
        ctx.fillStyle = '#64748b';
        ctx.textAlign = 'left';
        ctx.fillText('Gujarat Technological University • Innovation & Startup Cell', 124, 1260);
        ctx.textAlign = 'right';
        ctx.fillText('Official Ratified Results • 2026', W - 75, 1260);

      } else {
        // =====================================================================
        // 1:1 SQUARE LAYOUT (1080 x 1080)
        // =====================================================================

        const uniLogoSize = 100;
        const uniLogoX = 65;
        const uniLogoY = 46;

        if (uniLogoImg) {
          ctx.save();
          ctx.shadowColor = 'rgba(245, 158, 11, 0.4)';
          ctx.shadowBlur = 14;
          ctx.drawImage(uniLogoImg, uniLogoX, uniLogoY, uniLogoSize, uniLogoSize);
          ctx.restore();
        }

        const rndLogoSize = 100;
        const rndLogoX = W - 65 - rndLogoSize;
        const rndLogoY = 46;

        if (rndLogoImg) {
          ctx.save();
          ctx.shadowColor = 'rgba(56, 189, 248, 0.4)';
          ctx.shadowBlur = 14;
          ctx.drawImage(rndLogoImg, rndLogoX, rndLogoY, rndLogoSize, rndLogoSize);
          ctx.restore();
        }

        ctx.textAlign = 'center';
        ctx.font = '800 18px Inter, sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.fillText('GUJARAT TECHNOLOGICAL UNIVERSITY', W / 2, 76);

        ctx.font = '900 25px Outfit, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('INSTITUTE OF TECHNOLOGY & RESEARCH', W / 2, 104);

        ctx.font = '800 14px Inter, sans-serif';
        ctx.fillStyle = '#38bdf8';
        ctx.fillText("IIC & R&D CELL • SMART INDIA HACKATHON 2026", W / 2, 128);

        const ribW = 720;
        const ribH = 44;
        const ribX = W / 2 - ribW / 2;
        const ribY = 152;

        let bannerText = team.is_top_20 
          ? `🏆 SELECTED FOR SIH 2026 FINALS • RANK #${team.rank}`
          : `🌟 EVALUATED PARTICIPANT • RANK #${team.rank}`;

        const rGrad = ctx.createLinearGradient(ribX, 0, ribX + ribW, 0);
        rGrad.addColorStop(0, team.is_top_20 ? '#d97706' : '#1e3a8a');
        rGrad.addColorStop(1, team.is_top_20 ? '#f59e0b' : '#0f52ba');
        ctx.fillStyle = rGrad;
        drawRoundedRect(ctx, ribX, ribY, ribW, ribH, 10);
        ctx.fill();

        ctx.font = '900 20px Outfit, sans-serif';
        ctx.fillStyle = team.is_top_20 ? '#111827' : '#ffffff';
        ctx.fillText(bannerText, W / 2, ribY + 29);

        const pBoxX = 160;
        const pBoxY = 210;
        const pBoxW = 760;
        const pBoxH = 370;
        const pRadius = 18;

        if (teamImg) {
          ctx.save();
          drawRoundedRect(ctx, pBoxX, pBoxY, pBoxW, pBoxH, pRadius);
          ctx.clip();
          const scale = Math.max(pBoxW / teamImg.width, pBoxH / teamImg.height);
          const sW = teamImg.width * scale;
          const sH = teamImg.height * scale;
          const sX = pBoxX + (pBoxW - sW) / 2;
          const sY = pBoxY + (pBoxH - sH) / 2;
          ctx.drawImage(teamImg, sX, sY, sW, sH);

          const vGrad = ctx.createLinearGradient(0, pBoxY + pBoxH - 90, 0, pBoxY + pBoxH);
          vGrad.addColorStop(0, 'transparent');
          vGrad.addColorStop(1, 'rgba(6, 10, 18, 0.7)');
          ctx.fillStyle = vGrad;
          ctx.fillRect(pBoxX, pBoxY + pBoxH - 90, pBoxW, 90);
          ctx.restore();

          ctx.strokeStyle = team.is_top_20 ? '#fbbf24' : '#38bdf8';
          ctx.lineWidth = 4;
          drawRoundedRect(ctx, pBoxX, pBoxY, pBoxW, pBoxH, pRadius);
          ctx.stroke();

          drawRoundedRect(ctx, pBoxX + 14, pBoxY + 14, 180, 30, 6);
          ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
          ctx.fill();
          ctx.textAlign = 'left';
          ctx.font = '800 12px Inter, sans-serif';
          ctx.fillStyle = '#34d399';
          ctx.fillText('📸 Verified Venue Selfie', pBoxX + 24, pBoxY + 34);
        } else {
          ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
          drawRoundedRect(ctx, pBoxX, pBoxY, pBoxW, pBoxH, pRadius);
          ctx.fill();

          ctx.textAlign = 'center';
          ctx.font = '900 64px Outfit, sans-serif';
          ctx.fillStyle = '#38bdf8';
          ctx.fillText(team.team_name.charAt(0).toUpperCase(), W / 2, pBoxY + 190);
        }

        const cBoxX = 65;
        const cBoxY = 600;
        const cBoxW = W - 130;
        const cBoxH = 245;
        ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
        drawRoundedRect(ctx, cBoxX, cBoxY, cBoxW, cBoxH, 18);
        ctx.fill();
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.textAlign = 'center';
        let teamNameSize = 38;
        ctx.font = `900 ${teamNameSize}px Outfit, sans-serif`;
        while (ctx.measureText(team.team_name).width > (cBoxW - 60) && teamNameSize > 22) {
          teamNameSize -= 2;
          ctx.font = `900 ${teamNameSize}px Outfit, sans-serif`;
        }
        ctx.fillStyle = '#ffffff';
        ctx.fillText(team.team_name, W / 2, cBoxY + 50);

        ctx.font = '700 17px Inter, sans-serif';
        ctx.fillStyle = '#38bdf8';
        ctx.fillText(`[ ${team.category.toUpperCase()} EDITION ]  •  PSID: #${team.psid}`, W / 2, cBoxY + 86);

        ctx.font = '600 19px Inter, sans-serif';
        ctx.fillStyle = '#e2e8f0';
        ctx.fillText(`👑 Team Leader: ${team.leader_name}`, W / 2, cBoxY + 124);

        const scW = 340;
        const scH = 42;
        const scX = W / 2 - scW / 2;
        const scY = cBoxY + 144;
        drawRoundedRect(ctx, scX, scY, scW, scH, 8);
        ctx.fillStyle = 'rgba(245, 158, 11, 0.16)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(245, 158, 11, 0.5)';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.font = '900 21px Outfit, sans-serif';
        ctx.fillStyle = '#fbbf24';
        ctx.fillText(`⭐ JURY SCORE: ${team.score_str}`, W / 2, scY + 29);

        if (team.is_ssip) {
          ctx.font = '800 15px Outfit, sans-serif';
          ctx.fillStyle = '#34d399';
          ctx.fillText('💰 RECOMMENDED FOR SSIP ₹2,50,000/- GRANT', W / 2, cBoxY + 215);
        }

        const igW = 720;
        const igH = 60;
        const igX = W / 2 - igW / 2;
        const igY = 865;

        const igGrad = ctx.createLinearGradient(igX, 0, igX + igW, 0);
        igGrad.addColorStop(0, '#f09433');
        igGrad.addColorStop(0.25, '#e6683c');
        igGrad.addColorStop(0.5, '#dc2743');
        igGrad.addColorStop(0.75, '#cc2366');
        igGrad.addColorStop(1, '#bc1888');

        ctx.save();
        ctx.shadowColor = 'rgba(220, 39, 67, 0.45)';
        ctx.shadowBlur = 16;
        ctx.fillStyle = igGrad;
        drawRoundedRect(ctx, igX, igY, igW, igH, 30);
        ctx.fill();
        ctx.restore();

        ctx.font = '900 23px Outfit, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('📸 Tag  @gtu_itr_official  on Instagram', W / 2, igY + 38);

        ctx.font = '700 15px Inter, sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('#SIH2026  #GTUITR  #GTU  #SmartIndiaHackathon  #SSIP  #Innovation', W / 2, 955);

        if (uniLogoImg) {
          ctx.drawImage(uniLogoImg, W / 2 - 200, 990, 26, 26);
          ctx.font = '500 13px Inter, sans-serif';
          ctx.fillStyle = '#64748b';
          ctx.textAlign = 'left';
          ctx.fillText('Gujarat Technological University • Innovation & Startup Cell', W / 2 - 165, 1008);
        } else {
          ctx.font = '500 13px Inter, sans-serif';
          ctx.fillStyle = '#64748b';
          ctx.textAlign = 'center';
          ctx.fillText('Gujarat Technological University • Innovation & Startup Cell', W / 2, 1005);
        }
      }

      if (loader) loader.style.display = 'none';
    }

    function downloadPosterImage() {
      const canvas = document.getElementById('posterCanvas');
      const team = currentPosterTeam;
      const safeName = (team ? team.team_name : 'Team').replace(/[^a-zA-Z0-9]/g, '_');
      const filename = `SIH2026_Poster_${safeName}_GTU_ITR.png`;

      if (canvas.toBlob) {
        canvas.toBlob((blob) => {
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          triggerConfetti();
        }, 'image/png');
      } else {
        const a = document.createElement('a');
        a.href = canvas.toDataURL('image/png');
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        triggerConfetti();
      }
    }

    async function sharePoster() {
      const canvas = document.getElementById('posterCanvas');
      const team = currentPosterTeam;
      if (!team) return;

      const caption = getPosterCaption(team);

      if (navigator.share && canvas.toBlob) {
        canvas.toBlob(async (blob) => {
          const file = new File([blob], `SIH2026_${team.team_name.replace(/\s+/g, '_')}.png`, { type: 'image/png' });
          try {
            await navigator.share({
              title: `SIH 2026 - ${team.team_name}`,
              text: caption,
              files: [file]
            });
          } catch (err) {
            copyPosterCaption();
            downloadPosterImage();
          }
        });
      } else {
        copyPosterCaption();
        downloadPosterImage();
      }
    }

    function triggerConfetti() {
      if (window.confetti) {
        confetti({
          particleCount: 120,
          spread: 80,
          origin: { y: 0.6 }
        });
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    window.addEventListener('DOMContentLoaded', () => {
      init();
      setTimeout(triggerConfetti, 800);
    });
  </script>
</body>
</html>
"""

OUTPUT_HTML = '/home/gtu-itr/iic-cell-gtu-itr-/static/sih-results.html'
with open(OUTPUT_HTML, 'w') as f:
    f.write(html_code)

GEN_PY = '/home/gtu-itr/iic-cell-gtu-itr-/static/generate_results_page.py'
with open(GEN_PY, 'w') as f:
    f.write(html_code)

print(f"Generated {OUTPUT_HTML} and {GEN_PY} successfully!")
