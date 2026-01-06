"""
Migration script: Flat file structure -> Folder-based structure

Old structure:
custom_voices/
├── voices_metadata.json
└── 819873f6.wav

New structure:
custom_voices/
└── 819873f6/
    ├── metadata.json
    └── audio.wav
"""
import os
import json
import shutil
from datetime import datetime

VOICE_LIBRARY_DIR = "custom_voices"
BACKUP_DIR = "custom_voices_backup"

def migrate_voices():
    """Migrate from flat structure to folder-based structure"""
    
    print("=" * 60)
    print("Voice Library Migration")
    print("=" * 60)
    
    # Check if old metadata exists
    old_metadata_path = os.path.join(VOICE_LIBRARY_DIR, "voices_metadata.json")
    if not os.path.exists(old_metadata_path):
        print("No existing voices_metadata.json found. Migration not needed.")
        return
    
    # Load old metadata
    with open(old_metadata_path, 'r', encoding='utf-8') as f:
        old_metadata = json.load(f)
    
    if not old_metadata:
        print("No voices to migrate.")
        return
    
    print(f"\nFound {len(old_metadata)} voice(s) to migrate")
    
    # Create backup
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    print(f"\n📦 Creating backup in {BACKUP_DIR}/")
    shutil.copy2(old_metadata_path, os.path.join(BACKUP_DIR, "voices_metadata.json"))
    
    # Migrate each voice
    for voice_id, voice_data in old_metadata.items():
        print(f"\n🔄 Migrating voice: {voice_data.get('name', 'Unknown')} ({voice_id})")
        
        # Create voice folder
        voice_folder = os.path.join(VOICE_LIBRARY_DIR, voice_id)
        if not os.path.exists(voice_folder):
            os.makedirs(voice_folder)
            print(f"   Created folder: {voice_folder}/")
        
        # Move audio file
        old_audio_path = voice_data.get('audio')
        if old_audio_path and os.path.exists(old_audio_path):
            # Get file extension
            _, ext = os.path.splitext(old_audio_path)
            new_audio_path = os.path.join(voice_folder, f"audio{ext}")
            
            # Backup original
            backup_audio = os.path.join(BACKUP_DIR, os.path.basename(old_audio_path))
            shutil.copy2(old_audio_path, backup_audio)
            
            # Move to new location
            shutil.move(old_audio_path, new_audio_path)
            print(f"   Moved audio: {os.path.basename(old_audio_path)} -> {voice_id}/audio{ext}")
            
            # Update audio path in metadata
            voice_data['audio'] = new_audio_path
        
        # Create individual metadata.json
        metadata_path = os.path.join(voice_folder, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(voice_data, f, ensure_ascii=False, indent=2)
        print(f"   Created: {voice_id}/metadata.json")
    
    # Remove old metadata file
    print(f"\n🗑️  Removing old voices_metadata.json")
    os.remove(old_metadata_path)
    
    print("\n" + "=" * 60)
    print("✅ Migration completed successfully!")
    print("=" * 60)
    print(f"\nBackup location: {BACKUP_DIR}/")
    print(f"Migrated {len(old_metadata)} voice(s)")
    print("\nNew structure:")
    for voice_id in old_metadata.keys():
        print(f"  custom_voices/{voice_id}/")
        print(f"    ├── metadata.json")
        print(f"    └── audio.*")

if __name__ == "__main__":
    migrate_voices()
