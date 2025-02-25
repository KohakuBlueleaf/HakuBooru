import gradio as gr
from gui.haku_character import haku_character
from tag_list import generate_tag_files
from typing import Optional


def gradio_haku(
    names: str,
    required: str,
    exclude: str,
    max_images: str,
    ratings: str,
    score: str,
    db_path: str,
    image_path: str,
    output_path: str,
    id_range_min: str,
    id_range_max: str,
    add_character_category_path: bool,
    export_images: bool,
    process_threads: int,
) -> str:
    """Wrapper function for Gradio interface."""
    try:
        # Input validation
        names_list = [n.strip() for n in names.split(",") if n.strip()] if names else []
        required_list = (
            [r.strip() for r in required.split(",") if r.strip()] if required else []
        )
        exclude_list = (
            [e.strip() for e in exclude.split(",") if e.strip()] if exclude else []
        )

        # Convert numerical inputs
        max_posts = _safe_int(max_images, -1)
        score_value = _safe_int(score, -1)
        id_min = _safe_int(id_range_min, 0)
        id_max = _safe_int(id_range_max, 10_000_000)

        # Convert ratings
        rating_list = []
        for r in ratings.split(","):
            rating = _safe_int(r.strip(), default=None)
            if rating is None or rating not in {0, 1, 2, 3}:
                raise ValueError(f"Invalid rating value: {r}")
            rating_list.append(rating)

        return haku_character(
            names=names_list,
            required=required_list,
            exclude=exclude_list,
            max_posts=max_posts,
            ratings=rating_list,
            score_threshold=score_value,
            db_path=db_path,
            image_path=image_path,
            output_path=output_path,
            id_range_min=id_min,
            id_range_max=id_max,
            add_character_category_path=add_character_category_path,
            export_images=export_images,
            process_threads=process_threads,
        )
    except Exception as e:
        return f"Error occurred: {str(e)}"


def _safe_int(value: str, default: Optional[int] = None) -> int:
    """Safely convert string to integer."""
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return default if default is not None else 0


with gr.Blocks(title="HakuBooru GUI") as blocks:
    gr.Markdown("# HakuBooru GUI")

    with gr.Accordion("Basic Settings", open=True):
        with gr.Row():
            with gr.Column(min_width=300):
                names = gr.Textbox(
                    lines=3,
                    label="Tags (comma-separated)",
                    placeholder="Enter tags like: kamisato_ayaka, seele_vollerei",
                )
                required = gr.Textbox(
                    label="Required Tags", placeholder="solo, highres"
                )
                exclude = gr.Textbox(label="Excluded Tags", placeholder="lowres, nsfw")

            with gr.Column():
                max_images = gr.Number(value=-1, label="Max Images (-1 for no limit)")
                ratings = gr.Textbox(value="0,1,2,3", label="Allowed Ratings (0-3)")
                score = gr.Number(value=0, label="Minimum Score (-1 for auto)")

    with gr.Accordion("Advanced Settings", open=False):
        with gr.Row():
            db_path = gr.Textbox(value="./data/danbooru2023.db", label="Database Path")
            image_path = gr.Textbox(value="./images/images", label="Image Archive Path")
            output_path = gr.Textbox(value="./out", label="Output Directory")

        with gr.Row():
            id_range_min = gr.Number(value=0, label="Minimum Post ID")
            id_range_max = gr.Number(value=10_000_000, label="Maximum Post ID")
            add_character_category_path = gr.Checkbox(label="Organize by Tags")
            export_images = gr.Checkbox(value=True, label="Enable Export")
            process_threads = gr.Number(value=4, label="Processing Threads")

    with gr.Accordion("Tag List", open=False):
        with gr.Row():
            tag_db_path = gr.Textbox(
                value="./data/danbooru2023.db", label="Database Path"
            )
            tag_output_dir = gr.Textbox(
                value="./out/tag_list", label="Output Directory"
            )
        gen_tags_btn = gr.Button("Export Tag List", variant="secondary")

    run_button = gr.Button("Start Processing", variant="primary")
    output_log = gr.Textbox(label="Processing Log", interactive=False, lines=20)

    run_button.click(
        gradio_haku,
        inputs=[
            names,
            required,
            exclude,
            max_images,
            ratings,
            score,
            db_path,
            image_path,
            output_path,
            id_range_min,
            id_range_max,
            add_character_category_path,
            export_images,
            process_threads,
        ],
        outputs=output_log,
        concurrency_limit=1,  # Prevent concurrent executions
    )

    gen_tags_btn.click(
        generate_tag_files,
        inputs=[tag_db_path, tag_output_dir],
        outputs=output_log,
        concurrency_limit=1,
    )

blocks.launch(server_port=2104, inbrowser=True, show_error=True)
