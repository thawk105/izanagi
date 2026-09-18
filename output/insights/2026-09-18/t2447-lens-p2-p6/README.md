# [T-2447] D1893 の P2 / P6 を dev-wave 手順書へ収容した — 段 3・6 のレンズ 1 本を「過剰・削除」に固定、根拠を示せない scope 外所見は起票せず記録のみ

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-18
- wave: dev-wave-t2447-lens-p2-p6 (branch `worktree-dev-wave-t2447-lens-p2-p6`)
- 起点の裁定: D1893 (ユーザー裁定 2026-09-09。P2 と P6 を採る。P4 = 変異 matrix の義務の限定は定義し直してから採る → 本 wave は触らない)、D1798 (P1 の収容と P2/P4/P6 の裁定候補化)、D782 → D730 (予算手順)、D227 (原資の条件)
- 基準: local main `d2ebef7a407dc6be61622ed596cf08b8b518f606`、収容 commit `de7cc6424`
- 原典: `output/insights/2026-09-08_dev-wave-research-gate/RESULT.md` (P2 / P6 の提案と「なぜ止まらないか」)

## 0. 目的と結論

D1893 で採った 2 件を `docs/dev-wave/` の該当節へ収容した。docs のみ、実装面 0 byte、command 入口・`tools/check_docs.py`・テストは不変。

| 項 | 収容先 | 収容後の文言 (逐語) |
|---|---|---|
| P2 (段 3) | `docs/dev-wave/workers.md` DW-S03 | 正しさ境界・整合・実効性と過剰・削除（研究前進・実測欠陥への対応、削除・局所修正の可否）に分け、⏎親 brief 自身も検査対象だと明記する。 |
| P2 (段 6) | `docs/dev-wave/workers.md` DW-S06-A | 1 本は `DW-S03` の過剰・削除レンズに固定する。 |
| P6 | `docs/dev-wave/core.md` DW-S04 | 全段の scope 外 real 所見は実装せず、研究前進か実測欠陥を資料/実測で示した場合だけ設計択一・推奨案付き⏎裁定パッケージでユーザーへ返し、他は起票せず insight に記録する。 |

予算は増枠なし。L1 10,622 → 10,616 (段 5) → 10,623 (段 6 fix) / 10,625、L1.5 9,696 → 9,660 / 9,696 (`verbatim/layer-bytes-*.txt` は段 5 時点、段 6 fix の +7 は `verbatim/out-focus.md` が再計算)。commit は 2 つ: 段 5 `de7cc6424` (7 編集)、段 6 fix `2d953f228` (DW-S04 の 1 行)。

## 1. この wave が判定しないこと

- P4 (変異 matrix の義務を防壁・台帳・受入判定の実装面に限定) の定義し直し・採否。DW-S04 の免除条件と DW-M01 は 1 byte も変えていない。
- P2 / P6 の効果 (起票数・土台 wave の減少)。持ち越し T の件数 (D1798 時 345 → D1893 時 567 → 本 wave 時 638) は蓄積の兆候であって研究停滞との因果ではなく、効果測定の制度も作らない (段 3 A-5 / B-3、D1798 A-9 と同じ)。
- `docs/skill-self-improvement.md` routing の改訂 (全文 pin、scope 外)。
- 段 6 レビューの常時 2 本化、DW-S06-C (焦点再レビュー 1 本) の変更。

## 2. 収容の形と D1893 との対照

- **P2 = 既存 2 レンズの置き換え。** 旧「正しさ境界と整合・実効性を分け」の 2 本のうち「整合・実効性」側を「過剰・削除」に替え、落ちる「整合」「実効性」は正しさ側へ寄せた (3 本目にしない)。過剰・削除レンズの問いは原典 §なぜ止まらないか 2 の「この追加は実測欠陥に対応しているか、削除・局所修正で済まないか」を D1798 の研究前進と結線して書いた。段 6 は DW-S06-A に 1 行を足し、定義は DW-S03 への参照に倒した (D227 条件 3)。
- **P6 = DW-S04 の 2 文目の置き換え。** 「根拠が無い」を判定可能にするため「資料/実測で示せる場合だけ」とした (段 3 B-1)。「資料」が静的に確認した正しさの破れを覆い、DW-G05 第 2 段落の「資料/実測で確認できる」と同じ語彙になる (段 3 A-3)。研究前進は DW-S01 の定義で読む。P6 は起票判断であって停止 (DW-STOP)・受入・変異義務の免除ではない。
- **段 4 では解釈記録に留め、段 6 で文言へ入れた 2 点**: (a) 発見段を問わず (段 6・8 で初出する scope 外所見も) 同じ基準で親が裁定する — D1893 に段の限定は無い。段 4 は「段を問わず」(+15 bytes) が L1 を超過するとして解釈記録にしたが、段 6 の 2 レビューが同じ must-fix (RA-1 / RB-1: 段 8 の自己改善 routing が迂回路として手順書に残る) を出し、RB-1 の「全段の scope 外 real 所見は」(+7 bytes) で正本へ入れた。(b) 根拠なしの所見を段 8 の自己改善候補へ名前を変えて送り、routing 2 (裁定パッケージ) を起票の迂回路にしない — 「場合だけ」と「他は…記録する」がこの経路を閉じる (焦点再レビュー §逐語検証 (a))。候補の記録自体は既存契約と両立する。
- **「示せる」→「示した」** (段 6 RB-2、0 bytes): 提示可能性の自己申告でなく、提示済みの資料・実測で判定する。静的反例は「資料」として残る。
- **D1893 より広い点**: 対象を「real 所見」に限る (refuted 所見に記録義務を広げない)、記録先を insight に限る。**狭い点**: なし (段 2 plan「D1893 との意味差」、段 3 A-1〜A-3)。

## 3. 予算の原資 (D227 の 3 条件)

| 削った記述 | 担い手 (同一読点) | 上位互換の逐語 |
|---|---|---|
| DW-S06-A「所見ゼロの扱いは `DW-M02`。」(−34) | DW-M02 (段 6 U) | 見出し「所見ゼロの裏取り」と本文全体 |
| DW-S06-C「、成果物影響を書けない所見を must-fix にしない」(−61) | DW-G05 (段 6 U) | 「示せない must-fix は nit/backlog とし、追加 review を起動しない。」 |
| DW-S06-B「権限、reasoning/sandbox、テスト弱体化禁止、受理集合、期待赤、波及報告、」(−99) | 入口「段 5 の実装子契約 `DW-S05-A`、`DW-S05-B`、`DW-S05-C` を全文継承する」+ 段 6 U の S05-A/B/C | 権限 = S05-B、reasoning/sandbox = S05-A、他 4 要素 = S05-C (段 3 A の対照表) |
| DW-S09「再試行・停止は `DW-O23` に従い、」(−43) | 入口終端「段9は `DW-O23` に従い、競合時は再試行する。」+ DW-O23 (段 9 U) | 再試行・停止の手順本文 |
| operations.md preamble「該当節を操作直前に読み、停止条件を迂回しない。」(−70) | 入口の読み込み契約・凍結境界 (L0) | 「条件成立操作の直前に条件を再評価して表の節を読み」「規定の停止条件…を迂回しない」 |

3 者 (plan、レンズ A、レンズ B) とも欠落要素なしと照合した。段 3 B-2 の「E1 を短縮して E3 を不要にする」案は、短縮文が「親 brief 自身も検査対象だと**明記する**」(子への明記義務) を「親 brief も検査する」へ落とすため採らず、括弧内の短縮だけを採った。

## 4. 段 2 / 段 3 の所見と裁定

段 2 plan (`verbatim/out-plan.md`): byte 差は親の実測と一致、原資 4 件は D227 成立、E1 の実効性保持を推奨。段 3 レンズ A (正しさ境界・整合、`verbatim/out-consult-A.md`) A-1〜A-6、レンズ B (過剰・削除、`verbatim/out-consult-B.md`) B-1〜B-5 はすべて real。裁定の表は `verbatim/s4-ruling.md`。要点: 実効性を残す (A-1/B-2)、「資料/実測で示せる」(A-3/B-1)、段を問わず・routing 迂回禁止は解釈記録 (A-2/B-5)、本 wave の段 6 は 2 本 (A-4/B-4)、因果表現の訂正 (A-5/B-3)、routing は全文 pin で不変 (A-6)。

## 5. 段 5 の実走

- 親が 7 編集を旧文一致で置換 (docs-only、子ゼロ)。`git diff --check` rc=0。
- `python3 tools/check_docs.py` 違反なし。層予算は `verbatim/layer_bytes_probe.py.txt` (check_docs の関数で計算) で前後を実測。
- commit `de7cc6424` (message preflight rc=0、full provenance 監査 11,207 件・新規違反なし)。
- 焦点走 (`verbatim/focus-run-s5.log`): `orchestrator/tests/test_check_docs.py`、`test_dev_wave_launch_authority.py`、`test_codex_worker_launch.py` を run_tests.py 経由で計算ノード (4994.nqsv) に投入、855 passed / 3 skipped、rc=0。skipped 3 件は `docs_bytes` の growth hold (実 check_docs.py を回す test) で、親が check_docs.py を直接走らせた rc=0 が同じ検査を担う。
- 実装面差分ゼロのため変異 matrix は免除 (DW-S04)。受入全走は land 前に投入する (結果は worklog)。

## 6. 段 6 レビュー (2 本 + 焦点再レビュー 1 本)

本 wave は所見の受理集合 (何を裁定パッケージへ返すか) を変えるので、docs-only でも DW-C00 に従い review 子を省かなかった (段 4 A-4 / B-4)。docs-only 全般への一般化はしない。

| 所見 | 要旨 | 裁定 | fix 後 |
|---|---|---|---|
| RA-1 = RB-1 (must-fix) | P6 が段 4 の規則として読め、段 8 の自己改善 routing (裁定パッケージへ返す) が根拠なし scope 外所見の迂回路として手順書に残る。段 4 の解釈記録では将来の wave に届かない | real・採用。RB-1 の最小是正「全段の scope 外 real 所見は」(+7 bytes) | closed |
| RB-2 (nit) | 「示せる」は提示可能性の自己申告を残す | 採用。「示した」(0 bytes) | closed |
| RB-3 (nit) | 明記義務を保った 172 bytes の E1 で E3 を不要にできる | 不採用。読みやすさと残 36 bytes を優先、義務差なし | closed (不採用裁定) |
| RA-2 / RA-3 (記録) | 原資に義務欠落なし。pin・構造・予算の衝突なし。plan v2 と実 file は byte 一致 | 記録 | closed |

- fix commit `2d953f228` (DW-S04 の 1 行、L1 10,623 / 10,625)。焦点再レビュー (`verbatim/out-focus.md`) は 6 所見すべて closed、退行なし、派生値 (+7、10,623、残 2) の再計算一致。
- fix 後の焦点走 (`verbatim/focus-run-s6-after-fix.log`): 855 passed / 3 skipped (同じ growth hold)、rc=0。full provenance 監査 11,208 件・新規違反なし。

## 7. 工数と実走

- codex 子 6 本 (plan 1、consult 2、review 2、focus 1。全段 `gpt-6-astra`、plan / consult は `reasoning=medium` 明示、review / focus は docs 権威由来)。子はすべて read-only の静的検査。
- 親の実走: check_docs.py 3 回 (編集前・段 5・段 6)、層予算 probe 3 回、焦点走 2 回 (計算ノード 4994.nqsv / 5016.nqsv、pytest 部分は各 16.65 / 13.26 秒)、provenance 監査 3 回 (preflight 2 + full 2)、受入全走 1 回 (land 前、結果は worklog)。
- 所要: 06:12 起動 → 段 6 閉 07:16 (JST)。worktree 作成に 3 分 46 秒 (並行 add 6 本)。

## 8. 保証しないこと

- P2 / P6 が起票の連鎖を実際に止めること。効果は未測定。
- 段 6 U の dispatch に DW-S03 は含まれない。DW-S06-A の参照は同一 file 内の節への pointer であり、裁定後に段 4 から再開する型は前 wave の段 3 成果物 (レンズ定義を含む) を流用する前提で成り立つ。inline 化は約 100 bytes で予算外 (段 2 plan、段 4 裁定)。
- 段 8 preflight の必読集合に DW-S04 は無い。「全段の」は規則の適用範囲を明記したものであり、段 8 での再読を強制する機構ではない (焦点再レビュー §逐語検証 (b))。
