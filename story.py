# """
# story.py — Generates a structured cartoon story broken into scene prompts.
# Returns a list of scene descriptions suitable for AnimateDiff.
# """

# from openai import OpenAI
# import json
# from openai import OpenAI
# from dotenv import load_dotenv
# import os
# import json

# load_dotenv()

# def generate_story(topic: str, num_scenes: int = 6) -> tuple[str, list[str]]:
#     """
#     Generate a short cartoon story and split it into scene prompts.

#     Returns:
#         (full_story_text, list_of_scene_prompts)
#         - full_story_text: used for voiceover TTS
#         - list_of_scene_prompts: short visual descriptions per scene for AnimateDiff
#     """
#     client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

#     # Step 1: Generate the full story for narration
#     story_response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{
#             "role": "user",
#             "content": (
#                 f"Write a short, fun anime-style cartoon story for kids about '{topic}'. "
#                 f"Keep it to about {num_scenes * 2} sentences. "
#                 "Use vivid, visual language."
#             )
#         }]
#     )
#     full_story = story_response.choices[0].message.content

#     # Step 2: Break story into visual scene prompts for AnimateDiff
#     scene_response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{
#             "role": "user",
#             "content": (
#                 f"Based on this story:\n\n{full_story}\n\n"
#                 f"Create exactly {num_scenes} short visual scene descriptions (one sentence each) "
#                 "that describe what's VISUALLY happening in each scene — like prompts for an anime artist. "
#                 "Focus on characters, setting, action, and mood. "
#                 f"Reply ONLY with a JSON array of {num_scenes} strings, nothing else."
#             )
#         }]
#     )

#     raw = scene_response.choices[0].message.content.strip()
#     # Strip markdown fences if present
#     raw = raw.replace("```json", "").replace("```", "").strip()
#     scenes = json.loads(raw)

#     print(f"[story] Story generated with {len(scenes)} scenes.")
#     return full_story, scenes




"""
story.py — Generates a structured kids cartoon story broken into scene prompts.
Target audience: children aged 2-10 years.
Style: 2D soft storybook animation, colorful, safe, moral-driven.
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

# Main character options: "baby panda", "little robot", "magic cat", "talking car"
MAIN_CHARACTER = "baby panda"

# Moral lesson options: "kindness", "sharing", "honesty", "friendship"
MORAL_LESSON = "sharing makes us happy"

# 2D storybook style prefix injected into every scene prompt
# SCENE_STYLE_PREFIX = (
#     "2D children's storybook illustration, soft pastel watercolor, "
#     "cute kawaii style, big expressive eyes, bright cheerful colors, "
#     "safe for kids, non-scary, warm soft lighting, "
# )

SCENE_STYLE_PREFIX = "2D storybook, pastel colors, kawaii, kids safe, "


# ── Functions ─────────────────────────────────────────────────────────────────

def generate_story(topic: str, num_scenes: int = 8) -> tuple[str, list[str]]:
    """
    Generate a short kids cartoon story and split it into visual scene prompts.

    Story structure (8 scenes):
        1. Hook       — exciting/funny opening moment
        2. Intro      — introduce the main character
        3. Problem    — small challenge or problem
        4. Scene A    — adventure begins
        5. Scene B    — challenge gets harder / funny moment
        6. Scene C    — key emotional/learning moment
        7. Solution   — character solves the problem
        8. Happy End  — happy ending + moral lesson screen

    Returns:
        (full_story_text, list_of_scene_prompts)
        - full_story_text : used for voiceover TTS (narrator script)
        - list_of_scene_prompts : visual descriptions per scene for AnimateDiff
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # ── Step 1: Full narration story ──────────────────────────────────────────
    story_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a warm, playful children's story narrator. "
                    "Write stories that are safe, positive, non-scary, and non-violent. "
                    "Use simple sentences suitable for children aged 2-10. "
                    "Include repetition and catchy phrases for engagement. "
                    "Always include a clear moral lesson at the end."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Write a short, fun 2D cartoon story for kids about '{topic}'. "
                    f"The main character is a {MAIN_CHARACTER} with big expressive eyes. "
                    f"The story should teach children that '{MORAL_LESSON}'. "
                    f"Keep it to exactly {num_scenes * 2} short sentences. "
                    "Use repetition of a catchy phrase at least twice. "
                    "Add humor and emotional warmth. "
                    "End with a clear moral lesson statement. "
                    "Use vivid, colorful, visual language."
                )
            }
        ]
    )
    full_story = story_response.choices[0].message.content.strip()

    # ── Step 2: Visual scene prompts for AnimateDiff ──────────────────────────
    scene_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate visual scene descriptions for a 2D kids cartoon. "
                    "Each description must be safe for children, colorful, and cute. "
                    "Never include anything scary, violent, or adult."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Based on this kids story:\n\n{full_story}\n\n"
                    f"Create exactly {num_scenes} short visual scene descriptions. "
                    "Follow this structure strictly:\n"
                    "  Scene 1: Hook — exciting/funny opening moment\n"
                    "  Scene 2: Introduce the main character in their home/world\n"
                    "  Scene 3: The problem appears\n"
                    "  Scene 4: Adventure begins\n"
                    "  Scene 5: Funny or emotional challenge moment\n"
                    "  Scene 6: Key learning/emotional moment\n"
                    "  Scene 7: Character solves the problem happily\n"
                    "  Scene 8: Happy ending with friends, celebration, stars, rainbows\n\n"
                    "Each description should mention: character, setting, action, mood, colors. "
                    "Keep each description under 20 words. "
                    f"Reply ONLY with a JSON array of exactly {num_scenes} strings, nothing else."
                )
            }
        ]
    )

    raw = scene_response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    scenes_raw = json.loads(raw)

    # Inject 2D storybook style prefix into every scene prompt
    scenes = [f"{SCENE_STYLE_PREFIX}{scene}" for scene in scenes_raw]

    print(f"[story] Story generated with {len(scenes)} scenes.")
    return full_story, scenes