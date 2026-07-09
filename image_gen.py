# """
# image_gen.py — Generates anime-style background/character images per scene
# using Stable Diffusion 1.5 with anime LoRA, optimized for 6GB VRAM.
# These images are used as init frames fed into AnimateDiff.
# """

# from diffusers import StableDiffusionPipeline
# import torch
# import os

# os.makedirs("output/frames", exist_ok=True)

# # Anime-style model — swap to "Ojimi/anime-kawai-diffusion" or any anime SD1.5 checkpoint
# MODEL_ID = "dreamlike-art/dreamlike-anime-1.0"

# pipe = StableDiffusionPipeline.from_pretrained(
#     MODEL_ID,
#     torch_dtype=torch.float16,
#     safety_checker=None,
# )
# pipe = pipe.to("cuda")

# # Memory optimizations for 6GB VRAM
# pipe.enable_attention_slicing()
# pipe.enable_vae_slicing()

# ANIME_STYLE_SUFFIX = (
#     "anime style, 2D cartoon, vibrant colors, detailed lineart, "
#     "studio ghibli inspired, high quality, masterpiece"
# )
# NEGATIVE_PROMPT = (
#     "3d render, realistic, blurry, low quality, watermark, "
#     "text, ugly, deformed, nsfw"
# )

# def generate_images(scenes: list[str]) -> list[str]:
#     """
#     Args:
#         scenes: list of scene description strings (one per story beat)
#     Returns:
#         list of saved image file paths
#     """
#     paths = []
#     for i, scene in enumerate(scenes):
#         full_prompt = f"{scene}, {ANIME_STYLE_SUFFIX}"
#         print(f"[image_gen] Generating frame {i+1}/{len(scenes)}: {scene[:60]}...")

#         result = pipe(
#             prompt=full_prompt,
#             negative_prompt=NEGATIVE_PROMPT,
#             width=512,
#             height=512,
#             num_inference_steps=25,
#             guidance_scale=7.5,
#         )
#         path = f"output/frames/scene_{i:02d}.png"
#         result.images[0].save(path)
#         paths.append(path)

#     print(f"[image_gen] Generated {len(paths)} scene frames.")
#     return paths




"""
image_gen.py — Generates 2D kids storybook-style images per scene
using Stable Diffusion with a kawaii/children's illustration model.

These frames are used as init_image input to AnimateDiff in video.py,
which gives more consistent character appearance across scenes.

Model options (uncomment preferred):
    - "Ojimi/anime-kawai-diffusion"        ← soft kawaii, very kid-friendly ✅
    - "stablediffusionapi/kids-illustration" ← dedicated kids illustration
    - "dreamlike-art/dreamlike-anime-1.0"  ← original (NOT recommended for kids)
"""

from diffusers import StableDiffusionPipeline
import torch
import os

os.makedirs("output/frames", exist_ok=True)

# ── Model ─────────────────────────────────────────────────────────────────────
# Changed from dreamlike-anime (adult-style) → kawaii kids-friendly model
MODEL_ID = "Ojimi/anime-kawai-diffusion"

pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    safety_checker=None,       # We rely on prompt-level safety instead
)
pipe = pipe.to("cuda")

# ── VRAM optimizations (supports 6GB GPUs) ────────────────────────────────────
pipe.enable_attention_slicing()
pipe.enable_vae_slicing()

# ── Style constants ───────────────────────────────────────────────────────────

# Changed from anime/ghibli → kids 2D storybook illustration style
KIDS_STYLE_SUFFIX = (
    "2D children's storybook illustration, soft pastel watercolor, "
    "cute kawaii style, big expressive eyes, bright cheerful colors, "
    "warm soft lighting, flat 2D art, simple clean lineart, "
    "safe for kids, non-scary, magical atmosphere, high quality"
)

# Strong negative prompt to ensure kid-safe output
NEGATIVE_PROMPT = (
    "3d render, realistic, photorealistic, blurry, low quality, "
    "watermark, text, ugly, deformed, nsfw, violence, blood, scary, "
    "horror, dark, adult content, weapon, monster, disturbing"
)

# ── Main function ─────────────────────────────────────────────────────────────

def generate_images(scenes: list[str]) -> list[str]:
    """
    Generate a 2D storybook-style image for each scene.

    Args:
        scenes: list of scene description strings (already include style prefix from story.py)
    Returns:
        list of saved image file paths (used as init frames in video.py)
    """
    paths = []

    for i, scene in enumerate(scenes):
        # Style suffix already in scene from story.py, but append extra quality boosters
        full_prompt = f"{scene}, {KIDS_STYLE_SUFFIX}"

        print(f"[image_gen] Generating frame {i+1}/{len(scenes)}: {scene[:60]}...")

        result = pipe(
            prompt=full_prompt,
            negative_prompt=NEGATIVE_PROMPT,
            width=768,          # Changed: 512→768 for 16:9 widescreen kids video
            height=432,         # Changed: 512→432 to maintain 16:9 ratio
            num_inference_steps=30,   # Increased: 25→30 for better quality
            guidance_scale=8.0,       # Increased slightly for stronger style adherence
            generator=torch.manual_seed(100 + i),  # Consistent seed per scene
        )

        path = f"output/frames/scene_{i:02d}.png"
        result.images[0].save(path)
        paths.append(path)
        print(f"[image_gen] Saved: {path}")

    print(f"[image_gen] Generated {len(paths)} scene frames.")
    return paths