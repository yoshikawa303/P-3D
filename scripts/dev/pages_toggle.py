#!/usr/bin/env python3
"""P-3D: GitHub Pages 一時公開の切替（Mac／Windows 共通、ワンクリック用）。

- リポジトリが Private のとき: Public へ変更 → Pages を `main` ルートで有効化 → ビルドを要求 →
  `main` の最新コミットが配信されるまで待ち → 配信URLの HTTP 200 を確認 → ブラウザで開く。
- リポジトリが Public のとき: Private へ戻す（Free プランでは Pages は自動停止し 404 になる）。

認証は環境変数 GITHUB_TOKEN、無ければ `gh auth token`（GitHub CLI のログイン）を使う。
ローカルの未push変更は配信されない（配信されるのは GitHub 上の `main`）。

使い方:
  python3 scripts/dev/pages_toggle.py            # 切替（Private→Public+配信 / Public→Private）
  python3 scripts/dev/pages_toggle.py --status   # 現在の状態を表示するだけ
  python3 scripts/dev/pages_toggle.py --dry-run  # 変更せずに実行予定の操作を表示
  python3 scripts/dev/pages_toggle.py --no-open  # 配信後にブラウザを開かない
"""
import argparse, json, os, shutil, subprocess, sys, time, urllib.error, urllib.request, webbrowser

OWNER, REPO = "yoshikawa303", "P-3D"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"
PAGES_URL = f"https://{OWNER}.github.io/{REPO}/"


def token():
    value = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if value:
        return value.strip()
    gh = shutil.which("gh")
    if gh:
        result = subprocess.run([gh, "auth", "token"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    sys.exit("GitHub の認証が見つかりません。`gh auth login` を実行するか、環境変数 GITHUB_TOKEN を設定してください。")


def api(method, path, body=None, allow404=False, tok=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": f"Bearer {tok}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "p3d-pages-toggle",
    })
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        if allow404 and error.code == 404:
            return None
        detail = error.read().decode(errors="replace")
        sys.exit(f"GitHub API エラー {error.code} ({method} {path}): {detail}")


def http_status(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "p3d-pages-toggle", "Cache-Control": "no-cache"}), timeout=30) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except Exception:
        return 0


def warn_local_changes():
    git = shutil.which("git")
    if not git:
        return
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    inside = subprocess.run([git, "-C", root, "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    if inside.returncode != 0:
        print("注意: このフォルダは Git checkout ではないため、配信されるのは GitHub 上の main です。")
        return
    status = subprocess.run([git, "-C", root, "status", "--short"], capture_output=True, text=True).stdout.strip()
    if status:
        print("注意: 未コミットの変更があります。配信されるのは push 済みの main だけです。")
    ahead = subprocess.run([git, "-C", root, "rev-list", "--count", "@{u}..HEAD"], capture_output=True, text=True)
    if ahead.returncode == 0 and ahead.stdout.strip() not in ("", "0"):
        print(f"注意: 未push のコミットが {ahead.stdout.strip()} 件あります。先に `git push` してください。")


def publish(tok, dry_run, open_browser, timeout):
    head = api("GET", "/commits/main", tok=tok)["sha"]
    print(f"配信対象: main @ {head[:7]}")
    warn_local_changes()
    if dry_run:
        print("[dry-run] Public へ変更 → Pages を main ルートで有効化 → ビルド要求 → 配信待ち → ブラウザで開く")
        return
    api("PATCH", "", {"private": False}, tok=tok)
    print("リポジトリを Public へ変更しました。")
    pages = api("GET", "/pages", allow404=True, tok=tok)
    source = {"branch": "main", "path": "/"}
    if pages is None:
        api("POST", "/pages", {"source": source, "build_type": "legacy"}, tok=tok)
        print("GitHub Pages を有効化しました（main ルート）。")
    elif (pages.get("source") or {}).get("branch") != "main" or (pages.get("source") or {}).get("path") != "/":
        api("PUT", "/pages", {"source": source, "build_type": "legacy"}, tok=tok)
        print("GitHub Pages の配信元を main ルートへ変更しました。")
    else:
        # 有効化直後は自動ビルドが走るため、要求は配信元が既に main のときだけ行う（二重要求は片方が取り消される）。
        try:
            api("POST", "/pages/builds", tok=tok)
            print("Pages のビルドを要求しました。")
        except SystemExit as error:
            print(f"ビルド要求は省略（自動ビルド待ち）: {error}")
    if wait_until_served(tok, head, timeout):
        print(f"配信完了: {PAGES_URL}  (main @ {head[:7]})")
        print("確認が終わったら、もう一度このバッチを実行すると Private に戻ります。")
        if open_browser:
            webbrowser.open(PAGES_URL)


def wait_until_served(tok, head, timeout):
    """main の HEAD がビルド済みで配信URLが 200 を返すまで待つ。

    Pages の有効化・push・ビルド要求が重なると GitHub 側で古いビルドが取り消され、
    `builds/latest` が一時的に errored（"Page build failed."）を返すことがある。
    そのため errored は即失敗にせず、同じ失敗ビルドが続いた場合だけ失敗とする。
    """
    print("配信完了を待っています", end="", flush=True)
    deadline = time.time() + timeout
    errored_since, errored_url = None, None
    while time.time() < deadline:
        time.sleep(6)
        build = api("GET", "/pages/builds/latest", allow404=True, tok=tok) or {}
        status, commit = build.get("status"), build.get("commit") or ""
        if status == "built" and commit == head and http_status(PAGES_URL) == 200:
            print()
            return True
        if status == "errored":
            if build.get("url") != errored_url:
                errored_since, errored_url = time.time(), build.get("url")
                print("!", end="", flush=True)
                try:
                    api("POST", "/pages/builds", tok=tok)
                except SystemExit:
                    pass
            elif time.time() - errored_since > 120:
                print(f"\nPages のビルドが失敗したままです: {(build.get('error') or {}).get('message')}")
                print("GitHub の Actions タブ（pages build and deployment）でログを確認してください。")
                return False
            continue
        errored_since, errored_url = None, None
        print(".", end="", flush=True)
    print()
    print(f"時間内に配信を確認できませんでした（{timeout}秒）。数分後に {PAGES_URL} を開いて確認してください。")
    return False


def unpublish(tok, dry_run):
    if dry_run:
        print("[dry-run] Private へ戻す（Pages は停止して 404 になる）")
        return
    api("PATCH", "", {"private": True}, tok=tok)
    print("リポジトリを Private へ戻しました。Pages は停止し、数分以内に 404 になります。")


def main():
    parser = argparse.ArgumentParser(description="GitHub Pages 一時公開の切替")
    parser.add_argument("--status", action="store_true", help="状態表示のみ")
    parser.add_argument("--dry-run", action="store_true", help="変更せず予定を表示")
    parser.add_argument("--no-open", action="store_true", help="配信後にブラウザを開かない")
    parser.add_argument("--timeout", type=int, default=600, help="配信待ちの上限秒（既定600）")
    parser.add_argument("--wait", action="store_true", help="切替せず、main の最新が配信されるまで待つだけ（Public のとき）")
    args = parser.parse_args()
    tok = token()
    repo = api("GET", "", tok=tok)
    private = bool(repo.get("private"))
    pages = api("GET", "/pages", allow404=True, tok=tok)
    served = http_status(PAGES_URL)
    note = "（CDNキャッシュの残り）" if not pages and served == 200 else ""
    print(f"{OWNER}/{REPO}: {'Private' if private else 'Public'} / Pages: {'有効 (' + (pages.get('html_url') or PAGES_URL) + ')' if pages else '無効'} / 配信URL HTTP {served}{note}")
    if args.status:
        return
    if args.wait:
        if private or not pages:
            sys.exit("Private または Pages 無効のため待機できません。切替（引数なし）で実行してください。")
        head = api("GET", "/commits/main", tok=tok)["sha"]
        print(f"配信対象: main @ {head[:7]}")
        if wait_until_served(tok, head, args.timeout):
            print(f"配信完了: {PAGES_URL}  (main @ {head[:7]})")
        return
    if private:
        publish(tok, args.dry_run, not args.no_open, args.timeout)
    else:
        unpublish(tok, args.dry_run)


if __name__ == "__main__":
    main()
