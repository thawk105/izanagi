# 親が実測した証拠 (段 3 の材料)

すべて親が現物から取った。推測は「推測」と明記してある。

## 1. 合成監査の検出実績 (母集合と除外を明記する)

母集合: `docs/archive/worklog-phase3-*.md` のうち「合成監査」を含む 22 file。
`git grep` で tracked file だけを対象にした (worktree のコピーを除外)。
除外: `docs/archive/` 以外の live docs には同語が無い (`docs/decisions.md` 2 件、
`docs/failures.md` 7 件はいずれも規定と事故記録であって走行記録ではない)。

抽出できた走行は 13〜15 回。**うち 8 回が本物の欠陥を検出した。**

| 出典 | 検出物 | 競合 | テスト |
|---|---|---|---|
| 0814-550-0815-553 | 相手の新設失敗経路が共通 attestation 形式を使わず運用 log へ出しうる | なし | 緑 |
| 0816-566-567 (F324) | 呼出し規約を厳しくした側の契約を相手の新規呼出しが満たさない (3 件) | 1 hunk のみ | 緑 |
| 0817-621 | 不変条件テストの競合解消と assert 統合 (落とした assert 0 件) | あり | — |
| 0818-656 | 凍結の不変検査が祖先 commit で永久拒否になる | なし | 緑 |
| 0820-771/772 | main 側 docstring の stale 識別子参照 2 箇所 | なし | 緑 |
| 0823-852-853 (F481) | 相手の認証済み `--ignore` を絞り込みと誤認し stale 検査を毎回無効化 | なし | **緑のまま** |
| 0823-859 | flaky hold の完全集合検査が内部 shard の部分集合を誤認し UsageError | なし | 赤になる |
| 0823-863 | `failure_class` 必須化で旧 schema V1〜V3 receipt が拒否される受理集合の退行 | なし | 緑 |

検出ゼロだった走行 (「変更不要」「是正不要」「破れなし」「危険ゼロ」「欠落ゼロ」):
0816-593 / 0817-637 / 0823-866 / 0824-904 / 0825-906 の 5 件。
outcome を worklog に書いていない走行が 0816-602 (2 本) と 0825-917-918 (1 本)。

**F481 は受入全走でも緑になる。** `docs/failures.md` F481 本文に
「受入全走のたびに stale registry 検査が無効化される。registry が腐っても検出されない」とある。
受入を厚くしても代替できない型が実在する。

## 2. F324 の一次資料 — 監査の真の射程は path でなく識別子の閉包である

出典: `output/insights/2026-08-15_t817-verifier-epoch/verbatim/merge-audit.md` (逐語)

- 競合したのは `orchestrator/campaign/p3_autonomous_workload_trial.py` の 1 本。
- **実際の穴は競合していない別 2 file にあった。**
  `orchestrator/tests/test_p3_autonomous_workload_trial.py:3779` と
  `orchestrator/tests/test_campaign.py:8163`。
- 特定の方法は **`require_admitted_campaign` の全呼出しを AST で数え上げること**。
  結果は「grep 104 textual hits に対し AST の実呼出し 65 件。production 16/16、
  tests 48/49、残る 1 件は purpose 必須を確認する意図的な `TypeError` 負例」。

この事実から親が導いた設計上の帰結 (段 3 で検査せよ):

- `tools/check_ai_provenance.py` の `_message_file_paths` は
  「両親双方と食い違う実装面 path」= 交差集合を返す。**この集合は F324 の穴を含まない。**
  したがって checker の path 集合を監査の探索範囲の上界にしてはならない。
- grep は over-count する (104 対 65)。数え上げの権威は AST である。

## 3. 監査子の工数 (receipt 台帳の実測、n=5)

母集合: `/work/1/SFC/tanab/dev-wave-jobs` 配下の receipt.json のうち、job 名が
merge/audit/s9 系に一致するもの。launcher_error 2 件を除く。
**この母集合は不完全である** — 合成監査の job 名は wave ごとに異なり
(`merge-audit` / `stage9-merge-N` / `s9-merge-verify` / `recovery-merge-synthesis` /
`mid-merge-codex-author`)、機構に安定した識別子が無い。数字は下界として読むこと。

| wave | job | 秒 | model call | 親が渡した射影 | 重複実装面 file |
|---|---|---|---|---|---|
| t1578-t1579-t1431 | stage6-merge-audit-2 | 468 | 28 | diff 2 本 + merged .py 4 本、repo 遮断 | 4 |
| t1636-dangling-argv-batch | merge-audit-1 | 394 | 19 | 無 (repo アクセス可、相手の全 diff を対象) | 0 (交差なし) |
| t1726-freeze-rederive | t1726-s9-merge-audit | 320 | 7 | 無 (repo アクセス可、親が疑い所を 3 点名指し) | 1 |
| t1539-insights-retention | recovery-merge-synthesis | 162 | 10 | — | — |
| paper-story-a1-paired | stage9-merge-3 | 106 | 6 | — | — |

**親の当初仮説「射影を厚くすれば速い」は、この表が反証している。**
射影が最も厚い t1578 が最も遅い。t1726 が最も速いのは、親が
「重複している実装面 file は 1 本である (親がこの範囲で実測済み)」と
**探索範囲を実測で閉じて渡した**からだ、というのが親の現在の解釈である。

これも推測にすぎない。n=5、交絡 (対象 file 数、repo 遮断の有無、wave の複雑さ) が多い。
段 3 はこの解釈自体を検査対象に含めよ。

## 4. 既裁定 (緩めてはならない)

- D697 決定 8 — 両親が同じ実装面 file を変更した main 取り込みでは合成監査を行う
- D554 — 受入 postclaim merge の author 要件は実装面の真の衝突時だけの条件付き昇格
- D770 — 両親が同じ実装面 file を触る取り込みは 2 commit へ分ける
  (authority docs の bytes gate により staged merge のまま子を起動できないため)
- D894 — 合成のみの merge の記録規則
- F504 — 合成監査を commit 前に挟む経路が塞がっていた

## 5. 親が段 2 後に実測した 3 件 (段 3 はこれも検査せよ)

### (a) 実装面の定義は Python より広い

`tools/check_ai_provenance.py:67-78` の定数。
prefix = `orchestrator/`, `tools/`, `hooks/`, `.github/`, `.codex/`, 第三者 submodule tree、
suffix = `.py .sh .bash .c .cc .cpp .cxx .h .hh .hpp .hxx .cmake .patch .diff`、
basename = `CMakeLists.txt`, `Makefile`, `GNUmakefile`, `pyproject.toml`, `pytest.ini`。
Python AST が届くのはこのうち `.py` だけである。

### (b) 全 repo AST 走査は login node の既存作法である (前例あり)

`tools/check_subprocess_bytecode_guard.py` は `orchestrator/` と `tools/` の全 Python を
`ast.parse` する。`scan_repository` は `_scan_file` が tree を返さず、**1 file ずつ parse して
捨てる streaming 形**である。

親の実測 (pegasus02 login node、`--repo .`):
**wall 10.9 秒 / user 9.9 秒 / 最大 RSS 59,908 KB (約 60 MB) / rc=0**

同 script は `tools/pegasus/admission_registry.json` に**登録されていない**。
registry の非 pegasus entry は 58 件中 1 件 (`tools/claude_session_ledger.py`、class=unknown) だけで、
`tools/` の 45 script のうち 44 は未登録のまま login node で常用されている。

`hooks/guard_bash.py:962-987` の `_script_targets` は、`_SANCTIONED_PATHS` に無く registry
entry も無い path を target 集合へ入れない。したがって `tools/pegasus/` 以外の未登録 script は
machine gate に当たらない。`tools/README.md` の分類義務は prompt 規律であり、
同 README 自身が「3 層の外は緑のまま通り」と書いている。

**段 3 への問い:** 段 2 plan は「Pegasus login の実行分類が最大の未解決点」と書いた。
上の実測はこれを弱めるか。新 tool を registry へ `unknown` で登録すると、
比較可能な 44 script のどれにも無い hook 拒否を新設することになるが、それは正しいか。

### (c) 親の probe は streaming ではなかった

親の `probe_ast_cost.py` は 666 file の AST を**同時に保持**して 16 秒だった。
これは (b) の前例より重い形である。**本実装は (b) と同じ streaming 形にすること。**
probe の 16 秒を本 tool の見積りに使ってはならない。
