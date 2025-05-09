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
    """Класс для представления научной статьи."""
    
    id: str
    title: str
    authors: List[str]
    abstract: str
    year: int
    doi: Optional[str] = None
    url: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    keywords: List[str] = None
    full_text: Optional[str] = None
    file_path: Optional[str] = None
    categories: List[str] = None
    added_date: datetime = None
    source: str = "Unknown"
    citation_count: int = 0
    reference_count: int = 0
    summary: Optional[str] = None
    references: List[str] = None
    published: Optional[datetime] = None

    def __post_init__(self):
        """Инициализация после создания объекта."""
        self.keywords = self.keywords or []
        self.categories = self.categories or []
        self.references = self.references or []
        self.added_date = self.added_date or datetime.now()

    @property
    def citation(self) -> str:
        """Возвращает форматированную цитату статьи."""
        authors = ", ".join(self.authors)
        year = f"({self.year})" if self.year else ""
        journal = f". {self.journal}" if self.journal else ""
        volume = f", {self.volume}" if self.volume else ""
        issue = f"({self.issue})" if self.issue else ""
        pages = f", {self.pages}" if self.pages else ""
        doi = f". DOI: {self.doi}" if self.doi else ""
        
        return f"{authors} {year}. {self.title}{journal}{volume}{issue}{pages}{doi}"

    def to_dict(self) -> dict:
        """Преобразует статью в словарь для сериализации."""
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'year': self.year,
            'doi': self.doi,
            'url': self.url,
            'journal': self.journal,
            'volume': self.volume,
            'issue': self.issue,
            'pages': self.pages,
            'keywords': self.keywords,
            'full_text': self.full_text,
            'file_path': self.file_path,
            'categories': self.categories,
            'added_date': self.added_date.isoformat() if self.added_date else None,
            'source': self.source,
            'citation_count': self.citation_count,
            'reference_count': self.reference_count,
            'summary': self.summary,
            'references': self.references,
            'published': self.published.isoformat() if self.published else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Article':
        """Создает объект статьи из словаря."""
        if 'added_date' in data and data['added_date']:
            data['added_date'] = datetime.fromisoformat(data['added_date'])
        if 'published' in data and data['published']:
            data['published'] = datetime.fromisoformat(data['published'])
        return cls(**data)

    def to_bibtex(self) -> str:
        """Возвращает статью в формате BibTeX."""
        # Создаем ключ для BibTeX
        first_author = self.authors[0].split(',')[0] if self.authors else "Unknown"
        bibtex_key = f"{first_author}{self.year}"
        
        # Формируем записи
        entries = [
            f"@article{{{bibtex_key},",
            f"  title = {{{self.title}}},",
            f"  author = {{{' and '.join(self.authors)}}},",
            f"  year = {{{self.year}}},",
        ]
        
        # Добавляем опциональные поля
        if self.journal:
            entries.append(f"  journal = {{{self.journal}}},")
        if self.volume:
            entries.append(f"  volume = {{{self.volume}}},")
        if self.issue:
            entries.append(f"  number = {{{self.issue}}},")
        if self.pages:
            entries.append(f"  pages = {{{self.pages}}},")
        if self.doi:
            entries.append(f"  doi = {{{self.doi}}},")
        if self.url:
            entries.append(f"  url = {{{self.url}}},")
        
        # Удаляем запятую у последней записи и добавляем закрывающую скобку
        entries[-1] = entries[-1][:-1]
        entries.append("}")
        
        return "\n".join(entries)
    
    @property
    def author(self) -> str:
        """Возвращает основного автора статьи в виде строки."""
        if not self.authors:
            return "Unknown"
        elif len(self.authors) == 1:
            return self.authors[0]
        else:
            return f"{self.authors[0]} et al."
    
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