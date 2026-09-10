結論は **NO-GO** です。旧文の「2文目だけが全 wave に適用される」形は消えましたが、今度は「ときだけ」が受入全走にも係り、通常経路の義務を否定する読みが残っています。

## 焦点判定

現文は次です。

> 「実装しない」裁定で実装差分ゼロのときだけ、対象外は変異 matrix だけで、実 repo を読むテストがあれば段 7 の記録前に受入全走を実走し、結果を worklog へ書く。

[core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:79)

入口は、通常遷移を `1→2→3→4→5→6→7→8→9` とし、特殊経路だけを `4→7→8→9` としたうえで、通常の段6に受入再走を要求しています。[dev-wave.md:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:33)、[dev-wave.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:49)、[dev-wave.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:51)

しかし「C のときだけ、P で、Q」は、P だけでなく Q も C の場合に限ると読めます。したがって「通常経路では C が偽なので受入全走も不要」という限定解釈と、入口51行目の通常義務が衝突します。優先順位がない以上、(b) は閉じていません。

## 所見対応表

| ID | 判定 | 静的根拠 | 成果物への影響 |
|---|---|---|---|
| (b) 通常経路の条件化 | `regressed` | 句点分離は解消したが、「ときだけ」が受入全走まで限定できる。入口51行目との衝突を解消する文言がない。 | 未受入の実装 tip が certified 選択・試行台帳・レポートの受理集合へ入り得る。 |
| (i) 「対象外」の係り先 | `partial` | 入口51行目との対照から段6検査を指す意図は推定できるが、「段6検査の」等の対象名がなく、直前の「scope 外の real 所見」[core.md:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:75) とも競合して読める。 | scope 外所見を実装対象へ戻す／記録だけでよい検査を落とす解釈により、台帳・レポートの対象集合が分岐し得る。 |
| (ii) 「ときだけ」の射程 | `regressed` | 文全体を束縛したため、受入全走も特殊経路限定の義務と読める。これが (b) の残存原因。 | 通常 wave のコード回帰を検出しないまま成果物を certified 扱いできる。 |
| (iii) `4→7→8→9` の削除 | `closed` | literal は入口49行目に逐語で残り、通常遷移も33行目に残る。 | 遷移・受理集合・成果物参照への影響なし。 |
| A1 自己認証 | `partial` | 「実走し」は維持されたが、テスト存在判定の証拠義務はなく、裁定パッケージもこれを認める。[s4-adjudication.md:51](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:51) | 偽の不存在申告で未受入 tip が成果物集合へ入り得る。 |
| A2 matrix 免除漏出 | `closed` | 「実装しない」かつ実装差分ゼロが明記され、通常段6の matrix は入口51行目に残る。 | 実装 wave の matrix kill 証拠は台帳から落ちない。 |
| A3 実行点・期限 | `closed` | 特殊経路でも段7記録前が期限で、親が全走を所有する。[dev-wave.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:35) | 正側では受入 receipt のない tip を段7へ送れない。 |
| A4 byte理由の安全義務削除 | `closed` | matrix と受入の義務自体は現文に残り、byte 上限にも適合する。今回の問題は byte ではなく「ときだけ」の意味。 | 予算超過による成果物拒否は現 snapshot では生じない。 |
| A5 negative control | `scope 外` | gate 新設を裁定パッケージへ返す処置は維持。[s4-adjudication.md:31](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:31) | ユーザー裁定までは不存在誤判定による成果物リスクが残る。 |
| A6 docs-only 確定 | `closed` | 現 `git diff` は `core.md` だけで、docs-only の親編集は入口36行目が許可する。 | 親所有の未監査実装 hunk は成果物集合へ入らない。 |
| A7 scope と記録成果物 | `closed` | 規範編集と段7記録成果物を分離した裁定は変更されていない。[s4-adjudication.md:33](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:33) | 台帳 fragment・レポート参照を正規に記録できる。 |
| B1 約束だけで充足 | `closed` | 「受入全走を実走し、結果を書く」の完了形が維持される。 | 特殊経路を予定記録だけで certified 扱いできない。 |
| B2 旧 D 系の参照分岐 | `partial` | 前向き supersession を記録する処置は整合するが、現 fix の差分には記録 fragment がない。[s4-adjudication.md:35](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:35) | 記録完了までは旧 precedent と新規範で台帳・レポート参照が分岐する。 |
| B3 合算 byte 競合 | `partial` | 現 snapshot は適合したが、commit・land 直前の再計測は未実施。[s4-adjudication.md:36](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:36) | 並行変更後に上限超過すれば本 wave の成果物は checker の受理集合へ入らない。 |
| B4 本文 pin 不在 | `scope 外` | checker変更を実装せず裁定パッケージへ返す処置は `DW-S04` と整合する。[s4-adjudication.md:37](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:37) | ユーザー裁定までは将来の文言回帰を静的受理し得る。 |
| B5 bootstrap 時点 | `partial` | 時制を fragment に記録する処置は整合するが、現差分にはその記録がない。[s4-adjudication.md:38](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:38) | 記録完了までは台帳・レポートが誤った発効時点を参照し得る。 |
| 裁定パッケージの充足 | `partial` | A1/A5/B4 を返す routing は正しいが、現パッケージは選択肢と所見だけで、`DW-S04` が要求する明示的な「推奨案」がない。[core.md:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:75)、[s4-adjudication.md:51](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:51) | 推奨不在の裁定で免除方針が未確定となり、decisions・台帳・レポートの authority が分岐し得る。 |

## byte 実測

`wc -c` による現物の実測です。

| ファイル | bytes |
|---|---:|
| `core.md` | 8,641 |
| `workers.md` | 4,575 |
| `mutation.md` | 3,674 |
| `operations.md` | 8,301 |
| **合計** | **25,191 / 25,200** |
| **余白** | **9** |

pytest、`tools/run_tests.py`、`tools/check_docs.py`、受入全走は実行しておらず、検査を「緑」とは判定しません。

## 総括

**NO-GO。** 「ときだけ」が受入全走にも係り、通常経路の義務を否定する読みを排除できないため、(b) は `regressed`。  
A2/A3/A4/A6/A7/B1 と 25,191-byte 適合は維持したが、裁定パッケージも推奨案欠落で `partial`。  
検査は静的確認のみで、pytest・受入全走・`check_docs.py` は未実走。