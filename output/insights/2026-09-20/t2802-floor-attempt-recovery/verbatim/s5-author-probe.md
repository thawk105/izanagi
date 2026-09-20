## 総括

指定の5ファイルを新規作成しました。production・docs は変更せず、作業 worktree の add／commit 等も行っていません。

| ファイル | 行数 |
|---|---:|
| [run-measure.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-probe/probe-t2802/run-measure.sh) | 181 |
| [run-series.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-probe/probe-t2802/run-series.sh) | 31 |
| [run-warm.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-probe/probe-t2802/run-warm.sh) | 32 |
| [t2802_ab_analyze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-probe/probe-t2802/t2802_ab_analyze.py) | 332 |
| [t2802_diff_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-probe/probe-t2802/t2802_diff_probe.py) | 315 |

実走した検査：

```bash
python3 probe-t2802/t2802_ab_analyze.py --selftest
```

rc=0、PASS。過去6走・各523 node・18 shard の抽出、判定3分岐、不足対・12走超過を確認しました。

```bash
python3 probe-t2802/t2802_diff_probe.py --selftest --repo-root /work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-probe --base-module /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery/verbatim/base-module/s8b_holdout_admission_base.py
```

rc=0、PASS。24状態すべて両順序で一致し、root の不変も確認。緩めた stub の正例は内部比較 rc=1 で不一致を検出しました。

```bash
bash -n probe-t2802/run-measure.sh && bash -n probe-t2802/run-series.sh && bash -n probe-t2802/run-warm.sh
bash probe-t2802/run-measure.sh
bash probe-t2802/run-measure.sh 01 A 1
```

構文検査 rc=0。引数不足・tips JSON 不在はいずれも rc=2、runs／aborts の内容に変更なし。合成523件による集計 CLI も rc=0 で出力し、hash 改竄後は無効対に変わることを確認しました。

差分 probe の状態は以下です。

- **a〜c:** marker 不在、1 claim の M+A−、M+A+。
- **d:** 2・3 attempt の消費途中と消費後、3消費後の各 target の M+A−。
- **e:** 後段の非 target marker の campaign_run_id、extra-key、改名、未登録 attempt。
- **f:** 後段 A 行の campaign_run_id、canonical 二重化。追加で marker 欠落。
- **g〜j:** completed journal、main records 改竄、claim 非 canonical bytes、consumed symlink。
- **追加:** 別 run_id・複数 claim の marker 不在、M+A−、M+A+。

判定式は集計器の [`decision()`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-probe/probe-t2802/t2802_ab_analyze.py:175)。F は Decimal で計算し、表示は小数3桁です。T-2766 から、条件別 tips／worktree、共通 env、前後の tree 検査・差分 hash、AB／BA／AB、赤で系列停止、条件別 warm-up に変更しました。

**入力上の注意:** 凍結523件には過去6走すべてで skipped の3件があります。selftest だけ例外を明示して抽出を確認し、本走では指定どおり無効にします。同じ状態の本走からは有効対が成立しません。

復元は完全一致 classname と parameter を含む name に限定し、class 配下9件は除外します。import の実測では書込み・process 起動とも0件でしたが、authority 検査・registry／RLock 作成はあります。fixture 内部の git 初期化・commit は削除済みの一時領域内だけです。base と現行は依存 module を共有します。

測定・warm-up・collect-only、および修正後 production に対する差分 probe は**実装済み・未実走**です。