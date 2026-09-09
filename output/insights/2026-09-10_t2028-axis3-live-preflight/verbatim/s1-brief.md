# 段 1 brief — [T-2028] 軸 3 の登録済み検索を live preflight まで実行する

**研究前進.** 論文 B-1「合成軸が既知軸最良を超える」の比較対象となる既知軸カタログを、軸 3 (説明可能性)
について埋める。軸 3 は現在 `RW0` で外部 request が 1 本も出ておらず、`RW3` へ向かう次の一段は
契約 (2026-09-01 amendment §3) が定める 2 段 preflight の第 2 段 = **live preflight** である。これが
無いと B5 の予算表も B2 の anchor 到達性も存在せず、本走を計画できない。止めている実測は「軸 3 の
外部 request 0 本」であり、最小差分は「pacing の実装 → 再 `register` → `preflight --live` の実走」。

**scope (本題の実装だけ).**
1. `orchestrator/related_work_search.py` の live 経路へ host 単位の最小間隔 pacing を入れる。
   既存策は `orchestrator/axis1_search/runner.py` の `HostLimiter` (実測済み: arXiv 3.0 / OpenAlex 1.0 /
   DBLP 45.0 秒、`sleeper` 注入 seam つき)。新規汎用機構を作らず同型を移植する。
2. 旧登録 §8.3 / §13.2 N3 が既に登録している「最小 request 間隔と cooldown の観測」を preflight
   report へ記録する (`Retry-After`・rate-limit header・実観測間隔)。**登録済み要件の履行であり新設 gate ではない。**
3. 実装 commit 後に `register` を再実行して新しい seal を発行し、`preflight --live` を login node で実走する。
4. 新日付の実行記録 (`docs/related-work/claim-survey/2026-09-09-axis3-live-preflight.md`) を凍結物として書く。

**scope 外.** 本走 (`run-ready --live`)、resolver、control 評価器、`start_independent_pass` /
`blocked_on_ruling` の executor、B1 の alias 裁定、仮想リスク向けの gate・検査・台帳・一般化。

**確定済みユーザー裁定と既裁定.** Codex `role=author` = D95。B3 = D1206 (「版番号」と呼ばず
「版が取得不能な場合の代替来歴」と書く)。取得は login node、計算ノードは外部網に出られない。
登録の語彙・除外規則を緩めない。規律 2 を緩めない。

**(P1) 親の provisional 裁定 — 攻撃対象.** 本 wave の実行対象を live 本走ではなく live preflight に
限る。根拠は amendment §6 の「U11 の扱いは人間裁定に属し、裁定が付くまで軸 3 の live 本走は
開始できない」と、control 評価器・resolver の未実装 (09-01 記録 §6.1)。live preflight は U11 の
対象外と読んだ。**この読みが誤りなら wave は 1 本も request を出さずに止まる。**

**(P2) 親の provisional 裁定 — 攻撃対象.** pacing 定数を軸 1 の実測下限からそのまま継承する。
自分で測るには保護対象の request をまさに送る必要があり、循環する。継承の妥当性は「同一ノード・
同一 3 索引・production 実績あり」に依拠する。**軸 3 固有の事情でこれが不十分なら指摘せよ。**

**不変条件.**
- 凍結物 `2026-08-27-axis3-search-preregistration.md` / `2026-08-27-axis3-index-measurements.md` /
  `2026-09-01-axis3-search-amendment.md` / `2026-09-01-axis3-registration-preflight.md` を 1 byte も変えない。
- 語・10 枝・cutoff (2026-12-31)・包含・除外・判定語彙・query ID 集合を変えない。pacing は
  scheduling だけに触れ、受理集合 (`ready` / `unavailable` / `blocked` の判定規則) を変えない。
- 非 200 を `unavailable` にする既存分類を緩めない (§8.4)。pacing は 429 を「起こさない」ためのもので、
  起きた 429 を「無かったこと」にする retry ではない。
- `preflight --live` は `enforce_head=True`。closure 8 file の作業ツリー bytes が `HEAD:<path>` と
  一致している必要がある → **実装を commit してから実走する。**
- bundle は repo 外の恒久 path (`/work/1/SFC/tanab/axis3-bundles/...`) に置く。

**成果物の形.** (a) pacing + N3 観測の実装差分と test、(b) 新しい registration seal 一式、
(c) repo 外 raw bundle と preflight report、(d) 新日付の凍結実行記録 (B2 / B5 の判定、B1 / B3 の状態、
N1〜N4 の観測、U11 と未実装 3 件の裁定パッケージ)、(e) worklog / decisions / insight。

**並列分割方針.** 編集面は `orchestrator/related_work_search.py` と
`orchestrator/tests/test_related_work_search.py` に集中し素集合へ割れない。段 5 は Codex author 1 単位。
段 3 の敵対相談と段 6 の敵対レビューは 2 本並列。

**実測環境.** login node (外部網あり)。受入は `tools/dev_wave_wait.py acceptance`。
live preflight の所要見積り = DBLP 1533×45s + arXiv 373×3s + OpenAlex 23×1s ≈ **19.5 時間**。
中断時は `resume --live` が残り行を継続する (実装で確認済み)。
