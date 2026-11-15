# StoryForge AI — Troubleshooting & Diagnostics Guide

This document outlines common setup edge cases on Windows and their immediate resolutions.

---

## 1. Windows SSL Certificate Verification (`SSLCertVerificationError`)

### Symptom:
```
ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

### Cause:
Standalone Python distributions on Windows (e.g. from `uv` or portable zips) may not automatically import Windows Root CA certificates into Python's `ssl` context.

### Solution:
StoryForge AI automatically invokes `truststore.inject_into_ssl()` at startup in `voice_service.py` and `provider.py`. Ensure `truststore` is installed in your virtual environment:
```powershell
pip install truststore
```

---

## 2. FFmpeg Execution & PATH Detection

### Symptom:
`FFmpeg was not found in PATH` or `ffprobe: The term 'ffprobe' is not recognized`.

### Solution:
1. Verify FFmpeg is installed by running:
   ```powershell
   ffmpeg -version
   ```
2. If installed in a custom directory (e.g., `C:\Users\<user>\tools\ffmpeg\bin`), add it to your user PATH:
   ```powershell
   $ffmpegBin = "C:\Users\$env:USERNAME\tools\ffmpeg\extracted\ffmpeg-master-latest-win64-gpl\bin"
   [Environment]::SetEnvironmentVariable("PATH", "$ffmpegBin;$([Environment]::GetEnvironmentVariable('PATH', 'User'))", "User")
   ```
3. Restart your PowerShell terminal.

---

## 3. SQLAlchemy Asyncio `greenlet` Missing

### Symptom:
```
ImportError: The SQLAlchemy asyncio module requires that the Python 'greenlet' library is installed.
```

### Solution:
SQLite asyncio in SQLAlchemy requires the C-extension `greenlet`:
```powershell
pip install greenlet
```

---

## 4. Hardware Memory Limits (4GB VRAM on RTX 3050)

### Guidance:
- **Local LLMs:** Use quantized GGUF/AWQ models (e.g., `llama3.2:3b-instruct-q4_K_M` or `phi3:mini`) which take < 2.2GB VRAM.
- **Image Generation:** If running ComfyUI, start it with `python main.py --lowvram --fp16`.
- **Zero-GPU Fallback:** When no GPU is present or VRAM is exhausted, StoryForge AI seamlessly switches to its built-in procedural canvas compositor with atmospheric lighting, silhouettes, and Ken Burns motion. Video rendering will never fail!

---

## 5. Telugu Unicode Rendering in PowerShell & Subtitles

### Symptom:
PowerShell displays `???` or throws `UnicodeEncodeError: 'charmap' codec can't encode characters` when printing Telugu script.

### Solution:
Set PowerShell encoding to UTF-8:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
```
In video subtitles, StoryForge AI uses the `Nirmala UI` font (standard in Windows 10 and 11), ensuring 100% correct Telugu and Devanagari ligatures.

---

## 6. YouTube API Quotas and Approval Gate

### Note:
StoryForge AI strictly enforces an **approval gate** before publishing videos to YouTube. The application will never post without explicit confirmation. If YouTube API credentials (`YOUTUBE_CLIENT_ID`) are omitted in `.env`, the system automatically outputs a ready-to-publish MP4 file and formatted metadata bundle (`title`, `description`, `tags`) for manual upload.
