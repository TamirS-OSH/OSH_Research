import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. ALWAYS READ FROM THE PRISTINE ORIGINAL SOURCE
source_file = os.path.join(SCRIPT_DIR, "IIOSH_Research_Update_2026-06-22_V2.html")
output_file = os.path.join(SCRIPT_DIR, "IIOSH_V2_copy.html")

if not os.path.exists(source_file):
    print(f"❌ Error: Can't find the original source file:\n   {source_file}")
    exit()

print(f"Reading fresh data from pristine source: {os.path.basename(source_file)}")
with open(source_file, "r", encoding="utf-8") as f:
    html = f.read()

print("Applying surgical layout updates...")

# 2. UPGRADE GLOBAL WRAPPER & FONTS
html = re.sub(
    r'<body[^>]*>',
    '<body dir="ltr" style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.6; max-width: 850px; margin: 40px auto; padding: 25px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">',
    html
)

# 3. UPGRADE MAIN NEWSLETTER HEADER TITLE
html = html.replace(
    '<h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">IIOSH Weekly Research Update | לקט מחקרים שבועי</h2>',
    '<h2 style="color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 12px; margin-top: 0; font-size: 26px; font-weight: 800;">IIOSH Weekly Research Update <span style="color: #94a3b8; font-weight: 300; font-size: 20px; margin: 0 10px;">|</span> לקט מחקרים שבועי</h2>'
)

# 4. UPGRADE SUBJECT CATEGORY TITLES (e.g., Occupational Health)
html = html.replace(
    "<h3 style='color: #2980b9; margin-top: 20px;'>",
    "<h3 style='color: #1e3a8a; margin-top: 40px; margin-bottom: 15px; font-size: 22px; font-weight: 700; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;'>"
)

# 5. SURGICALLY INJECT AND INDENT THE "ARTICLES" SUBHEADER RIGHT BELOW THE OVERVIEW BOX
# This targets the closing tag of the original summary box non-greedily
html = html.replace(
    '</p>\n            </div>',
    '</p>\n            </div>\n        <div style="margin: 35px 0 20px 15px; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px;">\n            <span style="color: #475569; font-size: 14px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px; display: inline-block;">Articles / מאמרים מדעיים</span>\n        </div>'
)

# 6. DESIGN UPGRADE: Transform the Summary Box Background into a Floating Premium Card
html = html.replace(
    '<div style="margin: 10px 0 20px 0; padding: 12px 15px; background-color: #eef7f9; border-left: 4px solid #00a8cc; border-radius: 4px; font-style: italic; color: #2c3e50; font-size: 14px; line-height: 1.5;">',
    '<div style="margin: 15px 0 30px 0; padding: 22px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-top: 4px solid #0284c7; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); color: #334155; font-size: 14.5px; line-height: 1.65;">'
)
html = html.replace('<strong>Executive Summary:</strong>', '<strong style="color: #0369a1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Executive Summary:</strong>')
html = html.replace('<strong>תמצית מנהלים:</strong>', '<strong style="color: #0369a1; font-weight: 700;">תמצית מנהלים:</strong>')

# 7. DESIGN UPGRADE: Restyle Individual Article Container Cards
html = html.replace(
    '<div style="margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #3498db; border-radius: 4px;">',
    '<div style="margin-bottom: 25px; padding: 20px; background-color: #fafafa; border: 1px solid #f1f5f9; border-left: 5px solid #2563eb; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.01);">'
)

# 8. ADJUST TYPOGRAPHY AND SPACING INSIDE THE ARTICLE CARDS
html = html.replace('<h4 style="margin: 0 0 5px 0; color: #2c3e50; font-size: 15px;">', '<h4 style="margin: 0 0 8px 0; color: #0f172a; font-size: 16px; font-weight: 700; line-height: 1.4;">')
html = html.replace('<b>Journal:</b>', '<strong style="color: #475569;">Journal:</strong>')
html = html.replace('<p style="margin: 0 0 10px 0; font-size: 14px; color: #444;">', '<p style="margin: 0 0 14px 0; font-size: 14.5px; color: #334155; text-align: justify;">')
html = html.replace('<p dir="rtl" style="margin: 0 0 12px 0; font-size: 14px; color: #2c3e50; text-align: right; line-height: 1.5;">', '<p dir="rtl" style="margin: 0 0 18px 0; font-size: 14.5px; color: #1e293b; text-align: right; line-height: 1.6;">')

# Modernize Links
html = html.replace(
    'style="color: #3498db; text-decoration: none; font-weight: bold; font-size: 13px;"',
    'style="color: #2563eb; text-decoration: none; font-weight: 700; font-size: 13.5px; display: inline-block;"'
)

# 9. SAVE TO THE TARGET COPY FILE NAME
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html)

print("\n" + "="*60)
print(f"🎉 SUCCESS! Clean copy rebuilt from scratch successfully!")
print(f"📁 Target Output File: {os.path.basename(output_file)}")
print("="*60)