結論は **NO-GO**。must-fix は 5 件です。pytest、probe、perf、PBS job は一切実行しておらず、以下は静的レビュー結果です。

## 所見

### B1. C1 は「実行不能」か「login で perf を実行」の二択になる

- `file:line`: [s4-adjudication.md:24](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:24)、[t293_perf_site_probe.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:162)、[submission.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/orchestrator/qualification/submission.py:83)、[guard_bash.py:607](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/hooks/guard_bash.py:607)
- **成果物影響:** C1 を変異台帳の有効な control として受理できず、これを「KILLED」と記録すると段 6 の受理集合とユーザー裁定材料が偽緑になる。
- 深刻度: **must-fix**
- 再現条件・失敗シナリオ: login に候補の一方が追加された、または候補を持つ別 login node で走らせると、`gcc-13` 検査より先の直接 `_executable()` が `perf --version` を実行し、その後 [probe.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:208) の `perf stat` に到達する。候補不在は期待値であって防壁ではない。逆に hook 有効面では `tools/pegasus/` の非 sanctioned 実行体として拒否される。加えて probe の cgroup peak は未計測なので、runbook §7.0 上も login 実行は `unknown = dispatch-required` である。

### B2. PBS job は既存 output と symlink を追って上書きできる

- `file:line`: [t293_perf_site_probe.pbs:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:13)、[同:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:21)、[同:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:26)、[同:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:28)
- **成果物影響:** stale `probe.json` と新しい marker/log/rc が混在して材料レポート・台帳の観測を取り違えるか、symlink 先の policy/source を切り詰めて series identity と受理集合自体を変える。
- 深刻度: **must-fix**
- 再現条件・失敗シナリオ: `$OUT` を先に作り、`marker` を `tools/pegasus/policy.json` への symlink にしておけば `> "$OUT/marker"` が tracked policy を切り詰める。単なる再実行でも `mkdir -p` は既存 dir を受理し、marker、probe.log、probe.rc を上書きする。`probe.json` だけは [probe.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:238) の `"x"` で create-only なので、むしろ新旧混在が生じる。marker は probe より先に書かれているが、freshness の証明にはなっていない。

### B3. C1/M1 は DW-M03 の「kill」ではなく、受理述語のない診断差分

- `file:line`: [s4-adjudication.md:24](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:24)、[同:35](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:35)、[probe.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:21)、[同:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:225)
- **成果物影響:** 診断 field の反転だけで mutation matrix を KILLED と誤記し、probe の実装受理と裁定パッケージを偽緑にする。
- 深刻度: **must-fix**
- 再現条件・失敗シナリオ: C1 の `resolved:false` と M1 の `resolved:true` は、どちらも process rc=0、`ok:true` で「測定完了」として受理される。fail-closed 挙動は変化していない。また `resolved = hostname.startswith("bnode")` という policy を一切読まない site 条件定数でも C1 の期待差を通る。C1 が否定できるのは無条件の単一 literal だけで、「policy／filesystem に駆動される」証拠にはならない。現契約なら diagnostic sensitivity pin として扱うべきである。

### B4. M1 の変異位置は一意でなく、単一理由性も復元契約も成立しない

- `file:line`: [s4-adjudication.md:29](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:29)、[同:32](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:32)、[probe.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:57)、[同:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:136)、[同:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:162)、[同:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:176)
- **成果物影響:** 変異箇所の選び方だけで SURVIVED/KILLED が反転し、段 6 の mutation 台帳と probe 受理判断が再現不能になる。
- 深刻度: **must-fix**
- 再現条件・失敗シナリオ:

  - 136 行だけを `/bin/true` に変えると候補記録だけが変わり、162 行は元 policy を再読するため期待 field は反転しない。
  - 162 行を変えると反転するが、それは policy 読取を検査せず、policy を明示的に迂回した結果である。
  - policy mapping 自体を変えると候補記録、直接解決、`prepare_toolchain`、smoke が同時に変わる。
  - `/bin/true` は現 host では regular executable で、generic `_executable()` の file・symlink・version 検査を通る一方、full `prepare_toolchain` では手前の cc/cxx が同じ試行を mask しうる。
  - 手編集後の `git checkout --` だけでは、中断時に `/bin/true` 変異が残る。これは [DW-M05](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/docs/dev-wave/mutation.md:31) の固定 HEAD、flock、signal 復元を満たさない。

### B5. N3 を “real” とした裁定は、既知の compiler blocker と標本範囲を無視している

- `file:line`: [brief.md:23](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:23)、[同:28](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:28)、[同:32](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:32)、[s4-adjudication.md:12](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:12)、[submission.py:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/orchestrator/qualification/submission.py:105)
- **成果物影響:** D96 裁定で perf の読取 site や identity path を変更して受理系列を変えても、qualification は cc/cxx で停止したままとなり、不要な受理集合変更だけが certified series identity に入る。
- 深刻度: **must-fix**
- 再現条件・失敗シナリオ: 今日の bnode で direct perf resolution が成功しても、`prepare_toolchain` は python→gcc-13→g++-13→cmake→perf の順である。runbook の既知証拠は `g++-13` が login/compute 双方に無いとしており、実 PBS body も [t126_qualification.sh:532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/t126_qualification.sh:532) で perf より前に gcc/g++-13 を要求する。したがって N2 は N3 の根拠ではなく、むしろ「perf site mismatch が本質」という単因果を壊す。`real (仮説)` は裁定ではない。少なくとも今日の `real_prepare_toolchain` 結果まで未裁定へ戻す必要がある。

### B6. N1 の旧証拠と今日 1 node の probe から、compute site 全体へは一般化できない

- `file:line`: [brief.md:23](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:23)、[s4-adjudication.md:10](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s4-adjudication.md:10)
- **成果物影響:** 一標本を site-wide capability として裁定すると、将来別 bnode に着地する系列の受理可否を誤り、policy 変更または読取 site 変更のユーザー裁定を誤誘導する。
- 深刻度: **should-fix**
- 再現条件・失敗シナリオ: 引用された debug job は実際には 2026-07-19、t141 は 2026-07-29 の観測である。今日 1 回の allocation が成功しても、別 bnode の package image が異なれば次の qualification は失敗する。逆に今日の 1 node が失敗しても全 bnode 不在とは言えない。報告単位は `hostname + epoch + policy SHA` の一標本に限定すべきである。

### B7. 実行される Python/source が commit に束縛されていない

- `file:line`: [s5-impl.md:24](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/s5-impl.md:24)、[t293_perf_site_probe.pbs:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:23)、[probe.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:52)、[同:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.py:65)
- **成果物影響:** 材料レポートと台帳が観測を誤った commit／probe bytes に帰属し、再裁定時に同じ実コードを再構成できない。
- 深刻度: **should-fix**
- 再現条件・失敗シナリオ: 現在の 2 ファイルは untracked。queued 後、開始前に probe または `submission.py` が修正されると、PBS は `$PBS_O_WORKDIR` の新しい bytes を実行する。JSON は policy SHA しか記録せず、HEAD、probe/PBS/submission SHA を持たない。

### B8. NQSV の `.o/.e` は指定 output 外へ出る

- `file:line`: [t293_perf_site_probe.pbs:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:2)、[brief.md:41](/work/1/SFC/tanab/dev-wave-jobs/t293-perf-site/brief.md:41)、[pegasus-runbook.md:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/docs/pegasus-runbook.md:103)
- **成果物影響:** F49(c) の会計痕跡が裁定パッケージ外に散り、投入有効性の参照が欠落するか、worktree に余分な untracked file を残す。
- 深刻度: **should-fix**
- 再現条件・失敗シナリオ: `-o/-e` 指定がないため、NQSV は `<script>.o<ID>` / `.e<ID>` を qsub 時の directory に返す。これは brief の「書込みは新規 output 配下だけ」と一致しない。qsub cwd も明示されていないため、job directory から投げると `$PBS_O_WORKDIR` 自体が repo root でなくなり、marker だけ作って probe path 不在となりうる。

## この wave でも答えが出ない問い

- `perf_candidates` が全 gen_S bnode、再queue先、将来の allocation で使えるか。
- pegasus01/02/03 と bnode 群の同時点比較で、差が site、node image、時間 drift のどれに由来するか。
- compiler・dependency を含む実際の T-126 経路が、どの site で最初に停止するか。
- toolchain manifest／series identity を login と compute のどちらで確定すべきか。
- policy 値の移設、読取箇所の移設、動的 discovery のどれが D96 上妥当か。
- 今日の capability を将来も有効とみなす attestation／更新規則をどうするか。

なお、PBS の `-A SFC`、`queue=gen_S`、`elapstim_req=00:10:00`、`-b 1` は runbook と brief に一致する。marker も [PBS:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:21) で probe 起動 [PBS:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t293-perf-site/tools/pegasus/probes/t293_perf_site_probe.pbs:23) より先に書かれる。ただし B2 のため、その marker は fresh/create-only 証拠ではない。計算ノード側では build、pytest、CCBench bench はなく、短い version/hash と `perf stat -- true` だけである。

## 総括

- must-fix: **5 件**
  1. C1 が login perf 禁止と login 重量分類を破る
  2. PBS output が既存 file／symlink を上書きできる
  3. C1/M1 を kill と数える受理述語がない
  4. M1 の変異位置・単一理由性・復元契約が不成立
  5. N3 の real 裁定が compiler blocker と標本範囲を無視している
- 計算ノード投入: **NO-GO**。少なくとも create-only output、symlink/既存 dir 拒否、実行 source の束縛を直すまで投入してはならない。C1 は login 実行案自体を撤回または compute 上の同一-site control へ再設計する必要がある。
- 実際に読んだファイル（`rg` の単なる索引走査対象は除外）:
  - 必須 6 ファイル: `brief.md`、`s4-adjudication.md`、`s5-impl.md`、`t293_perf_site_probe.py`、`t293_perf_site_probe.pbs`、`orchestrator/qualification/submission.py`
  - 規律・契約: `.agents/skills/dev-wave/SKILL.md`、`CLAUDE.md`、`.claude/commands/dev-wave.md`、`docs/dev-wave/{workers,core,mutation,operations}.md`、`docs/skill-self-improvement.md`
  - 関連正本: `docs/pegasus-runbook.md`、`docs/decisions.md` の D96/D115、`docs/worklog.md` の T-293 周辺、`hooks/guard_bash.py`
  - 関連実装: `tools/pegasus/policy.json`、`submit_t126_qualification.sh`、`t126_qualification.sh`
  - 旧証拠: `output/env/pegasus/debug/debug_perf.sh`、`debug_perf.sh.e867873`、`perf-0_867873.nqsv.log`、calibration request 867874/867876 の `perf-selection.json`・会計ログ・receipt/attestation 該当行、t141 request 873859 の `attestation.txt`