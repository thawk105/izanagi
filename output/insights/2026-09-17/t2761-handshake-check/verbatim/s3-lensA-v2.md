## 所見一覧 (番号・real/refuted・must-fix/nit・scope 内/外・根拠 file:line)

以下の「受理／拒否」は静的な述語評価の予測であり、pytest の結果ではない。指定資料はすべて読取済み。ファイル変更・pytest・対象 test の直接呼出しは行っていない。

1. **real / must-fix / scope 内 — P2 は完全な値ではなく、その接頭辞にも一致する。規律 2 の穴が残る。**

   `repo_root = Path("/__t2761__/rele")` とし、production の REPO 行を次へ変える反例を構成できる。

   ```python
   REPO={shlex.quote(str(repo_root))}ase
   ```

   生成行は `REPO=/__t2761__/release`。旧検査は拒否するが、新検査では `REPO=<REPO>ase` となり受理する。6 needle の出現数はすべて 1 のままで、P5 は防げない。他の production 行を維持すれば既存 3 assert にも影響しない。

   これは **環境値と template 追加分の境界をまたぐ `release`** の反例である。固定文字列 `release` 全体を消す反例でも、実際の handshake 待機を見逃す実証でもない。しかし、追加された `ase` により初めて旧検査が拒否する入力になり、正規化がそれを受理する。「完全表現」「template 由来の検出力維持」という無条件の主張には反する。現在の C/R だけではこの境界を覆わない。

   Python の文字列評価で、出現数 `[1, 1, 1, 1, 1, 1]`、旧述語は拒否、新 release 述語は受理となることを確認した。

   根拠: [s1-brief-v2.md:38](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief-v2.md:38)、[s2-plan-v2.md:28](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:28)、[s2-plan-v2.md:172](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:172)、[dispatch_compute.py:870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py:870)。

2. **refuted / nit / scope 内 — 指定された固定 basename・suffix・marker 定数の改名は隠れない。**

   - `result.json` → `release.json`：RESULT needle が一致せず、P5 が拒否する。
   - dispatcher suffix に `release` を挿入：DISPATCHER needle が一致せず、P5 が拒否する。
   - 既存 suffix の後ろへ `.release` を追加：接頭辞置換されても `.release` が残り、release 検査が拒否する。
   - `_COMPUTE_MARKER_NAME` → `compute-visible.release`：検索側も追従するが、置換側にも同じ定数が残るため release 検査が拒否する。
   - `RESULT` 等の代入名を改名：検索が外れ、P5 が拒否する。

   したがって、この設計が production 定数を無条件に隠すという攻撃は成立しない。

   根拠: [s2-plan-v2.md:21](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:21)、[dispatch_compute.py:845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py:845)。

3. **refuted / nit / scope 内 — 指定された引用符・行末構文・別行の過剰除去は起きない。**

   Python 式で次を確認した。

   ```text
   shlex.quote(str(Path("/__t2761__/repo release's checkout")))
   → '/__t2761__/repo release'"'"'s checkout'
   ```

   production の f-string で生成した REPO 行と検索式は UTF-8 bytes で一致する。値直後の `; until …` と別行の `until …` は置換対象外であり、付加した文字列がそのまま残ることも確認した。

   ただし、これは所見 1 の「同じ shell word に続く文字列」の境界確認を代替しない。

   根拠: [s2-plan-v2.md:24](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:24)、[s2-plan-v2.md:262](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:262)、[dispatch_compute.py:870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py:870)。

4. **refuted / nit / scope 内 — P5 自体を独立した「追加 gate」とする攻撃は採らない。ただし説明は不正確。**

   P5 は、この検査置換で環境値を除去してよいことを確認する内部前提であり、別目的の gate ではない、と判断する。

   一方、「production の受理集合にも触れない」は、**test が受理する production の集合**という意味では誤り。release を含まない代入名改名、同一代入の重複、引用形式変更、行頭への空白追加、固定 basename 変更でも、新たに P5 が拒否し得る。これは検査を厳しくする方向であり、規律 2 の緩和ではない。

   「正規化の前提が崩れた入力を保守的に拒否する。同一検査内の前提確認」と説明し直すべきである。

   根拠: [s1-brief-v2.md:55](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief-v2.md:55)、[s2-plan-v2.md:38](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:38)。

5. **real / must-fix / scope 内 — 「B2 は狭い定義なら生存」は定義不足で成立しない。**

   狭い検査が marker 参照を文字列 `$MARKER` 等に限定するなら、brief の alias 3 行は同一行共起を避ける。しかし、`RELEASE_FILE` を marker 由来の参照として数えるなら、最後の行に `RELEASE` と marker 参照が共存し、拒否される。B2 の即抜け版では `$marker_tmp` も同じ行に存在するため、それを marker 参照に含める検査にも拒否される。

   従って、B2 は広い述語が alias 例を拒否する証拠にはなるが、狭い述語との差を無条件に証明しない。広い定義の採用理由には「環境部分以外の旧 release 検出力を維持する」を用いるべきである。

   根拠: [s1-brief-v2.md:45](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief-v2.md:45)、[s1-brief-v2.md:72](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief-v2.md:72)、[s2-plan-v2.md:237](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:237)。

6. **real / must-fix / scope 内 — B/B2 の即抜けは正常なファイル生成に依存し、無条件ではない。**

   `_job_script` は 864 行で `set -u`、872 行で `MARKER`、887 行で `marker_tmp` を定義する。B/B2 の注入位置では両変数が定義済みであり、B2 の `gate`、`RELEASE_FILE` も順番に定義される。未定義変数による問題はない。

   しかし、888–889 行のリダイレクトが権限・親ディレクトリ消失等で失敗し、一時ファイルが存在しなければ、`set -u` だけでは処理は止まらない。左側の release ファイルもなければ、`||` の右側も偽になり待機する。生成後の削除競合や、通常ファイルでない対象でも同様である。

   `printf` 失敗のすべてが待機を起こすわけではない。通常ファイルが作られた後の書込み失敗なら、空ファイルでも `-f` は真になり得る。

   B3 は代入直後の非空 `MARKER` を使うので、このファイル実在依存がない。B/B2 も非空変数による条件へ揃えられる。

   根拠: [dispatch_compute.py:864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py:864)、[dispatch_compute.py:887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/tools/pegasus/dispatch_compute.py:887)、[s2-plan-v2.md:269](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:269)。

7. **real / nit / scope 内 — 即抜け変異が実証するのは静的な候補行検出であり、待機動作の検出ではない。**

   非空変数の OR 条件を付けると、親からの release がなくても進む。FA-4 が避ける「親死亡で job が待つ」動作そのものは作られない。

   静的検査の変異としては有効であり、この理由だけで変異を無効とする必要はない。ただし「実行時挙動は無関係」は対象 test 内に限った説明である。変異 production を runner 自身が実行する経路では、所見 6 のとおり実行時挙動が重要になる。

   根拠: [FA-4-T188.md:1](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/verbatim/FA-4-T188.md:1)、[s1-brief-v2.md:63](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief-v2.md:63)、[s2-plan-v2.md:205](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:205)。

8. **refuted / nit / scope 内 — 対象 node 内で、既存 3 assert が B/B2/B3 を先に拒否する構成ではない。**

   marker 定数と元の `mv "$marker_tmp" "$MARKER"` は残り、`selected=""` との順序も変わらない。注入語は `until` で、`while` は追加しない。B3 も MARKER needle を一つ残す。通常の正規化前提下では、最初の失敗箇所は release 候補行の assert になる。

   ただし、**node 集合だけでは失敗理由を証明できない**。親の実測では B/B2/B3 の traceback と候補行診断も保存すべきである。

   根拠: [test_pegasus_dispatch_compute.py:2590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2761-handshake-check/orchestrator/tests/test_pegasus_dispatch_compute.py:2590)、[s2-plan-v2.md:171](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:171)、[s2-plan-v2.md:262](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:262)。

9. **real / nit / scope 内 — A の `{R}` は環境条件付きの予測であり、まだ完全集合の証拠ではない。**

   記載された container path に `release` はない。しかし、それだけでは計算ノードで実際に用いられる `_REPO`、basetemp、ユーザー名を含む tmp_path を確定できない。比較は大小無視であり、`Release` も除外条件に含む。既存 `while` 検査による環境由来の失敗もないことが必要になる。

   また runner は file 全体を指定している。対象 C/R の静的推論だけから、file 全体の失敗 node 完全集合は確定できない。plan が要求する probe と本走の確認が必要である。

   根拠: [s1-brief-v2.md:60](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s1-brief-v2.md:60)、[s2-plan-v2.md:112](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:112)、[s2-plan-v2.md:273](/home/SFC/tanab/.claude/jobs/1031d339/tmp/wave/s2-plan-v2.md:273)。

## 検出力の比較表 (入力 × 現行 / plan v2)

すべて静的予測。既存 assert に影響する別要因がないことを前提とする。

| 入力 | 現行 | plan v2 |
|---|---|---|
| 現 template、path に release なし | 受理 | 受理 |
| 合成 repo path `repo release's checkout` | 拒否 | 受理：意図された変更 |
| submission 親 path に release | 拒否 | 受理：通常の tmp_path 名を前提 |
| RESULT basename を `release.json` に変更 | 拒否 | 拒否：P5 |
| dispatcher suffix に release を挿入 | 拒否 | 拒否：P5 または残存文字列 |
| marker 定数を `compute-visible.release` に変更 | 拒否 | 拒否：release 候補行 |
| release なしの代入名改名 | 受理 | 拒否：P5 |
| B / B2 / B3 | 拒否 | 拒否：release 候補行 |
| `RELEASE=1`、release を含む comment | 拒否 | 拒否：広い定義 |
| repo `/__t2761__/rele`、REPO template に `ase` を直結 | 拒否 | **受理：境界の後退** |

## 推奨する修正 (あれば。通る正例 1 つと落ちる負例 1 つ)

正規化対象を「needle が一致する接頭辞」から「環境値だけで完結した shell word」へ限定する。現在必要な改行・空白・`;` 等の終端を確認し、終端文字自体と後続構文は残す。想定外の連結は正規化せず、元の release 検査対象に残す。別目的の gate や汎用 shell parser は不要である。

- **通る正例:** 合成 repo path をそのまま代入した現 template。引用符を含む値だけを除き、release 候補行がなくなる。
- **落ちる負例:** repo `/__t2761__/rele` に対する `REPO={shlex.quote(str(repo_root))}ase`。完全な環境値ではないため除去せず、生成された `release` を拒否する。

B/B2 の即抜け条件は、ファイル実在に依存する `-f "$marker_tmp"` から、定義済み非空変数の `-n "$MARKER"` 等へ変更する。注入された release 条件は残る。

brief の「B2 は狭い定義なら生存」は削除するか、比較対象となる狭い述語を具体的に定義する。P5 の説明も所見 4 に合わせて修正する。

## 変異登録への修正案

- **境界反例を補助 probe に登録する。** 所見 1 の環境値と template 連結を用い、修正後に拒否されることを確認する。runner の cwd を壊し得るため、production dispatch 変異にはしない。
- **B/B2 の即抜け条件を非空変数へ変更する。** 期待 node 集合は維持し、「release 待機候補行の静的検出」という証拠の範囲を明記する。
- **B/B2/B3 の失敗理由を記録する。** node 集合に加え、release 候補行 assert と注入行の診断を確認する。P5・収集失敗・timeout を代替証拠にしない。
- **A の環境前提を実測記録する。** 計算ノード上の実効 `_REPO`、tmp_path／basetemp に大小無視の `release` がなく、既存 `while` 検査にも干渉しないことを確認する。
- **B4 は維持する。** 定数改名が P5 ではなく、正規化後の release 候補行によって拒否されるという診断まで確認する設計は適切である。

## 総括

plan v2 は固定名・marker 定数・通常の行末 handshake を残す点では成立する。ただし、**値の末尾境界を確認しない正規化には、旧拒否を新受理へ変える具体的な反例がある**。規律 2 に対する must-fix とする。

併せて、B/B2 のファイル依存の即抜けと、B2 が狭い検査を通過するという断定を修正すべきである。検証は静的評価のみであり、テストの緑・変異の KILLED は未確認である。