import json
import base64

with open('/home/gtu-itr/iic-cell-gtu-itr-/static/sih_2026_results_data.json') as f:
    teams_data = json.load(f)

for t in teams_data:
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
gtu_rnd_uri = 'data:image/png;base64,' + gtu_rnd_b64

html_code = """<!DOCTYPE html>
<html lang="en">
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
    :root {
      /* GTU-ITR IIC Brand Primary Colors */
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

      /* Neutrals & Surfaces - Aligned with GTU-ITR IIC Portal Dark Theme */
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
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: var(--bg-body);
      background-image: 
        radial-gradient(circle at 10% 12%, rgba(15, 82, 186, 0.25) 0%, transparent 45%),
        radial-gradient(circle at 90% 20%, rgba(214, 40, 40, 0.14) 0%, transparent 40%),
        radial-gradient(circle at 50% 85%, rgba(15, 82, 186, 0.15) 0%, transparent 55%);
      background-attachment: fixed;
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      padding-bottom: 60px;
      overflow-x: hidden;
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
      filter: drop-shadow(0 2px 6px rgba(0,0,0,0.4));
      flex-shrink: 0;
    }
    .brand-text {
      min-width: 0;
    }
    .brand-text h1 {
      font-family: 'Outfit', sans-serif;
      font-size: 1.15rem;
      font-weight: 800;
      color: #38bdf8;
      line-height: 1.2;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .brand-text p {
      font-size: 11px;
      color: var(--text-muted);
      font-weight: 500;
      letter-spacing: 0.04em;
      text-transform: uppercase;
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
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-radius: 9px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      border: 1px solid transparent;
      user-select: none;
    }
    .btn--primary {
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
      color: #fff;
      border-color: rgba(56, 189, 248, 0.3);
      box-shadow: 0 2px 8px rgba(15, 82, 186, 0.35);
    }
    .btn--primary:hover {
      background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
      transform: translateY(-1px);
      box-shadow: 0 4px 14px rgba(15, 82, 186, 0.45);
    }
    .btn--outline {
      background: rgba(255,255,255,0.05);
      border-color: var(--border-color);
      color: var(--text-main);
    }
    .btn--outline:hover {
      background: rgba(255,255,255,0.1);
      border-color: #64748b;
    }
    .btn--gold {
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      color: #0b1528;
      font-weight: 700;
      border-color: rgba(251, 191, 36, 0.4);
      box-shadow: 0 2px 8px rgba(245, 158, 11, 0.35);
    }
    .btn--gold:hover {
      filter: brightness(1.1);
      transform: translateY(-1px);
      box-shadow: 0 4px 14px rgba(245, 158, 11, 0.45);
    }
    .btn--secondary {
      background: rgba(255,255,255,0.06);
      color: var(--text-main);
      border: 1px solid var(--border-color);
    }
    .btn--secondary:hover {
      background: rgba(255,255,255,0.12);
    }

    /* Container */
    .container {
      max-width: 1320px;
      margin: 0 auto;
      padding: 24px 20px 0;
      width: 100%;
    }

    /* Hero Banner */
    .hero-banner {
      background: linear-gradient(135deg, rgba(17, 29, 51, 0.95) 0%, rgba(11, 21, 40, 0.92) 100%);
      border: 1.5px solid rgba(56, 189, 248, 0.28);
      border-radius: 24px;
      padding: 36px 32px;
      margin-bottom: 24px;
      box-shadow: 0 20px 40px -15px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255, 255, 255, 0.08);
      position: relative;
      overflow: hidden;
    }
    .hero-banner::before {
      content: '';
      position: absolute;
      top: -40%;
      right: -15%;
      width: 420px;
      height: 420px;
      background: radial-gradient(circle, rgba(15, 82, 186, 0.22) 0%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
    }
    .hero-banner::after {
      content: '';
      position: absolute;
      bottom: -40%;
      left: -15%;
      width: 380px;
      height: 380px;
      background: radial-gradient(circle, rgba(214, 40, 40, 0.14) 0%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
    }
    .hero-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 14px;
      background: rgba(245, 158, 11, 0.15);
      border: 1px solid rgba(245, 158, 11, 0.4);
      border-radius: 9999px;
      color: #fbbf24;
      font-size: 11.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 14px;
    }
    .hero-title {
      font-family: 'Outfit', sans-serif;
      font-size: clamp(1.65rem, 3.8vw, 2.65rem);
      font-weight: 900;
      line-height: 1.18;
      margin-bottom: 12px;
      color: #ffffff;
    }
    .hero-title span {
      background: linear-gradient(135deg, #38bdf8 0%, #60a5fa 50%, #93c5fd 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
      color: var(--text-muted);
      font-size: 14.5px;
      line-height: 1.6;
      max-width: 820px;
      margin-bottom: 22px;
    }

    /* KPI Metrics Cards */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-top: 24px;
    }
    .metric-card {
      background: rgba(11, 21, 40, 0.65);
      backdrop-filter: blur(8px);
      border: 1px solid rgba(56, 189, 248, 0.18);
      border-radius: 16px;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 14px;
      transition: all 0.2s ease;
    }
    .metric-card:hover {
      border-color: rgba(56, 189, 248, 0.35);
      transform: translateY(-2px);
      background: rgba(17, 29, 51, 0.85);
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
      font-size: 1.55rem;
      font-weight: 800;
      color: #ffffff;
      line-height: 1;
    }
    .metric-label {
      font-size: 11.5px;
      color: var(--text-muted);
      margin-top: 4px;
      font-weight: 500;
      line-height: 1.25;
    }

    /* Tab Controls */
    .controls-panel {
      background: rgba(17, 29, 51, 0.75);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border-color);
      border-radius: 20px;
      padding: 16px 20px;
      margin-bottom: 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .tabs-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      border-bottom: 1px solid var(--border-subtle);
      padding-bottom: 12px;
    }
    .tab-btn {
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 10px 18px;
      border-radius: 11px;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s ease;
      user-select: none;
    }
    .tab-btn:hover {
      background: rgba(255, 255, 255, 0.05);
      color: var(--text-main);
    }
    .tab-btn.active {
      background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
      color: #ffffff;
      border-color: rgba(56, 189, 248, 0.4);
      box-shadow: 0 4px 14px rgba(15, 82, 186, 0.4);
    }
    .tab-badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.22);
      font-weight: 700;
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
      background: #0b1528;
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 10px 14px 10px 38px;
      color: var(--text-main);
      font-size: 13px;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    .search-box input:focus {
      border-color: #38bdf8;
      box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
    }
    .search-box i, .search-box svg {
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
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
      background: #0b1528;
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
      border-color: #64748b;
      color: #fff;
    }
    .pill-btn.active {
      background: rgba(15, 82, 186, 0.35);
      border-color: #38bdf8;
      color: #38bdf8;
      box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
    }

    .view-toggles {
      display: flex;
      gap: 6px;
    }
    .icon-toggle {
      background: #0b1528;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      width: 38px;
      height: 38px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s;
    }
    .icon-toggle:hover {
      border-color: #64748b;
      color: #fff;
    }
    .icon-toggle.active {
      background: var(--primary);
      border-color: #38bdf8;
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(15, 82, 186, 0.4);
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
      box-shadow: var(--shadow-md);
      min-width: 0;
    }
    .team-card:hover {
      transform: translateY(-4px);
      border-color: #38bdf8;
      box-shadow: 0 16px 36px -6px rgba(15, 82, 186, 0.4);
    }
    .team-card.gold-tier {
      border-color: rgba(245, 158, 11, 0.45);
    }
    .team-card.gold-tier:hover {
      border-color: #fbbf24;
      box-shadow: 0 16px 36px -6px rgba(245, 158, 11, 0.4);
    }

    /* Card Header / Rank Badge */
    .card-topbar {
      padding: 11px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(11, 21, 40, 0.85);
      border-bottom: 1px solid var(--border-subtle);
    }
    .rank-pill {
      font-family: 'Outfit', sans-serif;
      font-size: 12.5px;
      font-weight: 800;
      padding: 4px 10px;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .rank-pill.rank-1 {
      background: linear-gradient(135deg, #f59e0b, #d97706);
      color: #0b1528;
      font-weight: 900;
    }
    .rank-pill.rank-2 {
      background: linear-gradient(135deg, #e2e8f0, #94a3b8);
      color: #0b1528;
    }
    .rank-pill.rank-3 {
      background: linear-gradient(135deg, #d97706, #b45309);
      color: #fff;
    }
    .rank-pill.rank-top {
      background: rgba(15, 82, 186, 0.25);
      border: 1px solid rgba(56, 189, 248, 0.4);
      color: #38bdf8;
    }
    .rank-pill.rank-eval {
      background: rgba(148, 163, 184, 0.12);
      color: #94a3b8;
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
      background: rgba(15, 82, 186, 0.2);
      color: #60a5fa;
      border: 1px solid rgba(56, 189, 248, 0.35);
    }
    .category-badge.hardware {
      background: rgba(249, 115, 22, 0.15);
      color: #fb923c;
      border: 1px solid rgba(249, 115, 22, 0.3);
    }

    /* Card Photo Box */
    .card-photo-wrapper {
      position: relative;
      width: 100%;
      height: 200px;
      background: #0b1528;
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
      bottom: 10px;
      left: 10px;
      background: rgba(11, 21, 40, 0.88);
      backdrop-filter: blur(6px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 10.5px;
      font-weight: 700;
      color: #34d399;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .photo-zoom-hint {
      position: absolute;
      bottom: 10px;
      right: 10px;
      background: rgba(0,0,0,0.75);
      color: #fff;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 10px;
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
      background: radial-gradient(circle, #172642 0%, #0b1528 100%);
      color: #64748b;
      gap: 8px;
    }
    .placeholder-avatar {
      width: 54px;
      height: 54px;
      border-radius: 14px;
      background: rgba(15, 82, 186, 0.2);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: #38bdf8;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Outfit', sans-serif;
      font-size: 1.4rem;
      font-weight: 800;
    }

    /* Card Content */
    .card-body {
      padding: 16px;
      display: flex;
      flex-direction: column;
      flex-grow: 1;
      gap: 12px;
      min-width: 0;
    }
    .team-heading {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 10px;
      min-width: 0;
    }
    .team-name {
      font-family: 'Outfit', sans-serif;
      font-size: 1.22rem;
      font-weight: 800;
      color: #f8fafc;
      line-height: 1.25;
      word-break: break-word;
      overflow-wrap: break-word;
    }
    .team-reg {
      font-size: 11px;
      color: var(--text-muted);
      font-family: monospace;
      margin-top: 3px;
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
      font-size: 1.35rem;
      font-weight: 900;
      color: #38bdf8;
      line-height: 1;
    }
    .score-num.gold { color: #fbbf24; }
    .score-num.emerald { color: #34d399; }
    .score-num.muted { color: #94a3b8; font-size: 1rem; }
    .score-sub {
      font-size: 10px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      margin-top: 2px;
    }

    /* PSID & Leader */
    .info-list {
      display: flex;
      flex-direction: column;
      gap: 7px;
      background: rgba(11, 21, 40, 0.65);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 9px 12px;
      font-size: 12px;
    }
    .info-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .info-label {
      color: #94a3b8;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 11.5px;
      flex-shrink: 0;
    }
    .info-val {
      color: #f8fafc;
      font-weight: 600;
      text-align: right;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* SSIP Tag */
    .ssip-ribbon {
      background: linear-gradient(135deg, rgba(217, 119, 6, 0.22), rgba(245, 158, 11, 0.12));
      border: 1px solid rgba(245, 158, 11, 0.45);
      border-radius: 8px;
      padding: 7px 11px;
      font-size: 11.5px;
      font-weight: 700;
      color: #fbbf24;
      display: flex;
      align-items: center;
      gap: 7px;
    }

    /* Card Footer Action Buttons */
    .card-footer-actions {
      display: flex;
      gap: 8px;
      margin-top: auto;
      padding-top: 10px;
      border-top: 1px solid var(--border-subtle);
    }
    .btn-poster-action {
      flex: 1;
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.22), rgba(217, 119, 6, 0.12));
      border: 1px solid rgba(245, 158, 11, 0.45);
      color: #fbbf24;
      border-radius: 8px;
      padding: 9px 12px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      user-select: none;
    }
    .btn-poster-action:hover {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.38), rgba(217, 119, 6, 0.28));
      border-color: #fbbf24;
      color: #fff;
      transform: translateY(-1px);
      box-shadow: 0 4px 14px rgba(245, 158, 11, 0.35);
    }
    .btn-photo-action {
      padding: 9px 12px;
      border-radius: 8px;
      font-size: 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border-color);
      color: #94a3b8;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      user-select: none;
    }
    .btn-photo-action:hover {
      background: rgba(255, 255, 255, 0.12);
      color: #fff;
      border-color: #64748b;
    }

    /* Dedicated Compact 2-Column Grid Layout */
    .cards-grid.compact-view {
      grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
      gap: 14px;
    }
    .cards-grid.compact-view .team-card {
      border-radius: 14px;
    }
    .cards-grid.compact-view .card-topbar {
      padding: 7px 10px;
    }
    .cards-grid.compact-view .rank-pill {
      font-size: 11px;
      padding: 2px 7px;
      gap: 4px;
    }
    .cards-grid.compact-view .category-badge {
      font-size: 9.5px;
      padding: 2px 5px;
    }
    .cards-grid.compact-view .card-photo-wrapper {
      height: 125px;
    }
    .cards-grid.compact-view .placeholder-avatar {
      width: 40px;
      height: 40px;
      font-size: 1.15rem;
      border-radius: 10px;
    }
    .cards-grid.compact-view .photo-tag {
      font-size: 9px;
      padding: 2px 6px;
      bottom: 6px;
      left: 6px;
    }
    .cards-grid.compact-view .photo-zoom-hint {
      display: none;
    }
    .cards-grid.compact-view .card-body {
      padding: 10px;
      gap: 8px;
    }
    .cards-grid.compact-view .team-heading {
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
    }
    .cards-grid.compact-view .team-name {
      font-size: 0.94rem;
      line-height: 1.25;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      min-height: 2.3em;
    }
    .cards-grid.compact-view .team-reg {
      display: none;
    }
    .cards-grid.compact-view .score-badge {
      flex-direction: row;
      align-items: center;
      gap: 5px;
    }
    .cards-grid.compact-view .score-num {
      font-size: 1.15rem;
    }
    .cards-grid.compact-view .score-sub {
      font-size: 9px;
      margin-top: 0;
    }
    .cards-grid.compact-view .ssip-ribbon {
      padding: 4px 6px;
      font-size: 9.5px;
      border-radius: 6px;
      gap: 4px;
    }
    .cards-grid.compact-view .ssip-ribbon i, .cards-grid.compact-view .ssip-ribbon svg {
      width: 12px;
      height: 12px;
    }
    .cards-grid.compact-view .info-list {
      padding: 6px 8px;
      font-size: 10.5px;
      gap: 4px;
      border-radius: 6px;
    }
    .cards-grid.compact-view .info-row {
      font-size: 10.5px;
    }
    .cards-grid.compact-view .info-label {
      font-size: 10px;
      gap: 3px;
    }
    .cards-grid.compact-view .info-label i, .cards-grid.compact-view .info-label svg {
      width: 11px;
      height: 11px;
    }
    .cards-grid.compact-view .info-val {
      font-size: 10.5px;
    }
    .cards-grid.compact-view .card-footer-actions {
      padding-top: 6px;
      gap: 4px;
    }
    .cards-grid.compact-view .btn-poster-action {
      padding: 6px 4px;
      font-size: 10.5px;
      gap: 4px;
      border-radius: 6px;
    }
    .cards-grid.compact-view .btn-poster-action i, .cards-grid.compact-view .btn-poster-action svg {
      width: 12px;
      height: 12px;
    }
    .cards-grid.compact-view .btn-photo-action {
      padding: 6px 7px;
      font-size: 10.5px;
      border-radius: 6px;
    }
    .cards-grid.compact-view .btn-photo-action i, .cards-grid.compact-view .btn-photo-action svg {
      width: 12px;
      height: 12px;
    }

    /* Table View */
    .table-wrapper {
      background: var(--bg-card);
      border: 1.5px solid var(--border-card);
      border-radius: 16px;
      overflow-x: auto;
      box-shadow: var(--shadow-sm);
      -webkit-overflow-scrolling: touch;
    }
    .results-table {
      width: 100%;
      min-width: 680px;
      border-collapse: collapse;
      font-size: 13px;
    }
    .results-table th {
      background: #0b1528;
      color: #94a3b8;
      font-weight: 700;
      font-size: 11.5px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 14px 16px;
      text-align: left;
      border-bottom: 1px solid var(--border-color);
    }
    .results-table td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-subtle);
      color: #cbd5e1;
      vertical-align: middle;
    }
    .results-table tr:hover td {
      background: rgba(15, 82, 186, 0.1);
    }
    .table-thumb {
      width: 52px;
      height: 40px;
      border-radius: 6px;
      object-fit: cover;
      cursor: pointer;
      border: 1px solid var(--border-color);
      transition: transform 0.2s;
    }
    .table-thumb:hover {
      transform: scale(1.15);
      border-color: #38bdf8;
    }

    /* Lightbox & Poster Modals */
    .modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.88);
      backdrop-filter: blur(8px);
      z-index: 1000;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .modal-overlay.open { display: flex; }
    .modal-box {
      background: #111d33;
      border: 1.5px solid var(--border-card);
      border-radius: 20px;
      max-width: 720px;
      width: 100%;
      overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(0,0,0,0.7);
      animation: zoomIn 0.2s ease-out;
    }
    @keyframes zoomIn {
      from { opacity: 0; transform: scale(0.95); }
      to { opacity: 1; transform: scale(1); }
    }
    .modal-header {
      padding: 16px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--border-color);
      background: rgba(11, 21, 40, 0.85);
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
      background: #0b1528;
      border-top: 1px solid var(--border-subtle);
    }

    /* Poster Specific Modal Elements */
    .poster-modal-dialog {
      background: #111d33;
      border: 1.5px solid var(--border-card);
      border-radius: 20px;
      max-width: 860px;
      width: 100%;
      max-height: 94vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8);
      animation: zoomIn 0.2s ease-out;
    }
    .poster-canvas-box {
      max-width: 440px;
      width: 100%;
      box-shadow: 0 20px 45px rgba(0,0,0,0.65);
      border-radius: 14px;
      overflow: hidden;
      border: 1.5px solid rgba(56, 189, 248, 0.35);
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
        padding: 24px 18px;
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
        padding-bottom: 8px;
      }
      .tabs-row::-webkit-scrollbar {
        display: none;
      }
      .tab-btn {
        flex-shrink: 0;
        white-space: nowrap;
        padding: 8px 14px;
        font-size: 12.5px;
      }
      .filter-row {
        flex-direction: column;
        align-items: stretch;
        gap: 10px;
      }
      .search-box {
        min-width: 100%;
        width: 100%;
      }
      .filter-actions-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        width: 100%;
      }
      .filter-pills {
        flex-wrap: nowrap;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        flex: 1;
        min-width: 0;
        padding-bottom: 2px;
      }
      .filter-pills::-webkit-scrollbar {
        display: none;
      }
      .pill-btn {
        flex-shrink: 0;
        white-space: nowrap;
        padding: 6px 11px;
        font-size: 11.5px;
      }
      .view-toggles {
        flex-shrink: 0;
      }
      .brand-text p {
        display: none;
      }
    }

    @media (max-width: 640px) {
      .container {
        padding: 14px 10px 0;
      }
      .topbar__inner {
        padding: 10px 12px;
        gap: 10px;
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
        padding: 6px 10px;
        font-size: 11.5px;
        border-radius: 8px;
      }
      .btn--print {
        display: none !important;
      }
      .hero-banner {
        padding: 18px 14px;
        border-radius: 18px;
        margin-bottom: 16px;
      }
      .hero-title {
        font-size: 1.4rem;
      }
      .hero-subtitle {
        font-size: 12.5px;
        line-height: 1.5;
        margin-bottom: 16px;
      }
      .metrics-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin-top: 16px;
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
        font-size: 10.5px;
        line-height: 1.2;
      }
      
      /* Standard Cards View on Mobile */
      .cards-grid {
        grid-template-columns: 1fr;
        gap: 14px;
      }
      .team-card {
        border-radius: 16px;
      }
      .card-photo-wrapper {
        height: 185px;
      }
      .card-body {
        padding: 14px;
        gap: 10px;
      }
      .team-name {
        font-size: 1.15rem;
      }
      .card-footer-actions .btn-poster-action {
        padding: 10px 14px;
        font-size: 12.5px;
      }

      /* Compact 2-Column Grid View on Mobile */
      .cards-grid.compact-view {
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
      }
      .cards-grid.compact-view .card-photo-wrapper {
        height: 110px;
      }
      .cards-grid.compact-view .card-body {
        padding: 8px 6px;
        gap: 5px;
      }
      .cards-grid.compact-view .team-name {
        font-size: 0.84rem;
      }
      .cards-grid.compact-view .score-num {
        font-size: 1.05rem;
      }
      .cards-grid.compact-view .btn-poster-action {
        padding: 5px 3px;
        font-size: 9.5px;
      }
      .cards-grid.compact-view .btn-photo-action {
        padding: 5px 5px;
        font-size: 9.5px;
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

  <!-- Hidden DOM Preload for GTU Logos (Guarantees instant availability) -->
  <img id="domGtuUniSeal" src="/static/gtu_uni_seal_300.png" style="display:none;" alt="GTU Seal">
  <img id="domGtuRndSeal" src="/static/gtu_rnd_seal_300.png" style="display:none;" alt="GTU R&D Seal">

  <!-- Top Bar -->
  <header class="topbar">
    <div class="topbar__inner">
      <a href="/" class="brand-group">
        <img src="/static/gtu_uni_seal_300.png" alt="GTU Logo" class="brand-logo" onerror="this.src='/static/gtu_logo.png'">
        <div class="brand-text">
          <h1>GTU-ITR IIC &amp; R&amp;D Cell</h1>
          <p>Smart India Hackathon (SIH 2026) Internal Results</p>
        </div>
      </a>
      <div class="nav-actions">
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

  <!-- Main Container -->
  <main class="container">
    
    <!-- Hero Banner -->
    <section class="hero-banner">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
        <div>
          <div class="hero-badge">
            <i data-lucide="award" style="width:13px;height:13px;"></i>
            Official Result Declaration • SIH 2026
          </div>
          <h2 class="hero-title">
            Smart India Hackathon 2026<br>
            <span>Internal Hackathon Results &amp; Nominations</span>
          </h2>
          <p class="hero-subtitle">
            Heartiest congratulations to all 36 participating innovator teams of Gujarat Technological University - ITR!
            Below is the officially ratified evaluation roster comprising the <strong>Top 20 Teams Selected for SIH 2026</strong>, 
            along with <strong>15 Projects Recommended for SSIP ₹2,50,000/- Grant Support</strong>.
          </p>
        </div>

        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
          <button onclick="openPosterModal(ALL_TEAMS[0].team_name)" class="btn btn--gold" style="padding: 10px 18px; border-radius: 12px; font-weight: 800;">
            <i data-lucide="sparkles" style="width:16px;height:16px;"></i>
            <span>Create Team Posters</span>
          </button>
        </div>
      </div>

      <!-- KPI Metrics -->
      <div class="metrics-grid">
        <div class="metric-card">
          <div class="metric-icon" style="background:rgba(56, 189, 248, 0.15); color:#38bdf8;">
            <i data-lucide="trophy" style="width:24px;height:24px;"></i>
          </div>
          <div>
            <div class="metric-val" id="metricTop20">20</div>
            <div class="metric-label">Teams Selected for SIH 2026</div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon" style="background:rgba(245, 158, 11, 0.15); color:#fbbf24;">
            <i data-lucide="coins" style="width:24px;height:24px;"></i>
          </div>
          <div>
            <div class="metric-val" id="metricSsip">15</div>
            <div class="metric-label">SSIP Recommended (₹2.5L Grant)</div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon" style="background:rgba(168, 85, 247, 0.15); color:#c084fc;">
            <i data-lucide="camera" style="width:24px;height:24px;"></i>
          </div>
          <div>
            <div class="metric-val" id="metricPhotos">""" + photo_count_str + """</div>
            <div class="metric-label">Verified Venue Selfies</div>
          </div>
        </div>

        <div class="metric-card">
          <div class="metric-icon" style="background:rgba(16, 185, 129, 0.15); color:#34d399;">
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
            <button class="icon-toggle active" id="btnViewGrid" onclick="setViewMode('grid')" title="Detailed Cards View">
              <i data-lucide="layout-grid" style="width:17px;height:17px;"></i>
            </button>
            <button class="icon-toggle" id="btnViewCompact" onclick="setViewMode('compact')" title="Compact 2-Column Grid View">
              <i data-lucide="grid-2x2" style="width:17px;height:17px;"></i>
            </button>
            <button class="icon-toggle" id="btnViewTable" onclick="setViewMode('table')" title="Table Sheet View">
              <i data-lucide="table" style="width:17px;height:17px;"></i>
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
          <h3 id="modalTeamName" style="font-family:'Outfit'; font-size:1.15rem; color:#38bdf8; font-weight:800;">Team Selfie</h3>
          <p id="modalSub" style="font-size:12px; color:#94a3b8;">GTU-ITR Internal Hackathon Venue Capture</p>
        </div>
        <button onclick="closePhotoModal()" style="background:none; border:none; color:#94a3b8; cursor:pointer;">
          <i data-lucide="x" style="width:20px;height:20px;"></i>
        </button>
      </div>
      <div class="modal-img-wrap">
        <img id="modalImg" src="" alt="Team Group Selfie" class="modal-img">
      </div>
      <div class="modal-footer">
        <span id="modalMeta" style="font-size:12px; color:#cbd5e1; font-weight:600;"></span>
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
          <h3 id="uploadModalTitle" style="font-family:'Outfit'; font-size:1.15rem; color:#38bdf8; font-weight:800; display:flex; align-items:center; gap:8px;">
            <i data-lucide="camera" style="width:18px;height:18px;"></i>
            <span>Upload Team Hackathon Photo</span>
          </h3>
          <p id="uploadModalSub" style="font-size:12px; color:#94a3b8;">Attach official group photo or selfie for Results &amp; Social Poster</p>
        </div>
        <button onclick="closeUploadModal()" style="background:none; border:none; color:#94a3b8; cursor:pointer;">
          <i data-lucide="x" style="width:20px;height:20px;"></i>
        </button>
      </div>

      <div style="padding: 18px; background: #0f172a; display: flex; flex-direction: column; gap: 14px;">
        <div style="background: rgba(15, 82, 186, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 10px; padding: 10px 14px;">
          <div style="font-size: 14px; font-weight: 800; color: #f8fafc;" id="uploadModalTeamName"></div>
          <div style="font-size: 12px; color: #94a3b8; margin-top: 3px;" id="uploadModalDetails"></div>
        </div>

        <div id="uploadPreviewArea" style="width: 100%; height: 210px; border: 2px dashed rgba(56, 189, 248, 0.4); border-radius: 12px; background: rgba(30, 41, 59, 0.6); display: flex; flex-direction: column; align-items: center; justify-content: center; overflow: hidden; position: relative;">
          <img id="uploadPreviewImg" src="" style="width: 100%; height: 100%; object-fit: cover; display: none;">
          <div id="uploadPrompt" style="text-align: center; padding: 16px;">
            <i data-lucide="image-plus" style="width: 40px; height: 40px; color: #38bdf8; margin: 0 auto 8px; display: block;"></i>
            <span style="font-size: 13px; color: #cbd5e1; font-weight: 600;">Choose Photo or Take Selfie</span>
            <p style="font-size: 11px; color: #64748b; margin-top: 4px;">Supports JPG, PNG, WEBP</p>
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

        <div id="uploadProgressBox" style="display: none; align-items: center; gap: 10px; padding: 10px; background: rgba(56, 189, 248, 0.15); border-radius: 8px; color: #38bdf8; font-size: 12.5px; font-weight: 600;">
          <div class="spinner"></div>
          <span>Uploading and updating live results...</span>
        </div>

        <div id="uploadAlertBox" style="display: none; padding: 10px; border-radius: 8px; font-size: 12.5px;"></div>

        <button id="btnSubmitPhotoUpload" onclick="submitDirectPhotoUpload()" class="btn btn--primary" style="width: 100%; padding: 11px; font-weight: 800; font-size: 13.5px; display: inline-flex; align-items: center; justify-content: center; gap: 8px;" disabled>
          <i data-lucide="check-circle" style="width: 16px; height: 16px;"></i>
          <span>Save &amp; Update Photo</span>
        </button>

        <div style="text-align: center; margin-top: -2px;">
          <a id="uploadAttendanceLink" href="/attendance" target="_blank" style="font-size: 11.5px; color: #94a3b8; text-decoration: underline;">
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
          <h3 id="posterModalTitle" style="font-family:'Outfit'; font-size:1.2rem; color:#fbbf24; font-weight:800; display:flex; align-items:center; gap:8px;">
            <i data-lucide="sparkles" style="width:18px;height:18px;"></i>
            <span>Team Achievement Poster</span>
          </h3>
          <p style="font-size:12px; color:#94a3b8;">Instagram Story / Post Ready • Tag <strong>@gtu_itr_official</strong></p>
        </div>
        <button onclick="closePosterModal()" style="background:none; border:none; color:#94a3b8; cursor:pointer;">
          <i data-lucide="x" style="width:20px;height:20px;"></i>
        </button>
      </div>

      <!-- Modal Body with Canvas & Controls -->
      <div style="padding: 16px 20px; overflow-y: auto; display: flex; flex-direction: column; align-items: center; gap: 14px; background: #0b1120;">
        <!-- Format selector pills -->
        <div style="display: flex; gap: 10px; align-items: center; justify-content: center; width: 100%;">
          <span style="font-size: 12px; color: #94a3b8; font-weight: 600;">Size:</span>
          <button id="btnAspectPortrait" onclick="setPosterAspectRatio('portrait')" class="pill-btn active">
            📱 4:5 Portrait (Insta Post &amp; Story)
          </button>
          <button id="btnAspectSquare" onclick="setPosterAspectRatio('square')" class="pill-btn">
            🔲 1:1 Square (Feed)
          </button>
        </div>

        <!-- Canvas preview container -->
        <div class="poster-canvas-box">
          <canvas id="posterCanvas"></canvas>
          <div id="posterLoading" style="position: absolute; inset: 0; background: rgba(11, 17, 32, 0.85); backdrop-filter: blur(4px); display: none; align-items: center; justify-content: center; flex-direction: column; gap: 10px; color: #38bdf8;">
            <i data-lucide="loader-2" class="spin" style="width: 32px; height: 32px;"></i>
            <span style="font-size: 13px; font-weight: 600;">Rendering HD Poster with GTU Seal...</span>
          </div>
        </div>

        <!-- Caption Box with Copy Button -->
        <div style="width: 100%; max-width: 500px; background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border-color); border-radius: 10px; padding: 12px 14px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 11.5px; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 5px;">
              <i data-lucide="instagram" style="width: 13px; height: 13px;"></i> Ready-to-Post Instagram Caption:
            </span>
            <button onclick="copyPosterCaption()" class="btn btn--secondary" style="padding: 4px 10px; font-size: 11px; border-radius: 6px;">
              <i data-lucide="copy" style="width: 12px; height: 12px;"></i>
              <span id="copyCaptionText">Copy Caption</span>
            </button>
          </div>
          <p id="posterCaptionPreview" style="font-size: 12px; color: #cbd5e1; line-height: 1.5; margin: 0; white-space: pre-line; user-select: all; font-family: sans-serif;"></p>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="modal-footer" style="padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; background: #0f172a;">
        <div style="display: flex; align-items: center; gap: 8px; color: #94a3b8; font-size: 12px;">
          <span style="display: inline-flex; align-items: center; gap: 4px; color: #fbbf24; font-weight: 700;">
            <i data-lucide="instagram" style="width: 14px; height: 14px;"></i> @gtu_itr_official
          </span>
          <span>• Official GTU Seal Verified</span>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <button onclick="sharePoster()" id="btnSharePoster" class="btn btn--secondary" style="padding: 8px 16px; font-size: 12.5px; border-radius: 8px; display: inline-flex; align-items: center; gap: 6px;">
            <i data-lucide="share-2" style="width: 14px; height: 14px;"></i>
            <span>Share</span>
          </button>
          <button onclick="downloadPosterImage()" class="btn btn--gold" style="padding: 8px 18px; font-size: 12.5px; font-weight: 800; border-radius: 8px; display: inline-flex; align-items: center; gap: 6px;">
            <i data-lucide="download" style="width: 15px; height: 15px;"></i>
            <span>Download Poster (PNG)</span>
          </button>
        </div>
      </div>
    </div>
  </div>

  <script>
    // Embedded Official SIH 2026 Dataset & Logos
    let ALL_TEAMS = """ + teams_json_str + """;
    const GTU_UNI_SEAL_URI = '""" + gtu_uni_uri + """';
    const GTU_RND_SEAL_URI = '""" + gtu_rnd_uri + """';

    let currentTab = 'top20';
    let currentCategory = 'all';
    let filterWithPhotoOnly = false;
    let currentView = 'grid';
    let searchQuery = '';
    let currentPhotoTeamName = '';

    // Poster Modal State
    let currentPosterTeam = null;
    let currentPosterAspect = 'portrait';
    const photoCache = {};

    function init() {
      // Check URL Hash or localStorage for initial tab
      const hash = (window.location.hash || '').replace('#', '');
      if (hash === 'ssip' || hash === 'top20' || hash === 'all') {
        switchTab(hash);
      } else {
        const savedTab = localStorage.getItem('sih_default_tab');
        if (savedTab) {
          localStorage.removeItem('sih_default_tab');
          switchTab(savedTab);
        }
      }

      // Preload GTU Logos into cache
      loadImageAsync(GTU_UNI_SEAL_URI);
      loadImageAsync(GTU_RND_SEAL_URI);

      if (window.lucide) lucide.createIcons();
      render();
      syncLiveResults();
    }

    async function syncLiveResults() {
      try {
        const res = await fetch('/api/sih-results?t=' + Date.now(), { cache: 'no-store' });
        if (res.ok) {
          const freshTeams = await res.json();
          if (Array.isArray(freshTeams) && freshTeams.length > 0) {
            let changed = false;
            if (freshTeams.length !== ALL_TEAMS.length) {
              changed = true;
            } else {
              for (let i = 0; i < freshTeams.length; i++) {
                if (freshTeams[i].photo_url !== ALL_TEAMS[i].photo_url || freshTeams[i].has_photo !== ALL_TEAMS[i].has_photo) {
                  changed = true;
                  break;
                }
              }
            }
            if (changed) {
              ALL_TEAMS = freshTeams;
              render();
              console.log('[Live Sync] Results updated with newly uploaded photos.');
            }
          }
        }
      } catch (e) {
        console.debug('Live sync check:', e);
      }
    }

    setInterval(syncLiveResults, 15000);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') syncLiveResults();
    });

    function switchTab(tab) {
      currentTab = tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      if (tab === 'top20') document.getElementById('tabBtnTop20').classList.add('active');
      if (tab === 'ssip') document.getElementById('tabBtnSsip').classList.add('active');
      if (tab === 'all') document.getElementById('tabBtnAll').classList.add('active');
      render();
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
      const btnCompact = document.getElementById('btnViewCompact');
      if (btnCompact) btnCompact.classList.toggle('active', mode === 'compact');
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

      if (currentView === 'grid' || currentView === 'compact') {
        cardsContainer.style.display = 'grid';
        tableContainer.style.display = 'none';
        if (currentView === 'compact') {
          cardsContainer.classList.add('compact-view');
        } else {
          cardsContainer.classList.remove('compact-view');
        }
        renderGrid(teams, cardsContainer);
      } else {
        cardsContainer.style.display = 'none';
        tableContainer.style.display = 'block';
        renderTable(teams, tableContainer);
      }

      if (window.lucide) lucide.createIcons();
    }

    function renderGrid(teams, container) {
      if (teams.length === 0) {
        container.innerHTML = `
          <div style="grid-column: 1/-1; text-align:center; padding: 60px 20px; background:var(--bg-card); border-radius:16px; border:1px dashed var(--border-color);">
            <i data-lucide="search-x" style="width:48px;height:48px;color:#64748b;margin-bottom:12px;"></i>
            <h3 style="font-size:1.2rem;color:#f8fafc;margin-bottom:6px;">No Teams Found</h3>
            <p style="color:#94a3b8;font-size:13px;">Try clearing filters or adjusting your search keyword.</p>
          </div>
        `;
        return;
      }

      container.innerHTML = teams.map(t => {
        const isGold = t.rank <= 3;
        let rankClass = 'rank-top';
        let rankLabel = `#${t.rank} Nominated`;
        if (t.rank === 1) { rankClass = 'rank-1'; rankLabel = '🥇 Rank 1 (Top Winner)'; }
        else if (t.rank === 2) { rankClass = 'rank-2'; rankLabel = '🥈 Rank 2 (1st Runner Up)'; }
        else if (t.rank === 3) { rankClass = 'rank-3'; rankLabel = '🥉 Rank 3 (2nd Runner Up)'; }
        else if (!t.is_top_20) { rankClass = 'rank-eval'; rankLabel = `Rank #${t.rank}`; }

        const catClass = (t.category || '').toLowerCase() === 'hardware' ? 'hardware' : 'software';

        // Photo HTML
        let photoHtml = '';
        const hasPhoto = Boolean(t.has_photo || t.photo_url);
        if (hasPhoto && t.photo_url) {
          photoHtml = `
            <div class="card-photo-wrapper" onclick="openPhotoModal('${escapeHtml(t.team_name)}', '${t.photo_url}', '${escapeHtml(t.leader_name)}', '${t.score_str}', '${t.rank}')">
              <img src="${t.photo_url}" alt="${escapeHtml(t.team_name)}" class="card-photo" loading="lazy">
              <span class="photo-tag"><i data-lucide="camera" style="width:11px;height:11px;"></i> Verified Selfie</span>
              <span class="photo-zoom-hint"><i data-lucide="maximize-2" style="width:10px;height:10px;"></i> View Photo</span>
            </div>
          `;
        } else {
          const initial = t.team_name.charAt(0).toUpperCase();
          photoHtml = `
            <div class="card-photo-wrapper">
              <div class="photo-placeholder">
                <div class="placeholder-avatar">${initial}</div>
                <span style="font-size:11.5px;color:#94a3b8;display:inline-flex;align-items:center;gap:4px;">
                  <i data-lucide="camera-off" style="width:13px;height:13px;"></i> Photo Pending
                </span>
                <button onclick="openUploadModal('${escapeHtml(t.team_name)}', '${t.reg_id || ''}', ${t.team_no || 'null'})" style="margin-top:8px; font-size:11px; font-weight:700; color:#38bdf8; background:rgba(56,189,248,0.14); border-radius:6px; border:1px solid rgba(56,189,248,0.35); padding:4px 10px; cursor:pointer; display:inline-flex; align-items:center; gap:4px;" title="Upload Team Group Photo">
                  <i data-lucide="camera" style="width:12px;height:12px;"></i> Upload Photo
                </button>
              </div>
            </div>
          `;
        }

        // Score color
        let scoreClass = 'emerald';
        if (isGold) scoreClass = 'gold';
        if (t.score_str === 'Absent') scoreClass = 'muted';

        return `
          <div class="team-card ${isGold ? 'gold-tier' : ''}">
            <div class="card-topbar">
              <span class="rank-pill ${rankClass}">${rankLabel}</span>
              <span class="category-badge ${catClass}">${t.category}</span>
            </div>

            ${photoHtml}

            <div class="card-body">
              <div class="team-heading">
                <div>
                  <h3 class="team-name">${escapeHtml(t.team_name)}</h3>
                  <div class="team-reg">${t.reg_id !== '-' ? t.reg_id : 'Internal Entry'} • PSID: <strong>${t.psid}</strong></div>
                </div>
                <div class="score-badge">
                  <div class="score-num ${scoreClass}">${t.score_str}</div>
                  <div class="score-sub">${t.score_str === 'Absent' ? 'Status' : 'Jury Score'}</div>
                </div>
              </div>

              ${t.is_ssip ? `
                <div class="ssip-ribbon">
                  <i data-lucide="coins" style="width:15px;height:15px;flex-shrink:0;"></i>
                  <span><strong>SSIP Recommended:</strong> ₹2,50,000/- Grant Support</span>
                </div>
              ` : ''}

              <div class="info-list">
                <div class="info-row">
                  <span class="info-label"><i data-lucide="crown" style="width:12px;height:12px;"></i> Team Leader</span>
                  <span class="info-val">${escapeHtml(t.leader_name)}</span>
                </div>
                ${t.leader_phone && t.leader_phone !== '-' ? `
                <div class="info-row">
                  <span class="info-label"><i data-lucide="phone" style="width:12px;height:12px;"></i> Contact</span>
                  <span class="info-val" style="font-family:monospace;">+${escapeHtml(t.leader_phone)}</span>
                </div>
                ` : ''}
                <div class="info-row">
                  <span class="info-label"><i data-lucide="check-circle-2" style="width:12px;height:12px;"></i> SIH Status</span>
                  <span class="info-val" style="color:${t.is_top_20 ? '#34d399' : '#94a3b8'}">
                    ${t.is_top_20 ? 'Selected for SIH 2026' : (t.status === 'HONORABLE_MENTION' ? 'Honorable Mention' : 'Evaluated')}
                  </span>
                </div>
              </div>

              <!-- Card Action Buttons -->
              <div class="card-footer-actions">
                <button onclick="openPosterModal('${escapeHtml(t.team_name)}')" class="btn-poster-action">
                  <i data-lucide="sparkles" style="width:14px;height:14px;"></i>
                  <span>Social Poster</span>
                </button>
                ${hasPhoto && t.photo_url ? `
                <button onclick="openPhotoModal('${escapeHtml(t.team_name)}', '${t.photo_url}', '${escapeHtml(t.leader_name)}', '${t.score_str}', '${t.rank}')" class="btn-photo-action" title="View Full Selfie">
                  <i data-lucide="eye" style="width:14px;height:14px;"></i>
                </button>
                ` : `
                <button onclick="openUploadModal('${escapeHtml(t.team_name)}', '${t.reg_id || ''}', ${t.team_no || 'null'})" class="btn-photo-action" style="border-color:rgba(56,189,248,0.4); color:#38bdf8;" title="Upload Team Photo">
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
        container.innerHTML = '<div style="padding:40px;text-align:center;color:#94a3b8;">No teams match the filter.</div>';
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
                : `<button onclick="openUploadModal('${escapeHtml(t.team_name)}', '${t.reg_id || ''}', ${t.team_no || 'null'})" style="font-size:10.5px; color:#38bdf8; background:rgba(56,189,248,0.14); border-radius:5px; border:1px solid rgba(56,189,248,0.3); padding:3px 8px; cursor:pointer;" title="Upload Team Group Photo">📸 Upload</button>`;

              let rankBadge = `<strong style="font-size:14px;color:#f8fafc;">#${t.rank}</strong>`;
              if (t.rank === 1) rankBadge = '🥇 #1';
              if (t.rank === 2) rankBadge = '🥈 #2';
              if (t.rank === 3) rankBadge = '🥉 #3';

              return `
                <tr>
                  <td style="text-align:center; font-weight:700;">${rankBadge}</td>
                  <td style="text-align:center;">${thumbHtml}</td>
                  <td>
                    <div style="font-weight:700; color:#f8fafc; font-size:14px;">${escapeHtml(t.team_name)}</div>
                    <div style="font-size:11px; color:#64748b; font-family:monospace;">${t.reg_id}</div>
                  </td>
                  <td>
                    <span class="category-badge ${t.category.toLowerCase()}">${t.category}</span>
                  </td>
                  <td><code style="background:#0f172a; padding:2px 6px; border-radius:4px; color:#38bdf8;">${t.psid}</code></td>
                  <td>
                    <div style="font-weight:600; color:#e2e8f0;">${escapeHtml(t.leader_name)}</div>
                    <div style="font-size:11px; color:#64748b;">${t.leader_phone || '-'}</div>
                  </td>
                  <td style="text-align:right;">
                    <strong style="font-size:14px; color:${t.rank<=3 ? '#fbbf24' : '#34d399'};">${t.score_str}</strong>
                  </td>
                  <td>
                    <div style="display:flex; flex-direction:column; gap:4px;">
                      ${t.is_top_20 ? '<span style="color:#34d399; font-size:11.5px; font-weight:700;">⭐ Selected for SIH 2026</span>' : ''}
                      ${t.is_ssip ? '<span style="color:#fbbf24; font-size:11px; font-weight:700;">💰 SSIP ₹2,50,000/- Grant</span>' : ''}
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

    // =========================================================================
    // DIRECT PHOTO UPLOAD & REAL-TIME SYNC ENGINE
    // =========================================================================
    let currentUploadTeam = null;
    let selectedPhotoBase64 = null;

    function openUploadModal(teamName, regId, teamNo) {
      const team = ALL_TEAMS.find(t => t.team_name.toLowerCase().trim() === teamName.toLowerCase().trim()) || { team_name: teamName, reg_id: regId, team_no: teamNo };
      currentUploadTeam = team;
      selectedPhotoBase64 = null;

      document.getElementById('uploadModalTeamName').textContent = `${team.team_name} (Rank #${team.rank || '-'})`;
      document.getElementById('uploadModalDetails').textContent = `Leader: ${team.leader_name || '-'} • Category: ${team.category || '-'} • Score: ${team.score_str || '-'}`;
      
      const previewImg = document.getElementById('uploadPreviewImg');
      const promptArea = document.getElementById('uploadPrompt');
      const submitBtn = document.getElementById('btnSubmitPhotoUpload');
      const alertBox = document.getElementById('uploadAlertBox');
      const progressBox = document.getElementById('uploadProgressBox');
      const attLink = document.getElementById('uploadAttendanceLink');

      previewImg.src = '';
      previewImg.style.display = 'none';
      promptArea.style.display = 'block';
      submitBtn.disabled = true;
      alertBox.style.display = 'none';
      progressBox.style.display = 'none';

      const tNo = team.team_no || teamNo;
      if (tNo) {
        attLink.href = `/static/attendance.html?team=${tNo}`;
        attLink.style.display = 'inline-block';
      } else {
        attLink.href = '/attendance';
        attLink.style.display = 'inline-block';
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
        const img = new Image();
        img.onload = function() {
          const maxDim = 1280;
          let w = img.width;
          let h = img.height;
          if (w > maxDim || h > maxDim) {
            if (w > h) {
              h = Math.round((h * maxDim) / w);
              w = maxDim;
            } else {
              w = Math.round((w * maxDim) / h);
              h = maxDim;
            }
          }

          const canvas = document.createElement('canvas');
          canvas.width = w;
          canvas.height = h;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, w, h);

          selectedPhotoBase64 = canvas.toDataURL('image/jpeg', 0.85);

          const previewImg = document.getElementById('uploadPreviewImg');
          const promptArea = document.getElementById('uploadPrompt');
          const submitBtn = document.getElementById('btnSubmitPhotoUpload');

          previewImg.src = selectedPhotoBase64;
          previewImg.style.display = 'block';
          promptArea.style.display = 'none';
          submitBtn.disabled = false;
        };
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
    }

    async function submitDirectPhotoUpload() {
      if (!currentUploadTeam || !selectedPhotoBase64) return;

      const submitBtn = document.getElementById('btnSubmitPhotoUpload');
      const progressBox = document.getElementById('uploadProgressBox');
      const alertBox = document.getElementById('uploadAlertBox');

      submitBtn.disabled = true;
      progressBox.style.display = 'flex';
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

        if (res.ok && data.success) {
          progressBox.style.display = 'none';
          alertBox.style.display = 'block';
          alertBox.style.background = 'rgba(16, 185, 129, 0.2)';
          alertBox.style.border = '1px solid #10b981';
          alertBox.style.color = '#34d399';
          alertBox.innerHTML = `✅ Photo updated successfully! Refreshing view...`;

          // Update local dataset
          const teamInAll = ALL_TEAMS.find(t => t.team_name.toLowerCase().trim() === currentUploadTeam.team_name.toLowerCase().trim());
          if (teamInAll) {
            teamInAll.photo_url = selectedPhotoBase64;
            teamInAll.has_photo = true;
          }

          // Update header metric count
          const photoCount = ALL_TEAMS.filter(t => t.photo_url).length;
          const metricPhotos = document.getElementById('metricPhotos');
          if (metricPhotos) metricPhotos.textContent = photoCount;

          setTimeout(() => {
            closeUploadModal();
            renderCards(filterTeams(), document.getElementById('cardsView'));
            if (window.confetti) {
              confetti({ particleCount: 60, spread: 70, origin: { y: 0.6 } });
            }
            openPosterModal(currentUploadTeam.team_name);
          }, 1000);

        } else {
          throw new Error(data.error || 'Failed to upload photo.');
        }

      } catch (err) {
        progressBox.style.display = 'none';
        submitBtn.disabled = false;
        alertBox.style.display = 'block';
        alertBox.style.background = 'rgba(239, 68, 68, 0.2)';
        alertBox.style.border = '1px solid #ef4444';
        alertBox.style.color = '#f87171';
        alertBox.innerHTML = `❌ Error: ${escapeHtml(err.message)}`;
      }
    }

    function openPhotoModal(teamName, photoUrl, leaderName, score, rank) {
      currentPhotoTeamName = teamName;
      document.getElementById('modalTeamName').textContent = `${teamName} (Rank #${rank})`;
      document.getElementById('modalSub').textContent = `Team Leader: ${leaderName} • Score: ${score}`;
      document.getElementById('modalImg').src = photoUrl;
      document.getElementById('modalMeta').textContent = `Official Internal Hackathon Venue Selfie • ${teamName}`;
      document.getElementById('modalDownload').href = photoUrl;
      document.getElementById('modalDownload').download = `SIH_${teamName.replace(/\\s+/g, '_')}_Selfie.jpg`;
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

    // Bulletproof Image Loader (never hangs, handles cached, DOM & Data URI instantly)
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

        // Max 3.5 seconds timeout safety
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

      // 1. Cosmic Dark Background
      const bgGrad = ctx.createLinearGradient(0, 0, 0, H);
      bgGrad.addColorStop(0, '#040812');
      bgGrad.addColorStop(0.3, '#0b162a');
      bgGrad.addColorStop(0.7, '#07101e');
      bgGrad.addColorStop(1, '#03060a');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, W, H);

      // Ambient Glows
      const gGold = ctx.createRadialGradient(200, 160, 20, 200, 160, 480);
      gGold.addColorStop(0, 'rgba(245, 158, 11, 0.22)');
      gGold.addColorStop(1, 'transparent');
      ctx.fillStyle = gGold;
      ctx.fillRect(0, 0, W, 600);

      const gCyan = ctx.createRadialGradient(880, H - 220, 20, 880, H - 220, 480);
      gCyan.addColorStop(0, 'rgba(14, 165, 233, 0.22)');
      gCyan.addColorStop(1, 'transparent');
      ctx.fillStyle = gCyan;
      ctx.fillRect(0, H - 650, W, 650);

      // 2. High-tech Outer Border Frame
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
      ctx.lineWidth = 2;
      drawRoundedRect(ctx, 36, 36, W - 72, H - 72, 26);
      ctx.stroke();

      // Golden Corner Crosshairs
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(36, 95); ctx.lineTo(36, 36); ctx.lineTo(95, 36); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(W - 95, 36); ctx.lineTo(W - 36, 36); ctx.lineTo(W - 36, 95); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(36, H - 95); ctx.lineTo(36, H - 36); ctx.lineTo(95, H - 36); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(W - 95, H - 36); ctx.lineTo(W - 36, H - 36); ctx.lineTo(W - 36, H - 95); ctx.stroke();

      if (isPortrait) {
        // =====================================================================
        // 4:5 PORTRAIT LAYOUT (1080 x 1350)
        // =====================================================================

        // 1. TOP-LEFT: OFFICIAL GTU UNIVERSITY EMBLEM MEDALLION
        const uniLogoSize = 118;
        const uniLogoX = 70;
        const uniLogoY = 54;

        if (uniLogoImg) {
          ctx.save();
          ctx.shadowColor = 'rgba(245, 158, 11, 0.45)';
          ctx.shadowBlur = 16;
          ctx.drawImage(uniLogoImg, uniLogoX, uniLogoY, uniLogoSize, uniLogoSize);
          ctx.restore();
        }

        // 2. TOP-RIGHT: GTU-ITR R&D & INNOVATION COUNCIL LOGO
        const rndLogoSize = 118;
        const rndLogoX = W - 70 - rndLogoSize;
        const rndLogoY = 54;

        if (rndLogoImg) {
          ctx.save();
          ctx.shadowColor = 'rgba(56, 189, 248, 0.4)';
          ctx.shadowBlur = 16;
          ctx.drawImage(rndLogoImg, rndLogoX, rndLogoY, rndLogoSize, rndLogoSize);
          ctx.restore();
        }

        // 3. CENTER: INSTITUTIONAL TEXT TITLE HIERARCHY
        ctx.textAlign = 'center';
        ctx.font = '800 19px Inter, sans-serif';
        ctx.fillStyle = '#f8fafc';
        ctx.fillText('GUJARAT TECHNOLOGICAL UNIVERSITY', W / 2, 86);

        ctx.font = '900 27px Outfit, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('INSTITUTE OF TECHNOLOGY & RESEARCH', W / 2, 118);

        ctx.font = '800 15px Inter, sans-serif';
        ctx.fillStyle = '#38bdf8';
        ctx.fillText("INSTITUTION'S INNOVATION COUNCIL (IIC) & R&D CELL", W / 2, 144);

        // Header Divider
        const divGrad = ctx.createLinearGradient(65, 0, W - 65, 0);
        divGrad.addColorStop(0, 'transparent');
        divGrad.addColorStop(0.25, 'rgba(245, 158, 11, 0.8)');
        divGrad.addColorStop(0.75, 'rgba(56, 189, 248, 0.8)');
        divGrad.addColorStop(1, 'transparent');
        ctx.fillStyle = divGrad;
        ctx.fillRect(65, 185, W - 130, 2);

        // Event Title & Badge
        ctx.textAlign = 'center';
        ctx.font = '800 20px Outfit, sans-serif';
        ctx.fillStyle = '#fbbf24';
        ctx.fillText('SMART INDIA HACKATHON 2026 • INTERNAL ROUND', W / 2, 218);

        // Achievement Pill / Ribbon
        const ribW = 760;
        const ribH = 50;
        const ribX = W / 2 - ribW / 2;
        const ribY = 236;

        let bannerText = '';
        let ribColor1 = '#d97706';
        let ribColor2 = '#f59e0b';
        let ribTextColor = '#111827';

        if (team.rank === 1) {
          bannerText = '🥇 CHAMPION • RANK #1 (SIH 2026 NOMINATED)';
        } else if (team.rank === 2) {
          bannerText = '🥈 1ST RUNNER UP • RANK #2 (SIH 2026 NOMINATED)';
        } else if (team.rank === 3) {
          bannerText = '🥉 2ND RUNNER UP • RANK #3 (SIH 2026 NOMINATED)';
        } else if (team.is_top_20) {
          bannerText = `⭐ SELECTED FOR SIH 2026 NATIONAL FINALS • RANK #${team.rank}`;
        } else {
          bannerText = `🌟 OFFICIAL PARTICIPANT & EVALUATED • RANK #${team.rank}`;
          ribColor1 = '#1e3a8a';
          ribColor2 = '#0f52ba';
          ribTextColor = '#ffffff';
        }

        const rGrad = ctx.createLinearGradient(ribX, 0, ribX + ribW, 0);
        rGrad.addColorStop(0, ribColor1);
        rGrad.addColorStop(1, ribColor2);
        ctx.fillStyle = rGrad;
        drawRoundedRect(ctx, ribX, ribY, ribW, ribH, 12);
        ctx.fill();

        ctx.font = '900 22px Outfit, sans-serif';
        ctx.fillStyle = ribTextColor;
        ctx.fillText(bannerText, W / 2, ribY + 33);

        // Team Photo Box
        const pBoxX = 130;
        const pBoxY = 302;
        const pBoxW = 820;
        const pBoxH = 468;
        const pRadius = 20;

        if (teamImg) {
          ctx.save();
          drawRoundedRect(ctx, pBoxX, pBoxY, pBoxW, pBoxH, pRadius);
          ctx.clip();

          // Scale crop aspect cover
          const scale = Math.max(pBoxW / teamImg.width, pBoxH / teamImg.height);
          const sW = teamImg.width * scale;
          const sH = teamImg.height * scale;
          const sX = pBoxX + (pBoxW - sW) / 2;
          const sY = pBoxY + (pBoxH - sH) / 2;
          ctx.drawImage(teamImg, sX, sY, sW, sH);

          // Bottom vignette gradient
          const vGrad = ctx.createLinearGradient(0, pBoxY + pBoxH - 120, 0, pBoxY + pBoxH);
          vGrad.addColorStop(0, 'transparent');
          vGrad.addColorStop(1, 'rgba(6, 10, 18, 0.7)');
          ctx.fillStyle = vGrad;
          ctx.fillRect(pBoxX, pBoxY + pBoxH - 120, pBoxW, 120);

          ctx.restore();

          // Photo Border
          ctx.strokeStyle = team.is_top_20 ? '#fbbf24' : '#38bdf8';
          ctx.lineWidth = 4;
          drawRoundedRect(ctx, pBoxX, pBoxY, pBoxW, pBoxH, pRadius);
          ctx.stroke();

          // Verified Tag
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
          // Placeholder Graphic
          ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
          drawRoundedRect(ctx, pBoxX, pBoxY, pBoxW, pBoxH, pRadius);
          ctx.fill();
          ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
          ctx.lineWidth = 2;
          ctx.stroke();

          // Avatar initial circle
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

        // Team Info Card Box
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

        // Team Name (Dynamic Font Sizing)
        ctx.textAlign = 'center';
        let teamNameSize = 44;
        ctx.font = `900 ${teamNameSize}px Outfit, sans-serif`;
        while (ctx.measureText(team.team_name).width > (cBoxW - 60) && teamNameSize > 24) {
          teamNameSize -= 2;
          ctx.font = `900 ${teamNameSize}px Outfit, sans-serif`;
        }
        ctx.fillStyle = '#ffffff';
        ctx.fillText(team.team_name, W / 2, cBoxY + 56);

        // Category & PSID Pill
        ctx.font = '800 18px Inter, sans-serif';
        ctx.fillStyle = '#38bdf8';
        const domainText = `[ ${team.category.toUpperCase()} EDITION ]  •  PSID: #${team.psid}`;
        ctx.fillText(domainText, W / 2, cBoxY + 98);

        // Leader Name
        ctx.font = '600 21px Inter, sans-serif';
        ctx.fillStyle = '#e2e8f0';
        ctx.fillText(`👑 Team Leader: ${team.leader_name}`, W / 2, cBoxY + 144);

        // Jury Score Badge
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

        // SSIP Banner if applicable
        if (team.is_ssip) {
          ctx.font = '800 16px Outfit, sans-serif';
          ctx.fillStyle = '#34d399';
          ctx.fillText('💰 RECOMMENDED FOR SSIP ₹2,50,000/- FUNDING GRANT', W / 2, cBoxY + 242);
        }

        // =====================================================================
        // INSTAGRAM TAG & SOCIAL MEDIA SECTION (USER REQUIREMENT)
        // =====================================================================
        const igW = 760;
        const igH = 68;
        const igX = W / 2 - igW / 2;
        const igY = 1085;

        // Authentic Instagram Linear Gradient
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

        // Hashtags Row
        ctx.font = '700 17px Inter, sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('#SIH2026   #GTUITR   #GTU   #SmartIndiaHackathon   #SSIP   #Innovation', W / 2, 1190);

        // Official Ratification Footer with Mini GTU Seal
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

        // Left GTU Seal & Right R&D Seal
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

        // Achievement Pill
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

        // Team Photo Box (Square proportion)
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

          // Verified Tag
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

        // Details Box
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

        // Score Badge
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

        // Instagram Banner
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

        // Hashtags
        ctx.font = '700 15px Inter, sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText('#SIH2026  #GTUITR  #GTU  #SmartIndiaHackathon  #SSIP  #Innovation', W / 2, 955);

        // Footer with Mini GTU Seal
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
          const file = new File([blob], `SIH2026_${team.team_name.replace(/\\s+/g, '_')}.png`, { type: 'image/png' });
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

with open('/home/gtu-itr/iic-cell-gtu-itr-/static/sih-results.html', 'w') as f:
    f.write(html_code)

with open('/home/gtu-itr/iic-cell-gtu-itr-/static/generate_results_page.py', 'w') as f:
    f.write(html_code)

print("Generated sih-results.html successfully with authentic GTU Seal and R&D Seal!")
