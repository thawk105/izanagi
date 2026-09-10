# [T-1619] 段 4 裁定の追補 — 変異事前登録の訂正

段 5 の実装子起動後、親が変異の**帰属可能性**を独立に検査して欠陥を見つけたので、
`s4-adjudication.md` の「変異事前登録」節を本追補で置き換える。
plan も段 3 の 2 レンズもこの欠陥を指摘していない。

## 発見した欠陥

変異 harness は変異を **commit せず working tree へ書くだけ**である
(`tools/mutation_harness.py:2096` の `target.write_text(...)`。commit する経路は無い)。

一方、本族が評価する対象は **HEAD の git blob** である。

- `_snapshot_current_commit` は `git ls-tree -r --name-only HEAD` と
  `git archive --format=tar HEAD` で HEAD の blob を新しい一時 repo へ写す
  (`orchestrator/tests/test_s8c_preregistration_predicates.py:151-165`)。
- `evaluate_all` は `core.resolve_commit` と `_read_blob_at_resolved` で
  解決済み commit の blob を読む
  (`orchestrator/campaign/s8c_preregistration_evidence.py:3114-3123`)。

したがって次の区別が成立する。

| 変異対象 | working tree 変異の可視性 | 理由 |
|---|---|---|
| **評価器のコード** (`orchestrator/campaign/s8c_preregistration*.py`) | **見える** | test process が working tree から import する |
| **評価される repository の内容** (`p3_autonomous_workload_trial.py` 等を blob として読む面) | **見えない** | 評価は HEAD の blob を読む。working tree の変更は HEAD に入らない |
| **evidence 契約 file** | **見える (snapshot 側のみ)** | `_write(root, core.EVIDENCE_CONTRACT_PATH, CONTRACT_FILE.read_bytes())` が working tree を読んで snapshot へ上書きする (`:166`) |

`s4-adjudication.md` に登録した m03 / m04 / m05 は 2 行目の型であり、
**偽の SURVIVED になる**。このまま走らせると「変異が生き残った」という誤った証拠を作る。
`DW-M04` の「注入なしを緑と報告しない」に抵触する。

## 訂正後の変異事前登録

版 A = 変更前 HEAD 版 (共有化なし)、版 B = 変更後版 (共有化あり)。
**KILLED の条件は、A と B で赤くなる node 集合が完全一致すること**とする (`DW-M08` の対称形)。
片方だけが赤い、または赤い node が異なる変異は検出力が変わった証拠として停止する。

| ID | 変異対象 | 変異内容 | 期待 KILLED node (完全集合) | 帰属の根拠 |
|---|---|---|---|---|
| m01 | 評価器コード | `EvidenceRef` を作る経路で `blob_sha256` を 63 文字に切り詰める | `test_current_repository_snapshot_has_zero_satisfied_predicates` | `len(ref.blob_sha256) == 64` を見る assert は本族でこの 1 件。import 経路なので可視 |
| m02 | evidence 契約 file (working tree) | 有効 whitespace 1 byte を別の有効 whitespace へ置換 (**非対称**) | `test_current_repository_snapshot_exactly_matches_head` | snapshot 側だけが working tree を読むので snapshot と実 HEAD がずれる。完全等値を見るのは本族でこの 1 件。status / reason は不変 |
| m03 | 評価器コード | C11 の reason code literal を別の登録済み reason code へ置換 | `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` | C11 の reason literal を見るのは本族でこの 1 件。snapshot 側と HEAD 側の両方が同じ評価器を使うので対称に変わり、`exactly_matches_head` は緑のまま (過剰決定を避ける) |
| m04 | 評価器コード | C12 の status を `EVIDENCE_UNDEFINED` から別の status へ置換 | `test_current_repository_gap_reason_snapshot_requires_cross_wave_review`, `test_current_repository_c12_registry_reports_unwired_allocation_consumer`, `test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer` | C12 の status を見る 3 件が同時に赤くなる。**過剰決定を認めた上で 3 件を期待完全集合として登録する** (`DW-M03`) |
| m05 | 評価器コード | C12 の reason code literal を別の登録済み reason code へ置換 | 同上 3 件 | m04 と別 run。reason 側の経路を別に踏む |

### 実装子・fix 子への追加要求

- 各変異の anchor が対象 file に**一意に存在する**ことを適用前に検査する (`DW-M04`)。
  一意でなければその変異を実行しない。
- m01 / m03 / m04 / m05 の具体的な file:line と置換文字列は、段 6 の変異 matrix 準備時に
  評価器コードを読んで確定する。本追補では帰属の型だけを固定する。
- 版 A / 版 B の clean 走 (非変異) が両方緑であることを毎回記録する (`baseline 緑必須`)。

## 実施前に親が行う実証

段 6 で matrix を走らせる前に、親が `DW-O19` に従って次を 1 回ずつ実測し、
本追補の可視性の表が正しいことを確かめる。

1. 評価器コードの working tree 変異 → 本族が赤くなること (可視の実証)。
2. blob として読まれる repository 内容の working tree 変異 → 本族が緑のままであること
   (不可視の実証。これは「変異が効かない」ことの positive control であり、
   偽 SURVIVED を作らないための根拠になる)。

実装子が tree を占有している間は行わない。復元は `git diff` と `git checkout --` を正本とし、
変異前に `--porcelain` 空を確認する。

## 採用しなかった追加の共有化 (backlog)

`_snapshot_current_commit` は archive 対象 path を決めるために
`evaluate_all("HEAD", repo_root=_ROOT)` を既に 1 回実行している
(`test_s8c_preregistration_predicates.py:145-149`)。
これを `test_current_repository_snapshot_exactly_matches_head` の右辺と共有すれば
さらに約 13 秒縮むが、**採用しない**。本族は `REAL_REPO_SERIAL_NODES` に属さないため、
fixture 構築時点と assert 時点の間に実 repo が他の writer に変えられる可能性があり、
現行コードはその不一致を赤で検出する。共有するとこの検出を失う。
