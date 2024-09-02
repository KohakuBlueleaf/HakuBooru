import gradio as gr
from haku_character import haku_character


def gradio_haku(
    names,
    required,
    max,
    ratings,
    score,
    db_path,
    image_path,
    output_path,
    id_range_min,
    id_range_max,
    add_character_category_path,
    export_images,
):
    names_list = [name.strip() for name in (names.split(",") if names else [])]
    required_list = [req.strip() for req in (required.split(",") if required else [])]
    max_image = int(max)
    ratings_list = [int(r.strip()) for r in ratings.split(",")]
    score = int(score)
    id_min = int(id_range_min)
    id_max = int(id_range_max)
    log_contents = haku_character(
        names_list,
        required_list,
        max_image,
        ratings_list,
        score,
        db_path,
        image_path,
        output_path,
        id_min,
        id_max,
        add_character_category_path,
        export_images,
    )
    return log_contents


with gr.Blocks() as blocks:
    gr.Markdown(
        "## [HakuBooru](https://github.com/KohakuBlueleaf/HakuBooru) GUI Beta version"
    )
    with gr.Row():
        with gr.Column(scale=1):
            names = gr.Textbox(
                lines=5,
                # value="kamisato_ayaka,seele_vollerei",
                info="Enter tags separated by commas, such as: kamisato_ayaka,seele_vollerei",
                label="Tags (Not mandatory)",
            )  # tag列表
            required = gr.Textbox(
                lines=1,
                # value="solo,highres",
                info="Enter required tags separated by commas, such as: solo,highres",
                label="else required tags(Not mandatory; this field is only available if 'Tags' is filled in.)",
            )  # 必要的标签
            max = gr.Number(
                value="-1",
                info="Enter images max number, -1 means no limit",
                label="Max Images",
            )  # 最大数量
            ratings = gr.Textbox(
                value="0,1,2,3",
                info="Enter rating number(s) separated by commas, such as: 0,1,2,3. 0 means safe, 3 means nsfw",
                label="Ratings",
            )  # 评级，越小越安全
            score = gr.Number(
                value="-1",
                info="Enter score threshold, -1 means automatically from top to bottom",
                label="Score",
            )  # danbooru分数
        with gr.Column(scale=2):
            db_path = gr.Textbox(
                lines=1,
                value="./data/danbooru2023.db",
                info="Enter database path",
                label="DataBase path",
            )  # 数据库路径
            image_path = gr.Textbox(
                lines=1,
                value="./images",
                info="Enter images path",
                label="Images path",
            )  # 图片路径
            output_path = gr.Textbox(
                lines=1,
                value="./train_data",
                info="Enter output path",
                label="Output path",
            )  # 输出路径
            id_range_min = gr.Number(
                value="0",
                info="Enter id min range",
                label="ID Min",
            )  # id范围
            id_range_max = gr.Number(
                value="10000000",
                info="Enter id max range",
                label="ID Max",
            )  # id范围
            add_character_category_path = gr.Checkbox(
                info="When enabled, folders will be automatically categorized based on the tags.",
                label="Add tag category path",
            )  # 是否根据tags中的名称单独新建文件夹
            export_images = gr.Checkbox(
                info="When enabled, images will be exported to the output path.",
                label="Export images",
            )  # 是否导出图片
    with gr.Row():
        run_button = gr.Button("Start")
    with gr.Row():
        output_log = gr.Textbox(label="Log contents")

    run_button.click(
        gradio_haku,
        inputs=[
            names,
            required,
            max,
            ratings,
            score,
            db_path,
            image_path,
            output_path,
            id_range_min,
            id_range_max,
            add_character_category_path,
            export_images,
        ],
        outputs=output_log,
    )

blocks.launch(share=True, server_port=2104)
