import asyncio
import email
import os
import uuid
from email import policy
from email.parser import BytesParser
from pathlib import Path
from app.core.paths import INBOX_DIR


class LocalSmtpServer:
    def __init__(self, host="127.0.0.1", port=0, inbox=INBOX_DIR):
        self.host = host
        self.port = port
        self.inbox = Path(inbox)
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.server = None

    async def start(self):
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        self.port = self.server.sockets[0].getsockname()[1]

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def _handle_client(self, reader, writer):
        writer.write(b"220 local-mail ESMTP\r\n")
        await writer.drain()
        data_mode = False
        message_lines = []
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip("\r\n")
                if data_mode:
                    if text == ".":
                        self._save_message(b"\r\n".join(message_lines) + b"\r\n")
                        data_mode = False
                        message_lines = []
                        writer.write(b"250 Message accepted\r\n")
                    else:
                        message_lines.append(line.rstrip(b"\r\n"))
                    await writer.drain()
                    continue
                command = text.upper()
                if command.startswith(("EHLO", "HELO")):
                    writer.write(b"250-local-mail\r\n250 SIZE 10485760\r\n")
                elif command.startswith("MAIL FROM") or command.startswith("RCPT TO"):
                    writer.write(b"250 OK\r\n")
                elif command == "DATA":
                    data_mode = True
                    writer.write(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                elif command == "QUIT":
                    writer.write(b"221 Bye\r\n")
                    await writer.drain()
                    break
                else:
                    writer.write(b"250 OK\r\n")
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    def _save_message(self, raw_message: bytes):
        self.save_message(raw_message)

    def save_message(self, raw_message: bytes):
        message_id = uuid.uuid4().hex
        path = self.inbox / f"{message_id}.eml"
        path.write_bytes(raw_message)
        message = BytesParser(policy=policy.default).parsebytes(raw_message)
        for part in message.walk():
            filename = part.get_filename()
            if filename:
                attachment_path = self.inbox / f"{message_id}_{Path(filename).name}"
                attachment_path.write_bytes(part.get_payload(decode=True) or b"")


local_smtp_server = LocalSmtpServer(
    host=os.getenv("LOCAL_SMTP_HOST", "127.0.0.1"),
    port=int(os.getenv("LOCAL_SMTP_PORT", "0")),
)
