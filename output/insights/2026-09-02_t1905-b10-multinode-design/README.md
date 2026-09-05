# [T-1905] B-10 分散設計 wave の逐語

設計そのものの正本は `docs/b10-multinode-formal-run-design.md`。本書はその設計を作る過程で
子が返した所見の逐語と、親が現物で裏を取った結果の対応表である。**測定は行っていない。
静的検査だけである。**

- `verbatim/s2-plan.md` — 段 2 プラン起草 (codex, read-only)
- `verbatim/s3-consult-a.md` — 段 3 敵対検証 A (正しさ境界と事前登録適合)
- `verbatim/s3-consult-b.md` — 段 3 敵対検証 B (実効性・所要・資源・運用)

## 親が現物で裏を取った所見

| 所見 | 裁定 | 親の確認 |
|---|---|---|
| 検証 capability は発行 PID に束縛され、別プロセスの検査結果を commit できない | real・採用 | `orchestrator/verifier/core.py` の `_assert_matches` が `issuer_pid != os.getpid()` で拒否する |
| 正しさ検証は 5 反復ではなく legacy 1 + 実寸 5 の 6 走 | real・採用 | `orchestrator/campaign/loop.py` の `_closed_verify_workloads` と `orchestrator/campaign/pipeline.py` の passes 構築 |
| 静定待ちは 20 秒で諦めて進み、静定可否は判定に使われない | real・採用 | `orchestrator/calibrator/runner.py` の `settle` |
| 「ベンチマーク実体 1 workload 4.5 分」は性能相の値ではない (登録値から 675 秒) | real・採用 | 事前登録 spec の block 3 × 15 点 × 5 反復 × 3 秒 |
| 壁時計の固定値は 4 か所ではなく 5 か所 | real・採用 | 5 番目は `orchestrator/campaign/b10_backoff_shape_sweep.py` の submission receipt 検査 |
| binary をジョブ間で運ぶ案は RUNPATH が消える領域を指すので実行不能 | real・採用 | `tools/pegasus/b10_backoff_shape_campaign.sh` の `TMPDIR=/scr/<jobid>-b10` と EXIT トラップ |
| ビルドキャッシュ置き場が並行ジョブで共有される | real・採用 | ジョブは `REPO_ROOT=$PBS_O_WORKDIR` で repo を複製しない |
| 各ジョブが他 workload の記録を走査してその時点のレポートを書く | real・採用 | `b10_backoff_shape_sweep.py` の全 workload 横断集約 |
| 親 brief の (P2) 9 分割案は律速を 3 倍払う | real・採用 | 認証は変種ごと。block 分割は 15 変種の認証を workload あたり 3 回払う |
| 中断した正しさ検証は同一 WAL を再開できない | real・採用 | claim は解放を持たず、D193 がビルド完了後の中断を拒否する |
| plan の「fresh group ID を作り write-heavy を取り直す」 | 不採用 | campaign 同一性は既に workload ごとに分かれており、隔離のために新識別子は要らない。取り直しは裁定項目へ回した |
| worker 異常時の reject 規則が未定義 | suspect・設計要件として採用 | 実装時に定める。本 wave では実装しない |

## この wave が主張しないこと

- 分散すれば所要が縮むとは主張しない。縮むのは 3 workload を並べる分だけである。
- 検査を何本まで並行にできるかは測っていない。
- read-heavy の約 25 時間という外挿は固定費を重複させた粗い上側の値であり、予算値ではない。
- 本 wave は投入していない。設計は承認されていない。

> **但し書き (D1529、2026-09-04)。** 上の「約 25 時間」は、撤去された request `965996` の走行
> 時間 (一次資料では 5 時間 5 分。計測区間は現記録から確定できず、request 全体の Elapse は
> 20950 秒 = 約 5 時間 49 分) を完了 3 変種で 15 変種へ外挿した値である。その走行時間には、
> campaign 記録上 commit (変種の認証確定) に到達しないまま打ち切られた実行 (欠測 attempt) である
> `constant-mu2` 変種 `292d58f1dad8` の初期確認 (legacy) 1 反復と本規模 (performance) 3 反復の
> 時間を少なくとも含む。
> 終了直前に次の反復が始まっていたかは記録が無く不明である。値を無効にするものではなく、
> 欠測 attempt の時間を除いた再計算は行っていない。
