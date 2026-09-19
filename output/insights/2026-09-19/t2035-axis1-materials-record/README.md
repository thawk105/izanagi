# T-2035 — 軸 1 OpenAlex の登録 78 leaf の全列挙記録と 2 本目論文への導線 (docs のみ、request 0 件)

- authority: none
- default_effect: no-state-change
- 裁定: 新規なし。反映済みは D2120 項 14 (2 走目停止・落ち据え置き) と D2150 項 4 (`Q6-SY2026` 未走のまま・77 leaf 分の限定付き・`RW1`)。
- 成果物: `docs/related-work/claim-survey/2026-09-19-axis1-search-execution.md` (2026-09-18 (b) の追補)、同 `README.md` の一覧行、
  `docs/paper-story-backoff/README.md`「`docs/paper-story/` との関係」節の導線 1 項目。
- wave: dev-wave-t2035-axis1-materials-record。着手時 local main `a99425b66`、段 4 前に `657e1e5a7` へ `--ff-only`。
- 原ログ: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2035-axis1-materials-record/`。逐語は `verbatim/`。
- 逐語の可逆正規化: `git diff --check` に抵触した行末 space だけを `verbatim/consult.md` (4 行) と `verbatim/review.md` (2 行) から除去した
  (可視文字不変)。`verbatim-normalization.json` に原文 / 正規化後の SHA-256・byte 数と 1 起点の行番号別除去 suffix (hex) を保存。対応行の
  改行直前へ suffix を戻すと原文を復元でき、原文一致を実測した (`normalize_verbatim.py`、job dir)。
- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、記録 commit 前): rc=0、H1 (rr80) / H2 (rr20) の
  conjunction hit 0、positive control 217。placeholder (`{{`) は fragment に 0。

## 何を作り、何を作らなかったか

先行の凍結記録 2 本 (18 / 18b) は材料の範囲を区分の件数 (数える 61・数えない 16・未走 1) と、`complete` 8・落ちた 16・未走 1 の
名前で持つが、pass 1 完了・2 走目停止の 53 leaf は名前を持たなかった。本 wave は window6 の `bundle-check.json`
(`status.leaf_diagnostics`、SHA-256 `7a39126b…`、18b が offline 再走で byte 一致を確認済み) から OpenAlex 78 leaf を機械分類し
(`verbatim/make_table.py`)、1 行 1 leaf の表 (区分 A〜G × 検査器の `state` / `reason_code` / `resume_action` / checkpoint) と枝別内訳を
凍結記録に置いた。E (`declared_total_drift` 2) / F (条件 5 で pass 1 が落ちた 5) は検査器の最終コードが同値で区別できず、窓 3・4・5・6 記録の
逐語で分けたことを記録に明記した。

作らなかったもの: 取得・request・件数 probe (0 件)、bundle への接触、検査器の再走、leaf ごとの取得日・頁数の 6 窓横断再構成、候補判定、
不在の文、主論文 `docs/paper-story/` への変更、`docs/paper-story-backoff/` の新しい日付版、gate・検査・台帳、実装面の差分。

## 前提の実測と裁定

- **(P1) 置き場 — 親の provisional 裁定は誤りで、相談が退けた。** 親は「軸 1 は主論文の主張軸 (`docs/paper-story/2026-08-26.md` §3 の 1、
  `related-work/README.md` §7.7 は paper-story §8 C-4 の規則) なので、依頼の『2 本目論文 `docs/paper-story-backoff/` へ記録』は誤前提であり、
  置き場は主論文 README の stale 注記」と提示した。段 3 の codex 相談 (luna、medium、read-only) は帰属の事実は認めつつ must-fix で退けた:
  `paper-story-backoff/README.md` は一次資料の共有を認め、`2026-09-10.md` §8 が禁じるのは「一般的な CC 合成文献調査を B5 の完了に数えること」で
  参考材料としての参照ではない。依頼の用途指定と scope 外 (主論文の関連研究) をそのまま守り、凍結記録は claim-survey (共有物) に置き、
  backoff README の「関係」節から導線を引いた (stale 注記節には足さない — B5 の記述は古くなっていない)。
- **(P2) T-2035 の残件。** carry 本文 (archive entry 1676、裁定 wave の fold) が求める「D1208 に従い後継の実行記録へ確定を反映」は entry 1660
  (`2026-09-18b`、commit `d56c5a7d3`) で消費済み。1660 は未 land の裁定 wave fragment との fold 衝突 (`transition-target` / `base-mismatch`) を
  避けて [T-2035] に触れず暗黙 carry したため (entry 1660 本文「台帳の扱い」、commit `03829a867`)、後から fold された 1676 の文が stale になった。
  本 wave の記録は裁定の初反映ではなく 18b の追補であり、依頼の成果条件 (leaf 一覧・限定・未走 query) をこれで満たして [T-2035] を閉じる。
- **(P3) 新規性。** 78 leaf の名前付き全列挙 (とくに B の 53) は凍結 docs に無かった。相談・レビューとも real。

相談の所見 8 (must 2・should 5・refuted 1) は全部採用 (`verbatim/adjudication.md` の表)。段 4 直前の裁定 inbox 再走査: main が
T-2489 の land で `657e1e5a7` へ前進、編集面と非交差、未 fold fragment 0、decisions に軸 1 の新規言及なし。

## 独立検証と修復

- 段 3 相談 1 本 (レンズ 2 つを prompt 内で分けた)、段 6 レビュー 1 本 (再抽出の照合 + 過剰・削除レンズ)。いずれも正規の隔離 Codex subprocess、
  read-only、`check_codex_output.py` rc=0。実装面ゼロのため段 5 は親が docs を起草し (commit `1415ee04c`)、変異 matrix は免除 (D95 決定 2)。
- レビューは 78 leaf × 7 field = 546 値を `bundle-check.json` と全件比較して不一致 0、§3 の枝別内訳を §2 から再集計して全セル一致、
  §0 の身元を 18b と逐語一致、限定の弱化なし、`RW1` 違反の文なし、consult の must-fix 2 件の充足を確認した。
- レビュー所見と処置 (親、docs、commit `d28da27e8`):

| 所見 | 判定 | 処置 | 状態 |
|---|---|---|---|
| R-1 表題・README 行の「取得済み 78 leaf」は未走 1 を取得済みに含める | real / must-fix | 表題・冒頭・§2 見出し・README 行を「登録 78 leaf (取得証拠あり 77・未走 1)」へ訂正。backoff README の導線は「取得済みの leaf 一覧」= 一覧の名であり数を書かないので不変。`grep "取得済み 78"` 残存 0 | closed |
| R-2 18 / 18b の SHA-256 が省略形のみ | real / nit | 完全値を §0 入力 path (2) に記載 (各 1 回) | closed |
| R-3 §1 の全ゼロ表と §7 の残件再掲は短縮できる | real / nit | §1 を 1 文、§7 を先行記録への参照へ | closed |

  fix は文言の訂正 3 件で、78 行の表・枝別内訳・限定・導線は不変 (`git diff --stat` = 2 file、+8/−16)。焦点再レビューの子は起動せず、
  親が訂正語の残存 0 と `check_docs.py` 違反なし・`git diff --check` OK で閉じた (DW-O16 の対応表は上)。

## 受入・検査

- 記録前の焦点走 (login、`tools/run_tests.py` に file 指定、受入形ではない): 計算ノードへ dispatch (request `10755.nqsv`、2026-09-19 22:15:49〜22:16:04 JST)、`orchestrator/tests/test_check_docs.py` + `test_axis1_search_catalog.py` + `test_related_work_search.py` = 722 passed / 3 skipped (13.56 s)、rc=0。変更 file を参照する consumer test は無い (3 test は catalog JSON と登録文書の固定 path だけを読む) が、docs lint と軸 1 の登録 consumer を焦点集合にした。
- `python3 tools/check_docs.py`: 違反なし (段 5 後・段 6 fix 後の 2 回)。
- 受入全走: 記録 commit と段 8 の後の最終 tip で `tools/dev_wave_wait.py acceptance` 経由で投入し、結果は land の受領証 (job dir の `acceptance1.receipt.json` / `land-result.json`) が持つ。本 README は受入前に凍結するので結果を書かない。

## scope 外の実在 stale (実装せず、起票せず、所在だけ記録)

主論文の入口 `docs/paper-story/README.md` と最新版 `2026-09-17.md` §8 C-4・冒頭「先行研究調査そのものは、前版の時点で止まっている」は
「3 窓ぶん取得・2026-09-08 に打ち切り (D1760)・この版でも動いていない」と書くが、2026-09-17 の窓 5・6 (T-2035、entry 1589 / 1631)、
D2120 項 14、D2150 項 4、凍結記録 18 / 18b / 本記録を含まない。依頼の scope 外 (主論文の関連研究) なので触っていない。次に主論文側を
触る wave が stale 注記 4 件目で所在を指すのが自然 (DW-S04: scope 外 real 所見は起票せず insight に記録)。

## 言わないこと

- 軸 1 が `RW2` 以上に進んだ、材料が 61 から増えた、`Q6-SY2026` が取得された、B5 の成熟度が動いた、世界の不在について何か言えるようになった —
  いずれも言わない。表の数は登録 leaf の取得状態の集計であり、候補判定や文献の網羅性の数ではない。

## dev-wave 改善候補

なし。
