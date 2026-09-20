# [T-2501] 「exploration」(campaign の use class) と「探索」(D1813 の標本帰属) の語の整理 — runbook §7.9 と glossary 1 項目の記録 (2026-09-20)

- authority: none
- default_effect: no-state-change
- 裁定: D1879 (2026-09-09、探索走 T-2418 が範囲外として返した 4 件のうち「語の整理だけ」を実施。working bytes 拘束と
  `run_kind == "extended"` 必須化は採らない)。依頼文の逐語は `verbatim/T-2501-origin.md`。
- **本 wave は docs 2 file (`docs/pegasus-runbook.md` の `### 7.9` 新設 + §8 の 1 句、`docs/glossary.md` §4 の 1 項目) だけを変えた。
  実装面の差分はゼロ (変異 matrix 免除、DW-S04)。** 凍結成果物・正式 consumer の受理集合・`run_kind`・コードには触れていない。
  D1859 の射程は広げていない。gate・検査・台帳・一般化は足していない。
- 一次資料 (事実の出所): `orchestrator/campaign/layout.py` (use class と 2 つの出力 root 環境変数の解決規則)、
  `orchestrator/campaign/backoff_extended_sweep.py` (RUN_KIND 3 値と `declared_use_class = official`)、
  `orchestrator/campaign/b10_backoff_static_tail_formal.py` (`--explore-campaign` の mode 検査)、
  `tools/pegasus/b10_backoff_grid.sh` / `paper_story_a1_paired.sh` / `submit_b10_backoff_grid.sh`、
  D1813 / D1848 / D1879 / D123 / D158 / D528、`output/insights/2026-09-09_t2418-backoff-static-explore/README.md` §5 / §10、
  `docs/b10-backoff-static-tail-preregistration.md` §2.1、`docs/b10-backoff-static-tail-submission.md`。grep の逐語は
  `verbatim/parent-measurements.md`。

## 1. 結論 (1 行ずつ)

1. **同じ「探索」が 2 つの別物を指していた。** 語 A = campaign layout の use class `exploration` (`declared_use_class`、閉表 4 値、
   出力先の namespace と解決規則を決める。`IZANAGI_EXPLORATION_OUTPUT_ROOT` はこの語)。語 B = D1813 の測定段階「探索」
   (静的 backoff 1000 マイクロ秒超の 2 段構成の第 1 段、探索値は正式標本へ混ぜず開示だけする。`run_kind = t2418-explore`)。
2. **語 B の探索走は語 A では `official` である。** `backoff_extended_sweep.py` は `declared_use_class="official"` を渡し、job 本体
   `b10_backoff_grid.sh` は `IZANAGI_OFFICIAL_OUTPUT_ROOT` を export する。exploration root へは移していない (D1848 却下肢 3)。
3. **語 A の `exploration` は「非正式な標本」を意味しない。** A-1 対測定 `paper_story_a1_paired.py` は `DECLARED_USE_CLASS = "exploration"`
   を宣言し、job script は `IZANAGI_EXPLORATION_OUTPUT_ROOT` を export する。標本の帰属はこの宣言では決まらない (A-1 の標本が正式か否かは
   本 wave では判定しない)。
4. **第 3 の表記が 2 つある。** `submit_b10_backoff_grid.sh --explore-campaign` (`t2500-tail-formal` 限定) は語 B の探索走の campaign directory を
   指し、`b10_backoff_static_tail_formal.py` の検査文言 `mode source must be exploration` は `run_kind == "t2418-explore"` の要求 (語 B)。
   `layout.py` の `ExplorationCampaignLayout` の docstring「探索専用 layout」は語 A。
5. 上記を runbook `### 7.9` (定義 A / 定義 B / 第 3 の表記 / 対応表 5 行 / 読み分け) と glossary §4 の 1 項目 (機体固有値なし、対応表は runbook へ委譲) に書いた。

## 2. 段構成と実行 (時刻は `date` / mtime / commit 日時)

- 起点 local main: worktree 作成時 `7baf3f375` → 開始 gate 直前に main が 7 commit 進んでいたため ff-only で `f94b61fc8` に揃え、
  開始 gate (`check_wave_startup.py --mode fresh --external-handoff`) rc=0 (20:53:36 JST、`verbatim/startup-gate.log`)。
  submodule は `dev_wave_submodule_init.py` rc=0、`submodule status --recursive` 3 行とも初期化済み。
- 段 1 brief (`verbatim/brief.md`) → 条件表 08/09/10/11/13 の再評価は全て不成立 → 段 2・3 は軽量版で省略 (設計択一が割れず、正しさ防壁に
  触れず、受理集合も変わらない) → 段 4 裁定 (`verbatim/adjudication.md`、裁定 inbox の再走査で本件の更新なし) → 段 5 は親が docs を起草
  (実装面 0 につき実装子なし) → commit 1 `a9ca20cbe` (21:04:51 JST、`verbatim/commit-1.patch.txt`) → 段 6 read-only codex review 1 本
  (2 レンズを 1 本で) → must-fix 1 / should 4 を是正案の逐語で反映 → commit 2 `31b5271e0` (21:17:04 JST、`verbatim/fix-1.patch.txt`) → 段 7 (本 README、
  worklog fragment) → 受入全走 → 段 8 → 段 9 land。
- **注記 (時刻の誤記):** `verbatim/brief.md` の見出しの「21:05 JST」と `verbatim/adjudication.md` の「21:12 JST」は、書いた時点の推定値であり
  実測ではない。実際にはどちらも commit 1 (21:04:51) より前に書かれている (brief は開始 gate 20:53:36 の後)。逐語は改変せず、ここで訂正する。

## 3. 段 6 レビュー (read-only codex、gpt-6-astra / medium、1 attempt、7 model call、289 秒、受理 `check_codex_output.py` OK)

prompt は `verbatim/prompt-review.md`、出力の逐語は `verbatim/out-review.md`。所見 7 件 = **must-fix 1 / should 4 / nit 1 / 記録 1、refuted 0**。
裁定 (親) と反映:

| 所見 | 主張 | 裁定 | 反映 |
|---|---|---|---|
| R-1 (must-fix) | `IZANAGI_EXPLORATION_OUTPUT_ROOT` の process pin を「全解決経路」に広げて書いた。`layout.py` の `_resolve_exploration_output_root` は env 経路だけ pin し、明示引数と repo 既定は対象でない | real、採用 | runbook §7.9 の該当文を是正案の逐語で置換 |
| R-2 (should) | 対応表の env cell「exploration だけ base を差し替えられる」は限定先が曖昧 (official も明示引数と env で base を指定できる) | real、採用 | 「この env は exploration の base 解決に使い、official の base 解決には使わない」へ |
| R-3 (should) | 「code 中の『探索』は語 A」は 2 つの docstring の観察から code 全体へ一般化している (formal driver の検査文言は語 B) | real、採用 | 「この 2 つの docstring 中の『探索』は語 A」へ限定 |
| R-4 (should) | 「直交性」行の双方向の非含意は、現行実装の具体的対応 (`t2418-explore` → `official`) と食い違う | real、採用 | 行を「読み違えない点」(宣言だけでは帰属は決まらない / 探索走を exploration use class と読み替えない) へ |
| R-5 (should) | glossary の namespace を `output/…` 固定で書き、語 B を「任意の 2 段測定の第 1 段」に広げている | real、採用 | `<base>/exploration/campaigns/<id>/` + base 既定 `output/`、語 B を静的 backoff 1000 マイクロ秒超に限定 |
| R-6 (nit) | brief の「省略時 repo 既定 `output/exploration/`」は base と namespace 付加後の path の取り違え (runbook 本文は正しい) | real、記録のみ | brief は逐語記録なので改変しない。正しくは base が `output/`、layout がその下に `exploration/campaigns/<id>/` を付ける |
| R-7 (記録) | brief の「runbook / glossary は構造 lint のみ、束縛なし」は限られた grep からの全称断定 | real、記録のみ | 射程を本 README §4 に書き直す (下記) |

fix は 5 件とも是正案の逐語をそのまま当て、差分 (`verbatim/fix-1.patch.txt`、6 行追加 / 5 行削除) が是正案と一致することを親が目視で照合した。
codex の焦点再レビューは投じていない (逐語適用で新しい判断を含まないため)。

## 4. 検査

- `tools/check_docs.py`: commit 1 前・fix 後とも「違反なし」rc=0 (login 実行は runbook §7.0 の暫定例外)。`git diff --check` 空。
- `tools/check_ai_provenance.py --message-file`: commit 1・2 とも rc=0。全史監査 (commit 1 後): 12061 件、新規違反なし、rc=0 (21:06:04 JST)。
  記録 commit 後にもう一度走らせる (結果は worklog)。
- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、21:12:23 JST): conjunction hit は既知 4 file
  (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/{journal.jsonl,manifest.json,result.json}`、
  `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`) だけで、本 wave の file は含まれない。positive_control の hit_count は 233 (> 0)。
  走査 report 自体は三軸語を含むため insight へ写していない (F1013 型の回避)。
- runbook / glossary への束縛の射程 (R-7 の是正): 射影した grep の範囲 (`orchestrator/campaign/*.py`・`tools/*.py`・`hooks/*.py` で
  `pegasus-runbook` / `glossary` を検索、`orchestrator/tests/`・`tools/`・`hooks/` で §8 の該当文言を検索) では、runbook の参照は
  `tools/check_docs.py` (§7.0 の dispatch inventory 表と living docs の構造 lint) だけ、glossary の参照は `tools/check_docs.py` と
  `hooks/guard_read.py` のコメントだけ、該当 checklist 文言の一致は 0 件。glossary を含む全参照・間接束縛の不存在までは確認していない。
  提示した差分は runbook / glossary の説明文の追加だけである。
- 受入全走・land: 実測前なので本 README には書かない (結果は worklog entry と land の受領証)。

## 5. 限界・言わないこと

- 各 producer が実行時に `run_campaign` へ渡す値は静的 grep で確認しただけで、実行経路は測っていない。
- A-1 対測定の標本が「正式」か否か、`docs/b10-backoff-static-tail-preregistration.md` の第 2 段が投入済みか否かは判定しない。
- 語の整理は読み手の誤解を消すだけで、機械可読な区別は既に D1848 が成果物へ載せた `declared_use_class` field が担う。本 wave は field も
  consumer も変えていない。
- glossary 項目は近傍項目より長い (field 名・裁定番号が多い)。詳細は runbook §7.9 へ委ねる導線を持つ。

## 6. verbatim 一覧

- `verbatim/T-2501-origin.md` — 依頼文と起票行の逐語
- `verbatim/brief.md` / `verbatim/adjudication.md` — 段 1 brief / 段 4 裁定 (handoff からの逐語。時刻の誤記は §2 の注記)
- `verbatim/parent-measurements.md` — 親の grep 実測の逐語
- `verbatim/startup-gate.log` — 開始 gate の出力
- `verbatim/commit-1.patch.txt` — commit 1 の差分 (§7.9 新設 + §8 の 1 句 + glossary 1 項目)
- `verbatim/prompt-review.md` / `verbatim/out-review.md` — 段 6 レビューの prompt と出力の逐語
- `verbatim/fix-1.patch.txt` — R-1〜R-5 の反映差分

## 7. 工数

- codex 1 本 (review、7 model call、289 秒、gpt-6-astra / medium)。計算ノード job = 受入全走のみ (段 9 の記録に書く)。
