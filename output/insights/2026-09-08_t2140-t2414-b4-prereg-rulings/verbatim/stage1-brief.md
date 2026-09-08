# 段 1 brief — [T-2140] D1812 + [T-2414] D1779 を B-4 事前登録へ反映する

## 研究前進

B-4 還流 ablation の**正式標本の実走前**に必要な最後の文書作業である。事前登録が既裁定と食い違った
まま凍結されると、実走成果物について「仮説が結果より先」(§1) を主張できない。止めている研究は
B-4 の正式標本そのもの。最小差分は、本文を裁定どおりに訂正することだけで、実装も測定も伴わない。
完了判定 = D1812 の 4 項と D1779 が本文へ反映され、既存の bytes pin と §5 の受理集合が不変であること。

## scope (この 5 点だけ。他は一切足さない)

対象 file は `docs/phase3-b4-reflux-ablation-preregistration.md` の 1 file。

1. **(a) §5.1 primary outcome 項**へ erratum。「その artifact」= **分析 source file**
   (path + sha256 の 5 member) と読む。§5 の既存記入を維持し差し戻さない (D1812 (a))。
2. **(b) §5.1 開始時刻 項**へ erratum。予定開始時刻の拘束は **D1649 決定 2 (2026-09-05) で撤廃済み**。
   固定日時を指名しない (D1812 (b))。実投入の順番付けは D1641 の測定認可と D1477
   (計算資源の空きで順番付ける) に委ね、実投入時刻は投入時に実走成果物側へ記録する
   (D1649 = 実走成果物側の記録だけを正本)。
3. **(c) §11.1 の割り当て表**と **§11.2** へ erratum。12 行は D1641 決定 3 が「§11.2 の案を採る」で
   確定済み、D1695 が標本数を改めた。**新規の採否ではなく既裁定の反映**であると書く。
4. **(d) §7.2 と §10** の「manifest・append-only registry・完全性 consumer は存在しない」という
   一括断言へ erratum。D1765 のとおり既存記述を消さず、日付 + task ID 付きの追記で直す。
5. **(T-2414) §11.2「費用の目安」**の括弧内の条件付き注記を、reference が pair-sample あたり
   2 件になった現構成へ書き直す (D1779)。加算ではなく内訳の組み替え。

## 不変条件 (破ったら停止)

- **§5 の表を 1 byte も変えない。** 値セルも行 label も変えない (D1649 が行 label 集合の不変を明記。
  `p3_b4_admission_record.py` と `test_p3_b4_closed_critic.py` の `_SECTION5_LABELS` が pin)。
- **§5.1.1 の bytes を変えない。** pin 範囲は `p3_b4_analysis_prereg_consumer._locate_section()` が
  決める **`#### 5.1.1` 見出しから次の level<=4 見出し (`## 6.`) の直前まで**。
  `PREREGISTRATION_SECTION_5_1_1_SHA256 = 0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`。
  **この範囲へ見出しを足さない** (H5 集合と順序も凍結されている)。
- **既存記述を削除・書き換えしない** (絶対規律 7、D1765)。**唯一の例外は scope 5 の括弧内注記**で、
  D1779 が「書き直す」と名指しで裁定した範囲に限る。
- **gate・検査・台帳・一般化を新設しない。** §5.1 の解除条件も §6 の前提条件も 1 つも緩めない。
  文書が発効しない状態は本 wave でも変わらない。
- living doc 規約 (`tools/check_docs.py` の `LIVING_DOCS`): 他 doc への行番号参照を書かない。
  worklog が正本の可変状態を再掲しない。
- 実装面 (コード・テスト) の差分ゼロ。したがって変異 matrix は免除 (DW-S04)。受入全走は免除しない。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-1) §5 の「実行責任者・開始時刻」値セルは変えない。**
  現状は `実行責任者 = thawk105、開始時刻 = 未記入`。`未記入` を外すとその行の実走前関門が開くので、
  受理集合を変える編集になる。D1649 が改訂対象としたのは**本文**(§5.1 の拘束)であって値セルではない。
  他 6 欄が未記入である以上、発効可能時期はこの編集で 1 日も早まらない。
  代わりに erratum の中で「発効版ではこの欄をどう書くか」を規範として書く。
  **攻撃点:** 拘束を撤廃したと書きながら sentinel を残すと、欄が永久に埋まらない矛盾を残さないか。
- **(P1-2) T-2414 は既存の *事実* 行 (248 セッション / 3,720 秒 / 1,860 秒) を消さず、
  括弧内の 2026-09-07 注記だけを差し替える。** D1779 が「構成の記述は括弧ごと本件の裁定範囲として
  残されている」と書いているため。
  **攻撃点:** *事実* 行を残したまま括弧だけ替えると、本文と括弧が矛盾して読めないか。
- **(P1-3) 新しい派生値は「名目」であることを明示する。** `PerfConfig` は未校正なので、
  起草時と同じ仮定 (1 測定 = 5 反復 x 3 秒) を引き継いだ比較可能な目安としてしか書けない。
  **攻撃点:** 起草時の「1 セッション = 5 反復 x 3 秒」と現構成の「1 セッション = 2 測定」で
  単位が変わる。単位を明示せずに秒数だけ書くと読み手が取り違えないか。

## 実測した現構成 (T-2414 の材料。子はこれを再確認してよい)

`orchestrator/campaign/floor_pair_driver.py`:
- 行 70 `REFERENCE_MEASUREMENTS_PER_PAIR_SAMPLE = 2`、行 96 `_SIDE_IDS = ("candidate_1", "candidate_2")`
- module docstring: 同一 candidate の**二つの独立 side session**を作り、各 side の
  `pre probe -> measurement 1 -> mid probe -> measurement 2 -> post probe` 区間で
  **candidate と reference を各 1 回**測る。
- 行 72 `DIFFERENCE_FORMULA` =
  `D=abs((median(candidate_1)/median(reference_1)-1)-(median(candidate_2)/median(reference_2)-1))`

導かれる構成: 1 pair-sample = 2 session、1 session = 2 測定 (candidate 1 + reference 1)。
1 セル・n=62・2 campaign = 124 pair-sample = **248 session = 496 測定**。
起草時の名目単位 (1 測定 = 5 反復 x 3 秒) を引き継ぐと **7,440 秒 (約 124 分)**。
起草時は「候補 248 session = 3,720 秒」+「参照 124 session = 1,860 秒」= 5,580 秒 だった。
**差の原因は reference が pair-sample あたり 1 件 -> 2 件になったこと**で、session 数 248 は変わらず、
session の中身が 1 測定 -> 2 測定になった。

## 実測した現状 (d) の材料

`orchestrator/campaign/p3_b4_analysis_ledgers.py` は実在し、定数
`B4_SCHEDULED_REGISTRY_SCHEMA_VERSION` / `B4_ANALYSIS_MANIFEST_SCHEMA_VERSION` /
`B4_MANIFEST_COMPLETENESS_SCHEMA_VERSION` を持つ。violation は
"One append-only protocol-violation event" として chained row で積む。
`orchestrator/campaign/p3_b4_prerun_issuer.py` が `ledgers.assert_analysis_manifest_complete` を呼ぶ。
**しかし** 同 module の docstring は自ら
"this module does not create or identify the authoritative producer. Consequently it does not claim
to close the file-drawer risk while that producer is absent." と書く。さらに [T-2140] の実測どおり
`output/` 配下に manifest / registry の**実体は 1 件も無い**。
→ 陳腐化しているのは「機構が存在しない」だけで、結論「file-drawer は開いている」はなお真である
(D1765 と同じ型)。

## 成果物の形

- `docs/phase3-b4-reflux-ablation-preregistration.md` への追記中心の 1 file 変更。
- `output/insights/2026-09-08_t2140-t2414-b4-prereg-rulings/` に逐語と README。
- `docs/spool/` へ worklog fragment (canonical 3 台帳は直接編集しない。fold は段 9 の land)。

## 分割方針

docs-only で実装面の差分ゼロ。**Codex 実装子は起動しない**(親が docs 本文を編集する)。
段 2 に read-only の plan 子 1 本、段 3 に敵対 2 本 (レンズ A = 正しさ境界・凍結規律、
レンズ B = 整合・実効性の現物検算)、段 6 にレビュー 2 本。
