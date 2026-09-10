# 段 1 brief — [T-474] 旧 trigger artifact に admitted view を名乗らせない (縮小版再検査)

基準 main = 55c2e84、branch `worktree-dev-wave-t474-legacy-trigger-admission`。

## scope

[T-409] 択一 C のユーザー裁定 (2026-08-05 /rulings) = 「(a) の縮小版」。原文の本質は
**「admitted view を名乗らせない」ことであり、reinspection ledger の新設は費用次第**。
対象は [T-428]/D160 の land 以前に生成された trigger 軸 campaign artifact。

## 段 1 前提実測 (親がこの worktree で実測。裁定前提を覆す/裏取りする事実)

- **M1**: 旧 trigger artifact は実在 7 件。`p3-s8a-trigger-loop-…-3f72ecd5` (proposal 系) は
  overlay-denied / `legacy-unclassified` で **admitted でない**。残る機械 sweep 6 件
  (`p3-s8a-trigger-sweep-{balanced,read-heavy,write-heavy}-…`) は
  `historical-pre-admission-schema` / `historical-not-reclassified` で
  **`decision.admitted` が True** = `require_admitted_campaign` が view を発行する。
  歴史枝は `validate_trigger_bindings` を一切通らない (post-policy 枝のみが呼ぶ)。
- **M2**: その 6 件の実述語を 32 正準集合と直接照合した。`s8a_trigger_sweep_provenance.json` の
  `entries[*].implementation` 39 件のうち **34 件は全て正準**。残り 5 件は各 campaign の
  `stock` entry で、中身は C++ でなく日本語の説明文である。つまり **membership 違反はゼロ**で、
  `implementation` という同名 field が「述語」と「説明」に二義化している (D75 系の欠陥、DW-O13)。
- **M3**: D160 決定 5 は、この 6 件について「proposal 経路なし」により**遡及被害ゼロを実測済み**と
  宣言し、却下選択肢として「marker 欠落 artifact の包括 legacy 化」と
  「全 trigger campaign への binding 遡及要求 (機械 sweep 6 件が拒否へ反転する)」を明記している。
  **T-474 の素朴な実装は D160 の却下選択肢そのものに当たる。**
- **M4**: 露出は歴史限定ではない。post-policy でも機械 sweep lock は
  `validate_trigger_bindings` が `{}` を返すだけで membership 証拠を要求しない。
- **M5**: 現行テストが今の挙動を pin している —
  `test_post_policy_trigger_machine_sweep_does_not_require_binding` と
  `test_exact_pre_policy_git_snapshot_artifact_remains_readable`。
- **M6** (DW-O09/O10): `artifact_admission.py` は `FROZEN_MANIFEST` (23 key) にも
  `s8b_oracle_manifest._GENERATOR_SOURCES` にも無い。`admission_decision` を持つ persisted
  artifact は repo 内に **0 件**。よって同 file の編集は凍結 bytes を変えない。
  ただし `s8a_trigger_sweep.py` は `known_axes_freeze.json` が path+sha を記録する producer
  (現行 sha は freeze 記録と既に不一致) であり、**本 wave の編集面から外す**。

## 不変条件

- 正しさゲートを緩める方向の変更は採らない (規律 2)。既存テストの緩和で赤を消さない。
- D160 決定 5 を親が一方的に覆さない。覆す実装しか成立しないなら実装せず裁定パッケージへ返す
  (`DW-S04`)。
- 凍結 bytes・既存 certified 選択・proof chain の歴史分類は不変に保つ。
- `s8a_trigger_sweep.py` と `output/s1-freeze/` は非接触。
- 並行 wave [T-472] が `s1_direct_comparison.py` / `s1_verify_extime_calibration.py` を所有中。

## 択一 (親の provisional 裁定 = 攻撃対象)

- **(P1)** 実害の所在は「旧 artifact に非正準述語が入っている」ことでは**ない** (M2 で反証)。
  「admitted view が trigger membership について何の証拠も持たず、consumer が
  binding 証明済みと歴史的無証明を区別できない」ことである。**provisional: real。**
- **(P2)** 方向 A (歴史 trigger artifact の `admitted` を False へ反転し
  `require_admitted_campaign` を拒否させる) は D160 却下選択肢の再現であり、
  layer3 生成と既存材料を落とす。**provisional: 親は採らず、採るならユーザー再裁定。**
- **(P3)** 方向 B = `CampaignAdmissionDecision` に閉じた trigger 証拠 field を足し
  (binding-proven / machine-sweep-unbound / legacy-unbound / not-applicable)、
  trigger 主張を出す consumer に**明示掲載を義務付ける**。受理集合は変えず、
  「admitted と名乗るが membership は名乗らない」を機械化する。**provisional: これを採用。**
- **(P4)** reinspection ledger (7 件の exact hash 台帳) の新設は費用に見合わない。
  overlay ledger は records=3 固定で authority が T-342+T-343+T-344 に pin されており、
  拡張は台帳契約と authority の改訂を要する。**provisional: 作らない。**

## 純増検出力 (性質で検索した既存被覆)

- 「歴史 trigger artifact が admitted view を得る」ことを正例/反例で固定したテストは **0 件**。
- 「機械 sweep は binding 不要」は pin 済み (M5) だが、**membership 証拠の不在を consumer へ
  伝える経路そのものが無い**。よって純増は (a) 証拠 field の存在と閉包、(b) 歴史 trigger 枝の
  正例/反例、(c) `implementation` field 二義化の明示。

## 成果物影響 (DW-G05)

実装しない場合: layer3 材料レポートは、trigger 軸の結果を binding 証明済み campaign と
無証明の歴史 campaign から**同じ形で**出し続ける。読み手は `classification` を自分で
読み解かない限り両者を区別できず、将来 machine sweep 経路が非正準述語を materialize しても
(M4 の穴) 受理集合は無変化のまま材料へ流れる。

## 成果物の形

`artifact_admission.py` への閉じた field 追加 + layer3 schema/report への必須掲載 +
正例/反例テスト。変異事前登録は段 4 (`DW-M01`)。実装面は Codex `role=author` が書く。

## 環境

テスト実測は Pegasus login node から `tools/run_tests.py` が計算ノードへ同期 dispatch する。
性能計測は行わない (本 wave に計測項目なし)。
