# Componentes externos

Este ZIP contém o código-fonte e um gerador de instalador, mas não incorpora os binários de Python, Qt, bibliotecas Python ou FFmpeg. Na compilação Windows, o PyInstaller e o Inno Setup incluem os componentes necessários no instalador resultante. Consulte também LICENCAS-E-DISTRIBUICAO.txt.

| Componente | Origem e informações de licença |
| --- | --- |
| Python | https://www.python.org/psf/license/ |
| PySide6 / Qt for Python / Shiboken | https://doc.qt.io/qtforpython-6/licenses.html — opções LGPL/GPL/comercial conforme os componentes |
| NumPy | https://numpy.org/doc/stable/license.html |
| Pillow | https://pillow.readthedocs.io/en/stable/about.html#license |
| Mutagen | https://mutagen.readthedocs.io/ — GPL |
| Windows Capture | https://pypi.org/project/windows-capture/ — MIT |
| SoundCard | https://pypi.org/project/SoundCard/ — BSD |
| OpenCV | https://opencv.org/license/ |
| CFFI | https://cffi.readthedocs.io/en/latest/ — MIT |
| FFmpeg | https://ffmpeg.org/legal.html — a licença depende da configuração da distribuição |
| FFmpeg Essentials / Gyan | https://www.gyan.dev/ffmpeg/builds/ — binários, informações e fontes da distribuição |
| pytest / Ruff, desenvolvimento | https://docs.pytest.org/ e https://docs.astral.sh/ruff/ |

Consulte os textos de licença distribuídos com cada dependência e suas dependências transitivas. O instalador de FFmpeg também registra a origem e o checksum em `tools/SOURCE.txt`.

Os mascotes foram gerados para este projeto. DuckCapture não é associado a Medal, Discord, Spotify, Minecraft ou fabricantes de GPU. Links do Spotify são abertos no serviço oficial; esta versão não utiliza credenciais ou API do Spotify.

Os sons `clip.wav` e `print.wav` são tons originais sintetizados para o DuckCapture, sem amostras de músicas ou bibliotecas externas.

- **Manrope**, por Mikhail Sharanda e colaboradores: [Google Fonts](https://github.com/google/fonts/tree/main/ofl/manrope), SIL Open Font License 1.1. Licença incluída em `duckcapture/assets/fonts/OFL-Manrope.txt`. As instâncias estáticas Regular, SemiBold, Bold e ExtraBold foram obtidas da fonte variável com fontTools 4.60.1 para compatibilidade consistente com Qt/Windows.
- **Python/WinRT** 3.2.1: https://github.com/pywinrt/pywinrt — MIT. Usado para controlar exclusivamente a sessão de mídia do aplicativo Spotify para Windows, sem senha ou token Spotify no DuckCapture.
- O novo `clip.wav` é sintetizado por `scripts/create_sounds.py`, com semente fixa e sem amostras externas.
