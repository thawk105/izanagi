# 段 4 裁定 — [T-2807] B-8 発効 → 校正 → 本走 (2026-09-21 JST、親)

入力: `s1-brief.md` (P1〜P7)、段 3 相談 `codex/s3-consult.md` (gpt-6-astra consult sol/medium、read-only、rc=0、check_codex_output OK)。
裁定 inbox 再走査: 第 28 回控え (08:20、`2026-09-21-rulings-full28-verdicts.md`) は T-2807 に触れない。承認済み裁定 D2194 項 1 を止める新事実は無い。

## 所見の裁定

| # | 所見 | real / refuted | 採否 | 処置 |
|---|---|---|---|---|
| H1 | P7: 未完走を一律 reverify にすると「保全済み・verifier 未開始」の枠を回復できない (runner:694-726 の resume 経路) | real | 採用 | 本走の未完走は 2 分岐。(i) 保全済み・verifier 未開始 → 元の `verify` argv に `--resume` (初回 verifier 1800 s、bench 不変)。(ii) verifier 起動済み・operational 未完走 (bench 完走・保全完了・identity 一致) → `reverify --rep-dir <run/verify/<wl>-j<n>/rep-R/attempt-1>` を 1 回 (3600 s、`--output-dir` / `--third-party-cache` は渡さない)。anomaly / 非 serializable の枠・bench 失敗・保全未完了は再検証せず開示 |
| M1 | P2: 3 commit の役割が曖昧 (承認記録 ≠ 承認対象) | real | 採用 | bundle `effective` 節の field を役割別に: `approval_record_commit` (3016f22ee、裁定の記録) / `decision_numbering_fold_commit` (2afb39768) / `approval_target_snapshot_main` (285477c00) + `approval_target` = 「提示 snapshot 内の試走 insight §7.1・発効束 draft・事前登録 v1 とその実値」 |
| M2 | P3: 「1 値も変えない」は文字どおりでない (status は置換) | real (表現) | 採用 | 「実験構成の既存値は不変、`status` は置換、`effective` 節を追加」と書く。JSON 外の発効束項目は README で試走 insight §7.1 との対応を明示 |
| M3 | P6: F 上限 2400 は watchdog でない、count / preserve に deadline 無し | real | 採用 | 上限式は予約の妥当性を見る見積式として使い、count / preserve の採用値・倍率・余裕を記録。「厳密な上限保証」と書かない。runner は改修しない |
| M4 | P4: 探索範囲 (`calib/*/calib.json`、`verify/*/rep-*`、`rglob('job-*.json')`) に退避物・別 cohort が入りうる | real (経路) | 採用 (手順) | `run/` は本 cohort の正規成果物だけ。退避・複製・別 cohort は `run/` の外。開始済みの失敗走の record は除去しない |
| M5 | 本走前の記録・費用照合の不足 (§12 後段、§7) | real | 採用 | 本走前に insight へ: 校正 6 行 (打切り行含む)、extime、B(E)、stage_B_allowed、本走 walltime の倍率と上限式、保全容量見積り (校正 manifest)、保全先の空き容量 (`df`)。最終費用は dispatch Elapse の和で照合し、runner の `consumed_job_wall_s` は暫定値として別記 |
| M6 | P5: 同 SHA だけでは再利用可否を決められない | real | 採用 | 本走は新しい submit-tree 3 本 (発効 SHA を明示) + 校正 3 本の再利用。再利用前に request 終端 (`.done`・dispatch receipt)・木の clean・HEAD == 発効 SHA・orphan hold 無しを確認。hold があれば別木で迂回しない |
| L1 | P1 (README stale 注記) | 攻撃不成立 | P1 維持 | README に「旧仕分け (2) に代えて独立 process の自己シードを要件として認める。seed 値・乱数列の独立性は検証していない」と明記し発効記録を指す |
| L2 | 固定 checkout・履歴保持 | 攻撃不成立 | 維持 | submit-tree は明示 SHA で作る (mk-submit-trees.sh は SHA 引数、作成済み)。land は通常 merge + ff-only、rebase / squash / cherry-pick を使わない |
| — | summarize の SHA policy | (相談の注意) | 採用 | `summarize --accept-ruling-sha 6ccb18c7… --accept-bundle-sha <発効束 sha>` を各 1 値で明示 |

## plan v2 (確定)

1. 発効 commit (docs のみ): `output/insights/2026-09-21/t2807-b8-effective/README.md` + `verbatim/b8-effective-bundle.json` (M1・M2 の field) + `docs/paper-story/README.md` stale 注記の項目 3 (L1)。`python3 tools/check_docs.py` 緑、provenance trailer。
2. submit-tree c1〜c3 を発効 SHA から作成 (mk-submit-trees.sh)、HEAD == 発効 SHA・clean を確認。
3. 校正 3 job を並行投入 (launch-calib-*.sh、walltime 03:30:00)。launcher が投入直前に runner / 規則 file の sha256 を照合。
4. 校正終端 → `summarize` (accept sha 明示) → M5 の本走前記録 → stage_B_allowed なら本走 6 job (c1〜c3 再利用は M6 の確認後、c4〜c6 新規)。本走 walltime は校正実測の最大所要 × 倍率 (M3 の見積式を記録)。
5. 本走終端 → 未完走は H1 の 2 分岐 → `summarize` の 3 値判定 → results 稿・README stale 注記更新・insight §3〜§6・決定 fragment・worklog fragment。
6. 段 6 read-only レビュー 1 本 (results 稿・insight を一次 record と照合)、受入全走、段 7〜9。

## 変異 matrix

実装面 (D95 決定 2) の差分ゼロ → 免除 (DW-S04)。受入全走は免除しない。
