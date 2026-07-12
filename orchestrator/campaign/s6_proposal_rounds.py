#!/usr/bin/env python3
"""s6_proposal_rounds — D52 提案ラウンド束 (S-2/C4/C5) の実走 driver。

正本 = docs/phase3-main-experiment.md「2026-07-13 着手時確定」節 (凍結数値) +
output/insights/2026-07-13_s6-round-execution-design.md (運用設計 v2 — 3 レンズ敵対レビュー済み)。
本スクリプトは v2 の機械手続き (§2/§3/§5/§6) の実装であり、凍結値を変更しない。

サブコマンド (実行順):
  freeze     凍結物の生成 (--master-seed 必須 — 人間が承認 gate で独立確定した整数):
             用途別 seed 導出 / C4 抽出列 / 実行順・採点順 / 60 呼び出しペイロード /
             採点プロンプト投入定型部 / hash 台帳。生成後に凍結コミットする (人間手順)
  verify     実走前検証: 鮮度検証 3 述語 (v2 §3.1) + アーム間単一差分の機械 diff (v2 §6)。
             1 つでも不成立なら exit 1 (fails-closed — 実走を開始しない)
  run        60 スロットの実行 (再開冪等: 出力ファイルが存在するスロットは skip)。
             proposer 出力の三分法判定 (v2 §3.3) と補充 (retry ≤ 2/スロット) を機械執行
  anonymize  ラベル除去 (実行メタを落とし proposer 出力 JSON 本体のみに) + 採点順の混合
  score      採点実行 (混合順・1 件ごと fresh・カウンタ上限 120 の機械執行、v2 §5.5)
  tally      集計 (ラウンド二値・アーム適格率・Fisher 名目 p 値。Holm 族最終判定はしない —
             S-1a/S-1b 確定まで閉じない、凍結済み)

実行機構 (canary 07-13 (1) と同一): claude -p headless・全ツール disallow・
動的システムプロンプト節の除去・リポジトリ外の中立 cwd・model = opus。
"""

import argparse
import hashlib
import json
import random
import subprocess
import sys
from math import comb
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUBMODULE = REPO / "external/ccbench"
N1_PROVENANCE = REPO / "output/insights/2026-07-10_s8a-n1-provenance.json"
AGENT_DEF = REPO / ".claude/agents/axis-proposer.md"
SCORING_SYSTEM = Path(__file__).parent / "s6_scoring_prompt_system.txt"
SCORING_USER_TEMPLATE = Path(__file__).parent / "s6_scoring_prompt_user_template.txt"

OUT = REPO / "output/s6-rounds"
FROZEN = OUT / "frozen"
RUNS = OUT / "runs"
ANON = OUT / "anon"
SCORES = OUT / "scores"

N_ROUNDS = 20  # 凍結値 (変更禁止)
ARMS = ("main", "c4", "c5")  # 本アーム / 選定無作為対照 / 帰属遮断対照
MAX_RETRY = 2  # 補充 retry 上限/スロット (凍結値)
SCORING_BUDGET = 120  # 総採点上限 = 二値が得られた成功採点数 (凍結値、v2 §5.5 の操作化)
EXPECTED_POPULATION_SIZE = 17

# canary (07-13 (1)) の遮断構成を踏襲
DISALLOWED_TOOLS = (
    "Bash Read Write Edit Glob Grep WebFetch WebSearch Agent Task NotebookEdit "
    "TodoWrite Skill Workflow ExitPlanMode AskUserQuestion ToolSearch CronCreate "
    "CronDelete CronList DesignSync EnterWorktree ExitWorktree Monitor "
    "PushNotification RemoteTrigger ReportFindings ScheduleWakeup SendMessage "
    "TaskCreate TaskGet TaskList TaskOutput TaskStop TaskUpdate"
)

PROPOSAL_REQUIRED_FIELDS = (
    "axis_name", "mutation_type", "hole_location", "mechanism_hypothesis",
    "safety_argument_hypothesis", "unknowns",
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def derive_seed(master_seed: int, purpose: str) -> int:
    digest = hashlib.sha256(f"izanagi-s6:{master_seed}:{purpose}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def load_projected_input() -> dict:
    with open(N1_PROVENANCE) as f:
        return json.load(f)["projected_input"]


def agent_system_prompt() -> str:
    """axis-proposer.md 本文 (frontmatter 除く) = proposer のシステムプロンプト。"""
    text = AGENT_DEF.read_text()
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        sys.exit("fails-closed: axis-proposer.md の frontmatter 構造が想定外")
    return parts[2].lstrip("\n")


# ---------------------------------------------------------------- freshness


def freshness_check() -> list[str]:
    """v2 §3.1 の機械述語 3 点。返り値 = 不一致の記述リスト (空 = 全一致)。"""
    problems = []
    pi = load_projected_input()

    ls = subprocess.run(
        ["git", "-C", str(SUBMODULE), "ls-tree", "-r", "--name-only", "HEAD", "cc/silo/"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    regen = sorted(
        [p for p in ls if (p.endswith(".cc") or p.endswith(".hh")) and "/script/" not in p]
        + ["include/backoff.hh"]
    )
    frozen_regions = sorted(e["region"] for e in pi["edit_surface_map"])
    if regen != frozen_regions:
        problems.append(f"領域集合不一致: 再生成のみ {set(regen) - set(frozen_regions)}, "
                        f"凍結のみ {set(frozen_regions) - set(regen)}")

    for e in pi["stock_excerpts"]:
        cur = subprocess.run(
            ["git", "-C", str(SUBMODULE), "show", f"HEAD:{e['region']}"],
            capture_output=True, text=True,
        )
        if cur.returncode != 0 or cur.stdout != e["excerpt"]:
            problems.append(f"抜粋全文不一致: {e['region']}")

    ebs = {"include/backoff.hh", "cc/silo/transaction.cc"}
    for e in pi["edit_surface_map"]:
        if e["opened"] != (e["region"] in ebs):
            problems.append(f"opened 判定不一致: {e['region']}")
    return problems


# ------------------------------------------------------------------- freeze


def build_payload(pi: dict, arm: str, directive: "str | None") -> dict:
    """アーム別入力 JSON (v2 §4 — 差分は構成フィールドのみ)。"""
    payload = {
        "diagnostics": {} if arm == "c5" else pi["diagnostics"],
        "stock_excerpts": pi["stock_excerpts"],
        "edit_surface_map": pi["edit_surface_map"],
    }
    if arm == "c4":
        if directive is None:
            sys.exit("fails-closed: c4 に directive がない")
        payload["hole_region_directive"] = directive
    return payload


def cmd_freeze(args) -> None:
    if FROZEN.exists() and any(FROZEN.iterdir()):
        sys.exit("fails-closed: frozen/ が既に存在する — 凍結のやり直しは引き直しの余地。"
                 "意図的な再凍結なら人間がディレクトリを明示削除してから再実行 (git 履歴に残す)")
    problems = freshness_check()
    if problems:
        sys.exit("fails-closed: 鮮度検証不一致 — 実走準備を開始しない:\n  " + "\n  ".join(problems))

    FROZEN.mkdir(parents=True, exist_ok=True)
    pi = load_projected_input()
    s = args.master_seed

    # C4 抽出 (s6_c4_region_draw と同一規則 — 二重実装を避けるため同一手続きをここに持つ)
    regions = sorted(e["region"] for e in pi["edit_surface_map"])
    if len(regions) != EXPECTED_POPULATION_SIZE:
        sys.exit(f"fails-closed: 領域数 {len(regions)} != {EXPECTED_POPULATION_SIZE}")
    draw_seed = derive_seed(s, "c4-draw")
    drawn = random.Random(draw_seed).choices(regions, k=N_ROUNDS)

    # 実行順 (60 スロットの混合) と採点順の seed
    slots = [f"{arm}-{i:02d}" for arm in ARMS for i in range(N_ROUNDS)]
    exec_seed = derive_seed(s, "exec-order")
    exec_order = slots[:]
    random.Random(exec_seed).shuffle(exec_order)
    scoring_seed = derive_seed(s, "scoring-order")  # 混合列は anonymize 時に実スロット集合へ適用

    # ペイロード 60 本
    payloads = {}
    for arm in ARMS:
        for i in range(N_ROUNDS):
            directive = drawn[i] if arm == "c4" else None
            payloads[f"{arm}-{i:02d}"] = build_payload(pi, arm, directive)
    payload_dir = FROZEN / "payloads"
    payload_dir.mkdir()
    for slot, p in payloads.items():
        (payload_dir / f"{slot}.json").write_text(
            json.dumps(p, ensure_ascii=False, indent=1) + "\n")

    # proposer システムプロンプト / 採点プロンプト投入定型部
    sysp = agent_system_prompt()
    (FROZEN / "proposer_system_prompt.txt").write_text(sysp)
    scoring_system = SCORING_SYSTEM.read_text()
    (FROZEN / "scoring_system_prompt.txt").write_text(scoring_system)
    template = SCORING_USER_TEMPLATE.read_text()
    scoring_user_prefix = template.replace(
        "{PROJECTED_INPUT_JSON}", json.dumps(pi, ensure_ascii=False, indent=1))
    if "{PROPOSAL_BUNDLE_JSON}" not in scoring_user_prefix:
        sys.exit("fails-closed: 採点雛形にプレースホルダがない")
    (FROZEN / "scoring_user_prefix.txt").write_text(scoring_user_prefix)

    ledger = {
        "what": "D52 提案ラウンド束の凍結台帳 (v2 §3.2/§5.2 — 提案生成前の freeze-before-observation)",
        "master_seed": s,
        "master_seed_provenance": "人間確定 (承認 gate)。準備者は候補提示・試算をしていない",
        "seed_derivation_rule": "int.from_bytes(sha256('izanagi-s6:<master>:<用途>')[:8], 'big')",
        "derived_seeds": {"c4-draw": draw_seed, "exec-order": exec_seed,
                          "scoring-order": scoring_seed},
        "c4_drawn_regions": drawn,
        "population_sha256": sha256_text(
            json.dumps(regions, ensure_ascii=False, separators=(",", ":"))),
        "exec_order": exec_order,
        "proposer_system_prompt_sha256": sha256_text(sysp),
        "scoring_system_prompt_sha256": sha256_text(scoring_system),
        "scoring_user_prefix_sha256": sha256_text(scoring_user_prefix),
        "payload_sha256": {slot: sha256_text((payload_dir / f"{slot}.json").read_text())
                           for slot in sorted(payloads)},
        "submodule_pin": subprocess.run(
            ["git", "-C", str(SUBMODULE), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip(),
        "n1_provenance_sha256": sha256_text(N1_PROVENANCE.read_text()),
        "python_version": sys.version.split()[0],
    }
    (FROZEN / "hash_ledger.json").write_text(
        json.dumps(ledger, ensure_ascii=False, indent=1) + "\n")

    total_chars = sum(len((payload_dir / f"{s_}.json").read_text()) for s_ in payloads)
    print(f"凍結完了: {FROZEN}")
    print(f"  ペイロード 60 本 (計 {total_chars/1e6:.1f}M 文字 ≈ {total_chars/3.5/1e6:.2f}M tokens 入力)")
    print(f"  採点定型部 {len(scoring_user_prefix)/1e3:.0f}k 文字 ≈ "
          f"{len(scoring_user_prefix)/3.5/1e3:.0f}k tokens/採点")
    print("次: 凍結コミット (人間手順) → verify → run")


# ------------------------------------------------------------------- verify


def cmd_verify(_args) -> None:
    problems = freshness_check()

    ledger = json.loads((FROZEN / "hash_ledger.json").read_text())
    # 凍結物の hash 再検証 (改変検出)
    for name, key in [("proposer_system_prompt.txt", "proposer_system_prompt_sha256"),
                      ("scoring_system_prompt.txt", "scoring_system_prompt_sha256"),
                      ("scoring_user_prefix.txt", "scoring_user_prefix_sha256")]:
        if sha256_text((FROZEN / name).read_text()) != ledger[key]:
            problems.append(f"凍結物改変: {name}")

    # アーム間単一差分の機械 diff (v2 §6): 各ラウンド i で main/c4/c5 のペイロードを比較
    for i in range(N_ROUNDS):
        loaded = {arm: json.loads((FROZEN / "payloads" / f"{arm}-{i:02d}.json").read_text())
                  for arm in ARMS}
        for arm in ARMS:
            if sha256_text(json.dumps(loaded[arm], ensure_ascii=False, indent=1) + "\n") \
                    != ledger["payload_sha256"][f"{arm}-{i:02d}"]:
                problems.append(f"凍結物改変: payload {arm}-{i:02d}")
        keys = {arm: set(loaded[arm].keys()) for arm in ARMS}
        if keys["main"] != {"diagnostics", "stock_excerpts", "edit_surface_map"} \
                or keys["c5"] != keys["main"] \
                or keys["c4"] != keys["main"] | {"hole_region_directive"}:
            problems.append(f"ラウンド {i}: キー集合が想定差分と不一致")
            continue
        for shared in ("stock_excerpts", "edit_surface_map"):
            if not (loaded["main"][shared] == loaded["c4"][shared] == loaded["c5"][shared]):
                problems.append(f"ラウンド {i}: 共通部 {shared} がアーム間で異なる")
        if loaded["main"]["diagnostics"] != loaded["c4"]["diagnostics"]:
            problems.append(f"ラウンド {i}: diagnostics が main と c4 で異なる")
        if loaded["c5"]["diagnostics"] != {}:
            problems.append(f"ラウンド {i}: c5 の diagnostics が空でない")

    if problems:
        sys.exit("fails-closed: verify 不成立 — 実走を開始しない:\n  " + "\n  ".join(problems))
    print("verify: 鮮度 3 述語 + 凍結物 hash + アーム間単一差分 = すべて成立")


# --------------------------------------------------------------------- run


def classify_proposer_output(raw: str):
    """v2 §3.3 の三分法。返り値 = (分類, 詳細)。
    分類: 'supplement' (機械故障 → retry) / 'score' (採点行き) / 'score_zero' (ラウンド 0 直行)。
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return "supplement", {"reason": "json-parse-failure"}
    if not isinstance(data, dict) or "proposals" not in data or "global_unknowns" not in data:
        return "supplement", {"reason": "missing-required-field:top-level"}
    p = data["proposals"]
    if not isinstance(p, list):
        return "score_zero", {"reason": "type-invalid:proposals-not-array"}
    if len(p) == 0:
        return "score_zero", {"reason": "zero-proposals"}
    # 非 dict 要素 (型不正の提案) は採点前に機械除去して記録する — 内容退化の機械適用
    # (曖昧は no)。除去後 0 件ならラウンド不適格に直行。
    dropped = [i for i, prop in enumerate(p) if not isinstance(prop, dict)]
    p = [prop for prop in p if isinstance(prop, dict)]
    if len(p) == 0:
        return "score_zero", {"reason": "all-proposals-type-invalid"}
    for idx, prop in enumerate(p):
        for k in PROPOSAL_REQUIRED_FIELDS:
            if k not in prop:
                return "supplement", {"reason": f"missing-required-field:proposals[{idx}].{k}"}
    truncated = None
    if len(p) > 3:
        truncated = f"truncated-{len(p)}-to-3 (JSON 配列順先頭 3 件、v2 §3.3)"
        p = p[:3]
    data["proposals"] = p
    return "score", {"bundle": data, "truncated": truncated,
                     "dropped_non_dict_indices": dropped or None}


def call_headless(system_prompt: str, user_prompt: str, cwd: Path) -> dict:
    """claude -p headless 呼び出し (canary の遮断構成)。返り値 = 生出力とメタ。"""
    cmd = [
        "claude", "-p", "--model", "opus", "--output-format", "json",
        "--exclude-dynamic-system-prompt-sections",
        "--disallowedTools", *DISALLOWED_TOOLS.split(),
        "--system-prompt", system_prompt,
        user_prompt,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd), timeout=1200)
    return {"returncode": r.returncode, "stdout": r.stdout, "stderr": r.stderr[-2000:]}


def cmd_run(args) -> None:
    cmd_verify(args)  # 実走直前に必ず verify (fails-closed)
    RUNS.mkdir(parents=True, exist_ok=True)
    ledger = json.loads((FROZEN / "hash_ledger.json").read_text())
    sysp = (FROZEN / "proposer_system_prompt.txt").read_text()
    neutral_cwd = Path(args.neutral_cwd)
    if str(REPO) in str(neutral_cwd.resolve()) or "izanagi" in neutral_cwd.name:
        sys.exit("fails-closed: 中立 cwd がリポジトリ内/izanagi を含む")
    neutral_cwd.mkdir(parents=True, exist_ok=True)

    for slot in ledger["exec_order"]:
        final = RUNS / f"{slot}.final.json"
        if final.exists():
            continue  # 再開冪等 (v2 §3.4)
        payload = (FROZEN / "payloads" / f"{slot}.json").read_text()
        outcome = None
        for retry in range(MAX_RETRY + 1):
            attempt_path = RUNS / f"{slot}.attempt{retry}.json"
            if attempt_path.exists():
                attempt = json.loads(attempt_path.read_text())
            else:
                res = call_headless(sysp, payload, neutral_cwd)
                if res["returncode"] != 0:
                    attempt = {"classification": "supplement",
                               "detail": {"reason": f"api-error:rc={res['returncode']}"},
                               "raw": res}
                else:
                    # claude -p --output-format json の result フィールドが本文
                    try:
                        body = json.loads(res["stdout"]).get("result", "")
                    except (json.JSONDecodeError, ValueError):
                        body = res["stdout"]
                    cls, detail = classify_proposer_output(body)
                    attempt = {"classification": cls, "detail": detail, "raw": res}
                attempt_path.write_text(json.dumps(attempt, ensure_ascii=False, indent=1))
            if attempt["classification"] != "supplement":
                outcome = attempt
                break
        if outcome is None:
            outcome = {"classification": "unfilled",
                       "detail": {"reason": f"supplement-retry-exhausted({MAX_RETRY})"}}
            # 凍結規則: 上限内で 20/アーム未達 → 当該検定判定不能 (tally が執行)
        final.write_text(json.dumps(outcome, ensure_ascii=False, indent=1))
        print(f"{slot}: {outcome['classification']}")
    print("run 完了 (全スロット final あり)")


# ---------------------------------------------------------- anonymize/score


def cmd_anonymize(_args) -> None:
    ANON.mkdir(parents=True, exist_ok=True)
    ledger = json.loads((FROZEN / "hash_ledger.json").read_text())
    slots = [f"{arm}-{i:02d}" for arm in ARMS for i in range(N_ROUNDS)]
    to_score = []
    for slot in slots:
        final = json.loads((RUNS / f"{slot}.final.json").read_text())
        if final["classification"] == "score":
            to_score.append(slot)
    order = to_score[:]
    random.Random(ledger["derived_seeds"]["scoring-order"]).shuffle(order)
    mapping = {}
    for pos, slot in enumerate(order):
        final = json.loads((RUNS / f"{slot}.final.json").read_text())
        # ラベル除去: 提案束 JSON 本体のみ (実行メタ・アーム名・raw は落とす)
        (ANON / f"score-input-{pos:03d}.json").write_text(
            json.dumps(final["detail"]["bundle"], ensure_ascii=False, indent=1))
        mapping[f"{pos:03d}"] = slot
    (ANON / "mapping.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=1))
    print(f"anonymize: 採点対象 {len(order)} 件 (score_zero/unfilled は採点外で確定済み)")


def validate_score(score, bundle) -> "str | None":
    """採点出力の機械照合 (敵対チェック must 1)。返り値 = 不備の記述 (None = 合格)。
    round_eligible の型 (bool)・件数一致・eligible == AND(c1,c2,c3)・
    round_eligible == OR(eligible)・副指標の範囲を照合する。不備 = 機械故障 → retry。
    """
    if not isinstance(score, dict):
        return "score-not-dict"
    ps = score.get("proposals_scored")
    if not isinstance(ps, list):
        return "proposals_scored-not-list"
    if len(ps) != len(bundle["proposals"]):
        return f"count-mismatch:{len(ps)}!={len(bundle['proposals'])}"
    if not isinstance(score.get("round_eligible"), bool):
        return "round_eligible-not-bool"
    eligibles = []
    for i, item in enumerate(ps):
        if not isinstance(item, dict):
            return f"scored[{i}]-not-dict"
        bits = [item.get("c1_novel_vs_projection"), item.get("c2_mechanism_substantive"),
                item.get("c3_axis_eligible"), item.get("eligible")]
        if any(not isinstance(b, bool) for b in bits):
            return f"scored[{i}]-criteria-not-bool"
        if item["eligible"] != (bits[0] and bits[1] and bits[2]):
            return f"scored[{i}]-eligible!=AND(c1,c2,c3)"
        eligibles.append(item["eligible"])
    if score["round_eligible"] != any(eligibles):
        return "round_eligible!=OR(eligible)"
    dea = score.get("distinct_eligible_axes")
    if not isinstance(dea, int) or not (0 <= dea <= sum(eligibles)) \
            or (sum(eligibles) > 0 and dea < 1):
        return "distinct_eligible_axes-out-of-range"
    return None


def cmd_score(args) -> None:
    SCORES.mkdir(parents=True, exist_ok=True)
    # 凍結測定器の同一性を実行直前に再検証 (cmd_run が verify を呼ぶのと対称)
    ledger = json.loads((FROZEN / "hash_ledger.json").read_text())
    prefix = (FROZEN / "scoring_user_prefix.txt").read_text()
    scoring_sys = (FROZEN / "scoring_system_prompt.txt").read_text()
    if sha256_text(prefix) != ledger["scoring_user_prefix_sha256"] \
            or sha256_text(scoring_sys) != ledger["scoring_system_prompt_sha256"]:
        sys.exit("fails-closed: 採点プロンプトが凍結 hash と不一致 — 採点を開始しない")
    neutral_cwd = Path(args.neutral_cwd)
    neutral_cwd.mkdir(parents=True, exist_ok=True)
    inputs = sorted(ANON.glob("score-input-*.json"))
    success_count = sum(1 for _ in SCORES.glob("score-*.final.json"))
    for path in inputs:
        pos = path.stem.split("-")[-1]
        final = SCORES / f"score-{pos}.final.json"
        if final.exists():
            continue
        if success_count >= SCORING_BUDGET:
            sys.exit(f"fails-closed: 採点カウンタ {success_count} が上限 {SCORING_BUDGET} — "
                     "未採点が残るため当該検定は判定不能 (tally に committed)")
        bundle = json.loads(path.read_text())
        user_prompt = prefix.replace("{PROPOSAL_BUNDLE_JSON}", path.read_text())
        outcome = None
        for retry in range(MAX_RETRY + 1):  # 機械故障のみ retry (別カウンタ、120 に数えない)
            res = call_headless(scoring_sys, user_prompt, neutral_cwd)
            if res["returncode"] != 0:
                continue
            try:
                body = json.loads(res["stdout"]).get("result", "")
                score = json.loads(body)
            except (json.JSONDecodeError, ValueError):
                continue  # パース不能 = 機械故障扱い → retry
            problem = validate_score(score, bundle)
            if problem is not None:
                # 型・論理和・件数の不整合 = 機械故障扱い → retry (敵対チェック must 1)
                (SCORES / f"score-{pos}.reject{retry}.json").write_text(json.dumps(
                    {"problem": problem, "score": score}, ensure_ascii=False, indent=1))
                continue
            outcome = {"score": score, "retries_used": retry}
            break
        if outcome is None:
            sys.exit(f"fails-closed: 採点スロット {pos} が retry {MAX_RETRY} 超過 — "
                     "二値が得られない = 当該検定判定不能 (0 計上への置換はしない、v2 §5.5)")
        final.write_text(json.dumps(outcome, ensure_ascii=False, indent=1))
        success_count += 1
        print(f"score-{pos}: round_eligible={outcome['score']['round_eligible']} "
              f"({success_count}/{SCORING_BUDGET})")


# -------------------------------------------------------------------- tally


def fisher_one_sided_p(x1: int, x2: int, n1: int, n2: int) -> float:
    k = x1 + x2
    denom = comb(n1 + n2, k)
    hi = min(k, n1)
    return sum(comb(n1, i) * comb(n2, k - i) for i in range(x1, hi + 1)) / denom


def cmd_tally(_args) -> None:
    mapping = json.loads((ANON / "mapping.json").read_text())
    inv = {v: k for k, v in mapping.items()}
    rounds = {arm: {} for arm in ARMS}
    undecidable = []
    for arm in ARMS:
        for i in range(N_ROUNDS):
            slot = f"{arm}-{i:02d}"
            final = json.loads((RUNS / f"{slot}.final.json").read_text())
            if final["classification"] == "score_zero":
                rounds[arm][i] = 0
            elif final["classification"] == "unfilled":
                undecidable.append(slot)
            else:
                pos = inv[slot]
                sc = json.loads((SCORES / f"score-{pos}.final.json").read_text())["score"]
                # validate_score が保証済みの整合を tally でも独立再計算 (防御の二重化)
                recomputed = any(x["eligible"] for x in sc["proposals_scored"])
                if sc["round_eligible"] is not recomputed:
                    sys.exit(f"fails-closed: {slot} の round_eligible が再計算と不一致 — "
                             "採点物が validate_score を経ていない")
                rounds[arm][i] = 1 if recomputed else 0
    result = {"rounds": rounds, "undecidable_slots": undecidable}
    if undecidable:
        result["verdict"] = ("判定不能 (n=20/アーム の二値が揃わない — 凍結の判定不能原則)")
    else:
        x = {arm: sum(rounds[arm].values()) for arm in ARMS}
        result["eligible_counts"] = x
        result["eligible_rates"] = {arm: x[arm] / N_ROUNDS for arm in ARMS}
        result["nominal_p_s2_main_vs_c4"] = fisher_one_sided_p(x["main"], x["c4"], N_ROUNDS, N_ROUNDS)
        result["nominal_p_s3_main_vs_c5"] = fisher_one_sided_p(x["main"], x["c5"], N_ROUNDS, N_ROUNDS)
        result["floor_main_ge_10"] = x["main"] >= 10
        result["note"] = ("名目 p 値の先行報告のみ。Holm 族調整済み最終判定は S-1a/S-1b の p 値"
                          "確定まで閉じない (凍結済み)。連言 = Fisher 有意 かつ floor")
    out = OUT / "tally.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_freeze = sub.add_parser("freeze")
    p_freeze.add_argument("--master-seed", type=int, required=True,
                          help="人間が承認 gate で独立確定した整数")
    sub.add_parser("verify")
    p_run = sub.add_parser("run")
    p_run.add_argument("--neutral-cwd", required=True,
                       help="リポジトリ外の中立 cwd (パスに izanagi を含まない)")
    sub.add_parser("anonymize")
    p_score = sub.add_parser("score")
    p_score.add_argument("--neutral-cwd", required=True)
    sub.add_parser("tally")
    args = ap.parse_args()
    {"freeze": cmd_freeze, "verify": cmd_verify, "run": cmd_run,
     "anonymize": cmd_anonymize, "score": cmd_score, "tally": cmd_tally}[args.cmd](args)


if __name__ == "__main__":
    main()
