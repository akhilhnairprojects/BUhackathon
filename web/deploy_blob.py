"""Upload the web app's data and code to the Vercel Blob store that trip-risk-checker.vercel.app reads from.

    python web/deploy_blob.py            # uploads web/data/**/*.json, app.js and styles.css
    python web/deploy_blob.py --backup   # copies the current app.js and styles.css to backup/, the files
                                         # trip-risk-checker-simple.vercel.app reads (frozen on purpose)
Token: web/.blob_token (git-ignored) - the BLOB_READ_WRITE_TOKEN of the Vercel project.
After changing index.html, redeploy it through the Vercel dashboard or the API (see DEPLOY.md).
"""
import pathlib, concurrent.futures as cf, requests

ROOT = pathlib.Path(__file__).resolve().parent
TOKEN = (ROOT / ".blob_token").read_text().strip()
PREFIX = "trip-risk"


def put(rel: str, data: bytes, ctype: str, max_age: int):
    h = {"Authorization": f"Bearer {TOKEN}", "x-api-version": "7", "x-content-type": ctype,
         "x-add-random-suffix": "0", "x-cache-control-max-age": str(max_age), "x-allow-overwrite": "1"}
    r = requests.put(f"https://blob.vercel-storage.com/{PREFIX}/{rel}", data=data, headers=h, timeout=120)
    return rel, r.status_code


if __name__ == "__main__":
    import sys
    if "--backup" in sys.argv:
        jobs = [("backup/app.js", (ROOT / "app.js").read_bytes(), "text/javascript; charset=utf-8", 60),
                ("backup/styles.css", (ROOT / "styles.css").read_bytes(), "text/css; charset=utf-8", 60)]
        print([put(*j) for j in jobs]); sys.exit()
    jobs = [(f.relative_to(ROOT / "data").as_posix(), f.read_bytes(), "application/json", 3600) for f in (ROOT / "data").rglob("*.json")]
    jobs += [("app.js", (ROOT / "app.js").read_bytes(), "text/javascript; charset=utf-8", 60),
             ("styles.css", (ROOT / "styles.css").read_bytes(), "text/css; charset=utf-8", 60)]
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda j: put(*j), jobs))
    bad = [r for r in res if r[1] != 200]
    print(f"uploaded {len(res) - len(bad)} files; failed: {bad}")
