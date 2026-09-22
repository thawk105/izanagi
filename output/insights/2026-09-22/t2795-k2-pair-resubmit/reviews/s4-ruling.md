# 段 4 裁定 — [T-2795] K2 同 job pair 再投入 (2026-09-22 08:5x JST、mtime で確認)

段 2・3 は省略 (DW-C00 軽量版: 実装面の差分ゼロ、受理集合・正しさ防壁・設計択一に触らない。投入手順は D2205 / D2211 項 1 / D2194 項 2 で確定済み)。
段 4 直前の裁定 inbox 再走査: 最新 `2026-09-22-rulings-full31-verdicts.md` (08:43) の項 1 = 見積りは job Elapse の実測、2 未満は確認待ちにしない。T-2795 の新裁定なし。

- **実装しない** (4→7→8→9)。glue は job root (repo 外、実装面ではない)。変異 matrix は DW-S04 で免除、受入全走は行う。段 6 の read-only レビュー 1 本は残す (DW-C00)。
- (P1)〜(P4) を採用 (brief)。やらない理由の最も強い形:
  - P1「pair 再投入の結果を planner-5 に渡さない」— 渡せば同 job stock という新しい事実で planner が判断できる。しかし D2194 は択 C (直前評価の出所混在) を却下し、4 巡目の入力を round 3 派生物に固定した。4 巡目の job 自体が同 job stock を持つので R0 への答えは 4 巡目の中で得られる。採用。
  - P2「既知値でも評価」— 既知値 10 なら pair 再投入と情報が重なる。しかし出力を見てから評価を選ぶと選択の偏りになり、D2172 は「新規生成 1 回」を評価する認可である。結果を見る前に固定する。採用。
- **停止規則 (結果を見る前に固定):**
  1. pair 1 本目は 1 回だけ投入する。submit 失敗 (qsub rc≠0、job が走らない) も含め再投入しない。
  2. 成立 = WAL で候補 (variant `002642c7ac96`) が verify `certified=true` ∧ terminal `commit`、かつ stock (variant = `variant_id(stock genome)`) が certified ∧ terminal `commit` ∧ BUILD_START `src_token == "stock"`。job rc・driver の stdout 行・campaign id からは判定しない。
  3. 不成立なら 4 巡目は投げず、認定せず報告して止める (D2187)。新しい不整合は D2205 の再訪条件 (結合検査の stub 境界の切り分け) を次の一手に書く。
  4. 成立なら 4 巡目: 入力組立て → planner-5 1 回 → coder-5 1 回 → proposal-5 → production 検査 3 本 (`assert_closed_proposal_schema`、`validate_backoff_preflight` accepted、`load_proposal_file`)。どれかが拒否したら再生成せず停止。
  5. 4 巡目投入前に pair 1 本目の実測 Elapse で見積りを取り直す。合計が 2 node 時間以上なら確認を取る。
  6. 4 巡目 job も 1 回だけ。判定は 2 と同じ (候補 variant は proposal-5 の genome)。
- **記録:** 新 insight `output/insights/2026-09-22/t2795-k2-pair-resubmit/`、round 3 README 末尾に追記 1 節、`docs/phase3.md` 項 4 に 1 行、worklog fragment。decisions / failures は新しい設計判断・失敗が出たときだけ。
