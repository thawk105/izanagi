## 追加したテスト

[test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1283) に `t2146` 名の13テストを追加した。

- Write / Edit / MultiEdit / NotebookEdit の root・子孫・未存在 path 拒否
- apply_patch 全 directive と Move 双方向
- Bash redirect、writer、root・祖先・partial glob、相対 cwd
- hardlink、canonical symlink、lexical 独立判定
- sibling・無関係 directory・job dir・worktree の許可
- authority 読取りと symlink entry 自身の unlink/move 許可
- 両 guard の内部例外 fallback
- 実 hook subprocess smoke 4件

`test_plain_runner_coverage.py` の2検査を直接実行し、`test_hooks.py` の既存 `_run()` で全追加テストが収集対象になることを確認した。underscore 始まりの一時 runner は `test_*.py` の対象外で、登録変更は不要だった。

## 変異 M1〜M15 との対応

| 変異 | 対応する歯 |
|---|---|
| M1 | 全 Write 系 tool の root・子孫拒否 |
| M2 | apply_patch Add / Update / Delete / Move 双方向 |
| M3 | Bash `rm -rf <root>` |
| M4 | `cp` / `mv` / `install` / `tee` / `truncate` |
| M5 | `>` / `>>` / `>&` / `&>` |
| M6 | authority-only command、canonical・inode alias の fast-path 到達 |
| M7 | `rm -rf <authority の親>` |
| M8 | 末尾を `?` にした partial glob |
| M9 | 両 guard の hardlink inode alias |
| M10 | 両 guard の canonical symlink alias |
| M11 | 未存在 path と、canonical から独立した lexical fixture |
| M12 | 両 `main()` の内部例外時 rc=2 |
| M13 | `-copy`、`2`、無関係・job・worktree path |
| M14 | symlink entry 自身の Delete / Move / `rm` / `mv` |
| M15 | `cat` / `grep` / `sha256sum` / `stat` |

## 反転検査 runner

[_t2146_inversion_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/_t2146_inversion_runner.py:1) を追加した。

`git show <base>:hooks/guard_{bash,write}.py` で取得した wave 前実装と working tree 実装へ、61件の同一 corpusを入力する。うち51件は authority 以外で、WAL、campaign.lock、build-variants、namespace marker、hooks、ccbench、s8b-freeze、通常開発操作を含む。

実行コマンド:

```text
PYTHONDONTWRITEBYTECODE=1 python3 orchestrator/tests/_t2146_inversion_runner.py f486ff13c7f30cf41fdcb0574744968df4c01077
```

実測結果（rc=0）:

```json
{
  "after": "working-tree",
  "allow_to_deny": 9,
  "base": "f486ff13c7f30cf41fdcb0574744968df4c01077",
  "deny_to_allow": 0,
  "reversals": {
    "allow_to_deny": [
      {
        "id": "bash-authority-redirect",
        "guard": "guard_bash",
        "before": {"allow": true, "reason": ""},
        "after": {"allow": false}
      },
      {
        "id": "bash-authority-copy",
        "guard": "guard_bash",
        "before": {"allow": true, "reason": ""},
        "after": {"allow": false}
      },
      {
        "id": "bash-authority-remove",
        "guard": "guard_bash",
        "before": {"allow": true, "reason": ""},
        "after": {"allow": false}
      },
      {
        "id": "bash-authority-ancestor-remove",
        "guard": "guard_bash",
        "before": {"allow": true, "reason": ""},
        "after": {"allow": false}
      },
      {
        "id": "write-authority",
        "guard": "guard_write",
        "before": {"allow": true, "reason": ""},
        "after": {"allow": false}
      },
      {
        "id": "notebook-authority",
        "guard": "guard_write",
        "before": {"allow": true, "reason": ""},
        "after": {"allow": false}
      },
      {
        "id": "patch-authority-add",
        "guard": "guard_write",
        "before": {"allow": true, "reason": ""},
        "after": {"allow": false}
      },
      {
        "id": "patch-authority-delete",
        "guard": "guard_write",
        "before": {"allow": true, "reason": ""},
        "after": {"allow": false}
      },
      {
        "id": "patch-authority-move-out",
        "guard": "guard_write",
        "before": {"allow": true, "reason": ""},
        "after": {"allow": false}
      }
    ],
    "deny_to_allow": []
  },
  "total": 61
}
```

Runner本体は各 detail に入力と前後の理由も出力する。`deny_to_allow > 0` なら rc=1、runner障害はJSON errorとrc=2になる。

## 直接呼び出しと反実仮想の実測

pytestは指示どおり実行していない。追加13関数を module import 後に直接呼び出し、13/13通過した。したがってpytestとしては「実装済み・未実走」。

実行時 monkeypatch だけで判定を除去した反実仮想は21/21が期待どおり赤化し、`DID NOT RAISE` は0件だった。M9〜M14は必要に応じて両 guard を個別に反転した。

構文検査も実施した。

```text
python3 -m py_compile orchestrator/tests/test_hooks.py \
  orchestrator/tests/_t2146_inversion_runner.py
```

結果はrc=0、`git diff --check`もrc=0。

## 波及可能性

- managed sandboxでは実 authority mountからwritable mountへのhardlinkが`EXDEV`になった。その場合だけ、テストは`tmp_path`内のsynthetic authorityへ切り替えて同じ実装のinode detectorを検査する。通常環境では最初に実 authority public keyへのhardlinkを試す。
- 両 guardが実 authority rootのinode集合を読み取れることも独立に確認している。終了後のpublic keyのlink countは1。
- `hooks/guard_bash.py`、`hooks/guard_write.py`、docsは変更していない。
- `hooks/README.md`には当担当外の既存差分が残っているが、触れていない。
- `git add` / `git commit` / `git merge` は実行していない。

## 総括

M1〜M15を狙う13テストと、61件のD428反転検査runnerを実装した。直接呼び出し13/13、反実仮想21/21、反転検査は`deny → allow = 0`、`allow → deny = 9`だった。pytestによる実測は親に残している。