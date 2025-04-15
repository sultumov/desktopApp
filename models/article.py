from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Author:
    """Модель представления автора статьи."""
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None


@dataclass
class Article:
    """Модель представления научной статьи."""
    title: str
    authors: List[Author]
    abstract: str
    year: int
    doi: Optional[str] = None
    url: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    full_text: Optional[str] = None
    references: List['Article'] = field(default_factory=list)
    file_path: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    added_date: datetime = field(default_factory=datetime.now)
    source: str = "Unknown"
    confidence: float = 0.0  # Уверенность при поиске источников
    citation_count: int = 0   # Для Semantic Scholar - количество цитирований
    reference_count: int = 0  # Для Semantic Scholar - количество ссылок
    paper_id: Optional[str] = None  # ID статьи в API источника
    
    @property
    def author(self) -> str:
        """Возвращает основного автора статьи в виде строки."""
        if not self.authors:
            return "Unknown"
        elif len(self.authors) == 1:
            return self.authors[0].name
        else:
            return f"{self.authors[0].name} et al."
    
    @property
    def citation(self) -> str:
        """Возвращает полную библиографическую ссылку на статью."""
        authors_str = ", ".join([author.name for author in self.authors])
        
        if self.journal:
            if self.volume and self.issue and self.pages:
                return f"{authors_str} ({self.year}). {self.title}. {self.journal}, {self.volume}({self.issue}), {self.pages}."
            else:
                return f"{authors_str} ({self.year}). {self.title}. {self.journal}."
        else:
            return f"{authors_str} ({self.year}). {self.title}."
    
    @property
    def display_info(self) -> str:
        """Возвращает информацию для отображения в списке."""
        citation_info = ""
        if self.citation_count > 0:
            citation_info = f" [цитирований: {self.citation_count}]"
            
        reference_info = ""
        if self.reference_count > 0:
            reference_info = f" [источников: {self.reference_count}]"
            
        return f"{self.title} ({self.year}, {self.author}){citation_info}{reference_info} [{self.source}]"
    
    def to_bibtex(self) -> str:
        """Преобразует статью в формат BibTeX."""
        # Создаем ключ цитирования на основе фамилии первого автора и года
        if self.authors and self.authors[0].name:
            last_name = self.authors[0].name.split()[-1].lower()
            key = f"{last_name}{self.year}"
        else:
            key = f"unknown{self.year}"
        
        bibtex = [f"@article{{{key},"]
        
        # Добавляем обязательные поля
        bibtex.append(f"  title = {{{self.title}}},")
        
        # Авторы
        if self.authors:
            authors_str = " and ".join([author.name for author in self.authors])
            bibtex.append(f"  author = {{{authors_str}}},")
        
        # Год
        bibtex.append(f"  year = {{{self.year}}},")
        
        # Добавляем необязательные поля, если они есть
        if self.journal:
            bibtex.append(f"  journal = {{{self.journal}}},")
        
        if self.volume:
            bibtex.append(f"  volume = {{{self.volume}}},")
        
        if self.issue:
            bibtex.append(f"  number = {{{self.issue}}},")
        
        if self.pages:
            bibtex.append(f"  pages = {{{self.pages}}},")
        
        if self.doi:
            bibtex.append(f"  doi = {{{self.doi}}},")
        
        if self.url:
            bibtex.append(f"  url = {{{self.url}}},")
        
        # Завершаем запись
        bibtex.append("}")
        
        return "\n".join(bibtex) 