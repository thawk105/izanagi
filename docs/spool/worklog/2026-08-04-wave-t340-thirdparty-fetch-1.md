---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-t340-thirdparty-fetch
seq: 1
title: [T-340] third-party source の取得経路を tools/pegasus へ置いた — 検証器の再利用で二重化を避け、共有 FS の publish 方式を実測で決めた (コード + docs、branch worktree-wave-t340-thirdparty-fetch、変異 = 15/15 KILLED)
---

## 本文

- **裁定は既に台帳へ landed 済みだった。** command 引数は「台帳未記録」としていたが、
  worklog (145) に択 (a) 採用が記録済みで内容も一致した。stale な前提として扱い実装へ進んだ
- **scope を 1 段格下げした (段 3 レンズ A の指摘が real)。** brief は「取得の由来が台帳から
  追える」と書いたが、取得経路は submit receipt にも evidence にも**値として漏れない**
  (`third_party_rederivation` は `sha256-chain-consistency-only`)。よってこの主張を取り下げ、
  本 wave の成果物は**任意の operator preflight helper** と定義した。最終権威は凍結された
  submitter / job script の pin/clean 検査のままであり、campaign の受理集合は変わらない。
  helper を必須工程と解釈すると (origin 等を追加要求するため) 受理集合が変わってしまう
- **凍結 4 本を 1 byte も触らない制約が設計を決めた。** 凍結 evidence が
  `policy.json` / `silo_ladder_rung1.sh` / `submit_silo_ladder_rung1.sh` /
  `orchestrator/campaign/silo_ladder_rung1.py` の sha256 を束縛している。したがって
  新規ファイルだけで閉じる形にし、consumer 接続は「submit の `[[ ! -e "$destination" ]]` 分岐を
  満たすように staging を先に埋める」ことで実現した
- **検証器は再実装せず import した。** `third_party_source_contract` / `third_party_policy` が
  pin 一致・clean・symlink 拒否・CMake 同期検査を既に持つ。ロジック二重化の攻撃面を減らした
- **敵対レンズ 4 本で計 31 所見。** 段 3 (プラン攻撃) 18 件、段 6 (実装攻撃) 13 件。
  段 6 の blocker はすべて real で、**うち 1 件は親の裁定 R6 自身の誤り**だった —
  「consumer へ cache root を渡す」という指示が、cache が持ちうる ignored ビルド生成物を
  そのまま build 入力へ運ぶ経路を作っていた。訂正して `hydrate` の `source_root` のみを
  consumer 用とした。逐語は `output/insights/2026-08-04_t340-thirdparty-fetch/`
- **設計判断は {{D:thirdparty-fetch-path}} を参照**
- 検出漏れ 1 件と規律違反 1 件は {{F:mutation-masked-by-outer-verify}} と
  {{F:empty-dir-untracked-fixture}} に記録した
- **受入 (最終 tip、計算ノード全走): 5535 passed / 19 skipped / 0 failed、rc=0。**
  `check_docs.py` rc=0、`check_ai_provenance.py` rc=0。既知赤 waiver W1 は
  [T-407] の land により失効しており、**適用せずに緑を得た**
- **変異 matrix: 事前登録 15 件すべて実効的に KILLED。** 1 回目は KILLED 10 / MISMATCH 4 /
  SURVIVED 1。MISMATCH 4 件 (M02/M10/M12/M14) は**すべて過剰決定**で、登録 node は全件赤・
  冗長 gate が追加で赤くなっただけである。SURVIVED 1 件 (M15) は真の検出漏れで、
  テスト強化後の再走で M15 (単層) / M15C (両層同時) とも KILLED。初回結果は erratum として残す
- **codex 実装子は 2 回とも pytest を実走できなかった** (計算ノード dispatch が rc=16)。
  緑の主張もしなかった。テストと変異の実測はすべて親が行った
- 走行中に main が 48 commit 進み、merge commit で取り込んだ。取り込み後も凍結 binding は一致

## 次の一手差分

### 完了

- [T-340] 取得経路を `tools/pegasus/fetch_third_party.py` として実装し land した。
  `fetch` / `hydrate` / `verify` / `verify-deps` の 4 subcommand、cache root は明示必須、
  publish は mkdir 排他予約 + rename、Git metadata と危険 config を fail-closed 拒否。
  hydrate 後に凍結 submitter を `--prepare-third-party-only` で実走して rc=0 を確認した。
  `gflags_source_path` / `glog_source_path` の絶対パス直参照は `verify-deps` の検査対象に
  含めるに留めた (policy が凍結されており直参照そのものは動かせない)。
  remaining: none
  base: 7012e39fcaa0f85001c0815115c01c357abd1886e2f92dc685a30b6d2b07ffbb

### 新規

- {{T:thirdparty-fetchcontent-other-campaigns}} **P2・新規・ユーザー裁定要**:
  **rung1 と T-139 probe 以外の campaign は `FETCHCONTENT_SOURCE_DIR_*` を渡していない。**
  certify / floor / t126 qualification / t141 / t152 は override 無しで CCBench を configure
  するため、network の無い計算ノードでは FetchContent が外部取得へ進む構造である
  (親が grep で実測、段 3 両レンズが独立に指摘)。certify が過去に成功している事実との整合は
  未検証。択 = (a) 各 campaign の CMake argv へ verified cache projection を足す、
  (b) buildcache 契約へ三 source の identity と source-dir を足す、(c) 現状維持で記録に留める
- {{T:thirdparty-acquisition-receipt}} **P3・新規・ユーザー裁定要**:
  **取得経路を proof chain へ束縛するか。** 現状は helper bytes・cache identity・実 transport・
  Git hardening 状態のいずれも receipt に現れず、取得経路を evidence から再構成できない。
  束縛するなら凍結 evidence の再発行 (D96 手続き) が要る
- {{T:thirdparty-hydrate-enforcement}} **P3・新規**:
  **hydrate を機械的に強制する経路が無い。** 呼び忘れると凍結 submitter が従来どおり
  GitHub から clone するため、worktree 消滅事故は「今日と同じ状態」に戻る (悪化はしない)。
  強制には凍結 submitter の書き換えが要る
- {{T:mimalloc-tag-pin-sync}} **P3・新規**:
  **mimalloc の `fetchcontent_ref` は annotated tag `v2.3.2`、`pin` は commit SHA で、
  両者を照合する gate が無い** (`third_party_policy` は ref が 40-hex のときしか照合しない)。
  tag が動いても現行検査は通る。凍結 driver の変更が要る
- {{T:codex-reasoning-ab-tmp-flake}} **P3・新規**:
  `test_codex_reasoning_ab.py::test_agent_sandbox_binds_exclude_attempt_receipt_directory` が
  受入全走 1 回で setup error になった (`/tmp` の git object copy が `No such file or directory`)。
  **単独再走 97 passed で再現せずフレーク**。xdist 並列下の `/tmp` 競合が疑われる
- {{T:mutation-runner-known-red}} **P3・新規・ユーザー裁定要 (dev-wave 改善候補、予算外)**:
  **変異 harness の `KILLED` 判定は赤 node 集合の完全一致**であるため、main 側に既知赤が
  1 件でもあると**全変異が `MISMATCH` になる**。本 wave は runner から既知赤 node を
  `--deselect` して回避したが、この作法はどの reference にも書かれていない。
  `docs/dev-wave/**` は 25,196/25,200 bytes で 4 bytes しか余裕が無く、意味等価な縮約でも
  入らなかった。択 = (a) 予算を空けて `DW-M05` か `DW-M08` へ 1 行足す、
  (b) harness 側に既知赤の除外機構を作る、(c) 運用規律に委ねる
- {{T:thirdparty-cache-same-uid-toctou}} **P3・新規**:
  **repo 外 cache に対する同一 UID 敵対者への完全防御は入れていない。** symlink 拒否・
  publish 後再検証・fresh clone までは入れたが、dirfd + inode pinning による親 component の
  TOCTOU 封じは preflight helper に対して不釣り合いと裁定した。境界に含めるかは未裁定
