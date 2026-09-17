## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・根拠 file:line)

以下、`brief`・`plan` は指定された `s1-brief.md`・`s2-plan.md`、`DC` は `tools/pegasus/dispatch_compute.py`、`test` は `orchestrator/tests/test_pegasus_dispatch_compute.py` を指す。赤・緑は静的な期待であり、pytest の実測結果ではない。

1. **real / must-fix / scope内 — plan は環境値と production 定数を一緒に隠す。**
   plan は `MARKER` の basename を含む完全 path と、`DC._job_name(...)` の返り値全体を除去する（`plan:45–46,53`）。しかし marker 名は production の定数、job 名の `izdw-` は template 側の定数である（`DC:82,828–831,845–847`）。

   具体的な退行入力を構成できる。production の marker 定数を `compute.release` に変更し、`mv` の直前へ次を加える。

   ```bash
   until [[ -f "$MARKER" ]]; do sleep 1; done
   ```

   親がその marker を作るまで job が待つ構成なら FA-4 に抵触する。現行検査は `MARKER=/.../compute.release` により赤になる。plan は期待値を変更後の `DC._COMPUTE_MARKER_NAME` から作るため、この `release` を丸ごと隠す。待機行には `release` も `while` もなく、既存の marker 名存在・`mv` 順序検査も通る（`test:2590–2593`）。**広い定義でも、正規化が検出根拠を消せば実害のある後退になる。**

   また `_job_name` が `izdw-release-...` を返す変異も同様に隠れる。こちら単独では handshake ではなく nit だが、brief の「template 由来の release は保持」という宣言には反する（`brief:16`）。

2. **refuted / nit / scope内 — 通常の本文追記が消えるという攻撃は、plan の位置限定置換には成立しない。**
   `RELEASE=1`、`# release`、`trap 'echo release' EXIT`、`${MARKER}.release` を待つ `until` は、いずれも指定された7箇所の値の外にある。plan の広い検査では現行同様に赤になる（`plan:19,53–57`）。

   絶対 path の部分一致置換で `REPO=` や `$REPO` が消えるという具体的主張も成立しない。それらには絶対 path 文字列がない（`DC:870,905`）。`str(repo_root)` の全域置換なら dispatcher の root 部分は消えるが、`tools/pegasus/dispatch_compute.py` という suffix は残る（`DC:849,871`）。plan はそもそも全域置換を採らない。

   行全体を除外する方式は不採用を維持すべきである。`REPO=<値>; until ...release...` の待機部分まで消すため、規律2に直接抵触する。

3. **real / nit / scope内 — 「release 行＝handshake 行」は意味論として過大。**
   `RELEASE=1` 単独、`# release`、`trap 'echo release' EXIT` は、それだけでは親→job の待機を作らない。これらを狭い検査が受理することは受理集合の拡大だが、FA-4 に対する実害の証拠ではない（`FA-4-T188.md:1`）。親の説明は、この区別を省いている（`brief:23–25`）。

   今回は既存検出力を保持する保守的方針として広い検査を推奨する。ただし「handshake 構文を認識する」とは説明せず、**環境値を除いた本文の release 候補行を保守的に拒否する**と記すべきである（`plan:34`）。

4. **real / must-fix / scope内 — 狭い定義の反例は、複数行というだけでは成立しない。**
   提示された次の例は、代入行に `release` と `$MARKER` が同居するため、単純な同一行共起検査でも赤になる。

   ```bash
   RELEASE_FILE="$MARKER.release"
   until [[ -f "$RELEASE_FILE" ]]; do sleep 1; done
   ```

   本当に狭い定義を破る例は次である。

   ```bash
   gate="$MARKER"
   RELEASE_FILE="$gate.release"
   until [[ -f "$RELEASE_FILE" ]]; do sleep 1; done
   ```

   `$MARKER` 参照と `release` が別行になり、親が release file を作るまで待つ構成を見逃す。現行と広い定義は赤にする。狭い定義を退ける根拠・変異例には、この実害のある形を使うべきである（`plan:31,34`、`FA-4-T188.md:1`）。

5. **refuted / nit / scope内 — 現在の対象呼出しに対する環境値の列挙漏れはない。**
   対象は `repo_root`、result/probe/request/marker の4 path、dispatcher、job name の計7値で、plan はすべて列挙している（`DC:845–872`、`plan:40–46`）。`walltime` と request hash は本 test で固定されている（`test:2587–2588`）。

   インストール済み pytest のコードを読み、命名変換のみを Python で評価した。`_pytest/tmpdir.py:282–287` は node 名を置換後30文字に切り、連番付き directory を作る。現在名と `[repo-release-path]` 付きの名前は、どちらも：

   ```text
   basename: test_compute_marker_is_cross_n
   job name: izdw-test_compu
   ```

   となる。したがって**現在の test 名・追加予定 ID から `release` は残らない**。将来の改名で先頭30文字に含めれば directory 名に、先頭10文字に含めれば job 名にも残り得る。

   一方、`--basetemp`、`PYTEST_DEBUG_TEMPROOT`、temp root、ユーザー名由来の祖先 path には含まれ得る。根拠は `/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/tmpdir.py:154–166,213–215`。pytest・fixture 作成は実行していない。

6. **real / nit / scope内 — brief の「残りは定数」は対象 test 限定なら概ね正しいが、path 不在ではない。**
   `_INTERPRETER_CANDIDATES` は `python3.10`、`/usr/bin/python3.10`、`/bin/python3.10`。`release` はないが絶対 path はある（`DC:408–412,857,893`）。これは固定の production 内容なので除去対象へ広げてはならない。

   また一般の `_job_script` には可変の `walltime`、hash、task による unset 行の分岐がある（`DC:840–855,862,869,913`）。`brief:14` は「この test の固定引数下では」と限定するのが正確。plan は既に固定引数を明記している（`plan:59`）。

7. **refuted / nit / scope内 — 負例Bが他の既存 assert によって赤になる懸念は、指定の注入では成立しない。**
   `until [[ -f "${MARKER}.release" ]]; do sleep 1; done` を `mv` 直前へ加えても、marker 名は残り、元の `mv` は `selected=""` より前にあり、`while` は増えない（`DC:887–892`、`test:2590–2593`、`plan:124–130`）。baseline が通る同一環境なら、新 release 検査へ帰属できる。親は終了コードだけでなく、失敗した assertion と候補行を確認すること。

8. **real / nit / scope外 — 任意の repo path に対する test 全体の不変性は保証できない。裁定パッケージ候補。**
   `/repo/while-release` のような path では、release 正規化後も既存の `"while" not in script` が赤になる（`test:2593`）。したがって `brief:4,16` の保証は広すぎる。plan は release 検査だけの保証へ限定済み（`plan:76–80`）。`while` 検査の是正は今回実装せず、必要なら別裁定に回す。

## 検出力の比較表 (入力 × 現行 / 広い定義 / 狭い定義)

すべて静的期待。「広い定義」はplanの7値完全マスク、「狭い定義」は同じ正規化後の release・marker参照の同一行共起とする。

| 入力 | 現行 | 広い定義 | 狭い定義 |
|---|---|---|---|
| repo path だけに `release` | 赤 | 緑 | 緑 |
| 本文 `RELEASE=1` | 赤 | 赤 | 緑 |
| 本文 `# release` | 赤 | 赤 | 緑 |
| `trap 'echo release' EXIT` | 赤 | 赤 | 緑 |
| `until [[ -f "${MARKER}.release" ]]; do sleep 1; done` | 赤 | 赤 | 赤 |
| `RELEASE_FILE="$MARKER.release"` ＋待機 | 赤 | 赤 | 赤 |
| `gate="$MARKER"` → `RELEASE_FILE="$gate.release"` →待機 | 赤 | 赤 | 緑 |
| `REPO=<値>; until [[ -f "${MARKER}.release" ]]; do sleep 1; done` | 赤 | 赤 | 赤 |
| marker 定数を `compute.release` に変更＋ `$MARKER` 待機 | 赤 | **緑** | **緑** |

最後の行は正規化の過剰による後退であり、広い／狭い定義の選択だけでは防げない。

## 推奨する検査の形 (1 つ、通る正例 1 つと落ちる負例 1 つ)

**埋込み位置を限定し、環境由来の部分だけを token 化して、残った全 release 行の不在を検査する。**

plan の「改行＋代入名＋正確な quote 済み値」「各1回」「行末構文を残す」は維持する。ただし replacement には production 側の固定部分を残す。

| 対象 | 正規化後に残す内容 |
|---|---|
| `REPO` | `<REPO>` |
| `DISPATCHER` | `<REPO>/tools/pegasus/dispatch_compute.py` |
| `RESULT` / `PROBE` / `REQUEST` | `<SUBMISSION>/` と各固定 basename |
| `MARKER` | `<SUBMISSION>/` と **`DC._COMPUTE_MARKER_NAME`** |
| PBS job name | `izdw-<NONCE>` |

job name の検索値は、production の `_job_name` 全返り値を追従して隠すのではなく、既知形式 `izdw-` と fixture の nonce から組み立てる。形式変更に `release` が加われば、その行を残して検査する。これは置換処理の修正であり、追加 gate は不要。

最後はplanどおり：

```python
release_lines = [
    line for line in script_body.splitlines()
    if "release" in line.lower()
]
assert not release_lines, release_lines
```

- **通る正例:** repo root が `/__t2761__/repo release's checkout`、本文は現行のまま。
- **落ちる負例:** `mv` 直前へ `until [[ -f "${MARKER}.release" ]]; do sleep 1; done` を注入。

いずれも期待であり、未実測。

## 変異登録への修正案

既存の A・B・M0 は維持し、正規化境界を検証する以下を同じ変異 matrix に加える。恒久 test や gate の追加は不要。

- **B2：別名を経由する複数行待機。** 所見4の3行を注入し、release 検査で KILLED を期待する。
- **B3：代入行末の待機。** `REPO=<埋込み値>` の直後へ `; until [[ -f "${MARKER}.release" ]]; do sleep 1; done` を追加する。行全体除去への退行を検出する。
- **B4：定数と環境値の混同。** marker 定数を `compute.release` に変更し、`mv` 前へ `$MARKER` を待つ `until` を追加する。提案planでは取り逃し、推奨修正後は KILLED を期待する。実験内の変更に限定する。
- **正例の環境条件:** 親の実験で submission 側の祖先 path にも `release` を含め、7値正規化のうち repo 以外も確認する。
- **帰属条件:** B群は対象 node の release assertion と残存候補行を記録する。構文エラー・収集失敗・他 assertion の赤を成功として数えない。

M0 はplanどおり `release`・`while` を含まない comment に限定する。`# release` はshell動作上無害でも、現行の受理集合に対する等価変異ではない。

## 総括

**plan は正規化境界の修正が必要。** 本文の広い release 検査と位置限定置換は妥当だが、marker basename・job 名まで production の返り値ごと隠すと、現行が捕捉する違反を通し得る。環境由来部分だけを隠し、固定部分を残す形を推奨する。

親 brief は「release 行＝handshake」と「任意の path で test が不変」という説明を限定すべきである。ファイル変更・pytest・変異テストは実施しておらず、緑は未確認。
