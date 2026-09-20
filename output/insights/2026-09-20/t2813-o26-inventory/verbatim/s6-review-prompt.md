単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2813-o26-inventory

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 統合差分 (レビュー対象、docs commit 0bb4365a2 + 実装 commit c805a53a7 の累積、base f94b61fc8): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/s5-cumulative.diff.txt
- 親の段 1 brief: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/verbatim/brief.md
- 親の段 4 裁定 (§2 新本文の確定と削減表、§3 変更面、§4 変異事前登録): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/verbatim/s4-adjudication.md
- 新本文の正本 (998 bytes): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/verbatim/dw-o26-new-section.md
- ユーザー裁定 D2186 項 5 の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/verbatim/D2186-item5.md
- 予算処理の委任裁定 D782 / D961 の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/verbatim/D782.md, /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/verbatim/D961.md
- T-2292 (契約側更新をセットで行う) の起点 entry の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/verbatim/T-2292-origin.md
- 段 5 Codex author の報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/codex/s5-author.md
- repo 内 (統合 commit 済みの wave worktree、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2813-o26-inventory/ 配下の
  `docs/dev-wave/operations.md` (DW-O26 節。旧本文は差分の `-` 側)、`docs/dev-wave/core.md` (DW-C00 の「同一worktreeのdispatchは全種直列（並行はorphan holdでrc=16、`DW-O26`）」の行)、
  `tools/check_docs.py` (`grep -n "DEV_WAVE_DW_O26_SECTION_LITERAL\|DEV_WAVE_L2_SECTION_BYTES_MAX\|_check_dev_wave_layer_budget"` で位置を出し `sed -n` で読む。全文 cat しない)、
  `orchestrator/tests/test_check_docs.py` (`grep -n "_SYNTHETIC_DW_O26_SECTION\|== 998\|o26_contract_weakened\|case == \"M8\"\|静的レビューが見落とした破れを"` で位置を出し `sed -n` で読む。全文 cat しない)、
  読むだけ: `docs/failures.md` の DW-O26 逐語引用 (`grep -n "file 集合列挙のメタテストも焦点走に含める\|静的レビューが見落とした破れを"`。歴史記録として本 wave は触っていない)。

書込可能な tmp は無い。pytest 緑を要求しない。静的検査でよい。テスト実測は親が行う (author の実走結果は報告に列挙済み: test_check_docs.py 583 件 580 passed / 3 skipped、check_docs 違反なし)。

## 前置き — この依頼の性質

研究用 repo の開発手順書 `docs/dev-wave/operations.md` の DW-O26 節 (焦点走の consumer test 拡張) へ、ユーザー裁定 D2186 項 5 が採用した 1 句
「production file を変えた wave は、repo 全体の inventory test 4 群 (…) を参照関係に依らず焦点走に含める」を足した wave である。同節は
`tools/check_docs.py` の literal と `orchestrator/tests/test_check_docs.py` の合成 fixture に byte 単位で pin され、単節予算 1000 bytes (旧 979、新句 331) に
入らないため、親が D782 / D961 の手順 1 段目 (既存記述の削減) で 998 bytes へ収め、Codex author が pin 側を追随させた。上限は上げていない。
正しさゲート (verifier) には触れない。裁定は「追加するのはこの 1 句だけで、他の gate・検査は足さない」。

# 依頼 — 3 レンズを 1 本で: (A) 義務の欠落と意味の変化 / (B) pin 整合 / (C) 過剰・削除

差分を守らず検査する。親の裁定 (段 4 §2 の削減表) も検査対象で、誤っていれば名指しせよ。各所見は「何が・どこで・どう壊れるか」と、
放置したときに成果物 (dev-wave の焦点走集合、check_docs の受理集合、pin の整合) がどう変わるかを 1 行で書く。示せない所見は nit に落とす。

A. **義務の欠落と意味の変化。** 旧本文 (差分の `-` 側) と新本文 (`+` 側) を文単位で対応づけ、(1) 6 義務 (参照関係で引く / private symbol を symbol 名で
   production を grep / 同一 worktree の dispatch 全種直列 / 変更 test file の受入前単独走 / 新規 test file のメタテスト収載 / 並行 wave の相乗り・受入後に足さない)
   のどれかが弱まった・落ちた・条件が変わったか、(2) 削った語句 (段 4 §2 の表) が本当に「根拠説明」であって義務でないか (例:「全走緑は file 単独緑を含意しない」
   「初回実測でも」「名前の推測でなく」)、(3) 「受入全走前」→「受入前」、「production 全体を grep」→「production を grep」、「焦点走対象 file 集合」→
   「焦点走 file 集合」、「焦点走に含める」→「含める」(メタテスト文) が意味を狭める・広げる・二義化するか、(4) 新句が裁定 D2186 項 5 の文言と違う点
   (`orchestrator/tests/` prefix を落とした、「wave は、」の読点、全角括弧) が意味を変えるか、bare file 名 4 つが repo 内で一意か (親の実測 = `git ls-files` で一意)。
B. **pin 整合。** (1) docs 本文 / `DEV_WAVE_DW_O26_SECTION_LITERAL` / `_SYNTHETIC_DW_O26_SECTION` の 3 者が byte 一致か (差分の `+` 側を目視で照合。末尾改行・行折返し位置・
   全角半角・NFC)。(2) bytes assert 998 が実 bytes と一致するか (UTF-8 で数えよ: 日本語 3 bytes、`—` 3 bytes、全角括弧 3 bytes、`` ` `` 1 byte)。(3) `o26_contract_weakened`
   の attack 文字列「静的レビューが見落とした破れを」が新本文の 1 行内に 1 回だけあるか (行折返しで分断されていないか)。(4) M8 変異の追随
   (`test_non_attributable_landing_contract_mutations_have_one_finding[M8]`) — 削除対象の新文が本文に 1 回だけ存在し、削除後の本文が単節予算内 (< 1000) のまま
   exact 不一致「だけ」で赤になるか (削除で他の違反 = 予算・被覆・可視 H2 1:1 が同時に立たないか)。(5) `DW-C00` の「並行はorphan holdでrc=16、`DW-O26`」が
   DW-O26 側から rc=16 の説明を落とした後も参照として成立するか (DW-O26 側に「同一 worktree の dispatch は全種直列」が残る)。(6) 他に旧本文の断片に依存する
   test・checker・docs 参照が残っていないか (author は「無い」と報告。`grep -rn` 相当の静的探索で裏取りせよ。`docs/failures.md` の逐語引用は歴史記録で対象外)。
C. **過剰・削除 (DW-S03 固定レンズ)。** (1) 裁定「この 1 句だけ」に対し、本 wave が足したものは 1 句だけか。一次資料 §7 の候補 1 件目 (provenance 監査 dispatch の
   直列化の 1 句) を混ぜていないか。(2) 削減が D782 / D961 の「既存記述の削減」の範囲内か、D961 が禁じる「安全義務を落として予算を守る」に当たるものが無いか。
   (3) 上限 (1000) を動かしていないか、`DEV_WAVE_EXACT_VISIBLE_SECTIONS` の登録集合・他の pin 節・L1 / L1.5 予算に副作用が無いか。(4) 逆に、足りないもの
   (例: T-2292 の起点 entry が指摘した「process 起動一覧と subprocess guard も落ちる」型が新句の 4 群で被覆されるか、されないなら本 wave の scope 外として
   正しく記録すべきか) を指摘せよ。ただし新しい gate・検査・台帳の追加は提案しない (scope 外)。

## 出力形式

- 見出しはすべて `##`。節: `## 所見` (番号付き。各所見に レンズ (A/B/C)・must-fix か nit か・「放置時の成果物影響 1 行」・根拠 (file と行または引用) を書く。
  所見ゼロなら「ゼロ」と書き、何を検査してゼロだったかを列挙する)、`## 親裁定への反証` (段 4 §2 の削減表と D782 手順の適用に誤りがあれば)、
  `## GO / NO-GO` (must-fix があれば NO-GO、無ければ GO。判定理由 1 行)、最後に `## 総括`。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終わる (無出力が最悪)。
