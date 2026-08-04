---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t419-probe-experiment
seq: 1
---

## 新規

### {{F:single-tenancy-unreachable-on-compute-node}}. 単独性の合格条件を「非自 process の CPU 時間ゼロ」にしたため、計算ノードでは決して満たせなかった [恒真ゲート] [計測汚染]

- 事象: [T-419] の probe 因果実験を Pegasus 計算ノード bnode138 で走らせたところ、最初の arm (A0) で
  競合を検出して fail-closed 停止し、因果の本体である A1 (pin sweep) が走らなかった。
  検出された「競合」は NQSV 自身のノード常駐デーモン `nqs_shpd`
  (uid 0、cgroup `/system.slice/nqs-jsv.service`、CPU 22、正の CPU 時間) だった。
- 根本原因: 親が段 6 で裁定した単独性 gate が「非自 PID が正の CPU-time delta を持てば COMPETITOR」
  という**到達不能な必要条件**だった。batch scheduler のノードデーモンは全計算ノードに常駐するため、
  この条件は**どのノードでも永久に偽**になる。恒真ゲートの裏返し (恒偽ゲート) であり、
  「厳しくして安全側」と見えて実際には**測定そのものを不可能にする**型である。
  実機で走らせる前に、その機体に何が常駐しているかを実測していなかった。
- 影響: 計算ノード job 1 本を消費して `execution_validity=INVALID` /
  `causal_verdict=NOT_EVALUATED` だけを得た。F108 の因果は依然として未立証のまま。
  ただし **fail-closed 自体は正しく働いており、無効な実験を有効な因果結論として記録しなかった**。
- 恒久対応: **未実施 (ユーザー裁定待ち)。** 是正案は「`/system.slice` の uid 0 システムデーモンを
  環境として記録し、テナントの競合と区別する」で、裁定パッケージ
  `output/insights/2026-08-04_t419-probe-causality/ruling-package.md` §6 U-1b(i) に置いた。
  実装面の修正には Codex `role=author` が要るが利用枠切れのため着手していない。
- 再発検知: 同 insight の `mutation-ledger-2layer.json` が示すとおり、単独性 gate の
  両分岐を同時に無効化する変異は `test_contention_invalidates_execution_and_verdict` と
  `test_residual_above_self_unattributable_invalidates_and_stops_later_arms` を赤にする。
  gate 自体はテストで pin 済みで、**欠けているのは「合格条件が到達可能か」の事前実測**である。

### {{F:unreadable-diagnostic-treated-as-fatal}}. permission で読めない診断 field を「不完全 = 致命」とし、裁定の三分類から逸脱した [手順漏れ]

- 事象: 同じ実験で診断 snapshot が `pre.complete=False` になり、validity 理由
  `diagnostic_snapshot_incomplete` が立った。原因は
  `/sys/devices/system/cpu/cpufreq/policyN/cpuinfo_cur_freq` が 48 policy すべてで
  Permission denied (非 root) だったことである。
- 根本原因: 段 4 の親裁定は「**不在・不可読・値ありを区別して記録する**」(段 3 レンズ B-11 の採用) と
  書いていたのに、実装は「不可読 → incomplete → validity 失敗」にしていた。
  裁定文と実装の乖離を親が段 6 のレビューで捕まえられなかった (レビュー 3 本とも
  `cpuinfo_cur_freq` の実可読性を実測していない。read-only 子には測れない)。
- 影響: 上の F と重なって A1 以降を止めた。単独では致命ではないが、
  **どの計算ノードでも常に成立する**ため、これ単独でも実験は永久に INVALID になる。
- 恒久対応: **未実施 (ユーザー裁定待ち)。** 裁定パッケージ §6 U-1b(ii)。
  裁定どおり「不可読」を記録値として扱い、incomplete=致命 にしない。
- 再発検知: 「read-only の子が確認できない実環境の可読性・常駐プロセスは、実機の安価な 1 発で
  親が先に測る」を段 1 の前提実測へ入れる。本 wave の段 1 はログインノードしか測っておらず、
  計算ノード側は job を投げるまで未知のままだった。
