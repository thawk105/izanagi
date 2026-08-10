静的検査のみを行った。親提示の実測結果は再現しておらず、pytest は実走していない。

## 1. 残る迂回

### real — 「可視行」が本文の可視 prose に限定されていない

新 lint は frontmatter を解析する前に文書全体を走査するため、frontmatter も候補になる。[tools/check_docs.py:4076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4076) [tools/check_docs.py:4085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4085)

以下の緑・赤は、通常の command 編集として digest を同期した後の新 lint 判定を指す。

```diff
-description: マージ済みブランチと worktree を安全手順で掃除する (...)
+description: 旧参照例 F26 `docs/failures.md`
...
-復元する。正本は `docs/failures.md` F26。
+復元する。旧正本ポインタは廃止した。
```

**緑。** frontmatter の description が偽 edge になる。body の到達手段は失われている。

```diff
-復元する。正本は `docs/failures.md` F26。
+復元する。旧正本ポインタは廃止した。
+
+[obsolete]: /unused "F26 `docs/failures.md`"
```

**緑。** Markdown の link definition は通常本文として描画されないが、scanner は link definition を除外しない。plan-v2 の「link definition が死ぬ」という断定は、現在の n4 形だけにしか成立しない。[plan-v2.md:80](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/plan-v2.md:80) [tools/check_docs.py:1039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1039)

```diff
-復元する。正本は `docs/failures.md` F26。
+復元する。旧正本ポインタは廃止した。
+
+    F26 `docs/failures.md`
```

**緑。** 4-space indented code blockは scanner によって不可視化されない。scanner が除外する fence・HTML は限定列挙で、それ以外はそのまま返される。[tools/check_docs.py:950](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:950) [tools/check_docs.py:982](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:982)

```diff
-復元する。正本は `docs/failures.md` F26。
+復元する。~~正本は `docs/failures.md` F26。~~
```

**緑。** 描画上は削除された prose だが、strikethrough を認識しないため edge と数える。

さらに通常 prose の否定形、たとえば「`docs/failures.md` F26 は参照してはならない」も**緑**である。これは意味解析をしない構造 lint の限界ではあるが、既知限界として列挙された inline hidden HTML／協調改変とは別である。decision fragment が未検出限界をその2点だけのように記述しているため不整合も残る。[decision fragment:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/spool/decisions/2026-08-11-dev-wave-t675-address-edge-lint-1.md:27)

## 2. 偽陽性

### refuted — 空白なし・全角括弧

次はいずれも**緑**で、偽陽性にならない。

- `正本はF26。(`docs/failures.md`)`
- `正本はF26。（`docs/failures.md`）`

lookaround が ASCII 英数字だけを隣接禁止にしているため、日本語文字・句読点・全角括弧は許容される。[tools/check_docs.py:4077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4077)

### real — 正当な構造的表現を拒否する

```markdown
## F26
正本: `docs/failures.md`
```

これは見出しと本文の階層で一意な edge を表すが、別行なので**赤**。

```markdown
| 項目 | 値 |
|---|---|
| ID | F26 |
| 正本 | `docs/failures.md` |
```

key/value 表として意味は一意だが別行なので**赤**。一方、`| F26 | `docs/failures.md` |` の一行表は**緑**であり、表の意味ではなく物理行への依存で受否が変わる。

```markdown
正本は F26（[docs/failures.md](../../docs/failures.md)）。
```

実際の Markdown link で到達可能性は強いが、backtick code span がないため**赤**。[tools/check_docs.py:4078](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4078)

したがって、「正当な言い換えを殺さない」は一例 p1 に限られ、一般には成立しない。

## 3. 負例 helper と帰属

### refuted — digest finding は隔離される

helper は変更後 command の digest を計算し、合成 repo にコピーされた checker の定数だけを一意置換する。[test_check_docs.py:6717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6717) `_build_min_repo()` は実 checker を合成 repo へコピーしている。[test_check_docs.py:717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:717)

`assert digest != check_docs.CLEANUP_COMMAND_SHA256` は適切である。これは実 repo の hash を期待出力へ焼き込むものではなく、「今回の fixture 変更が実際に再束縛を必要とする」ことの確認である。実定数・合成 command・固定期待値の parity は別テストで固定済み。[test_check_docs.py:6545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6545)

### real — finding の対象 path を検証していない

`_assert_cleanup_address_edge_violation` は generic なメッセージ断片だけを検索し、`.claude/commands/cleanup-branches.md:` prefix を assert していない。[test_check_docs.py:6738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6738)

したがって M6 では dev-wave command に出た finding が cleanup finding の代用品になり、n1〜n4 が誤って通る。これは新 lint 分岐自体は測るが、対象束縛を測っていない real 所見である。

### real — n2 は二重欠陥で過剰決定

n2 は同時に `F26→F260` と exact path の破壊を行う。[test_check_docs.py:6761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6761)

そのため一方の条件だけを緩めても他方が拒否し続け、M2・M3 を kill できない。これはテスト弱体化というより、単一理由性の欠落である。

### refuted — 揮発 payload の焼き込み

期待値に working-tree hash は含まれない。digest は合成 checker 内へ動的に差し込むだけで、stdout の hash 値や現在 checkout 固有値を assert していない。

## 4. 正例 baseline

### refuted — 恒真ではないが完全に重複

`test_cleanup_address_edge_accepts_baseline` は lint の条件反転などで赤くなるため恒真ではない。[test_check_docs.py:6831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6831)

ただし同じ `_build_min_repo()` と rc=0 は既存 `test_synthetic_repo_baseline_clean` が既に固定しているため、純増の検出力はない。[test_check_docs.py:856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:856)

## 5. M1〜M7 の単一理由性

plan-v2 の事前登録は [plan-v2.md:148](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/plan-v2.md:148)。

| 変異 | 判定 | 静的に予測される第一失敗 |
|---|---|---|
| M1 | **成立** | n1。分岐削除後は digest も再束縛済みなので違反が消える |
| M2 | **不成立・SURVIVED** | なし。n2 は path 条件が引き続き拒否 |
| M3 | **不成立・SURVIVED** | なし。n2 は `F260` が lookaround で引き続き拒否 |
| M4 | **成立** | n3。raw HTML 行を `text` が直接数える |
| M5 | **KILLED だが登録誤り** | p2 ではなく n1。反転すると invalid input で finding が消える |
| M6 | **KILLED だが登録誤り** | 焦点 node 順では p1。n1〜n4 は dev-wave finding を誤認する |
| M7 | **成立** | n3。`_visible_markdown_text` は raw HTML block を除かない |

特に M2/M3 は `DW-M01` の「赤理由を一つへ絞る」に違反する重大な事前登録誤りである。M5/M6 は kill 自体は可能だが、記録した第一失敗 nodeid が誤っている。

## 6. frontmatter 手前の挿入

### refuted — 既存の「違反ちょうど1件」テストは壊れない

既存 frontmatter malformed caseは rulings command を変更しており、cleanup 分岐は発火しない。[test_check_docs.py:4855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:4855)

既存 cleanup の件数1テストは frontmatter を壊さず、F26 edge も保持している。[test_check_docs.py:6628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6628)

### real — 挿入位置により frontmatter decoy を edge と数える

前述のとおり、frontmatter を含む文書全体を parser より先に走査するため、metadata 内の共起で body 欠落を隠せる。壊れた cleanup command が edge も欠けば2件出るのは独立違反として妥当だが、valid frontmatter 自体を edge 候補にする現在の位置・入力範囲は不適切である。

## 7. meta-test

### refuted — 6件の登録漏れ・恒真化はない

6つの test 名はすべて登録され、各定義が exact 1 件であることを source count で検査する。[test_check_docs.py:2889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:2889) [test_check_docs.py:2904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:2904)

ただし強制するのは定義の存在・一意性だけで、M2/M3 の生存、finding の対象 path、第一失敗 nodeid は検査しない。この限界は今回の誤登録を実際に通している。

最小修正案:

- n2 を「exact path + F260」と「F26 + archive path」の独立2負例へ分割する。
- helper の needle を cleanup command の完全な prefix 込みにする。
- M5 の第一失敗を n1、M6 を修正後の n1へ更新する。
- frontmatter、link definition、indented code、strikethroughを edge 候補から除く負例を追加する。
- 通常 prose の否定 decoyまで機械排除しないなら、未見の既知限界として再裁定し、decision fragmentへ明記する。

## 総括

M2/M3 は事前登録どおり kill されず、M6 の対象束縛も負例 helper が検査していない。  
さらに frontmatter・link definition・indented code・strikethroughで偽 edgeを作れる。  
既知限界として裁定されていない検出穴であり、現状 land は防壁の錯覚を生む。  
最小修正は独立負例化、path prefix assert、可視本文の範囲修正、限界の再裁定である。  
NO-GO