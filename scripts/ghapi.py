"""Tiny GitHub API helper (stdlib only). Reads GH_USER and GH_TOKEN from env."""
import json
import os
import ssl
import urllib.request

USER = os.environ.get("GH_USER", "ritujain8638-source")
TOKEN = os.environ.get("GH_TOKEN", "")
SSL_CTX = (ssl.create_default_context(cafile="/etc/ssl/cert.pem")
           if os.path.exists("/etc/ssl/cert.pem") else None)


def _req(url, data=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-gen"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=10, context=SSL_CTX) as resp:
        return json.load(resp)


def rest(path):
    return _req(path if path.startswith("http") else f"https://api.github.com{path}")


def gql(query, **variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    out = _req("https://api.github.com/graphql", body)
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]


def repos():
    out, page = [], 1
    while True:
        batch = rest(f"/users/{USER}/repos?per_page=100&type=owner&page={page}")
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def calendar():
    if TOKEN:
        q = """query($login:String!){user(login:$login){contributionsCollection{
          contributionCalendar{totalContributions weeks{contributionDays{
          date contributionCount weekday}}}}}}"""
        cal = gql(q, login=USER)["user"]["contributionsCollection"]["contributionCalendar"]
        return cal["totalContributions"], cal["weeks"]
    import datetime
    data = _req(f"https://github-contributions-api.jogruber.de/v4/{USER}?y=last")
    total = data.get("total", {}).get("lastYear", 0)
    weeks, cur_week = [], []
    for item in data.get("contributions", []):
        dt = datetime.date.fromisoformat(item["date"])
        wd = (dt.weekday() + 1) % 7  # Sunday = 0
        if wd == 0 and cur_week:
            weeks.append({"contributionDays": cur_week})
            cur_week = []
        cur_week.append({
            "date": item["date"],
            "contributionCount": item["count"],
            "weekday": wd,
        })
    if cur_week:
        weeks.append({"contributionDays": cur_week})
    return total, weeks


def streaks(weeks):
    """-> (current streak, longest streak, busiest day)"""
    counts = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    # today may not have a contribution yet; don't let that zero out the streak
    trail = counts[:-1] if counts and counts[-1] == 0 else counts
    cur = 0
    for c in reversed(trail):
        if not c:
            break
        cur += 1
    return cur, longest, max(counts, default=0)
