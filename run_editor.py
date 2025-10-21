#!/usr/bin/env python3
"""
Simple web server to run the JSON Diarization Editor.

Usage:
    python run_editor.py [port]

Default port is 8000.
"""

import http.server
import socketserver
import sys
import os
import webbrowser
from pathlib import Path


def run_server(port=8000):
    """Run a simple HTTP server to serve the diarization editor."""

    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)

    # Check if the HTML file exists
    html_file = script_dir / 'diarization_editor.html'
    if not html_file.exists():
        print(f"Error: diarization_editor.html not found in {script_dir}")
        sys.exit(1)

    # Create server
    Handler = http.server.SimpleHTTPRequestHandler

    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            url = f"http://localhost:{port}/diarization_editor.html"
            print("=" * 60)
            print("JSON Diarization Editor Server")
            print("=" * 60)
            print(f"Server running at: {url}")
            print("\nPress Ctrl+C to stop the server")
            print("=" * 60)

            # Open browser automatically
            try:
                webbrowser.open(url)
                print("\nOpening browser automatically...")
            except Exception as e:
                print(f"\nCouldn't open browser automatically: {e}")
                print(f"Please open {url} manually in your browser.")

            # Serve forever
            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\nError: Port {port} is already in use.")
            print(f"Try a different port: python {sys.argv[0]} <port>")
            sys.exit(1)
        else:
            raise


if __name__ == "__main__":
    # Get port from command line argument, default to 8000
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if port < 1 or port > 65535:
                raise ValueError
        except ValueError:
            print("Error: Port must be a number between 1 and 65535")
            print(f"Usage: python {sys.argv[0]} [port]")
            sys.exit(1)

    run_server(port)
