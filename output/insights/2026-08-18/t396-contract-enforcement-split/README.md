# [T-396] sort coder 契約の執行主体を分けた — 禁止文を書き換えずに後置し、pin が意味を守らないことを変異で実証した

2026-08-18、dev-wave `dev-wave-t396-contract-alignment`、基準 main = `a160f4aa`。
ユーザー裁定 (2026-08-15 /rulings 全件、A/B/C/D) の実装。

逐語は `verbatim/`。段 1 brief、段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定、段 5 実装子 2 本、
段 6 敵対レビュー 2 本を凍結した。

## 1. 実装が要ったのは A と B だけだった

| 裁定 | 内容 | 本 wave の処置 |
|---|---|---|
| A | 契約側を実態へ合わせる | **実装した** |
| B | bounded loop の固定を外して未定義へ戻す | **実装した** |
| C | verifier の予定操作数検査を起票する | **既に実行済み** — [T-1148] が entry 568 (2026-08-16) で起票され、現 worklog でも active |
| D | 段 8 の gate inventory 1 文 | **見送り確定** — commit `4dd87752` で処理済み。D344 も覆さない |

C を再起票していれば二重在籍 ID になり、fold が rc=26 で止まっていた。
起動時の実測 (F35 の stale 照合) がこれを防いだ。

## 2. 段 2 の置換案を段 3 が反証し、設計ごと差し替えた

段 2 プランは禁止 5 bullet を「機械執行される項目」と「auditor が拒否する残余」へ
**書き直す**案を出した。段 3 レンズ A (`gpt-5.6-sol`, reasoning=max) が 3 件を must-fix にした。

1. **書き直しの過程で禁止が 1 つ落ちた。** 現行契約は「例外送出は不可」と無条件に書くが、
   置換案は機械項を「oracle が実際に観測した例外」、残余項を「corpus で発火しない条件付き例外」に
   限定していた。**内部で処理された例外送出**がどちらにも属さず、policy 上の受理集合が黙って広がる。
2. **複合 bullet 内の原子的義務を取りこぼした。** 第 3 bullet は comment delimiter の禁止と
   「説明をコード内に埋めず `justification` へ書く」義務の 2 つを含む。前者は機械執行だが、
   後者は `justification` が optional key で loader が欠落を空文字列にするため未検査である
   (`projection_guard.py:32-33`、`p3_s4_loop_sort.py:371`)。置換案は bullet 全体を「完全」とした。
3. **「auditor が拒否する」は結線されていない。** `.claude/agents/auditor.md:21-28,32-36,66-82` の
   入力にも checklist にも sort closed-region の残余は無い。coder prompt へ書くだけでは
   分離された auditor の判定規則にならない — 謳うだけで発火しない保証である。

親はこれを全件採用し、**禁止 5 bullet を 1 byte も変えずに残して執行範囲を後置する**形へ変えた。
段 6 レンズ 1 が基準 main `a160f4aa` と現行の当該 block を byte 比較し、完全一致を確認している。

### 親が足した所見 — 回避条件の開示

段 2 案の残余記述は「有限 SWO oracle で relation の変動として観測されない」「明示的な無条件
ループとして検出されず」という**回避の境界条件を逐語で書いていた**。これを読むのは合成側の
LLM であり、D48 の偵察 firewall に逆行する。執行の粒度 (完全 / 部分 / なし) までに留め、
境界条件は書かないと裁定した。契約が実態より広く読めることの実害は「守られていると誤読する」
ことなので、粒度を示せば解消する。この設計判断は本 wave の decisions エントリ (「role 契約の執行主体は禁止文を書き換えずに後置で示す」) に記録した。

## 3. 確定した執行範囲 (原子的義務の粒度)

段 2・段 3 レンズ A・段 5 実装子・段 6 レンズ 1 が独立に導出し、4 者で一致した。
射程は **live `CoderProposalSort` build 経路**に限る (S6 sort sweep は固定候補で SWO oracle を
呼ばず、freeze 再実体化は `prepare_cell` で quarantine と oracle を再実行する)。

| 原子的義務 | 判定 | 規則 ID |
|---|---|---|
| 生の前処理指令 | 完全 | `HOLE_ESCAPE/content-directive` (`diff_quarantine.py:491-496`) |
| 新しいヘッダ取り込み | 完全 | 同上 + `FRAME_ALTERED`/`OUTSIDE_REGION` + include HEAD 照合 (`source_digest.py:669`) |
| 新しいマクロの追加 | 完全 | `HOLE_ESCAPE/content-directive` |
| 新しいグローバル変数の追加 | 完全 | `FRAME_ALTERED`/`OUTSIDE_REGION` + `not-a-single-sort-statement` (`sort_swo_oracle.py:486`) |
| `//`・`/*`・行末 backslash | 完全 | `content-comment-line`/`content-comment-block`/`content-line-splice` (`diff_quarantine.py:503-522`) |
| 非決定ビルトイン | 部分 | `relation-varies-within-process` / `relation-varies-across-process-order` |
| 副作用のある呼び出し | 部分 | `host-effect.*.v1` 5 規則 + `corpus-mutated-by-comparator` |
| ループ | 部分 | `host-effect.unconditional-loop.v1` + `candidate-run-cpu-limit-exceeded` |
| 例外送出 | 部分 | `candidate-comparator-threw` |
| 新しい型/関数の追加 | **なし** | 該当する rule ID は存在しない |
| 説明を `justification` へ置くこと | **なし** | 該当する rule ID は存在しない |

親が段 1 で書いた (P1)「5 項目とも未執行」は粗すぎた。5 bullet と原子的義務を同一視したことが、
段 2 の誤り 1・2 と同じ型の誤りである。

## 4. pin は bytes の同一性しか証明しない (変異で実証)

段 2・段 3 レンズ A・段 6 レンズ 2 が独立に「禁止文の保持を意味で守る test は実在しない」と
結論した。所見ゼロを変異なしで緑と数えない (`DW-M02`) ため、**M6 を SURVIVED 期待で事前登録**した。

M6 は禁止 bullet を 1 行削り、`SOURCE_FILE_SHA256` と生成 adapter を**整合させて再承認する**
3 枚同時変異である。再承認後の adapter bytes は repo の tracked file を 1 byte も触らずに、
job dir の scratch root へ必要 3 directory を複製して `render_adapter` を回して求めた。

pin だけを外した変異 (M1)、adapter 内 pin だけを戻した変異 (M2)、adapter 埋込本文から
1 行削った変異 (M3) は殺されるが、**3 枚を整合させると全検査が緑のまま通る。**
本走の M6 は `anchor_counts` が 3 枚とも 1 で rc=0・failed node 0 件であり、
注入は実在して等価変異ではない。
checker の緑を意味の証明として報告してはならない。別タスクへ分離した。

## 5. waiver を機械会計させるため commit を 2 本に分けた

段 5 実装子は `.codex/role-adapters/coder-v4-autonomous-sort.json` を書けなかった。
codex の sandbox が repo 内の `.codex/` を read-only でマウントしている
(`OSError: [Errno 30] Read-only file system`、実測)。親は D95 決定 (3) に従い代行せず
ユーザー裁定へ返し、承認を得て D105 の waiver 経路で renderer 出力を適用した。

段 6 レンズ 2 が `check_ai_provenance.py` の実装を読み、
**「commit 内に Codex author が 1 人でもいると checker は先に成功し、waiver を適用済みと数えない」**
ことを指摘した。1 commit のままなら人間可読な帰属は残せても、親が adapter を書いた事実は
機械証明できない。実装面 3 枚 (Codex author) と adapter 1 枚 (親 author + waiver) を分けた結果、
`implementation-author-waived=1` として実際に発火・計上された。

## 6. B が失う検出力

削除したのは `test_ordinary_for_range_for_and_data_dependent_loops_pass` の 5 parameter。
production の `coder_effect_gate.py` は変更していないので**現在の受理集合・certified 選択・
材料レポートの値は不変**である。失うのは「将来 bounded / range-for / data-dependent loop を
誤って拒否する回帰」の検出だけで、**受け皿は無い**。姉妹の false-literal テストは別入力を
覆うだけで代替にならない。live meta-test・docs の逐語参照は全件検索で 0 件だった。

これは裁定 B が明示的に選んだ未定義化であり、テストを甘くして緑にしたのではない。

## 7. 実装しなかった real 所見 (裁定パッケージ)

1. **auditor の残余が契約へ結線されていない。** §2-3 の根。sort の closed-region 残余を
   auditor の入力と checklist へ結線するまで、契約文へ「残余は auditor が拒否する」と
   書いてはならない。本 wave は sort role 1 枚だけを触る裁定だったため実装していない。
2. **禁止集合の保持を意味で守る検査が無い。** §4 の M6 が実証した残余。
3. **codex sandbox が `.codex/` を read-only にする。** Claude role source を触る wave は
   毎回 D105 waiver を要する。恒久解が要るか waiver の反復で足りるかの裁定。

## 8. セッション異常

13:01 JST に段 3 の子 2 本が `401 Unauthorized` の連打で rc=1・出力 0 bytes で即死した。
`codex login status` は "Logged in using ChatGPT" のままだった。並行 wave [T-688] は同じ
時間帯に usage limit として観測しており、同一障害が 2 つの表層症状を持つ。
新しい prompt bytes で再投入して回復を確認した (job-id は prompt 内容の sha256 なので、
ファイル名だけ変えても `既存の完全な receipt は上書きできない` で止まる)。
詳細は本 wave の failures エントリ (「codex の同一上流障害が『認証失効』と『枠切れ』の 2 症状で出た」) に記録した。

## 9. 環境と実測

性能計測は行っていない。焦点走 (`test_coder_effect_gate.py` + `test_codex_agents.py` +
`test_codex_role_runtime.py`) = 174 passed / 4 skipped / 0 failed。
`tools/check_codex_agents.py` rc=0、`tools/check_docs.py` 違反なし、
全史 provenance 監査 4001 件・新規違反なし (waiver 9 件目として計上)。
変異 matrix = baseline PASSED・KILLED 5/5・SURVIVED 1 (事前登録)・MISMATCH 0・matching 6/6。
受入全走の結果は worklog エントリへ書く。
