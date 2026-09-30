#!/usr/bin/env python3
"""Quét 2 bộ (.claude của AI-Agent-Master + các domain của AI-Agent-Security-DevOps)
-> sinh agent-hub/data.js + gói .zip trong agent-hub/downloads/.

Chạy lại mỗi khi thêm/sửa nội dung:
    python3 agent-hub/build.py

Mô tả mỗi thẻ lấy tự động từ chính file .md (frontmatter description,
dòng Activate/Trigger, hoặc đoạn văn đầu). Tag là KHOÁ ổn định — nhãn VI/EN
được dịch ở index.html để đổi ngôn ngữ không vỡ bộ lọc.
"""
import json
import re
import zipfile
from datetime import date
from pathlib import Path

HUB = Path(__file__).resolve().parent
ROOT = HUB.parent                      # AI-Agent-Master
DL = HUB / "downloads"
SECOPS = ROOT.parent / "AI-Agent-Devops"   # clone của AI-Agent-Security-DevOps (sibling)
MCP = Path.home() / "Documents" / "LMS" / "mcp-starter-kit"   # clone của MCP-STARTER-KIT

# Link GitHub thay cho tải file
REPO = {
    "master": "https://github.com/fdhhhdjd/AI-Agent-Master",
    "secops": "https://github.com/fdhhhdjd/AI-Agent-Security-DevOps",
    "mcp": "https://github.com/fdhhhdjd/MCP-STARTER-KIT",
}
BLOB = {k: v + "/blob/main/" for k, v in REPO.items()}
# Public = ai cũng mở link được; Private = repo riêng, chỉ lớp/người có quyền mới xem.
# (Trạng thái repo GitHub 2026-09-30 — cập nhật nếu đổi public/private.)
ACCESS = {"master": "private", "secops": "private", "mcp": "public"}
OVERRIDES = json.loads((HUB / "overrides.json").read_text(encoding="utf-8")) if (HUB / "overrides.json").exists() else {}
SECOPS_VI = json.loads((HUB / "secops-vi.json").read_text(encoding="utf-8")) if (HUB / "secops-vi.json").exists() else {}

# --- Tag: khoá -> danh sách từ khoá; khớp khi 1 token của đường dẫn/slug trùng,
#     hoặc (với khoá có "-") khớp chuỗi con. Thứ tự = ưu tiên; giữ tối đa 2 tag.
TAG_RULES = [
    ("cloud",     ["aws","azure","gcp","cloudflare","cloudformation","terraform","ec2","s3","rds","iam","vpc","lambda","aks","gke","eks","ecs","fargate","vercel","firebase","convex","arm","cloud"]),
    ("compliance",["compliance","audit","auditing","cloudtrail","gdpr","hipaa","soc2","iso27001","pci","fedramp","governance","policy","continuity","disaster","runbook","vendor"]),
    ("security",  ["security","identity","iam","sso","scim","mfa","harden","hardening","scan","scanning","sast","dast","injection","rbac","auth","fingerprint","guard","guardrails","pentest","penetration","ssl","tls","vault","secrets","secret","firewall","waf","vpn","zero-trust","threat","incident","cis","sbom","supply-chain","red-teaming","keyvault","sops"]),
    ("ai",        ["ai","llm","llmops","rag","agent","model","ollama","vllm","inference","fine-tuning","bedrock","mcp","prompt","eval","evals","multi-agent","gpu","local-ai","progressive","disclosure","authoring","token"]),
    ("ops",       ["monitoring","observability","logging","loki","prometheus","grafana","datadog","new-relic","opentelemetry","elk","alerting","oncall","sre","dashboards","ebpf","sonarqube"]),
    ("data",      ["backup","cdc","database","databases","postgresql","mysql","mongodb","redis","planetscale","vector","object-storage","block-storage","nfs","index","recovery","storage"]),
    ("infra",     ["cicd","ci-cd","docker","deploy","vps","k3s","k8s","kubernetes","ssh","jenkins","helm","argocd","gitops","kustomize","ha","domain","infra","devops","container","containers","podman","nginx","reverse-proxy","load-balancing","cdn","dns","service-mesh","mesh","systemd","linux","server","servers","networking","github-actions","gitlab","circleci","openshift","blue-green","feature-flags","semantic-versioning","git-workflow","platform","devcontainers","windows","opentofu","mdm","device","troubleshooting","it"]),
    ("backend",   ["rabbitmq","payment","sepay","naming","folder","software"]),
    ("frontend",  ["frontend","responsive","animation","animations","ui","diagram","apple","emil","vocabulary","design"]),
    ("quality",   ["unit","tests","qa","review","testing"]),
    ("product",   ["build","spec","project","manager","plan","plans","achitecture","architecture","oss","seo","obsidian","patterns","modular","placement","entry","business","flow"]),
]

# --- 2 bộ nguồn
SOURCES = [("master", ROOT), ("secops", SECOPS)]
SECOPS_DOMAINS = ["security", "devops", "infrastructure", "compliance"]


def disp_path(p, base):
    return p.relative_to(base).as_posix()


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return {}, text
    fm, key = {}, None
    for line in m.group(1).splitlines():
        if line[:1] in (" ", "\t") and key:
            fm[key] = (fm[key] + " " + line.strip()).strip()
        elif ":" in line:
            key, v = line.split(":", 1)
            key, v = key.strip(), v.strip()
            fm[key] = "" if v in (">", "|", ">-", "|-") else v.strip('"').strip("'")
    return fm, text[m.end():]


def clean(s):
    s = re.sub(r"^(>\s*)+", "", s.strip())
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"[*_`]", "", s)
    s = re.sub(r"^(Activate|Trigger|Kích hoạt)\s*:\s*", "", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip()


def _describe(fm, body):
    if fm.get("description"):
        return clean(fm["description"])
    head = re.split(r"^## ", body, maxsplit=1, flags=re.M)[0]
    lines = head.splitlines() if len(head.strip().splitlines()) > 1 else body.splitlines()
    role = re.search(r"^## Role\s*\n+(.+)$", body, re.M)
    if role:
        return clean(role.group(1))
    for ln in lines:
        t = ln.lstrip("> ").strip()
        if ln.startswith(">") and re.match(r"(\*\*)?(Activate|Trigger|Kích hoạt)", t, re.I):
            return clean(t)
    for ln in lines:
        t = ln.strip("> ").strip()
        if ln.startswith(">") and len(t) > 30 and not t.startswith(('"', '*"', "**Level", "Level", "**Date")):
            return clean(t)
    para = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith(("#", "|", "```", "-", "*", "<")):
            if para:
                break
            continue
        para.append(s)
    return clean(" ".join(para)) or "—"


def describe(fm, body):
    d = _describe(fm, body)
    if d in ("—", ""):
        m = re.search(r"^## .+\n+((?:[^#|`\n<>-].*\n?)+)", body, re.M)
        if m:
            return clean(m.group(1))
    return d


def title_of(fm, body, fallback):
    m = re.search(r"^#\s+(.+)$", body, re.M)
    return clean(m.group(1)) if m else (fm.get("name") or fallback)


def motto(body):
    m = re.search(r'^>\s*\*?"(.+?)"\*?\s*$', body, re.M)
    return clean(m.group(1)) if m else ""


def headings(body):
    out, in_code = [], False
    for ln in body.splitlines():
        if ln.startswith("```"):
            in_code = not in_code
        elif not in_code and re.match(r"^##\s", ln):
            out.append(clean(ln[3:]))
    return out[:40]


_NOISE = {"claude","commands","command","skills","skill","rules","rule","references","reference",
          "agents","agent","md","src","the","and","for","with","a","of","to","in"}
def tags_for(key):
    toks = set(re.split(r"[-_/. ]+", key.lower())) - _NOISE
    k = re.sub(r"\.claude/", "", key.lower())
    tags = []
    for t, kws in TAG_RULES:
        if any((w in k) if "-" in w else (w in toks) for w in kws):
            tags.append(t)
        if len(tags) == 2:
            break
    return tags or ["other"]


_BOX = set("─│┌┐└┘├┤┬┴┼╔╗╚╝═║╠╣╦╩╬╭╮╯╰")
def extract_flows(text):
    """Chỉ lấy SƠ ĐỒ KHỐI (mermaid + ascii có khung vẽ) — KHÔNG lấy prose/step/code."""
    flows = []
    src = text.split(chr(10))
    i = 0
    while i < len(src):
        ln = src[i].strip()
        if ln.startswith("```"):
            lang = ln[3:].strip().lower()
            j = i + 1
            block = []
            while j < len(src) and not src[j].strip().startswith("```"):
                block.append(src[j]); j += 1
            if lang == "mermaid":
                flows.append({"type": "mermaid", "code": chr(10).join(block).strip()})
            else:
                boxlines = sum(1 for b in block if any(c in b for c in _BOX))
                if boxlines >= 3:
                    keep = block[:26]
                    code = chr(10).join(keep).rstrip()
                    if len(block) > 26:
                        code += chr(10) + "…"
                    flows.append({"type": "ascii", "code": code})
            i = j + 1
        else:
            i += 1
    flows.sort(key=lambda f: 0 if f["type"] == "mermaid" else 1)
    return flows[:2]



def make_item(kind, source, slug, main, base, extra=(), invoke="", group=""):
    text = main.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)
    files = [main] + [f for f in extra if f != main]
    tag_seed = slug + " " + disp_path(main, base) + " " + group
    words = sum(len(f.read_text(encoding="utf-8").split()) for f in files)
    file_objs = [{"path": disp_path(f, base), "url": BLOB[source] + disp_path(f, base)} for f in files]
    item_id = f"{source}-{kind}-{slug}".replace("/", "-")
    meta = {}
    fmraw = re.match(r"^---\n(.*?)\n---", text, re.S)
    if fmraw:
        for mk in ("author", "version"):
            mm = re.search(rf"^\s*{mk}:\s*\"?([^\"\n]+)", fmraw.group(1), re.M)
            if mm:
                meta[mk] = mm.group(1).strip().strip('"')
    return {
        "id": item_id,
        "type": kind,
        "source": source,
        "group": group,
        "slug": slug,
        "title": title_of(fm, body, slug),
        "desc": describe(fm, body),
        "motto": motto(body),
        "tags": tags_for(tag_seed),
        "invoke": invoke,
        "simple": OVERRIDES.get(item_id, {}),
        "url": file_objs[0]["url"],
        "repo": REPO[source],
        "access": ACCESS[source],
        "toc": [],
        "flows": extract_flows(text),
        "files": file_objs,
        "words": words,
        "readmin": max(1, round(words / 200)),
    }


def collect_master():
    items, cl = [], ROOT / "CLAUDE.md"
    C = ROOT / ".claude"
    if cl.exists():
        it0 = make_item("start", "master", "CLAUDE.md", cl, ROOT, invoke="Tự động — Claude đọc file này đầu tiên"); it0["tags"]=["product"]; items.append(it0)
    for f in sorted((C / "agents").glob("*.md")):
        items.append(make_item("agent", "master", f.stem, f, ROOT, invoke=f'Gọi agent "{f.stem}"'))
    cmd = C / "commands"
    folders = {"frontend": "frontend", "google-drive-backup": "google-drive-backup", "unit-tests": "unit-tests-rules"}
    for f in sorted(cmd.glob("*.md")):
        sub = folders.get(f.stem)
        extra = sorted((cmd / sub).rglob("*.md")) if sub and (cmd / sub).is_dir() else []
        items.append(make_item("command", "master", f.stem, f, ROOT, extra, invoke=f"/{f.stem}"))
    anim = cmd / "animation"
    if anim.is_dir():
        for d in sorted(p for p in anim.iterdir() if p.is_dir()):
            m = d / "SKILL.md"
            if m.exists():
                items.append(make_item("command", "master", f"animation/{d.name}", m, ROOT, sorted(d.rglob("*.md")), invoke=f"/animation:{d.name}"))
    for d in sorted(p for p in (C / "skills").iterdir() if p.is_dir()):
        mds = sorted(d.rglob("*.md"))
        if mds:
            main = d / "SKILL.md" if (d / "SKILL.md").exists() else mds[0]
            items.append(make_item("skill", "master", d.name, main, ROOT, mds, invoke=f"/{d.name} hoặc tự kích hoạt"))
    for f in sorted((C / "rules").glob("*.md")):
        items.append(make_item("rule", "master", f.stem, f, ROOT, invoke="Luôn bật — nạp qua CLAUDE.md"))
    for f in sorted((C / "references").rglob("*.md")):
        items.append(make_item("reference", "master", f.relative_to(C / "references").with_suffix("").as_posix(), f, ROOT, invoke="Tra cứu khi cần"))
    return items


DOMAIN_LABEL = {"security": "Security", "devops": "DevOps", "infrastructure": "Infrastructure", "compliance": "Compliance"}


MCP_FILES = [
    ("skill",     "mcp-starter-kit",         "SKILL.md",                       ["ai"],           "/mcp-starter-kit hoặc tự kích hoạt"),
    ("reference", "feature",                 "feature.md",                     ["ai"],           "Điền form rồi đưa cho Claude scaffold"),
    ("reference", "api-key-backend-guide",   "API-KEY-BACKEND-GUIDE.md",       ["ai","security"], "Tra cứu khi backend chưa có hệ API key"),
    ("reference", "quy-trinh-chuan",         "docs/MCP-QUY-TRINH-CHUAN.md",    ["ai"],           "Tra cứu quy trình chuẩn dựng MCP"),
    ("reference", "server-chuc-nang",        "docs/MCP-SERVER-CHUC-NANG.md",   ["ai"],           "Tra cứu chức năng MCP + API key"),
    ("reference", "template",                "templates/README.md",            ["ai"],           "Khung code mẫu để copy"),
    ("reference", "readme",                  "README.md",                      ["ai"],           "Giới thiệu bộ MCP Starter Kit"),
]


def collect_mcp():
    items = []
    if not MCP.exists():
        print(f"  (bỏ qua bộ MCP: không thấy {MCP})")
        return items
    for kind, slug, path, tags, invoke in MCP_FILES:
        f = MCP / path
        if not f.exists():
            continue
        it = make_item(kind, "mcp", slug, f, MCP, invoke=invoke, group="MCP")
        it["tags"] = tags
        if slug == "readme": it["title"] = "MCP Starter Kit — Overview"
        if slug == "template": it["title"] = "MCP template (khung code mẫu)"
        items.append(it)
    return items


def collect_secops():
    items = []
    if not SECOPS.exists():
        print(f"  (bỏ qua bộ 2: không thấy {SECOPS})")
        return items
    for domain in SECOPS_DOMAINS:
        root = SECOPS / domain
        if not root.is_dir():
            continue
        for skill in sorted(root.rglob("SKILL.md")):
            if "node_modules" in skill.parts:
                continue
            d = skill.parent
            mds = sorted(f for f in d.rglob("*.md") if "node_modules" not in f.parts)
            slug = d.relative_to(SECOPS).as_posix()
            it = make_item("skill", "secops", slug, skill, SECOPS, mds,
                           invoke=f"/{d.name} hoặc tự kích hoạt", group=DOMAIN_LABEL[domain])
            vi = SECOPS_VI.get(d.name)
            it["simple"] = {"vi": vi or it["desc"], "en": it["desc"]}
            items.append(it)
    return items


def zip_files(target, pairs):
    """pairs = [(source_path, arcname)]"""
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in pairs:
            z.write(src, arc)


def src_base(source):
    return ROOT if source == "master" else SECOPS


def build_zips(items):
    for old in DL.rglob("*.zip"):
        old.unlink()

    def pairs_of(it):
        base = src_base(it["source"])
        prefix = "" if it["source"] == "master" else "AI-Agent-Security-DevOps/"
        return [(base / f["path"], prefix + f["path"]) for f in it["files"]]

    all_pairs, by_src, by_type = [], {}, {}
    for it in items:
        pr = pairs_of(it)
        all_pairs += pr
        by_src.setdefault(it["source"], []).extend(pr)
        by_type.setdefault(it["type"], []).extend(pr)
        if len(it["files"]) > 1:
            it["zip"] = f"downloads/items/{it['id']}.zip"
            zip_files(HUB / it["zip"], pr)

    def uniq(pairs):
        seen, out = set(), []
        for s, a in pairs:
            if a not in seen:
                seen.add(a); out.append((s, a))
        return out

    zip_files(DL / "all.zip", uniq(all_pairs))
    coll = {s: f"downloads/{s}.zip" for s in by_src}
    for s, pr in by_src.items():
        zip_files(HUB / coll[s], uniq(pr))
    tzip = {t: f"downloads/type-{t}.zip" for t in by_type}
    for t, pr in by_type.items():
        zip_files(HUB / tzip[t], uniq(pr))
    return coll, tzip


def main():
    items = collect_master() + collect_secops() + collect_mcp()
    data = {
        "generated": date.today().isoformat(),
        "repos": REPO,
        "items": items,
    }
    (HUB / "data.js").write_text("window.HUB_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    n = {}
    for it in items:
        n[(it["source"], it["type"])] = n.get((it["source"], it["type"]), 0) + 1
    size = (HUB / "data.js").stat().st_size // 1024
    print(f"OK: {len(items)} mục -> data.js ({size} KB)")
    for k in sorted(n):
        print(f"   {k[0]:7} {k[1]:10} {n[k]}")


if __name__ == "__main__":
    main()
