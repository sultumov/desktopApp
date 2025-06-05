"""Сервис для создания интеллект-карт."""

import logging
from typing import List, Dict, Any, Optional
import networkx as nx
import matplotlib.pyplot as plt
from models.article import Article
import re
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class MindMapService:
    """Сервис для создания интеллект-карт."""
    
    def __init__(self):
        """Инициализация сервиса."""
        self.output_dir = Path("output/mindmaps")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def create_mindmap(self, article: Article, keywords: List[str]) -> Optional[str]:
        """Создает интеллект-карту для статьи на основе ключевых слов.
        
        Args:
            article: Объект статьи
            keywords: Список ключевых слов
            
        Returns:
            Путь к созданному изображению или None в случае ошибки
        """
        try:
            logger.info(f"Создание интеллект-карты для статьи: {article.title}")
            
            if not keywords:
                logger.warning("Не предоставлены ключевые слова")
                return None
                
            # Создаем граф
            G = nx.Graph()
            
            # Добавляем центральный узел (название статьи)
            title_short = article.title[:50] + "..." if len(article.title) > 50 else article.title
            G.add_node(title_short, size=3000, color='lightblue')
            
            # Добавляем узлы ключевых слов и связи
            for keyword in keywords:
                G.add_node(keyword, size=2000, color='lightgreen')
                G.add_edge(title_short, keyword)
                
                # Ищем связи между ключевыми словами в тексте
                for other_keyword in keywords:
                    if keyword != other_keyword:
                        # Проверяем, встречаются ли слова рядом в тексте
                        if self._are_words_related(article.abstract or "", keyword, other_keyword):
                            G.add_edge(keyword, other_keyword)
            
            # Создаем изображение
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # Рисуем узлы
            nx.draw_networkx_nodes(G, pos,
                                 node_color=[G.nodes[node]['color'] for node in G.nodes()],
                                 node_size=[G.nodes[node]['size'] for node in G.nodes()],
                                 alpha=0.7)
            
            # Рисуем связи
            nx.draw_networkx_edges(G, pos, alpha=0.5)
            
            # Добавляем подписи
            nx.draw_networkx_labels(G, pos, font_size=8, font_family='sans-serif')
            
            # Сохраняем изображение
            output_path = self.output_dir / f"mindmap_{article.id}.png"
            plt.savefig(output_path, format='png', dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Интеллект-карта сохранена: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Ошибка при создании интеллект-карты: {str(e)}", exc_info=True)
            return None
            
    def _are_words_related(self, text: str, word1: str, word2: str, max_distance: int = 50) -> bool:
        """Проверяет, встречаются ли слова рядом в тексте.
        
        Args:
            text: Текст для анализа
            word1: Первое слово
            word2: Второе слово
            max_distance: Максимальное расстояние между словами в символах
            
        Returns:
            True если слова встречаются рядом, False иначе
        """
        # Ищем все вхождения первого слова
        positions1 = [m.start() for m in re.finditer(re.escape(word1.lower()), text.lower())]
        positions2 = [m.start() for m in re.finditer(re.escape(word2.lower()), text.lower())]
        
        # Проверяем расстояние между словами
        for pos1 in positions1:
            for pos2 in positions2:
                if abs(pos1 - pos2) <= max_distance:
                    return True
                    
        return False 