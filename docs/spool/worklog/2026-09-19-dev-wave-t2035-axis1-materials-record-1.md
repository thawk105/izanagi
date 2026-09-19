---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-t2035-axis1-materials-record
seq: 1
title: [T-2035] 軸 1 OpenAlex の取得済み 78 leaf を全列挙した後継の凍結記録を足し、2 本目論文の入口から参考材料として指した — 材料に数える 61・数えない 16・未走 1 は不変、`RW1` 据え置き、request 0 件 (docs のみ、branch worktree-dev-wave-t2035-axis1-materials-record、実装面差分ゼロ = 変異 matrix 免除、codex 子 2 本 read-only)
---

## 本文

- ユーザー依頼は「[T-2035] 軸 1 の後継記録。D2150 項 4 のとおり `Q6-SY2026` を未走のまま置き、軸 1 を 77 leaf 分の限定付き (`RW1` のまま) として、
  window 5・6 の取得結果を 2 本目論文 docs/paper-story-backoff/ の関連研究の材料へ記録する。取得の再実行・新しい query の追加はしない。
  成果 = 取得済み leaf の一覧・限定の明記・未走 query の明記を持つ記録 1 本。実装面差分ゼロ。scope 外 = 取得再実行・request の追加・主論文の関連研究」。
- 段 1 の前提実測で 2 点が覆った。(1) [T-2035] の carry 本文 (entry 1676、裁定 wave の fold) が求める「後継記録手番」は entry 1660
  (`2026-09-18b-axis1-search-execution.md`、commit `d56c5a7d3`) で消費済み — 1660 は未 land の裁定 wave fragment との fold 衝突を避けて
  [T-2035] に触れず暗黙 carry したため、後から fold された 1676 の文が stale になった。(2) 先行記録 2 本 (18 / 18b) は区分の件数と
  `complete` 8・落ちた 16・未走 1 の名前を持つが、pass 1 完了・2 走目停止の 53 leaf は名前を持たない (一次資料 window6 の
  `bundle-check.json` / `leaf-states.txt` にだけある)。→ 依頼の成果条件は「78 leaf の全列挙を持つ追補記録」で満たす。
- 親の provisional 裁定 (P1)「軸 1 は主論文の主張軸なので置き場は主論文側 (paper-story README の stale 注記)」は、段 3 の codex 相談
  (luna、medium、read-only) が must-fix で退けた — 軸 1 の帰属 (主論文 `2026-08-26.md` §3 の 1) は事実だが、`paper-story-backoff/README.md` は
  一次資料の共有を認め、`2026-09-10.md` §8 が禁じるのは「B5 の完了に数えること」だけで参考材料としての参照は禁じていない。依頼の用途指定と
  scope 外 (主論文の関連研究) をそのまま守り、**主論文 `docs/paper-story/` には触れなかった**。相談の所見は must 2 (A-1 用途・導線、B-2 導出元
  commit と転記値の身元)・should 5 (18b の追補として execution 型にする、`Q3` / `Q6` の母集合は `SPRE1991` + `SY1991`〜`SY2026`、`complete` 8 のうち
  `Q2` は 1 走完走の枝、「被覆」を「枝別内訳」にして網羅性の数でない旨を併記、主論文 README の追記は削る)・refuted 1 (gate 新設の疑い)。全部採用。
- 成果物 (段 5、親、docs のみ、commit `1415ee04c`): (a) `docs/related-work/claim-survey/2026-09-19-axis1-search-execution.md` — 2026-09-18 (b) の追補。
  §0 身元 (導出元 commit `657e1e5a7`、入力 path と SHA、bundle manifest SHA は 18b 記載値の転記で現物未照合、`Q6-SY2026` の 21,040 件・106 頁・1060 credit
  は件数 probe の申告総数からの換算で取得実績ではない)、§2 78 leaf × 区分 A〜G × 検査器の `state` / `reason_code` / `resume_action` / checkpoint の
  全列挙 (A 8 / B 53 / C 3 / D 6 / E 2 / F 5 / G 1。E / F の 7 leaf は検査器の最終コードでは区別できず窓 3・4・5・6 記録の逐語で分ける)、§3 枝別内訳
  (`Q3` 37 = 材料 29 + 数えない 8、`Q6` 37 = 材料 31 + 数えない 5 + 未走 1。候補判定・網羅性の数ではない)、§4 限定の逐語引き継ぎ、§5 未走 query、
  §6 2 本目論文が参考材料として引く読み方 (B5 の完了・成熟度には数えない)。(b) claim-survey README に 1 行。(c) `docs/paper-story-backoff/README.md` の
  「`docs/paper-story/` との関係」節に導線 1 項目 (stale 注記節には足さない、凍結版は不変)。request 0 件、bundle 非接触、検査器再走なし、新裁定なし。
- 段 6 レビュー (codex、read-only、1 本、rc=0・受理 OK): 78 leaf × 7 field = 546 値を `bundle-check.json` と全件比較して不一致 0、枝別内訳の
  再集計は全セル一致、身元は 18b と逐語一致、限定の弱化なし、`RW1` 違反の文なし、相談の must-fix 2 件は充足。所見は must 1 (R-1: 表題と README
  行の「取得済み 78 leaf」が未走 1 を取得済みに含める → 「登録 78 leaf (取得証拠あり 77・未走 1)」へ訂正)・nit 2 (R-2: 18 / 18b の完全な
  SHA-256 を記載、R-3: §1 の全ゼロ表と §7 の再掲を短縮)。3 件とも親が docs で処置 (commit `d28da27e8`、表・内訳・限定・導線は不変)。焦点再レビューの
  子は起動せず、訂正語の残存 0・`check_docs.py` 違反なし・`git diff --check` OK で閉じた (対応表は insight README)。
- 検査 (段 7、記録 commit 前): 焦点走 = `test_check_docs.py` + `test_axis1_search_catalog.py` + `test_related_work_search.py` を計算ノードへ
  dispatch (request `10755.nqsv`、22:15〜22:16 JST) で 722 passed / 3 skipped、rc=0 (変更 file を読む consumer test は無い — 3 test は固定 path だけを
  読む)。三軸語走査 (`s8b_holdout_freeze search`) と `check_docs.py`、provenance の `--message-file` は記録 commit の直前に実走 (結果は insight
  README と commit message)。受入全走は記録 commit と段 8 の後の最終 tip で `dev_wave_wait.py acceptance` 経由で投入し、結果は land の受領証。
- 受入 1 (22:24 投入、計算ノード) は child-green (25,323 passed / 69 skipped、red 0、flake 0、tested main `657e1e5a7` / tested tip
  `ca3625c8b`)。land 1 巡目は F672 型 (別 wave の登録 path `dev-wave-t2786-recovery` の strict 解決が `[Errno 4]` で落ち、
  `retryable_same_request=false`、main は無傷) で rc=31。既存 F672 の復旧どおり受入 1 を捨て、failures fragment (F672 の再発 4 例目) を
  同じ tip に積んで受入 2 を取り直した (child-green、同数)。main が `8fd1eecf9` へ進んでいたので固定 SHA で前方 merge し landing tip
  `b81d16ddf` で land 2 巡目 → 同型 F672 (別の他 wave の path、5 例目) で rc=31。fragment に機序の候補 (watchdog の 0.1 秒 SIGALRM) を
  追記して受入 3 を取り直し、新しい request で land した (結果は land の受領証)。
- 工数: codex 子 2 本 (consult 1・review 1、いずれも read-only、luna / medium)。親の実測: 分類 script 1、sha256sum 1、焦点走 1、check_docs 4、
  provenance 検査 4、spool dry-run 2、受入 2、land 2 巡以上。
- scope 外の実在 stale (実装せず、起票せず、insight に記録): 主論文の入口 `docs/paper-story/README.md` と最新版 `2026-09-17.md` §8 C-4 の
  「3 窓ぶん取得・9/8 打ち切り・この版でも動いていない」は窓 5・6 (9/17)・D2120 項 14・D2150 項 4 を含まない。次に主論文側を触る wave が
  stale 注記で所在を指す。
- 一次資料 (相談・裁定・レビューの逐語、親の分類 script): `output/insights/2026-09-19/t2035-axis1-materials-record/`。専用 handoff は repo 外 job dir。
  自己改善候補 0。decisions / failures fragment 0。push しない。

## 次の一手差分

### 完了

- [T-2035] 後継の凍結記録 `2026-09-19-axis1-search-execution.md` (78 leaf 全列挙・限定・未走 query) と 2 本目論文 README からの導線を
  land した。D2150 項 4 の反映手番は entry 1660 の `2026-09-18b` で消費済みで、本 wave はその追補。軸 1 は `未完走`・`RW1` のまま、
  材料に数える leaf は 61 で不変。`Q6-SY2026` の取得には取得器契約の変更か catalog の amendment を伴う新しい裁定が要り、本 item では扱わない。
  remaining: none
  base: a20b1575e40e85242307ce4878464e34d4dd2e5145deed0b0d9e215b1bfd311b
