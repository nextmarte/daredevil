#!/usr/bin/env python3
"""
Mock da API Remota de Conversão para Testes Locais

Este script simula a API remota (192.168.1.29:8591) localmente
para testar o fluxo assíncrono completo sem depender da máquina remota.

Uso:
    python test_remote_api_mock.py

Isso inicia um servidor mock na porta 8592.
Depois configure REMOTE_CONVERTER_URL=http://localhost:8592 e teste.
"""

import json
import time
import uuid
import os
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Simulação de fila de conversão
conversion_jobs = {}

class MockConverterHandler(BaseHTTPRequestHandler):
    """Handler para simular API remota de conversão"""

    def do_POST(self):
        """POST /convert-async - Enfileira conversão"""
        path = urlparse(self.path).path
        
        if path == "/convert-async":
            self.handle_convert_async()
        elif path == "/health":
            self.handle_health()
        else:
            self.send_error(404, "Not found")

    def do_GET(self):
        """GET endpoints"""
        path = urlparse(self.path).path
        
        if path.startswith("/convert-status/"):
            job_id = path.split("/")[-1]
            self.handle_status(job_id)
        elif path.startswith("/convert-download/"):
            job_id = path.split("/")[-1]
            self.handle_download(job_id)
        elif path == "/health":
            self.handle_health()
        else:
            self.send_error(404, "Not found")

    def handle_convert_async(self):
        """Simula conversão assíncrona (enfileira)"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        # Simula processamento rápido (em background)
        job_id = str(uuid.uuid4())
        conversion_jobs[job_id] = {
            "status": "processing",
            "progress": 0,
            "created_at": time.time(),
            "output_file": f"/tmp/converted_{job_id}.wav"
        }
        
        # Simula criação de arquivo convertido (em 1 segundo)
        def simulate_conversion():
            time.sleep(1)
            # Cria arquivo WAV vazio (fake)
            Path(conversion_jobs[job_id]["output_file"]).touch()
            conversion_jobs[job_id]["status"] = "completed"
            conversion_jobs[job_id]["progress"] = 100
        
        thread = threading.Thread(target=simulate_conversion, daemon=True)
        thread.start()
        
        response = {
            "success": True,
            "job_id": job_id,
            "status": "queued",
            "message": "Conversion queued successfully"
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
        
        print(f"✅ Conversão enfileirada: {job_id}")

    def handle_status(self, job_id):
        """Simula consulta de status"""
        if job_id not in conversion_jobs:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": "Job not found"
            }).encode())
            return
        
        job = conversion_jobs[job_id]
        response = {
            "success": True,
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "queue_position": 0
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
        
        print(f"📊 Status consultado: {job_id} - {job['status']} ({job['progress']}%)")

    def handle_download(self, job_id):
        """Simula download do arquivo convertido"""
        if job_id not in conversion_jobs:
            self.send_response(404)
            self.end_headers()
            return
        
        job = conversion_jobs[job_id]
        output_file = job["output_file"]
        
        if not os.path.exists(output_file):
            self.send_response(404)
            self.end_headers()
            return
        
        # Retorna arquivo vazio (simulação)
        with open(output_file, 'rb') as f:
            content = f.read()
        
        self.send_response(200)
        self.send_header('Content-Type', 'audio/wav')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)
        
        print(f"📥 Download completo: {job_id}")
        
        # Limpa após download
        os.remove(output_file)
        del conversion_jobs[job_id]

    def handle_health(self):
        """Health check"""
        response = {
            "status": "healthy",
            "api_version": "1.0",
            "queue_size": len(conversion_jobs),
            "active_jobs": sum(1 for j in conversion_jobs.values() if j["status"] == "processing")
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        """Suprime logs padrão do servidor"""
        return


def main():
    print("🚀 Iniciando Mock da API Remota")
    print("=" * 60)
    print()
    print("Endpoints disponíveis:")
    print("  POST   /convert-async           - Enfileira conversão")
    print("  GET    /convert-status/{job_id} - Consulta status")
    print("  GET    /convert-download/{job_id} - Download resultado")
    print("  GET    /health                 - Health check")
    print()
    print("=" * 60)
    print()
    print("Para testar com Daredevil:")
    print()
    print("1. Configure a variável de ambiente:")
    print("   export REMOTE_CONVERTER_URL=http://localhost:8592")
    print()
    print("2. Reinicie os containers:")
    print("   docker compose down && docker compose up -d")
    print()
    print("3. Teste o upload:")
    print("   curl -X POST -F 'file=@whatsapp.ogg' \\")
    print("     http://localhost:8511/api/transcribe/async")
    print()
    print("=" * 60)
    print()
    
    server = HTTPServer(("127.0.0.1", 8592), MockConverterHandler)
    print(f"✅ Mock API ouvindo em http://127.0.0.1:8592")
    print()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏹️  Servidor finalizado")
        server.server_close()


if __name__ == "__main__":
    main()
