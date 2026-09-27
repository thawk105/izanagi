単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy

作業木 (あなたが編集してよい唯一の木): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl (branch `fix-t2273pi-impl-1`、HEAD は wave 木の統合 commit と同内容)
所有 path (これ以外を編集しない): `orchestrator/tests/conftest.py`、`orchestrator/tests/test_s8b_oracle_driver.py`。
docs は編集しない。commit しない (起動器が終端で記録する)。

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s6-ruling.md — **段 6 裁定。fix L の対象は B1・A1・A2 だけ。** 変異 erratum E1・E2 も読む。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/s4-ruling.md — 段 4 裁定 (プラン v2 と規模: 変更は本題に必要な範囲だけ)。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s6-review-a-out.md、s6-review-b-out.md — 所見の本文。
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/s5-author-l-prompt.md — 段 5 の実装子契約 (「規約」節)。**全文を継承する。**
- 作業木の orchestrator/tests/conftest.py (`_start_t080_visible_output_snapshot`、`_finish_t080_visible_output_snapshot`) と orchestrator/tests/test_s8b_oracle_driver.py (`_t080_copy_visible_output`、`test_t080_visible_output_snapshot_starts_once_and_preserves_copy`)。

## 直すこと

1. B1: T1 で、同じ `config` と同じ `testrunuid` を持つ**別々の** node (`SimpleNamespace` 2 個) それぞれで本物の `pytest_configure_node` を呼ぶ。実関数 spy が 1 回であることの検査は維持。
2. A1: `_finish_t080_visible_output_snapshot` で join・削除・生成エラーを個別に扱い、保存済みの生成エラーがあればそれを優先して伝播する (削除の失敗は生成エラーが無いときだけ伝播)。数行に収める。
3. A2: T1 の signature に `stat.S_IMODE(path.stat().st_mode)` を加える (必要なら `import stat`)。

## 規約

- **既存テストの期待値を変更しない。** 反転・緩和・skip・xfail・削除を禁じる。赤なら実装側が誤りとする。期待値が誤りと考えるなら実装を変えず報告して止める。
- 上の 3 点以外を変えない (仮想リスク向けの gate・検査・一般化を足さない)。
- 変異 erratum E1・E2 と登録変異 P0・M1〜M7 について、fix 後の実装で置換 old 文字列 (s6-review-a-out.md の「変異の再照準」表を基に) が各 file 内で一意か、単一理由で T1 / T2 が落ちるかを静的に確かめ、確定した old / new 文字列の表を報告する (実行は不要、親が harness で走らせる)。
- テストの実走: この sandbox では pytest が拒否されうる。走らせられなければ「実装済み・未実走」と書き、`python3 -m py_compile` を通す。

## 出力形式

- `## 変更`、`## 実走`、`## 変異の置換表` (ID、file、old、new、kill node と assert)、`## 総括` (3〜6 行)
