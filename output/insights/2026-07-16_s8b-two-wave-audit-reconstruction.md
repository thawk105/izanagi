# 8b 二波監査 — 原文消失の記録および残存証拠からの再構成 (2026-07-16)

- **日付:** 2026-07-16
- **記録種別:** 二波監査の原文消失記録および残存証拠からの再構成。**逐語の監査記録ではない。**
- **対象:** 2026-07-16 の 8b selector/oracle 実装 (commit range e247552..98e4133) に対する
  codex 二波敵対監査 (read-only、real/refuted 選別)
- **関連 worklog:** `docs/worklog.md` 2026-07-16 (5) = 監査当時の集計・重要所見の正本。
  消失の発見・本再構成の経緯・第 3 波監査は同日 worklog の当該セッションエントリを参照
- **関連成果物:** `output/insights/2026-07-16_s8b-freeze-consultations.md` (本再構成の凍結プラン
  への敵対相談 C1 の逐語保存。本文書の骨子は C1 裁定に従う)

## 1. 位置づけ

本文書は、消失した二波監査の原文を復元したものではない。**「原文が消失した」という事実の記録**と、
repo 内に残存した contemporaneous な証拠 (worklog 要約・commit 本文・現行テスト) から**再構成
できる範囲だけ**を、証拠の強さごとに書き分けて凍結するものである。phase3 checkpoint (c) が当初
求めていた「原文の凍結」は実現不能であり、本文書はその代替である (checkpoint 側の文言改訂は
本文書の凍結と同時に行う)。

## 2. 原文の状態 — 消失の事実

- 元ファイル: `audit-wave1-out.md` / `audit-wave2-out.md` (第 1 波・第 2 波の監査出力)
- 監査実施セッション (2026-07-16 午前) で一時領域 (/tmp 配下の Claude scratchpad) へ退避された
  まま repo へ移されず、後日 (同日午後の凍結セッション) の探索で不在を確認した
- 探索範囲: 全 `/tmp/claude-*/` scratchpad (不在)、`~/.codex/sessions` (本日午後の 4 件のみ
  残存 — 監査は午前実行のため該当なし)、Claude transcript (監査内容の埋め込みなし)
- 原文の hash は取得されておらず存在しない。したがって仮に同名ファイルが後日出現しても原文
  同一性は検証できない
- **削除時刻・削除主体・原因は不明であり、断定しない。** 記録できる事実は「そのパスへ退避した」
  「後の探索時に存在しなかった」の 2 点のみである

## 3. 残存証拠と証拠階層

証拠は強い順に次の 3 層であり、以降の節はこの階層に従って書き分ける。

1. **worklog 2026-07-16 (5)** — 監査当日にセッション末で記録された集計と重要所見の要約。波別
   件数・最重要所見群 (report/judge の false-green 4 経路、driver の gate 恒真化) の正本。
   ただし要約であり、個別 finding の ID 番号は明記していない
2. **commit 本文 (e247552..98e4133 の 5 commit)** — 各修正 commit が「監査 F-x/G-y (…) を
   修正済み」の形式で監査 ID と修正内容を contemporaneous に帰属させている。ID と修正の対応の
   一次証拠だが、各 ID の記述は括弧内の短い要約に限られる
3. **現行コード・テスト** — 修正後の不変条件が現在も成立していることの regression evidence。
   **原監査の逐語 evidence ではない。** 実装とテストは各 feature commit で同時に新規追加されて
   おり、監査前後の版が Git に存在しないため、個々のテストが監査起因で追加されたことは証明
   できない。本文書ではテストを「番人テスト (監査起因)」と呼ばず、修正後不変条件の回帰証拠と
   してのみ引く

補足: §5 の表に載せるテストシンボル 5 件 (report 4 + driver 1) は grep で実在を機械確認済み。監査当日の「8b 対象
178 passed」は worklog (5) の当時記録としての引用であり、本文書の凍結セッションで再実行して
確認したものではない。

## 4. 確定できる集計

worklog (5) から確定できるのは以下のみである。

| 波 | 対象 | real | refuted |
|---|---|---|---|
| 第 1 波 | 領域 A/C/D2 (対象 14 files) | 9 | 5 |
| 第 2 波 | 領域 B/D1 | 4 | 6 |
| **合計** | | **13** | **11** |

- 「14 file」は**第 1 波の対象コード規模**であり、finding 数ではない
- real/refuted の選別手順の詳細 — 判定プロンプト、裁定者、severity 体系、個々の却下理由 —
  は原文消失により**復元不能**。記録できるのは worklog が「codex read-only、real/refuted 選別」
  と記していることだけであり、一般的な監査作法から補完しない

## 5. real finding 再構成台帳 (12/13 件)

commit 本文から監査 ID を回収できたのは **F-1〜F-7・F-9・G-1〜G-4 の 12 件**である。凡例:

- **historical_source:** `worklog-detail` = worklog (5) に個別の所見記述があり commit 要約と
  一致する / `commit-attributed` = commit 本文の短い要約のみが根拠
- **reconstructed_summary:** commit 引用と worklog 記述からの再構成。証拠を超えて膨らませない
- **current_regression_evidence:** 修正後不変条件の回帰証拠として同定できた現行テスト
  (§3 のとおり監査起因の証明ではない)。同定できなかったものは「同定せず」
- **confidence:** 高 = worklog 詳細と commit 要約の二重証拠 / 中 = commit 要約のみ

| finding_id | historical_source | reconstructed_summary | fix_commit | current_regression_evidence | confidence |
|---|---|---|---|---|---|
| F-1 | commit-attributed | binding identity の検証が恒真だった | bdb3624 | 同定せず | 中 |
| F-2 | commit-attributed | catalog の duplicate key による parser 迂回 | 4639558 | 同定せず | 中 |
| F-3 | commit-attributed | null freeze から executable manifest を受理していた | bdb3624 | 同定せず | 中 |
| F-4 | worklog-detail | expected binding 欠落で binding_ok=True になる false-green | 4d82c98 | `orchestrator/tests/test_s8b_oracle_report.py::test_missing_or_partial_expected_binding_is_protocol_violation` | 高 |
| F-5 | worklog-detail | retry で correctness red が後続 commit に上書きされる (worklog は「規律2 直撃」と記録) | 4d82c98 | `orchestrator/tests/test_s8b_oracle_report.py::test_definitive_red_survives_later_committed_retry` | 高 |
| F-6 | worklog-detail | holdout 全落ちでも determinate と判定される | 4d82c98 | `orchestrator/tests/test_s8b_oracle_report.py::test_expected_cells_keep_deleted_holdout_indeterminate` | 高 |
| F-7 | worklog-detail | manifest hash を自己申告のまま受理 (→ 独立再計算で照合へ) | 4d82c98 | `orchestrator/tests/test_s8b_oracle_report.py::test_manifest_hash_is_recomputed_independently_after_tampering` | 高 |
| F-9 | commit-attributed | generator の実ファイル hash が manifest に束縛されていなかった | bdb3624 | 同定せず | 中 |
| G-1 | worklog-detail | null-restore が未承認 floor で gate を開く恒真化 (→ 非 null freeze は freeze-v2-verifier-not-implemented で拒否) | 98e4133 | `orchestrator/tests/test_s8b_oracle_driver.py::test_nonnull_floor_requires_v2_verifier_and_run_block_writes_nothing` | 高 |
| G-2 | commit-attributed | source/raw/provenance の hash が現物へ非束縛、agent provenance が exact schema でない | 405bc46 | 同定せず | 中 |
| G-3 | commit-attributed | budget 超過 debit の残行処理が例外死 (→ budget-refused + trial-skipped で終端) | 98e4133 | 同定せず | 中 |
| G-4 | commit-attributed | verify 中断の outcome 分類欠落 (→ verify-inconclusive 追加) | 4d82c98 | 同定せず | 中 |

台帳への注記 (再構成の限界):

- **13 件目は不明のまま残す。** commit 本文の ID 列で欠落しているのは番号系列上おそらく F-8 だが、
  それが原監査の正式 ID であったかも断定できない。この 1 件は**内容・修正 commit・テスト対応の
  いずれも不明**であり、題名・severity・テストの割当てを行わない。worklog (5) は「全 13 件を
  F1/F2 で修正」と記録しており、修正自体はコミット済みコードに含まれていると当時記録されて
  いるが、どの変更がこの 1 件に対応するかは同定できない
- **worklog-detail 5 件の ID 対応は列挙順推定である。** worklog (5) は個別 ID を書いておらず、
  4d82c98 / 98e4133 の commit 本文内の並列列挙 (F-4/F-5/F-6/F-7、G-1) と worklog の所見記述を
  語順どおり一対一対応させた。内容の再構成は二重証拠で高確度だが、番号の割当てはこの推定に
  依存する
- **ID 系列と波の対応は推定。** commit 回収分は F 系 8 件 + 欠落 1 件 = 9、G 系 4 件であり、
  波別集計 (第 1 波 real 9 / 第 2 波 real 4) と数が整合するため F 系 = 第 1 波、G 系 = 第 2 波
  と推定できるが、原文消失によりこの対応は確認できない
- real 13 件とテストが一対一対応するという主張はしない (worklog の「番人テストを追加」は集計
  としての記録であり、全単射を意味しない)

## 6. refuted 11 件

第 1 波 5 件、第 2 波 6 件、合計 11 件が refuted と選別された — 記録できるのはこの件数のみで
ある。**原 claim の内容・却下理由・ID・severity はいずれも原文消失により不明**であり、復元
不能と明記する。もっともらしい却下理由で空欄を埋めることはしない。

## 7. 第 3 波監査との関係

本日、98e4133 後の現行コードを対象とする第 3 波監査を別途実施した (成果物 = `output/insights/2026-07-16_s8b-third-wave-audit.md`)。
第 3 波は**別成果物・別 ID 系列**であり、対象も本文書の二波 (修正前コード) とは異なる。第 3 波の
所見・件数を本文書の real 13 / refuted 11 の集計に混ぜてはならず、また第 3 波を消失した原文の
復元や、§5 で不明のまま残した 1 件の補完と称してはならない。現行コードの保証は第 3 波が、
修正前コードに対する二波の歴史記録は本文書が、それぞれ別個に担う。

## 8. 消失インシデントの恒久対応

本件は失敗台帳 `docs/failures.md` の F20 として登録済み。恒久対応の
要約: **セッションを跨いで必要になり得る成果物は、生成したセッション内のうちに repo 配下
(output/ 等) へ置く** — 一時 scratchpad は非永続として扱い、「後で移す」を許さない。詳細は
failures.md F20 と同日 worklog を正本とする。
