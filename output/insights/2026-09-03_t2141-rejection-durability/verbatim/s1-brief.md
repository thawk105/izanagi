# [T-2141] 段 1 brief — raw 試行記録 producer の rejection 耐久化

## scope

`orchestrator/campaign/p3_b4_raw_record_producer.py` の `publish_b4_attempt_result` /
`publish_b4_attempt_results` が返す `B4RawRecordRejection` を耐久化し、**publication root だけを
入力とする consumer が、棄却された候補の理由・証拠と実験母数を後から復元できる**状態にする。
まず既存の記録経路 (issuer publication の固定 artifact、`p3_b4_admission_record`、
`p3_b4_analysis_ledgers`、campaign WAL) に相乗りできるかを file:line で測り、**足りない分だけ**足す。

## 確定済みユーザー裁定

- 本題の実装だけを行う。**仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。**
- 絶対規律 2 (正しさゲートを緩める変異を許さない) を緩めない。
- 着手直前の local main (`4ec3eba04`) から fresh worktree を作る → 実施済み。
- T-2103 と producer 側コードが重なるなら片方の着地を待つ → **起動時検査の結果、T-2103 の wave は
  存在しない** (worktree・branch とも 0 件、状態は「裁定済み D1345 → 比較実験待ち」)。待機条件は不成立。
  T-2102 (B-4 registry) は worklog 1219 で land 済み。全 59 worktree を branch 差分 + 未 commit まで
  走査し、`p3_b4_*` を触る稼働 wave は 0 件。

## 不変条件

- **成功公開の受理集合を 1 bit も広げない。** rejection を記録するようになっても、これまで棄却された
  入力が成功公開へ変わってはならない。rejection 記録の失敗を成功公開の理由にもしない。
- `_publish_exact` の no-replacement 契約 (`PLANNED_PATH_CONFLICT`) と 0o700 real-parent 検査を保つ。
- 新しい artifact 名は issuer の固定 artifact 名および planned result path と衝突してはならない
  (`p3_b4_prerun_issuer.py:418-440` の `_reject_fixed_artifact_conflicts` を通す)。
- trace-enabled 正しさ検証と trace-disabled 性能計測の分離を変えない (本 wave は性能面に触れない)。
- 既存の凍結成果物 bytes を変えない。**DW-O09 の pin 閉包検査結果: producer path を key にする
  `FROZEN_MANIFEST` / golden / trust root の pin は 0 件** (`git grep p3_b4_raw_record_producer` の hit は
  decisions.md の説明、material_report の import、`acceptance_duration_ledger.json` の所要値、テストのみ)。
  T-2103 の記述「producer は凍結 closure 外」と一致する。
- **DW-O10 producer write-path 棚卸し: 現行 producer が書くファイル種は 1 種類だけ** —
  issuer が事前計画した attempt result JSON (`_planned_path` → `_publish_exact`)。親 directory を
  0o700 で作る以外に書き込みは無い。本 wave はここに種類が増える。

## 成果物の形

- producer 側: rejection の耐久記録経路 (相乗り可なら既存 artifact への追記、不可なら最小の新 leaf)。
- consumer 側: `assemble_b4_raw_analysis` / `p3_b4_material_report` が過去 rejection を復元する経路。
  成立すれば `p3_b4_material_report.py:53-55` の非保証
  `past_producer_rejections_are_not_fully_reconstructible_from_publication_root` を狭める / 落とす。
- テスト (負例: 記録が無ければ復元不能であること / 正例: 記録があれば復元できること)、insight、
  worklog fragment。

## 実アンカー表

| 対象 | 実アンカー |
|---|---|
| rejection 生成 | `p3_b4_raw_record_producer.py:129-133` (`B4RawRecordRejection`)、`:267-277` (`_rejection`) |
| rejection の戻り口 | 同 `:1760-1772` (単発)、`:1836-1885` (batch)、`:2047-2056` (assembly) |
| 成功公開の唯一の書き込み | 同 `:475-500` (`_publish_exact`)、`:640-652` (`_planned_path`) |
| issue 語彙 (閉じた 12 値) | 同 `:105-117` (`B4RawRecordIssueCode`) |
| 実験母数の既存所在 | `p3_b4_prerun_issuer.py:443-466` (`scheduled_attempt_count`, `planned_result_artifacts`)、`:1007-1046` (`load_b4_prerun_publication`) |
| publication root の固定 artifact | 同 `:45-48`、衝突拒否は `:418-440` |
| 欠陥の宣言箇所 | `p3_b4_material_report.py:53-55`、出力は `:741`, `:777` (`report_non_guarantees`) |
| deferred (rejection ではない第 3 状態) | `p3_b4_raw_record_producer.py:135-140` (`B4RawRecordDeferred`) |

## 分割方針

軽量版ではなく段 2・3 の敵対検証子を置く。**理由: 受理集合に触れる面 (producer の棄却判定) の
近傍を変更し、consumer の復元契約という設計択一が割れるため** (DW-C00)。
実装面は Codex `role=author` 1 本に持たせる (producer と consumer の contract が単位を跨ぐため
並行 fix で契約を割らない)。親は brief・裁定・commit・変異・受入・記録・land を担う。

## (P1) 親の provisional 裁定 — 攻撃対象

- **(P1-a) 実験母数はすでに復元可能である。** issuer receipt の `scheduled_attempt_count` と
  `planned_result_artifacts` が publication root 内にあり、absent な planned path は列挙できる。
  したがって真に欠けているのは「各 absent path が **なぜ** absent か」(rejected / deferred /
  未試行 の区別と、rejection の issue 群) だけである。
- **(P1-b) 既存経路への相乗りは成立しない。** `p3_b4_admission_record` は事前 admission の git 検証、
  `p3_b4_analysis_ledgers` は scheduled registry / manifest / assignment、campaign WAL は
  campaign 実行の記録であり、いずれも「producer が個々の attempt を棄却した事実」の器ではない。
  最小の追加は publication root 配下の append-only な rejection leaf 1 種。
- **(P1-c) rejection 記録は publication root 内に置く。** consumer の入力が publication root だけ
  である以上、root 外に置けば要求を満たさない。ただし issuer が root を「新規で自分が作る」契約
  (`_ensure_new_publication_root`) を持つため、producer が後から root へ書けるかを実装前に確かめる。

## DW-G05 成果物影響

放置すると material report の `report_non_guarantees` に file-drawer が残り続け、B-4 の
棄却率・実験母数・棄却理由が proof chain から辿れない。すなわち certified 選択の材料レポートが
「何を見なかったか」を機械的に示せない。閉じれば同レポートの非保証が 1 件減る。

## DW-G04 発火 gate

production の publication root は現時点で 0 件 (`find output -name prerun-issuer-receipt.json` が空)、
`p3_b4_launcher.py` にも publication 配線は無い。したがって本 wave は **既存 artifact を書き換えず**、
コード上の consumer (`p3_b4_material_report.py:741,777`) を発火先の実アンカーとする。
「production 実績が無いので実装しない」ではなく「production 実績が無いので既存 bytes への
migration は作らない」と裁定する。
