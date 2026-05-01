import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Define the source directory and images
brain_dir = r"C:\Users\RAKESH PATRA\.gemini\antigravity\brain\13c50b21-b58b-4b3a-815f-ec15d1047b5e"
output_pdf = "linkedin_premium_carousel.pdf"

# Find all media files and sort them by timestamp (name-based sorting works here)
files = [f for f in os.listdir(brain_dir) if f.startswith("media__") and f.endswith(".png")]
files.sort() # Already in chronological order

# Define titles for each slide (matching the chronological order of chat history)
# 1. Vault Engines, 2. Vault Secret, 3. Grafana, 4. Prometheus, 5. Vote UI, 
# 6. Vote Result, 7. Swagger, 8. GitHub Actions, 9. Supabase, 10. Temporal List, 
# 11. Temporal Detail, 12. LangSmith Trace
titles = [
    "Zero-Trust Infrastructure", # Vault Engines
    "Dynamic Secret Management", # Vault Secret
    "Deep-Stack Observability", # Grafana
    "Real-time Cluster Health", # Prometheus
    "Hardened Applications", # Vote UI
    "Data Consistency at Scale", # Vote Result
    "Professional-Grade AI API", # Swagger
    "DevSecOps Automation", # GitHub Actions
    "Long-Term Conversation Memory", # Supabase
    "Durable AI Orchestration", # Temporal List
    "Reliable Self-Healing", # Temporal Detail
    "AI Reasoning & Traceability" # LangSmith Trace
]

# We want LangSmith to be the FIRST slide for "Wow" factor
# Reordering mapping (from current index to desired index)
# Current Order: 0:VaultEng, 1:VaultSec, 2:Grafana, 3:Prom, 4:VoteUI, 5:VoteRes, 6:Swagger, 7:GH, 8:Supa, 9:TempList, 10:TempDetail, 11:LangSmith
# Desired Order: 11, 10, 9, 7, 0, 1, 8, 3, 2, 4, 5, 6
order = [11, 10, 9, 7, 0, 1, 8, 3, 2, 4, 5, 6]

ordered_files = [files[i] for i in order]
ordered_titles = [titles[i] for i in order]

def add_branding(img, title):
    # Create a copy to draw on
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Simple branding bar at the top
    bar_height = int(height * 0.08)
    draw.rectangle([0, 0, width, bar_height], fill="#0077B5") # LinkedIn Blue
    
    # Try to load a font, otherwise use default
    try:
        # Windows standard font path
        font_title = ImageFont.truetype("arial.ttf", int(bar_height * 0.6))
    except:
        font_title = ImageFont.load_default()
        
    # Draw Title
    draw.text((20, int(bar_height * 0.2)), title, fill="white", font=font_title)
    
    # Add watermark/branding at the bottom
    draw.text((width - 250, height - 30), "AI-SRE Platform | Rakesh Patra", fill="gray")
    
    return img

img_list = []
for i, filename in enumerate(ordered_files):
    path = os.path.join(brain_dir, filename)
    img = Image.open(path)
    # Add professional branding
    branded_img = add_branding(img, ordered_titles[i])
    img_list.append(branded_img)

if img_list:
    img_list[0].save(
        output_pdf,
        save_all=True,
        append_images=img_list[1:],
        resolution=100.0,
        quality=95
    )
    print(f"✅ Successfully created {output_pdf}")
else:
    print("❌ No images found to process.")
