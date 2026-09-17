---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t1505-a1-sized-submit
seq: 1
title: [T-1505] A-1 balanced5 sized 本走 attempt-0001 を D2120 項 3 の認可どおり 1 回投入し、3 workload とも valid で完走した — 登録済み解析の分類は 3 本とも resolved-above-floor (符号 +/+/−)、非認証 lane のまま (docs のみ、branch worktree-dev-wave-t1505-a1-sized-submit、実装面差分ゼロ = 変異 matrix 免除)
---

## 本文

- ユーザー依頼は「[T-1505] (D2120 項 3、ユーザー裁定 2026-09-17) A-1 balanced5 sized 本走を 1 attempt だけ投入する。着手直前の local main から fresh worktree を作る。既存 submit 経路 `paper_story_a1_paired.py submit --study-id paper-story-a1-20260901-balanced5-sized-v1` (hydrate 済み third-party source root 必須) をそのまま使い、どこかの層で落ちたら再投入せず insight に報告して止める (再投入は再認可)。完走したら attempt 成果物・受領証・outer status を `output/insights/` に構造化し、paper-story A-1 の状態欄が書ける形にする。実装差分は既定ゼロ。規律 2 を緩めない。本題の投入だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **全層が実機で通り、attempt-0001 は完走した。** 一次資料は `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md` (時系列・受領証・分類・言わないこと) と公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` (materializer が排他作成した README / receipt / result / .complete.json を byte 保持で複製、sha は `.complete.json` と一致)。decisions fragment は無し (新しい設計判断なし)。
- 投入の形: local main `d2ebef7a4` (= origin/main) の detached submit-tree を job dir 下に作り (submodule 再帰初期化、CCBench 511c9538 tracked-clean、lock)、hydrate を submit-tree 既定 staging root (gflags / glog) と job dir (`--third-party-source-root`) の 2 箇所へ行い、submit → 3 job → complete → materialize を同じ submit-tree から実行した (投入後 1 byte も書いていない)。記録は別の wave worktree。
- 結果 (JST): submit rc 0 06:30 → job `4939` (write-heavy, bnode107) / `4940` (balanced, bnode108) / `4941` (read-heavy, bnode109) が driver rc 0 で 06:36〜06:43 に終端 (投入から 13 分、bench-start barrier は 06:33:15 に 3 本同時) → complete rc 0 06:44 → materialize rc 0 06:45。stdout / stderr 空、failure 受領証なし。3 workload とも `valid=true` / `errors=[]`、各 30 対、6 arm とも verifier `0 anomalies`。
- 登録済み解析の descriptive 出力: 対差平均 (variant − baseline) write-heavy +1,591,948.5 tps (baseline 2,293,174.0)、balanced +448,830.2 (3,862,563.2)、read-heavy −576,749.8 (10,340,146.7)。分類は 3 本とも `resolved-above-floor` (B = 3%)、`variance_plan_breach` 3 本とも false (標本 sd は計画 sigma の 0.70 / 0.97 / 0.85 倍)。符号は C1 の旧環境値と一致するが再現判定ではない。**`formal=false` / `promotion_prohibited=true` の非認証 lane のままで、A-1 の充足・昇格は判定しない。** workload をまたぐ結論は作らない。
- 観察 (直していない): 事前登録 README §5.2 の分類語 (`resolved-beyond-floor (improvement / regression)` / `bounded-within-floor`) と policy / 実装の語 (`resolved-above-floor` / `bounded-below-floor`) は異なるが述語は同値。向きは平均の符号で読む。
- 段構成: 軽量版 (段 1 → 4「実装しない」→ 親の実測 → 7 → 8 → 9)。codex 子 0 本。受入全走は記録 commit 後の tip で 1 走 (結果は land の受領証)。submit-tree と耐久 base `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-a1-balanced5-sized-20260913/measurement/attempt-0001` は原本として残置 (撤去は別途)。

## 次の一手差分

### 完了

- [T-1505] D2120 項 3 の認可どおり sized 本走 attempt-0001 を 1 回投入し、3 workload とも valid で完走した。成果物は `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` と `output/insights/2026-09-18/t1505-a1-sized-attempt1/`。再投入なし。
  remaining: none
  base: 07f41b9c59290457e425e9f087d8e730620d0f8d7dc82bf44b010f633cce8776

### 新規

- {{T:a1-sized-status-column}} **P2・新規**: paper-story の A-1 状態欄 (`docs/paper-story/` 次稿 §8 と `claim-evidence` の A-1 行) を attempt-0001 の事実 (完走・3 workload valid・分類・非認証 lane のまま) で更新する。材料は `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md` §7。A-1 の充足・formal 化の判定はこの更新に含めない。
