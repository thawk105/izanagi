# 段 4 裁定 — A-1 balanced5 sized attempt-0002 (2026-09-19 22:05 JST)

## 決定の要約

1. **attempt-0002 は既存 submit 経路では投入できない (承認前提を覆す新事実、相談 B 所見 1、親が現物で確定)。**
   `orchestrator/campaign/paper_story_a1_paired.py` の `_assert_no_prior_v3_bench_start` (呼び出しは `_run_submit_v3`、
   intent 作成・qsub の前) は、policy 固定の durable base `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement`
   直下の先行 attempt を走査し、`barrier/bench-go.json` (study_id 一致)・`barrier/ready/{3 workload}.json`・
   `barrier/bench-start/{3 workload}.json` のいずれかがあれば `prior attempt reached the bench barrier; group rerun is prohibited`
   で拒否する。attempt-0001 はこの 3 種すべてを持つ (現物を `ls` で確認)。この gate は commit `abff80d1b` (2026-09-03、A-1 pilot の
   3 job 分割) が**規律 2 の穴 (測定済み workload の再投入) を塞ぐ**ために入れたもので、受理を狭める方向のみ・列挙理由の再走を
   bench 開始後は拒否する設計である。認可済みの独立再現と失敗後の再走を区別する入力を持たない。
2. **拒否は intent・attempt root・qsub のいずれも作らない (副作用なし)。** `_run_submit_v3` は lexists 検査 → 本 gate → intent 書込の順で、
   gate はその前段の読取り検査 (`_assert_ccbench_acceptance`、`_parent_porcelain`、`_validate_attempt_root`、hydrate root の
   `is_dir`) だけを経て呼ばれる。したがって**既存経路を 1 回実走して拒否を実測しても、1 attempt の認可は消費されない** (qsub に達しない)。
3. **裁定: 既存経路を 1 回だけ実走し、拒否本文 (rc・stderr) を逐語で記録して「submit 層で落ちた」として止める。** 予測を実走 rc と
   書かない (F29、相談 B 提案 1)。再投入・gate 緩和・過去証拠の移動/削除・base/policy の変更のいずれも行わない (ユーザー裁定
   「落ちたら再投入せず報告して止める」、規律 2、DW-STOP)。
4. **射程判定: (c) 一部が絶対規律の射程内。** 通す手段は「gate の受理集合を広げる (規律 2 由来の防壁)」「policy/事前登録の束縛を変える」
   「先行 attempt の証拠を base から動かす」のいずれかで、最初の 1 つは規律 2 の射程、後の 2 つは凍結物の改変または証拠の改変であり、
   いずれも本 wave の scope 外 (「既存 submit 経路」「追加 gate は scope 外」)。相談 2 本 (A: 正しさ境界、B: 手順) のどちらも
   「今回だけ通す」案を支持せず、B は明示的に「過去証拠の移動・削除、study／base の変更、gate 緩和で今回だけ通さない」とした。
   したがって DW-S04 に従い、新事実を添えて設計択一・推奨案付きの裁定パッケージをユーザーへ返す (実装しない)。
5. **成果物の縮小:** 測定値が存在しないので results 系列稿 (attempt-0002 稿・2 attempt の並記) は作らない (存在しない一次資料を
   作らない、相談 B 提案 2)。`docs/paper-story/README.md` の results 表に行を足さない。成果物は記録 insight
   (`output/insights/2026-09-19/a1-sized-attempt2/`: brief・相談 2 本・本裁定・投入前照合表・実走した拒否の逐語・裁定パッケージ)、
   worklog fragment、decisions fragment (ユーザー裁定の記録と本 wave の帰結)、stale 注記 1 件 (`docs/paper-story/README.md`
   「最新スナップショット以後に確定したこと」に attempt-0002 の未投入と理由を 1 項)。

## 相談所見の裁定

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 | import 閉包の変更は 2 file だけ、は誤り (`condition_meaning_gate.py`、`trial_registry.py` 等も変更) | real | 採用。brief の実測を訂正し、記録では「束縛 9 file + pin の bytes 同一」「束縛外の変更 file 一覧」「A-1 到達性は未評価」を分けて書く。「測定は等価」は書かない |
| A2 | 束縛一致だけでは測定・判定の等価性を証明しない | 根拠不足 → 採用 | 「同じ測定条件・解析規則」と「同じ測定値」を区別する文言にする |
| A3 | §6.1 から study 全体で公開 1 回とは導けない、対案 (a) は必ず迂回ではない | refuted (親の (P1) 根拠の一部が弱い) | 採用 (brief の理由を訂正)。ただし所見 B1 により submit-tree の commit 選択は無意味化 (どの tree でも submit 層で拒否) |
| A4 | raw と公開 result の差は `materialization_evidence` だけではない (`limitations` も)。P2 は「宛先既存拒否だけなら」に限定 | real | 採用 (B7 と同一)。今回は materialize に達しないので帰結なし |
| A5 | attempt-0002 の転記元を results 系列規則へ接続する変更が不足 | real | 採用だが今回は稿を作らないので帰結なし。裁定パッケージの付帯論点に含める |
| A6 | D2120 の再認可条件に抵触 | refuted | 記録のみ |
| A7 | 独立性・安定性は成立しない、並記は 6 行表で可 | 根拠不足 → 採用 | 裁定パッケージの「並記の形」に含める |
| A8 | 規律 1・2・6 の記述は brief にある、anomaly 時の停止手順は補記 | refuted (補記は採用) | 今回は bench に達しないので帰結なし |
| B1 | **既存 submit は先行 attempt の bench 到達で拒否する** | **real (親が現物で確定)** | **採用。本裁定の決定 1〜4** |
| B2 | 手順の順序と shell rc 判定の不足 | real | 採用。親が各段の `.done` を読んでから次段へ進む。hydrate → 照合 → submit の順 |
| B3 | hydrate に独自 pin 検査は不要、cache の健全性は今回の verify 出力を残す | refuted / 採用 | verify rc 0 (21:59 JST) を記録済み。hydrate 出力を job dir に残す |
| B4 | 親 tree の clean は CCBench の clean を証明しない | real | 採用。投入前照合に CCBench の HEAD と tracked-clean を入れる |
| B5 | attempt dir 不在だけでは投入前提にならない (intent 不在・権限) | real | 採用。照合に `attempt-0002.intent.json` 不在・base の権限を入れる |
| B6 | idle 65 host から即時開始は導けない、barrier timeout の起点は ready 書込後 | 根拠不足 → 採用 | 記録の文言を訂正 (「見込み」と「保証」を分ける、timeout の起点を正しく書く) |
| B7 | raw／公開 result の差に `limitations` もある | real | 採用 (A4 と同一) |
| B8 | 証拠複製と失敗時成果物の分岐 | real | 採用。今回は submit 前停止なので「未投入・intent 未作成・測定値なし」と書く |
| B9 | F1／F29 対策は必要、F36 の名称対応は refuted | real / refuted | 採用。拒否は実走で実測する。MANIFEST は自身を hash しない。未実施検査を成功と書かない |
| B10 | 図なし P3 は過剰でない | refuted | 記録のみ |

## 変異 matrix・受入

- 実装面の差分ゼロ → 変異 matrix 免除 (DW-S04)。受入全走は記録 commit 後の tip で 1 走 (免除しない)。
- 実 repo を読む test は無し。

## 裁定パッケージ (ユーザーへ返す設計択一。本 wave では実装しない)

**何を決めるか:** 同じ study で 2 本目 (以降) の認可済み独立再現を、規律 2 の gate を緩めずに投入できる形をどう作るか。

- **択 1 — 認可記録付きの gate 解除 (同 study の attempt-0002 のまま):** durable base に認可 record (study_id・attempt 名・裁定日/D 番号・
  source sha) を置き、gate はその attempt 名に限って bench 後の group 再投入禁止を解除する。materialize の排他公開先も attempt 別
  (`…-sized/attempt-0002` 等) を受理する形に広げる。**帰結:** 規律 2 由来の gate と公開先 gate の受理集合が 2 箇所広がる
  (Codex author + 敵対レビュー + 変異 matrix 必須)。事前登録 §6.1 (一度しか作れない宛先) と §6.4 (再走理由の閉じた列挙) に
  erratum が要る。「認可があれば何度でも再走できる」経路を作るので、性能値を見た後の再投入と構造的に区別できない点が残る。
- **択 2 — 独立再現を別 study として登録 (推奨):** policy v3 の複製 (`study_id`・`durable_measurement_base`・
  `materialization_relative_path`・`preregistration` だけを変え、測定条件・arm・n・k・sigma・seed 原像の接頭辞以外は同一) と、
  元の事前登録を sha で引用する短い事前登録 (root seed は §2.1 の規則で study 名から新規に凍結)、source 契約 v2 の study 行の追加。
  **帰結:** 既存 gate・既存 leaf・attempt-0001 の束縛に一切触れない。公開先も base も別なので「一度しか作れない宛先」の設計を保つ。
  比較可能性は policy の測定条件 field の同一性を test で pin して示す。D2096 項 5 の「3 study 目の枠組みは作らない」に対しては、
  固定表への 1 行追加であって登録 API ではないことをユーザーが認めるかが論点。seed が変わるので物理順は attempt-0001 と
  同一にならない (同じ配置規則の別走であり、同一順序の再走ではない)。
- **択 3 — 独立再現を行わない:** attempt-0001 の単一 attempt を限定 L-A1S-4 付きのまま論文素材にする。**帰結:** 反復間の安定性は
  観察としても書けない。実装は不要。

**推奨: 択 2。** 理由: 規律 2 の gate を広げない・凍結物に erratum を要しない・排他公開先の設計を保つ。蹴った帰結: 択 1 は
「認可された再走」と「性能値を見た再走」を機械が区別できないまま gate を緩める。択 3 は研究前進を止める。
**返答例:** 「択 2 で進める。study 名は `paper-story-a1-20260919-balanced5-sized-replication1-v1`、D2096 項 5 は固定表 1 行の追加を
許す」。
