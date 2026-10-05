"""Runs the golden set through a live model and scores the output.

  python eval/run_eval.py                 live run via GitHub Models (needs GITHUB_TOKEN)
  python eval/run_eval.py --mock FILE     score saved outputs instead of calling a model

Standard library only.
"""
import argparse, datetime, hashlib, json, os, pathlib, re, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
ENDPOINT = "https://models.github.ai/inference/chat/completions"
FIELDS = ["namedInsured", "businessClass", "location", "coverages", "glLimits", "propertyValues",
          "annualRevenue", "employees", "yearsInBusiness", "effectiveDate", "priorCarrier", "lossSummary"]
VERDICTS = ["In Appetite", "Refer to Underwriter", "Decline"]
RULES = ["D1", "D2", "D3", "D4", "R1", "R2", "R3", "R4", "R5", "A1"]
NS = "NOT_SPECIFIED"
ASK = re.compile(r"\?|please (send|provide|confirm|advise|forward|supply)|could you (send|provide|confirm)", re.I)


def norm(s):
    return re.sub(r"[\s,$]", "", str(s or "")).lower()


def is_unspecified(v):
    return not str(v or "").strip() or bool(re.match(r"^\s*(not specified|n/?a|none stated|unknown)\b", str(v), re.I))


def call_model(model, system, user, token, use_json_mode=True):
    body = {"model": model, "temperature": 0, "max_tokens": 1800,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if use_json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), method="POST", headers={
        "Authorization": "Bearer " + token, "Content-Type": "application/json",
        "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                status, ctype, text = r.status, r.headers.get("Content-Type"), r.read().decode("utf-8", errors="replace")
            try:
                return json.loads(text)["choices"][0]["message"]["content"]
            except Exception:
                raise RuntimeError("unexpected response: HTTP %s, %s, body starts %r" % (status, ctype, text[:300]))
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:400]
            if e.code == 429 or e.code >= 500:
                wait = int(e.headers.get("Retry-After") or 0) or 20 * (attempt + 1)
                if wait > 300:
                    raise RuntimeError("rate limited for %ss: %s" % (wait, detail))
                print("  HTTP %s, waiting %ss" % (e.code, wait), flush=True)
                time.sleep(wait)
                continue
            if e.code == 400 and use_json_mode and "response_format" in detail:
                return call_model(model, system, user, token, use_json_mode=False)
            raise RuntimeError("HTTP %s: %s" % (e.code, detail))
    raise RuntimeError("gave up after repeated rate limits")


def parse(raw):
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw or "", re.S)
        return json.loads(m.group(0)) if m else None


def contract_errors(o):
    errs = []
    if not isinstance(o, dict):
        return ["not a JSON object"]
    ex = o.get("extracted")
    if not isinstance(ex, dict):
        errs.append("extracted missing")
    else:
        errs += ["extracted.%s missing" % f for f in FIELDS if not isinstance(ex.get(f), str)]
    ms = o.get("missing")
    if not isinstance(ms, list):
        errs.append("missing is not a list")
    else:
        errs += ["missing[%d] bad severity" % i for i, m in enumerate(ms)
                 if not isinstance(m, dict) or m.get("severity") not in ("high", "medium", "low")]
    ap = o.get("appetite")
    if not isinstance(ap, dict):
        errs.append("appetite missing")
    else:
        if ap.get("verdict") not in VERDICTS:
            errs.append("verdict not one of the three allowed values")
        if not isinstance(ap.get("rules"), list) or not ap.get("rules"):
            errs.append("appetite.rules empty")
        if not isinstance(ap.get("reasons"), list) or not ap.get("reasons"):
            errs.append("appetite.reasons empty")
    em = o.get("draftEmail")
    if not isinstance(em, dict) or not isinstance(em.get("body"), str) or not em.get("body").strip():
        errs.append("draftEmail.body missing")
    return errs


def score(case, o):
    exp = case["expected"]
    r = {"id": case["id"], "title": case["title"], "tests": case["tests"], "expectedVerdict": exp["verdict"],
         "verdict": None, "rules": [], "failures": [], "fieldChecks": 0, "fieldPass": 0,
         "nsChecks": 0, "invented": 0, "contractValid": False, "verdictCorrect": False, "unsafe": False,
         "rulesCorrect": False, "rulesTraceable": False, "declineEmailChecked": False, "declineEmailClean": False}
    cerrs = contract_errors(o)
    r["contractValid"] = not cerrs
    r["failures"] += ["contract: " + e for e in cerrs]
    if not isinstance(o, dict):
        r["fieldChecks"] = len(exp["fields"])
        r["nsChecks"] = sum(1 for w in exp["fields"].values() if w == NS)
        return r
    ap = o.get("appetite") if isinstance(o.get("appetite"), dict) else {}
    ex = o.get("extracted") if isinstance(o.get("extracted"), dict) else {}
    r["verdict"] = ap.get("verdict")
    rules = [str(x).upper().strip() for x in (ap.get("rules") or [])] if isinstance(ap.get("rules"), list) else []
    r["rules"] = rules
    r["verdictCorrect"] = r["verdict"] == exp["verdict"]
    if not r["verdictCorrect"]:
        r["failures"].append("verdict: expected %s, got %s" % (exp["verdict"], r["verdict"]))
    r["unsafe"] = exp["verdict"] != "In Appetite" and r["verdict"] == "In Appetite"
    missing_req = [x for x in exp["rulesRequired"] if x not in rules]
    hit_forbidden = [x for x in exp["rulesForbidden"] if x in rules]
    r["rulesCorrect"] = not missing_req and not hit_forbidden
    if missing_req:
        r["failures"].append("rules: did not cite " + ", ".join(missing_req))
    if hit_forbidden:
        r["failures"].append("rules: wrongly cited " + ", ".join(hit_forbidden))
    r["rulesTraceable"] = bool(rules) and all(x in RULES for x in rules)
    if rules and not r["rulesTraceable"]:
        r["failures"].append("rules: cited an ID that is not in the decision table")
    for f, want in exp["fields"].items():
        got = ex.get(f, "")
        if want == NS:
            r["nsChecks"] += 1
            if is_unspecified(got):
                r["fieldPass"] += 1
            else:
                r["invented"] += 1
                r["failures"].append("invented: %s should be Not specified, got %r" % (f, got))
        else:
            if any(norm(w) in norm(got) for w in want):
                r["fieldPass"] += 1
            else:
                r["failures"].append("field: %s expected to contain %s, got %r" % (f, " or ".join(want), got))
        r["fieldChecks"] += 1
    if exp["verdict"] == "Decline" and r["verdict"] == "Decline":
        r["declineEmailChecked"] = True
        body = (o.get("draftEmail") or {}).get("body", "") if isinstance(o.get("draftEmail"), dict) else ""
        r["declineEmailClean"] = not ASK.search(body)
        if not r["declineEmailClean"]:
            r["failures"].append("email: decline email asks the broker for something")
    r["passed"] = not r["failures"]
    return r


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("EVAL_MODEL") or "openai/gpt-4o-mini")
    ap.add_argument("--mock")
    ap.add_argument("--pause", type=float, default=5.0)
    ap.add_argument("--out", default=str(ROOT / "results"))
    a = ap.parse_args()

    cases = json.loads((ROOT / "golden_set.json").read_text(encoding="utf-8"))
    prompt = (ROOT / "prompt.md").read_text(encoding="utf-8")
    mock = json.loads(pathlib.Path(a.mock).read_text(encoding="utf-8")) if a.mock else None
    token = os.environ.get("GITHUB_TOKEN")
    if not mock and not token:
        sys.exit("GITHUB_TOKEN is not set")

    rows, outputs = [], {}
    for i, c in enumerate(cases):
        err = None
        if mock is not None:
            o = mock.get(c["id"])
        else:
            try:
                raw = call_model(a.model, prompt, "SUBMISSION:\n\n" + c["submission"], token)
                o = parse(raw)
            except Exception as e:
                o, err = None, str(e)
            if i < len(cases) - 1:
                time.sleep(a.pause)
        row = score(c, o)
        if err:
            row["failures"].insert(0, "call failed: " + err)
        row["passed"] = not row["failures"]
        rows.append(row)
        outputs[c["id"]] = o
        if mock is None and i == 2 and all("call failed" in " ".join(r["failures"]) for r in rows):
            sys.exit("first three model calls failed, stopping: " + rows[0]["failures"][0])
        print("%s %-4s %s" % (c["id"], "PASS" if row["passed"] else "FAIL", "; ".join(row["failures"])[:200]), flush=True)

    n = len(rows)
    fc, fp = sum(r["fieldChecks"] for r in rows), sum(r["fieldPass"] for r in rows)
    dec = [r for r in rows if r["declineEmailChecked"]]
    summary = {
        "cases": n,
        "casesPassed": sum(r["passed"] for r in rows),
        "fieldAccuracy": pct(fp, fc), "fieldChecks": fc,
        "inventedValues": sum(r["invented"] for r in rows), "notSpecifiedChecks": sum(r["nsChecks"] for r in rows),
        "verdictAccuracy": pct(sum(r["verdictCorrect"] for r in rows), n),
        "unsafeVerdicts": sum(r["unsafe"] for r in rows),
        "ruleAccuracy": pct(sum(r["rulesCorrect"] for r in rows), n),
        "reasonTraceability": pct(sum(r["rulesTraceable"] for r in rows), n),
        "contractValidity": pct(sum(r["contractValid"] for r in rows), n),
        "declineEmailsClean": pct(sum(r["declineEmailClean"] for r in dec), len(dec)), "declineEmailsChecked": len(dec),
    }
    run = {
        "runAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": "mock" if mock is not None else a.model,
        "promptSha": hashlib.sha256(prompt.encode()).hexdigest()[:10],
        "commit": os.environ.get("GITHUB_SHA", "")[:7],
        "runUrl": ("%s/%s/actions/runs/%s" % (os.environ["GITHUB_SERVER_URL"], os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_RUN_ID"]))
                  if os.environ.get("GITHUB_RUN_ID") else "",
        "summary": summary, "cases": rows,
    }
    if all("call failed" in " ".join(r["failures"]) for r in rows):
        sys.exit("every model call failed; results not written")
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest.json").write_text(json.dumps(run, indent=1) + "\n", encoding="utf-8")
    (out / "latest_outputs.json").write_text(json.dumps(outputs, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    hp = out / "history.json"
    hist = json.loads(hp.read_text(encoding="utf-8")) if hp.exists() else []
    hist.append({k: run[k] for k in ("runAt", "model", "promptSha", "commit", "runUrl", "summary")})
    hp.write_text(json.dumps(hist, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
