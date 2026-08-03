---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-03
wave: dev-wave-t293-perf-site
seq: 2
---

## {{D:two-sided-control-for-gateless-measurement}}. gate を新設しない実測 wave では、手編集の変異 matrix でなく同一 run 内の両側 control で測定器の感度を裏取りする

**背景:** [T-293] の計算ノード実測 wave は gate もテストも新設せず、成果物は「測った値」だけである。
当初は DW-M01 に倣って変異を 2 件事前登録した — (C1) 同じ probe をログインノードで走らせて
逆の結果が出ることを確認する negative control、(M1) 候補読取箇所を `/bin/true` へ一時変異して
verdict が反転することを確認する。段 6 の敵対レビュー 2 本が、この設計を独立に否定した。

**決定 (1): ログインノードでの negative control は撤回する。** 候補が 1 本でも解決すれば
`_executable` が `perf --version` を実行し、続いて smoke で `perf stat` に到達する。
**候補不在は期待値であって防壁ではない。** 加えて runbook §7.0 は「消費量が未知なら計算ノードへ
dispatch」であり、cgroup peak を測っていない probe を login で走らせる根拠がない。

**決定 (2): 診断 field の反転を kill と数えない。** C1 の `resolved:false` と M1 の `resolved:true` は
**どちらも rc=0 / `ok:true`** であり、fail-closed 挙動は変化しない。DW-M03 の「受理集合か
fail-closed 挙動が期待方向へ変わったときだけ数える」を満たさない。
`resolved = hostname.startswith("bnode")` のような policy を読まない定数でも C1 の期待差は通る。

**決定 (3): 手編集変異は単一 anchor を持てないので使わない。** 候補を読む箇所は「候補記録の行」
「resolver 入力の行」「policy mapping 自体」に分かれ、どこを変異させるかで結果が反転する。
`git checkout --` だけの復元は DW-M05 の固定 HEAD・flock・signal 復元も満たさない。

**決定 (4): 代替は同一 run 内の両側 control とする。** probe 自身が、同じサイト・同じ run・同じ
実コードで次の 2 つを実行する。**存在する実体 path は解決しなければならない (正)。存在し得ない
候補は解決してはならない (負)。** どちらかが破れたら測定器の故障として `ok:false` / rc 非 0 で
fail-closed する。これは診断値の反転ではなく **fail-closed 挙動の変化**なので DW-M03 の意味で
有効な受理述語である。stuck-false な resolver (何を渡しても失敗する) を検出できる点が、
負側 1 点だけの control との決定的な差である。

**決定 (5): 受理述語を 5 条件で機械判定する。** (i) 実行 bytes の binding が期待値と一致、
(ii) `ok:true` かつ必須 field 完備かつ probe rc=0、(iii) control が両側成立、
(iv) probe 完了後に書く done-marker が実在、(v) 全測定層が `attempted:true`。
1 つでも欠ければ測定失敗として扱い、**測った対象の可否を結論しない。**

**却下した案:** (a) 変異を計算ノードで別 job として走らせる — 待ち行列を 2 倍消費するのに、
得られるのは同一 run 内 control と同じ性質である。(b) 変異 matrix を「対象外」とだけ書いて
何も裏取りしない — レビュー所見ゼロを変異なしで緑と数えない (DW-M02) の趣旨に反する。

**実効性の実証:** 本 wave の 1 回目の実走 (request `881946`) が、この設計の効果をそのまま示した。
計算ノードの既定 `python3` が 3.10 未満で orchestrator を import できず
({{F:compute-node-default-python-is-oneapi}})、probe は `control_sensitivity: not-established` と
`ok:false` / rc=3 で停止した。**測定器の故障と正当な否定結果を分離していなければ、この走行は
`ok:true` かつ `resolved:false` を返し、「計算ノードでも候補は使えない」という誤結論を成果物へ
残していた。** 2 回目 (request `881960`) は `two-sided-ok` で成立し、そこで得た `resolved:false` は
真の測定結果として採用できる。

**研究状態への影響:** なし。本 D は gate を新設しない実測 wave の**裏取り方法**を定めるだけで、
production 挙動・受理集合・certified 選択・凍結 bytes はいずれも不変である。
`tools/pegasus/policy.json` の sha256 は wave を通じて `b1c42e49…961ac` のまま変わっていない。
