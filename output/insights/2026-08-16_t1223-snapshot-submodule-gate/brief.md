# [T-1223] 段 1 brief — verify_snapshot の submodule 未初期化 fail-open を塞ぐ

## scope

`tools/codex_reasoning_ab.py` の `verify_snapshot` が、既定 spec 経路で submodule の初期化状態を
一切要求しないために、未初期化 snapshot を reason 0 件で受理する穴を塞ぐ。**受理集合は狭める側のみ。**
実装面は同 file と `orchestrator/tests/test_codex_reasoning_ab.py` に限る。

## 実アンカー (分類文を置かない)

- `tools/codex_reasoning_ab.py:695` `_snapshot_spec(case)` — 返す key は
  case / head / branch / tracked_paths / hashes / numstat / untracked / modes / forbidden の 9 個。
  submodule 系の key を 1 つも返さない。
- `tools/codex_reasoning_ab.py:1693-1700` — `expected.get("submodule_manifest_sha256")` が
  `None` のとき照合節を丸ごと飛ばす。既定 spec では常に `None`。
- `tools/codex_reasoning_ab.py:1685-1692` — `enforce_closure` の真偽に関わらず
  `submodule_manifest` は必ず得られ、`_submodule_manifest_sha256` も必ず計算される。
- `tools/codex_reasoning_ab.py:915-981` `_submodule_worktree_state` — 返す state は
  `"initialized"` と `"uninitialized"` の 2 値のみ。gitlink 不一致・検査不能は例外。
- `tools/codex_reasoning_ab.py:984-1037` `_submodule_inventory` — 行は
  path / gitlink_commit / initialization の 3 field。`initialized` の行だけ再帰する。
- 既定 spec 経路の caller: `1508`、`2210`、`2371`、`4885` (replay)、`5561` (CLI)。
  pin 済み spec 経路は `2475-2478` (`_assert_submodule_manifest_sha256`) と
  `3869-3911` (POS/NEG 突合)。後者 2 つは本 wave で触らない。

## 確定済みユーザー裁定・先行裁定

- 起票元は worklog entry 591 の scope 外 real 所見 (worklog.md:1157-1163)。「本 wave が作った穴ではない」。
- 当該機構 (`submodule_manifest_sha256` / submodule 初期化) の**見送り裁定は不在**。
  worklog・worklog-archive・decisions を機構名で検索して 0 件 (起票元の 1 件を除く)。
- 規律 2 (正しさゲートを緩める変異を許さない) の面。fail-open を fail-closed へ寄せる方向のみ。

## 不変条件 (破ったら停止)

1. **受理集合は狭めるだけ。** 現在 reject される入力を新たに accept してはならない。
2. **oracle document に key を足さない。** `verify_snapshot` の戻り値 dict の field 集合が変わると
   `manifest_sha256` が動き、`4877` の slot 突合・replay・過去 run artifact の照合が壊れる。
   検出は `reasons` への追加だけで行う (DW-O09 の pin 閉包を動かさないための設計拘束)。
   pin 閉包の実測: `tools/codex_reasoning_ab.py` の bytes を pin する台帳・trust root は
   `grep -rln "codex_reasoning_ab" --include=*.py orchestrator/ tools/ hooks/` で 8 file、
   いずれも source hash pin ではない (provenance checker・hold 台帳・serial node 一覧・自テスト)。
3. **`_git_closure_reasons` / `_submodule_inventory` の受理集合を変えない。**
   `test_uninitialized_nested_submodule_is_manifested_and_accepted` (test:2004) は
   「未初期化 nested submodule を manifest へ正直に記録し closure reason 0 件」を意図的に主張する。
   本 wave は verifier 層だけを締め、manifest 層の正直さは温存する。
4. 新規テストは**実 repo を clone しない**。`benchmark_snapshots` fixture (test:351) は
   real repo 由来で成長比例、当該 file の 16 node は既に恒久保留 (growth_test_holds.py:100-115)。
   新規テストは `_synthetic_nested_submodule_snapshot` (test:1930 近傍) 型の合成 repo + 独自 spec で書く。
5. トレース・性能計測ビルドには触れない (該当なし)。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 既定の要求は「深さ 1 の submodule が `initialized` であること」に限る。**
  全深度 initialized を要求すると、標準 worktree 手順 (DW-O20 = `git submodule update --init`、
  非再帰) で作った作業木を source にした snapshot が壊れる。本 worktree で
  `--init --recursive` を実行したところ `external/ccbench/third_party/shirakami` と
  その配下 `third_party/googletest` を新規 clone した (= 深さ 2 以降は標準手順では未初期化)。
  `_init_submodules_from_local_source` (715-762) は source で initialized な submodule だけを
  snapshot 側で init するので、この未初期化は snapshot へそのまま伝播する。
  **深さ 1 だけを要求するのが「production を壊さずに受理集合を狭める」最大幅**というのが親の読み。
  対案 (a) 全深度要求、(b) 既定 spec に `submodule_manifest_sha256` の実値を pin (CCBench pin 更新で
  毎回腐る)、(c) 初期化ベクタを spec の allowlist で表す。攻撃せよ。
- **(P2) 実装形は `expected` の新 key (例 `require_initialized_depth` 相当) を
  `_snapshot_spec` が返し、`verify_snapshot` が reason を積む形。** spec 未指定 (caller が
  独自 spec を渡す既存テスト) では従来どおり無効化されうるので、**既定値は spec 側でなく
  `verify_snapshot` 側の `expected.get(..., <fail-closed 既定>)` に置く**こと。
  `spec=` を渡す既存経路 (test:1228) が黙って緩まないかを攻撃せよ。
- **(P3) 変更面は `tools/codex_reasoning_ab.py` 1 file + テスト 1 file。** 分割せず実装子 1 本。

## 純増検出力 (性質で検索した既存被覆)

- 既存: POS/NEG の初期化状態**差**の検出 (`3905-3911`)、schedule 済み slot の
  manifest sha 突合 (`2476`)、pin 済み nested gitlink の変更検出 (test:2086)、
  closure 層での uninitialized の**記録** (test:2004)。
- **不在**: 単一 snapshot を既定 spec で検証したとき、submodule が未初期化であることを
  理由に reject する経路。純増検出力はこの 1 点に限る。

## 成果物影響 (DW-G05)

未実装なら、A/B 実験の oracle が「CCBench 実体を持たない snapshot」を正規と認定しうる。
その snapshot 上で走った試行の prompt 入力・rollout は材料レポートと proof chain に
「pin 済みの木で得た」として載るが、実際には pin された tracked 内容の一部が不在であり、
certified 選択の根拠となる試行台帳の同一性主張が偽になる。

## 成果物の形

- `tools/codex_reasoning_ab.py` の verifier 層に fail-closed 検査 1 つ。
- 合成 repo による負例 (未初期化 → reject) と正例 (初期化済み → 従来どおり accept) のテスト。
- 変異 matrix (段 6)、受入全走、worklog/decisions fragment。

## 受入・実測環境

Pegasus login node (worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1223-snapshot-submodule-gate`)。
受入全走は `tools/run_tests.py` の受入形を lease 取得後に背景投入する。
変異 runner は dispatch recipe (`--force-dispatch` 必須)。
