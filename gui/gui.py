import gradio as gr
from haku_character import haku_character


def gradio_interface(
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
    )
    return log_contents


iface = gr.Interface(
    fn=gradio_interface,
    inputs=[
        gr.Textbox(
            lines=5,
            value="kamisato_ayaka,seele_vollerei",
            info="Enter names separated by commas,such as: kamisato_ayaka,seele_vollerei",
            label="names",
        ),  # 名字列表
        gr.Textbox(
            lines=1,
            value="solo,highres",
            info="Enter required tags separated by commas,such as: solo,highres",
            label="else required tags",
        ),  # 必要的标签
        gr.Number(
            value="-1", label="Enter images max number,-1 means no limit"
        ),  # 最大数量
        gr.Textbox(
            value="0,1,2,3",
            label="Enter rating number(s) separated by commas,such as: 0,1,2,3, 0 means safe, 3 means nsfw",
        ),  # 评级，越小越安全
        gr.Number(
            value="-1",
            label="Enter score threshold, -1 means automatically from top to bottom",
        ),  # danbooru分数
        gr.Textbox(
            lines=1, value="./data/danbooru2023.db", placeholder="Enter database path"
        ),  # 数据库路径
        gr.Textbox(
            lines=1, value="./images", placeholder="Enter image path"
        ),  # 图片路径
        gr.Textbox(
            lines=1, value="./train_data", placeholder="Enter output path"
        ),  # 输出路径
        gr.Number(value="0", label="Enter id min range"),  # id范围
        gr.Number(value="10000000", label="Enter id max range"),  # id范围
        gr.Checkbox(
            label="add_character_category_path"
        ),  # 是否根据names中的名称单独新建文件夹
    ],
    outputs="text",  # 输出为文本，显示结果
)

iface.launch(share=True, server_port=2104)
