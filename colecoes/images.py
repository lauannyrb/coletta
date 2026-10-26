"""Processamento seguro das capas das coleções (RN24)."""
from io import BytesIO
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 2 * 1024 * 1024        # 2 MB
MAX_PIXELS = 25_000_000                   # ex.: 5000 x 5000; evita "bombas" de descompressão
MAX_SIDE = 1600                           # lado maior da imagem salva
ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}  # identificados pelo conteúdo, não pela extensão

INVALID_MESSAGE = 'Envie uma imagem JPG, PNG ou WEBP válida.'


def process_cover(uploaded):
    """Valida a imagem enviada e devolve uma cópia nova em WEBP com nome aleatório.

    Regravar a imagem descarta metadados (EXIF, incluindo localização GPS) e qualquer conteúdo
    que não seja a própria imagem, como scripts escondidos em arquivos "poliglotas".
    """
    if uploaded.size > MAX_UPLOAD_BYTES:
        raise ValidationError('A imagem deve ter no máximo 2 MB.')

    try:
        # `formats` limita os parsers usados para identificar o arquivo: GIF, TIFF, PDF, XBM etc.
        # nem chegam a ser lidos (seus parsers já tiveram falhas de segurança exploráveis no open).
        # Image.open só lê o cabeçalho: dimensões são conferidas antes de decodificar.
        with Image.open(uploaded, formats=sorted(ALLOWED_FORMATS)) as image:
            if image.width * image.height > MAX_PIXELS:
                raise ValidationError('A imagem tem dimensões grandes demais.')

            image.load()  # decodifica de fato: arquivo corrompido ou falso falha aqui
            image = ImageOps.exif_transpose(image)  # mantém a orientação de fotos de celular
            image.thumbnail((MAX_SIDE, MAX_SIDE))
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGBA' if 'A' in image.getbands() else 'RGB')

            output = BytesIO()
            image.save(output, format='WEBP', quality=82)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValidationError(INVALID_MESSAGE)

    return ContentFile(output.getvalue(), name=f'{uuid4().hex}.webp')
