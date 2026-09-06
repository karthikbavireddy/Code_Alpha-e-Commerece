import sys
import traceback
from django.http import HttpResponseServerError

class ExceptionLoggingMiddleware:
    """Catches any unhandled exceptions and prints/returns the exact diagnostic traceback."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        tb = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        print(f"VERCEL SERVER ERROR:\n{tb}", flush=True)
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Diagnostic Traceback - CodeAlpha</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace; background: #090d16; color: #f8fafc; padding: 2rem; margin: 0;">
          <div style="max-width: 900px; margin: 0 auto; background: #111827; border: 1px solid #ef4444; border-radius: 12px; padding: 2rem; box-shadow: 0 10px 40px rgba(0,0,0,0.5);">
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
              <span style="background: #ef4444; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; font-size: 12px;">500 EXCEPTION</span>
              <h2 style="color: #f8fafc; margin: 0; font-size: 1.3rem;">Server Error Diagnostic</h2>
            </div>
            <p style="color: #94a3b8; font-size: 14px; margin-bottom: 1.5rem;">The server encountered an exception during request execution:</p>
            <div style="background: #030712; padding: 1.25rem; border-radius: 8px; border: 1px solid #374151; overflow-x: auto;">
              <div style="color: #f87171; font-weight: 700; font-size: 15px; margin-bottom: 0.75rem;">{type(exception).__name__}: {exception}</div>
              <pre style="color: #cbd5e1; margin: 0; font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word;">{tb}</pre>
            </div>
          </div>
        </body>
        </html>
        """
        return HttpResponseServerError(html)
