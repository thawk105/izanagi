# CCBench insight: docs/protocols_en.md の YCSB 対応表が実ビルドと矛盾

- **発見日:** 2026-06-17 (Phase 1 タスク0 解剖中)
- **対象:** `external/ccbench` @ `33d74a3`
- **種別:** ドキュメント不整合 (機能バグではない)
- **還元判断: ユーザー確認待ち** (AI は構造化まで。上流 PR を出すかは人間が決める — D6)

## 何が矛盾しているか

`docs/protocols_en.md` の**上段の手書き表** (`:9-21`) は、各 protocol の YCSB/TPC-C/BoMB 対応を示す。そこで:
- `:18` で **ss2pl を YCSB ✓**
- `:20` で **mvto を YCSB ✓**
としている (正確には `:11` の "Silo, MOCC, ... ✓" 行とは別に、`:18`/`:20` 行が該当)。

しかしこれは**実際のビルドと矛盾する**。真実 (= CMake の `WORKLOADS` 行) では ss2pl/mvto は YCSB バイナリを作らない。

## 根拠 (source of truth)

1. **CMake の `WORKLOADS`:** `cc/ss2pl/CMakeLists.txt` = `bomb tpcc`、`cc/mvto/CMakeLists.txt` = `bomb tpcc`。`ccbench_add_protocol` (`cmake/ProtocolHelpers.cmake:32-34`) は `WORKLOADS` の各タグからのみ `<wl>_<name>.exe` を生成する。
2. **entry point の不在:** `ycsb_ss2pl.cc` / `ycsb_mvto.cc` が存在しない。
3. **auto-生成表との矛盾:** 同じ `docs/protocols_en.md` の**下段の auto-生成表** (`:35-46`、`build/PROTOCOL_MATRIX.md` を反映) は mvto/ss2pl の YCSB を正しく `—` としている。つまり同一ファイル内で上段(手書き)と下段(自動)が食い違う。
4. **実ビルド確認:** 本プロジェクトで全ビルドした結果、`ycsb_ss2pl.exe` / `ycsb_mvto.exe` は生成されない (YCSB バイナリは silo/tictoc/mocc/cicada/ermia/si/oze の7種のみ)。

## 影響

- 上段表だけを読むと「write-heavy/high-contention → ss2pl を YCSB ベースCC に」という選定をしてしまうが、YCSB では使えない。Izanagi 側は `docs/ccbench-anatomy.md` §2 で「YCSB 対応の真実は CMake の WORKLOADS」と明記し、YCSB の高コンテンション代表は `mocc` を使う方針にした。
- d2pl は上段表でも `—`/限定なので問題なし。

## 還元案 (人間が判断)

`docs/protocols_{ja,en}.md` の上段手書き表の ss2pl/mvto の YCSB 列を `—` に修正する PR。CCBench の規約 (`CLAUDE.md` ハードルール5) では `_ja`/`_en` セット更新が必須。ただし**上流還元するかはユーザー確認待ち** — まず Izanagi 側は anatomy doc で正しい事実を採用済みなので、機能上は未ブロック。
