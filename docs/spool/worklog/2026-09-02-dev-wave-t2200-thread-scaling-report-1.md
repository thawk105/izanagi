---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2200-thread-scaling-report
seq: 1
title: {{T:tuned-adaptive-backoff-baseline}} backoff の利得はスレッド数の関数であり、既定 adaptive の劣位は定数のせいだった — 刻み 0.5µs で 3.3 倍 (docs のみ、branch worktree-dev-wave-t2200-thread-scaling-report、実装面 0 につき変異 matrix 免除)
---

## 本文

- **ユーザー裁定 (2026-09-02):** 稼働中だった B-10 正式走 `965996` を撤去した。ユーザー明言
  「性能測定で計算ノード上を5時間走るっていうのはありえないゴミです。撤去。二度とそんなことはやらない」
  「8分割するにしても2ノードに分散して投げたらすぐ終わる」
  「ワークロードのパラメータースイープするにしても他の計算ノードに並列でジョブ投げたらすぐ終わる」。
  `qdel` に加えて当該 wave の監視・待ち手プロセス 10 本を停止し、投入元セッションへ裁定を中継した。
  相手は「現行の形では再投入しない、balanced も投げない」と応答。worktree と commit は無傷。
- **撤去対象の実測 (判断根拠):** `965996` は 5 時間 5 分で 15 cell 中 3 cell しか終えず、
  `fitness_tps` は全件 null (`note=no-bench`)。CPU 時間 17,909 秒 / 経過 18,196 秒 = 実効 1.0 コアで、
  48 コア確保のうち 47 が遊休。空きノードは 108/149。12 時間上限に対し完走には約 23 時間必要で、
  打ち切り軌道にあった。**律速はビルド (2 バイナリで 51 秒) ではなく verify** で、read-heavy は
  3 秒走が 1,690 万 commit + 300 万 abort を出し、直列性検査 1 回に 23 分かかっていた。
- **代替として並列走査を実施:** 同じ 15 cell を 6〜48 スレッドの 8 点 × 3 秒 3 rep で測り直した。
  workload とスレッド数は実行時フラグなのでビルドを全条件で共有でき、6 ノード同時で約 14 分。
  結果は {{D:tuned-adaptive-is-the-baseline}} の根拠および
  `output/insights/2026-09-02_backoff-thread-scaling.md` に置いた。
- **ユーザー指摘で adaptive の定数を実測:** 「cicada adaptive backoff はパラメーターをうまく
  設定すればすごくいい感じになるのでは。それやってないでしょ」との指摘を受け、`kIncrBackoff` /
  `kMaxBackoff` をビルド時パラメータへ開いて刻みを 8 値で振った (job 966798–966803、6 ノード約 12 分)。
  **既定 adaptive の劣位は機構ではなく定数に由来する**ことが確定した (48 スレッドで
  +159.5% / +241.4% / +329.6%、最良の静的値に対して −8.2% / −1.0% / +2.6%)。
  陽性対照として既定値のセルを格子に残し、無改変ビルドを全 24 点で最大 2.84% 差で再現した
  (`none` の走行間ばらつきと同値) ので、パッチは既定値では inert である。
- **この穴は自認済みで 2 か月放置されていた。** 2026-07-04 の docs 整合監査
  (`docs/archive/audit-2026-07-04-docs-consistency.json`) が
  「grid 定数 (kIncrBackoff=100us) を調整した適応 backoff とは未比較」「sweep 1 本で埋まる」と
  名指ししていたが、live な項目にならないまま残っていた。
- **セッション異常 (自分の欠陥) 2 件。**
  (1) 待ち手の生存判定を `qstat` の終了コードで書き、終了済み job を生存と誤判定して
  2 時間 15 分空転した。**同じ罠は 2026-08-29 に踏んで memory に記載済みだった** — 記憶があっても
  書く瞬間に引かなければ効かない。文字列一致 (`does not exist`) へ直した。
  (2) 中間報告で「内蔵 adaptive が一貫して最下位」と書いた。事実だが、既定値を叩いているだけで
  主張としては不当だった。ユーザー指摘で訂正し、D 記録へ格上げした。
- **成果物はすべて認証されていない。** trace-disabled の性能測定のみで直列性の検査を通していない。
  variant 採用の根拠には使えない (規律 2)。
- probe 一式 (`.py` / `.pbs` / `.patch`) は実装面につき本 wave では repo へ入れず、
  `izanagi-job-evidence/thread-scaling/` (repo 外) に置いた。取り込みは Codex author を立てて別 wave。

## 次の一手差分

### 新規

- {{T:tuned-adaptive-backoff-baseline}} **P1・新規**: 調整済み adaptive backoff を正式な対照へ組み込む。
  {{D:tuned-adaptive-is-the-baseline}} に従い、既存の比較・図・論文ストーリーのうち既定 adaptive を
  単独基準線に使っている箇所を洗い出して差し替える。
- {{T:adaptive-probe-tooling-land}} **P2・新規**: thread scaling probe と adaptive parameter probe
  (`.py` / `.pbs` / `cicada-adaptive-params.patch`) を Codex author を立てて repo へ取り込む。
  現状は repo 外にあり、再現には job evidence directory が要る。
- {{T:adaptive-backoff-trajectory-diagnostic}} **P2・新規**: 刻みに対する応答が単調でない
  (0.5µs が最良、5〜25µs が谷、100µs でやや回復) 機序を、`Backoff_` の時系列と gradient 符号の
  ノイズ支配率で切り分ける。現状は機序未確定のまま報告している。
- {{T:tuned-adaptive-correctness}} **P2・新規**: 調整済み adaptive backoff に対する直列性の検査を
  trace-enabled 走行 + verifier で通す。現在の数値は性能のみで認証されていない。
- {{T:ccbench-adaptive-step-upstream}} **P3・ユーザー裁定待ち**: `kIncrBackoff` の既定値について
  上流 CCBench へ還元するかを決める。材料は
  `output/insights/2026-09-02_ccbench-adaptive-backoff-step-granularity.md`。
  単一環境・正しさ未検査・機序未確定という限界も同文書に明記済み。
- {{T:verifier-parallelization}} **P1・新規**: 直列性検査が単一スレッドで、read-heavy の 3 秒走
  (2,000 万トランザクション) に 1 回 23 分かかる。これが B-10 正式走の律速だった。
  **検査を弱める方向 (トレース短縮) は規律 2 に触るため採らない**。検査器側の並列化で詰める。
