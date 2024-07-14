import gradio as gr
from haku_character import haku_character


def gradio_interface(
    names,
    required,
    max,
    ratings,
    db_path,
    image_path,
    output_path,
    id_range_min,
    id_range_max,
    add_character_category_path,
):
    names_list = [name.strip() for name in names.split(",")]
    required_list = [req.strip() for req in required.split(",")]
    max_image = int(max)
    ratings_list = [int(r.strip()) for r in ratings.split(",")]
    id_min = int(id_range_min)
    id_max = int(id_range_max)
    log_contents = haku_character(
        names_list,
        required_list,
        max_image,
        ratings_list,
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
            placeholder="Enter names separated by commas,such as: kamisato_ayaka,seele_vollerei",
        ),  # 名字列表
        gr.Textbox(
            lines=1,
            placeholder="Enter required tags separated by commas,such as: solo,highres",
        ),  # 必要的标签
        gr.Number(
            value="-1", label="Enter images max number,-1 means no limit"
        ),  # 最大数量
        gr.Textbox(
            value="0,1,2,3",
            label="Enter rating number(0~3), 0 means safe, 3 means nsfw",
        ),  # 评分，越小越安全
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
        gr.Number(value="8000000", label="Enter id max range"),  # id范围
        gr.Checkbox(
            label="add_character_category_path"
        ),  # 是否根据names中的名称单独新建文件夹
    ],
    outputs="text",  # 输出为文本，显示结果
)

iface.launch(share=True, server_port=2104)
