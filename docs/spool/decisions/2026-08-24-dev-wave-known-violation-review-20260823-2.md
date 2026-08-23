---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: dev-wave-known-violation-review-20260823
seq: 2
---

## {{D:known-violation-zero-unreachable}}. known-violation 0 件は現行契約では到達不能であり、目標指標の改訂をユーザー裁定へ返す

**決定:** 「known-violation を 0 件にする」は、現行の provenance 契約と履歴不変の原則のもとでは
AI 側の作業だけでは達成できないと記録する。53 件のうち 49 件は不可逆であり、残り 4 件も
{{D:merge-line-authorship-predicate-rejected}} により撤去しない。目標指標を改めるか、
遡及訂正の枠を開くかはユーザー裁定へ返す。

**理由:**
- known-violation は「過去の commit がその時点で有効だった規約に違反していた」という事実の記録で
  あり、commit message を書き換えずに事実を消す手段は無い。履歴の書き換えは禁止されている。
- 最大の塊である 2026-08-09 の 22 件は、trailer literal が全件同一の単一事故である。
  「規則が後から出来たため legacy 免除に当たるのでは」という仮説は反証した — 値の文字集合規則と
  role 許可集合はいずれも checker 導入 commit `50c1ef4e` (2026-07-14) から在り、
  `docs/ai-provenance.md` も違反 commit `f277efd446` (2026-08-08) の時点で同じ本文だった。
- 遡及訂正の経路は 1 本しかなく、閉じている。`docs/provenance/correction.md` の `PR-C01` は
  「一般 allowlist・設定・CLI 免除へ拡張しない。この枠は `6d7141dc` で消費済みであり、
  新しい担い手を追加してはならない」と明記する。`AI-Agent-Waiver` は commit 自身の trailer を
  読むため遡及適用に履歴書き換えを要する。git notes による外付け訂正の経路は repo 内に存在しない
  (全数検索で不在を確認)。
- 増加は実測で単調である。各 blob の registry tuple を `ast` で構文解析し `--first-parent` で
  main 本線だけを追うと、件数の変化点は増加 20 回・減少 2 回。意味のある減少は checker 是正による
  53→34 の 1 回だけで、44.7 時間後に 53 へ復帰した (約 10 件/日)。**生成器を止めずに台帳だけ
  減らしても 2 日と持たない。**

**却下した選択肢:**
- trailer の文法 (`IDENT` の文字集合、role の許可集合) を緩めて 22 件を通す — 絶対規律 2 に反する。
  違反当時から有効だった規則を後から緩めることは、監査そのものを無効化する。
- 親の判断で `PR-C01` の一回性を解除する — 訂正機構を恒久的に開く判断であり、
  「後から書けば直せる」経路を作る。親の裁量ではない。
- 台帳の件数を報告から省く、または「残置」として扱いを下げる — D662 決定 5 が
  「低優先度の残置ではなく高優先度タスクとして随時解決する」と定めた方針に反する。

## {{D:merge-line-authorship-predicate-rejected}}. merge の実装面判定に「著作行の実在」による免除を入れない

**決定:** merge commit の実装面 path 判定へ、「結果の全行がいずれかの親に存在し、かつ全親が結果の
subsequence である」ことを根拠に除外する一般則は入れない。D721 を維持する。
該当していた 4 件 (`5823caf328`, `3eaf2038ec`, `0c0f3e71b3`, `bf92f327ca`) は台帳に残す。

**理由:**
- 述語を満たしても merge author は実装上の意味を著作できる。親 P1 が `@audit`、親 P2 が
  `@authorize` を持ち、結果が両方を並べる場合、全行が親由来で両親とも結果の subsequence であり
  出現回数も上限内である。しかし `audit(authorize(check))` という**相対順序を決めたこと自体**が
  実装著作であり、逆順とは挙動が異なる。両親が同じ 1 行を持ち結果がそれを 2 回置く場合も同型で、
  二重登録という新しい挙動を merge author が作っている。
- したがって D721 の中心理由「最終形からは自動解決と手解決を区別できない」は、述語を
  行の集合包含から順序保存へ強めても解消しない。強めても救えるのは 10 件から 4 件へ狭まるだけで、
  「手で解決した merge を Codex author 不要にする」という本質は変わらない。
- 収量が小さい。4 件は台帳 53 件の 7.5% であり、同じ労力を生成器側へ向ければ最大 12 件分の
  将来抑止になる ({{D:known-violation-entry-storage-needs-ruling}})。

**却下した選択肢:**
- 述語をさらに強めて「最短共通 supersequence」まで要求する — 同一の空行や閉じ括弧が多数ある
  file では、別ブロックの同値行を同一視して正当な独立追加まで落とす。順序著作の反例も残る。
- `git merge-file` の再計算で自動解決だった merge だけを通す — blob 単位の低水準 merge であり、
  rename 検出・`.gitattributes` の custom merge driver・実際の strategy を再現しない。
  当時の解決主体を示す証拠にならない。
- 該当 4 件だけを個別にユーザー裁定で撤去する — 既に exact SHA の known-violation として
  登録済みであり、狭い裁定を二重に重ねるだけで受理集合は変わらない。

## {{D:known-violation-entry-storage-needs-ruling}}. 台帳の entry 単位格納への移行は、逐語 pin 撤去のユーザー裁定を着手条件とする

**決定:** `KNOWN_PROVENANCE_VIOLATIONS` を entry 単位のデータへ移す改修は、
`test_known_violation_ledger_matches_literal_entries` の独立 literal pin を撤去してよいという
ユーザー裁定が出るまで着手しない。裁定が出た場合の必須条件を本決定に固定する。

**理由:**
- 移行の効果は逐語ミラーを畳むことと不可分である。正本の tuple だけをデータへ移しても、
  ミラーが Python literal のまま残れば登録のたびにそこを編集することになり、実装面の変更と
  競合が残る。ミラーを同じデータから読む形に書き換えれば、同じ値を 2 度読むだけの恒真な検査になる。
- 逐語ミラーは説明文だけを固定しているのではない。53 件全部の commit・finding kind・
  expected value・ruling・note・順序・一意性を独立に照合しており、`ruling` と `note` は
  受理判定に使われない**からこそ**全史監査では改変を検出できない。実 commit 照合テストの被覆は
  31 件にとどまり、最新 22 件を含まない。**この pin を畳めば、単一 file の編集だけで
  台帳の裁定根拠と公開 note を偽造・消去できる。**
- 既存の正しさ防壁を撤去する判断は親の裁量ではない (絶対規律 2)。

**必須条件 (裁定が出た場合):**
- file key は `<sha>` 単独では足りない。1 commit が 2 finding を持つ実例があるため
  複合 key (`<sha>--<kind>` 等) で一意化し、filename と本文の一致を検査する。
- index file を持たず `sorted` の directory 列挙で読む。index を置けば共通編集面が復活する。
- 現行 `_known_violation_registry()` の全検証 (full lowercase SHA、kind 集合、ruling 非空、
  note の改行禁止と禁止文字と descriptive 要求、malformed の value 要否、SHA/finding 重複禁止) を
  同値に保存し、重複 key・未知 key・欠落 key・型違反を厳格に拒否する。
- tracked な regular file だけを読み、symlink・untracked・ignored を拒否する。
  HEAD の tree から読むか、worktree と HEAD の一致を検証する。**さもなければ untracked file を
  置くだけで finding を抑止できる。**
- データ directory は実装面として分類する。`docs/` 配下へ置いて docs-only 化することは
  利点ではなく、Codex author 契約の抜け道である。
- loader は lazy load とし、import 時に走らせない (`--message-file` 契約を壊す)。
- 53 件全部を実 commit の finding と突き合わせる検査と、公開 stdout の逐語検査を同じ wave に置く。
- 投影外 consumer (`tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`、
  `orchestrator/tests/test_hooks.py`、`orchestrator/tests/test_dev_wave_land.py`) の
  opaque pin (whole-file SHA-256、byte 予算、行数、逐語断片) の read-only 閉包確認を必須 scope に含める。
- 同一 entry の並行登録は競合が残る。別 filename へ逃がすと merge 後に registry 重複で
  停止するため、**意図的に fail-closed とする。**

**却下した選択肢:**
- 逐語 pin を単純削除して競合面を減らす — 受理集合と land 可否を変えずに台帳の裁定根拠だけを
  偽造・消去できるようになる。gate の弱化である。
- 正本の tuple だけをデータ化し、ミラーは Python literal のまま残す — 競合面が減らないため
  効果が出ない。
- データを `docs/` 配下へ置いて登録 commit を docs-only にする — 現行の実装面判定は
  prefix・suffix・basename の 3 条件だけを見るため `docs/**/*.json` を実装面にしない。
  結果として Claude 単独の commit で finding を抑止できるようになる。
