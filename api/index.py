import os
import sys
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs

# Legg til prosjektets rotmappe i Python-stien
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer din AI-klasse fra ai_engine.py
from src.ai_engine import RailAdviceAI

# Initialiser AI-en. Dette vil kjøre kun én gang per "cold start".
ai_instance = RailAdviceAI()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data.decode('utf-8'))
            question = body.get("question", "")
            
            if not question:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Spørsmål mangler i forespørsel"}).encode('utf-8'))
                return

            response = ai_instance.query(question)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
        
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def do_GET(self):
        # En enkel GET-forespørsel for å sjekke om API-et fungerer
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("RailAdvice AI API er i gang!".encode('utf-8'))