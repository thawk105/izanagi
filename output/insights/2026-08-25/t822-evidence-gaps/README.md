# [T-822] 8c 正式受入の証拠欠落 — wave 記録

branch: `worktree-dev-wave-t822-evidence-gaps`
base: main `bb7753fa`

## 何をしたか

裁定 D863 が挙げる証拠欠落 3 件のうち、**第 3 条件 (レポート間で計測対象の一致を検査しない)**
を実質的に閉じた。

正式受入 `assert_trial_registry_acceptance` はこれまで、6 report が同じ
`measurement_head` (izanagi 側の git commit) を持つことだけを要求し、
**何を計測したかを一切照合していなかった** (`trial_registry.py` に `ccbench` と
`env_tag` の出現は 0 件だった)。6 セルが別々の CCBench source を別々の環境で計測した束も
受理された。arm 間比較 (on/off/swapped) の差を機構へ帰属させる成果物にとって中核の穴である。

受入自身が各 trial の `campaign_root/reports/layer3_report.json` を再読し、
`meta.ccbench_commit` と `env_tags` (ちょうど 1 要素) が 6 件すべてで同一であることを要求する。
完全 build 束では層 3 レポートがちょうど 6 件あることも要求し、0 件や欠落は hard failure とする。
受入中に層 3 レポートの bytes が変わっていないことも照合する。

## 親が段 0 で誤った — 段 3 が救った

段 1 brief で親は「D863 の 3 件は 2026-08-17〜18 に実装済みで既に閉じている」と書いた。
根拠は (a) `assert_campaign_layer3_chain` が acceptance から呼ばれている、
(b) `acceptance-arm-execution` が arm を再導出している、
(c) `measurement_head` の 6 件一致検査がある、の 3 点と、
判定器で C02 / C09 / C10 が合格終端に達していることだった。

**段 3 レンズ A がこれを原典で反証した。**

- 層 3 鎖の呼び出しは必須経路ではない。`do_build=False` は関数を呼ばずに進み
  (`trial_registry.py:5736-5738`)、campaignless failure cell は呼んでも `continue` で
  鎖検証へ到達しない。既存テスト
  `test_s8c_acceptance_failure_cell_pins_layer3_chain_absent_reason` が、
  この迂回を含む束が受領証発行まで進むことを逐語で固定している。
- 契約 C09 の「no-build を certify しない」という保証は**恒真である**。
  `s8c_acceptance_receipt.py:393-396` が `certifying is not False` を無条件に拒否し、
  受領証は構造上つねに非 certifying だからである。何も certify できない以上、
  「certify しない」は自動的に成り立つ。
- arm 検査は provider 入力 bytes までは届くが、その入力から得た proposal が
  実際に build・bench された source であることまでは認証しない。
- `measurement_head` の一致は「同じ git commit」であって「同じ計測対象」ではない。

**親の誤りは「呼び出しが存在すること」を「保証が発火すること」と同一視した点である。**
段 3 を省いていれば、閉じていない条件を閉じたと台帳へ書き、
正式系列の起動条件を誤って解除していた。

## 段 2 プランの芯を不採用にした

段 2 は世代数の独立再導出先として `loop_state.json` の `iteration` を選んだ。
段 3 レンズ A が原典で反証し、親が逐語で裏取りした。

- `p3_s4_loop.py:632-634`: 「checkpoint は WAL でなく loop 状態の投影 — 正本は WAL」
- `p3_s4_loop.py:703-704`: 「iteration 整合・entry 件数・campaign/run origin は本関数では検査しない」

同じ走行側が書いた値どうしの照合を「独立再導出」として記録すると、
弱い述語を強い証明として扱う恒真な保証になる。実装しなかった。

## 実測

- 焦点走 (`test_trial_registry.py`): **224 passed, 0 failed** (PBS 947565.nqsv)
- consumer 拡張焦点走 (6 file): **728 passed, 0 failed** (PBS 947568.nqsv)
- provenance 全履歴監査: rc=0、5898 件、新規違反なし
- 変異 matrix: **baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0**
  - M04 は「対象 0 件なら通す」型の恒真化を注入する変異で、これも KILLED になった
  - M06 は過剰拒否を検出する正例 (母数を 6→5 に変える) で、KILLED になった
    = 正しい 6 report 束が落ちれば検出できる

## 変異 matrix の運用で分かったこと

`tools/mutation_harness.py` の起動条件で 5 回はじかれた。いずれも harness 側の正当な要求で、
どれも起動前には気づけない。

1. 走行 argv に `-rf` が必須 (DW-M08)
2. `--spec` は試験対象 checkout の**外**に置く
3. spec の key は `schema` + `timeout_seconds` (`schema_version` ではない)
4. 作業ツリーが固定 HEAD blob と一致していること = **実装 commit が先**
5. untracked file が 1 つでもあると停止

さらに最終巡は M02 で `PARSE_ERROR` 停止した。rc=1 だが計算ノードの stdout から
failed node を確実に抽出できなかったもので、**変異でなく捕捉側の失敗**である
(同じ M02 は probe 巡で node 1 件の KILLED だった)。`--resume` で続きから再開して完走した。

## 残したもの (裁定パッケージ)

- **D863 第 1 条件** — 迂回を hard failure にするかは設計択一。
  正式受入が no-build や層 3 不在の trial を含む束を拒否すべきか、
  現状どおり理由コード付きの非 certifying 受領証を発行すべきか。
  親の推奨は拒否 (択 a) だが、失敗試行の記録経路を同時に設計する必要がある。
- **D863 第 2 条件** — 宣言 arm から実 CCBench source への因果束縛。
  producer / completeness 側の変更が要り、本 wave では稼働中の別 wave が
  `autonomous_trial_completeness.py` を編集中のため触れなかった。
- **[T-1211]** — 世代数の独立再導出。自身の記述が「外部 immutable anchor が要る」と
  述べており、campaign tree 内の checkpoint では閉じられない。open のまま残す。
- **standalone verifier の再発火** (段 6 レビュー B 所見 3) — 受領証の耐久性は別面。
- **正式系列の実残 blocker** — C03 (`manifest-registry-proof-undefined`)、
  C05 (`schedule-schema-absent`)、C08 (`prereg-binding-proof-undefined`)、
  T-468 (承認権限の不在)。

## 子の工数

codex 8 本 (plan 1・consult 2・author 1・review 2・fix 2)。全て `launcher_rc=0`。
model は全段 `gpt-5.6-sol`、reasoning は `xhigh`。

## 逐語

`verbatim/` に段 1 brief、段 2 プラン、段 3 敵対レンズ 2 本、段 4 裁定、
段 5 実装報告、段 6 レビュー 2 本を置く。
