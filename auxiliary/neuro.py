# -*- coding: utf-8 -*-
import os
from typing import List, Tuple, Dict, Union

from frontmatter import load


class FileMetadataExtractor:
    """Экстрактор данных из файлов."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_metadata(self) -> Tuple[int, str, bool]:
        """
        Извлекает вес, заголовок и флаг черновика из файла.
        """
        post = load(self.file_path, encoding="utf-8")
        weight: int = int(post.metadata.get("weight", 0))
        title: str = post.metadata.get("title", "")
        draft: bool = (post.metadata.get("weight", "false") == "true")

        return weight, title, draft


class DirectoryStructureBuilder:
    """Строитель структуры директорий и файлов."""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def build_hierarchy(self) -> Dict[str, Union[str, Dict]]:
        """
        Рекурсивно строит иерархию директорий и файлов.
        """
        hierarchy = {}
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            # Изначально определяем rel_path для текущей папки
            rel_path = os.path.relpath(dirpath, self.root_dir)

            # Если папка валидна (есть index.md или _index.md)
            index_md = next((fn for fn in filenames if fn in ('index.md', '_index.md')), None)
            if index_md:
                file_path = os.path.join(dirpath, index_md)
                metadata_extractor = FileMetadataExtractor(file_path)
                weight, title, _ = metadata_extractor.extract_metadata()
                hierarchy[rel_path] = {'weight': weight, 'title': title, 'children': []}

            # Если есть файлы помимо index.md или _index.md, добавляем их в children
            other_files = [file for file in filenames if file != index_md and file.endswith('.md')]
            for file in other_files:
                file_path = os.path.join(dirpath, file)
                metadata_extractor = FileMetadataExtractor(file_path)
                weight, title, draft = metadata_extractor.extract_metadata()
                if not draft:
                    hierarchy[rel_path]['children'].append({'path': file_path, 'weight': weight, 'title': title})

            # Проходим по вложенным папкам
            for subdir in dirnames:
                child_dir = os.path.join(dirpath, subdir)
                child_hierarchy = self.build_hierarchy_for_subdir(child_dir)
                if child_hierarchy:
                    hierarchy.update(child_hierarchy)

        return hierarchy

    def build_hierarchy_for_subdir(self, dirpath: str) -> Dict[str, Union[str, Dict]]:
        """
        Отдельный метод для рекурсивной обработки вложенных папок.
        """
        hierarchy = {}
        for dirpath_, dirnames, filenames in os.walk(dirpath):
            # Изначально определяем rel_path для текущей папки
            rel_path = os.path.relpath(dirpath_, self.root_dir)

            # Если папка валидна (есть index.md или _index.md)
            index_md = next((fn for fn in filenames if fn in ('index.md', '_index.md')), None)
            if index_md:
                file_path = os.path.join(dirpath_, index_md)
                metadata_extractor = FileMetadataExtractor(file_path)
                weight, title, _ = metadata_extractor.extract_metadata()
                hierarchy[rel_path] = {'weight': weight, 'title': title, 'children': []}

            # Если есть файлы помимо index.md или _index.md, добавляем их в children
            other_files = [file for file in filenames if file != index_md and file.endswith('.md')]
            for file in other_files:
                file_path = os.path.join(dirpath_, file)
                metadata_extractor = FileMetadataExtractor(file_path)
                weight, title, draft = metadata_extractor.extract_metadata()
                if not draft:
                    hierarchy[rel_path]['children'].append({'path': file_path, 'weight': weight, 'title': title})

            for subdir in dirnames:
                child_dir = os.path.join(dirpath_, subdir)
                child_hierarchy = self.build_hierarchy_for_subdir(child_dir)
                if child_hierarchy:
                    hierarchy.update(child_hierarchy)

        return hierarchy


class DirectoryAnalyzer:
    """Главный класс для анализа директорий."""

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def analyze(self) -> Dict[str, Union[str, Dict]]:
        """
        Главный метод для анализа директорий и построения структуры.
        """
        builder = DirectoryStructureBuilder(self.root_dir)
        result = builder.build_hierarchy()
        return result


if __name__ == '__main__':
    # Пример использования
    root_dir = '../../MME/content/common'
    analyzer = DirectoryAnalyzer(root_dir)
    result = analyzer.analyze()
    for key, value in result.items():
        print(f"{key}: {value}")
