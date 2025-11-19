"""
Gerenciador de fontes para PDF-CLI.

Este módulo é responsável por:
- Detectar fontes ausentes ou variantes não encontradas
- Notificar o usuário sobre fontes necessárias
- Sugerir downloads e instalação de fontes
- Validar disponibilidade de fontes antes de edição
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum


class FontMatchQuality(Enum):
    """Qualidade da correspondência de fonte encontrada."""
    EXACT = "exact"  # Fonte exata encontrada
    SIMILAR = "similar"  # Fonte similar encontrada (ex: Arial → Helvetica)
    VARIANT = "variant"  # Variante encontrada (ex: ArialNarrow → ArialNarrow7)
    FALLBACK = "fallback"  # Fallback genérico (ex: qualquer → Helvetica)
    MISSING = "missing"  # Fonte não encontrada


@dataclass
class FontRequirement:
    """Requisito de fonte para edição de PDF."""

    font_name: str
    """Nome da fonte original no PDF"""

    variant: Optional[str] = None
    """Variante específica (Bold, Italic, Narrow, etc.)"""

    match_quality: FontMatchQuality = FontMatchQuality.MISSING
    """Qualidade da correspondência encontrada"""

    found_font: Optional[str] = None
    """Nome da fonte encontrada (se houver)"""

    system_path: Optional[str] = None
    """Caminho da fonte no sistema (se encontrada)"""

    download_url: Optional[str] = None
    """URL sugerida para download da fonte"""

    installation_instructions: Optional[str] = None
    """Instruções de instalação da fonte"""

    occurrences: int = 1
    """Número de ocorrências desta fonte no documento"""

    pages: List[int] = None
    """Páginas onde a fonte é usada"""

    def __post_init__(self):
        if self.pages is None:
            self.pages = []

    def is_acceptable(self) -> bool:
        """
        Verifica se a fonte encontrada é aceitável.

        Returns:
            bool: True se a correspondência é exata
        """
        return self.match_quality == FontMatchQuality.EXACT

    def needs_installation(self) -> bool:
        """
        Verifica se a fonte precisa ser instalada ou tem problemas.

        Returns:
            bool: True se a fonte não foi encontrada, é fallback ou é variante
        """
        return self.match_quality in [FontMatchQuality.MISSING, FontMatchQuality.FALLBACK, FontMatchQuality.VARIANT]

    def to_dict(self) -> Dict:
        """Converte para dicionário para logging."""
        return {
            "font_name": self.font_name,
            "variant": self.variant,
            "match_quality": self.match_quality.value,
            "found_font": self.found_font,
            "system_path": self.system_path,
            "occurrences": self.occurrences,
            "pages": self.pages,
            "needs_installation": self.needs_installation()
        }


class FontManager:
    """Gerenciador de fontes para operações de PDF."""

    # Mapeamento de fontes comuns para URLs de download
    FONT_DOWNLOAD_URLS = {
        "Arial": "https://docs.microsoft.com/typography/font-list/arial",
        "ArialMT": "https://docs.microsoft.com/typography/font-list/arial",
        "ArialNarrow": "https://docs.microsoft.com/typography/font-list/arial-narrow",
        "ArialNarrow-Bold": "https://docs.microsoft.com/typography/font-list/arial-narrow",
        "Times": "https://docs.microsoft.com/typography/font-list/times-new-roman",
        "TimesNewRoman": "https://docs.microsoft.com/typography/font-list/times-new-roman",
        "Courier": "https://docs.microsoft.com/typography/font-list/courier-new",
        "CourierNew": "https://docs.microsoft.com/typography/font-list/courier-new",
    }

    # Instruções de instalação por sistema operacional
    INSTALLATION_INSTRUCTIONS = {
        "Windows": "1. Baixe o arquivo de fonte (.ttf ou .otf)\n"
                  "2. Clique com botão direito no arquivo\n"
                  "3. Selecione 'Instalar' ou 'Instalar para todos os usuários'\n"
                  "4. Reinicie o PDF-CLI após instalação",

        "Linux": "1. Baixe o arquivo de fonte (.ttf ou .otf)\n"
                "2. Copie para ~/.fonts/ ou /usr/share/fonts/\n"
                "3. Execute: fc-cache -f -v\n"
                "4. Reinicie o PDF-CLI após instalação",

        "Darwin": "1. Baixe o arquivo de fonte (.ttf ou .otf)\n"
                 "2. Abra o Font Book\n"
                 "3. Arraste o arquivo para Font Book ou use 'Arquivo > Adicionar Fontes'\n"
                 "4. Reinicie o PDF-CLI após instalação"
    }

    def __init__(self):
        self.requirements: List[FontRequirement] = []
        self.missing_fonts: List[FontRequirement] = []
        self.warnings: List[str] = []

    def add_requirement(
        self,
        font_name: str,
        found_font: Optional[str],
        match_quality: FontMatchQuality,
        system_path: Optional[str] = None,
        page: Optional[int] = None
    ) -> FontRequirement:
        """
        Adiciona um requisito de fonte.

        Args:
            font_name: Nome da fonte original
            found_font: Nome da fonte encontrada (se houver)
            match_quality: Qualidade da correspondência
            system_path: Caminho da fonte no sistema
            page: Página onde a fonte é usada

        Returns:
            FontRequirement: Requisito criado ou atualizado
        """
        # Verificar se já existe requisito para esta fonte
        existing = None
        for req in self.requirements:
            if req.font_name == font_name:
                existing = req
                break

        if existing:
            # Atualizar requisito existente
            existing.occurrences += 1
            if page is not None and page not in existing.pages:
                existing.pages.append(page)
            return existing

        # Criar novo requisito
        req = FontRequirement(
            font_name=font_name,
            variant=self._extract_variant(font_name),
            match_quality=match_quality,
            found_font=found_font,
            system_path=system_path,
            download_url=self._get_download_url(font_name),
            installation_instructions=self._get_installation_instructions(),
            pages=[page] if page is not None else []
        )

        self.requirements.append(req)

        # Adicionar à lista de fontes faltantes se necessário
        if req.needs_installation():
            self.missing_fonts.append(req)

        return req

    def _extract_variant(self, font_name: str) -> Optional[str]:
        """Extrai a variante da fonte do nome."""
        variants = []
        name_upper = font_name.upper()

        if "BOLD" in name_upper:
            variants.append("Bold")
        if "ITALIC" in name_upper or "OBLIQUE" in name_upper:
            variants.append("Italic")
        if "NARROW" in name_upper:
            variants.append("Narrow")
        if "CONDENSED" in name_upper:
            variants.append("Condensed")
        if "LIGHT" in name_upper:
            variants.append("Light")
        if "BLACK" in name_upper:
            variants.append("Black")

        return " ".join(variants) if variants else None

    def _get_download_url(self, font_name: str) -> Optional[str]:
        """Obtém URL de download para a fonte."""
        # Tentar correspondência exata
        if font_name in self.FONT_DOWNLOAD_URLS:
            return self.FONT_DOWNLOAD_URLS[font_name]

        # Tentar correspondência por família
        for key, url in self.FONT_DOWNLOAD_URLS.items():
            if key.lower() in font_name.lower() or font_name.lower() in key.lower():
                return url

        # URL genérica para busca
        return f"https://www.google.com/search?q=download+{font_name.replace(' ', '+')}+font"

    def _get_installation_instructions(self) -> str:
        """Obtém instruções de instalação para o sistema operacional atual."""
        import platform
        system = platform.system()
        return self.INSTALLATION_INSTRUCTIONS.get(system, self.INSTALLATION_INSTRUCTIONS["Windows"])

    def has_missing_fonts(self) -> bool:
        """Verifica se há fontes faltantes."""
        return len(self.missing_fonts) > 0

    def get_missing_fonts_summary(self) -> str:
        """
        Gera um resumo das fontes faltantes para exibir ao usuário.

        Returns:
            str: Resumo formatado das fontes faltantes
        """
        if not self.has_missing_fonts():
            return "✅ Todas as fontes necessárias estão disponíveis."

        lines = []
        lines.append("\n" + "="*80)
        lines.append("⚠️  ATENÇÃO: FONTES FALTANTES DETECTADAS")
        lines.append("="*80)
        lines.append("")
        lines.append(f"O PDF-CLI detectou {len(self.missing_fonts)} fonte(s) que não puderam ser")
        lines.append("preservadas perfeitamente devido à ausência no sistema.")
        lines.append("")

        for i, req in enumerate(self.missing_fonts, 1):
            lines.append(f"{i}. Fonte: {req.font_name}")
            if req.variant:
                lines.append(f"   Variante: {req.variant}")
            lines.append(f"   Usada em: {req.occurrences} ocorrência(s)")
            lines.append(f"   Páginas: {', '.join(map(str, sorted(req.pages)))}")

            if req.found_font:
                lines.append(f"   ⚠️  Usando fallback: {req.found_font}")
            else:
                lines.append(f"   ❌ Nenhuma fonte similar encontrada")

            lines.append("")
            lines.append(f"   📥 Para instalar esta fonte:")
            if req.download_url:
                lines.append(f"      Download: {req.download_url}")
            lines.append("")
            if req.installation_instructions:
                for line in req.installation_instructions.split('\n'):
                    lines.append(f"      {line}")
            lines.append("")
            lines.append("-" * 80)
            lines.append("")

        lines.append("💡 RECOMENDAÇÃO:")
        lines.append("   Instale as fontes listadas acima e execute o comando novamente")
        lines.append("   para garantir preservação perfeita das fontes originais.")
        lines.append("")
        lines.append("="*80)

        return "\n".join(lines)

    def get_summary_dict(self) -> Dict:
        """
        Gera um dicionário com resumo das fontes para logging.

        Returns:
            Dict: Resumo das fontes
        """
        return {
            "total_fonts": len(self.requirements),
            "missing_fonts": len(self.missing_fonts),
            "fonts": [req.to_dict() for req in self.requirements],
            "has_issues": self.has_missing_fonts()
        }

    def should_block_operation(self, strict_mode: bool = False) -> bool:
        """
        Verifica se a operação deve ser bloqueada devido a fontes faltantes.

        Args:
            strict_mode: Se True, bloqueia operação se qualquer fonte não for exata

        Returns:
            bool: True se operação deve ser bloqueada
        """
        if not strict_mode:
            return False

        # Em modo strict, bloquear se houver qualquer fonte que não seja exata
        for req in self.requirements:
            if req.match_quality != FontMatchQuality.EXACT:
                return True

        return False
