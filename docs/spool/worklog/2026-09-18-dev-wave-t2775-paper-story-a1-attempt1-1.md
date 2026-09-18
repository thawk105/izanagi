---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2775-paper-story-a1-attempt1
seq: 1
title: [T-2775] 論文ストーリー README の stale 注記へ A-1 sized 本走 attempt-0001 の完走を 3 件目として積んだ — 同版 §8 の「本走未投入・認可据え置き」は執筆時点で真、非認証 lane (`formal=false`) のままで充足・formal 化・再認可は判定しない (docs のみ、branch worktree-dev-wave-t2775-paper-story-a1-attempt1、実装面差分ゼロ = 変異 matrix 免除)
---

## 本文

- ユーザー依頼は「[T-2775] (P2、entry 1636) 論文ストーリーの A-1 状態を attempt-0001 の事実で更新する (docs のみ) —
  `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」節へ D1858 に従い積む (新しい日付の版は作らない):
  D2120 項 3 が 1 attempt を認可し、attempt-0001 (job 4939 / 4940 / 4941、source d2ebef7a4) が 2026-09-18 に 3 workload とも
  valid=true / errors=[] で完走、登録済み解析は 3 workload とも resolved-above-floor (符号 +/+/−)、非認証 lane (formal=false) のまま。
  材料は `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md` §7。A-1 の充足・formal 化・本走認可の判定は含めない
  (認可はユーザー手番、D2044 項 8)。claim-evidence 系列は凍結物なので上書きせず、同節から指す。着手直前の local main から fresh
  worktree を作る。規律 2 を緩めない。本題の追記だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた。** 同節の項目数を 2 → 3 に更新し、3 件目 (A-1 attempt-0001 の完走) を既存 2 項と同じ形式で積んだ。新しい日付の版・
  claim-evidence・results・figures は作らず、凍結物 (`2026-09-17.md`、`claim-evidence/2026-08-26.md`) は 1 byte も変えていない。
  decisions fragment 0 (新しい設計判断なし)、failures fragment 0 (事故なし)。
- 項の骨子: 同版 §8 A-1 項の見出しと「着地済みの正典は無い」(同じ趣旨は §0 前進 10・§2 (g) 要点 2・§2 第 2 幕・§6・§9 表) は
  執筆時点で真 → D2120 項 3 (2026-09-17) が 1 attempt を認可 (D2044 項 8 の据え置き条件は entry 1590 / `ad83b108b` で成立) →
  [T-1505] が 2026-09-18 に attempt-0001 を投入し 3 workload とも `valid=true` / `errors=[]` で完走 (再投入なし) → 一次資料 2 箇所
  (insight と公開 leaf) → 登録済み解析の分類 `resolved-above-floor` ×3・符号 +/+/−・`variance_plan_breach=false` ×3・verifier 0 anomalies
  (規律 2 の判定で性能の判定ではない) → **変わらないこと** (`formal=false` / `promotion_prohibited=true` の非認証 lane のまま、
  「A-1 の値がある」とは書けない区別は動かしていない、充足・formal 化・昇格・再投入・再認可は判定せず認可はユーザー手番、
  descriptive 出力を headline 値・横断結論・C1 の再現判定にしない、§7 のチェック項目 2 つは有効) → claim-evidence 2026-08-26 の
  A-1 行は旧 v2 policy 前提の凍結物で本 attempt を反映していないと明記。
- 一次資料からの検算 (版の記述を出所にしていない): 公開 leaf `result.json` で 3 workload とも `valid=true` / `errors=[]` / n=30 /
  `resolved-above-floor` / `variance_plan_breach=false`、対差平均 +1,591,948.5 / +448,830.17 / −576,749.77 tps、
  `measurement_source_commit` `d2ebef7a4`; `receipt.json` で job `4939.nqsv` / `4940.nqsv` / `4941.nqsv`、`formal=false` /
  `promotion_prohibited=true`。実装 commit `ad83b108b` は main の祖先。§ 番号は 2026-09-17 版の H2 / H3 / H4 見出しで照合し、
  起草時の誤り 2 件 (§5 → §2 第 2 幕、§10 → §7) を commit 前に直した。
- 観察 (直していない、欠陥ではない): 公開 leaf `result.json` の最上位 `authority` は schema v3 の固定値 `exploratory` (materializer が
  `!= "exploratory"` を拒否する契約) で、policy の `authority.result_authority` (`sized-preregistered-descriptive-only`) とは別欄。
  README では両方の出所を明示して書いた。
- 段構成: 軽量版 (段 1 → 4「実装しない」= 親が docs 本文を書く → 7 → 8 → 9)。codex 子 0 本。裁定 inbox の再走査 (段 4 直前) は
  本題と無関係な 2 件のみ。`python3 tools/check_docs.py` は記録 commit 前に違反なし。受入全走は land の `dev_wave_wait.py acceptance`
  で 1 走 (結果は land の受領証)。

## 次の一手差分

### 完了

- [T-2775] README の stale 注記へ A-1 attempt-0001 の完走を 3 件目として積んだ。充足・formal 化・再認可は判定していない。
  remaining: none
  base: a9fe73b168cb0bb6084051b7e84424db666b05d318b4f8652a05bf9ee2811091
