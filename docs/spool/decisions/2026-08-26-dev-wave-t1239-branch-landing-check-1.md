---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1239-branch-landing-check
seq: 1
---

## {{D:branch-landing-machine-check}}. 取り残し branch の着地判定は commit closure を対象にし、決定的証拠を exact tree state と fold receipt だけに限る

**決定:** D720 条件 1 (未着地であること) の機械判定を `tools/check_branch_landed.py` として実装し、
次の 6 点を固定する。条件 2 (現況で妥当であること) は機械化せず、出力に未検査であることを明示する。

1. **判定対象は commit closure である。** `git rev-list <対象> --not <main>` の全 commit を列挙し、
   各 commit が**全ての親に対して**導入した tree entry の状態だけを証明義務にする。
   tip の net 差分を対象にしない。merge commit も対象に含める。
2. **決定的な証拠は 2 つだけである。** (a) `(path, mode, object type, oid)` の同時状態が
   main から到達可能であること、(b) spool fragment なら正式 schema を満たす fold receipt に
   その `content_sha256` があること。別々の commit から mode と blob を拾って合成しない。
3. **patch の指紋・台帳の task ID 検索・本文の逐語照合は `observations` であり verdict を動かさない。**
   `git cherry` は merge commit を落とし、この機体の git 2.34.1 は `patch-id --verbatim` を持たず
   空白差を無視する。逐語照合は重複した節・頻出行で偽陽性を作れる。
4. **判定は 3 値とし、`not-landed` は closed-world の負証拠があるときだけ返す。**
   探索の打ち切り・timeout・上限超過・parse 不能・shallow・履歴書き換え・ref 移動は
   すべて `indeterminate` に倒す。同一 path の blob 不一致だけを未着地の証拠にしない
   (別 path への移植を排除できない)。
5. **fold receipt に無いことを未着地の証拠にしない。** fragment は別 wave 名へ re-home されてから
   fold されることがあり、その場合 whole-file の sha が変わる。実例が現存する
   (`worktree-roadmap-workload-hint` の decisions fragment は receipt に無いが D568 として着地済み)。
   receipt 不在は `indeterminate` とし、非決定の `ledger_probe` が
   frontmatter の `title:` を identity 単位、本文の構造単位を補助として
   canonical 台帳と `docs/archive/` を検索して手掛かりを返す。
6. **入力は local branch 名と commit-ish の両方を受ける。** 取り残しの実体は削除後には
   到達不能 commit であり、判定が最も要るのは削除の直前と直後である。
   両方が解決する曖昧な入力は fail-closed で `indeterminate` にする。

**理由:**
- **tip の net 差分は削除で失われる内容を測れない。** merge commit が持つ競合解決の結果と、
  branch 途中でだけ存在した blob は net 差分に現れない。判定の目的は
  「この ref を消したとき何が到達不能になるか」であり、対象は closure でなければならない。
- **逆に、和集合で数えると証明義務が実データで一桁膨らむ。** `worktree-t1458-side-ccbench-provenance-fix`
  の merge は全親に対する差が 0 file だが、parent edge ごとの和集合では 17 file が課される。
  実装初版はこれで 18 file を要求し `indeterminate` になった。積集合へ直すと 1 file になり
  `landed` を返せた。同じ機序で `t1484-backup-before-trailer-fix` は 171 unit から 6 unit へ減った。
- **偽の `landed` と偽の `not-landed` は損害が非対称である。** 前者は削除で内容を失い、
  後者は着地済みを二重に台帳へ入れる。前者を優先して塞ぎ、後者は `indeterminate` で人へ返す。
- 決定的証拠を絞った結果、実データ 8 件のうち 4 件が `landed`、4 件が `indeterminate` になり、
  `not-landed` は 0 件だった。**未 fold の fragment を機械で名指しできないのは意図した保守性である**が、
  そのままでは回収対象を選べないため、非決定の観測層で手掛かりを出す形にした。

**却下した選択肢:**
- **`git cherry` の `-` を landed の十分条件にする** — 空白差を無視し merge を落とす。
  実データ 4 本で closure の commit 数と `git cherry` の行数が食い違った。
- **追加行が main に逐語で存在すれば landed とする** — main 側に同じ節が複製されていると、
  branch が変更した節とは別の複製に偶然一致する。反例が構成的に作れる。
- **fold receipt に無い fragment を未着地とする** — 実データで 5 件中 3 件が誤りになる。
  うち 1 件は D568 の二重採番を招く。
- **生成物らしい file を照合対象から外す一般則を作る** — 都合の悪い file を外す抜け道になる。
  再生成される不透明 blob は `indeterminate` に残す。
- **判定を 2 値にする** — 「まだ着地していない」と「着地したか判定できない」が混ざる。
  実データに、blob も逐語も一致しないが未着地とは言えない file が現存する。
