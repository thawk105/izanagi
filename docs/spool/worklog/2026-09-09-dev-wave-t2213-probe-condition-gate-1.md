---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2213-probe-condition-gate
seq: 1
title: [T-2213] adaptive const probe の条件関門は配線せず裁定へ返した — 解除条件の文言は満たすが、実行時意味の witness が 13 macro すべてに存在せず、inert 実測は login node で行えない (docs のみ、branch worktree-dev-wave-t2213-probe-condition-gate、実装面の差分 0)
---

## 本文

- **依頼が名指した 3 要素のうち 1 つが構造的に存在しない。** 関門の受理規則は
  実行時意味が `green` または `unestablished` なら通す。この driver が使う 13 macro は
  witness registry に 1 件も載っておらず、宣言は全件 `None` を返して `unestablished` になる。
  配線しても実行時意味の腕は何も言わないまま admission を通る。親が現物のコードで確認した。
- **inert 要求の成否は未実測で、この計算機の login node では実測できない。** 要求値が
  既定値または宣言済み inert 値のとき、対照は patch 未適用の clean stock 木になる。
  この driver の cell は必ず inert 値を含むので、ここが緑かどうかが配線の成否を決める。
  親は既存 CLI (`python3 -m orchestrator.campaign.condition_meaning_gate`) に
  pin 済み clone + A/B/C patch の木と clean な pinned 木を渡して実走したが、
  `Could NOT find gflags` で CMake configure が止まった。関門は ccbench の configure を
  本物で走らせるので依存一式を要し、その供給は計算ノードの job の中にある。
- **繰延べ台帳の certify 側 entry は現状まったく抑止していない。** 親が閉包分類を実走した
  結果は `{'proven-unreachable': 38}` で、`deferred` は 0 件だった。もう 1 件の sink は
  `{'deferred': 14, 'proven-unreachable': 24}` で繰延べが効いている。詳細は
  {{F:enclosing-scope-build-sink-hides-macros-from-closure}}。
  この非対称のため「entry を消して検査が緑」を解除の証拠に使えない。
- 裁定は {{D:t2187-probe-condition-gate-deferral-maintained}}。**実装面の差分は 0 件**なので
  変異 matrix は免除 (DW-S04)。受入全走は免除せず実走した。
- **起動時の重複検査で稼働 wave を 1 本検出した。** `dev-wave-t2417-policy-arm-perf` が
  対象 3 file すべてで merge 競合中 (`UU` 2 件) のまま生きており (同日 07:21 に段 6 の子が完了)、
  probe を 315 行変更し、繰延べ 2 entry の行番号更新と entry 2 の理由文追記を持っている。
  依頼文と codex 相談のどちらも挙げていなかった。本 wave は実装面を触らないので影響は無い。
  依頼文の見立て (main で同 file を直近に変更したのは T-2265 であって T-2418 ではない) は
  commit 履歴として正しいことを確認した。
- **親の段 1 brief に 4 件の誤りがあり、子が訂正した。** 失敗台帳の番号を F1402 と書いたが
  正本は F794。sink 2 を trace 無効の性能 build とだけ書いたが診断 mode では同じ sink が
  計測用 binary も作る。不変条件「`DEFINE_SPECS` との積集合で要求を作る」は過大で、
  registry 外の flag が黙って落ちる。アンカー表が挙げた counter 行は probe 固有ではなかった。
- 配線の型としては `backoff_sweep.py` より `orchestrator/campaign/screening_driver.py` の
  `_run_condition_gate_for_genome()` 系が近い。genome の flags から要求を導出する形を
  既に実装している。将来の配線 wave はこちらを型にする。
- 逐語と実測の生出力は `output/insights/2026-09-09_t2213-probe-condition-gate/`。

## 次の一手差分

### 更新

- [T-2213] **P2・ユーザー裁定待ち**: `t2187_adaptive_const_probe.py` の build 地点 2 件を
  条件関門へ正配線する件。解除条件の文言 (entry 1 の「本 wave の scope 外」) は満たすが、
  技術的前提 2 件が未充足であることを実測した
  ({{D:t2187-probe-condition-gate-deferral-maintained}})。取りうる形は
  (a) 実行時意味の witness を 13 macro へ新設してから配線する、
  (b) supply と family だけ配線し実行時意味は未確立と成果物へ明記する、
  (c) 繰延べを維持したまま計算ノードで inert 実測だけ先に取る。
  成果物影響 = 放置すると、論文の主要 driver の測定条件は関門の外に在り続ける。
  base: 30bb051a37326ac5737482a87f5d5dd6fe10f752d8210f494b141abb0ce1e243

### 新規

- {{T:probe-condition-gate-inert-supply-compute-node}} **P2・新規**: patch stack を当てた木の
  inert 要求が supply effectuation の緑に到達するかを、計算ノードの job で実測する。
  login node は gflags / glog を持たず configure が止まる。[T-2505] と同型の問いである。
  成果物影響 = これが赤なら、この driver への関門配線は driver を止めるので採れない。
- {{T:condition-gate-runtime-meaning-witness-for-backoff-macros}} **P2・新規・ユーザー裁定待ち**:
  実行時意味の witness を backoff 系 13 macro へ広げるかを裁定する。共有の正しさ防壁の
  改造であり、macro ごとの実行時 witness と負例と変異が要る。
  成果物影響 = 広げない限り、この族の条件は supply までしか機械証拠を持てない。
- {{T:closure-check-enclosing-scope-sink-reachability}} **P2・新規**: 閉包検査が、外側 scope から
  条件を受け取る build sink の macro を到達不能と分類する穴を塞ぐかを判断する
  ({{F:enclosing-scope-build-sink-hides-macros-from-closure}})。
  成果物影響 = 塞がない限り、入れ子関数へ build を置くだけで閉包の網から外れる。
