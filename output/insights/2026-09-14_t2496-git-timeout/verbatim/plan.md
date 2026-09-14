## 挿入点

行番号は読取り時点のもの。変更は指定の 2 ファイルに限定する。

- `orchestrator/campaign/trial_registry.py:256` の `_GIT_ENV_ALLOW` が終わる **263 行直後**へ `_GIT_TIMEOUT_S = 300.0` を追加する。
- 同ファイル **967–977 行**の `_git` を次の形へ置き換える。既存のコマンド、環境、出力形式、終了コードの扱いは維持する。

```python
def _git(
    repository_root: Path,
    args: Sequence[str],
    *,
    timeout_s: float = _GIT_TIMEOUT_S,
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", "-C", os.fspath(repository_root), *args],
            env=_git_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise TrialRegistryError(
            f"[git-operational] git command timed out after {timeout_s:g}s"
        ) from exc
```

挿入位置は、既存 **969 行の後**が keyword-only 引数、**971 行**が `try` と既存呼出しのインデント変更、**976 行の後**が `timeout=timeout_s`、既存 **977 行の後**が捕捉・変換である。新しい例外型、retry、部分結果の返却は追加しない。

## 注入 seam

現在の `_git` には予算引数も timeout 定数もなく、既存の予算注入 seam はない。**既定値付き keyword-only 引数を追加する案を採用する。**

同型の前例は `tools/dev_waves/git_state.py:178` の `_run`。**183 行**で `timeout_s: float = _GIT_TIMEOUT_S` を受け、**195 行**で `subprocess.run` に渡し、**197 行**で `TimeoutExpired` を業務例外へ変換している。campaign 内にも `orchestrator/campaign/pipeline.py:409` の `_run_trace` に、定数を既定値とする `timeout_s` 引数がある。

テストは `R._git(..., timeout_s=0.25)` と直接指定する。module 定数や `subprocess.run` の monkeypatch は不要で、DW-O14 に沿う。なお、定数を既定引数に束縛した後の定数 monkeypatch は既定値を変えないため、両方式を混用しない。

## 受理を広げないことの確認

`trial_registry.py` の指定された 10 捕捉箇所の結論は次のとおり。

| 行 | 関数 | 処理と timeout の扱い |
|---|---|---|
| 613 | `_decode_json` | 再送出。JSON 処理から `_git` への辺もない |
| 645 | `_read_regular_bytes` | 再送出 |
| 1138 | `_open_registry_parent` | fd を閉じて再送出 |
| 1895 | `append_trial_registration` | 再送出 |
| 2462 | `_write_create_only` | 再送出 |
| 2578 | `_looks_like_attempt_genesis` | `False` に変換するが、捕捉範囲は JSON decode のみ |
| 3044 | `_locked_attempt_registry_update` | 再送出 |
| 4674 | `_locked_lifecycle_update` | 再送出 |
| 5687 | `_exclusive_create_acceptance_receipt` | 再送出 |
| 6609 | `main` | `parser.error(str(exc))` による CLI エラー終了 |

唯一の `False` 変換について、呼出し方向は以下となる。

```text
_assert_attempt_registry_history_append_only
  ├─2606: _git(rev-list ...)
  ├─2617: _attempt_tree_paths
  │         ├─2543: _git(ls-tree ...)
  │         └─2560: _git(cat-file ...)
  └─2634: _looks_like_attempt_genesis
            └─2577: _decode_json
                      └─json.loads / JSON 検証 callback
```

Git 読取りは genesis 判定より前に完了する必要がある。**2576 行の `try` は Git 呼出しを囲まず、`_decode_json` からも `_git` に到達しない。** したがって timeout を「genesis ではない」に変換する経路はない。

残りの Git 呼出しは、repository/commit 検査（987・1151・1168）、履歴改変・祖先検査（1180・1189・1205・1229・1294）、blob 読取り（1330・1349）、lifecycle/history 検査（4583・5303・5342）にある。いずれも `_git` が例外を送出すれば、終了コードや空出力による分岐へ進まない。

`p3_autonomous_workload_trial.py` 側も、受理への変換は確認されなかった。

- `run_trial` → binding/measurement 検査 → registry → `_git` は、例外伝播となる。
- `run_trial` → attempt 分類・開始・観測開始・terminal 記録 → registry → `_git` は、`BaseException` 捕捉後に再送出、または `mark_experiment_indeterminate` を通る。
- **同ファイル 4538 行**の `mark_experiment_indeterminate` は terminal 記録失敗を補足情報にするが、**4611 行で `raise cause`** する。副次的失敗の捕捉を成功復帰と取り違えない。
- `_finish_trial` の広い捕捉で失敗を記録する場合も、**3764 行**の complete 条件が `fatal_error is None` を要求する。
- `run_origin_trial` の捕捉は `OriginPreflightFailure` または `OriginPartialTrialReport` を返す。`OriginCompletedTrialReport` は正常復帰後の complete 分岐だけである。

## 正例と負例

追加位置は `orchestrator/tests/test_trial_registry.py:5246` の既存 Git operational failure テスト直後、**5249 行の次テストの decorator より前**とする。

PATH shim の前例はある。

- `orchestrator/tests/test_ruleops.py:428`：tmp の `bin/git` を作成し、**442 行**で実行権限、**443 行**で PATH を差し替えて実プロセスを呼ぶ。
- `orchestrator/tests/test_t139_blobref_git_trust.py:53`：絶対パスの Python shebang を持つ偽 Git と、**61 行**の PATH 差替え。
- 短い予算で実際の sleep を遮断する前例は `orchestrator/tests/test_buildcache_v2.py:2227`。2 秒 sleep に **0.05 秒**を渡している。

具体案は以下。

| node 案 | 入力・予算 | 確認内容 |
|---|---|---|
| `test_git_timeout_is_operational_rejection` | `#!/bin/sh` と、解決済み絶対パスの Python を `exec` して `time.sleep(2)`。`timeout_s=0.25` | `[git-operational]` と timeout 診断を持つ `TrialRegistryError`。`__cause__` が `subprocess.TimeoutExpired`、その `timeout == 0.25` |
| `test_git_timeout_allows_completed_command` | 即時に stdout/stderr の sentinel を出して終了する shell shim。同じ `timeout_s=0.25` | `returncode == 0`、stdout/stderr が期待する bytes と一致 |
| `test_git_timeout_allows_real_repository_query` | PATH を差し替えず、既存 `_SOURCE_REPO`（49 行）へ `rev-parse --is-inside-work-tree`。`timeout_s=1.0` | `returncode == 0`、`stdout.strip() == b"true"` |

**負例が排除するのは、timeout 対応が正常な `CompletedProcess` まで一律に拒否したり、stdout/stderr・終了コードを壊したりする変異であり、300 秒が全負荷条件で十分だという主張ではない。**

追加の要点：

- PATH 差替えにだけ `monkeypatch.setenv` を使い、予算は引数で渡す。
- sleep は shell の子として残さず、`exec` で置換する。
- 正例の sleep は有限の 2 秒にする。timeout 指定を削除した変異も、長時間停止せず assertion failure になる。
- 新規 repo 作成・commit・履歴全走は不要。正常実装の subprocess 待ち予算は合計 **1.5 秒**で、追加 node 合計 5 秒以内を狙う。環境遅延を含む実所要は未測定であり、実装段の焦点走で確認する。

## 既存テストへの波及

**既存 16 呼出しを二引数のまま維持すれば、signature 互換性は壊れない。**

- `test_trial_registry.py:5239` の `fail_merge_base(repository_root, args)` は、5242 行で元の `_git` を二引数で呼ぶ。
- 同 **6570 行**の `fail_parent_query(repository_root, args)` も、6575 行で二引数委譲する。

既存呼出しへ `timeout_s=` を追加しないため、これらのラッパーを変更する必要はない。

spawn-site 登録は `test_ccbench_spawn_sites.py:284` の値 **1** を維持する。同ファイルでは、

- **347 行**で関数 scope を管理し、
- **378–387 行**で process API の `ast.Call` ごとに `(relative_path, scope)` を加算し、
- **390–401 行**で production ファイルを走査する。

`try/except` や数値引数の追加は scope も process 呼出し数も変えない。`<module>._git` 内の `subprocess.run` は引き続き 1 個である。

## 所要台帳

**新規 node の entry がないこと自体では赤にならない。台帳変更は不要。**

`orchestrator/tests/conftest.py` の規則は次のとおり。

- **1506 行**：台帳文書を検証する。`nodeid_count` は台帳内の辞書件数との一致であり、pytest の収集 node 数との一致ではない。
- **1546 行**：ファイル読取り・decode 失敗は空の台帳として扱う。
- **1661 行**：node の所要を検索し、通常キーと歴史的な group suffix 付きキーの双方になければ `None`。
- **1726–1729 行**：`None` は未知所要の unit とする。
- **1739–1749 行**：既知所要がなければ並べ替えを省略し、ある場合は未知 unit に既知所要由来の代替コストを与える。

これは実行順のための台帳であり、未登録 node を拒否する網羅性検査ではない。

## 予算値への異議

**300.0 秒固定に異議はない。** brief の観測最大 6.954 秒に対して約 43 倍あり、I/O 待ち支配と負荷変動を踏まえると、今回 subcommand 別に細分化する根拠は不足している。D265 と同じ値という親の根拠とも整合する。

形は「production の既定値を固定定数にし、private helper にテスト用の引数 seam を持たせる」とする。既存 production 呼出しは全て 300.0 秒を使う。

ただし、これは**単一 Git 呼出しに渡す timeout**である。履歴全走の呼出し総数、`run_trial` 全体の終端、OS のプロセス作成・終了処理まで含む厳密な壁時計上限は保証しない。

## 総括

定数 1 個、`_git` の予算引数と例外変換、既存テストファイルへの 3 node 追加で進める。受理へ変換する例外経路は静的検査では見つからず、既存ラッパー・spawn-site 件数・所要台帳の変更は不要。

指定 5 ファイルは全て読取り済み。編集・commit・push・pytest は未実施で、実走の緑や合計 5 秒以内は未確認。補助探索の `orchestrator/campaign/*git*` は該当なしだったが、実例は `tools/dev_waves/git_state.py` で確認した。