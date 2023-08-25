import argparse
import base64
import io
import os

import requests
from PIL import Image, PngImagePlugin

import glob


def process_process(process_dir):
    process_list = []
    process_txt_path_list = glob.glob(args.process_dir + "/*")
    for process_txt_path in process_txt_path_list:
        # print(process_txt_path)
        with open(process_txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # print(content)
        items = content.split(";")
        # print(lines)
        process_info = {}
        for item in items:
            if item.strip():
                idx = item.find(':')
                k, v = item[:idx].strip(), item[idx + 1:].strip()
                if '[' in v or '{' in v:
                    # print(v)
                    v = eval(v)
                process_info[k] = v
            # break
        # break
        process_list.append(process_info)

    process_list.sort(key=lambda x: int(x.get('Process number')))

    return process_list


def process_task(task_path):
    with open(task_path, 'r', encoding='utf-8') as f:
        content = f.read()
    task_list = []
    # print(content)
    task_blocks = content.split('————————————————————————————————————————')
    # print(task_blocks)

    for task_block in task_blocks:
        task_info = {}
        items = task_block.split(';')
        for item in items:
            if item.strip():
                idx = item.find(':')
                k, v = item[:idx].strip(), item[idx + 1:].strip()
                if '[' in v or '{' in v:
                    v = eval(v)
                task_info[k] = v
        # print(task_info)
        task_list.append(task_info)

    task_list.sort(key=lambda x: int(x.get('Task number')))
    return task_list


def run(args):
    process_list = process_process(args.process_dir)
    task_list = process_task(args.task_path)

    import copy

    url = args.url
    output_root = args.output_root

    for task in task_list:
        print(f"Executing task {task['Task number']}: {task['Task name']}")
        output_task_path = os.path.join(output_root, task['Task name'])
        if not os.path.exists(output_task_path):
            os.makedirs(output_task_path)

        for process in process_list:
            print(f"  Using process {process['Process number']}: {process['Process name']}")
            output_process_path = os.path.join(output_task_path, process['Process name'])
            if not os.path.exists(output_process_path):
                os.makedirs(output_process_path)

            info = copy.deepcopy(process)
            for k, v in task.items():
                if k in info:
                    if v == info[k]:
                        continue
                    elif k == 'prompt' or k == 'negative_prompt':
                        if v.strip():
                            info[k] = v + ', ' + info[k]
                    else:
                        info[k] = v
                else:
                    info[k] = v

            print(info)
            settings = copy.deepcopy(info)
            settings.pop('Task number')
            settings.pop('Task name')
            settings.pop('Process number')
            settings.pop('Process name')

            response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=settings)

            r = response.json()

            cnt=0

            for i in r['images']:
                image = Image.open(io.BytesIO(base64.b64decode(i.split(",", 1)[0])))

                png_payload = {
                    "image": "data:image/png;base64," + i
                }
                response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)

                pnginfo = PngImagePlugin.PngInfo()
                pnginfo.add_text("parameters", response2.json().get("info"))
                png_name = str(cnt)+".png"
                cnt+=1
                png_path = os.path.join(output_process_path, png_name)
                image.save(png_path, pnginfo=pnginfo)
            print("\n*******************************************************************")
            print(f"Task {info['Task number']} process {info['Process number']} finish")
            print("*******************************************************************\n")


def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument("--url",
                        type=str,
                        default="http://localhost:7860",
                        help="url to use sd api")
    parser.add_argument("--task_path",
                        type=str,
                        required=True, help="task file you want to use")
    parser.add_argument("--process_dir",
                        type=str,
                        required=True, help="process dictionary you want to use")
    parser.add_argument("--output_root",
                        type=str,
                        default=".", help="the root path you want to save image")

    return parser


if __name__ == "__main__":
    parser = setup_parser()

    args = parser.parse_args()
    run(args)
