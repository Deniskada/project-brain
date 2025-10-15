"""
Экспорт документации в различные форматы
"""
import logging
from typing import Dict, Any
import markdown
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentationExporter:
    """Экспорт документации в различные форматы"""
    
    def __init__(self):
        # Настройки markdown
        self.md_extensions = [
            'extra',
            'codehilite',
            'toc',
            'tables',
            'fenced_code'
        ]
    
    def to_html(self, markdown_content: str, title: str = "Документация") -> str:
        """
        Конвертация Markdown в HTML с красивым оформлением
        """
        try:
            # Конвертируем markdown в HTML
            html_body = markdown.markdown(
                markdown_content,
                extensions=self.md_extensions
            )
            
            # Оборачиваем в полный HTML документ
            html_template = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        
        h3 {{
            color: #7f8c8d;
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        
        p {{
            margin: 15px 0;
        }}
        
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin: 8px 0;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
        }}
        
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 20px 0;
        }}
        
        pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        
        th {{
            background: #3498db;
            color: white;
            font-weight: 600;
        }}
        
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        
        strong {{
            color: #2c3e50;
        }}
        
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        .toc {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 6px;
            margin: 30px 0;
        }}
        
        .toc ul {{
            list-style: none;
        }}
        
        .footer {{
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
        
        <div class="footer">
            <p>Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Project Brain - Автоматическая генерация документации</p>
        </div>
    </div>
</body>
</html>"""
            
            return html_template
            
        except Exception as e:
            logger.error(f"Ошибка конвертации в HTML: {e}")
            return f"<html><body><h1>Ошибка</h1><p>{str(e)}</p></body></html>"
    
    def to_pdf_html(self, markdown_content: str, title: str = "Документация") -> str:
        """
        Конвертация в HTML, оптимизированный для печати в PDF
        """
        # Используем тот же HTML, но с дополнительными стилями для печати
        html = self.to_html(markdown_content, title)
        
        # Добавляем CSS для лучшей печати
        print_styles = """
        <style>
            @page {
                size: A4;
                margin: 2cm;
            }
            
            @media print {
                h1, h2, h3 {
                    page-break-after: avoid;
                }
                
                pre, table {
                    page-break-inside: avoid;
                }
                
                a {
                    color: #000;
                    text-decoration: none;
                }
            }
        </style>
        """
        
        # Вставляем перед закрывающим </head>
        html = html.replace('</head>', f'{print_styles}</head>')
        
        return html
    
    def export_all_formats(
        self,
        markdown_content: str,
        title: str = "Документация"
    ) -> Dict[str, str]:
        """
        Экспорт во все форматы
        """
        return {
            'markdown': markdown_content,
            'html': self.to_html(markdown_content, title),
            'pdf_html': self.to_pdf_html(markdown_content, title)
        }

