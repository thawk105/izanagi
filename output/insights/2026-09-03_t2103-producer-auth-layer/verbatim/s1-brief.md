# [T-2103] 段 1 brief — 凍結 closure 外 raw-record producer の認証層を比較実験で決める

base commit: `4ec3eba04354f9ba86117a2dd488c72d007045e6` (local main)
wave worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2103-producer-auth-layer`

## 1. scope

D1345 が要求する比較実験を実施し、**候補 3 層の拒否能力を同一の変異集合で測って数字で示す**。
測定に必要な最小の候補実装と測定 harness だけを作る。結論が「どの層でも同じ」なら、そう書いて閉じる。

scope 外 (実装しない): 仮想リスク向けの gate・検査・台帳・一般化、5-file pin の恒久的拡張、
認証層の本採用実装、B-4 の実走・qsub・性能測定。

## 2. 確定済みユーザー裁定 (覆さない)

- **D1345** (`docs/decisions.md:42911`): 認証層は候補層の拒否能力を変異で比較してから決める。
  候補は **issuer / raw assembly / frozen consumer** の 3 つ。5-file pin を無条件に広げる案は採らない。
- 一次資料: `output/insights/2026-08-29_t2049-b4-raw-record-producer/verbatim/s4-ruling.md` §4 項 3。
- 規律 2 を緩めない。正しさゲートを弱める変異は採用しない。

## 3. 実測した前提 (brief 前に親が確認済み)

| 事実 | 実アンカー |
|---|---|
| 5-file pin の定義 | `orchestrator/campaign/p3_b4_analysis_path.py:67` `_SOURCE_CLOSURE_PATHS` |
| 同じ 5 path の第 2 の pin (AST 照合) | `orchestrator/campaign/p3_b4_analysis_prereg_consumer.py:98` `_CLOSURE_PATHS`、照合は同 file `:752` |
| closure receipt の生成 | `p3_b4_analysis_path.py:481` `_generate_analysis_source_closure_receipt` |
| producer 本体 (closure 外) | `orchestrator/campaign/p3_b4_raw_record_producer.py`、公開 API は `assemble_b4_raw_analysis` (`:1894`) と `publish_b4_attempt_result(s)` |
| 欠陥は producer 自身が非保証として明記済み | `p3_b4_raw_record_producer.py:65`「producer は凍結された analysis source closure の外にあり、source hash が producer 意味論を識別しない」 |
| 判断値の実体 | 同 file `:77` `_JUDGMENT_FIELDS` (`treatment_fired` / `contaminated` / `protocol_ok` / `execution_disposition` ほか) |
| issuer の封印物 | `orchestrator/campaign/p3_b4_prerun_issuer.py:110` `B4PrerunPublication`。非保証に「commitment は identity/signature/external pin ではない」と明記 (`:116`) |
| 既存の変異集合 | `orchestrator/tests/test_p3_b4_raw_record_producer.py` の `test_m01`〜`test_m18` (T-2049 で 18/18 KILLED 実測済み) |
| 稼働 wave との重複 | T-2102 / T-2141 は worktree・branch・稼働 process のいずれにも不在。近縁の t733 は `artifact_admission.py` / `campaign_lock.py` / `contract_loader_binding.py` で別 file 群 |

## 4. 不変条件

- 5-file pin (`_SOURCE_CLOSURE_PATHS` と `_CLOSURE_PATHS`) の **恒久的な bytes 変更を成果物に含めない**。
- producer の既存受理集合を変えない。既存 29 node の producer test は緑のまま。
- 自己申告 hash を認証根拠にしない (F29 / F36)。
- 測定は実体を名指しした負例で張る。両層 stub で機構を通らず緑になる形を作らない。

## 5. 割れうる前提 (親の provisional 裁定 — 攻撃対象)

- **(P1) frozen consumer 候補の測り方。** 恒久変更が禁じられている層の拒否能力をどう測るか。
  親の provisional 裁定: `DW-O19` の一時変異 (統合 commit 後・`git checkout --` 復元) で実体を通す。
  代案 (別 path の prototype module で模す) は F29 の「模擬で自己 hash・pin を裁定しない」に抵触しうる。
- **(P2) raw assembly 候補が何かを拒否できるか。** 親の provisional 裁定: producer が自分の意味論を
  名乗る形は循環で拒否能力ゼロ。issuer の封印物に束縛すると issuer 候補へ縮退する。
  **この「ゼロ」自体が測定結果**であり、事前に潰さず測る。
- **(P3) 変異集合の設計。** 親の provisional 裁定: T-2049 の M01〜M18 (pinned producer の bytes を
  変える負例) **だけでは層が分離しない** — source hash を取る層は一律 18/18 KILLED になり、
  比較が自明化する。層を分離する負例を最低 2 種足す:
  (a) **別 path の rogue producer** が同形の成果物を組み立てる (path を key にする pin は素通ししうる)。
  (b) **正規 producer の出力を下流で判断値だけ差し替える**。
  正例 (過剰拒否の検出) も 1 件登録する。

## 6. 成果物の形

1. 候補 3 層それぞれの**最小の認証 prototype** (実装子が書く。既存 file の恒久変更を含まない形)。
2. 同一変異集合を 3 層へ当てる**比較 harness** と、KILLED / SURVIVED の matrix。
3. `output/insights/2026-09-03_t2103-producer-auth-layer/` に一次資料 (逐語・変異 spec・report・比較表)。
4. 変更閉包の実測 (各候補が触る file 数・pin 数) を比較表に併記する。
5. 結論の decision fragment (`docs/spool/decisions/`)。差が出ないならそう書く。

## 7. 並列分割方針

段 5 は Codex `role=author` 1 本。編集面は新規 prototype + 新規 test + harness で所有が割れない。
段 2 プラン 1 本、段 3 敵対相談 2 本 (レンズ: (a) 比較の自明化・恒真な保証、(b) 凍結境界と規律 2 の侵食)。
段 6 は敵対レビュー 2 本 + fix。

## 8. 受入・実測環境

login node で受入全走 (`tools/dev_wave_wait.py acceptance`)。計算ノード投入は不要 (実走・性能測定なし)。
