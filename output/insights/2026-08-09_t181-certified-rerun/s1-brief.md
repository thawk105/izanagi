# 段 1 brief — dev-wave-t181-certified-rerun

## scope

事前登録済みの T-181 プロトコル (`adjudication-plan-v2.md` §2.5〜2.8 + 訂正 A2〜A7) を**変えずに**、
最終版装置の下で 10 run を再走し、`aggregate` / `verify` がともに `experiment_complete=true` を
返す認証済み台帳を作って [T-184] へ渡す。装置 (`tools/codex_reasoning_ab.py`) は変更しない。

**実装面は無い。** よって Codex `role=author` の実装子は起動しない (DW-C00 の docs-only 相当)。
codex 子は実験そのもの (10 run) と第二読者 1 本だけであり、これらは dev-wave の段子ではない。

## 確定済みユーザー裁定

- 本 wave の起動指示そのもの (認証再走を実行し、[T-184] の判定根拠に使える aggregate/verify を返す)。
- 研究側 wave (`dev-wave-t139-r4-probe`) の計測資源と競合させない。

## 段 1 前の実測 (DW-S01。裁定前提の再測)

1. **2026-07-30 の成果物は、もはや再検証できない。** 今日 `verify` を frozen manifest へ流すと
   rc=24、失敗理由は `snapshot oracle replay mismatch` ではなく
   **`prompt cannot be read`** ×10 である。manifest が指す
   `/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/` (prompt / receipt / score / packet_state /
   verdict_log / verdict_freeze / revealed_map) が削除済みのため。
   → 「再走しなければ認証できない」は真。実測 = `verify-repro.json`。
2. **F61 の根本原因は装置側では解消済み。** 今日 `build-snapshot` → `verify-snapshot` を
   POS / NEG それぞれ 2 回走らせ、**replay 出力が byte 完全一致**することを実測した
   (`probe_snapshot.log`)。snapshot oracle は現行版で決定的である。
   → 装置のコード修正は不要。
3. **未認証の第 2 の原因が判明した (新事実)。** 旧 manifest の失敗理由には
   `manifest schedule_sha256 mismatch` と `manifest.judgments is not an array` も含まれる。
   旧 manifest は top-level の `schedule_sha256` と `judgments` を**そもそも持っていない**。
   つまり旧 wave は、snapshot 問題が無かったとしても認証を通せない形の manifest を凍結していた。
   → 本 wave は manifest を規定の形 (`schedule_sha256`、slot ごとの `judgments`
   = `{slot_id, packet_id, score_input_sha256, combined_verdict_sha256, r1_detected,
   reader_agreement}`) で組む。これも「mismatch の原因の修正」に含む。
4. **認証不能の運用原因は保存場所。** 旧 wave は run root を `~/.t181-bench`、
   packet / verdict / prompt / receipt / score を job tmp に置いた。job tmp は消える。
   → 本 wave は**全ファイルを `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/`
   配下**へ置き、land 後も replay できる状態を残す。home にも job tmp にも置かない。
5. 環境: `bwrap` = `/usr/bin/bwrap` 実在。`codex` = 0.146.0。認証はサブスク
   (`auth.json` の `OPENAI_API_KEY` は未設定、`tokens` あり、`last_refresh` 2026-08-08)。
   歴史 rollout は `~/.codex/sessions` に残存 (POS/NEG の pin sha は build-snapshot が検証済み)。
6. 計算資源: 現在 gen_S に他 wave の 2 job が走行中。R4 probe の qsub は**未投入**。
   本 wave の 10 run はログインノードの codex 実行であり計算ノードを使わない。
   → R4 probe の計測資源とは競合しない。受入全走だけが計算ノードへ dispatch されるため、
   投入直前に `qstat` を見て R4 probe の probe job が走っていれば待つ。受入 lease も取る。
7. 旧 insight `output/insights/2026-07-30_t181-reasoning-ab/` は `FROZEN_MANIFEST` 非登録、
   `--include=*.py` の path pin 0 件、docs 参照は `docs/phase3.md:719` と archive worklog 1 件。
   → bytes を変えずに残せる。新結果は**別 directory** に置く。

## 不変条件

1. 事前登録 (schedule 設計、codebook 3 命題、判定表、決定関数 A6) を**事後に変えない**。
2. 実走前に装置を凍結し、版を receipt へ pin する (F61 恒久対応 (a))。実走中に
   `tools/codex_reasoning_ab.py` を編集しない。
3. verdict を凍結する**前に** `aggregate` を走らせない (旧 wave の既知弱点
   「親が verdict 記入前に機械層の arm 別候補数を観測した」を今回は避ける)。
4. `experiment_complete=false` のまま「認証済み」と書かない。判定表が許す文言だけを書く。
5. 旧 insight の bytes を 1 byte も変えない。
6. home / job tmp に成果物を置かない。

## (P1) 親の provisional 裁定 — 攻撃対象

- **(P1) schedule は旧 wave と同じ block/arm 配置 (s01〜s10、b1〜b5) を再利用する。**
  事前登録の再現であって新設計ではない、という整理。乱数で組み直すと事前登録との対応が切れる。
- **(P2) 親 (私) は旧 wave の結果表を既に読んでいる。** packet→slot の対応は今回新規かつ
  ランダムなので arm は推測できないが、「両 arm とも R-1 を検出した」という事前知識は
  masking を弱める残差である。insight に limitation として明記する。緩和として (3) を守る。
- **(P3) 本 wave は「同一プロトコルの 2 回目の実施」であり、旧 6 run と合算しない。**
  合算は事前登録に無い。

## 成果物影響 (DW-G05)

- 実装しなかった場合: [T-184] (工程別 reasoning policy) は根拠となる認証済み台帳を持てず、
  `docs/phase3.md` の「再走せずに [T-184] の根拠にしてはならない」により前進できない。
  段 6 = high の現行契約は 2026-08-08 のユーザー裁定だけを根拠に据え置かれる。
- 実装した場合に変わる値: 新 insight の `aggregate.json` / `verify.json` が
  `experiment_complete=true`、`decision` が判定表の該当 row になる。既存の certified 選択・
  レポート・台帳の値は変わらない (本 wave は CC 合成の成果物に触れない)。

## 成果物の形

- `output/insights/2026-08-09_t181-certified-rerun/` に、run-ledger / aggregate.json /
  verify.json / schedule.json / codebook 参照 / verdict 系 / 第二読者逐語 / README を凍結。
- `docs/spool/` に worklog fragment (+ 必要なら failures fragment)。
- 実 artifact (snapshot、run root、packet、custodian) は
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/` に残す。

## 並列分割方針

直列。10 run は逐次 crossover が事前登録の要件であり並列化できない。
待ち時間には `output/` を触らない独立作業 (manifest builder の準備、記録の下書き) を充てる。
