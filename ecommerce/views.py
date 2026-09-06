import sys
import traceback
from django.http import HttpResponseServerError

def handler500(request):
    exc_type, exc_value, exc_tb = sys.exc_info()
    if exc_value:
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    else:
        error_msg = "No exception active in sys.exc_info()."
    
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>500 Diagnostic - CodeAlpha</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace; background: #090d16; color: #f8fafc; padding: 2rem; margin: 0;">
  <div style="max-width: 900px; margin: 0 auto; background: #111827; border: 1px solid #ef4444; border-radius: 12px; padding: 2rem;">
    <h2 style="color: #ef4444; margin-top: 0;">Server Error (500) Traceback</h2>
    <div style="background: #030712; padding: 1.25rem; border-radius: 8px; border: 1px solid #374151; overflow-x: auto;">
      <pre style="color: #fca5a5; margin: 0; font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word;">{error_msg}</pre>
    </div>
  </div>
</body>
</html>"""
    return HttpResponseServerError(html)
