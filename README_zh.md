[![SVG Banners](https://svg-banners.vercel.app/api?type=origin&text1=CosyVoice🤠&text2=Text-to-Speech%20💖%20Large%20Language%20Model&width=800&height=210)](https://github.com/Akshay090/svg-banners)

# 🚀 增强版本 - 主要改进

> **这是官方CosyVoice仓库的增强版本，增加了额外的功能和改进，提供更好的用户体验。**

## ⚠️ 重要提示：推荐使用 WSL 环境

**我们强烈推荐使用 WSL (Windows Subsystem for Linux) 而不是原生 Windows 环境。**

### 为什么使用 WSL？

虽然之前开发过 Windows 原生版本，但由于兼容性问题，某些关键功能不得不被禁用：

- ❌ **ttsfrd**：文本标准化包需要 Linux 特定依赖，无法在 Windows 上原生运行
- ❌ **SenseVoiceSmall**：ASR（自动语音识别）模型在 Windows 上兼容性有限
- ⚠️ **功能缺失**：缺少这些组件后，Windows 版本的体验大打折扣

### WSL 的优势：

- ✅ **完整功能支持**：包括 ttsfrd 和 SenseVoiceSmall 在内的所有功能都能完美运行
- ✅ **更好的兼容性**：原生 Linux 环境确保所有依赖按预期工作
- ✅ **简单设置**：WSL2 在 Windows 上提供接近原生的 Linux 性能
- ✅ **共享文件系统**：可以从 WSL 无缝访问 Windows 文件

**安装指南**：如果您还没有设置 WSL，请参考 [WSL 官方安装指南](https://learn.microsoft.com/zh-cn/windows/wsl/install)。

---

## ✨ 本版本的新功能

### 🎵 音色库管理系统
- **保存自定义音色**：将您喜欢的克隆音色保存到持久化音色库中以便重复使用
- **便捷加载音色**：加载之前保存的音色，无需重新上传音频文件
- **音色管理**：通过WebUI组织、重命名和删除音色配置文件
- **文件夹存储**：每个音色配置文件存储在 `custom_voices/` 目录中，包含音频和元数据

### 🎙️ 自动语音识别（ASR）
- **自动文本提取**：从上传的音频文件中自动提取提示文本
- **SenseVoiceSmall集成**：由FunASR的SenseVoiceSmall模型驱动
- **多语言支持**：支持中文、英文和其他语言
- **节省时间**：无需手动输入提示文本进行语音克隆

### 🖥️ 增强版WebUI (`app_local.py`)
- **改进的界面**：更好的UI组织，带有音色库管理面板
- **音频后处理**：自动音频增强和标准化
- **自动启动**：启动时自动在浏览器中打开
- **详细日志**：提供全面的日志输出，便于调试

### � 其他功能
- **缓存管理**：智能模型缓存，加快后续推理速度
- **音色迁移工具**：`migrate_voices.py` 用于轻松迁移音色库
- **API服务器**：增强的基于FastAPI的服务器，提供额外的接口
- **更好的文档**：详尽的README，提供清晰的设置说明

### 📂 项目结构改进
```
├── custom_voices/          # 新增：音色库存储
├── voice_manager.py        # 新增：音色管理模块
├── app_local.py            # 增强：带音色库的WebUI
├── cache_manager.py        # 新增：模型缓存管理
├── migrate_voices.py       # 新增：音色迁移工具
└── start_all.py           # 新增：一键启动脚本
```

## 📖 如何使用增强功能

1. **音色库**：在WebUI中，使用"🎵 音色库管理"折叠面板来保存/加载/删除自定义音色
2. **ASR**：上传音频文件后，提示文本将自动识别
3. **启动增强版WebUI**：使用 `python app_local.py` 而不是 `webui.py` 来使用所有功能

---

## �👉🏻 官方CosyVoice信息 👈🏻

**Fun-CosyVoice 3.0**: [演示](https://funaudiollm.github.io/cosyvoice3/); [论文](https://arxiv.org/abs/2505.17589); [魔搭社区](https://www.modelscope.cn/studios/FunAudioLLM/Fun-CosyVoice3-0.5B); [CV3-Eval](https://github.com/FunAudioLLM/CV3-Eval)

**CosyVoice 2.0**: [演示](https://funaudiollm.github.io/cosyvoice2/); [论文](https://arxiv.org/abs/2412.10117); [魔搭社区](https://www.modelscope.cn/studios/iic/CosyVoice2-0.5B); [HuggingFace](https://huggingface.co/spaces/FunAudioLLM/CosyVoice2-0.5B)

**CosyVoice 1.0**: [演示](https://fun-audio-llm.github.io); [论文](https://funaudiollm.github.io/pdf/CosyVoice_v1.pdf); [魔搭社区](https://www.modelscope.cn/studios/iic/CosyVoice-300M)

## 亮点🔥

**Fun-CosyVoice 3.0** 是一个基于大型语言模型（LLM）的先进文本转语音（TTS）系统，在内容一致性、说话人相似度和韵律自然度方面超越了其前身（CosyVoice 2.0）。它专为野外零样本多语言语音合成而设计。

### 主要特性
- **语言覆盖**：涵盖9种常见语言（中文、英语、日语、韩语、德语、西班牙语、法语、意大利语、俄语），18+种中文方言/口音（粤语、闽南语、四川话、东北话、陕西话、山西话、上海话、天津话、山东话、宁夏话、甘肃话等），同时支持多语言/跨语言零样本语音克隆。
- **内容一致性和自然度**：在内容一致性、说话人相似度和韵律自然度方面达到业界领先水平。
- **发音修复**：支持中文拼音和英文CMU音素的发音修复，提供更强的可控性，适合生产环境使用。
- **文本标准化**：支持数字、特殊符号和各种文本格式的读取，无需传统的前端模块。
- **双向流式**：支持文本输入流式和音频输出流式，延迟低至150ms，同时保持高质量音频输出。
- **指令支持**：支持各种指令，如语言、方言、情感、语速、音量等。


## 开发路线图

- [x] 2025/12

    - [x] 发布 Fun-CosyVoice3-0.5B-2512 基础模型、RL模型及其训练/推理脚本
    - [x] 发布 Fun-CosyVoice3-0.5B 魔搭社区 gradio 空间

- [x] 2025/08

    - [x] 感谢NVIDIA张悦凯的贡献，添加triton trtllm运行时支持和cosyvoice2 grpo训练支持

- [x] 2025/07

    - [x] 发布 Fun-CosyVoice 3.0 评估集

- [x] 2025/05

    - [x] 添加 CosyVoice2-0.5B vllm 支持

- [x] 2024/12

    - [x] 发布 25hz CosyVoice2-0.5B

- [x] 2024/09

    - [x] 25hz CosyVoice-300M 基础模型
    - [x] 25hz CosyVoice-300M 语音转换功能

- [x] 2024/08

    - [x] 重复感知采样(RAS)推理，提升llm稳定性
    - [x] 流式推理模式支持，包括kv缓存和sdpa以优化rtf

- [x] 2024/07

    - [x] Flow matching 训练支持
    - [x] 当ttsfrd不可用时支持WeTextProcessing
    - [x] Fastapi 服务器和客户端

## 评估结果
| 模型 | CER (%) ↓ (test-zh) | WER (%) ↓ (test-en) | CER (%) ↓ (test-hard) |
|-----|------------------|------------------|------------------|
| Human | 1.26 | 2.14 | - |
| F5-TTS | 1.53 | 2.00 | 8.67 |
| SparkTTS | 1.20 | 1.98 | - |
| Seed-TTS | 1.12 | 2.25 | 7.59 |
| CosyVoice2 | 1.45 | 2.57 | 6.83 |
| FireRedTTS-2 | 1.14 | 1.95 | - |
| IndexTTS2 | 1.01 | 1.52 | 7.12 |
| VibeVoice | 1.16 | 3.04 | - |
| HiggsAudio | 1.79 | 2.44 | - |
| MiniMax-Speech | 0.83 | 1.65 | - |
| VoxPCM | 0.93 | 1.85 | 8.87 |
| GLM-TTS | 1.03 | - | - |
| GLM-TTS_RL | 0.89 | - | - |
| Fun-CosyVoice3-0.5B-2512 | 1.21 |  2.24 | 6.71 |
| Fun-CosyVoice3-0.5B-2512_RL | 0.81 | 1.68 | 5.44 |


## 安装

### 克隆和安装

- 克隆代码仓库
    ``` sh
    git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
    # 如果由于网络原因克隆子模块失败，请运行以下命令直到成功
    cd CosyVoice
    git submodule update --init --recursive
    ```

- 安装 Conda：请参阅 https://docs.conda.io/en/latest/miniconda.html
- 创建 Conda 环境：

    ``` sh
    conda create -n cosyvoice -y python=3.10
    conda activate cosyvoice
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

    # 如果遇到sox兼容性问题
    # ubuntu
    sudo apt-get install sox libsox-dev
    # centos
    sudo yum install sox sox-devel
    ```

### 模型下载

我们强烈建议您下载预训练的 `Fun-CosyVoice3-0.5B`、`CosyVoice2-0.5B`、`CosyVoice-300M`、`CosyVoice-300M-SFT`、`CosyVoice-300M-Instruct` 模型和 `CosyVoice-ttsfrd` 资源。

**所有预训练模型应放置在 `pretrained_models/` 目录中。**

#### 方法1：使用Python SDK下载（推荐）

``` python
# SDK模型下载
from modelscope import snapshot_download
snapshot_download('FunAudioLLM/Fun-CosyVoice3-0.5B-2512', local_dir='pretrained_models/Fun-CosyVoice3-0.5B')
snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')
snapshot_download('iic/CosyVoice-300M', local_dir='pretrained_models/CosyVoice-300M')
snapshot_download('iic/CosyVoice-300M-SFT', local_dir='pretrained_models/CosyVoice-300M-SFT')
snapshot_download('iic/CosyVoice-300M-Instruct', local_dir='pretrained_models/CosyVoice-300M-Instruct')
snapshot_download('iic/CosyVoice-ttsfrd', local_dir='pretrained_models/CosyVoice-ttsfrd')
```

#### 方法2：手动下载

您也可以从以下地址手动下载模型：
- **魔搭社区（ModelScope）**： 
  - [Fun-CosyVoice3-0.5B-2512](https://www.modelscope.cn/models/FunAudioLLM/Fun-CosyVoice3-0.5B-2512)
  - [CosyVoice2-0.5B](https://www.modelscope.cn/models/iic/CosyVoice2-0.5B)
  - [CosyVoice-300M](https://www.modelscope.cn/models/iic/CosyVoice-300M)
  - [CosyVoice-300M-SFT](https://www.modelscope.cn/models/iic/CosyVoice-300M-SFT)
  - [CosyVoice-300M-Instruct](https://www.modelscope.cn/models/iic/CosyVoice-300M-Instruct)
  - [CosyVoice-ttsfrd](https://www.modelscope.cn/models/iic/CosyVoice-ttsfrd)
- **HuggingFace**: [FunAudioLLM 组织](https://huggingface.co/FunAudioLLM)

下载后，将它们放置在 `pretrained_models/` 目录中，结构如下：
```
pretrained_models/
├── Fun-CosyVoice3-0.5B/
├── CosyVoice2-0.5B/
├── CosyVoice-300M/
├── CosyVoice-300M-SFT/
├── CosyVoice-300M-Instruct/
└── CosyVoice-ttsfrd/
```

#### 可选：用于音频识别的ASR模型

如果需要在WebUI中使用音频自动识别功能，可以下载 SenseVoiceSmall 模型：
``` python
snapshot_download('iic/SenseVoiceSmall', local_dir='pretrained_models/SenseVoiceSmall')
```

可选地，您可以解压 `ttsfrd` 资源并安装 `ttsfrd` 包以获得更好的文本标准化性能。

注意，这一步不是必需的。如果您不安装 `ttsfrd` 包，我们将默认使用 wetext。

``` sh
cd pretrained_models/CosyVoice-ttsfrd/
unzip resource.zip -d .
pip install ttsfrd_dependency-0.1-py3-none-any.whl
pip install ttsfrd-0.4.2-cp310-cp310-linux_x86_64.whl
```

## 项目结构

安装和模型下载后，您的项目结构应如下所示：

```
CosyVoice/
├── pretrained_models/          # 预训练模型目录
│   ├── Fun-CosyVoice3-0.5B/   # Fun-CosyVoice 3.0 模型
│   ├── CosyVoice2-0.5B/       # CosyVoice 2.0 模型
│   ├── CosyVoice-300M/        # CosyVoice 1.0 基础模型
│   ├── CosyVoice-300M-SFT/    # CosyVoice SFT 模型
│   ├── CosyVoice-300M-Instruct/ # CosyVoice Instruct 模型
│   ├── CosyVoice-ttsfrd/      # 文本标准化资源
│   └── SenseVoiceSmall/       # （可选）ASR模型
├── custom_voices/              # 自定义音色库存储
│   └── [voice_id]/            # 每个自定义音色都有自己的文件夹
│       ├── audio.wav          # 音色音频样本
│       └── metadata.json      # 音色元数据（名称、文本等）
├── cosyvoice/                  # CosyVoice核心库
├── third_party/                # 第三方依赖
├── webui.py                    # 官方Web界面
├── app_local.py                # 增强版本地Web界面（含音色库）
├── voice_manager.py            # 音色库管理模块
└── requirements.txt            # Python依赖
```

### 关于 `custom_voices` 文件夹

`custom_voices/` 目录用于存储通过WebUI创建的自定义音色配置文件。每个音色配置文件包含：
- **音频样本**：用于语音克隆的参考音频文件（WAV格式）
- **元数据**：音色名称、提示文本、创建时间和音色ID

您可以：
- 从WebUI保存自定义音色以供日后重复使用
- 加载已保存的音色而无需重新上传音频文件
- 管理（删除）不需要的音色配置文件
- 通过复制音色文件夹来分享音色配置文件

**注意**：此文件夹已通过 `.gitignore` 排除在Git之外，以保持仓库整洁。

## 基本使用

我们强烈建议使用 `Fun-CosyVoice3-0.5B` 以获得更好的性能。
请参阅 `example.py` 中的代码了解每个模型的详细使用方法。
```sh
python example.py
```

#### CosyVoice2 vllm 使用

如果您想使用 vllm 进行推理，请安装 `vllm==v0.9.0`。较旧的 vllm 版本不支持 CosyVoice2 推理。

注意 `vllm==v0.9.0` 有很多特定要求，例如 `torch==2.7.0`。您可以创建一个新环境以防硬件不支持 vllm 且旧环境损坏。

``` sh
conda create -n cosyvoice_vllm --clone cosyvoice
conda activate cosyvoice_vllm
pip install vllm==v0.9.0 transformers==4.51.3 -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
python vllm_example.py
```

#### 启动Web演示

您可以使用我们的Web演示页面快速熟悉 CosyVoice。

**选项1：官方WebUI**
``` python
# 使用 iic/CosyVoice-300M-SFT 进行sft推理，或使用 iic/CosyVoice-300M-Instruct 进行instruct推理
python3 webui.py --port 50000 --model_dir pretrained_models/CosyVoice-300M
```

**选项2：增强版本地WebUI（含音色库）**
``` python
# 推荐：使用 app_local.py 获取音色库管理和ASR功能
python3 app_local.py --port 50000 --model_dir pretrained_models/Fun-CosyVoice3-0.5B
```

增强版WebUI（`app_local.py`）包括：
- 音色库管理（保存/加载/删除自定义音色）
- Prompt音频的自动语音识别
- 音频后处理和增强
- 自动在浏览器中启动

#### 高级用法

对于高级用户，我们在 `examples/libritts/cosyvoice/run.sh` 中提供了训练和推理脚本。

#### 构建部署

可选地，如果您想进行服务部署，
可以运行以下步骤。

``` sh
cd runtime/python
docker build -t cosyvoice:v1.0 .
# 如果要使用instruct推理，请将 iic/CosyVoice-300M 更改为 iic/CosyVoice-300M-Instruct
# grpc 用法
docker run -d --runtime=nvidia -p 50000:50000 cosyvoice:v1.0 /bin/bash -c "cd /opt/CosyVoice/CosyVoice/runtime/python/grpc && python3 server.py --port 50000 --max_conc 4 --model_dir iic/CosyVoice-300M && sleep infinity"
cd grpc && python3 client.py --port 50000 --mode <sft|zero_shot|cross_lingual|instruct>
# fastapi 用法
docker run -d --runtime=nvidia -p 50000:50000 cosyvoice:v1.0 /bin/bash -c "cd /opt/CosyVoice/CosyVoice/runtime/python/fastapi && python3 server.py --port 50000 --model_dir iic/CosyVoice-300M && sleep infinity"
cd fastapi && python3 client.py --port 50000 --mode <sft|zero_shot|cross_lingual|instruct>
```

#### 使用 Nvidia TensorRT-LLM 进行部署

使用 TensorRT-LLM 加速 cosyvoice2 llm 可以比 huggingface transformers 实现获得4倍的加速。
快速入门：

``` sh
cd runtime/triton_trtllm
docker compose up -d
```
更多详情，请查看[这里](https://github.com/FunAudioLLM/CosyVoice/tree/main/runtime/triton_trtllm)

## 讨论与交流

您可以直接在 [Github Issues](https://github.com/FunAudioLLM/CosyVoice/issues) 上讨论。

您也可以扫描二维码加入我们的官方钉钉交流群。

<img src="./asset/dingding.png" width="250px">

## 致谢

1. 我们从 [FunASR](https://github.com/modelscope/FunASR) 借用了大量代码。
2. 我们从 [FunCodec](https://github.com/modelscope/FunCodec) 借用了大量代码。
3. 我们从 [Matcha-TTS](https://github.com/shivammehta25/Matcha-TTS) 借用了大量代码。
4. 我们从 [AcademiCodec](https://github.com/yangdongchao/AcademiCodec) 借用了大量代码。
5. 我们从 [WeNet](https://github.com/wenet-e2e/wenet) 借用了大量代码。

## 引用

``` bibtex
@article{du2024cosyvoice,
  title={Cosyvoice: A scalable multilingual zero-shot text-to-speech synthesizer based on supervised semantic tokens},
  author={Du, Zhihao and Chen, Qian and Zhang, Shiliang and Hu, Kai and Lu, Heng and Yang, Yexin and Hu, Hangrui and Zheng, Siqi and Gu, Yue and Ma, Ziyang and others},
  journal={arXiv preprint arXiv:2407.05407},
  year={2024}
}

@article{du2024cosyvoice,
  title={Cosyvoice 2: Scalable streaming speech synthesis with large language models},
  author={Du, Zhihao and Wang, Yuxuan and Chen, Qian and Shi, Xian and Lv, Xiang and Zhao, Tianyu and Gao, Zhifu and Yang, Yexin and Gao, Changfeng and Wang, Hui and others},
  journal={arXiv preprint arXiv:2412.10117},
  year={2024}
}

@article{du2025cosyvoice,
  title={CosyVoice 3: Towards In-the-wild Speech Generation via Scaling-up and Post-training},
  author={Du, Zhihao and Gao, Changfeng and Wang, Yuxuan and Yu, Fan and Zhao, Tianyu and Wang, Hao and Lv, Xiang and Wang, Hui and Shi, Xian and An, Keyu and others},
  journal={arXiv preprint arXiv:2505.17589},
  year={2025}
}

@inproceedings{lyu2025build,
  title={Build LLM-Based Zero-Shot Streaming TTS System with Cosyvoice},
  author={Lyu, Xiang and Wang, Yuxuan and Zhao, Tianyu and Wang, Hao and Liu, Huadai and Du, Zhihao},
  booktitle={ICASSP 2025-2025 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)},
  pages={1--2},
  year={2025},
  organization={IEEE}
}
```

## 免责声明
以上提供的内容仅用于学术目的，旨在演示技术能力。部分示例来源于互联网。如果任何内容侵犯了您的权利，请联系我们要求删除。
