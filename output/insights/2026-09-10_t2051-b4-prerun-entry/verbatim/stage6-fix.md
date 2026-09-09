## 所見対応表 (closed / partial / regressed)

| 所見 | 状態 | 根拠 |
|---|---|---|
| レビュー A must-fix／レビュー B 同型所見 | **closed** | 実 issuer 発行・実 loader 検証済みの 202 件 publication を使用し、manifest 外の 202 番目を membership だけで拒否。対象 3 driver とファイル全 26 node が緑 |

## 変更した内容

- [p3_b4_proposal_binding_support.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/p3_b4_proposal_binding_support.py:61)

  - `attempt_count` と `bound_attempt_index` を追加。
  - 既定値は従来どおり 201 件・先頭行。
  - 指定行へ提案 canonical hash を設定し、その attempt_id を返す。

- [test_p3_b4_proposal_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2051-b4-prerun-entry/orchestrator/tests/test_p3_b4_proposal_binding.py:93)

  - 負例を 202 件・index 201 で発行。
  - `dataclasses.replace` による合成 publication と loader monkeypatch を撤去。
  - 実 publication root を各 driver の loader へ渡す。

`orchestrator/campaign/**` は編集していません。commit・push・branch 操作も未実施です。

## 単一理由性の根拠

- 全行の attempt_id、block_id、registry_ordinal は index 由来で一意。
- 全 202 行が適格で、manifest は先頭 201 行だけを収録。
- 202 番目は registry に一意に存在し、manifest には不在。
- driver は実行 driver と一致。
- 202 番目の proposal hash は入力文書の canonical hash と一致。
- 実 loader が publication の receipt・canonical bytes・sealed hash を検証した後、期待どおり `analysis manifest ... membership` で拒否。

## 実走結果 (nodeid と範囲。走れないなら「実装済み・未実走」)

実行:

```text
PYTHONPATH=. python3 orchestrator/tests/test_p3_b4_proposal_binding.py
```

範囲: 対象ファイル全 26 node。結果: **26 passed in 13.84s**、wall 14.55 秒。

対象負例:

```text
...::test_registry_attempt_outside_analysis_manifest_rejects[base]
...::test_registry_attempt_outside_analysis_manifest_rejects[sort]
...::test_registry_attempt_outside_analysis_manifest_rejects[trigger]
```

既存の manifest 内正例も base・sort・trigger の全 driver で通過しています。

fixture 発行時間の5回中央値:

- 201件: 0.434秒
- 202件: 0.492秒
- 実測差: **+0.058秒**

`git diff --check` も通過しました。

## 所有外への波及可能性

静的検索で helper の consumer は次の3ファイルだけです。

- `test_p3_s4_loop.py`: 3箇所。新引数を省略しており、従来の201件・先頭行束縛を維持。
- `test_p3_b4_closed_critic.py`: 1箇所。同じく既定挙動を維持。
- `test_p3_b4_proposal_binding.py`: 新負例だけが202件を指定。他の既存呼び手は既定挙動を維持。

production caller はありません。所有外テストは今回の指定 harness 範囲外のため未実走です。

## 総括

所見は **closed** です。正規 issuer→publication→実 loader の経路を通り、hash・driver・registry 一意性を満たしたうえで、manifest membership だけが拒否理由になる負例へ置き換えました。