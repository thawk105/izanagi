## 対応表

| 対象 | 状態 | 根拠 |
|---|---|---|
| FIX-1 | `closed` | live lock handle を導入し、再検証と action を caller-held lock 内へ統合。[production:289](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py:289)、[production:699](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py:699)、[production:5115](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py:5115)、[test:2173](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/tests/test_s8b_holdout_admission.py:2173) |
| FIX-2 | `closed` | marker、claim、主台帳行の canonical bytes digest を identity に束縛。[production:281](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py:281)、[production:5076](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py:5076)、[test:2544](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/tests/test_s8b_holdout_admission.py:2544) |
| FIX-3 | `closed` | retry 非0正負例、cut-6 `use()`、5軸の移植負例を追加。[test:2210](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/tests/test_s8b_holdout_admission.py:2210)、[test:2254](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/tests/test_s8b_holdout_admission.py:2254)、[test:2460](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/tests/test_s8b_holdout_admission.py:2460) |
| FIX-4 | `closed` | journal writer が root lock に参加せず、TOCTOU 窓が残ることを公開 docstring に明記。[production:339](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py:339) |
| 既知の赤 | `closed` | `_issued_cell(tmp_path / "current")` の呼び手側で親 directory を作成。[test:2126](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/tests/test_s8b_holdout_admission.py:2126) |

いずれも実装上の判定です。pytest は infrastructure failure で未実走のため、green とは申告しません。

## FIX-1 の採用形

`_locked(root)` が seal、live flag、fd、対象 root を持つ `_AdmissionRootLock` handle を yield します。`use()` と実際の再検証 helper はこの live handle を必須とし、action にも同じ handle を渡します。

これにより registry 側は後続単位で次の形へ接続できます。

- 既存の root lock を一度だけ取得する。
- 得た handle を `use(lock=...)` に渡す。
- action は渡された handle を lock-aware な更新 seam に渡し、同じ file lock を再取得しない。

通常構築した handle と context 終了後の失効 handle は拒否します。[test:2491](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/tests/test_s8b_holdout_admission.py:2491)

採らなかった候補は次のとおりです。

- `use()` 内で再取得する形: 同じ `flock` の自己 deadlock を残すため不採用。
- 再検証後に unlock して action を実行する形: durable evidence と action の同一 lock 区間を失うため不採用。
- caller-held lock を docstring だけで要求する形: lock 未保持でも呼べるため不採用。
- admission lock 全体を暗黙に再入可能へ変える形: 全 caller の lock 意味を変更し、本2ファイルの API seam より広い影響を持つため不採用。

## FIX-2 の3 digest

共通の `_sha256()` は canonical JSON bytes を sha256 化します。[production:566](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py:566)

identity への算出箇所は以下です。

- disk marker document: `marker_document_sha256`
- current claim document: `claim_document_sha256`
- 主台帳の該当行: `main_ledger_row_sha256`

3件とも [production:5076](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py:5076) で算出し、発行時 identity と使用時再導出 identity の完全等値で比較します。主台帳行の一意選択は [production:4940](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py:4940) です。

`_measurement_generation_claim_digest` の導出式は変更していません。[production:923](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py:923)

`entry_kind` を `"fresh"` から許可値 `"resume"` へ変える発行後改竄負例を追加し、action 未実行も検査しています。

## テスト

要求された command を実行しました。

```text
python3 tools/run_tests.py orchestrator/tests/test_s8b_holdout_admission.py -q -rf
```

結果:

- rc: `16`
- 原因: `qstat -Q preflight rc=1`
- dispatch child: 未起動
- 実走した nodeid: なし
- passed: 0
- failed: 0
- 判定: infrastructure failure。green ではない

追加・更新した焦点 node 定義には以下を含みます。

- retry ordinal 1 の正例と、1を0へ移植する負例
- cut-6 marker の `use()` 正例
- `root`、claim digest、`attempt_id`、`campaign_run_id`、`cell_id` の独立 parametrize node
- `"fresh"` から `"resume"` への発行後 claim 改竄
- 未発行および失効 lock handle の拒否

代替の静的確認はすべて成功しました。

- 両ファイルの AST parse
- production module import
- test module import
- `use()` の keyword-only `lock` signature
- 3 digest field の dataclass 射影
- `git diff --check`

runner が作った未起動 dispatch receipt と、この作業中に生成した pyc は除去済みです。

## 変更範囲

HEAD は `6ff06800de0e2a0a8ac261d2e20320e68db8ebb3` のままです。`git add`、`git commit` は行っていません。

- [s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py): 6836行、HEAD 比 `+420 / -13`
- [test_s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/tests/test_s8b_holdout_admission.py): 4215行、HEAD 比 `+578 / -0`

合計は `+998 / -13`。`git status --short --untracked-files=all` と `git diff --name-only` は指定2ファイルだけです。既存 test の期待値は変更、削除、緩和、skip していません。

## 所有外への波及

静的に確認した波及可能性は次のとおりです。

- `s8b_attempt_registry.py`
  - `_locked(root)` の既存4 caller は yield 値を無視するため互換です。
  - 単位 A の接続時は `with admission._locked(root) as lock` とし、lock-aware 更新 seam から `use(lock=...)` を呼ぶ必要があります。
- `test_s8b_attempt_registry.py`
  - 現在は新 capability の consumer test ではありません。単位 A で handle plumbing の consumer test が必要です。
- `s8b_floor_campaign.py`
  - 現行経路は新 capability を呼ばず、既存 `consume_attempt_ticket` のままです。
- `s8b_floor_stats.py`
  - inspection API の既存 import のみで、新 handle API の caller ではありません。
- `s8b_floor_evidence_fixture.py`
  - durable evidence producer bytes と legacy fixture は変更していません。
- 共有 test helper
  - `_consumed_marker_capability_case` に retry ordinal 1 の任意経路を追加しました。既定値は従来どおり planned ordinal 0 です。
- repo 内の新 API caller
  - 指定 test file 以外には存在しません。設計資料の文字列参照だけが見つかりました。

## 総括

FIX-1からFIX-4と既知の赤を、指定2ファイル内で修正しました。caller-held live lock handle、3 durable document digest、retry・cut-6・5軸・許可値間改竄の test を追加しています。最終差分は2ファイルのみですが、Pegasus dispatch infrastructure failure により pytest は0 node実走であり、実装済み・実走未確認です。