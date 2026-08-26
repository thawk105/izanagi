---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1784-prereg-admission-record
seq: 1
title: [T-1784] 事前登録 §5 の 3 期待値を実走前 commit の admission record として controller の必須入力にした (コード + テスト、branch worktree-dev-wave-t1784-prereg-admission-record、変異 matrix = baseline PASSED・14/14 一致・KILLED 13・SURVIVED 1 (登録どおり)・MISMATCH 0)
---

## 本文

- 依頼は「事前登録 §5 の全欄を実走前に埋めて commit し、model snapshot / prompt hash /
  projection hash の期待値を controller の必須入力にする admission record を作る」。
  **起動時の編集面重複検査で scope を実装側だけへ寄せた。**
- **併走 wave `dev-wave-b4-prereg-enactment` が同一文書の §5 を埋める scope を宣言済みだった。**
  4 面 (稼働 process の cmdline 全走査 / repo 外 job dir の brief・plan・prompt / 登録済み全 worktree
  38 本の branch tip / 作業ツリーの未 commit 差分) で実測し、job dir
  `/home/SFC/tanab/.claude/jobs/8b5f61ea` の段 1 brief が §5 表 (150-163 行) と §5.1 (165-192 行) を
  編集予約していることを確認した。**本 wave は事前登録文書を 1 byte も触っていない。**
  「値を書く側」を併走 wave に、「値を機械が要求する側」を本 wave に分けた。これは競合ではなく合成である。
- 設計判断は {{D:prerun-admission-record}}、{{D:admission-sidecar-not-receipt}}、
  {{D:section5-syntactic-scope}}。
- **段 2 plan は receipt schema を `/v3` へ上げる案を出したが、段 3 のレンズが実コードで反証した。**
  `/v2` は既に 3 実測値と `evidence_class` を持つため昇格は gate を 1 bit も強くせず、
  併走 wave との編集面の重なりを `main` 1 か所から 3 か所へ広げるだけだった。却下した。
  代わりに独立 sidecar を置いた ({{D:admission-sidecar-not-receipt}})。
- **段 3 の 2 レンズは合計 13 件の real を返し、うち 2 件を scope 外の裁定パッケージへ送った。**
  sol (正しさ防壁) は「両腕の receipt を整合的に `certified` へ書き換えると正式関門を通る」を
  最重要として挙げ、これは**段 5 の実装で塞がっていなかった**ため段 6 で塞いだ。
  luna (実効性) は「production factory は B-4 実走の支配点ではない」を挙げ、
  3 driver からの呼び手が 0 件であることを実測で示した。
- **本 wave 最大の所見は段 6 レビュー B の 1 件である。** 事前登録 §1 は逐語で
  「実走成果物にその発効版の commit hash を記録する。記録がない実走は事前登録された実験として
  扱わない」と要求する。receipt を変えない裁定と組み合わせると、**gate は通るのに監査の跡が
  残らない**状態になっていた。親が一次資料で逐語を確認し、sidecar で塞いだ。
- **§5 の描画位置を判定する関数が 3 巡続けて欠陥を出した** ({{F:markdown-rendered-position-by-line-regex}})。
  過剰拒否 → 過剰拒否 → 過剰受理と方向が振れ、一方向だけを直すと他方が開いた。
  4 巡目は行わず、残る過剰拒否 (inline code / indented code / backslash escape 内の `<!--` を
  comment opener と誤認する) を**既知の限界として docstring へ逐語で列挙**して閉じた。
  方向が fail-closed で未登録の実走を通す危険がないこと、同じ状態機械が既に 2 度後退していることが
  理由である。DW-O16 の 3 巡上限に一致する。
- **過剰拒否は正例テストでしか捕まらない。** 段 4 で受理集合を縮小する wave の必須登録として
  過剰拒否検出の正例 3 件を事前登録しており、そのうち 1 件が親の初回焦点走で赤 7 件を出した。
  負例を何本足しても、この 7 件は緑のままだった。
- **変異 M11 は登録どおり SURVIVED した。** `assert_b4_certified_arm_pair` の
  `evidence_class` 検査は、同じ入力を production seal が先に拒否するため到達しない冗長層である。
  DW-M02 に従い両層同時変異 M14 を追加登録して裏取りし、M14 は 2 node で KILLED した。
  M11 は DW-M03 の「冗長 gate」として単独変異の証拠から外し、SURVIVED 期待で登録した。
- **段 5 実装子と段 6 fix 子はいずれも pytest を 1 件も実走できなかった** (codex sandbox は
  計算ノードへ dispatch できない)。3 人とも「実装済み・未実走」と正直に申告し、緑を偽らなかった。
  テストは親が全数実走した。
- 段 6 レビューの投入で `--reasoning` を review 段に付けて 2 本とも rc=2 で即死した
  (argv 制約は plan/consult 専用)。付け直して再投入した。
- 実測の一次資料は `output/insights/2026-08-26_t1784-prereg-admission-record/` の
  `main-ledger.json`、`probe-ledger.json`、`probe2-ledger.json`、
  `mutation-spec-main.json` と `verbatim/` の子出力 9 本。

## 次の一手差分

### 更新

- [T-1784] **P1・部分完了**: 3 期待値を実走前 commit の admission record として controller の
  必須入力にする機構は実装した (`orchestrator/campaign/p3_b4_admission_record.py`、
  {{D:prerun-admission-record}})。**残るのは §5 の全欄を実際に埋めて commit する作業**であり、
  これは併走 wave `dev-wave-b4-prereg-enactment` の scope である。
  機構側で未了なのは §5 残り 9 欄の型検査 ({{D:section5-syntactic-scope}}) と
  active record の単一性。
  base: 404c64985847e69411810506f1f6ccd7cc7e04b8495aea7f6582c359e76bce62

### 新規

- {{T:b4-run-control-point}} **P1・新規**: **production factory は B-4 実走の支配点ではない。**
  3 driver からの呼び手は 0 件で、`run_one_iteration()` や fixture main を直接呼べば
  admission record も閉じた critic も通らずに certified campaign を作れる。
  B-4 標本を機械的に分ける支配点 (専用 orchestrator と B-4 identity) を置くか、
  downstream で B-4 名乗りだけを拒否するかを裁定する。
- {{T:b4-proposal-causal-binding}} **P1・新規**: 閉じた critic の decision hash と
  次 proposal の hash を鎖にする層が無い。receipt を持っているだけでは treatment を
  消費した証明にならず、receipt の decision を無視して任意 proposal を供給しても
  campaign / arm / iteration / digest の検査は通る。**併走 wave の必須配線の設計に直接効く。**
- {{T:b4-external-admission-anchor}} **P2・新規**: 別経路 (test-only factory、Python API 直呼び、
  過去の類似実験) で先に結果を知ってから record を commit し、新しい実走を始める攻撃は
  repository 内の Git だけでは識別できない。外部の append-only launch ledger、
  信頼できる timestamp、または一度だけ消費できる署名済み admission token のいずれが要るか裁定する。
- {{T:b4-prerun-model-attestation}} **P2・新規**: model 期待値の不一致は critic query と
  envelope 保存の**後**にしか検出できないため、出力を見てから record の model 欄を直して
  再試行できる。payload 送信前に exact snapshot を固定 (attest) する層を置くか裁定する。
- {{T:prereg-section5-typed-validation}} **P3・新規**: 事前登録 §5 の残り 9 欄の型検査
  (artifact path の実在、予算が正整数、時刻書式など)。本 wave では併走 wave が欄の書式を
  決めている最中のため入れなかった ({{D:section5-syntactic-scope}})。書式確定後に裁定する。
- {{T:s06b-replacement-counts-as-deletion}} **P3・新規・ユーザー裁定待ち**: 段 8 の自己改善で
  `DW-S06-B` へ「より強い検査への置換も削除に数える」を足そうとしたが、
  `docs/dev-wave/**` の L1.5 予算を 62 bytes 超過した (9628 > 9566)。予算満杯の文書を
  意味等価に縮約するのは逐語 pin を壊す既知の危険があるため、契約に従い編集を止めた。
  今 wave の実測 (fix 子が既存負例 2 件を「より強い 1 件」へ置換して削除した) は F80 の再発として
  記録済み。予算を上げるか、`DW-S06-B` を縮約するか、記録だけで足りるかを裁定する。
- {{T:b4-active-admission-record-uniqueness}} **P3・新規**: admission record を複数の path に
  置いて都合のよい方を選ぶ経路が残る。現状は content commit の blob が検証時 HEAD の blob と
  同一であることを要求して古い §5 版を指す record を落としているが、
  active record を固定 path 1 本に限るかどうかは文書側の規約であり未裁定。
