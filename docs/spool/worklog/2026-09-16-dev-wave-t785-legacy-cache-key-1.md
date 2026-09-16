---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t785-legacy-cache-key
seq: 1
title: [T-785] legacy cache_key の既定 toolchain 省略による偽 hit を production build() で実測再現し、省略条件を歴史的既定の literal 組へ切り離した (コード + テスト、branch worktree-dev-wave-t785-legacy-cache-key、変異 matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- 起点はユーザー依頼 (台帳 [T-785]、P2・B 系)。「まず偽 hit を実際に再現してから直す」「床値の build_v2 へ広げない」「仮想リスク向けの gate・検査・台帳・一般化は scope 外」を確定裁定として brief に固定した。
- 一次資料 = `output/insights/2026-09-16/t785-legacy-cache-key/README.md` (段 1〜6 の逐語、probe JSON 7 本、変異 spec と台帳を同 dir に収録)。実装 commit `6022f70d7` (`buildcache.py` の `tc` 行 1 行 + docstring 3 行、`test_campaign.py` へ回帰テスト 1 本)。
- 再現 (修正前、base `0c292eff6`): Pegasus login node で、実 ccbench checkout の source evidence と stock admission を用い、cmake 実行を極小 C++ ELF の生成に置き換えた production legacy `build()` probe (repo 外、Codex `role=author` 作、sha256 `5bc493ec…`) を実走した。`silo|BACK_OFF=1`・`trace=False` で、既定を gcc-12/g++-12 から gcc/g++ (11.4) へ替え、receipt が一致する条件で、旧 compiler 製 ELF への偽 hit (同一 key `silo_fed9a86c14_t0`、`cached=true`、cmake 呼出 0、binary sha 同一、configure argv は `g++` なのに `.comment` は GCC 12.3.0) を確認した。修正後 (`6022f70d7`) は同条件で key が分離し (`silo_6c154d405d_t0` → `silo_f368efad6c_t0`)、`cached=false`、g++ 11.4 で再生成された。
- 衝突は receipt に入る `source_bytes_sha256` (要求 compiler の前処理出力 digest) が compiler 間で一致するときだけ起きる。`clang++` は不一致で衝突しない。「既定変更で必ず偽 hit」ではない。
- 段 3 で brief の誤りを 3 件訂正 (real): pipeline の legacy 分岐 (`pipeline.py:2002`) は cc/cxx を省略し、compiler 入りの `common` は build_v2 分岐だけが使う / `s1_verify_extime_calibration.py:390` は generator receipt 付きの生成物 build で stock control ではない / `between_run_floor.py:316-324` は Pegasus 分岐だけ site 解決を明示する。修正は caller を変更しない。「T-785 に起因すると確認された研究停止は提示資料に無い」に限定 (研究停止一般の否定ではない)。
- 到達範囲の限定: 各 CLI 全体の実走、`trace=True`、生成物 admission、実 CCBench binary の build・実行・性能値・certified 選択は確認していない。要求名が同じまま実体・版が替わる場合は legacy key の対象外のまま (build_v2 は toolchain manifest で保護済み)。s1/s2/s3/s5 と非 Pegasus の `between_run_floor` は evidence 側に独立の `"g++-13"` 既定を持ち、本 wave は触っていない。
- 段 3 敵対相談 2 本 (sol 4 件・luna 8 件、MUST 5 件はすべて手順・記録側で採用、S-3 は scope 縮小で不要化)。段 6 敵対レビュー 2 本: MUST 0、SHOULD 1 (RA-1: 新規テストは cc/cxx を同時に変えるため cxx だけの片側比較へ退行しても緑。cc だけは既存テストが捕まえる) = real・不採用 (成果物影響が仮想、`DW-G05` と依頼の scope)、NIT 1 (RB-1 記録文言の限定) = 採用。fix 子なし。
- 変異 matrix (計算ノード dispatch、`repo_head=6022f70d7`、4 node 走行): baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致。M2 (常に suffix) は 4 node 外の `test_p3_s4_loop_sort.py::test_sort_contract_none_preserves_preexisting_identities` も破る (レビュー A の静的判定) ので、完全集合は 4 node 走行に限った記録。
- 焦点走: `test_campaign.py` の 4 node (新規 1 + 既存 cache_key 2 + golden 1) 計算ノード `1600.nqsv` で 4 passed。provenance 全史監査は新規違反なし。受入全走は本 fragment の後に最終 tip で 1 回投入する (結果は land 時の受領証)。
- 工数: codex 子 6 本 (plan 1・consult 2・author 2・review 2 のうち author は probe と修正で 2、fix 0)。段 5 の probe 子は 1 往復で完成、修正子は直接呼出で M1 の赤化まで自己確認して戻った。

## 次の一手差分

### 完了

- [T-785] legacy `cache_key` の既定 toolchain 省略を歴史的既定の literal 組へ切り離した (`6022f70d7`)。偽 hit の再現と修正後の miss は `output/insights/2026-09-16/t785-legacy-cache-key/` の probe JSON が一次資料。caller・build_v2・hit 時検査は不変。
  remaining: none
  base: ce9c78320f42d6e05c3c71e4f5f1bff7cf1ca89ac9e274542efd65bdd7058f0f

### 新規

- {{T:cache-key-one-sided-toolchain-coverage}} **P3・新規 (B 系)**: [T-785] の回帰テストは cc/cxx を同時に変えるため、`cache_key` の省略条件が `cxx == "g++-13"` だけの片側比較へ退行しても緑になる (cc だけの片側は既存 `test_cache_key_separates_compiler_request_name` が捕まえる)。同テストへ歴史的組から cc だけ・cxx だけ変えた入力を足せば閉じる (段 6 レビュー A の RA-1、成果物影響は仮想のため本 wave では不採用)。
