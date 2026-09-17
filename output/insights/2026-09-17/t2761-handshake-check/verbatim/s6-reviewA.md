## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・成果物影響・根拠 file:line)

以下、`TEST` は `orchestrator/tests/test_pegasus_dispatch_compute.py`、`PROD` は `tools/pegasus/dispatch_compute.py` を指す。

1. **real / must-fix / scope 内 — P5 が引用された path 内の文字列を代入行と重複計数する。**

   **成果物影響:** handshake のない正常な production でも、改行を含む `--basetemp` によって旧検査では受理した入力が新検査で偽赤になる。

   根拠: `TEST:2628`、`PROD:866`、`PROD:870`。

   現在の `_REPO` を `R` として、次の環境入力を構成できる。ここで `\n` は実際の改行である。

   ```python
   basetemp = "/tmp/t2761\nREPO=" + str(R) + "\nbase"
   tmp_path = Path(basetemp) / "test_compute_marker_is_cross_n0"
   ```

   `R` は現在の空白・引用符のない絶対パスなので、REPO needle は `"\nREPO=" + str(R)`。一方、submission path は改行を含むため `shlex.quote()` が全体を引用するが、内部の改行と `REPO=...` はそのまま残る。

   その結果、同じ needle が RESULT・PROBE・REQUEST・MARKER の**引用値内部**と、本来の REPO 代入に現れる。出現数は **5**。`TEST:2628` は元の `script` を数えるため、それ以前の正規化で RESULT 等を置換済みでも救われない。

   静的な文字列構成で、MARKER 行を除く段階でも出現数 **4**、その代入ブロックに `release`・`while` がないことを確認した。pytest・production 関数は実行していない。

   **修正方向:** 引用値内部を除外して実際の代入位置を特定する必要がある。単に重複検査を削除する、または最初の一致を採用する修正では、位置限定の保証を失う。裁定 P5 自体の修正が必要。

2. **refuted / nit / scope 内 — 終端集合の不足による検出力後退。**

   根拠: `TEST:2629`、`TEST:2630`、`TEST:2634`。

   値直後の `)`・バッククォート・`>` は許容集合外なので P5 が拒否する。`rele` に `ase` を連結する反例も同様。許容される空白・改行・`;`・`&`・`|` が介在する場合、その境界をまたいで連続文字列 `release` は成立しない。後続の完全な `release` は置換されず残る。

3. **refuted / nit / scope 内 — 固定部分や行末 handshake を正規化が消す。**

   根拠: `TEST:2600`、`TEST:2616`、`TEST:2620`、`TEST:2631`。

   固定 basename・dispatcher suffix・marker 定数は保持される。固定 basename や suffix の production 側だけの変更は needle 不一致で拒否され、marker 定数の `release` は replacement に残る。行末の `; until ...release...`、別行の alias 形も残る。

   needle 同士の包含について、現行の完全な引用表現と固定 suffix から検出力後退は構成できなかった。ただし、引用値内部の別 needle との衝突は所見 1 の偽赤として成立する。

4. **refuted / nit / scope 内 — 合成 path の実在要求、node pin 衝突、差分の逸脱。**

   根拠: `TEST:2580`、`PROD:845`、`PROD:848`、`PROD:858`、`s5-author-snapshot.patch:5`。

   `_job_script` はこの経路で Path の結合と文字列化だけを行い、合成 repo に対する `resolve()`・実在確認・ファイルアクセスはない。稼働コード・設定の検索では対象 node の pin／allowlist は見つからず、旧 node の duration ledger 登録は残っている。

   snapshot と現物の `git diff` は byte 一致。追跡差分は対象 test ファイルのみで、追加 import は `shlex` だけ。他 test・helper・production の変更はない。

5. **refuted / nit / scope 内 — 規律 2 に反する「検査を甘くして通す」経路。**

   根拠: `TEST:2596`、`TEST:2628`、`TEST:2635`。

   攻撃した境界・固定部分・同一行／別行 handshake について、旧が拒否する template 由来の `release` を新が受理する具体例は構成できなかった。環境値の `release` に対する受理拡大は依頼どおりである。

   ただし、これは所見 1 の偽赤を許容する理由にはならない。

6. **real / nit / scope 外 — `while` の環境依存偽赤は残る。裁定パッケージ候補。**

   根拠: `TEST:2636`、`s4-adjudication.md:73`。

   path に `while` が含まれると元の script に対する検査が拒否する。既知の裁定どおり本実装の修正対象外。

## 裁定との一致表 (P1〜P5 × 現物)

| 項目 | 現物 | 判定 |
|---|---|---|
| P1 | `TEST:2632` の説明と、大小無視の候補行列挙・空要求 | 一致 |
| P2 | `TEST:2598` の6組。値だけ各1回置換。job name は置換しない | 一致 |
| P3 | `TEST:2580` の2値・2 ID、`(tmp_path, repo_root)` | 一致 |
| P4 | 先頭2 assert は `TEST:2596`、`while` は検査末尾の `TEST:2636`。文言・相対位置を維持 | 一致 |
| P5 | 元の script に対する count、index、終端集合、診断文、置換順序 | 一致。ただし裁定自体に所見1の欠陥 |

P2 の6組は以下のとおり。`Q(x) = shlex.quote(str(x))`、`M = DC._COMPUTE_MARKER_NAME` とする。裁定の指定と needle／replacement の生成表現が一致する。

| needle | replacement |
|---|---|
| `"\nRESULT=" + Q(tmp_path / "result.json")` | `"\nRESULT=<SUBMISSION>/result.json"` |
| `"\nPROBE=" + Q(tmp_path / "interpreter_probe.py")` | `"\nPROBE=<SUBMISSION>/interpreter_probe.py"` |
| `"\nREQUEST=" + Q(tmp_path / "request.json")` | `"\nREQUEST=<SUBMISSION>/request.json"` |
| `"\nREPO=" + Q(repo_root)` | `"\nREPO=<REPO>"` |
| `"\nDISPATCHER=" + Q(repo_root / "tools" / "pegasus" / "dispatch_compute.py")` | `"\nDISPATCHER=<REPO>/tools/pegasus/dispatch_compute.py"` |
| `"\nMARKER=" + Q(tmp_path / M)` | `"\nMARKER=<SUBMISSION>/" + M` |

変異用 anchor も静的に確認した。`a-old-check` の新ブロック、M0/B/AB/B2 共通 production anchor、B3 anchor はそれぞれ出現数1。

## 検出力の比較 (旧 / 新、構成した入力)

以下は静的判定。親のログにある実測とは区別する。

| 入力・変更 | 旧 | 新 | 理由 |
|---|---|---|---|
| 合成 repo `"/__t2761__/repo release's checkout"`、通常本文 | 拒否 | 受理 | 意図した path 偽赤是正 |
| `REPO=/__t2761__/rele` の直後に `ase` | 拒否 | 拒否 | P5 が非終端として拒否 |
| 完全な値直後に `)`・バッククォート・`>`、後続に release | 拒否 | 拒否 | 許容終端集合外 |
| MARKER 代入末尾に `; until [[ -f "${MARKER}.release" ... ]]` | 拒否 | 拒否 | 行末構文が残る |
| `gate="$MARKER"`、`RELEASE_FILE="$gate.release"` の alias 形 | 拒否 | 拒否 | 別行の release が残る |
| marker 定数を `compute-visible.release` に変更 | 拒否 | 拒否 | replacement が定数を保持 |
| 所見1の改行入り basetemp、通常本文 | 受理 | **拒否** | 引用値内部を重複計数する新しい偽赤 |

P5 は、代入の欠落・重複、引用方式の変更、行頭への空白追加、値の変更、許容集合外の文字の直結も拒否する。これらは受理集合を狭める方向だが、**厳しくなることと偽赤でないことは別**であり、所見1がその反例である。

`;`・`&`・`|` や通常の改行を含むだけなら、production と検査が同じ完全引用表現を生成するため不一致にはならない。問題は改行後に別 needle が成立する場合。空文字も `Path("")` は `"."` となり、今回の Path 入力から `shlex.quote("")` には到達しない。末尾 `/` の除去や `..` についても両側が同じ Path 表現を使うため、それだけでは不一致にならない。

## 総括

**must-fix 1件。現状の承認は不可。** 実装は裁定 v2.1 に忠実だが、P5 が引用された環境値内部まで数えるため、改行入り basetemp で新しい偽赤が生じる。裁定と実装の双方で正規化位置の識別を修正する必要がある。

template 由来の release に対する検出力後退は、今回の攻撃範囲では **refuted**。pytest は実行していない。親の焦点走2件成功・B4/B5拒否ログは確認したが、所見1を検証する入力は含まれていない。