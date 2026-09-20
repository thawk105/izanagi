## 検査範囲

必読資料はすべて読取可能でした。以下、`J` は指定 job dir、`W` は指定 worktree。`plan` は `J/codex/s2-plan.md`、`brief` は `J/brief.md`、repo 内のパスは W 相対です。静的読解に加え、書込みなしの Git trailer parser・hash・祖先・参照検索を実施しました。pytest・変異実行・ファイル書込みは未実施です。

## Findings

**A-1 — refuted：S1 の判定式が非適合行を受理するという懸念。** `plan:28` の raw件数＝1、parse件数＝1、raw完全一致、文法・予約語検査の組合せは妥当です。`orchestrator/campaign/s8b_ratified_freeze.py:518` は message 全体から key が AI-Agent の候補行を数え、`:528` は separator を `:` に固定して Git が認識した trailer の値だけを取り出します。CABだけ・waiverだけでは raw件数が0、本文だけの候補行では parse件数が0になります。大小文字違い・末尾空白・CRLF は値側の正規化後に raw完全一致で拒否されます。CRLF の raw 行に `\r` が残ることと、本文だけ／CABだけ／waiverだけの挙動は parser 呼出しでも確認しました。本文の普通の文章に埋め込まれた `AI-Agent:` 文字列は候補行になりません。本文中の候補行と末尾の適合 trailer が併存すれば raw件数で拒否します。ただし separator pin は設定全体の隔離ではありません（同 file `:310`）；plan は「隔離 parser」と一般化しないでください。

**A-2 — refuted：scope必須・role=author必須・product=codex必須への狭窄。** `plan:33` が参照する `tools/check_ai_provenance.py:87` の文法は scope 任意、`:66` は manager を含む5 role、product は IDENT から予約語4値を除く条件です。提示された Codex author 行、scope無し、manager、Claude の適合1行はいずれも S1 で受理されます。実際の A/X に Codex author を記録する指定（`plan:183`）は当該作業の provenance であり、一般受理条件とは別です。ただし正例表（`plan:106`）ではこの幅が明示されていないため、scope無し・manager・Claude の正例を parameterize すると、将来の余計な制限を検出できます。現案に追加裁定は不要です。

**A-3 — refuted：既存防壁や4呼び手への適用が変わるという懸念。** `plan:48` は `_assert_user_commit` の trailer 分岐だけを交換し、merge→trailer→ancestry の順を維持します。approval／pointer／revocation／cancellation は同 file `:1204`、`:1219`、`:1234`、`:1247` で同じ関数を呼びます。`generation-commit-none`（`:581`）、diff検査（`:1298`、`:1305`）、Xの親検査（`:1312`）、`_unique_introduction`（`:595`）、`history-mutated`（`:490`）は変更対象外です。批准側 `_is_none_commit:546` と、別 module の `orchestrator/campaign/t080_freeze_migration.py:1236`／`:1267` も不変です。これは計画上の判定であり、実装差分での byte 不変確認は後段に残ります。

**A-4 — 条件付き：複製＋meta-test は採用可能だが、規約全体の drift を検出する保証ではない。** `plan:88` の pattern・flags・予約語集合の exact比較は、IDENT・ROLESを含む文法変更を検出できます。一方、`tools/check_ai_provenance.py:1515` 以降の意味条件が将来追加されても、その3比較と既存の model/reasoning負例だけでは必ず検出できるとは限りません。遅延importも定数だけを取得するなら同じ限界があります。正本参照と別名 `_PROVENANCE_*` を保ち、単一行の正負例について checker との判定一致を検査する補強を推奨します。D75の「二義化禁止」と fail-closed に照らし、現実装経路では複製＋meta-testを条件付き支持しますが、「規約の全変更へ自動追随」とは記録できません。

**A-5 — refuted：遅延importが監査を起動する、またはImportErrorで受理へ倒れるという懸念。** `tools/check_ai_provenance.py:35` は root解決とsys.path挿入、`:44` は site_policy importを行います。`_KNOWN_VIOLATION_*`（`:36`）はパス定数の構築であり、その場で例外台帳をロードしません。site_policyのimport依存は標準ライブラリで、批准moduleへ戻る循環は確認できません。監査入口は `main:3519` と `__main__:3780` です。ただし最初の `tools` 解決に失敗した場合は内部のsys.path挿入では救えず、コピーfixtureのruntime補完も campaign配下に限定されています（`orchestrator/tests/test_s8b_oracle_driver.py:1492`）。`plan:90` と `brief:30` はImportErrorをRatifiedFreezeErrorに変換するため、意図は明確にfail-closedです。

**A-6 — real：変異表にdiff・Xの親関係を壊す変異が欠けています。** 裁定 `J/ruling-13-2x.md:3` は merge／X^≠A／diff超過を含む負例と変異matrixによるKILLED確認を要求しますが、`plan:372` の表はmergeとancestryまでで、approval diff・pointer diff・pointer parent検査の変異がありません。殺す既存testは `orchestrator/tests/test_s8b_ratified_freeze.py:2328`、`:2345`、`:2362` に実在し、構造化行へのparameterizeも `plan:119` にあります。段4へ各検査削除の3変異を追加し、それぞれ対応するexact reason assertionへ帰属させてください。

**A-7 — real：raw件数検査削除を殺す入力が、テスト仕様に明示されていません。** `plan:374` の変異には「本文に余分なAI-Agent行＋末尾に適合trailer1行」が必要ですが、`plan:109` は「本文にしか存在しない行」までしか列挙していません。本文だけならparse件数0が拒否を維持し、構造化2行ならparse件数2が拒否を維持します。追加すべき入力は、本文と末尾に**同じ適合値**を置いて raw＝2、parse＝1、先頭rawとparse値の完全一致を成立させるものです。この状態は書込みなしのparser呼出しで確認できました。helper直接検査の方針（`plan:144`）を使い、後段topologyによる拒否と分離してください。

**A-8 — 条件付き：その他の変異の帰属は概ね成立しますが、単独変異と複合変異を区別する必要があります。** `plan:376` の「raw／parse件数を**ともに**1件以上へ変更して先頭を採用」は、適合構造化2行を使う新設test（`:109`）で殺せます。片方だけの `==1→>=1` は他方が拒否を維持し得るため、この結果を転用できません。raw→strip比較はverbatim末尾空白（`:111`、`:142`）、key正規化は小文字case、文法検査削除・予約語削除・model/reasoning検査削除は適合prefixを持つ各負例（`:110`）へ帰属できます。none＋構造化混在は既存test `:2274` の第2行を適合値へ替えれば成立し、merge・ancestry・G変異も計画上対応があります。Gは受理ではなくreason変更によるkillです（`plan:387`）。`fullmatch→search` 単独は anchored regex と正規化済み1行値では等価になり得るため、無条件KILLED対象から外す `plan:389` は正しい判断です。

**A-9 — real：R3既存負例の説明が、改訂後の実際の検査箇所とずれます。** `orchestrator/tests/test_s8b_ratified_freeze.py:2308` は「`_is_none_commit` のraw検査のみが拒否し、そのstartswith変異をこのtestが殺す」と説明しています。しかしS1後のapproval経路は新helperを呼ぶため、このtestは `_is_none_commit` 自体の変異を検出しません（`plan:51`）。`plan:128` の説明更新対象3本に、このR3コメントも追加してください。旧helperのbyte検査を独立に保証する必要があるなら、同じ保存messageに対する `_is_none_commit` 直接assertを追加し、A/X側helperとは帰属を分ける必要があります。

**A-10 — 条件付き：claude-opus負例3本の検出力は維持されますが、名前だけでは旧意味が残ります。** `orchestrator/tests/test_s8b_ratified_freeze.py:2264`、`:2526`、`:2608` の値は `product=…` で始まらず、改訂後も文法不適合として拒否されます。`plan:128` のコメント更新とexact reason維持は妥当です。一方、`with_ai_trailer_rejected` 等のnode名は適合AI行も拒否するように読めます。名前維持を採るなら各testのdocstring冒頭に「歴史的node名。非構造化 `claude-opus` の拒否を検査」と明記してください。G fixtureの `claude-opus` は候補側の別契約であり（批准module `:586`）、一括置換しない方針も正しいです。

**A-11 — 条件付き：Codex author1行のA/X provenanceは、親が機械的代行に徹する場合に整合します。** `J/verbatim/ai-provenance.md:71` は機械的Git操作を記録せず、実質的な採否・統合判断や独立レビューは記録すると定めています。したがって `brief:25` は実際の寄与がその前提に合う場合に限り正しい記録です。CABは任意で代用不可（同資料 `:73`）なので付けない判断は妥当です。A/Xの通常JSONは `_is_implementation_path` のbasename・suffix・prefix条件に該当せず（checker `:1585`）、staged pathを使うpreflight（`:1830`、`:3662`）でもCodex author契約による追加拒否はありません。構造化文法への適合は別途必要で、rc=0実測は未実施です。`brief:33` のapproverはユーザー委任と裁定日を含み、裁定に合致します。親に実質的寄与が生じる場合は、1行制約のため記録を省略せず、運用見直しまたは裁定パッケージへ返してください。

**A-12 — real：briefのP3予測・P2件数・memo行指定には現物との差があります。** `brief:32` のv1 gate-checkに対する `freeze-not-active-generation` 予測は、driver `:627` のv1早期分岐と不整合です。`brief:18` の「2 passed」に対し、`orchestrator/tests/test_frozen_artifacts.py:187`、`:201`、`:212`、`:227`、`:234` の5関数をrunner `:251` が列挙します。ただし5 passedは成功時の予測で、実測結果ではありません。また `brief:16`／`:46` がno-active説明として挙げるmemo `:46` はpayer node名で、説明本文は `:17` にあります。これらはplan `:188`、`:238`、`:339`、`:345` が既に適切に補正しています。

**A-13 — refuted：briefの主要な実測前提が誤っているという懸念。** `brief:23` のG／X1′祖先関係は両方rc=0、generation SHAは指定値と一致し、approvals／activeは現worktreeで不在でした。`brief:27` のpin検索についても、主要な既存変更対象6ファイルのSHA256前半32桁をoutput／orchestrator/tests／docsへ検索し、各hit 0・検索エラーなしを確認しました。ただしこれを全形式の依存不存在へ一般化することはできません。「未登録nodeはfail-soft」は `orchestrator/tests/conftest.py:1739` が未知keyを最終的にNoneへ戻す実装と一致します。worker payload不正など別の拒否までfail-softと広げない限り、記述は妥当です。

## 総括

real finding：

- **A-6:** approval diff・pointer diff・Xの親検査に対応する3変異が未登録。
- **A-7:** raw件数検査削除を単独で殺す「本文＋末尾trailer」の入力仕様が不足。
- **A-9:** R3負例のコメントが、改訂後も旧helperの変異を殺すと誤説明する。
- **A-12:** briefのv1予測・P2件数・memo行指定が現物と不一致。planは補正済み。

裁定パッケージ候補は、親がA/Xへ実質的に寄与して複数provenance行が必要になる場合です。role=author／product=codexの一般受理条件への追加、CAB・waiver全般の新たな禁止は現裁定から導けず、導入するなら別件です。

**planはA-6・A-7・A-9を修正して採用、briefはA-12の補正を反映して採用を推奨します。** S1の受理式は支持します。文法共有は複製＋meta-testを条件付き支持し、意味条件の同期検査と受理側の幅を示す正例を補強してください。KILLED・preflight成功・批准成功は本段では確認していません。