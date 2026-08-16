# [T-1167] 8c 事前登録 C12 の allocation 節を実現可能な予約 binding へ縮小する

- 実施: 2026-08-17
- branch: `worktree-dev-wave-t1167-c12-allocation-binding`
- 最終 commit: `9aee98f3` (main `32f19421` 直上)
- 裁定: 2026-08-16 /rulings 全件 第 3 回のユーザー裁定、択 (c)

## 何を変えたか

C12 の allocation 節は「実装に存在しない述語 `single_process_required` の呼び出し」と
「8c launcher が single-process 違反と resume を launch 前に拒否すること」を要求していた。
前者は名前が実在せず、後者は module 局所の到達解析では原理的に示せない。結果として
**検査すると謳って 1 度も発火しない保証**になっていた (D441)。

要求を、実在する予約 binding の照合 — `read_binding` / `check_reservation` と
PBS job ID・boot ID・予約期限までの残時間 — だけへ縮小した。

## 縮小で保護されなくなったもの

事前登録本文 §6「既知の構造衝突」の 衝突 (e) に逐語で名指しした。要点は 3 点。

1. 1 割当・1 ノード・1 プロセスでの完走が保証されなくなった。
2. resume 実行が launch 前に拒否されることが保証されなくなった。
3. 予約 binding の照合は may-reach であり、data-flow・支配関係・例外伝播を証明しない。

**新たに拒否されなくなった実行は無い。** 旧要求は充足不能で 1 度も発火していなかったため
(D441 決定 3)、縮小は「発火しない保証を、発火する保証へ置き換えた」ものである。規律 2 の
逸脱ではないが、逸脱に見えうるので注記を本文へ残した。プロセス単独性の運用要求は Pegasus
runbook 側に残り、C12 の証拠範囲から外れただけである。

## 縮小後の binding が実データで発火することの証拠

実 repository の blob に対して、判定器が返す C12 の理由コードが
`environment-contract-consumer-absent` (誤診断) から
`allocation-enforcement-consumer-absent` (実在の欠落) へ変わる。これを 2 経路で pin した。

- production registry 経路 (`PredicateRegistry.evaluate_all` を通した実 repository 判定)
- helper 直呼び (`_c12_allocation_binding_verdict`)

判定の終端は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` のままで、
`SATISFIED` 経路は 1 本も作っていない。**受理集合は不変**である。

## 変異 matrix

`mutation-spec.json` / `mutation-ledger.json` が正本。最終 commit `9aee98f3` で **4/4 KILLED**、
baseline PASSED。期待 node は `mutation-spec-probe.json` の全件 SURVIVED 期待 probe で実測した
完全集合である。

| # | 変異 | 検出テスト数 |
|---|---|---|
| M1 | 必須関数集合から `read_binding` を落とす | 1 |
| M2 | 必須関数集合から `check_reservation` を落とす | 1 |
| M3 | allocation gate を environment gate の後ろへ戻す | 3 |
| M4 | `DECIDER_VERSION` を v1 へ戻す | 2 |

**runner 範囲の縮小 (silent cap にしない):** 変異 runner の範囲は
`test_s8c_preregistration_core.py` と `test_s8c_preregistration_predicates.py` の 2 本である。
`test_s8c_preregistration_invariant.py` を外したのは、当該ファイルの候補 tip テストが
`@xdist_group` 付き node ID を持ち、harness の node 正規化が接尾辞を剥がせず「期待 node が
collection record に無い」で停止するためである。外した結果 M4 の期待 node は 2 本になったが、
同じ変異は不変条件テスト側でも検出される (焦点走で確認済み)。

## 並行 wave との合成

`[T-1250]` が同じ面へ先に着地した。判明した構造事実を 2 点残す。

- **凍結世代 record の blob 不変は全履歴に及ぶ。** 同じ世代番号を並行 wave が先に land すると、
  自 branch の履歴に残る旧 record が `generation-mutated` を発火させる。main を merge しても
  履歴の旧 blob は消えないため解けず、branch を main 直上の線形形へ組み直した。
- **`prepare-revision` は文書変更を未 commit の状態で走らせる。** 文書と契約は作業木から読み、
  履歴は `--commit` で検証するため、文書変更を commit 済みにすると tip record が新しい文書と
  食い違い `record-protected-mismatch` で必ず落ちる。

不変条件テストの競合は、main 側 tip 束縛テストへ本 wave 固有の assert を統合して解いた
(落とした assert は 0 件)。詳細は `verbatim/s6-merge-audit.md`。

## `ruling_reference` の限界

第 5 世代 record の `ruling_reference` は `D441` である。D441 は択一集合を記録した決定であって
**択 (c) の承認そのものではない**。承認の一次資料は record の `revision_reason` の逐語と worklog
であり、この限界は台帳へ明記した。
