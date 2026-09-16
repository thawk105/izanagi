# 段 4 裁定 追補 3 (erratum-3) — 行番号 pin の台帳を単位 B へ足す

**正本の関係:** 追補 1・2 に続く。衝突したら**番号の大きい追補が優先**する。

**発生:** 単位 C (Python consumer) は付け替えを完了したが、**親の pin 閉包が取りこぼしていた
台帳テスト 3 node が赤**になった。C はこれを回帰として正直に報告し、期待値を変えずに止めた。
**C の判断は正しい。**

赤の実体 — `orchestrator/tests/test_ccbench_spawn_sites.py`:

1. `test_reviewed_process_launch_inventory_is_recursive_and_exact`
   `:90` が `("campaign/b4_binary_record.py", "<module>.prepare_dependencies"): 2` と
   **subprocess 起動箇所の本数**を固定している。`verify-deps` の呼びが消えたので実際は 1。
2. `test_define_sink_cross_product_has_no_unreviewed_ungated_member`
   `_DEFERRED_GATE_MEMBERS` (`:911-917`) が `sink_lineno = 127` と**行番号**を固定している。
   `_build_with_dependencies` は 118 行へ移動した。
3. `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`
   `:2714-2717` が同じ組を**別の場所にもう一度**書いており、exact 集合比較で 0 件一致になる。

**この赤は実装の回帰ではない。** 台帳が「本数」と「行番号」で固定しており、
段 1 の pin 閉包 (`DW-O09`) が **path 検索でも key 検索でも出ない形**だったために漏れた。

## 追補の決定

### (1) `orchestrator/tests/test_ccbench_spawn_sites.py` を単位 B の所有に足す

B は自分の編集を**全部終えた最後に**この台帳を直す。B 自身の編集で行番号がさらに動く可能性が
あるためである。

### (2) 直し方 — 台帳は「実態に合わせる」だけ。検出力を落とさない

- `prepare_dependencies` の本数を **2 → 1** にする。
- `_build_with_dependencies` の `sink_lineno` を **実測した現行の行番号**にする。
  **推測で書かない。** 現物を読んで確かめた値を入れる。
- 同じ組が 2 箇所 (`:911-917` と `:2714-2717`) にあるので**両方を同じ値に**する。
  片方だけ直すと exact 集合比較で必ず落ちる。
- **entry を消してはならない。** owner (`wave t2636`)、説明文、`sink_kind` (`buildcache`)、
  `sink_scope` は変えない。
- **exact 比較を緩めてはならない。** 「行番号を検査しない」「集合を部分一致にする」
  「entry を allowlist へ逃がす」はいずれも禁止。
- 本数・行番号以外の理由で赤が残るなら、**直さずに報告して止める。**

### (3) この形の pin を段 1 の閉包に含める (段 8 候補)

`DW-O09` の pin 閉包は「path 検索」「key 検索」を指示しているが、
**本数 pin・行番号 pin は成果物 path も key 名も持たない**ので、どちらの検索にも出ない。
本 wave では実装が済んでから実走で初めて出た。
段 1 で「編集する production file を**名前で**参照している test」を引く手順が要る
(`git grep -n "<module 名>" -- orchestrator/tests/`)。

### (4) 期待赤の最終形

B の完了をもって、次がすべて緑でなければならない。残る赤は**回帰**として段 6 の must-fix に上げる。

- 単位 A の期待赤 6 file
- `orchestrator/tests/test_t126_pegasus_tools.py` (追補 2 で B へ移管)
- `orchestrator/tests/test_ccbench_spawn_sites.py` (本追補で B へ追加)
