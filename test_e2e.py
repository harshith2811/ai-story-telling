"""StoryForge AI - Full E2E Pipeline Test
Generates a story, images, voice, and renders a final MP4 video.
"""
import urllib.request
import json
import time
import sys

BASE = "http://127.0.0.1:8000"

def api_get(path):
    resp = urllib.request.urlopen(f"{BASE}{path}", timeout=60)
    return json.loads(resp.read())

def api_post(path, data=None):
    payload = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}", data=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=300)
    return json.loads(resp.read())

def main():
    print("=" * 60)
    print("  StoryForge AI — Full End-to-End Pipeline Test")
    print("=" * 60)

    # 0. Check all routes
    openapi = api_get("/openapi.json")
    routes = sorted(openapi["paths"].keys())
    print(f"\n[ROUTES] {len(routes)} endpoints registered:")
    for r in routes:
        if r.startswith("/api"):
            print(f"  {r}")

    # 1. Health
    health = api_get("/health")
    print(f"\n[1/7] Health: {health['status']}")

    # 2. Diagnostics
    diag = api_get("/api/v1/system/diagnostics")
    print("[2/7] Services:")
    for svc, info in diag["services"].items():
        print(f"  {svc}: {info.get('status', '?')}")

    # 3. Generate story
    print("\n[3/7] Generating story...")
    project = api_post("/api/v1/stories/generate", {
        "topic": "A girl who taught herself to code and built an app that saved her village",
        "category": "inspirational",
        "language": "English",
        "duration": 60,
        "emotional_tone": "determination",
        "audience": "general",
        "visual_style": "cinematic",
    })
    pid = project["id"]
    print(f"  Project ID: {pid}")
    print(f"  Title: {project['title']}")
    print(f"  Scenes: {len(project.get('scenes', []))}")
    for sc in project.get("scenes", []):
        narr = sc["narration"][:70]
        print(f"    Scene {sc['scene_number']}: {narr}...")

    # Parse story quality
    sj = project.get("story_json")
    if sj:
        sd = json.loads(sj) if isinstance(sj, str) else sj
        print(f"  Hook: {sd.get('hook', 'N/A')[:80]}")
        print(f"  Quality: {sd.get('quality_audit', {}).get('quality_score', 'N/A')}/100")

    # 4. Generate images
    print(f"\n[4/7] Generating scene images for project {pid}...")
    try:
        img_resp = api_post(f"/api/v1/images/generate-all/{pid}", {})
        updated = img_resp.get("updated_scenes", img_resp)
        if isinstance(updated, list):
            for s in updated:
                print(f"    Scene {s.get('scene_number','?')}: {s.get('image_path','pending')}")
        else:
            print(f"    Response: {str(img_resp)[:200]}")
    except Exception as e:
        print(f"  [WARN] {e}")

    # 5. Voice synthesis
    print(f"\n[5/7] Synthesizing voice narration...")
    try:
        voice_resp = api_post("/api/v1/audio/synthesize-all", {
            "project_id": pid,
            "voice_id": "en-US-GuyNeural",
            "speed": 1.0
        })
        print(f"    Voice: {voice_resp.get('message', voice_resp.get('status', str(voice_resp)[:100]))}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  [WARN] {e.code}: {body[:200]}")
    except Exception as e:
        print(f"  [WARN] {e}")

    # 6. Render video
    print(f"\n[6/7] Rendering 1080x1920 MP4...")
    try:
        render_resp = api_post("/api/v1/renders/start", {
            "project_id": pid,
            "resolution": "1080x1920",
            "fps": 30,
            "format": "mp4",
        })
        print(f"    Render response: {str(render_resp)[:200]}")

        # If background render, poll
        rid = render_resp.get("render_id") or render_resp.get("id")
        if rid:
            for i in range(90):
                time.sleep(3)
                try:
                    st = api_get(f"/api/v1/renders/status/{rid}")
                    status = st.get("status", "unknown")
                    sys.stdout.write(f"\r    Status: {status} ({i*3}s elapsed)   ")
                    sys.stdout.flush()
                    if status in ("completed", "failed"):
                        print()
                        if status == "completed":
                            print(f"    [OK] Video: {st.get('output_path', 'N/A')}")
                        else:
                            print(f"    [FAIL] {st.get('error_message', '?')}")
                        break
                except Exception:
                    pass
            print()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  [WARN] {e.code}: {body[:300]}")
    except Exception as e:
        print(f"  [WARN] {e}")

    # 7. List projects
    print(f"\n[7/7] All projects:")
    projects = api_get("/api/v1/projects/")
    items = projects if isinstance(projects, list) else projects.get("items", [])
    for p in items[-5:]:
        print(f"    #{p['id']} {p['title'][:50]} [{p['status']}]")

    print("\n" + "=" * 60)
    print("  Dashboard:  http://127.0.0.1:8000/")
    print("  API Docs:   http://127.0.0.1:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    main()
