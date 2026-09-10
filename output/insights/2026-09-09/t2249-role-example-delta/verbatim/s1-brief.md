# 段 1 brief — [T-2249] role 入力例に残る `delta_pct: -1.2` の是正

## 研究前進

進む主張は Phase 3 段 4 の「planner/coder は勝ち筋チャネル (性能値) を見ずに合成する」という
リーク制御の主張である。この主張の因果入力は role 定義そのもので、`planner-v4.md` の bytes は
`orchestrator/campaign/p3_autonomous_workload_trial.py` の `ROLE_FILES["planner"]` として毎試行の
journal へ `provenance/role_file_sha256` で記録される。現行の入力例は、loop が
`WhiteboardLeakError` で塞いでいる性能変化率をそのまま role に見せている。止めている研究は、
次に走らせる K0/K1 対照アームで「role へ渡した契約文が段 4 の不変と一致する」と言えないこと。
最小差分は 2 file の入力例 1 行ずつと、その bytes を pin する 2 系統の更新。
完了判定は (a) 両 file に `-1.2` が無い、(b) `tools/check_codex_agents.py` rc=0、
(c) 受入全走緑、(d) 変異 matrix の期待 node 完全一致。

## scope (本題のみ)

1. `.claude/agents/coder-v4-autonomous.md:47` の `"delta_pct": -1.2` → `null`。
   兄弟 `-sort` / `-trigger-gating` の同行と byte 一致させる (K0/K1 対照の対称性維持)。
2. `.claude/agents/planner-v4.md:35` の `"last_delta_pct": -1.2` 行を削除する (P1)。
3. `orchestrator/codex_roles/review_ledger.py` の `SOURCE_FILE_SHA256` を両 role の新 sha256 へ更新。
4. `.codex/role-adapters/{coder-v4-autonomous,planner-v4}.json` を `spec.expected_adapters()` の
   期待 bytes へ再生成 (埋め込み本文・`source/sha256`・`review_ledger/source_file_sha256`・`semantic_digest`)。

scope 外: D118 残余 (b) の他 2 件 (planner の「leading-indicators だけ」、coder の「入力は 5 field のみ」)、
whiteboard 例の field 数拡張、gate・検査・台帳・一般化の新設、`p3_s4_loop.py` の変更。

## (P1) 親の provisional 裁定 — 攻撃対象

**(P1) `planner-v4.md` の `last_delta_pct` は「行削除」とする。** 根拠: D118 残余 (b) が
「存在しない `last_delta_pct`」と名指ししており、`git grep last_delta_pct` の hit は
role md・adapter・decisions.md だけで、どの射影経路も生成しない。`null` へ替えると存在しない
field が例に残る。対抗案は (a) `null` へ替える、(b) planner は scope 外にする
(`WhiteboardLeakError` は whiteboard 射影経路の `delta_pct` field だけの防壁であり
`current_perf.last_delta_pct` は D118 決定 (3) の防壁対象外、という読み)。

## 不変条件

- 規律 2 を緩めない。`p3_s4_loop.py` の `_DELTA_PCT_LIVE=False` と二重 fail-closed は不変。
- 凍結成果物の bytes を変えない。`test_reflux_originless_compatibility.py` の凍結 baseline が
  持つ planner sha は `journals/*/*/provenance/role_file_sha256` = `output/` 保存済み journal 内の値で、
  role file 編集では動かない。`FROZEN_MANIFEST` に対象 2 file は無い。
- frontmatter (description / model / effort / tools) を変えない → `DESCRIPTION_SHA256` と
  `ROLE_MANIFEST_SHA256` は不変。
- `.codex/role-adapters/*.json` は static-dormant のまま。runtime activation を開かない。
- `tools/check_codex_agents.py --write` を使わない (禁止済み)。

## 成果物の形

wave branch 上の 1 統合 commit (実装面 4 file のうち 3 file が実装面 → Codex `role=author` 必須、D95)、
変異 matrix 記録、insight dir、spool fragment (worklog / decisions)。

## 並列分割方針

**分割しない。Codex 実装子 1 本。** `review_ledger.py` の sha は md の bytes に依存し、adapter は
その両方に依存する直列依存で、並列所有を分けられない。段 2 プラン 1 本、段 3 敵対相談 2 本
(異なるレンズ)、段 6 レビュー 2 本 + fix。

## 受入・実測環境

login node で `tools/dev_wave_wait.py acceptance` の全走。計算ノード job は不要 (実測を伴わない)。
