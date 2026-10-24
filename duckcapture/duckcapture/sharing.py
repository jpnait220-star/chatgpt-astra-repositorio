"""Explicit, asynchronous uploads to Catbox. No background/automatic publishing."""
import json
import re
from pathlib import Path
from PySide6.QtCore import QFile, QIODevice, QTimer, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QHttpMultiPart, QHttpPart
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QProgressBar
from .config import data_dir, atomic_json
from .widgets import label, button
from .media_jobs import MediaJob

MAX_UPLOAD = 200_000_000  # Conservative decimal MB; provider's per-file limit.
UPLOAD_URL = 'https://catbox.moe/user/api.php'


def valid_clip_url(value):
    return bool(re.fullmatch(r'https://files\.catbox\.moe/[a-zA-Z0-9]+\.mp4', value))


def clip_signature(path):
    info = path.stat()
    return f'{path.resolve()}|{info.st_size}|{info.st_mtime_ns}'


class ShareDialog(QDialog):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.signature = clip_signature(self.path)
        self.setWindowTitle('Criar link do clipe')
        self.resize(580, 370)
        self.network = QNetworkAccessManager(self)
        self.reply = None
        self.preparing = None
        self.prepared = None
        self.closing_result = None
        self.timed_out = False
        self.idle = QTimer(self)
        self.idle.setSingleShot(True)
        self.idle.setInterval(90_000)
        self.idle.timeout.connect(self.timeout)
        self.deadline = QTimer(self)
        self.deadline.setSingleShot(True)
        self.deadline.setInterval(20 * 60_000)
        self.deadline.timeout.connect(self.timeout)
        body = QVBoxLayout(self)
        body.setContentsMargins(26, 24, 26, 24)
        body.setSpacing(15)
        body.addWidget(label('Compartilhe seu momento.', 'subheading'))
        body.addWidget(label(f'{self.path.name} · {self.path.stat().st_size / 1_000_000:.1f} MB', 'muted', True))
        body.addWidget(label('Ao enviar, o clipe ficará público no Catbox, um serviço externo. Qualquer pessoa com o link poderá assistir ou baixar. Limite: 200 MB por arquivo. Não envie conteúdo privado.', 'muted', True))
        body.addWidget(label('O link abre o MP4 no navegador. O Discord pode exibir o vídeo, conforme os limites e as configurações dele. Envio anônimo: o DuckCapture não oferece exclusão remota nem garante a permanência do arquivo.', 'tiny', True))
        body.addWidget(label('Clipes acima de 200 MB ganham uma cópia otimizada automaticamente, sem cortar o vídeo nem modificar o original. A preparação pode levar alguns minutos.', 'muted', True))
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        body.addWidget(self.progress)
        self.status = label('Seu arquivo só será enviado quando você clicar abaixo.', 'muted', True)
        body.addWidget(self.status)
        self.link = QLineEdit()
        self.link.setReadOnly(True)
        self.link.setPlaceholderText('O link aparecerá aqui após o envio')
        self.link.setAccessibleName('Link público do clipe')
        body.addWidget(self.link)
        actions = QHBoxLayout()
        self.send = button('Enviar e criar link', self.start, True)
        self.copy = button('Copiar link', self.copy_link)
        self.open = button('Abrir vídeo', self.open_link)
        self.copy.setEnabled(False)
        self.open.setEnabled(False)
        actions.addWidget(self.send)
        actions.addWidget(self.copy)
        actions.addWidget(self.open)
        body.addLayout(actions)
        self.cancel = button('Fechar', self.reject)
        body.addWidget(self.cancel)
        try:
            previous = json.loads((data_dir() / 'shared-clips.json').read_text(encoding='utf-8')).get(self.signature, '')
            if valid_clip_url(previous):
                self.show_link(previous)
                self.status.setText('Link criado anteriormente para este arquivo. A disponibilidade depende do Catbox.')
        except (OSError, ValueError, AttributeError):
            pass

    def start(self):
        if self.reply or self.preparing:
            return
        try:
            self.signature = clip_signature(self.path)
            size = self.path.stat().st_size
            if self.path.suffix.lower() != '.mp4':
                raise ValueError('Exporte o clipe em MP4 no editor antes de criar o link.')
            if size <= 0:
                raise ValueError('Este arquivo está vazio.')
            if size > MAX_UPLOAD and self.prepared is None:
                self.prepare_copy()
                return
            upload_path = self.prepared or self.path
            multipart = QHttpMultiPart(QHttpMultiPart.ContentType.FormDataType)
            request_type = QHttpPart()
            request_type.setHeader(QNetworkRequest.KnownHeaders.ContentDispositionHeader, 'form-data; name="reqtype"')
            request_type.setBody(b'fileupload')
            multipart.append(request_type)
            file = QFile(str(upload_path), multipart)
            if not file.open(QIODevice.OpenModeFlag.ReadOnly):
                multipart.deleteLater()
                raise OSError('Não foi possível ler este clipe.')
            part = QHttpPart()
            # Generic safe filename avoids leaking local names/paths in form fields.
            part.setHeader(QNetworkRequest.KnownHeaders.ContentDispositionHeader, 'form-data; name="fileToUpload"; filename="DuckCapture.mp4"')
            part.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, 'video/mp4')
            part.setBodyDevice(file)
            multipart.append(part)
            request = QNetworkRequest(QUrl(UPLOAD_URL))
            request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, 'DuckCapture/0.5.3')
            request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute, QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
            request.setTransferTimeout(90_000)
            self.reply = self.network.post(request, multipart)
            multipart.setParent(self.reply)
            self.reply.uploadProgress.connect(self.upload_progress)
            self.reply.finished.connect(self.finished_upload)
            self.timed_out = False
            self.idle.start()
            self.deadline.start()
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.send.setEnabled(False)
            self.cancel.setText('Cancelar envio')
            self.status.setText('Enviando ao Catbox…')
        except (OSError, ValueError) as error:
            self.status.setText(str(error))

    def prepare_copy(self):
        self.send.setEnabled(False)
        self.cancel.setText('Cancelar preparação')
        self.status.setText('Preparando cópia abaixo de 200 MB. O arquivo original será preservado…')
        self.progress.setValue(0)
        job = MediaJob(self.path, 'share', limit=MAX_UPLOAD, parent=self)
        self.preparing = job
        job.progress.connect(lambda value, message: (self.progress.setValue(value), self.status.setText(message)))
        job.failed.connect(self.preparation_error)
        job.finished.connect(self.preparation_finished)
        job.start()

    def preparation_error(self, message):
        self.status.setText('Não foi possível preparar o clipe: ' + message)

    def preparation_finished(self):
        job, self.preparing = self.preparing, None
        self.send.setEnabled(True)
        self.cancel.setText('Fechar')
        if self.closing_result is not None:
            result, self.closing_result = self.closing_result, None
            job.deleteLater()
            self.done(result)
            return
        if job.result and not job.cancelled.is_set():
            self.prepared = Path(job.result)
            job.deleteLater()
            self.start()
        else:
            job.deleteLater()

    def upload_progress(self, sent, total):
        if self.reply is None:
            return
        self.idle.start()
        if total > 0:
            self.progress.setValue(min(99, round(sent * 100 / total)))
            if sent >= total:
                self.status.setText('Arquivo enviado. Aguardando o link do Catbox…')

    def timeout(self):
        self.timed_out = True
        if self.reply:
            self.reply.abort()

    def finished_upload(self):
        reply, self.reply = self.reply, None
        self.idle.stop()
        self.deadline.stop()
        if reply is None:
            return
        self.send.setEnabled(True)
        self.cancel.setText('Fechar')
        value = bytes(reply.readAll()).decode('utf-8', 'replace').strip()
        code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if reply.error() == QNetworkReply.NetworkError.NoError and code == 200 and valid_clip_url(value):
            self.show_link(value)
            self.status.setText('Link público criado! Copie e cole onde quiser compartilhar.')
            try:
                target = data_dir() / 'shared-clips.json'
                try:
                    saved = json.loads(target.read_text(encoding='utf-8'))
                    if not isinstance(saved, dict):
                        saved = {}
                except (OSError, ValueError):
                    saved = {}
                saved[self.signature] = value
                atomic_json(target, saved)
            except OSError:
                self.status.setText('Link criado. Copie-o agora: não foi possível guardar o histórico local.')
        else:
            self.progress.setValue(0)
            self.status.setText('O Catbox demorou demais. Tente novamente.' if self.timed_out else f'Não foi possível criar o link (HTTP {code or "indisponível"}). Confira a conexão ou tente novamente mais tarde.')
        reply.deleteLater()

    def show_link(self, value):
        self.link.setText(value)
        self.progress.setValue(100)
        self.copy.setEnabled(True)
        self.open.setEnabled(True)
        self.send.setEnabled(False)

    def copy_link(self):
        if valid_clip_url(self.link.text()):
            QApplication.clipboard().setText(self.link.text())
            self.status.setText('Link copiado.')

    def open_link(self):
        if valid_clip_url(self.link.text()):
            QDesktopServices.openUrl(QUrl(self.link.text()))

    def done(self, result):
        if self.preparing:
            self.closing_result = result
            self.status.setText('Cancelando a preparação…')
            self.preparing.cancel()
            return
        self.idle.stop()
        self.deadline.stop()
        if self.reply:
            reply, self.reply = self.reply, None
            reply.finished.disconnect(self.finished_upload)
            reply.uploadProgress.disconnect(self.upload_progress)
            reply.abort()
            reply.deleteLater()
        super().done(result)
