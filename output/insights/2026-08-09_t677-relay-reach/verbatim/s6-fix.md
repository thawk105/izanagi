F1〜F10 をすべて実装しました。変更は許可された 2 ファイルのみで、commit・add・stash は実行していません。production 側の失敗受理条件、exit code、緑走行の無出力条件は変更していません。

### 所見別対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F1 | closed | sidecar から worker banner を検証・再構成し、byte/hash/manifest/excerpt を厳密検算。[test_pytest_failure_digest.py:595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:595) |
| F2 | closed | 論理 LF を物理行へ戻し、全行に `> ` を付与。4,096-byte 上限と escape を維持。[conftest.py:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/conftest.py:380) |
| F3 | closed | block を一度だけ描画する incremental 選択へ変更し、呼出回数を固定。[conftest.py:595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/conftest.py:595)、[test_pytest_failure_digest.py:412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:412) |
| F4 | closed | inner 例外中も digest を試み、emitter の全例外を抑止して元例外を維持。pluggy 経由で固定。[conftest.py:679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/conftest.py:679)、[test_pytest_failure_digest.py:837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:837) |
| F5 | closed | `ModuleNotFoundError(name="tools")` だけ無言 fail-open。その他は一行 ERROR。[conftest.py:648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/conftest.py:648) |
| F6 | closed | pass/skip/xfail/xpass/0 collected/collect-only と、strict xpass/collection error を実 subprocess で検査。[test_pytest_failure_digest.py:498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:498) |
| F7 | closed | 非ASCII・C0・backslash を含む二行目 decoy を raw/relay 1段/2段で consumer に通過。[test_pytest_failure_digest.py:907](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:907) |
| F8 | closed | 65,536 bytes丁度、digest 開始境界の前後、後続出力による欠落を固定。[test_pytest_failure_digest.py:972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:972) |
| F9 | closed | hash・stderr・excerpt対応・writer結線・relay定数導出を独立検査。[test_pytest_failure_digest.py:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:226) |
| F10 | closed | コメントを逐次再入へ限定し、実 `pytest.main()` 入れ子で外側 stash が消える現仕様を固定。[test_pytest_failure_digest.py:882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:882) |

検査結果:

- `python3 -m pytest -q orchestrator/tests/test_pytest_failure_digest.py`
  - 最終結果: `14 passed in 3.16s`
- 個別に全14 nodeidを実走。E2E/relay 3 nodeidは `3 passed in 1.13s`、実終了形は `1 passed in 1.64s`。
- 中間で例外テストの `writes.clear()` 不足により1件赤になりましたが、fixture分離後の同一範囲再走は `10 passed`。残存赤はありません。
- 追加 subprocess は計7起動、実測総 wall は全ファイル込み約3.2秒。timeout は10秒、12秒×5、15秒で、1起動15秒以下です。timeout 時の process group TERM→KILL・消滅確認を維持しています。
- monkeypatch は relay 定数との動的導出検査1箇所だけです。loader に引数/config seam がなく、固定値化変異を検出するため module attribute を一時変更しました。

静的な波及先は、canonical pytest 全走が共有する `conftest.py` hooks、xdist controller/worker、`dispatch_compute.DEFAULT_FAILURE_RELAY_LIMIT_BYTES`、`_relay_scheduler_logs`、`mutation_harness._failed_nodes`、plain-runner/self-run harness です。

未実装・裁定外は、U1（pre-item/internal error）、U2（SIGKILL/OOM/PBS打切り）、U3（relay耐久化）、U4（session束縛collectorへの全面移行）、D#9の2-byte余裕最適化です。M1〜M7の実変異と親の受入全走もauthor子の担当外として未実走です。

## 総括

- F1〜F10: targeted 実走に基づき全件 `closed`。
- 最終範囲: `orchestrator/tests/test_pytest_failure_digest.py` 全体、14 passed / 3.16s。
- E2E oracle は実 xdist bannerを独立再構成し、394,344 bytesを含む全会計を厳密検証。
- 残る赤: なし。親の受入全走は未実走であり、子の結果では代替していない。
- 変更ファイルは指定2本のみ。commit・git add・stashなし。