# Copyright (c) 2024 Alibaba Inc (authors: Xiang Lyu, Liu Yue)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys
import argparse
import gradio as gr
import numpy as np
import torch
import torchaudio
import random
import librosa
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
import webbrowser
import threading
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append('{}/third_party/Matcha-TTS'.format(ROOT_DIR))

from cosyvoice.cli.cosyvoice import AutoModel as CosyVoiceAutoModel
from cosyvoice.utils.file_utils import logging, load_wav
from cosyvoice.utils.common import set_all_random_seed, instruct_list
from voice_manager import (
    save_custom_voice, load_custom_voices, delete_custom_voice, 
    get_voice_by_id, get_voice_list_for_dropdown
)

# 配置详细日志 - DEBUG 级别
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 降低第三方库的日志级别（避免过多噪音）
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('gradio').setLevel(logging.INFO)
logging.getLogger('uvicorn').setLevel(logging.INFO)


inference_mode_list = ['预训练音色', '3s极速复刻', '跨语种复刻', '自然语言控制']
instruct_dict = {'预训练音色': '1. 选择预训练音色\n2. 点击生成音频按钮',
                 '3s极速复刻': '1. 选择prompt音频文件，或录入prompt音频，注意不超过30s，若同时提供，优先选择prompt音频文件\n2. 输入prompt文本\n3. 点击生成音频按钮',
                 '跨语种复刻': '1. 选择prompt音频文件，或录入prompt音频，注意不超过30s，若同时提供，优先选择prompt音频文件\n2. 点击生成音频按钮',
                 '自然语言控制': '1. 选择预训练音色\n2. 输入instruct文本\n3. 点击生成音频按钮'}
stream_mode_list = [('否', False), ('是', True)]
max_val = 0.8


def generate_seed():
    seed = random.randint(1, 100000000)
    return {
        "__type__": "update",
        "value": seed
    }

import regex

def count_chars_and_words(text):
    """
    计算字符串长度，汉字算一个字符，英语单词算一个字符，标点不计入
    """
    # 移除所有标点符号（包括中文和英文标点）
    # 这个正则表达式匹配常见的标点符号
    punctuation_pattern = r'[\p{P}\p{S}\s]+'
    text_no_punct = regex.sub(punctuation_pattern, ' ', text)

    # 分割字符串：汉字单独作为元素，英文单词作为整体
    # \p{Han} 匹配所有汉字
    # \p{Latin}+ 匹配拉丁字母序列（英文单词）
    pattern = r'\p{Han}|\p{Latin}+'

    matches = regex.findall(pattern, text_no_punct, regex.UNICODE)

    return len(matches)

top_db = 60
hop_length = 220
win_length = 440
def postprocess(wav):
    speech = load_wav(wav, target_sr=target_sr, min_sr=16000)
    speech, _ = librosa.effects.trim(
        speech, top_db=top_db,
        frame_length=win_length,
        hop_length=hop_length
    )
    if speech.abs().max() > max_val:
        speech = speech / speech.abs().max() * max_val
    speech = torch.concat([speech, torch.zeros(1, int(target_sr * 0.2))], dim=1)
    torchaudio.save(wav, speech, target_sr)
    return wav


def change_instruction(mode_checkbox_group):
    return instruct_dict[mode_checkbox_group]

def clear_instruct(text):
    if text == '自定义':
        return ''
    return text

def prompt_wav_recognition(prompt_wav):
    """使用 FunASR SenseVoiceSmall 进行音频识别"""
    if asr_model is None:
        return "ASR模型未加载"
    try:
        res = asr_model.generate(input=prompt_wav,
                                 language="auto",  # "zn", "en", "yue", "ja", "ko", "nospeech"
                                 use_itn=True,
        )
        text = res[0]["text"].split('|>')[-1]
        return text
    except Exception as e:
        logging.error(f"ASR识别失败: {e}")
        return "识别失败，请手动输入"


def load_voice_from_library(voice_name):
    """从音色库加载音色"""
    if not voice_name or voice_name == "不使用音色库":
        # 清空状态
        return None, "", gr.State(value=None)
    
    # 提取 voice_id（格式："音色名称 (voice_id)"）
    if " (" in voice_name:
        voice_id = voice_name.split(" (")[-1].rstrip(")")
    else:
        voice_id = voice_name
    
    voice_data = get_voice_by_id(voice_id)
    if voice_data:
        # 返回音频、文本和隐藏状态（用于 generate_audio 判断）
        return voice_data["audio"], voice_data["text"], gr.State(value=voice_data)
    else:
        gr.Warning(f"音色不存在")
        return None, "", gr.State(value=None)


def save_voice_to_library(voice_name, audio_upload, audio_record, prompt_text):
    """保存音色到音色库"""
    if not voice_name:
        gr.Warning("请输入音色名称")
        return gr.Dropdown(choices=["不使用音色库"] + get_voice_list_for_dropdown())
    
    # 优先使用上传文件，其次录音文件
    audio_file = audio_upload if audio_upload is not None else audio_record
    
    if not audio_file:
        gr.Warning("请上传或录制音频文件")
        return gr.Dropdown(choices=["不使用音色库"] + get_voice_list_for_dropdown())
    
    if not prompt_text:
        gr.Warning("请输入 prompt 文本")
        return gr.Dropdown(choices=["不使用音色库"] + get_voice_list_for_dropdown())
    
    result = save_custom_voice(voice_name, audio_file, prompt_text)
    if result["success"]:
        gr.Info(f"✅ 音色 '{voice_name}' 已保存")
    else:
        gr.Warning(f"✗ 保存失败: {result['message']}")
    
    # 返回更新后的下拉菜单选项
    updated_choices = ["不使用音色库"] + get_voice_list_for_dropdown()
    return gr.Dropdown(choices=updated_choices, value="不使用音色库")


def delete_voice_from_library(voice_name):
    """从音色库删除音色"""
    if not voice_name or voice_name == "不使用音色库":
        gr.Warning("请选择要删除的音色")
        return gr.Dropdown(choices=["不使用音色库"] + get_voice_list_for_dropdown())
    
    # 提取 voice_id（格式："音色名称 (voice_id)"）
    if " (" in voice_name:
        voice_id = voice_name.split(" (")[-1].rstrip(")")
    else:
        voice_id = voice_name
    
    result = delete_custom_voice(voice_id)
    if result["success"]:
        gr.Info(f"✅ 音色已删除")
    else:
        gr.Warning(f"✗ 删除失败: {result['message']}")
    
    # 返回更新后的下拉菜单选项
    updated_choices = ["不使用音色库"] + get_voice_list_for_dropdown()
    return gr.Dropdown(choices=updated_choices, value="不使用音色库")


def load_example_audio():
    """加载示例音频"""
    example_path = 'zero_shot_prompt.wav'
    example_text = '希望你以后能够做的比我还好呦'
    if os.path.exists(example_path):
        return example_path, example_text
    else:
        gr.Warning('示例音频文件不存在')
        return None, ""

def generate_audio(tts_text, mode_checkbox_group, sft_dropdown, prompt_text, prompt_wav_upload, prompt_wav_record, instruct_text,
                   seed, stream, speed, loaded_voice_state):
    # Force non-streaming to match official app.py behavior
    stream = False
    if count_chars_and_words(tts_text) > 200:
        gr.Warning('您输入的文字过长，请限制在200字以内')
        return (target_sr, default_data)

    if prompt_wav_upload is not None:
        prompt_wav = prompt_wav_upload
    elif prompt_wav_record is not None:
        prompt_wav = prompt_wav_record
    else:
        prompt_wav = None

    # if instruct mode, please make sure that model is iic/CosyVoice-300M-Instruct and not cross_lingual mode
    if mode_checkbox_group in ['自然语言控制']:
        if instruct_text == '':
            gr.Warning('您正在使用自然语言控制模式, 请输入instruct文本')
            return (target_sr, default_data)

    # if cross_lingual mode, please make sure that model is iic/CosyVoice-300M and tts_text prompt_text are different language
    if mode_checkbox_group in ['跨语种复刻']:
        if instruct_text != '':
            gr.Info('您正在使用跨语种复刻模式, instruct文本会被忽略')
        # 优先使用音色库，其次上传/录音
        if prompt_wav is None and loaded_voice_state is None:
            gr.Warning('您正在使用跨语种复刻模式, 请提供prompt音频或选择音色库')
            return (target_sr, default_data)
            return
        gr.Info('您正在使用跨语种复刻模式, 请确保合成文本和prompt文本为不同语言')

    # if in zero_shot cross_lingual, please make sure that prompt_text and prompt_wav meets requirements
    # 处理音色库加载的情况
    if loaded_voice_state is not None:
        # 使用音色库中的音频（如果没有上传新的）
        if prompt_wav is None:
            prompt_wav = loaded_voice_state["audio"]
        # 如果 prompt_text 为空，使用音色库中的文本
        if not prompt_text:
            prompt_text = loaded_voice_state["text"]
    
    if mode_checkbox_group in ['3s极速复刻', '跨语种复刻']:
        if prompt_wav is None:
            gr.Warning('prompt音频为空，您是否忘记输入prompt音频或选择音色库？')
            return (target_sr, default_data)
            return
        info = torchaudio.info(prompt_wav)
        if info.sample_rate < prompt_sr:
            gr.Warning('prompt音频采样率{}低于{}'.format(torchaudio.info(prompt_wav).sample_rate, prompt_sr))
            return (target_sr, default_data)
            return
        # relax the 15s limit to 30s as in webui.py, or keep 15s? webui says 30s.
        # User asked to merge webui.py features, so let's allow 30s but warn if too long maybe?
        # webui.py text says: "注意不超过30s"
        if info.num_frames / info.sample_rate > 30:
            gr.Warning('请限制输入音频在30s内，避免推理效果过低')
            return (target_sr, default_data)
            return

    # sft mode only use sft_dropdown
    if mode_checkbox_group in ['预训练音色']:
        if instruct_text != '' or prompt_wav is not None or prompt_text != '':
            gr.Info('您正在使用预训练音色模式，prompt文本/prompt音频/instruct文本会被忽略！')
        if sft_dropdown == '':
            gr.Warning('没有可用的预训练音色！')
            return (target_sr, default_data)
            return

    # Auto-wrap instruct text if needed
    if mode_checkbox_group in ['自然语言控制', '预训练音色', '3s极速复刻', '跨语种复刻']: 
        if instruct_text:
            if not instruct_text.startswith("You are a helpful assistant."):
                instruct_text = "You are a helpful assistant. " + instruct_text
            if not instruct_text.endswith("<|endofprompt|>"):
                instruct_text = instruct_text + "<|endofprompt|>"

    # zero_shot mode only use prompt_wav prompt text
    if mode_checkbox_group in ['3s极速复刻']:
        if prompt_text == '':
            gr.Warning('prompt文本为空，您是否忘记输入prompt文本？')
            return (target_sr, default_data)
            return
        if instruct_text != '':
            gr.Info('您正在使用3s极速复刻模式，instruct文本会被忽略！')

    if mode_checkbox_group == '预训练音色':
        logging.info('get sft inference request')
        set_all_random_seed(seed)
        speech_list = []
        for i in cosyvoice.inference_sft(tts_text, sft_dropdown, stream=stream, speed=speed):
            speech_list.append(i['tts_speech'])
        return (target_sr, torch.concat(speech_list, dim=1).numpy().flatten())
    elif mode_checkbox_group == '3s极速复刻':
        logging.info('get zero_shot inference request')
        set_all_random_seed(seed)
        speech_list = []
        for i in cosyvoice.inference_zero_shot(tts_text, prompt_text, postprocess(prompt_wav), stream=stream, speed=speed):
            speech_list.append(i['tts_speech'])
        return (target_sr, torch.concat(speech_list, dim=1).numpy().flatten())
    elif mode_checkbox_group == '跨语种复刻':
        logging.info('get cross_lingual inference request')
        set_all_random_seed(seed)
        speech_list = []
        for i in cosyvoice.inference_cross_lingual(tts_text, postprocess(prompt_wav), stream=stream, speed=speed):
            speech_list.append(i['tts_speech'])
        return (target_sr, torch.concat(speech_list, dim=1).numpy().flatten())
    else:
        logging.info('get instruct inference request')
        set_all_random_seed(seed)
        # Check if we should use SFT instruct or Zero-shot Instruct (CosyVoice 2/3)
        # If we have a prompt_wav, we likely want Zero-shot Instruct (inference_instruct2)
        # especially if sft_dropdown is empty.
        speech_list = []
        if prompt_wav is not None:
             # Use inference_instruct2 for Zero-shot Instruct (CosyVoice 3/2 feature)
             # Note: merged webui.py logic ignored prompt_wav in this mode, but original app_local.py used it.
             # We restore support for inference_instruct2.
            if hasattr(cosyvoice, 'inference_instruct2'):
                for i in cosyvoice.inference_instruct2(tts_text, instruct_text, postprocess(prompt_wav), stream=stream, speed=speed):
                    speech_list.append(i['tts_speech'])
                return (target_sr, torch.concat(speech_list, dim=1).numpy().flatten())
            else:
                gr.Warning('当前模型不支持零样本指令控制(inference_instruct2)，请尝试使用预训练音色')
                return (target_sr, default_data)
        elif sft_dropdown:
             # Use standard inference_instruct with SFT speaker
            for i in cosyvoice.inference_instruct(tts_text, sft_dropdown, instruct_text, stream=stream, speed=speed):
                speech_list.append(i['tts_speech'])
            return (target_sr, torch.concat(speech_list, dim=1).numpy().flatten())
        else:
             gr.Warning('请提供 Prompt 音频（用于零样本克隆）或选择预训练音色！')
             return (target_sr, default_data)


def main():
    with gr.Blocks() as demo:
        gr.Markdown("### 代码库 [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) \\\
                    预训练模型 [Fun-CosyVoice3-0.5B-2512](https://www.modelscope.cn/models/FunAudioLLM/Fun-CosyVoice3-0.5B-2512) \\\
                    [CosyVoice2-0.5B](https://www.modelscope.cn/models/iic/CosyVoice2-0.5B) \\\
                    [CosyVoice-300M](https://www.modelscope.cn/models/iic/CosyVoice-300M) \\\
                    [CosyVoice-300M-Instruct](https://www.modelscope.cn/models/iic/CosyVoice-300M-Instruct) \\\
                    [CosyVoice-300M-SFT](https://www.modelscope.cn/models/iic/CosyVoice-300M-SFT)")
        gr.Markdown("#### 请输入需要合成的文本，选择推理模式，并按照提示步骤进行操作")

        tts_text = gr.Textbox(label="输入合成文本", lines=1, value="你好，我是CosyVoice3语音合成模型。")
        with gr.Row():
            mode_checkbox_group = gr.Radio(choices=inference_mode_list, label='选择推理模式', value=inference_mode_list[0])
            instruction_text = gr.Text(label="操作步骤", value=instruct_dict[inference_mode_list[0]], scale=0.5)
            sft_dropdown = gr.Dropdown(choices=sft_spk, label='选择预训练音色', value=sft_spk[0] if len(sft_spk) > 0 else '', scale=0.25)
            stream = gr.Radio(choices=stream_mode_list, label='是否流式推理', value=stream_mode_list[0][1])
            speed = gr.Number(value=1, label="速度调节(仅支持非流式推理)", minimum=0.5, maximum=2.0, step=0.1)
            with gr.Column(scale=0.25):
                seed_button = gr.Button(value="\U0001F3B2")
                seed = gr.Number(value=0, label="随机推理种子")

        # 音色库管理
        with gr.Accordion("🎵 音色库管理", open=False):
            with gr.Row():
                voice_library_dropdown = gr.Dropdown(
                    choices=["不使用音色库"] + get_voice_list_for_dropdown(), 
                    label="选择音色", 
                    value="不使用音色库",
                    scale=2
                )
                load_voice_btn = gr.Button("📚 加载音色", size="sm", scale=1)
            
            with gr.Row():
                save_voice_name = gr.Textbox(label="音色名称", placeholder="例如：太乙真人", scale=2)
                save_voice_btn = gr.Button("💾 保存当前音色", size="sm", scale=1)
                delete_voice_btn = gr.Button("🗑️ 删除音色", size="sm", variant="stop", scale=1)
        
        # Prompt 音频和文本
        with gr.Row():
            prompt_wav_upload = gr.Audio(sources='upload', type='filepath', label='上传prompt音频文件（采样率≥16kHz）')
            prompt_wav_record = gr.Audio(sources='microphone', type='filepath', label='录制prompt音频文件')
        with gr.Row():
            load_example_btn = gr.Button("📂 加载示例音频", size="sm", scale=1)
            prompt_text = gr.Textbox(label="prompt文本（上传/录音后自动识别）", lines=1, placeholder="请输入prompt文本，或上传/录制音频后自动识别...", value='', scale=4)
        instruct_text = gr.Dropdown(choices=['自定义'] + instruct_list, label='选择instruct文本', value=instruct_list[0], allow_custom_value=True)

        # 隐藏的状态：用于保存音色库加载的数据
        loaded_voice_state = gr.State(value=None)

        generate_button = gr.Button("生成音频")

        audio_output = gr.Audio(label="合成音频", autoplay=True, streaming=False)

        # 事件绑定
        seed_button.click(generate_seed, inputs=[], outputs=seed)
        load_example_btn.click(load_example_audio, inputs=[], outputs=[prompt_wav_upload, prompt_text])
        
        # 音色库事件
        load_voice_btn.click(
            load_voice_from_library, 
            inputs=[voice_library_dropdown], 
            outputs=[prompt_wav_upload, prompt_text, loaded_voice_state]
        )
        save_voice_btn.click(
            save_voice_to_library, 
            inputs=[save_voice_name, prompt_wav_upload, prompt_wav_record, prompt_text], 
            outputs=[voice_library_dropdown]
        )
        delete_voice_btn.click(
            delete_voice_from_library, 
            inputs=[voice_library_dropdown], 
            outputs=[voice_library_dropdown]
        )
        
        generate_button.click(generate_audio,
                              inputs=[tts_text, mode_checkbox_group, sft_dropdown, prompt_text, prompt_wav_upload, prompt_wav_record, instruct_text,
                                      seed, stream, speed, loaded_voice_state],
                              outputs=[audio_output])
        mode_checkbox_group.change(fn=change_instruction, inputs=[mode_checkbox_group], outputs=[instruction_text])
        # ASR 自动识别：仅在用户手动上传/录音时触发，不在音色库加载时触发
        prompt_wav_upload.upload(fn=prompt_wav_recognition, inputs=[prompt_wav_upload], outputs=[prompt_text])
        prompt_wav_record.stop_recording(fn=prompt_wav_recognition, inputs=[prompt_wav_record], outputs=[prompt_text])
        instruct_text.change(fn=clear_instruct, inputs=[instruct_text], outputs=[instruct_text])
    
    # 自动打开浏览器
    def open_browser():
        import time
        time.sleep(2)  # 等待服务器启动
        webbrowser.open(f'http://localhost:{args.port}')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    demo.queue(max_size=4, default_concurrency_limit=2).launch(
        server_port=args.port, 
        server_name='0.0.0.0',
        quiet=True  # 减少 Gradio 的输出
    )


if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_dir',
                        type=str,
                        default='pretrained_models/Fun-CosyVoice3-0.5B',
                        help='模型目录路径')
    parser.add_argument('--port',
                        type=int,
                        default=50000,
                        help='服务端口')
    args = parser.parse_args()

    # 检查模型目录
    if not os.path.exists(args.model_dir):
        print(f"错误: 模型目录不存在: {args.model_dir}")
        print("请确保模型已下载")
        sys.exit(1)

    # 加载本地模型
    print("\n" + "="*60)
    print("🚀 启动 CosyVoice WebUI")
    print("="*60)
    print(f"📂 加载本地模型: {args.model_dir}")
    cosyvoice = CosyVoiceAutoModel(model_dir=args.model_dir, load_trt=False, fp16=False)

    # 预热（可选）
    sft_spk = []
    try:
        sft_spk = cosyvoice.list_available_spks()
        print(f"   可用音色: {len(sft_spk)} 个")
    except:
        print("注意: 该模型不支持 SFT 音色")
    if len(sft_spk) == 0:
        sft_spk = ['']

    prompt_sr = 16000
    # Use model's actual sample rate
    target_sr = cosyvoice.sample_rate
    default_data = np.zeros(target_sr)

    # 预热 (Warmup)
    print("\n🔥 正在进行模型预热...")
    try:
        # Try to use zero_shot_prompt.wav if available
        warmup_wav = 'zero_shot_prompt.wav'
        if os.path.exists(warmup_wav):
            # postprocess expects a file path, not a tensor
            warmup_processed = postprocess(warmup_wav)
            # Consume all chunks to fully warm up the streaming pipeline
            for _ in cosyvoice.inference_zero_shot('预热', '预热', warmup_processed, stream=True):
                pass
            print("\n✅ 模型预热完成")
        else:
            print(f"未找到预热音频 {warmup_wav}，跳过预热")
    except Exception as e:
        print(f"模型预热部分失败 (不影响正常使用): {e}")

    # 加载 ASR 模型（如果存在）
    asr_model = None
    asr_model_dir = "pretrained_models/SenseVoiceSmall"
    if os.path.exists(asr_model_dir):
        try:
            print(f"加载 ASR 模型: {asr_model_dir}")
            asr_model = AutoModel(
                model=asr_model_dir,
                disable_update=True,
                log_level='DEBUG',
                device="cuda:0" if torch.cuda.is_available() else "cpu"
            )
            print("ASR 模型加载成功")
        except Exception as e:
            print(f"ASR 模型加载失败: {e}")
            asr_model = None
    else:
        print(f"ASR 模型目录不存在: {asr_model_dir}，将不提供音频识别功能")
        asr_model = None

    print("\n" + "="*60)
    print("✅ 模型加载成功，启动 WebUI...")
    print(f"🌐 本地地址: http://localhost:{args.port}")
    print("="*60 + "\n")
    main()