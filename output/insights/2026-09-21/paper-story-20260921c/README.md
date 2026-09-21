# 論文ストーリー 2026-09-21c 版 (同日 3 版目)・claim-evidence 2026-09-21b 稿・状態図 fig3c — wave の記録

- wave: `worktree-paper-story-2026-09-21c` (背景 job 3a74883b、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-2026-09-21c/`)
- 依頼の逐語: `verbatim/origin.md`
- 起点 local main: `d99c556dfa23e446987ef3ccbb5c018986fe10b5` (fold、2026-09-21 13:35 JST、worklog entry 1795 まで)。着手 14:03 JST、開始 gate rc=0 (14:04)。
- 成果物: `docs/paper-story/2026-09-21c.md`、`docs/paper-story/claim-evidence/2026-09-21b.md`、`docs/paper-story/README.md` の更新、
  `docs/paper-story/figures/arc_status_story_2026-09-21c.json` (状態 JSON)、`docs/paper-story/figures/fig3c_arc_status_2026-09-21.{png,pdf,provenance.json}`、
  `docs/paper-story/figures/README.md` の fig3c 節、`tools/plotting/README.md` の追随、生成器 `tools/plotting/plot_arc_status.py` と test の最小修正 (Codex author)。
- commit: 統合 (生成器 + test) `76b60f6e1`、版・claim-evidence・README・状態 JSON `8256ebf78`、fig3c と figures README `0b427f5fb`、
  local main `24ca912ee` の取り込み `691be812d`、記録 (本 insight・stale 注記・spool fragment) はその次の commit。
- 本 dir の file: `verbatim/` (依頼、段 1 brief、段 3 相談の prompt と出力、段 4 裁定、段 5 author の最終報告、段 6 レビュー A / B と焦点再レビュー
  2 巡の prompt と出力)、変異の spec と結果 (`mutation-spec-{probe,final}.json`、`mutation-{probe,final}-results.json`)、行末空白の可逆正規化の記録
  (`verbatim-normalization.json`)。親が本文へ当てた置換 script と下書き役の置換案 JSON は job dir の `tools/` と `edits/` にあり、repo へは写していない
  (`.py` は実装面になるため)。本文の差分そのものは git の履歴が持つ。

## 1. 段構成と子

| 段 | 担い手 | 結果 |
|---|---|---|
| 1 brief | 親 | `verbatim/s1-brief.md`。(P1)〜(P6) |
| 3 相談 | Codex `gpt-6-astra` / medium、read-only、2 レンズ 1 本 | high 0 / mid 4 / low 5。JSON の任意 caption 欄 (親の初案) を「最小でない」と攻撃 → 撤回 (`verbatim/s3-consult.md`) |
| 4 裁定 | 親 | `verbatim/s4-ruling.md`。旧版だけ旧 caption、他は状態非依存の固定 caption。変異 M0〜M8 を事前登録 |
| 5 実装 | Codex author (`gpt-6-astra` / medium、12 call、268 s) | 統合 commit `76b60f6e1`。生成器 3 箇所 + test T9〜T13 (`verbatim/s5-author.md`) |
| 5 本文 | 親 + 下書き役 (Claude sonnet 8 本 = 節別、1 本 = claim-evidence) | 置換案を親が監査・修正して一括適用 (版 113 件 + 親 3 件、claim-evidence 55 件) |
| 6 レビュー | **Claude opus の独立 context 2 本** (Codex 利用上限のため代替、§4) | A: NO-GO must-fix 6 / should 9 / nit 8、B: NO-GO (条件付き) must-fix 1 / should 8 / nit 11 |
| 6 焦点 | Claude opus 2 巡 (`DW-O16`) | 1 巡目: 条件付き GO (closed 21 / partial 2 / regressed 0 / 不採用 1、新規 should 3 / nit 14)。2 巡目: **GO** (must-fix 0、1 巡目の 19 件は closed 15 / partial 3 / regressed 1、新規 should 8 / nit 6 は親がすべて適用)。3 巡目は起動していない |

段 6 の所見の型は前回 (21b 版) の wave と同じく「新旧の現在形の併存」が主で、版の must-fix は §9 と §8 B-8 の小項目に残った「未実施」、
検証相の種、判定集合 30 枠の帰属の書き方だった。30 枠は本走 24 (独立 8 反復 × 3 workload × extime 10 s) と校正の完走 6 (各 workload の
extime 6 s / 10 s 各 1 回) の和であり、全体を本走の条件へ帰属させない書き方に全箇所を揃えた (日本語草稿の wave も段 6 で同じ型を must-fix にしていた、entry 1801)。
焦点 2 巡目は、前版 §8 B-2 の小項目にも版名を冠した文の中の現在形があることを見つけた。親はこれを §10 (P2) の境界事例の 2 か所目に数え、
訂正 0 件の判定は保った (この読みを採らなければ訂正は 2 件になる、と版の §10 に書いた)。

## 2. 検査・実測

- 焦点走 1 (計算ノード `15122.nqsv`、Elapse 44 s、変更 test + meta-test 2 + DW-O26 の inventory 4 群): 607 passed / 1 failed / 3 skipped。赤 1 件は
  `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` が作業木の未追跡の版下書き
  `docs/paper-story/2026-09-21c.md` を余分な変更と数えたもの (親の未 commit docs が原因、実装とは無関係、commit 済みの木の受入では出ない)。
- 全史 provenance 監査: 統合 commit 後 12,363 件、docs commit 後 12,364 件、図の commit 後 12,365 件、main 取り込み後 12,398 件、いずれも新規違反なし。
- 変異 (独立 clone、D1009、`76b60f6e1`): probe で観測 → final (spec sha `4b8cc7ea…`) で baseline PASSED、**M1〜M8 KILLED 8/8 (期待 node 完全一致
  matching 9/9)、M0 SURVIVED** (M0 は無害な comment 1 行の対照)。erratum: M1 の事前登録は T10 と T11[invalid-calendar-day] の 2 node だったが、
  T13 も理由文字列の変化 (診断的な赤) で落ちることを probe で観測し、final の期待集合に足した (受理集合の縮小として殺したのは正例 T10)。
- 状態 JSON の検査 (login、出力なし): 生成器の `load_states` (anchor の一意性・自由文検査) → `make_figure` → 実寸 `check_figure_layout` を通過、27 項目。
  最終の本文 bytes (sha256 `0317911a…`) に対して取り直した。
- fig3c の生成 (login、2026-09-21 16:25 JST、rc=0): provenance の入力 sha256 は commit 済みの本文・状態 JSON・生成器の現物と一致、描いた項目 27、
  caption は汎用の固定文。PNG を目視で確認 (重なり・はみ出しなし)。3 成果物の SHA-256 は `docs/paper-story/figures/README.md` の fig3c 節。
- claim-evidence の入力版 sha256 は最終の本文 bytes で再計算して書き込んだ (`0317911a…`)。
- `tools/check_docs.py`: 違反なし (各段階)。`python3 tools/spool_fold.py --dry-run --show-diff` rc=0 (記録 commit 前)。
- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、記録 commit 前): rc=1。hit は既存の official 床値 campaign の 3 file
  (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/`) と、既存の図・稿・事前登録・decisions だけで、本 wave の新規・変更
  file は 0 件。placeholder (`{{`) は fragment の D 参照だけで、成果物には無い。
- 受入全走は本記録の時点で未実施。記録 commit を含む tip で land 前に 1 回投入し、結果は land の受領証が持つ。child-green でなければ land しない。

## 3. 状態 JSON の置き場

`tools/` 配下の非 Markdown は D95 の機械判定 (`tools/check_ai_provenance.py` の `_is_implementation_path`) で実装面になり、Codex author の trailer を要する。
Codex が利用上限で使えないので、人が本文から写すデータである状態 JSON は `docs/paper-story/figures/` に置いた (生成器は `--states` で任意の repo 内 path を読む)。

## 4. Codex の利用上限と段 6 の代替

段 6 レビュー B を Codex で起動したところ即終了した (receipt: `outcome=launcher_error`、`codex_exit_code=1`、model call 1、出力 0。events:
「You've hit your usage limit … try again at Sep 26th, 2026 7:35 PM」)。親の裁定: 実装は段 5 で Codex author 済みなので D95 には触れない。DW-S06-A の
2 本のレビューは Claude opus の独立 context (read-only 指示、同じ prompt・レンズ・出力形式) で代替し、実装面の must-fix が出たら停止する方針とした
(出なかった)。**別系統モデルによる独立性はこの分だけ弱い。** 上限解除 (2026-09-26 19:35) の後に Codex で段 6 を取り直すかはユーザーの判断に委ねる。
従量経路 (API キー等) には切り替えていない。

## 5. 持ち越し (次の状態図で直す)

- **汎用 caption の文言 (レビュー B の should-fix、焦点 2 巡目の nit16):** `GENERIC_CAPTION` の "each item's sublabel carries the recorded judgment words and limitations"
  は、副ラベルが記録された限定を網羅するように読める (B-8 の限定は単独稿 §4 の 11 項、副ラベルが運ぶのは 2 項)。直すのは生成器の変更で D95 により
  Codex author を要し、この wave では Codex が利用上限だったので見送った。fig3c は現行の文言のまま生成し、21c の本文 (Fig 3c についての注意) と
  figures README の fig3c 節に「副ラベルは要約、限定の正本は本文 §8」と書いて補った。次に状態図を作る wave で、caption の該当句を
  「副ラベルは記録された判定語と限定の要約」へ直すことを持ち越す (後継関係の表記 "Successor to fig3" に fig3b を含める nit も同じ機会に)。
  台帳 ID は起票しない (`DW-S04`: scope 外の real 所見は insight に記録する)。
- **Codex による段 6 の取り直し:** §4 のとおりユーザーの判断に委ねる。

## 6. 親の誤り (near miss、実害なし)

1. author-1 の起動で、detach script に引数つき launcher を 1 path として渡し spawn 失敗、続けて `--artifact-root` 未作成で rc=2 即終了 (子は未起動)。
   dry-run を launcher と同じ引数で先に通せば避けられた (DW-O01 は dry-run を要求済み)。author-2 で再投入。
2. 変異用 clone の作成で、統合 commit の 40 hex SHA を `rev-parse` から写さず推測補完した (F1031 と同型)。update-ref が nonexistent object で拒否し、
   実害なし。`rev-parse` で読み直して作り直した。failures へ再発として記録する (spool fragment)。
3. 作業ファイルと handoff に推定の時刻 (15:05 など。実際は 14:17) を書いた。14:36 に file の mtime で訂正した。
4. 下書き役の出力に、21b の起点より後の出来事を「2026-09-21 版で」と書く時点語の誤用が複数あり、親が監査で直し、稼働中の下書き役へ注意を送った。

## 7. 着地前に main が進んだこと

着手後に local main は `24ca912ee` まで進んだ (entry 1796〜1802: /cleanup-branches の引き渡し、D2206 = 第 29 回 /rulings 全 16 項、/next-tasks の是正、
[T-2835]、[T-2826] の計測設計の凍結、日本語草稿の B-8 反映、mocc の X/P 計装の pin 候補の前段 = D2207)。記録の前に固定 SHA で取り込み (`691be812d`、
競合なし)、版の資料締切は依頼どおり起点 `d99c556df` に固定した。起点後の着地は README の stale 注記に 3 項として積んだ (開発基盤・運用 5 件、日本語草稿の
更新、mocc X/P 計装の前段)。いずれも版の状態語を動かさない。21c 版 §5 の「日本語草稿は B-8 を反映していない」という注記だけが、執筆時点の事実のまま
古くなった (stale 注記の項 2)。

## 8. 言わないこと

- 新規計測・新しい主張は無い。B-8 の `pass` は観測した 30 枠の trace についての判定の記録で、未観測の条件・性能・S-1 (iv 付属) の充足・B-1 の変更へ広げない。
- fig3c は状態の模式図で、数値を描かず判定を再計算しない。fig3b と前後比較する材料にしない。
- gate・検査・台帳の追加、英語稿、2 本目論文の版は行っていない。**レビュー・焦点再レビューの「未確認」範囲は検証済みとして扱わない。**
