## 変更面 (file:line 表)

行番号は現 checkout 基準。変更は `orchestrator/tests/test_pegasus_dispatch_compute.py` の対象 test 内と、その parametrize decorator に限定する。

| file:line | 実装プラン |
|---|---|
| `orchestrator/tests/test_pegasus_dispatch_compute.py:2579` 直前 | `repo_root` を `_REPO` と `Path("/__t2761__/repo release's checkout")` で parametrize。id は `repo-current` / `repo-release-path`。 |
| 同 `:2580` | 引数に `repo_root` を追加。必要な `shlex` は test 内で import し、変更範囲を限定する。 |
| 同 `:2583` | `_job_script` の `repo_root=_REPO` を `repo_root=repo_root` に変更。 |
| 同 `:2592` | 埋込み値だけを置換した `script_body` を作り、大小無視で `release` を含む行を全件列挙し、空を要求する。 |
| 同 `:2590–2591`, `:2593` | marker 名、`mv` と `selected=""` の順序、`while` 不在の既存 3 assert はそのまま維持。 |

追加 helper 関数は不要。対象 test 内の置換表と短いループで実装し、他 test への共通化は行わない。

## P1〜P4 の判断と根拠

**P1：広い定義を採用する。**

path 等の埋込み値を除いた本文について、`release` を大小無視で含む行をすべて列挙する。comment も除外しない。狭い「同一行に marker 参照も必要」は、現行が拒否する template 行を見逃すため不採用。

以下の「赤」は検査定義からの静的な期待であり、実測結果ではない。

| template 由来の行の例 | 現行 | 広い定義 | 狭い定義 |
|---|---|---|---|
| `until [[ -f "${MARKER}.release" ]]; do sleep 1; done` | 赤 | 赤 | 赤 |
| `touch "$marker_tmp.release"` | 赤 | 赤 | 赤 |
| marker file 名と `release` が同じ行にある操作 | 赤 | 赤 | 赤 |
| `RELEASE=1` | 赤 | 赤 | 見逃す |
| `wait_for_release` | 赤 | 赤 | 見逃す |
| `# release handshake` | 赤 | 赤 | 見逃す |
| `RELEASE_PATH=...` と、それを使う marker 操作が別行 | 赤 | 赤 | release 側を見逃し得る |
| `REPO=<埋込み値>; wait_for_release` | 赤 | 赤 | 見逃す |

現 template 自体に `release` 行はない。上表は template に加わった場合の検出範囲である。広い定義は厳密な shell 構文解析ではなく、規律 2 を守る保守的な候補行検査と位置づける。

**P2：環境依存の 7 値を、埋込み位置に限定して除去する。**

| production の位置 | 埋込み値 | 除去する表現 |
|---|---|---|
| `tools/pegasus/dispatch_compute.py:866` | `tmp_path / "result.json"` | `RESULT=` 直後の `shlex.quote(str(path))` |
| 同 `:867` | `tmp_path / "interpreter_probe.py"` | `PROBE=` 直後の同表現 |
| 同 `:868` | `tmp_path / "request.json"` | `REQUEST=` 直後の同表現 |
| 同 `:870` | `repo_root` | `REPO=` 直後の同表現 |
| 同 `:871` | `repo_root / "tools" / "pegasus" / "dispatch_compute.py"` | `DISPATCHER=` 直後の同表現 |
| 同 `:872` | `tmp_path / DC._COMPUTE_MARKER_NAME` | `MARKER=` 直後の同表現 |
| 同 `:863` | `DC._job_name(tmp_path.name)` | `#PBS -N ` 直後の生文字列 |

`_job_name` の定義は同 `:828–831`、`izdw-` と submission directory 名の先頭 10 文字である。

実装位置は対象 test の旧 `:2592`。次の方針で置換する。

- `script_body` を元の `script` から作る。
- 各項目について「改行＋代入名／directive＋正確な埋込み値」を検索し、**値だけ**を `<PATH>` または `<JOB_NAME>` に置換する。置換回数は各 1 回。
- 文字列全体に対して置換してから `splitlines()` する。行全体の除外はしない。
- path は production と同じ `shlex.quote(str(path))` を使う。quote 不要の path ではこれが `str(path)` と一致するため、生文字列を別途置換する必要はない。

これにより `REPO=`、`MARKER=`、行末の追加構文は残る。例えば `REPO=<値>; wait_for_release` は、値を除いた後も赤になる。`str(repo_root)` や `str(tmp_path)` の無限定な全域置換は採らない。本文中の別の文字列まで消すことや、親 path と完全 path の置換順依存を避ける。

`walltime` と `request_sha256` はこの test では固定引数。他の展開値も本 test における環境依存 path ではないため、除去しない。

**P3：同 test の parametrize を採用する。**

- `repo-current`：既存の `_REPO`。
- `repo-release-path`：`Path("/__t2761__/repo release's checkout")`。

後者は `release` に加えて空白・単引用符を含め、shell quote 済みの値を正しく扱う入力とする。`while` は含めない。`_job_script` は path の文字列を埋め込むだけであり、directory 作成や実在確認は不要。

検索では、稼働コード中に旧 node を完全一致で選別する参照は見つからなかった。ただし、**参照が皆無ではない**。

- `orchestrator/tests/acceptance_duration_ledger.json:13320` に旧 node の所要時間 `0.001` がある。
- `tools/acceptance_shards.py:397–404` は未知 node に重み `1.0` を与えるため、新しい 2 node はその fallback 対象となる。収集対象から外れる仕組みではないが、配分重みは変わる。
- docs と過去の出力にも旧 node の記録がある。履歴は変更しない。

duration ledger 更新も今回の scope に含めない。

**P4：`"while" not in script` は触らない。**

brief の不変条件 (i) に従い、元の `script` への assert を維持する。path 除去後へ掛け直すことは今回指定された release 検査の置換に必要ない。

したがって「環境依存文字列で反転しない」は今回の **release 検査**について保証する。path に `while` が含まれる場合まで保証すると、不変条件 (i)・今回の scope と衝突する。

## 変異 matrix 事前登録案 (anchor・期待 node)

対象 node は次の 2 本とする。

- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_compute_marker_is_cross_namespace_evidence_without_release_handshake[repo-current]`
- `orchestrator/tests/test_pegasus_dispatch_compute.py::test_compute_marker_is_cross_namespace_evidence_without_release_handshake[repo-release-path]`

| 区分 | 変更 | 期待 |
|---|---|---|
| baseline | 変異なし | 両 node が緑 |
| 正例対照 A | 正規化本文への検査を旧検査へ戻す | `[repo-release-path]` が赤、KILLED |
| 負例 B | template の marker 公開直前に release 待機を注入 | 両 node が赤、KILLED |
| 等価 M0 | 同位置へ `release` / `while` を含まない comment のみ追加 | 両 node が緑、SURVIVED |

**A：旧検査へ戻す変異**

実装後の `orchestrator/tests/test_pegasus_dispatch_compute.py`、旧 `:2592` の置換箇所に、以下の複数行 anchor を設ける。

```python
    release_lines = [
        line for line in script_body.splitlines() if "release" in line.lower()
    ]
    assert not release_lines, release_lines
    assert "while" not in script
```

このブロックを旧 release assert と既存 while assert の 2 行へ戻す。正規化処理が残っても検査では使われなくなり、旧検査への復帰と同じ効果になる。

期待赤 node は上記 `[repo-release-path]`。`[repo-current]` は実行環境の path に依存するため、この変異の必須赤には指定しない。

この anchor は実装予定形であり、author 後に出現数 1 を確認する。

**B：handshake 注入変異**

`tools/pegasus/dispatch_compute.py:890–892` の anchor：

```text
mv "$marker_tmp" "$MARKER"

selected=""
```

現 source における出現数は静的確認で **1**。先頭の `mv` の直前へ、Python f-string 内の source として次を挿入する。

```text
until [[ -f "${{MARKER}}.release" ]]; do sleep 1; done
```

生成 script では `${MARKER}.release` になる。`until` を用いるため、既存の `while` assert ではなく、新しい release 行検査で赤になることを親が実測確認する。期待赤 node は両 node。

production の変更は変異実験内のみで、成果物には含めない。

**M0：comment のみの等価変異**

B と同じ複数行 anchor を使い、`mv` の直前へ次の comment のみを挿入する。

```text
# Publish compute visibility evidence.
```

両 node の SURVIVED を期待する。`release` を含む comment は現行も拒否するため、等価変異として使用しない。

## 波及と変更しない一覧

指定された他 test の `_job_script` 呼出しと assert を確認した。

| 対象 | 確認結果 |
|---|---|
| `:1054–1073` | manual ID/root の `unset` 検査。変更なし。 |
| `:1115–1131` | sidecar / auto-off の保持検査。変更なし。 |
| `:2290–2313` | interpreter、repo、network bootstrap の検査。変更なし。 |
| `:5924–5937` | mutation attempt marker の export 不在検査。変更なし。 |

検索で追加検出した呼出し `:4080`, `:4142`, `:5055`, `:5340`, `:6119`, `:6616` も確認した。変更は対象 test の入力と局所文字列処理だけで、共有 helper・production・global state を変更しないため、これらへの動作変更はない見込み。

変更しないもの：

- `tools/pegasus/dispatch_compute.py` を含む production。
- 対象以外の test と共有 helper。
- `_REPO` の定義。
- duration ledger。
- docs。
- 既存 3 assert。
- gate の追加、helper の一般化。

## 未確定事項

- pytest、collection、変異実測、受入全走は未実施。期待する緑・赤・SURVIVED は親が確認する。
- 新検査の anchor は author 後に一意性を確認する。現行 test の release／while 連続 2 行と、production の `mv`／空行／`selected` anchor は静的に各 1 箇所と確認済み。
- リポジトリ内の検索では稼働コードによる旧 node の pin は見つからなかったが、リポジトリ外の launcher 設定までは確認していない。

## 総括

広い release 行検査を採用し、7 個の環境依存値だけを埋込み位置で置換する。対象 test に release-path 入力を加え、旧検査復帰・handshake 注入・comment 追加の変異を事前登録する。既存 3 assert と production は維持する。ファイル変更・pytest 実行は行っておらず、緑は未確認。