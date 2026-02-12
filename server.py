import http.server
import socketserver
import sqlite3
import json
import urllib.parse
import os

PORT = 8001
DB_FILE = "cables.db"

class CableRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # CORS Header
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        
        # API Endpoint for search
        if path == "/api/search":
            query_params = urllib.parse.parse_qs(parsed_path.query)
            search_query = query_params.get("q", [""])[0]
            print(f"Received search query: '{search_query}'")
            
            if len(search_query) < 2:
                print("Query too short, returning empty.")
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps([]).encode('utf-8'))
                return

            try:
                conn = sqlite3.connect(DB_FILE)
                
                # Register custom function for case-insensitive search (Cyrillic support)
                conn.create_function("lower_str", 1, lambda s: s.lower() if s else "")

                cursor = conn.cursor()
                
                # Search using custom lower function
                sql = "SELECT name, weight_kg_km, diameter_mm, drums FROM cables WHERE lower_str(name) LIKE ? LIMIT 50"
                cursor.execute(sql, ('%' + search_query.lower() + '%',))
                rows = cursor.fetchall()
                print(f"Found {len(rows)} results for '{search_query}'")
                
                results = []
                for row in rows:
                    results.append({
                        "name": row[0],
                        "weight_kg_km": row[1],
                        "diameter_mm": row[2],
                        "drums": row[3].split(",") if row[3] else []
                    })
                
                conn.close()
                
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(results).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                print(f"Database error: {e}")
                
        else:
            # Serve static files (index.html, etc.)
            super().do_GET()

print(f"Starting server at http://localhost:{PORT}")
print("Press Ctrl+C to stop.")

# Allow address reuse to avoid "Address already in use" errors during restarts
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer(("", PORT), CableRequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
