# 段 1 brief — [T-2464] B-4 事前登録の開始時刻欄を発効条件から外す (D1871)

wave slug: `t2464-b4-start-time`
worktree (子が読む repo root): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2464-b4-start-time`
基準 commit: `d97c423bdd14e0b416cb4f585d350e6c2b251287` (local main、clean、submodule 初期化済み)

## 研究前進

論文 §8 の B-4 (還流 on/off ablation) 事前登録は、§5 の 10 欄がすべて埋まるまで発効しない。
D1649 決定 2 が 2026-09-05 に「開始時刻は `未記入` のままでよい」と拘束を撤廃したが、受理側
(`assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel`) はいまも
全 10 行へ一律に sentinel 禁止を掛けており、裁定が未実施のまま残っている。本 wave はその 1 欄だけを
裁定どおりに実装し、本文へ追補を足す。**これは土台であり、B-4 の発効そのものではない**
(下の実測のとおり残り 5 欄が `未記入` なので、本変更後も実文書は受理されない)。

## 親が実測した事実 (模擬でなく実物)

- 受理側は現在この文書を拒否する。probe 実測:
  `RAISED: [admission-preregistration] section 5 fixed table requires nonempty source cells and no reserved sentinel; types, meanings, and rendered non-emptiness are not checked`
- §5 表の対象行の生値は `|実行責任者・開始時刻|実行責任者 = thawk105、開始時刻 = 未記入|`。
  `_RESERVED_SENTINEL_RE` は `未記入` に span (24,27) で当たる。
- §5 表で `未記入` の行は 6 つある (赤 precursor の母集合 / floor / 校正済み `PerfConfig` /
  総計測予算 / env_tag / model snapshot、および対象行)。**したがって本変更の正例は実文書では作れず、
  合成 fixture (`_section5_document(value_overrides=...)`) で作る。**
- pin 閉包 (DW-O09): 事前登録 doc の whole-file sha256 を live で pin する箇所は無い
  (値検索の hit は `output/insights/2026-09-16_t2545-b4-publication-root/README.md` の記録 1 件だけ)。
  `tools/check_docs.py:146` は本 doc を living (byte 予算) として持つだけで sha pin しない。
- 解析規則側の sha 定数は `orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47,50` の
  `PREREGISTRATION_SECTION_5_1_1_SHA256` / `..._SEMANTIC_SHA256` で、**§5.1.1 だけ**を pin する。
  追補の挿入先は §5.1 の「開始時刻」節 (§5.1.0 より前) なので §5.1.1 の bytes は動かない見込み。
  **実測で確かめること。**
- 凍結成果物側の sha は admission record JSON の `preregistration_content_sha256`
  (`p3_b4_admission_record.py:157,179,279,775`)。tracked な発行済み record は repo に 0 件
  (`docs/phase3-b4-reflux-ablation-admission-record-{base,sort,trigger}.json` はいずれも不在)。
- `orchestrator/tests/test_s8c_preregistration_core.py:63` にも同名 label があるが、別文書・別 module
  (`orchestrator/campaign/s8c_preregistration.py`) であり **D1871 の射程外**。触らない。

## 確定済みユーザー裁定 (逐語は verbatim/ を読む)

- **D1871 (2026-09-09)** — 本 wave の正本。行 label 集合は変えず、本欄に限り `未記入` を受理する。
  §0 の原子性・sentinel 規則は他の欄についてはそのまま維持する。本文改訂は追補で別 wave (= 本 wave)。
- **D1649 決定 2 (2026-09-05)** — 予定開始時刻の記入義務を撤廃。欄は `未記入` でよい。
- **D1789 / D1790 (2026-09-08)** — 事前登録は in-place で書き換えず追補で訂正する。測定時点の束縛と
  現行の解析規則は別々の定数として pin する。

## scope

- **scope 内:** (a) `p3_b4_admission_record.py` の §5 検査を対象 1 行に限り緩める。
  (b) `docs/phase3-b4-reflux-ablation-preregistration.md` §5.1 の「開始時刻」節へ追補 (erratum) を
  末尾追加する。(c) (a) の正例・負例テスト。
- **scope 外 (足さない):** 新しい gate・検査・台帳・一般化、他 9 欄の緩和、8c 側、§0 本文の規則改訂、
  §5 表の値セルの書き換え、admission record の発行、B-4 の実走。

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-1) 緩和の粒度。** 親は **案 B** を採る: 対象行では `開始時刻` の値位置に現れる `未記入` だけを
  受理し、`実行責任者` 側は従来どおり sentinel・空を拒否する。理由は D1871 が外すのは「開始時刻」で
  あり、§5.1 の「実行責任者: 指名がないまま実走しない」義務と D1812 (b) の「実行責任者を不変の識別子で
  指名する義務は変わらない」が現に生きているため。**案 A (行全体を sentinel 検査から免除) は受理集合を
  裁定より広げる**ので採らない。案 B が §0 の「`名前 = 値` の形で並べてよい」と矛盾しないかを攻撃せよ。
- **(P1-2) 実装位置。** 親は行 label をキーに分岐する形 (`values` の走査で対象 label だけ別述語) を
  想定する。`_SECTION5_LABELS` の並び順 index ではなく label 文字列で引くこと。
- **(P1-3) 追補の文面が「§5 の欄を埋める権限」や「発効」を含意しないこと。** 既存の追記
  (2026-09-08、[T-2140]、D1812 (b)) と同じ体裁で、D1871 を引いて「受理側を裁定に合わせた」ことだけを
  述べる。本文の既存行を 1 文字も書き換えない。

## 不変条件

- 規律 2 を緩めない。対象欄以外の受理集合は 1 bit も広げない (負例で示す)。
- `_SECTION5_LABELS` の集合・順序・文字列を変えない。
- §5 表の値セル、§0 本文、§5.1.0、§5.1.1 の bytes を変えない。
- 既存テストの期待値を反転・緩和・skip・削除しない。
- 追補は追加のみ。in-place 書き換え禁止。

## 成果物の形

- コード差分 1 単位 (`orchestrator/campaign/p3_b4_admission_record.py`)、
  テスト差分 1 単位 (`orchestrator/tests/test_p3_b4_admission_record.py`)、
  docs 差分 1 単位 (事前登録本文の追補、親が書く)。
- 変異 matrix (受理集合を変えるので免除されない)、受入全走、insight、spool fragment。

## 並列分割方針

編集面が小さく所有が 1 単位なので、段 5 は Codex `role=author` 1 本。段 2 plan 1 本、段 3 は
2 レンズ並列、段 6 はレビュー 2 本並列。docs 追補は親が書く (実装面ではない)。

## 実アンカー表 (worktree 相対)

|対象|anchor|
|---|---|
|行 label 定義|`orchestrator/campaign/p3_b4_admission_record.py:78-88` (`_SECTION5_LABELS`)|
|sentinel 定義|`orchestrator/campaign/p3_b4_admission_record.py:114-121`|
|検査関数|`orchestrator/campaign/p3_b4_admission_record.py:602-676`|
|一律 sentinel 走査|`orchestrator/campaign/p3_b4_admission_record.py:667-673`|
|正規化|`orchestrator/campaign/p3_b4_admission_record.py:538`|
|文書束縛|`orchestrator/campaign/p3_b4_admission_record.py:760-786`|
|test fixture 生成|`orchestrator/tests/test_p3_b4_admission_record.py:83-115` (`_section5_document`)|
|test の label 複製|`orchestrator/tests/test_p3_b4_admission_record.py:42-52`|
|§0 の例外規定|`docs/phase3-b4-reflux-ablation-preregistration.md:36-41`|
|§5 表の対象行|`docs/phase3-b4-reflux-ablation-preregistration.md:167`|
|§5.1 実行責任者|`docs/phase3-b4-reflux-ablation-preregistration.md:339-340`|
|§5.1 開始時刻 + 既存追記|`docs/phase3-b4-reflux-ablation-preregistration.md:341-358` (追補の接続先)|
|§5.1.1 の sha pin|`orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:47-51,400-407`|
