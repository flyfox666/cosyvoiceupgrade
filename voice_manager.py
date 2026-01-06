"""
Voice Manager Module for CosyVoice WebUI (Folder-based Storage)
管理自定义音色库的保存、加载和删除功能 - 使用文件夹结构
"""
import os
import json
import shutil
import uuid
from datetime import datetime

# 音色库存储目录
VOICE_LIBRARY_DIR = "custom_voices"

def _ensure_voice_library_dir():
    """确保音色库目录存在"""
    if not os.path.exists(VOICE_LIBRARY_DIR):
        os.makedirs(VOICE_LIBRARY_DIR)

def _get_voice_folder(voice_id):
    """获取音色文件夹路径"""
    return os.path.join(VOICE_LIBRARY_DIR, voice_id)

def _get_voice_metadata_path(voice_id):
    """获取音色元数据文件路径"""
    return os.path.join(_get_voice_folder(voice_id), "metadata.json")

def _load_voice_metadata(voice_id):
    """加载单个音色的元数据"""
    metadata_path = _get_voice_metadata_path(voice_id)
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载音色元数据失败 ({voice_id}): {e}")
            return None
    return None

def _save_voice_metadata(voice_id, metadata):
    """保存单个音色的元数据"""
    voice_folder = _get_voice_folder(voice_id)
    if not os.path.exists(voice_folder):
        os.makedirs(voice_folder)
    
    metadata_path = _get_voice_metadata_path(voice_id)
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存音色元数据失败: {e}")
        return False

def save_custom_voice(name, audio_file, prompt_text):
    """
    保存自定义音色（文件夹结构）
    
    Args:
        name: 音色名称
        audio_file: 音频文件路径
        prompt_text: prompt 文本
    
    Returns:
        dict: {"success": bool, "message": str, "voice_id": str}
    """
    _ensure_voice_library_dir()
    
    if not audio_file or not os.path.exists(audio_file):
        return {"success": False, "message": "音频文件不存在"}
    
    if not name or not prompt_text:
        return {"success": False, "message": "音色名称和 prompt 文本不能为空"}
    
    # 生成唯一的 voice_id
    voice_id = str(uuid.uuid4())[:8]
    voice_folder = _get_voice_folder(voice_id)
    
    try:
        # 创建音色文件夹
        os.makedirs(voice_folder)
        
        # 获取音频文件扩展名
        _, ext = os.path.splitext(audio_file)
        if not ext:
            ext = ".wav"
        
        # 复制音频文件到音色文件夹
        audio_filename = f"audio{ext}"
        audio_dest = os.path.join(voice_folder, audio_filename)
        shutil.copy2(audio_file, audio_dest)
        
        # 创建元数据
        metadata = {
            "name": name,
            "audio": audio_dest,
            "text": prompt_text,
            "created_at": datetime.now().isoformat(),
            "voice_id": voice_id
        }
        
        # 保存元数据
        if _save_voice_metadata(voice_id, metadata):
            return {"success": True, "message": "保存成功", "voice_id": voice_id}
        else:
            # 如果保存元数据失败，清理文件夹
            if os.path.exists(voice_folder):
                shutil.rmtree(voice_folder)
            return {"success": False, "message": "保存元数据失败"}
            
    except Exception as e:
        # 出错时清理
        if os.path.exists(voice_folder):
            shutil.rmtree(voice_folder)
        return {"success": False, "message": f"保存失败: {e}"}

def load_custom_voices():
    """
    加载所有自定义音色（扫描文件夹）
    
    Returns:
        dict: {voice_id: voice_data}
    """
    _ensure_voice_library_dir()
    voices = {}
    
    try:
        # 扫描所有子文件夹
        for item in os.listdir(VOICE_LIBRARY_DIR):
            item_path = os.path.join(VOICE_LIBRARY_DIR, item)
            
            # 只处理文件夹
            if os.path.isdir(item_path):
                voice_id = item
                metadata = _load_voice_metadata(voice_id)
                
                if metadata:
                    voices[voice_id] = metadata
    except Exception as e:
        print(f"加载音色库失败: {e}")
    
    return voices

def delete_custom_voice(voice_id):
    """
    删除自定义音色（删除整个文件夹）
    
    Args:
        voice_id: 音色 ID
    
    Returns:
        dict: {"success": bool, "message": str}
    """
    voice_folder = _get_voice_folder(voice_id)
    
    if not os.path.exists(voice_folder):
        return {"success": False, "message": "音色不存在"}
    
    try:
        # 删除整个音色文件夹
        shutil.rmtree(voice_folder)
        return {"success": True, "message": "删除成功"}
    except Exception as e:
        return {"success": False, "message": f"删除失败: {e}"}

def get_voice_by_id(voice_id):
    """
    通过 ID 获取音色数据
    
    Args:
        voice_id: 音色 ID
    
    Returns:
        dict or None: 音色数据
    """
    return _load_voice_metadata(voice_id)

def get_voice_list_for_dropdown():
    """
    获取用于下拉菜单的音色列表
    
    Returns:
        list: ["音色名称 (voice_id)", ...]
    """
    voices = load_custom_voices()
    voice_list = []
    
    # 按创建时间排序（最新的在前）
    sorted_voices = sorted(
        voices.items(),
        key=lambda x: x[1].get("created_at", ""),
        reverse=True
    )
    
    for voice_id, voice_data in sorted_voices:
        name = voice_data.get("name", "未命名")
        voice_list.append(f"{name} ({voice_id})")
    
    return voice_list

def get_voice_audio_path(voice_id):
    """
    获取音色的音频文件路径
    
    Args:
        voice_id: 音色 ID
    
    Returns:
        str or None: 音频文件路径
    """
    metadata = _load_voice_metadata(voice_id)
    if metadata:
        return metadata.get("audio")
    return None

def update_voice_metadata(voice_id, updates):
    """
    更新音色元数据
    
    Args:
        voice_id: 音色 ID
        updates: 要更新的字段字典
    
    Returns:
        dict: {"success": bool, "message": str}
    """
    metadata = _load_voice_metadata(voice_id)
    if not metadata:
        return {"success": False, "message": "音色不存在"}
    
    # 更新字段
    metadata.update(updates)
    metadata["updated_at"] = datetime.now().isoformat()
    
    if _save_voice_metadata(voice_id, metadata):
        return {"success": True, "message": "更新成功"}
    else:
        return {"success": False, "message": "更新失败"}
