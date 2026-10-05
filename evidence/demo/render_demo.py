"""Render a captioned walkthrough from genuine browser captures, not simulated UI."""
from pathlib import Path
import subprocess
import sys
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / '.demo-runtime'))
import imageio_ffmpeg

FONT = Path('C:/Windows/Fonts/arial.ttf')
BOLD = Path('C:/Windows/Fonts/arialbd.ttf')
scenes = [
    (None, 6, 'Look closer before you trade.', 'Reef researches whether a funding opportunity survives execution costs and residual hedge risk.'),
    ('01-comparison.png', 14, 'Compare the whole trade.', 'Ask about two tracked pairs at the same reference size and holding period. Every financial figure comes from the frozen Python export.'),
    ('02-stress.png', 14, 'Challenge the assumption.', 'Reverse funding while retaining both instruments. Stress point estimates are separate from base verdicts and funding-only intervals.'),
    ('03-hold.png', 12, 'Continue the conversation.', 'Change the holding period to seven days. The comparison and selected stress stay in context.'),
    ('04-requirements.png', 12, 'Find the condition that binds.', 'Inspect execution cost, residual risk and required carry. The solver shows what would need to change under fixed assumptions.'),
    ('05-export.png', 10, 'Keep a dated research artifact.', 'Export the notebook with its questions, evidence and assumptions. Notebook turns are locally saved and are not Bitcoin-anchored.'),
    ('06-proof.png', 14, 'Inspect prediction and outcome.', 'A separate historical paper-trade case includes accounting, Merkle paths, OpenTimestamps proofs and Bitcoin headers. Hypothetical fills; no orders.'),
    (None, 8, 'Research first. Human decides.', 'reef-research-desk.vercel.app\nEdited walkthrough of verified browser captures. No trader validation or investment performance is claimed.'),
]

def paragraph(draw, text, x, y, width=30, size=28, color='#cbd4c6'):
    font = ImageFont.truetype(str(FONT), size)
    for part in text.split('\n'):
        for line in textwrap.wrap(part, width=width):
            draw.text((x, y), line, font=font, fill=color)
            y += size * 1.5
        y += 12

for i, (capture, duration, title, body) in enumerate(scenes):
    frame = Image.new('RGB', (1920, 1080), '#26382a')
    draw = ImageDraw.Draw(frame)
    draw.text((60, 48), 'REEF / RESEARCH DESK', font=ImageFont.truetype(str(BOLD), 24), fill='#cbd4c6')
    draw.text((1790, 48), f'{i+1:02d}', font=ImageFont.truetype(str(FONT), 24), fill='#cbd4c6')
    if capture:
        screen = Image.open(HERE / capture).convert('RGB')
        screen.thumbnail((1260, 890), Image.Resampling.LANCZOS)
        frame.paste(screen, (40, 120))
        paragraph(draw, title, 1350, 155, width=20, size=42, color='#ffffff')
        paragraph(draw, body, 1350, 365, width=27, size=27)
    else:
        paragraph(draw, title, 90, 240, width=30, size=74, color='#ffffff')
        paragraph(draw, body, 95, 560, width=70, size=30)
    draw.text((60, 1034), 'Captured October 5, 2026 | Historical estimates | Hypothetical fills', font=ImageFont.truetype(str(FONT), 20), fill='#cbd4c6')
    frame.save(HERE / f'scene-{i:02d}.png')

manifest = HERE / 'scenes.txt'
manifest.write_text(''.join(f"file 'scene-{i:02d}.png'\nduration {scene[1]}\n" for i, scene in enumerate(scenes)) + f"file 'scene-{len(scenes)-1:02d}.png'\n", encoding='utf-8')
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', str(manifest), '-vf', 'fps=24', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(HERE / 'reef-research-walkthrough.mp4')], check=True)
print('Rendered 90-second captioned walkthrough from actual browser captures.')
