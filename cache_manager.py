"""
Embedding Cache Manager
管理语音嵌入向量的缓存，提升推理性能
"""
import os
import torch
import hashlib
import json
from pathlib import Path
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Embedding cache manager for voice cloning acceleration"""
    
    def __init__(self, custom_voices_dir: str = "custom_voices"):
        self.custom_voices_dir = custom_voices_dir
        self.memory_cache: Dict[str, torch.Tensor] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "saves": 0,
            "loads": 0
        }
    
    def _get_cache_path(self, voice_id: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.custom_voices_dir, voice_id, "embedding.pt")
    
    def _get_audio_hash(self, audio_path: str) -> str:
        """计算音频文件的哈希值，用于检测文件变化"""
        try:
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
                return hashlib.md5(audio_data).hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute audio hash: {e}")
            return ""
    
    def _get_cache_metadata_path(self, voice_id: str) -> str:
        """获取缓存元数据路径"""
        return os.path.join(self.custom_voices_dir, voice_id, "cache_metadata.json")
    
    def _save_cache_metadata(self, voice_id: str, audio_hash: str):
        """保存缓存元数据（包括音频哈希）"""
        metadata_path = self._get_cache_metadata_path(voice_id)
        metadata = {
            "audio_hash": audio_hash,
            "cached_at": torch.datetime.datetime.now().isoformat() if hasattr(torch, 'datetime') else ""
        }
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _load_cache_metadata(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """加载缓存元数据"""
        metadata_path = self._get_cache_metadata_path(voice_id)
        if not os.path.exists(metadata_path):
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache metadata: {e}")
            return None
    
    def has_cache(self, voice_id: str, audio_path: str) -> bool:
        """
        检查是否存在有效的缓存
        
        Args:
            voice_id: 音色 ID
            audio_path: 音频文件路径
        
        Returns:
            bool: 是否存在有效缓存
        """
        cache_path = self._get_cache_path(voice_id)
        
        # 检查缓存文件是否存在
        if not os.path.exists(cache_path):
            return False
        
        # 检查音频文件是否被修改（通过哈希值）
        current_hash = self._get_audio_hash(audio_path)
        metadata = self._load_cache_metadata(voice_id)
        
        if metadata is None:
            return False
        
        cached_hash = metadata.get("audio_hash", "")
        
        # 如果哈希值不匹配，说明音频文件已修改，缓存失效
        if current_hash != cached_hash:
            logger.info(f"Cache invalidated for voice {voice_id} (audio modified)")
            self.delete_cache(voice_id)
            return False
        
        return True
    
    def save_embedding(self, voice_id: str, embedding: torch.Tensor, audio_path: str):
        """
        保存嵌入向量到缓存
        
        Args:
            voice_id: 音色 ID
            embedding: 嵌入向量
            audio_path: 音频文件路径
        """
        cache_path = self._get_cache_path(voice_id)
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            
            # 保存嵌入向量
            torch.save(embedding, cache_path)
            
            # 保存元数据
            audio_hash = self._get_audio_hash(audio_path)
            self._save_cache_metadata(voice_id, audio_hash)
            
            # 加载到内存缓存
            self.memory_cache[voice_id] = embedding
            
            self.cache_stats["saves"] += 1
            logger.info(f"Saved embedding cache for voice {voice_id}")
            
        except Exception as e:
            logger.error(f"Failed to save embedding cache: {e}")
    
    def load_embedding(self, voice_id: str, audio_path: str) -> Optional[torch.Tensor]:
        """
        加载嵌入向量缓存
        
        Args:
            voice_id: 音色 ID
            audio_path: 音频文件路径
        
        Returns:
            torch.Tensor or None: 嵌入向量，如果缓存不存在或失效则返回 None
        """
        # 先检查内存缓存
        if voice_id in self.memory_cache:
            self.cache_stats["hits"] += 1
            logger.debug(f"Memory cache hit for voice {voice_id}")
            return self.memory_cache[voice_id]
        
        # 检查磁盘缓存
        if not self.has_cache(voice_id, audio_path):
            self.cache_stats["misses"] += 1
            return None
        
        cache_path = self._get_cache_path(voice_id)
        
        try:
            embedding = torch.load(cache_path)
            
            # 加载到内存缓存
            self.memory_cache[voice_id] = embedding
            
            self.cache_stats["loads"] += 1
            self.cache_stats["hits"] += 1
            logger.info(f"Loaded embedding cache for voice {voice_id}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to load embedding cache: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    def delete_cache(self, voice_id: str):
        """
        删除缓存
        
        Args:
            voice_id: 音色 ID
        """
        cache_path = self._get_cache_path(voice_id)
        metadata_path = self._get_cache_metadata_path(voice_id)
        
        # 从内存中删除
        if voice_id in self.memory_cache:
            del self.memory_cache[voice_id]
        
        # 删除磁盘文件
        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
                logger.info(f"Deleted embedding cache for voice {voice_id}")
            
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
                
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
    
    def clear_memory_cache(self):
        """清空内存缓存"""
        self.memory_cache.clear()
        logger.info("Cleared memory cache")
    
    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            "memory_cached": len(self.memory_cache),
            "hit_rate": round(hit_rate, 2)
        }
    
    def preload_all_caches(self):
        """预加载所有可用的缓存到内存"""
        from voice_manager import load_custom_voices
        
        voices = load_custom_voices()
        loaded_count = 0
        
        for voice_id, voice_data in voices.items():
            audio_path = voice_data.get("audio")
            if audio_path and self.has_cache(voice_id, audio_path):
                embedding = self.load_embedding(voice_id, audio_path)
                if embedding is not None:
                    loaded_count += 1
        
        logger.info(f"Preloaded {loaded_count} embedding caches into memory")
        return loaded_count

# Global cache instance
_global_cache = None

def get_embedding_cache() -> EmbeddingCache:
    """获取全局缓存实例（单例模式）"""
    global _global_cache
    if _global_cache is None:
        _global_cache = EmbeddingCache()
    return _global_cache
