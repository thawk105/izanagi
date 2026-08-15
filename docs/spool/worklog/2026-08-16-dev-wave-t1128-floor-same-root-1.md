---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1128-floor-same-root
seq: 1
title: 床値の oracle 依存 root と build の source root を同一 tree へ揃えた — 敵対 3 本が独立に NO-GO、fix 4 巡、変異 9 件で SURVIVED 0 (コード + docs、branch worktree-dev-wave-t1128-floor-same-root)
---

## 本文

- **実装した。** 床値の `sort_best` cell について、job 一意な `$TMPDIR` 配下に canonical な
  FetchContent base を 1 個作り、依存の prebuild と cell build が同じ `<base>/masstree-src` を
  使うようにし、oracle の `dependency_root` をその root へ明示束縛した。
  **`FETCHCONTENT_SOURCE_DIR_*` は渡していない** — 該当項目の「実装しない」裁定を守った。
  設計判断は {{D:floor-shared-fetchcontent-base}}、
  {{D:dependency-identity-authority-is-content}}、
  {{D:closed-detail-codes-for-dependency-prebuild}}。
- **親の裁定文の誤りで 79 件が赤になった ({{F:ruling-implication-written-as-equivalence}})。**
  段 6 fix 契約で片方向の含意を「同値」と書いたため、実装子が忠実に双方向を実装し、
  base を持たない正常な `sort_best` record を全部拒否した。78 件が同一行から出ており原因は 1 本。
  **同じ wave のレビューが「受理集合の過剰縮小」として潰した型を、親自身が別の場所で作り直していた。**
  実装子は指示に忠実であり子側の欠陥ではない。fix 1 巡分を消費した。
- **偽の緑を 1 件是正した ({{F:unbound-name-nameerror-masquerades-as-expected-code}})。**
  失敗注入テストが `buildcache` を束縛しておらず、`NameError` が production の総括捕捉へ落ちて
  期待値と偶然一致していた。`[base]` パラメータは緑のまま通っており、
  「prebuild の base 失敗が閉じた detail code へ変換される」という保証は一度も検証されていなかった。
- **敵対検証が 3 回とも独立に NO-GO を返した。** 段 3 の 2 レンズ (scope / 正しさ防壁)、
  段 6 の敵対レビュー 2 本、段 6 の焦点再レビュー。所見は延べ 17 件で、うち must-fix 11 件を採用した。
  **最も重かったのは焦点再レビューの合成欠陥** — fresh で拒否した wrong-root の binary が
  完成 cache に残り、次回の cache hit で受理されるという lifecycle 欠陥である。
- **fix を 4 巡した。第 4 巡は `DW-O16` の 3 巡上限を超えている。** 新しい所見への追加対応ではなく、
  第 1 巡 fix 契約 F2 が「**どの root から**内容を取り直すか」を書き落としていた未完了部分の
  完成であること、および成果物影響が重いこと (oracle が検証していない依存で作られた binary に
  certified の admission receipt が出る) を理由に実施した。判断と根拠は
  `output/insights/2026-08-16_t1128-floor-same-root/verbatim/s6-fix4-ruling.md` §0 に書いた。
- **変異 9 件、SURVIVED 0。** 初回走は KILLED 7 / MISMATCH 2 で、MISMATCH は 2 件とも
  **観測が登録の上位集合**だった (spec が 1 つ前の commit 時点で書かれ、その後の fix が
  test を追加したため)。probe 巡として残し、期待 node を**因果を実コードで説明できたものだけ**
  再登録して再走し KILLED 2 / SURVIVED 0 を得た。
  **M8 (cache identity の receipt から archive sha256 を外す) が KILLED だったことが要点である** —
  段 6 の敵対レビューが「生存する」と予測した変異であり、fix がその検出力の穴を実際に塞いだ。
- **背景 job の待ち手が 3 回連続で偽の完了を返した
  ({{F:dev-wave-waiter-returns-success-without-artifact}})。**
  成果物・`.done` が無く生産者が生存している状態で rc=0・出力ゼロ。
  3 点照合で毎回 fail-closed に検出でき、最後は `.done` 出現までブロックする自前の待ちへ切り替えた。
- **login node の bounded local テスト実行は使えなかった。**
  `bounded scope の memory.max / memory.oom.group を走行中に attest できない` により
  rc=16 になる。これはテスト結果ではない。実測はすべて計算ノード (`gen_S`) へ
  `--force-dispatch` で回した。子 (codex) は sandbox が socket を拒むため dispatch できず、
  本 wave の pytest 実測はすべて親が行った。
- **本 wave は「床値が取れるようになった」とは主張しない。** 本走 (12 cell・測定・report) は
  行っていない。計算ノードで共有 base の再利用挙動が期待どおりかも**未測定**である。
  設計は fail-closed なので仮定が外れても偽の主張は出ず停止する。
- 材料の正本 = `output/insights/2026-08-16_t1128-floor-same-root/`
  (変異台帳 2 本、変異 spec 2 本、逐語 12 本)。

## 次の一手差分

### 完了

- [T-1128] 床値の oracle 依存 root と build の source root を同一 tree へ揃えた。
  oracle と `sort_best` cell の build は同じ `<base>/masstree-src` を使い、
  同一性は内容 (HEAD + `config.h` + archive の sha256) で主張する。
  remaining: none
  base: 4a7ef0043291bed41dabf921a1d3b00d23774e04fca7fd3af416de4f41e6cd16

### 新規

- {{T:floor-swo-pass-receipt-binding}} **P1・新規**: 床値の durable record へ SWO PASS receipt を
  束縛する。`prepare_cell` が返す `oracle_attempt` を `s8b_floor_campaign` は一度も読まないため、
  certified 選択の根拠から「どの comparator がどの oracle 実行で通ったか」への durable な辺が無い。
  本 wave は依存 identity (root・HEAD・`config.h`・archive) だけを束縛した。
- {{T:fetchcontent-fully-disconnected-review}} **P2・新規**: oracle 実行後の再 fetch を禁止する手段
  (`FETCHCONTENT_FULLY_DISCONNECTED=ON` 等) の可否を審査する。download 権威の変更であり、
  既存 pin 機構との関係を含めて独立に敵対検証してから決める。本 wave は検知して
  fail-closed に留めた。
- {{T:shared-fetchcontent-base-reuse-probe}} **P2・新規**: 計算ノードで共有 FetchContent base の
  再利用挙動を 1 job で実測する。2 本目以降の configure が既存 source を置換せず再 fetch も
  しないことを、inode と clone stamp の不変で確かめる。床値本走の前に測る。
  現状の根拠は CMake 3.22.1 の実ソースと、床値 job が `command -v cmake` で同じ実体を引くことだけ。
- {{T:dependency-aba-swap-prevention}} **P2・新規**: build 中に依存 tree を差し替えて元へ戻す
  (ABA) 攻撃への予防を設計する。前後 snapshot の同値検査では検出できない。
  予防には依存 tree の書込み禁止か、linker が実際に読んだ archive の identity を
  binary completion receipt へ束縛することが要る。どちらも書込み / download 権威の変更である。
- {{T:shared-base-ownership-lock}} **P3・新規**: 共有 FetchContent base に create-only の
  所有権 token を導入する。現状は job 一意な `$TMPDIR` 配下の `mkdtemp` で排他が構造的に成立し、
  cell loop も同期なので発火しない。**cell build を並列化するときの再審査事項**として起票する。
