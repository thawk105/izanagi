# 親が段 2 後に追加で取った実測値 — 段 3 の 2 論点を数字で詰める

段 2 のプランが親 brief へ出した異議のうち、2 件は数字がなければ裁定できない。親が測った。

## 論点 1 — 登録簿 scan の費用と成長の傾き

プランの異議 4:「repo 外 literal の完全走査も file 数比例であり、D335 と形式上衝突する」。

**決定的な先例を親が見つけた。** `orchestrator/tests/test_campaign_import_invariant.py` は
repo 全体の source を走査する既存テストだが、**`growth_test_holds.py:271-291` で 6 node が
恒久保留になっている。** つまり repo 全体走査は D335 により既に「保留すべき構造」と裁定済みで、
新設すれば同じ扱いになる。

そのうえで、提案されている scan の実費用を測った
(`python3 measure_scan_cost.py <worktree>/orchestrator/tests <worktree>/orchestrator/campaign 5`)。

```
test files total         : 345
files parsed after prefil: 16
distinct (module,literal): 19
scan best-of-5           : 0.610 s
```

- 字句 prefilter (`/home/`, `/work/`, `~/`) が効き、**345 file 中 16 file しか `ast.parse` しない。**
- distinct な `(module, literal)` は **19 件**で、プランの静的確認と一致した。
- 費用 0.610 秒の大半は 345 file の `read_text` であり、これが成長項である
  (約 1.8 ms / file)。5 秒に達するには test file が約 2800 本必要になる。
- **決定的な違い:** この scan は pytest の 1 test として **1 走に 1 回、1 worker で**払われる。
  単位 A の 3.44 秒とは違い、collection ではないので 48 worker x 3 shard に掛からない。

## 論点 2 — 構文検査の検出力低下は何 module 分か

プランの異議 2:「marker のない構文不正 file を現行だけが落とす」。

campaign module 186 本のうち、test suite の source のどこかに名前が現れるものを数えた。

```
campaign modules        : 186
named anywhere in tests : 183
never named in tests    : 3
    p2_5
    s6_amendment_20260713_fence
    s6_proposal_rounds_power
```

さらにこの 3 本が他の campaign module から参照されているかを引いたところ
(`grep -rln` で `orchestrator/campaign/*.py` を検索)、**自分自身の file しか hit しない。**

したがって:

- **prefilter が失う構文検査は、正確にこの 3 module 分だけである。** 残り 183 本は
  test suite のどこかで名前が挙がっており、import 経路があれば import 時に構文検査される。
- 逆に言えば、**この 3 module は test suite から一度も名指しされていない。**
  現在それらを parse している唯一の実行体が `test_p3_exploration_namespace.py` の
  187 file 全 parse である。これは prefilter とは独立に報告すべき被覆の穴である。

## 帰結 (親の provisional 裁定。段 4 で確定する)

- 論点 1: scan は 0.610 秒・1 走 1 回で、単位 A が消す費用とは桁も回数も違う。
  ただし構造は file 数比例であり、既存の同型テストは保留されている。
  **repo 全体走査を新設する形は採らず、走査対象を絞るか、費用の性質を明記して裁定へ返す。**
- 論点 2: 失う検出力は 3 module 分で、その 3 本はそもそも test から名指しされていない。
  **prefilter の採用を止める理由にはならないが、3 module の被覆の穴は次の一手として起票する。**
