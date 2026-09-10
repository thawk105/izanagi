# [T-2060] D1245 — 歴史閲覧と現行認証の分離を実体化する

wave: `dev-wave-t2060-current-closure-unknown` / branch `worktree-dev-wave-t2060-current-closure-unknown`
一次資料: `docs/decisions.md` の D1245、その親裁定 D1163 (絶対規律 7)。

## この wave が変えたもの

1. 歴史 view は `current_verifier_conformance` を exact `"unknown"` として持つ。
2. Layer 3 の歴史 report は同じ値を **top-level の optional field** として出す。
3. certified report は同 field を持たない。schema は `certifying_input == true` のとき同 field を拒否する。
4. 自律試行の完全性検査は、同 field を持たない保存済み report を従来どおり受理する
   (保存済み側が持つ場合は厳密比較を維持)。

中央 gate、reason enum、`CampaignVerifierEpoch`、certified 側の `current-closure-unavailable`、
`require_persisted_certified_commit`、certified token 発行、exact 型拒否は**すべて無変更**である。

## 実測で分かったこと

### 依頼文の前提が 1 つ食い違った

「`current-closure-unavailable` を歴史閲覧の拒否理由にしない」は **中央 gate では既に成立していた**。
`_require_verifier_epoch_for_purpose` は `HISTORICAL_RAW` で現行閉包を一切読まない。
D1245 の純増は (1) その構造を機構として固定すること と (2) 現行適合 unknown の明示表示であり、
後者はどこにも実体が無かった。

### 親の実測 2 件が過大一般化だった (段 3 レンズ A の訂正)

- 「現行閉包の可用性 = exact 24 path が HEAD と一致」は**誤り**。`capture_contract_loader_binding` は
  root 解決・Git top-level・no-follow/race・Git 実行・timeout・commit/blob 解決の失敗も
  同じ `ContractLoaderBindingError` へ畳む。**`current-closure-unavailable` は drift 以外も表す。**
- 「編集中は certified 経路のテストが一律赤」も**誤り**。`_committed_closure_repo` +
  `_REPO_ROOT` 差し替えの隔離 fixture を使うテストは未 commit 編集中でも緑になる。
  期待赤の一括分類は禁止し、赤は 1 件ずつ assertion 本文と差分実体で判定した。

### 実装が絶対規律 7 の違反を新たに作り込んでいた (親が段 6 で発見)

`autonomous_trial_completeness.py` は保存済み Layer 3 report と `build_report` の再構築を
`_canonical_bytes` で **byte 比較**する。新 field のせいで、**同 field を持たない保存済み report は
必ず食い違う**。`output/campaigns/` の保存済み report 7 件はいずれも同 field を持たない
(先頭 1 件の top-level key は 15 個、v2 形式)。

**この型はテスト色では見えない。** テスト内で保存済み report を `build_report` で作れば両側に
field が付いて緑になる。壊れるのは実成果物だけである。
段 6 の敵対レビュー 2 本はどちらもこれを指摘していない。親がレビュー B の「焦点走の漏れ」を
追跡して実測した。

直しは同 file の既存 legacy omission 正規化 (`include_epoch` /
`include_verifier_assessment_basis`) と同型の flag を 1 つ増やしただけである。

### 新規 6 node のうち 3 つは旧実装でも通る

構造回帰・dirty certified 負例・certified schema node は **D1245 実装の存在証明ではなく回帰 pin**
である。存在を証明するのは表示・投影・保存済み互換の 3 node と変異 D1/D2/C1/C2 である。
段 3 レンズ A の指摘 (T-01) をそのまま採用した。

### 表示は状態非依存の定数である

`current_verifier_conformance` は現行閉包の状態を見ない定数である。
現行閉包が clean でも表示は `"unknown"` であり、「現在適合している」の肯定表示はできない。
段 4 で明示的に受容した (P-03)。表示値の変異は kill ではなく診断感度 pin として別枠登録した。

## 実装しなかったこと (裁定パッケージ)

D1245 は歴史閲覧と現行認証の**分け方**を定めた裁定であり、既存の各消費者がどちらの purpose を
宣言するかまでは決めていない。過去の測定を実際に読む消費者
(`replay.load_landscape`、`s1_report` の epoch gate、`s8b_oracle_report` の epoch 証拠) の
再分類は certified 成果物の受理集合を変えるため、親の一存では行わなかった。

段 3 のレンズ B は「本 wave の scope では D1245 は満たされない」と判定しており、
その所見は real として採用したうえで、実装ではなく裁定パッケージへ送った。

## 一次資料

- `s1-brief.md` — 段 1 brief と親の実測
- `s4-adjudication.md` — 段 4 裁定、変異事前登録、gate の禁止と通る正例
- `s6-fix-adjudication.md` — 段 6 裁定 (レビュー 2 本 + 親所見)
- `verbatim/` — 子の出力逐語 (plan、相談 2 本、実装、レビュー 2 本、fix)
- `mutation-*.json` — 変異 spec と走行結果
