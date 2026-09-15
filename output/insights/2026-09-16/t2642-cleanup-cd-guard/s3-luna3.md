## 所見

### 所見 1: 親の10アンカーは pin 閉包の全数ではない

- **主張**: 親 brief の表外に、独立した逐語依存が **7群**ある。「10アンカーを追従すれば閉じる」は成立しない。
- **根拠 (file:line)**:

| 表外の依存 | `orchestrator/tests/test_check_docs.py` の位置 | 破損時の結果 |
|---|---|---|
| `commit graph` が一意 | 9935、9941 | 一意性／1-byte変異 assert が落ちる |
| `## 4. 事後検査` | 9963、9979、9991 | 置換が不発となり、純増 assert または digest 違反期待が落ちる |
| §2見出し全文が一意 | 10232、10242 | `original.count(section_two)` が落ちる |
| checker呼出しから「停止。」までの部分逐語 | 10153、10186、10209、10232 | checker定数を更新しても、test自身の `count(contract)` は別途落ちうる |
| `正本は `＋コードスパンの住所＋` F26。` | 10262〜10403 | 意味等価な住所変更でも、変異不発・純増不足・一意性 assert で落ちうる |
| description行の全文 | 10356、10361 | frontmatter key を維持しても全文一致 assert が落ちる |
| digest定数の代入書式と現在値 | 10103、10109 | `_rebind_synthetic_cleanup_command_digest` の `checker.count(old)` が落ちる |

- **成果物への影響**: プランの副作用表は最初の6群を概ね補っているが、最後の **定数代入書式依存**は明記していない。値だけを既存書式で更新する今回案では破損を確認しなかった。親表を全数表として扱う記述は修正対象。
- **深刻度**: **nit**

### 所見 2: 実装担当の分割はあるが、commit の分割が未指定

- **主張**: 「3 fileを1本のauthorへ渡す」は、同じ commit に収める指定ではない。
- **根拠 (file:line)**: `s2-plan.md:158` は担当分割のみ。`s1-brief.md:63` は spool・必要時の failures 追記も成果物に含める。一方、`docs/skill-self-improvement.md:78` は command と変更理由になった failures／decisions／reference の整合を同じ commit で保つ契約。
- **成果物への影響**: command・checker・test を同一 commit に収め、今回理由側の正本も変更するなら同じ commit に含める、と確定する必要がある。既に記録済みで変更不要な failures を、形式だけのために再編集する必要はない。現段階では違反する commit が作られた証拠はない。
- **深刻度**: **nit**

## pin 閉包の検査結果

指定2ファイルで確認した、command内容に依存する検査は以下。

| 検査 | 根拠 |
|---|---|
| UTF-8 byte上限5900・各行110文字 | `tools/check_docs.py:285`、5977、5987 |
| frontmatterの開始／終了、解析可能性、key重複禁止、key集合 | 同5084、6087 |
| `$ARGUMENTS` が全文で1件 | 同771、6108 |
| 自己改善文書のpathが全文に存在 | 同6114 |
| frontmatterを除いた可視行で、境界付きF26とコードスパン住所が共起 | 同6054、6065 |
| 可視§3見出しが一意、その節内に exact 2行契約が存在 | 同6074、755 |
| command全文SHA-256 | 同6571 |
| checker定数＝期待digest＝synthetic全文の派生digest | `orchestrator/tests/test_check_docs.py:9829`、9835 |
| byte値2箇所、上限、超過生成、5901の値と診断 | 同9840 |
| digest変異／見出し変異／Markdown変異 | 同9935、9963、9979、9991、10007 |
| checker呼出し削除／rc削除／否定／節分散 | 同10153、10186、10209、10232 |
| 住所の分割／隣接ID／コードスパン除去／HTML／link定義／frontmatter移設／言い換え／baseline | 同10262、10278、10297、10316、10336、10356、10384、10406 |
| 変異時の派生digest再束縛とbyte中立化 | 同10103、10124 |

**commandの固定行番号・総行数を assert する pin は、指定2ファイルでは見つからなかった。** 行番号／数値／digest／値文字列でも検索した。行番号を計算するテストの中身も確認したが、例えば同4589・4605・4656は provenance文書が対象だった。今回の81→84行だけを理由に落ちる行番号assertは確認していない。

なお、commandの登録・存在・regular file・UTF-8の検査も `tools/check_docs.py:5850`、5961にある。これは文面pinに加わる入力条件である。

## byte 算術と test 追従

提案された挿入・置換を**メモリ上で再構成**し、UTF-8で独立計数した。

| 項目 | 独立検算値 |
|---|---:|
| 現在 | 5898 bytes／81行 |
| 削除 | 508 bytes |
| 追加 | 507 bytes |
| 改訂後 | **5897 bytes／84行** |
| 最長行 | **105文字** |
| 改訂後の予算余り | **3 bytes** |

現在・改訂後とも末尾LFあり、CRなし。プランの算術は一致する。110は `len(line)` による文字数であり、byteとの取り違えはなかった。ASCIIバッククォートは1 byteとして数えた。

改訂案のSHA-256:

```text
ae20f2331636fda1f48193e6d65faf8309880af9f2084e87fefc4875b18a83d1
```

個別追従の照合結果:

| 対象 | プランの手当て |
|---|---|
| `5_898`：9843・9848 | 両方を`5_897`へ更新 |
| `TextLimit(5_900, 110)`：9842 | 維持 |
| padding：9849 | `x * 2`→`x * 3` |
| `5_901`：9850 | 維持。5897＋LF1＋x3＝5901 |
| 超過message：9857 | 維持 |
| slack：10132〜10138 | 維持。改訂後も全文・§3内で各1件 |

slackは21文字のASCII文字列である。実装上は**全文での一意性**を要求する。§3編集で消す・複製する場合、byte中立化を使う変異テストが破損するが、今回案は触れていない。

現在のsyntheticと実commandは完全一致した。更新漏れの場合:

- checker／期待digestだけ更新すると、syntheticの派生digest assert（9835）が落ちる。
- syntheticだけ更新すると、同assertと未更新のbyte assert（9843）が落ちる。
- checkerだけ更新してsyntheticを残すと、`_build_min_repo`（897・923）が旧commandを生成し、baseline成功期待（10406など）もdigest不一致で落ちる。
- **実commandだけ更新し、checkerとfixtureを両方残した場合、fixture中心のテストだけでは実fileとの差を直接検出できない。** 実repoのchecker実走（6571）が必要。プランはその実走を要求している。

## 恒真化・SKILL・親実測への攻撃

**恒真化:** 今回案はcheckerの判定分岐を増やさない。新しい進入禁止行を削除すれば未更新SHAに対して赤になるが、SHAも再束縛すれば、既存の構造検査はその欠落を拒否しない。新規文面を独立した機械防壁とは数えられない。

一方、既存検査全体が恒真という主張も成立しない。digestを再束縛しても、次は赤になる。

- rc規則を削除する：10186。
- 呼出しを否定文へ置換する：10209。
- F26と住所を別行へ分ける：10262。

住所検査は共起、占有契約は**節内のexact文字列包含**であり、両者は異なる。意味保証が対象外であることは `docs/skill-self-improvement.md:82` と整合する。機械保証の追加を求める場合は裁定パッケージ候補となる。

**SKILL digest:** commandだけ変更した場合、`CODEX_CLEANUP_BRANCHES_SKILL_SHA256` の更新経路はない。`tools/check_docs.py:5183`・5219はSKILL自身の文字列だけをhashし、commandは6571で別にhashする。commandを取り込んだ合成digestではない。

**74 worktree・重複0件:** briefには件数と結論があるが、再現コマンド・比較基準・失敗時の扱いがないため、その数値を再現可能な証拠とは扱えない。妥当な再現には、全worktreeの列挙、各処理の成功確認、staged／unstaged／untracked、各branchの共通基点以降の変更pathを含める必要がある。mainとの単純なtip差分にはmain側の前進が混ざる。`ps` の不在も観測時点の範囲に限られ、以後の重複不在は保証しない。

## 総括

(a) **must-fix：0件。nit：2件。** 静的検査のみで、pytest・受入の緑は主張しない。  
(b) **親のpin閉包に漏れあり：独立依存7群。pathは `orchestrator/tests/test_check_docs.py`。**  
(c) **改訂後byteの独立検算値：5897 bytes、84行、最長105文字、末尾LFあり。**