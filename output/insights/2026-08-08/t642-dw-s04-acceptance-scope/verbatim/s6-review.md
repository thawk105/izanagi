結論は **NO-GO**。段 5・6 skip の規範と byte 予算は保たれていますが、受入全走の否定側と適用経路に、受理集合を変え得る穴が残っています。

静的に `git diff`、性質検索、`wc -c` を実施しました。pytest、`tools/run_tests.py`、`tools/check_docs.py`、受入全走は実行しておらず、「緑」とは判定しません。

## 所見の対応表

| ID | 判定 | 現物根拠 | 成果物への影響 |
|---|---|---|---|
| A1 自己認証と宣言だけの実走 | `partial` | 「実走し、結果を書く」は [core.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:80) で閉じた。しかしテスト有無の判定証拠・不存在記録はなく、段4自身も残存を認める [s4-adjudication.md:51](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:51)。 | 親の「該当テストなし」だけで未全走 tip が land 受理集合へ入り、台帳・成果物索引・certified レポートの参照が壊れ得る。 |
| A2 ゼロ差分条件消失・matrix 免除漏出 | `closed` | [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:79) が「実装しない」経路かつ実装差分ゼロに直接束縛。通常経路の matrix は [入口:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:51) に残る。 | 実装差分あり wave の受理集合から matrix 証拠は落ちず、certified 選択と変異台帳の kill 参照は変わらない。 |
| A3 skip 後の受入実行点・期限なし | `closed` | [core.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:80) が段7記録前を期限化し、全走の所有者は [入口:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:35) で親。 | テスト存在を正しく判定した場合、受入 receipt のない tip は記録・報告の受理集合へ入らない。 |
| A4 byte 予算による安全義務削除 | `closed` | 改訂後も条件・実走・結果記録が [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:79) に残り、実測は正味 −1 byte。上限は [check_docs.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:254)。 | 予算を理由に matrix・受入の省略集合を拡大しておらず、成果物の値・参照は変わらない。 |
| A5 正例だけで negative control 不在 | `scope 外`（未解消） | 現文は正側だけ [core.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:80)。段4は gate 新設を scope 外へ送った [s4-adjudication.md:31](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:31)。 | 将来の誤った不存在判定により、未検査 tip が同じ契約名で land され、台帳・レポートの受理集合が変わる。 |
| A6 P4 の早すぎる docs-only 確定 | `closed` | 機械 gate を採らず、現差分は `core.md` のみ。docs-only 親編集は [入口:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:34) で許可される。 | 親所有の未監査コード hunk は生じず、certified 選択・台帳の受理集合は変わらない。 |
| A7 brief scope と記録成果物の矛盾 | `closed` | 旧 brief の衝突は [s1-brief.md:5](/work/1/SFC/tanab/dev-wave-jobs/t642/s1-brief.md:5) と [s1-brief.md:46](/work/1/SFC/tanab/dev-wave-jobs/t642/s1-brief.md:46)。後段の裁定が規範編集と記録成果物を分離した [s4-adjudication.md:33](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:33)。 | scope 違反と記録欠落の二択は解消され、台帳 fragment・レポート参照を正規受理集合へ含められる。 |
| B1 実走せず約束だけ書ける | `closed` | [core.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:80) は「実走し、結果を書く」と完了形を要求。 | 条件成立時に予定だけの worklog で受理する経路は消え、未検査 tip は受理集合へ入らない。 |
| B2 旧 D72 系との参照分岐 | `partial` | 新 living norm と裁定は [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:79)、[worklog.md:3179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/worklog.md:3179) にある。一方、旧規範は [decisions.md:2864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/decisions.md:2864) に残り、予定された supersession fragment は未作成。 | 旧 D を一般 precedent とする consumer は全走を受理集合から落とし、runbook と台帳・レポートの参照が分岐する。 |
| B3 並行 wave の合算予算競合 | `partial` | 現 snapshot は 25,195 bytes で適合するが、commit・land 直前の再計測はまだ将来義務 [s4-adjudication.md:36](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:36)。 | 並行 land で上限を超えれば T-642 の変更・fragment・レポートは checker の受理集合へ入らない。 |
| B4 checker が旧文回帰を拒否しない | `scope 外`（未解消） | checker は `DW-S04` の節実在を登録するだけ [check_docs.py:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:395)。本文 pin はない。 | 将来の全走免除への回帰が静的受理され、破損した台帳・レポートを許す受理集合が復活し得る。 |
| B5 bootstrap の有効時点 | `partial` | ユーザー裁定日は [worklog.md:3179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/worklog.md:3179) にあるが、旧 main から新契約を bootstrap 適用した実行時点・checkout の記録はまだない。 | 未 land 規範を既発効と誤記すると、台帳とレポートが誤った authority/effective-time を参照する。 |
| A-refuted 「段4で」削除 | `closed`（refuted / nit） | 節見出し [core.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:72) と段4 dispatch [入口:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:48) が段を固定。 | 成果物の値・受理集合・参照を変えないため nit。 |
| A-nit brief 59行 | `scope 外`（nit） | 10〜30行契約は [core.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:29)、現 brief は実測59行。 | certified 選択・レポート・台帳への直接影響を書けないため nit。 |
| B-nit skip と段6受入の位置 | `closed`（nit） | 通常の受入は [入口:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:51)、skip 経路の代替期限は [core.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:80)。 | 実行点欠落による受理集合の差はなくなり、単独の成果物影響はない。 |

## 削除した散文の代替

規範喪失はありません。

- 入口は通常遷移を `1→2→3→4→5→6→7→8→9` と固定しています [dev-wave.md:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:33)。
- その上で「実装しない」と裁定した場合だけ「段 5・6 を飛ばし、`4→7→8→9`」と逐語で規定しています [dev-wave.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:49)。

したがって、`4→7→8→9` literal 単独ではなく、入口49行目が削除散文の実質的な別正本です。

## 新しい抜け穴

### (a) matrix 免除の実装差分 wave への漏出

matrix 免除そのものは漏れていません。[core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:79) の条件節が「実装しない」経路かつ実装差分ゼロを要求します。後から実装差分が見つかれば scope・裁定前提の不整合として [DW-STOP:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:22) が発火します。

成果物影響: 実装差分あり wave の matrix kill 証拠は台帳から落ちず、certified 受理集合は変わりません。

### (b) 期限と通常経路

テストが存在する正側では矛盾しません。通常経路は段6で受入再走し、その後に段7へ進むため [入口:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:51)、期限「段7の記録前」と一致します。本 wave も段5・6を飛ばさない裁定です [s4-adjudication.md:5](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:5)。

ただし新文は句点で条件節を切り、2文目に「この経路では」がありません。[core.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:80) を全 wave 共通の限定規則と読むと、通常経路の無条件な受入再走まで「実 repo 読取テストがある場合だけ」に弱められます。これは新しい `regressed` 誤読です。

成果物影響: 実装 wave が全走を省き、コード回帰を含む tip が certified 選択・試行台帳・レポートの受理集合へ入り得ます。

### (c) 否定側

「実 repo を読むテストがない」場合について、次のすべてが未定義です。

- 誰が、どの checkout と検索手順で不存在を判定するか
- 不存在・判定根拠をどこへ記録するか
- 受入全走を免除するのか、別の受入を行うのか
- 「対象外は変異 matrix だけ」と、事実上の受入免除をどう両立させるか

現 repo では該当 node が実在します [test_check_docs.py:6396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/orchestrator/tests/test_check_docs.py:6396)。したがって T-642 自身は正側ですが、未来 wave の偽の不存在申告を拒めません。

成果物影響: 未全走 checkout が land 受理集合へ入り、台帳・成果物索引の赤と certified レポートの壊れた参照が残ります。

## byte 予算

`wc -c` による現在の4ファイル実測です。対象4ファイルは [check_docs.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:177)、hard ceiling は [check_docs.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:254) が正本です。

| ファイル | bytes |
|---|---:|
| `docs/dev-wave/core.md` | 8,645 |
| `docs/dev-wave/workers.md` | 4,575 |
| `docs/dev-wave/mutation.md` | 3,674 |
| `docs/dev-wave/operations.md` | 8,301 |
| **合計** | **25,195 / 25,200** |
| **余白** | **5** |

現 snapshot は上限以下です。旧合計25,196から正味 −1 byteという裁定の算術とも一致します。ただし `check_docs.py` 自体は実行していません。

## 総括

**NO-GO。**  
2文目の経路限定がなく、通常経路の受入再走まで条件化できるうえ、否定側には判定証拠・記録・fallbackがないため A1/A5 の根因が残る。  
段5・6 skip と byte 予算は保たれているが、「この経路」と不存在時の処置を明文化するまで land してはならない。