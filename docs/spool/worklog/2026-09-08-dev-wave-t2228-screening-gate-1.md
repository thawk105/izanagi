---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2228-screening-gate
seq: 1
title: [T-2228] screening 段の条件関門へ準備済み FetchContent base を供給した — 裁定どおり関門 1 箇所だけで、緑になったとは名乗らない (コード + テスト + docs、branch worktree-dev-wave-t2228-screening-gate、変異 matrix = baseline PASSED・KILLED 15・SURVIVED 0・MISMATCH 0・期待 node 完全一致 15/15)
---

## 本文

- **本 wave は「screening 関門が緑になった」とは名乗らない。** 名乗れるのは
  「driver 段と同型の供給を screening 関門へ入れた」ことだけである。現行の正規入口から
  実 CCBench で関門を通す生死確認は行っていない。段 3 の 2 レンズと段 6 の 1 レンズが
  それぞれ「実測が要る」と must-fix にしたが、親は**依頼が「本題の実装だけ」と明示していること**と、
  D1666 が実装 wave と実測 wave を分けた先例に従い、scope 外と裁定した。
- **ユーザー裁定 D1733 の射程は守った。** `backoff_repro` と `s1_direct_comparison` への供給、
  pin の整合、freeze の再生成には触れていない。両レンズが「その 2 経路にも同型の欠陥がある」と
  見つけたが、いずれも must-fix にせず裁定パッケージ候補へ分けさせた。
- **親 brief の不変条件が誤っていた。段 3 レンズ A が反証し、親が訂正した。** brief は
  「受理集合を変えない」「赤入力は赤のまま」と書いたが、本変更の目的そのものが
  「準備済み base の未供給だけを理由に前段で赤だった呼び出しを判定へ進ませる」ことである。
  正しい形は {{D:screening-gate-supply-route-proxy}} に記録した。
  「`config.h` 欠落だけが消える」も誤りで、FetchContent population 全体が変わる。
- **段 2 プランの正例は恒真だった。段 3 の両レンズが独立に指摘し、親が must-fix に採用した。**
  既存 fixture `condition_meaning_gate/supplied` は `FETCHCONTENT_BASE_DIR` を無害に参照するだけで、
  供給が実際には何も届けていない実装でも緑になる。段 5 で新 fixture
  `condition_meaning_gate/prepared-base-required` を作らせた。owner TU が準備済み base の中にしか
  無い header を include し、prepare の代役が**返り値ではなく副作用で**その header を置く。
  実 supply record の依存閉包にその header が入ることまで検査する。
- **段 3 レンズ A の must-fix 1 件を親が実測で refute した。** 「per-genome の prebuild が
  baseline と候補の熱状態を非対称にする」という指摘に対し、`pipeline.evaluate` が関門と計測の間で
  variant の完全 build を既に行っていることを現物で確認した。詳細は
  {{D:gate-prebuild-not-attributable-to-measurement-asymmetry}}。
- **段 4 裁定 8 の変異 M13 の期待を、段 6 レビュー B が訂正した。** 親は「load-bearing 正例
  だけを殺す」と書いたが、実際は 4 node を同時に赤にする。probe の観測どおり完全集合で登録した。
  `site` 引数の省略を変異させる案も、引数既定値と同じで意味を変えない no-op だったので削除した。
- **実装子と fix 子は計算ノード混雑 (`rc=16`) で pytest を 1 件も走らせられなかった。**
  テストの実測はすべて親が行った。焦点走 1 回目は 1 failed / 48 passed で、赤は F855 の同型再発
  (未使用 CMake 変数の警告が `configure-failed` になる) だった。fix 後の焦点走 12 file は
  **776 passed / 3 skipped, rc=0**。
- 段 6 レビュー B の待ち手が producer 生存中に rc=0 で戻った (F817 の再発)。`.done` の不在で
  気づき、until ループへ張り替えた。
- 子の工数: codex 6 本 (plan 1・consult 2・author 1・review 2・fix 1 の計 7 本)。全て
  `launcher_rc=0`。model は全段 `gpt-5.6-sol`、reasoning は全段 `xhigh`。

## 次の一手差分

### 更新

- [T-2228] **P2・進行中**: `backoff_sweep` の screening 段の関門へ、D1666 が driver 段へ入れたのと
  同型の FetchContent base 供給を入れた ({{D:screening-gate-supply-route-proxy}})。
  D1733 の射程どおり `backoff_repro` と `s1_direct_comparison`、pin の整合、freeze の再生成には
  触れていない。**残りは、現行の正規入口 (CLI) から `screening_fixed_us=2` の最小 screening を
  計算ノードで走らせ、baseline の stock 腕まで緑 record を得ること。**それまでは
  「screening 関門が緑になった」と名乗らない。
  base: cf52bb7889aad148210d89a998f57e78b48cbe6e2e18db57a0fdb7a71a0566de
