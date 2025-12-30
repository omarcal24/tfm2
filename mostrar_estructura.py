#!/usr/bin/env python3
"""
Script para mostrar la estructura del proyecto
"""
import os
from pathlib import Path

def show_structure(path, prefix="", max_depth=3, current_depth=0):
    if current_depth >= max_depth:
        return
    
    try:
        items = sorted(path.iterdir())
    except PermissionError:
        return
    
    for i, item in enumerate(items):
        # Ignorar directorios comunes
        if item.name in ['.git', '__pycache__', '.venv', 'venv', 'node_modules', '.pytest_cache']:
            continue
        
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{current_prefix}{item.name}")
        
        if item.is_dir():
            extension = "    " if is_last else "│   "
            show_structure(item, prefix + extension, max_depth, current_depth + 1)

# Empezar desde el directorio actual
current = Path.cwd()
print(f"\n📁 Estructura desde: {current}")
print("="*60)
print(f"{current.name}/")
show_structure(current, "", max_depth=3)
