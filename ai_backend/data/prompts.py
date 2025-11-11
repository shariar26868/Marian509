# ai_backend/data/prompts.py
DEFAULT_PROMPT_TEMPLATE = """
Visualize the user's room with the selected {theme} theme.
Place the furniture as follows: {user_prompt}.
Include items from: {furniture_links}.
Use realistic rendering with Stable Diffusion and ControlNet to preserve room structure.
"""