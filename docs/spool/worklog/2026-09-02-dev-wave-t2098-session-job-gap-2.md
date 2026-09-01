---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2098-session-job-gap
seq: 2
title: [T-2098] session 合計と job 合計の差 約 75 秒は、ほぼ全量が観測単位の違いだった — 実際に job の外で払っているのは 14 秒 (docs のみ、branch worktree-dev-wave-t2098-session-job-gap、実装面 0・変異 matrix 免除)
---

## 本文

- D1320 が「未分解であり、分解したかのように書かない」と残した約 75 秒を分解した。
  結論と実測は {{D:session-job-gap-is-mostly-a-unit-mismatch}}、
  {{D:login-collection-is-not-on-the-observed-critical-path}}、
  {{D:receipt-queue-wait-is-not-scheduler-queue-wait}}。
  一次資料は `output/insights/2026-09-02_t2098-session-job-gap/`。
  **新規の受入走行は 0 本で、すべて既存成果物の事後解析である。短縮の実装・提案はしていない。**

- **依頼の 75 秒は量として成立していなかった。** 549 session の中央値から 1297 job の中央値を
  引いた非対差であり、観測単位も母集合も違う。現在のコーパスで同じ形を計算すると 80 秒で、
  その内 **68 秒が「session は最も遅い shard を待つ」という数え方の違い**だった。
  session が job の外で実際に払っているのは、対で引いた残差の中央値 **14 秒**である。

- **段 3 の 2 レンズが BLOCKER を 2 件ずつ返し、うち 1 件が親のプランの因果を反転させた。**
  `confirm` は qsub が返った後に書かれるので `Created` より後であり、
  段 2 プランはこれを Created の前側 anchor に置いていた。親が
  `tools/pegasus/dispatch_compute.py` の qsub 呼出しと `_confirm_dispatch_intent` の順で実物照合した。
  同じ修正で「ログインノード・計算ノード・scheduler の mtime を単一時計として引き算する」問題も消え、
  **時計を跨ぐ引き算を主推定量から全部追い出す**組み替えになった。

- 段 3 はほかに、`max_j(E_j − C_j)` は shard ごとに `Created` がずれると session の臨界経路では
  ないこと (scheduler の包絡は `max_j E_j − min_j C_j`)、K=2 が正規であること
  (`tools/acceptance_shards.py` の `create_session` が 2 と 3 を受理する)、
  会計 file 名が 2 系統あることを出した。**21 所見すべてを real と裁定し、20 件採用・1 件部分採用した。**
  部分採用は「script が過剰」で、`--expected-sessions` gate・固定行帯・構造化 stdout protocol は
  削り、除外 counter は正直さに要るので残した。

- **段 6 の 2 レビューがさらに BLOCKER を 1 件ずつ返した。**
  (a) 出力を判定する集計が `Jmax` しか持たず依頼の形に答えられない、
  (b) 出力 3 本を追従書込みで開くため出力先の同名 symlink 経由で入力コーパスを切り詰めうる。
  後者は再取得できない一次資料を壊す型なので直した (F803 と同じ「計測が測定対象を壊す」型)。
  fix は 7 件すべて `closed`、焦点再レビューが独立に判定し回帰なしを確認した。

- **中央値は項別に足し引きできない。** 実測でも `median(S) − median(Jmax) = 12` に対し
  `median(S − Jmax) = 14` である。80 秒の 2 分割は中央値の値の間の算術であって
  session ごとの分解ではない、と成果物へ明記した。

- **D1320 の cohort は再現しなかった。** cutoff 2026-08-29 で fallback あり `(586, 1, 26, 559)`、
  fallback なし `(559, 0, 0, 559)`、目標 `(568, 1, 18, 549)`。**合わせ込んでいない。**
  一方、中央値 338 秒は両版・両候補式で再観測され、新たに出した全 shard の job span 中央値
  259 秒も D1320 の 263 秒に近い。後者は同じ式・同じ観測単位に対する別 cohort 間の
  弱い数値的一致であって、cohort の再現でも 263 秒の更新でもない。

- **親の 2 回の実走は同一 snapshot ではない。** 1 回目 737 session / 主集合 679、
  2 回目 739 session / 主集合 680 で、`Jmax` 中央値も 328 秒から 327 秒へ動いた。
  式の変更による回帰ではなく走査中のコーパス増加である。**正本は 2 回目**とし、
  inventory 窓 (2026-09-01T22:15:56Z 〜 22:16:11Z) を成果物に記録した。

- 計算資源: 計算ノードへの投入は 0 本 (受入全走を除く)。解析はログインノード上の read-only 走査で、
  1 回あたり約 15 秒。Codex 子は 8 本 (plan 1・consult 2・author 1・review 2・fix 1・focus 1)。
  解析 script は Codex `role=author` が書き、親が実行し、**repo へ commit せず** insight の
  `verbatim/` へ逐語で収めた (fix 後 sha256 `d81870c6af38f3eb...`、fix 前 `953c085731fd63d5...`)。

- **段 8 の自己改善候補 2 件のうち 1 件は機械 gate に反証された。** 親は
  `docs/dev-wave/workers.md` の DW-S05-A / DW-S06-A / DW-S06-C が書く `reasoning=xhigh` を
  「caller が渡すと `tools/dev_wave_codex.py` が rc=2 で拒否するので誤解を招く」と見て削ろうとしたが、
  `tools/check_docs.py` が 3 件の違反として拒否した — その文字列は段 5 / 6 の**採用裁定に束縛された
  adoption pin** であり、変更には採用裁定と pin の同時更新が要る。DW-O01 の
  「effort は段 5 / 6 が docs 権威から導出。caller 指定は不可」と読み合わせれば、この literal が
  その docs 権威そのものである。**候補を取り下げ編集を戻した。** もう 1 件は F37 の 4 例目として
  台帳へ送り、dev-wave docs は編集しなかった。

- 実装面の repo 差分は 0 byte。`DW-S04` により変異 matrix は免除。受入全走は免除せず、
  記録 commit 後に land 対象 tip へ投入した (`DW-O12`)。結果は land の受領証が正本。

## 次の一手差分

### 完了

- [T-2098] 保存済みの timing 記録だけで分解し、約 75 秒のほぼ全量が観測単位の違いであることと、
  job の外の残差が中央値 14 秒であることを確定した。起票時に想定していた「同一 session で
  各時点を時刻化する」計装は行っておらず、**その部分は {{T:acceptance-session-timeline-instrumentation}}
  へ移した** (ユーザー指示「新しい観測点が要るならそれを別項として返す」に従う)。
  remaining: none
  base: 83d9631ef7194336384b8109abf6fedda2e4e117f531e4cd45e7732e8e0ce2cc

### 新規

- {{T:acceptance-session-timeline-instrumentation}} **P3・新規**: 受入 session の
  「最後の `Ended` から最後の `handled` まで」中央値 13 秒の内訳を測るための計装を入れるか裁定する。
  保存済み記録では原理的に分けられないことを実測で確定済み
  ({{D:session-job-gap-is-mostly-a-unit-mismatch}})。必要な測点は
  `output/insights/2026-09-02_t2098-session-job-gap/README.md` の表が正本で、terminal poll ごとの
  生 qstat 応答と観測時刻、成果物収集の開始・終了、receipt 永続化、scheduler log 中継、
  `handled` 書込みを同一 login monotonic clock で刻むこと。**着手前に、13 秒を分解する価値が
  あるかをユーザー裁定へ諮る** — 受入 wall の中央値 339 秒に対して 4% であり、
  D1035 が指す排他閉包の細分化より優先する根拠は無い。実装面なので Codex author が要る。
