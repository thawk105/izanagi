静的レビューのみ。実行・変更はしていない。

### R2-1

- **ID:** R2-1
- **主張:** timed `Path.read_text()` 自体には subprocess・書込み・JSON encode はない。しかし連続 read の間に、全 PID の `stat/status/cgroup` 走査、`/proc/stat` 読取り、大量の dict/list 構築が毎回入る。50 ms は開始間隔ではなく「全後処理終了後の追加 sleep」であり、critical series は純粋でも固定間隔でもない。
- **file:line:** [t419_probe_causality.py:898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:898), [t419_probe_causality.py:1140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1140), [t419_probe_causality.py:1218](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1218), [t419_probe_causality.py:1264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1264)
- **具体的な失敗シナリオ:** A1 で target CPU に pin された probe が、各 cpuinfo read 後に全 `/proc` を走査する。その負荷で次回 read 前の P-state が変わり、A1 が測るのが cpuinfo 読取り単独の効果ではなく「cpuinfo + isolation scanner」の効果になる。A2 の busy child も scanner 所要時間中ずっと spin する。
- **成果物影響:** `pinned_hit_rate`、paired contrast、A2 busy−sham MHz 差、α/β/γ 表が変わり、`CONFIRMED`/`REFUTED` と方式別偽陰性数が反転しうる。
- **強度:** **強**。汚染経路は静的に確定。影響量は未実測。
- **最小の是正案:** read block 内では raw text と時刻だけを採り、parse・dict 化・process scan は block 後へ移す。isolation sampling 後は新しい anchor を破棄し、次回開始時刻を monotonic deadline で固定する。

### R2-2

- **ID:** R2-2
- **主張:** anchor と cooldown が裁定どおりでない。`setup_fn` の anchor は重い pre-diagnostics と tracker 初期化より前に取られ、A0/A3 quiet は block 初回を破棄しない。A2 は sham/busy 条件間にも target 間にも 1 秒 cooldown がない。
- **file:line:** [t419_probe_causality.py:1415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1415), [t419_probe_causality.py:1787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1787), [t419_probe_causality.py:1823](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1823), [t419_probe_causality.py:1830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1830), [t419_probe_causality.py:1879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1879), [s4-adjudication.md:24](/work/1/SFC/tanab/dev-wave-jobs/t419-probe-experiment/s4-adjudication.md:24)
- **具体的な失敗シナリオ:** randomized order が busy→sham になった対で、busy を止めた直後に sham を開始する。熱・P-state hysteresis が sham 側へ残り、対照差を縮めるか符号反転させる。A3+A2 の anchor も busy child 起動前なので介入成立後の初回値を捨てていない。
- **成果物影響:** `coresident_metrics`、quiet/reject の method table、α収束率と偽陰性数が順序依存になる。
- **強度:** **強**。欠落は静的に確定。
- **最小の是正案:** 全 instrumentation と介入開始後に anchor を取得・破棄する。A3 は block ごと、A2 は各 sham/busy condition ごとに anchor を置き、child 停止確認後に 1 秒 cooldown を入れる。

### R2-3

- **ID:** R2-3
- **主張:** isolation gate には transient competitor の確定的な見逃し窓がある。PID の前後スナップショット時の `processor` だけで判定し、記録した `/proc/stat` delta は競合判定に使っていない。また allowlist は process tree ではなく「self + 過去を含む direct child PID」である。
- **file:line:** [t419_probe_causality.py:1188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1188), [t419_probe_causality.py:1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1195), [t419_probe_causality.py:1222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1222), [t419_probe_causality.py:1244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1244), [t419_probe_causality.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:543)
- **具体的な失敗シナリオ:** 他テナントの短命 process が 50 ms sleep 中に allocated CPU で走って終了する。または snapshot 時には別 CPU へ migration している。PID record には現れず、CPU delta に負荷は残っても gate は参照しないため `competition_detected=false` になる。
- **成果物影響:** 汚染された全 arm が `execution_validity=VALID` を通り、A1 から `CONFIRMED`/`REFUTED` が生成されうる。受理集合へ非単独 job が混入する。
- **強度:** **強**。blind spot の存在は静的に確定。実際の同居発生は未実測。
- **最小の是正案:** active child と start-time を束縛した正確な自 tree を作り、曖昧な CPU delta・短命 task を fail-closed にする admission 判定を追加する。競合を検出した時点で後続 arm を走らせない。

### R2-4

- **ID:** R2-4
- **主張:** production parser crosscheck が fail-open。import 不能は `status=unavailable` だが、妥当性検査は `mismatch` だけを拒否する。
- **file:line:** [t419_probe_causality.py:559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:559), [t419_probe_causality.py:1571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1571)
- **具体的な失敗シナリオ:** 計算ノードで `campaign.env_attestation` の import が失敗する。自前 parser の値だけで全解析が進み、crosscheck は `unavailable` のまま `VALID+CONFIRMED` を返せる。
- **成果物影響:** 本番 parser と異なる vector・帯外集合が causal verdict と方式表の受理集合へ入る。
- **強度:** **強**。
- **最小の是正案:** raw 3 件すべてについて `parser_crosscheck.status == "match"` を `VALID` の必要条件にする。`unavailable`、`error`、件数不足はすべて `INVALID`。

### R2-5

- **ID:** R2-5
- **主張:** PBS/job 成果物に完走を証明する原子的な終端がない。`result.json` は provenance より先に書かれ、wrapper は probe log・rc file・done-marker を残さない。`.o/.e` と終了後 qstat/accounting も manifest 外である。compute marker が false でも wrapper 自身は Python を起動する。
- **file:line:** [t419_probe_causality.pbs:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.pbs:50), [t419_probe_causality.pbs:92](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.pbs:92), [t419_probe_causality.py:1990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1990), [t419_probe_causality.py:1992](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1992), [t293_perf_site_probe.pbs:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t293_perf_site_probe.pbs:82)
- **具体的な失敗シナリオ:** `result.json` が `VALID+CONFIRMED` として作られた後、PBS hash または manifest 書込みが失敗する。process rc は非零でも output dir には成功風の result が残り、完走 marker がないため file-existence collector が採用できてしまう。`.o/.e` は job 終了後に別場所へ戻るため、その内容と会計 rc は manifest に入らない。
- **成果物影響:** 未完走 result が最終結論・README の参照先になりうる。manifest の `rc` と実 wrapper rc、PBS 会計証拠を第三者が照合できない。
- **強度:** **強**。
- **最小の是正案:** compute marker false を Python 起動前に拒否する。先例同様、create-only の probe log・`probe.rc`・done-marker を作り、done は manifest 成功後だけ発行する。終了後に `.o/.e`、最終 qstat、会計 rc を hash した receipt を別途作り、採用条件にする。

### R2-6

- **ID:** R2-6
- **主張:** provenance は submission-time binding ではなく実行後の自己申告である。期待 HEAD・driver/PBS hash を受け取らず、dirty でも validity は通る。driver hash は測定後なので、queue 待ち中または実行中に bytes が変わっても計画した実装との同一性を証明しない。
- **file:line:** [t419_probe_causality.pbs:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.pbs:7), [t419_probe_causality.py:1959](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1959), [t419_probe_causality.py:1992](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1992), [t293_perf_site_probe.pbs:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t293_perf_site_probe.pbs:7)
- **具体的な失敗シナリオ:** qsub 後、開始前に worktree の driver、PBS、または calibration resolver が変更される。job は変更後 bytes で測定し、dirty を記録するだけで `VALID` を返す。実行中に driver file が再変更されれば、記録 hash は実際にロードされた bytes とも一致しない。
- **成果物影響:** band・raw vectors・causal verdict が段4で裁定した commit と異なるコード由来になり、第三者が hash しか残らない dirty bytes を再現できない。
- **強度:** **強**。
- **最小の是正案:** 先例同様、期待 HEAD・driver/PBS・較正 path/hash を submission から渡し、最初の outcome read 前に一致を検査する。関連 dirty は拒否するか exact bytes を成果物へ保存する。実 queue/project も hardcode でなく scheduler 証拠と照合する。

### R2-7

- **ID:** R2-7
- **主張:** 正常系の terminate→wait→liveness は実装済みだが、例外・hang 時の child 回収は bounded でない。`_stop_child` 自身が kill 前に例外を投げられ、`waitpid(..., 0)` に timeout/kill escalation がなく、外側 finally は affinity しか戻さない。
- **file:line:** [t419_probe_causality.py:1344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1344), [t419_probe_causality.py:1363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1363), [t419_probe_causality.py:1395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1395), [t419_probe_causality.py:1933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1933)
- **具体的な失敗シナリオ:** `/proc/<pid>/stat` が想定外 OSError を返す、または child が SIGTERM 後も終了しない。busy child が残ったまま post-diagnosticsへ進むか、blocking wait で walltime まで停止する。
- **成果物影響:** arm 診断が orphan child で汚染されるか、result/manifest が一切完成せず job 全体が不採用になる。
- **強度:** **弱い**。静的な未処理経路はあるが、管理下 child での発生実測はない。
- **最小の是正案:** outer scope に child registry を置き、全出口の finally で回収する。期限付き WNOHANG wait→SIGKILL→再 wait→生存確認を記録する。

### R2-8

- **ID:** R2-8
- **主張:** 通常経路は10分に収まりそうだが、上限は保証されない。primary は 445 read、anchor 込み `/proc/cpuinfo` open は 496 回。sleep だけで約22.2秒、cooldownで計約27.2秒あり、「数秒」ではない。各 read 後の全 PID 走査と `waitpid` は無期限である。
- **file:line:** [s4-adjudication.md:34](/work/1/SFC/tanab/dev-wave-jobs/t419-probe-experiment/s4-adjudication.md:34), [t419_probe_causality.py:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:32), [t419_probe_causality.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:55), [t419_probe_causality.py:1140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1140), [t419_probe_causality.py:1363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py:1363)
- **具体的な失敗シナリオ:** node に多数の PID がいると、約445回の全 `/proc` scan が支配的になる。busy child はその追加時間も spin し続け、熱汚染と walltime を同時に増やす。
- **成果物影響:** 10分 kill で done/manifest が欠け、job の全値が不採用になる。
- **強度:** **弱い**。静的下限と非有界経路は確定しているが、実 node の所要時間は未実測。
- **最小の是正案:** 投入前に同じ node class で per-arm 時間と PID 数依存を測り、hard deadline と child 回収期限を設ける。R2-1 の per-read scan 除去も必須。

静的に反証できた疑いとして、arm の大順序自体は裁定どおりであり、通常 child 停止順、hidepid/error の INVALID 化、Python 3.10 明示、no-clobber・symlink 検査、argv/env を除く process allowlist、`non_certifying` / `counterfactual_only` の両印は実装されている。既存 pin・凍結 bytes・受理集合への書込みも見当たらない。

## 総括

(a) **このまま投入してはだめ。**
(b) 投入前必須1: per-read `/proc` scan を critical series から除去し、anchor・固定間隔・child間 cooldown を裁定どおりにする。
(b) 投入前必須2: transient processを見逃さない fail-closed isolation admission と parser crosscheck の exact-match gate を作る。
(b) 投入前必須3: submission-time hash/HEAD binding、done-marker、rc、`.o/.e`・最終qstat receipt を揃える。
(c) 投入後は実 read 開始間隔、各 discarded anchor、child tick/affinity/回収、競合検出、全 arm 件数を確認する。
(c) wrapper rc・done・manifest hash・PBS会計rcが一致し、dirty=false、crosscheck=match であることを親が確認する。
(c) 実 walltimeとper-arm時間を記録し、未実測のR2-7/R2-8を実測でreal/refutedに裁定する。