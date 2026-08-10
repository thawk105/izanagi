#!/usr/bin/env python3
"""amendment 2026-07-13-fence: フェンス欠陥修正後の attempt 機械再分類 + final 再導出。

経緯: 実走 1 巡目 (master seed 265504576) で classify_proposer_output がコードフェンス
付き完全 JSON を json-parse-failure = supplement と誤判定 (5/7 attempt)。ユーザー裁定 A
(2026-07-13) = 分類器修正 + 保存済み raw からの追加呼び出しゼロ再分類 + 続きから再走。

規則 (機械的・内容非依存・アーム間中立):
1. 各 attempt の raw.stdout から body を再抽出 (cmd_run と同一ロジック) し、修正版
   classify_proposer_output で再分類。旧分類は amendment メタとして attempt 内に保持。
2. 各スロットの final を「最初の非 supplement attempt を採用」(v2 §3.4 と同じ凍結規則)
   で再導出。全 attempt (retry 上限 3 本) が supplement のときのみ unfilled。attempt が
   3 本未満で全部 supplement なら final を書かない (再走が続きを呼ぶ)。
3. 変更差分の全量を amendment 台帳 JSON に記録する。

再現: python3 orchestrator/campaign/s6_amendment_20260713_fence.py
(冪等 — 再分類済み attempt はスキップ)
"""
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from .s6_proposal_rounds import (  # noqa: E402
    RUNS, MAX_RETRY, classify_proposer_output)


AMENDMENT_ID = "2026-07-13-fence"
LEDGER_PATH = RUNS.parent / f"amendment-{AMENDMENT_ID.replace('-fence', '')}-fence.json"


def body_from_raw(raw: dict) -> str:
    try:
        return json.loads(raw["stdout"]).get("result", "")
    except (json.JSONDecodeError, ValueError):
        return raw.get("stdout", "")


def main() -> None:
    attempt_changes, final_changes = [], []
    slots = sorted({f.name.split(".")[0] for f in RUNS.glob("*.attempt*.json")})

    for slot in slots:
        attempts = []
        for retry in range(MAX_RETRY + 1):
            ap = RUNS / f"{slot}.attempt{retry}.json"
            if not ap.exists():
                attempts.append(None)
                continue
            a = json.loads(ap.read_text())
            raw = a.get("raw")
            if raw is None or raw.get("returncode") != 0:
                attempts.append(a)  # api-error は再分類対象外 (raw 由来でない分類)
                continue
            old_cls, old_detail = a["classification"], a["detail"]
            new_cls, new_detail = classify_proposer_output(body_from_raw(raw))
            if (new_cls, ) != (old_cls, ) or new_detail != old_detail:
                a["classification"], a["detail"] = new_cls, new_detail
                a["amendment"] = {"id": AMENDMENT_ID,
                                  "old_classification": old_cls,
                                  "old_detail_reason": old_detail.get("reason")}
                ap.write_text(json.dumps(a, ensure_ascii=False, indent=1))
                attempt_changes.append({"file": ap.name, "old": old_cls, "new": new_cls})
            attempts.append(a)

        # final 再導出 (凍結規則: 最初の非 supplement を採用)
        fp = RUNS / f"{slot}.final.json"
        old_final = json.loads(fp.read_text()) if fp.exists() else None
        outcome = None
        for a in attempts:
            if a is not None and a["classification"] != "supplement":
                outcome = a
                break
        if outcome is None:
            if all(a is not None for a in attempts):  # retry 上限まで全滅
                outcome = {"classification": "unfilled",
                           "detail": {"reason": f"supplement-retry-exhausted({MAX_RETRY})"}}
            else:  # 未消化 retry あり → final を書かず再走に委ねる
                if old_final is not None:
                    fp.unlink()
                    final_changes.append({"slot": slot,
                                          "old": old_final["classification"],
                                          "new": None})
                continue
        outcome = dict(outcome)
        outcome["amendment"] = {"id": AMENDMENT_ID}
        new_txt = json.dumps(outcome, ensure_ascii=False, indent=1)
        if old_final is None or json.dumps(old_final, ensure_ascii=False, indent=1) != new_txt:
            fp.write_text(new_txt)
            final_changes.append({
                "slot": slot,
                "old": old_final["classification"] if old_final else None,
                "new": outcome["classification"]})

    ledger = {
        "what": "フェンス欠陥 amendment の全変更差分 (追加 LLM 呼び出しゼロの機械再分類)",
        "amendment_id": AMENDMENT_ID,
        "user_ruling": "A: 修正 + 再分類 + 続きから再走 (2026-07-13、AskUserQuestion 裁定)",
        "pre_amendment_snapshot_commit": "d6895d3",
        "rule": "最初の非 supplement attempt を採用 (v2 §3.4 の凍結規則の機械再適用)",
        "attempt_changes": attempt_changes,
        "final_changes": final_changes,
    }
    LEDGER_PATH.write_text(json.dumps(ledger, ensure_ascii=False, indent=1))
    print(f"attempt 変更 {len(attempt_changes)} 件 / final 変更 {len(final_changes)} 件")
    for c in attempt_changes:
        print(f"  {c['file']}: {c['old']} -> {c['new']}")
    for c in final_changes:
        print(f"  final {c['slot']}: {c['old']} -> {c['new']}")
    print(f"台帳: {LEDGER_PATH}")


if __name__ == "__main__":
    main()
