## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・根拠 file:line)

以下、`brief`／`plan` は指定された `s1-brief-v2.md`／`s2-plan-v2.md`、`DC` は `tools/pegasus/dispatch_compute.py`、`MH` は `tools/mutation_harness.py`、`test` は `orchestrator/tests/test_pegasus_dispatch_compute.py` を指す。判定は静的確認に限る。

1. **refuted / nit / scope内 — dispatch blob 検査によって production 変異が一律停止する、という懸念。**
   `_runner_identity` の呼出しは注入前の `MH:3122`。dispatch の HEAD blob 比較は `MH:817–828` にあり、変異ループはその後の `MH:3262–3277`。変異ごとの再比較ではない。再起動・resume 時には再び検査されるが、正常な注入・復元の各走を阻止する構造ではない。

2. **real / must-fix / scope内 — B/B2/AB の「即抜け」は無条件ではなく、runner に新しい hang 経路を作る。**
   `plan:269` は書込み成功を前提としている。実物は `set -u` のみで、`printf` の失敗による終了も成功確認もない（`DC:864,887–890`）。一時 marker の作成に失敗し、release file もなければ、注入した `until` は永続待機する。元の script にはこの待機がない。したがって `brief:63–64` の「本物の待機を注入しない」を満たし切れていない。
   **変異だけの修正**として、B/B2 の条件に `|| -n "$MARKER"` を追加すれば、非空 path の代入後なので FS 成否によらず即抜けする。AB にも同じ B を使う。恒久 production 変更は不要。

3. **refuted / nit / scope内 — 正常経路の shell 構文・変数順・marker／会計／stdout 収集を壊す懸念。**
   B/B2 の挿入位置は `printf` の完了直後、`marker_tmp` の定義後。B2 の `gate`、`RELEASE_FILE` も参照前に定義される。B3 は `MARKER` 代入後に同じ行で検査する（`DC:872,887–890`、`plan:235–264`）。B3 の非空条件は成立する。
   M0/B/B2/B3 の anchor は各一箇所で、置換後ソースの AST parse も成立した。f-string の二重 brace は正しい。marker の名前・JSON 内容・publish、job name、request binding は変更されないため、正常経路で収集が壊れる静的根拠はない（`DC:828–831,887–890,1719–1733,1955–1966,2027–2028`）。ただし所見2の失敗経路は別である。

4. **real / must-fix / scope内 — A の `{R}` を保証する実行環境の確認手順が不足。**
   `plan:112` と `brief:69` は basetemp に `release` がないことを条件としているが、確認方法を登録していない。指定 container path の文字列には `release` がない。一方、test の `_REPO` は `resolve()` 後の path（`test:24`）であり、表記だけの確認では不十分。
   `run_tests.py` は pytest コマンドへ basetemp を自動追加していない（`tools/run_tests.py:550–572`）。したがって `/tmp/pytest-of-tanab/` と断定できず、環境・pytest 設定・worker 側の実効 path を確認する必要がある。新検査の無変異 baseline が緑でも、正規化が効くためこの条件の証明にはならない。
   親は実効 repo path と compute 側 basetemp を記録するか、走行専用の `--basetemp` を明示して固定すること。`while` 等の既存検査に当たる語も含めない。

5. **real / must-fix / scope内 — A/AB を DW-M08 の新旧 HEAD 両走と同一視する説明は成立しない。**
   `git show 38353207f:...` の `2592–2593` と A の復元 bytes は一致した。しかし A は新しい parametrize と引数変更を残し、変更前 HEAD のテストそのものではない（`plan:218`、`brief:78`）。`docs/dev-wave/mutation.md:63–64` の文言どおりの両走を実施したとは報告できない。
   さらに B と AB はともに拒否を期待しており、「新テストだけが検出する差分」を示すものではない。本件は偽赤の除去と既存拒否能力の維持なので、その契約の適用整理が必要。追加走・代替承認は裁定候補へ分離する。

6. **real / must-fix / scope内 — AB の R は handshake 検出の単独証拠にならない。**
   A だけで R は repo path により赤になる。AB の R は B がなくても赤であり、`{C,R}` 全体を「旧検査でも handshake を捕る」証拠として扱うのは過剰（`brief:69–71`、`plan:218`）。DW-M01/M03 は単一理由性を要求する（`docs/dev-wave/mutation.md:7–9,18–20`）。
   AB の期待集合は変更不要。ただし **C が handshake 検出証拠、R は環境 path による冗長な赤で単独証拠から除外**と明記する。

7. **refuted / nit / scope内 — anchor／schema／nodeid の不適合。**
   production の各 old は現物で出現数1。`${{MARKER}}`、`${{PBS_JOBID:-unknown}}`、`write_failure() {{` はソース置換として正しい。A の実装後一意性確認も `plan:271` に明記されている。C/R の完全 nodeid と parametrize id は `plan:99–100` にある。
   最終 JSON では `replacements` の各要素を相対 `file` と逐語 `old`／`new` の3 key にする（`MH:497–505,619–634`）。`expected_nodes` は集合表記や略号ではなく文字列配列にする（`MH:600–612`）。現 plan は登録素材であり、完成 JSON の適合性まで確認済みとは言えない。

8. **refuted / nit / scope内 — B4 の process 内定数差替えが効かない懸念。**
   `_job_script` は呼出し時に module global `_COMPUTE_MARKER_NAME` を読む（`DC:846`）。test の `DC` は同モジュール（`test:28`）。したがって `patch.object(ns["DC"], ...)` は生成と正規化の双方に効く。新ブロックは固定 marker 名を残すため、`plan:289` の行リスト検査は狙った拒否理由を確認できる。直接呼出しでは pytest の parametrize 展開は不要。実装後の probe 自体は未実行。

9. **refuted / nit / scope内 — plan の file:line・関数名・定数名の誤り。**
   `plan:7–13` の変更位置、`:116` 以降の production anchor 範囲、`:300` の他の呼出し位置10箇所を現物と照合し、一致を確認した。`test:2580` は複数行 signature の引数行であり、誤参照ではない。他の呼出しは transport／request envelope 等の検査で、今回の注入により追加失敗する明白な条件は見つからなかった。ただし完全集合は親の probe で確定する。

10. **real / nit / scope外 — `while` による同型偽赤は残る。裁定パッケージ候補。**
    `test:2593` は未正規化の script 全体を検査するため、repo path に `while` が入れば引き続き赤になる。`plan:92` は正しく除外している。
    指定の `not in script`／`not in .*lower()` と release の不在検査を検索し、今回以外に script/path へ同じ release 語不在を掛ける検査は見つからなかった。したがって着地後に撤去できるのは **release 専用の命名防壁**であり、「環境 path による偽赤を全面解消」とは書けない。

## 変異 matrix の実行可能性表 (変異 × runner 経路への影響 × 期待 node)

C/R は `plan:99–100` の完全 nodeid。すべて未実測の期待値。

| 変異 | runner 経路への影響 | 期待 node |
|---|---|---|
| M0 | comment のみ。収集契約を維持 | SURVIVED、`[]` |
| A | runner 無変更。実効 repo/basetemp 条件の固定が必要 | KILLED、`[R]` |
| B | 正常書込み時は即抜け。書込み失敗時に hang 経路あり、修正必須 | KILLED、`[C,R]` |
| AB | B と同じ。R は環境由来でも赤になる | KILLED、`[C,R]`。handshake の帰属証拠は C |
| B2 | B と同じ。alias 定義順は正しい | KILLED、`[C,R]` |
| B3 | 非空 MARKER により即抜け。行末構文は正規化後にも残る | KILLED、`[C,R]` |
| B4 | dispatch なし。module global 差替えは有効 | node 集合ではなく指定の AssertionError 内容 |
| 旧 HEAD 上の B〔追加候補〕 | 修正版 B を別 container／別 spec で実施 | parametrize なしの旧対象 node 1件 |

## 変異登録への修正案

1. B/B2/AB の待機条件へ `|| -n "$MARKER"` を追加し、FS 書込み失敗時にも待機しない変異にする。変更後の逐語 anchor・AST・shell 構文を再確認する。
2. A の環境条件を走行手順として具体化する。解決後の container path と compute 側の実効 basetemp を記録し、必要なら走行専用 basetemp を明示する。恒久 test gate は追加しない。
3. AB の R を冗長な赤として明記し、handshake 検出の単独証拠に数えない。
4. 最終 spec は schema の全必須 key を満たし、完全 nodeid を配列で登録する。probe は DW-M07 に従い全件 SURVIVED／空配列として観測を残し、本走の期待集合を再登録する。
5. 「A/AB で DW-M08 実現済み」の断定を削除し、次節の裁定結果を登録する。rc=16・timeout・収集失敗を KILLED に数えない方針は維持する。

## 裁定パッケージ候補

- **新旧両走の扱い。** 推奨は、変更前 `38353207f` の release を含まない別 container に修正版 B を当て、別 spec で旧 node の拒否を確認すること。ただし、この追加走も「新テストだけが検出する差分」は示さない。本件を偽赤是正として、①新 baseline の R 受理、②A の R 拒否、③新旧 B の handshake 拒否を比較証拠とする整理を裁定する。契約の一般改訂は本題の実装 scope 外。
- **`while` 偽赤。** 別タスク候補。本 wave では変更せず、release 専用防壁の撤去と区別して残課題を記録する。

## 総括

plan v2 の正規化・anchor・B4 は静的には整合する。ただし、**B/B2/AB の失敗時 hang、A の環境条件、AB の赤理由の帰属、新旧両走の扱い**は登録前に修正・整理が必要。

ファイル変更、pytest、対象 test の直接呼出し、dispatch は実行していない。確認できたのは静的整合性であり、テストの緑ではない。
