---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-acceptance-hotspots
seq: 1
title: 受入の直列鎖を支配していた 1 node を 171 秒から 94 秒へ縮め、走査型 gate の fail-open 4 箇所を塞いだ (コード+テスト+docs、branch worktree-dev-wave-acceptance-hotspots、変異matrix = baseline PASSED・MUT-1〜8 8/8 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

ユーザーが直接起票した依頼である。「受入全走で重い箇所を探索し、並列化やより賢い方法で
改善を試みて」。探索は親が実測で行い、実装 scope は段 4 で確定した。

**探索の結論は「wall は work 総和でなく直列鎖で決まる」で、D531 の模型が今も成立していた。**
既定並列度 3 走で `wall − 鎖` は 61.6 / 28.2 / 24.1 秒、D531 が記録した固定費 20.6〜28.8 秒の
内側かその近傍である。work 総和は 6,705.3 / 5,671.3 / 5,742.3 秒で、48 並列に対し鎖が
320〜330 秒あるため、コアを増やしても減らしても wall は鎖から離れない。

**鎖の 53% が 1 node だった。** `test_verify_replays_complete_fake_codex_experiment` が
170.92 / 171.11 / 171.68 秒。login node の cProfile で分解すると
`git fsck --unreachable --no-reflogs` の直列待ちが 129.9 秒 (188 回)、
path ごとに `Path.parent.resolve()` を呼ぶ filesystem 走査が 55.1 秒 (94 回) だった。
`_joinrealpath` 501,381 回、`lstat` 5,072,948 回。

**鎖は D532 記録時 (2026-08-18、77.5〜94.9 秒) から 5 日で約 3.5 倍に伸びていた。**
主因は直前の wave がこの node を既定走行へ戻したことである。

**段 3 の敵対 2 レンズが親 brief を 3 点訂正し、親は全部採用した。**
(a) 親の目標値 (鎖 190 秒 / wall 215 秒) は楽観で、理論上限 (fsck 約 97 秒 = `sum − max`、
1 snapshot あたり 4 repository / resolve 約 35 秒) とほぼ同値で余白がない。
(b) 不変条件「fsck の実行回数が変わらない」は異常経路で維持不能である。先行起動があるため、
先頭 spawn 失敗時に逐次版なら未起動の後続が並行版では起動済みになりうる。
(c) **`verify_snapshot` は同一 snapshot に対し filesystem 走査を 2 回している** —
allowlist 照合 (`_git_closure_reasons` 内) と oracle 構築で、両観測を突き合わせる検査は無い。
47 verify に対し 94 call はこの exact duplicate である。親が実コードで裏取りし、scope へ入れた。

**段 6 のレビュー A が blocker を出した。** 新しい走査は列挙失敗を拒否するようにしたが、
**同じ F363 型の fail-open が兄弟 3 箇所に残っていた** ({{F:scandir-fail-open-siblings}})。
とくに closure 検査の `any(path.rglob("*"))` は、`.git/logs` を列挙不能にすると
「reflog closure is not empty」が出ない。走査型の防壁が反転する。親が現物で裏取りし、
4 箇所すべてを `_scandir_entries` 経由へ統一した ({{D:scan-gate-fail-closed}})。

**production の内部 `assert` も構造化拒否へ置換した。** `assert` は最適化フラグで消えるため
正しさ境界の判定に使わない。副次的に、「fsck 結果を回収しない」変異が test gate より先に
`AssertionError` で落ちて検出力が見えなくなる mask も外れた。

**実測 (Pegasus 計算ノード、既定並列度)。** 対象 node は 170.92 / 171.11 / 171.68 秒 (変更前 3 走) から
93.83 / 93.87 秒 (変更後 2 走) で -45%。**この値は node 負荷に依存しない。**
鎖は 320.9〜329.7 秒から 197.0 / 266.4 秒、wall は 345.9〜391.3 秒から 229.5 / 303.2 秒。
ただし変更後 2 走目は work 総和が 7,443.9 から 11,457.6 秒へ膨らんだ混雑ノードに当たっており、
鎖と wall は node 負荷で交絡している ({{D:chain-metric-is-load-confounded}})。

**焦点走で本 wave と無関係な赤を 4 件踏んだ。** `replay_stage2_plan` の既定 wall-clock 予算は
1.0 秒 (timeout 検査は 0.1 秒) で、混雑ノードでは正常な処理でも超える。単独再走で 4 件とも
4.00 秒で緑になり、`replay_stage2_plan` は本 wave が変更した関数を 1 つも呼ばない。
赤が出た走の焦点走 wall は 916 秒で、緑の走の 256 秒に対し 3.6 倍だった。非帰属である。

**変異 matrix は 8 件すべて KILLED で、期待 node 集合は全件 EXACT 一致。**
baseline は PASSED (387 passed / 2 skipped / 165.00 秒)、SURVIVED と MISMATCH は 0。
期待 node は推測で書かず、全件 SURVIVED 期待の probe 相を先に走らせて観測集合を集めてから
本走で KILLED 期待として登録した。M05 (executor 構築失敗で検査を skip) と
M06 (別 snapshot の走査結果を使い回す) は期待 node 1 件、M08 (closure 検査の列挙失敗を
握り潰して空扱いに戻す) は 2 件で単一理由性が明確である。M02 (17 件) / M03 (8 件) /
M07 (32 件、過剰拒否の正例) は過剰決定であり、単独変異の証拠としては冗長 gate と明記する。

**変異 harness が group 注釈された node を期待 node として表現できない制約に当たった**
({{F:mutation-harness-cannot-pin-group-annotated-node}})。該当 1 件を `--deselect` で外し、
理由を実行スクリプトへ書いた。残る 6 件で M04 の検出力は示せている。

**worker 数の既定変更は本 wave で実装していない。** D532 が提案対象から外しているためである。
実測は既定 (48) 391.28 秒 / `-n 32` 358.96 秒 / `-n 16` 345.89 秒で単調改善だが、
別 job・別ノードの非対測定であり D531 の要件を満たさない。新事実として裁定へ返す
({{T:acceptance-nproc-default-reruling}})。

エージェント工数は codex 子 7 本 (plan 1 / consult 2 / author 1 / review 2 / fix 1)、
いずれも `gpt-5.6-sol` / `xhigh`。**author 子と fix 子はどちらも計算ノードのキュー混雑
(gen_S に 106 件待ち) で pytest を 1 件も実走できず、「実装済み・未実走」「partial」と
正しく申告した。実走はすべて親が行った。** 段 6 のレビュー子は 1 回目の投入で親の argv 誤り
(`--lane` は `--stage consult` でだけ指定できる) により即死し、`.done` を残したまま
新しい path で再投入した。

## 次の一手差分

### 新規

- {{T:acceptance-nproc-default-reruling}} **P1・ユーザー裁定待ち**: 受入全走の worker 数既定を
  再裁定するか諮る。D532 は「worker 数の増減は実測で効果が無いか悪化する」として提案対象から
  外しているが、その `-n 32` の根拠は D531 が退けた模型である。本 wave の実測は
  既定 (48) 391.28 秒 / `-n 32` 358.96 秒 / `-n 16` 345.89 秒で単調改善し、work 総和も
  6,705.3 / 4,860.9 / 3,360.9 秒と減る。ただし別 job・別ノードの非対測定なので因果は未確定。
  D531 準拠の測定設計 (同一割当内で 3 arm を Latin-square または random block で 6 組以上、
  block 内 paired difference で報告) を実施してよいかを含めて諮る。
- {{T:verify-snapshot-fanout-reduction}} **P2・新規**: `verify_snapshot` の呼出し扇形を縮約する。
  1 node 内で 47 回呼ばれており、内訳は fixture 2 / supervisor 25 / replay 20。
  supervisor の probe 結果を第 1 arm の before へ、第 1 arm の after を第 2 arm の before へ
  渡せば 25→15、replay の live verify 単位を変えれば 20→4 になる。artifact 照合は減らさないが、
  同時外部 mutation を観測する時間窓が減るため、静止契約または開始・終了 bracket の明文化が要る。
- {{T:real-repo-chain-test-restructure}} **P2・新規**: real-repo 鎖の 2〜4 位を含む test 構成を見直す。
  いずれも同じ module snapshot に対する closure / fsck / filesystem verify を独立に構築している。
  module-scoped full-experiment fixture の共有と、tamper 検査の pure/synthetic 分離が候補。
  `REAL_REPO_SERIAL_NODES` の排他閉包を弱めないことが前提で、鎖外へ出せるのは
  実 repo と共有 submodule を一切使わない部分だけである。
- {{T:mutation-harness-group-annotated-expected-node}} **P2・新規**: 変異 harness が
  xdist の group 注釈付き node を期待 node として扱えるようにするか裁定する。
  記録側の `FAILED` 行は `@<group>` を持ち、`--collect-only` 由来の実在検査はそれを持たない。
  本 wave は該当 1 件を `--deselect` で外して回避した。
- {{T:s8c-preregistration-chain-second}} **P2・新規**: `s8c-preregistration-candidate` group が
  第 2 の直列鎖になっている。実測は 64.7〜248.7 秒で node 負荷に強く依存する。
  real-repo 鎖を縮めた後はここが wall の下限へ近づくため、内訳を測って裁定する。
