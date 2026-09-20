# 段 6 裁定 — レビュー A / B の所見 (real / refuted、採否、fix の指示)

作成 2026-09-20 21:3x JST (親)。入力 = `codex/s6-review-A.md` (must 3 / should 2、NO-GO)、`codex/s6-review-B.md` (must 2 / should 4、NO-GO)、`s1-brief.md` §6 (P1)〜(P9)、事前登録 v1。

## 0. 所見の裁定

| # | 所見 | 裁定 | 採否・反映先 |
|---|---|---|---|
| A3 / B1 | bench 失敗後に attempt-2 を自動生成 (v2 継承)。事前登録 §5「bench を再生成しない」に違反 | **real (must-fix)。原因は親の author prompt (D2160 の規則を持ち込んだ)。author は差異を開示していた** | fix: attempt-2 を撤去。bench 失敗 (rc≠0 / timeout / witness 欠落) は当該 rep を `bench_failed` の 1 attempt で終端し、規約不適合として開示。`--resume` は失敗 rep を再走しない。`effective_attempt` (最後の attempt を有効枠にする集計) を撤去し、rep ごとに attempt は 1 つだけ |
| A1 | 校正の bench 失敗 (実際に開始して失敗) が pass を妨げない | **real (must-fix)**。§5「bench 失敗が 1 件でもあれば pass にならない (§6.1)」は verify の種別を限定しない。厳格読み (P10) を採る | fix: 判定集合の cohort (校正 + 本走) に bench 失敗 (開始して失敗。`not_run` = 打ち切りで未開始は除く) が 1 件でもあれば pass にならず未確定 + 開示。校正の bench 失敗を `summarize` が検出したら `stage_B_allowed=false` + 理由 (§5 により本走は pass になれない → §6.4 の新 cohort) |
| A2 | 判定集合外 record の混入 / sha 不一致が失格判定より優先され、有効な anomaly が未確定に丸まる | **real (must-fix)**。§6.1 の評価順は失格が先、規律 2 (anomaly は即 reject) | fix: 失格は、対象 (target / gate / workload 整合) の calibrate / verify / reverify record で verifier 完走のものについて、混入・sha 不一致・規約不適合の有無に**関わらず先に**評価する (P11)。混入・sha 不一致は pass を妨げ未確定へ落とすだけ。`in_judgment_set=false` の record (prerun) は失格評価に入れないが、calib / verify の木に在れば混入として開示 |
| B2 | `verify` job 段の identity 不一致 (`<job>/result.json`) を collector が読まず、`--resume` 後に pass になりうる | **real (must-fix)** | fix: `summarize` は `<input>/verify/*/result.json` と `<input>/calib/*/result.json` (job 段の失敗 record) も読み、identity 不一致・実行失敗を規約不適合として開示し、pass を妨げる (未確定)。§2.4「不一致の verify は判定集合に入れず規約不適合として件数を開示」+ §6.1 未確定 |
| A4 | (P2) の本走 3600 s は親の追加解釈。事前登録は校正 3600 s (§11) と上限 1800 s (§4.4 / §12、D2186 (5)) を書く | **real (should)。(P2) を改める** | fix: verifier hard timeout = **校正 3600 s (§11 の想定どおり)、本走 1800 s (§12 / D2186 (5) の上限そのもの)、再検証 (§6.4、同一 trace 1 回) 3600 s (D2160 継承、事前登録は値を置かない)**。判定の結果は変わらない (本走 1800 で未完走 → 再検証 1 回で同じ verdict に到達する。変わるのは費用) |
| A5 | D2186 項 1 の逐語 file が見出しで切れていた | **real (should)。親の sed 範囲ミス** | 済: `refs/d2186-item1-verbatim.md` を項 1 本文 + 理由まで (50 行) に作り直した (21:3x) |
| B3 | 「6 s 超過→10 s not_run」が helper 単体の検査で実行分岐 (L864〜875) を被覆しない。校正 anomaly の fixture が `phase='verify'` | real (should) | fix: 校正の計画・打ち切り分岐を純関数 (例: `calibration_plan(rows) → 次の extime または (None, reason)`) に切り出し run loop から呼び、selftest はその関数を正例・負例で検査。校正 anomaly の fixture を `phase='calibrate'` に直す |
| B4 | 期待 define を実装の `defines()` から作る自己参照、preservation / bundle 負例の理由重複 | real (should) | fix: 期待 define を literal 6 個で書く。負例は単一理由 (preservation 欠落だけ、bundle 期待値不一致だけ) に直す |
| B5 | `verify --resume` の照合に `in_judgment_set` が無い | real (should) | fix: `check_binding` に `in_judgment_set is True` を足す |
| B6 | setup+hydrate+build の 2400 s は事後検査で、各段の個別 timeout の和は 3600 s を超えうる | real (記録のみ、fix なし)。v2 継承。試走で F_s 30.5 / 31.0 s を実測。校正 job の walltime は §12 の「校正実測の最大所要 × 倍率」で別途決める | insight に記録 |
| A の nit 群 (P3 / P5 / 1800 境界 / 予算式 / identity / 構築経路 / 削除 / P7 / P9 / author 報告) | 攻撃不成立 | 現状維持 |
| B の項目 1〜3 (import・prerun 経路・bindings) | 攻撃不成立。§12 の発効束のうち runner が単独で揃えない項目 (pin と gitlink の一致・raw bytes の保存・承認情報・node 種別・保全先容量・校正 walltime) は親の裁定パッケージで補う | 現状維持、README §発効束 へ |

## 1. provisional 裁定の改訂

- (P2) → 校正 3600 / 本走 1800 / 再検証 3600 (上表 A4)。
- (P10) 新設: §5 の「bench 失敗が 1 件でもあれば pass にならない」は校正・本走を問わず、開始して失敗した bench に適用する (打ち切りによる `not_run` は失敗でない)。校正で bench 失敗が出た cohort は本走を投入しない (pass になれないため)。
- (P11) 新設: 失格 (§6.1 項 1) は、混入・sha 不一致・規約不適合の有無に関わらず、対象の完走 verdict について先に評価する。
- (P1) (P3)〜(P9) は不変。

## 2. fix の投入形

- fix 子 1 本 (Codex、workspace-write、author 木 `.codex/worktrees/t2807-author`、v3 → v4 in-place)。所有 = `probe/verify_phase_runner.py` 1 file。
- 親: 退避 → login selftest → v2→v4 diff → 焦点再レビュー 1 本 (所見ごとの closed / partial / regressed 表) → 試走を v4 で再投入 (runner sha256 を発効束の版に揃えるため。prepare 経路は不変の見込みだが実走で確かめる)。

## 3. 焦点再レビュー 1 巡目 (`codex/s6-focus.md`、22:0x JST) の裁定

| # | 所見 | 裁定 | 採否 |
|---|---|---|---|
| F1 | v4 が「bench 完走・保全済み・verifier 未開始」の rep (walltime kill 等) の初回 verifier 再開経路を削った (v3 L902〜924 にあった)。`verify --resume` は一律 skip、`reverify` は rc / 開始時刻とも None を拒否 → 当該枠が未確定に固定 | **real (must-fix)**。§5 (bench 不再生成) と §6.4 (未完走の再検証 1 回) のどちらにも反しない初回検証であり、fix 1 の副作用 (回帰) | fix 2: resume を 4 分類 ((a) bench 失敗 = 終端、(b) verifier 起動済み = skip、(c) 保全済み・未開始 = 復元 + 初回 verifier 1800 s・`verify_attempt_id=1`、(d) 保全未完了 = 規約不適合で終端)。selftest の一律 skip 肯定 case を 4 分類に直す |
| F2 | 焦点 prompt が指した fix 報告 `s6-fix-1.md` は停止した巡のもの | real (should)。親の prompt の path 誤り (実体は `s6-fix-1b.md`) | focus 2 の prompt で `s6-fix-1b.md` と `s6-fix-2.md` を指す |
| 対応表 | closed 7 / partial 1 (A3/B1 は F1 の回帰で partial) / regressed 0 | — | — |
| 発効束 draft | 指定検算項目すべて一致、runner sha は v4 実体と一致 | — | v5 で runner sha を再生成・再照合 |

fix 2 は 3 巡上限 (DW-O16) の 2 巡目。focus 2 で F1 が closed なら段 7 へ。

## 4. 焦点再レビュー 2 巡目 (`codex/s6-focus-2.md`、22:25 JST) の裁定

- GO。closed 9 (F1 + v4 で閉じた 8 件の維持) / partial 0 / regressed 0、新規所見 0、発効束 draft 全項目一致 (runner sha = v5 実体)。段 6 を閉じ段 7 へ。fix は 2 巡 (上限 3 巡内)。
- 実 trace の復元・verifier 再開経路は未実走 (合成 record と spy)。本走で初めて実走する点は insight §6 の限定 3 に含める。
