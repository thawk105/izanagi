---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2035-axis1-q6sy2026-record
seq: 1
title: [T-2035] 軸 1 OpenAlex の `Q6-SY2026` を未走のまま置く裁定 (第 22 回 /rulings 項 4) を後継の凍結記録へ反映した — 材料は 77 leaf 分 (数える 61 + 数えない 16) で区分不変、年 shard 枝の 2025・2026 年分は 4 leaf とも材料に無い、OpenAlex 78 leaf すべてに裁定が付き裁定待ち 0、`RW1` 据え置き (docs のみ、request 0 件、branch worktree-dev-wave-t2035-axis1-q6sy2026-record、変異 matrix 免除 = 実装面差分ゼロ、子ゼロ)
---

## 本文

- ユーザー依頼は「[T-2035] (第 22 回 /rulings 項 4、ユーザー『推奨通りで』2026-09-18。fragment = worktree-rulings-all-20260918 の
  docs/spool/decisions/2026-09-18-rulings-all-20260918-1.md) 軸 1 OpenAlex の Q6-SY2026 (106 頁、21,040 件、1060 credit、現行取得器では
  完走不能) を未走のまま置く裁定を、D1208 に従い新しい日付の実行記録として docs/related-work/claim-survey/ に足す (docs のみ、request
  0 件) — 材料は 77 leaf 分で『限定付き』、成熟度 RW1 のまま、宣言的除外 (D1207) や完走条件の免除には変えない、Q6-SY2025 は落ちた leaf に
  加わり据え置き、README の一覧 1 行。2026-09-18 の記録 (entry 1646、land 済み) は bytes を変えない。取得器・catalog・bundle は触らない。
  着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の記録だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外」。
- **閉じた (記録手番を消費した)。** 一次資料は `docs/related-work/claim-survey/2026-09-18b-axis1-search-execution.md` (同日の先行記録
  `2026-09-18-axis1-search-execution.md` と区別するため `b`、6 窓目 `2026-09-17b` と同じ慣行)。`claim-survey/README.md` の一覧に 1 行。
  decisions fragment 0 (新しい設計判断なし — 裁定は第 22 回 /rulings の fragment が持つ)、failures fragment 0。先行記録・6 窓目・
  取得器・catalog・bundle・検査器の bytes は不変 (manifest SHA-256 `06fbef369ed0…`、mtime 2026-09-17 21:39:35 JST のまま)。
- 反映の中身: (1) `Q6-SY2026@openalex` は起動しない。検査器は引き続き `leaf_not_run` と報告し、それは正しい (契約上は未走)。未走のまま
  置く根拠は decisions 台帳にあり、検査器・取得器・完走述語には無い。(2) 宣言的除外 (D1155 / D1207) でも完走条件の免除でもない —
  件数 probe が 21,040 件を返した以上、索引が返せる query であり「取得できるが取っていない leaf」のまま。`Q6` 枝の aggregate は `否`、
  軸 1 は `未完走`・`RW1`、不在の文は 1 つも作らない。(3) D2120 項 14 の「未走 2 leaf の初回取得 (1 窓)」は、`Q6-SY2025` 分を 6 窓目で
  消費し `Q6-SY2026` 分を本裁定が変更したので、取得指示を持たなくなった。(4) `Q6-SY2025` (51 頁、申告総数 10065、条件 5 で不足 12 件、
  再開点なし) は落ちた leaf に加わり据え置き (D1564 / D1623 のまま)。(5) 「材料は 77 leaf 分」= 78 − 未走 1 = pass 1 の証拠を持つ 77 leaf
  (材料に数える 61 + 契約の条件で落ちて数えない 16)。先行記録 §3 の区分は不変で、材料に数える leaf を 61 から増やしていない。
  (6) 限定の明記: 年 shard 枝 `Q3` / `Q6` の 2025・2026 年分は 4 leaf とも材料に無い (`Q3-SY2025` / `Q3-SY2026` / `Q6-SY2025` は
  条件 5 で落ち、`Q6-SY2026` は未走)。非 shard 4 枝のうち材料に数えるのは `Q2` だけ。(7) これで OpenAlex 78 leaf すべてに裁定が付き、
  裁定待ちの leaf は無い。取得するには取得器契約の変更 (択 (b)) か catalog の amendment (択 (c)) を伴う新しい裁定が要る。
- 一次資料の実測 (login node、read-only、request 0 件): bundle manifest SHA-256 = 6 窓目走行後の値と一致 (399 MB)。main `24ede1d11` の
  `tools/check_axis1_search.py bundle` を offline で再走 (10:41 JST、rc=2、`leaf_not_run`) し、6 窓目の `bundle-check.json` と byte 一致
  (SHA-256 `7a39126b…`)。出力から OpenAlex 78 leaf を数え直し = 53 (`start_independent_pass`、停止) / 8 (`complete`) / 7 (再開点なしの
  `leaf_page_evidence_missing` = 条件 5 で pass 1 が落ちた 5 + `declared_total_drift` 2) / 6 (`second_pass_digest_mismatch`) /
  3 (`distinct_work_id_total_mismatch` = `Q1` / `Q4` / `Q5`) / 1 (`leaf_not_run` = `Q6-SY2026`) — 先行記録 §5 の表と一致。枝の構成は
  `Q1` / `Q2` / `Q4` / `Q5` が各 1 leaf (非 shard)、`Q3` / `Q6` が各 37 shard (`SPRE1991` + `SY1991`〜`SY2026`) で計 78。
- 裁定の裏取り: fragment `2026-09-18-rulings-all-20260918-1.md` 項 4 の本文は依頼文と一致 (択 (a)、77 leaf 分、`RW1`、D1207 の除外に
  しない、D1208、`Q6-SY2025` 据え置き)。同 fragment は本 wave の着手時点で main の decisions に未 fold (D 番号未採番) のため、記録は
  「第 22 回 /rulings 項 4 (2026-09-18)」と決定台帳の見出しで指し、凍結物には番号を書き込めないことを記録 §6 に限界として明記した。
- 段 1 で pin 検査: claim-survey の file 集合・README 一覧行を pin するテストは無し (`test_axis1_search_catalog` / `test_axis_b5_*` /
  `test_related_work_search` は catalog JSON と登録文書の固定 path だけを読む)。`DW-O08` / `O09` / `O10` / `O11` / `O13` は不発火。
- 段 4 裁定: 実装しない (docs のみ、実装面差分ゼロ) → `4→7→8→9`。(P1)「77 leaf 分 = 78 − 1 で 61 / 16 の区分は不変」、(P2)「裁定は
  D 番号でなく回次・項番と見出しで指す」、(P3)「file 名は同日 2 本目なので `2026-09-18b`」を採用。裁定 inbox の再走査 = D2121〜D2141 に
  軸 1 の言及なし、未 fold fragment 0。main は着手時 `24ede1d11`、記録 commit 後に t2290 wave (dev-wave docs、`DW-O23` / `DW-O27` の
  収容) が `386fc515c` へ進めた — 本 wave の編集面とは非交差、段 9 前に取り込む。
- **台帳の扱い (着地順の衝突を避けた):** 裁定 wave (`rulings-all-20260918`、本 wave 中は受入の門番待ちで未 land) の worklog fragment が
  [T-2035] を `完了`、[T-2037] を「記録手番」へ `更新` する。fold は非 active item への操作 (明示 carry を含む) を `transition-target`、
  本文差を `base-mismatch` で協調 lock の中で止めるので、本 wave が同じ item に触れて先に land すると裁定 wave の land が lock 内で
  赤になる。よって本 fragment は [T-2035] / [T-2037] のどちらにも触れない (暗黙 carry)。どちらが先に land しても両 fold は通る。
  **裁定 wave の fold 後、[T-2037] の「記録手番」は本記録で満たされている** — 次に worklog へ触る wave が 1 行の `完了` fragment で閉じる
  (記録 = `2026-09-18b-axis1-search-execution.md`、残件なし)。裁定 wave が land しない場合は [T-2035] も同じ記録で閉じる。
  「残っている記録手番を通せ」と読んで再起動しないこと (F428 型)。
- 検査 (段 7、docs commit 前): 三軸語走査 (`s8b_holdout_freeze search`) rc=0 (H1 / H2 の conjunction hit 0、positive control 198)、
  `check_docs.py` 違反なし、provenance の `--message-file` rc=0 と記録 commit 後の全史監査 rc=0 (11,299 件、新規違反なし)。pytest の焦点走は login node の guard が pytest を拒否するため未実施 —
  claim-survey を読むテストは固定 path だけで本 wave の変更 file を読まない (grep で確認)。受入全走は記録 commit と段 8 の後の最終 tip で
  投入し、結果は land の受領証。
- 工数: codex 子 0 本 (軽量版、docs-only)。親の実測: sha256sum 2、bundle 検査器 1 走、集計 script 3 本 (job dir、repo 外)、三軸語走査 1、
  check_docs 1、provenance 検査 2。

## 次の一手差分
