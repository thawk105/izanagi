# 段 4 裁定 — 登録済み flake hold 3 件の解消

基準: main `e29084e0`。段 2 プラン `verbatim/s2-plan.md`、段 3 `verbatim/s3-sol.md` / `verbatim/s3-luna.md`、
親実測 `parent-measurements.md`。

## 裁定を変えた新事実 (親の実測、段 3 の後)

**hold#1 は負荷依存のフレークではない。決定的な 10 秒の床に、その長さちょうどの上界を置いていた。**

DW-O19 の一時計装で `first.join(...)` から `second.join(...)` までの実所要を測った
(probe: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-flaky-holds-20260826/join-probe.txt`)。

| 走 | 並列度 | 所要 |
|---|---|---|
| 1 | `-n 32` | 10.015 秒 |
| 2 | `-n 32` | 10.014 秒 |
| 3 | `-n 48` | 10.015 秒 |

母集合 = 計算ノードでの `test_pegasus_dispatch_compute.py` 単独 file 走 3 回。
regime は受入全走 (全 file・48 並列) と**同一ではない**。ただし観測されたばらつきは 1 ミリ秒であり、
所要の支配項が負荷でないことはこの母集合でも決まる。

正体は `tools/pegasus/dispatch_compute.py:68` の `DEFAULT_POLL_INTERVAL_S = 5.0` による
実 `time.sleep` が 2 回入ることである。`join(10)` の余裕は **15 ミリ秒**だった。

`dispatch()` は `poll_interval_s` と `sleep` の注入 seam を持つ
(`tools/pegasus/dispatch_compute.py:3687` 以降の signature)。
**同 file の他の 23 箇所は既に `poll_interval_s` を渡している。**
この 2 つの thread テストだけが渡していない (`:5414-5415` と `:5486-5487`)。

この事実は F480 の分類を部分的に覆す。F480 は本 node を
「絶対 wall-clock を assert するテストが受入全走の並列負荷で非再現の赤になる」族に入れたが、
負荷は引き金であって支配項ではない。**修理は timeout の拡大ではなく、
既に存在する注入 seam を使って決定的な 10 秒を消すことである。**

## 所見の裁定

### sol-1 — hold#1 の撤去根拠不足: **real / 採用 (ただし処方を変える)**

主張は正しい。`join(60)` は絶対 wall-clock の上界のままで、単独走を基準にした倍率は
適用先 regime の上界にならない。sol の「倍率で語ること自体が誤り」も支持する。

ただし sol の処方 (event 観測 + 外側 subprocess の長い watchdog) は採らない。
上の実測が示すとおり、支配項は scheduling ではなく production 側の固定 poll である。
**処方は `poll_interval_s` の注入。** 同 file の既存 23 箇所と同じ形であり、新奇な設計ではない。

- 採用する変更: `:5414-5415` と `:5486-5487` の 2 テストの `DC.dispatch(...)` 呼び出しへ
  `poll_interval_s` を短い値で渡す。値は「注入後の実所要 max への倍率」で決め、
  母集合と regime を comment に併記する (DW-O13)。
- `join(...)` の bound は残すが、**合否の latency 予算ではなく hang 回収の watchdog** として
  comment に明記する。注入後は決定的な床が消えるので、bound と実所要の比は桁で開く。
- 性質の assertion (`results`、qsub 回数、`_orphan_hold_present` 不在、
  `submission-disabled.json` の実在) は 1 つも減らさない。
- 注入後の実所要は段 5 の実装子が測れないので、**親が段 6 で実測して値を確定する**。

pytest-timeout は environment に無い (親が確認済み) ので、bound 無しの `join()` は採らない。
hang が受入全走 1 本を丸ごと潰す。

### sol-2 — directory metadata 正規化が一時作成後削除の検出を捨てる: **real / 採用 (設計を変える)**

主張は正しい。ただしプランの「全 directory で一律に正規化する」は採らない。

プランが動的判定を退けた理由は「before では候補が無く after では候補が増えるので、
正規化対象自体が変化する」だった。**これは (D-a) 修理前の前提である。**
(D-a) を規則由来へ直すと、除外 prefix は実在に依存しなくなり、
**その祖先集合も before / after で不変になる。** プランの反論はこの wave の中で解消する。

採用する設計。

- 規則由来の ignored prefix の**祖先である directory** (root を含む) だけ、
  `st_size` / `st_mtime_ns` / `st_ctime_ns` を正規化する。
- wildcard 規則 (`output/variants/*/bin/`) は、最初の wildcard より手前の静的 prefix
  (`output/variants`) 以下の subtree 全体を祖先扱いする。保守側に倒し、規則 bytes からだけ導く。
- それ以外の directory は timestamp を保持する。`output/insights`、`output/campaigns` などは
  検出力が落ちない。
- **この設計は、これまで存在しなかった positive control を可能にする。**
  祖先でない directory での「git-visible な一時作成 + 削除」が赤になることを検査できる。
  段 5 はこの control を必ず足す。docstring の主張が初めて独立に検証される。
- 祖先の導出が規則由来かつ before/after 不変にできないと段 5 が判断した場合だけ、
  一律正規化へ退避してよい。その場合は docstring を永続状態の主張へ狭め、
  失われる検出力を新規タスクへ起票する。退避したことを報告に明記する。

sol の指摘どおり、既存 docstring の主張は変更前から独立検証を持たない。
これは本 wave が壊すものではない。区別して記録する。

### sol-3 — hold#3 の順序強制に決定的な negative control が無い: **real / 採用**

`hookwrapper` の decorator を外す、記録を `yield` の後へ動かす、の 2 変異が決定的に赤になる
control を足す。実 xdist を待つのではなく、pluggy 層で直接呼ぶ形にする。

### sol-4 / luna-6 — 台帳の closure と再発時の分類手順: **real / 採用**

- F136 に hold#2 の修理内容・解消 commit・撤去日・再導入 node を追記する。
- F480 に hold#1 の真因訂正 (決定的な 10 秒の床であって負荷依存ではない)、
  `639f2f28` と本 wave の修理、hold#1 / hold#3 の撤去日を追記する。
  **F480 の族定義そのものを訂正する必要がある** — 本 node は族の例として不適切だった。
- luna の 6 段の分類手順を worklog へそのまま残す。

### luna-1 — wildcard 規則の実在依存が残る: **real / 部分採用**

wildcard を存在前に有限展開することはできない。残ることを認め、
**contract test で「literal directory 規則は実在に依存しない」ことだけを pin する**。
wildcard が実在依存であることを helper の docstring に明記する。
「実 repo の prefix を任意の `tmp_path` へ適用する」設計の歪みは既存であり、本 wave の scope 外。新規タスクへ。

### luna-2 — exclude source の列挙と linked worktree の `.git`: **real / 採用**

本 checkout は linked worktree で `.git` は file である。`repo_root / ".git" / "info" / "exclude"`
を directory 前提で読む実装は成立しない。`git rev-parse --git-path info/exclude` で解決する。
候補生成の source は次に限定し、helper の docstring に列挙する。

- repository root の `.gitignore`
- `git rev-parse --git-path info/exclude` が返す path
- `git config --get core.excludesFile` (未設定なら省略)

`output/` 配下の規則を持たない source は候補ゼロで通る。source を増やす改訂は再裁定を要する。

### luna-3 — `git check-ignore` の 3 分岐契約: **real / 採用 (親の実測を正本とする)**

親が実測済み (`parent-measurements.md` の M7 / M8)。

- rc=0: 1 件以上一致。stdout の NUL 区切り集合が答え。入力候補の部分集合であることを検査する。
- rc=1: 一致なし。stdout 空を要求。
- その他 (rc=128 等): Git error として fail-closed。
- **directory 規則由来の候補は末尾スラッシュを付けて問い合わせる。** 付けないと
  `check-ignore` 自身が directory の実在で答えを変え、修理が黙って無効になる (M7)。

### luna-4 — `--no-index` が force-add された tracked descendant を隠す: **real / 採用**

規則由来 prefix ごとに `git ls-files --cached -- output/<prefix>` が空であることを検査し、
空でなければ fail-closed にする。

### luna-5 — `output/task-runs/` 経由の F136 型が残る: **real / scope 外**

親が裏取りした。`output/task-runs/` は tracked (24 file) で git-visible、
`output/task-runs/reports` にも tracked file が 1 つある。並行 shard がここへ書く。
除外集合の直し方では消えない。writer を repo 外へ移すのが恒久解で、
`tools/run_tests.py` と `tools/task_runs/aggregate.py` の配線変更を伴う。

**hold#2 の node を戻すと、この経路の偽赤に晒される。** ただしこれは新しい危険ではない —
`test_s8b_floor_campaign.py` の非 hold な snapshot 検査が既に同じ経路に晒されている。
hold#2 を登録したままにする害 (fail-closed 境界が受入から外れ続ける) のほうが大きい。
**撤去する。** 残余 risk は新規タスクへ起票し、luna の分類手順で扱う。

### プラン E (P1) の hold source digest 機構: **不採用 / 設計メモへ**

DW-G04 に従う。3 行を撤去すると registry は空になり、この機構は**発火条件を満たす
既存 artifact path も計測 ID も無い**。次に誰かが hold を登録するまで死んだコードになる。
validator への field 追加、contract test 約 8 箇所、`docs/decisions.md` の D697 追補
(「受理条件は 6 つ」が不正確になる) というコストに対し、本 wave 中に発火しない。

代わりに設計メモ (`p1-stale-hold-detection.md`) を残し、新規タスクへ起票する。
**次に hold を登録する wave が、登録と同じ commit でこの field を導入する**という
条件付き導入にする。DW-G04 の「書けなければ設計メモに留める」に該当する。

### プラン D (helper 共通化): **不採用 (プランの推奨を支持)**

`test_s8b_floor_campaign.py` の helper は構造が違い、独立 oracle も持つ。
共通化は編集面を広げ、並行 wave との競合面を増やす。逐語同一の 2 helper へ同じ変更を当てる。

## 変更面 (実アンカー)

| file | 変更 |
|---|---|
| `orchestrator/tests/output_snapshot_ignores.py` | 規則由来の候補生成、末尾スラッシュ付き `check-ignore`、3 分岐 rc、tracked descendant 検査、祖先集合の公開 |
| `orchestrator/tests/test_s8b_oracle_driver.py` | `_t080_output_snapshot` の選択的正規化、negative control の順序、`runs-visible` positive control、非祖先 directory の一時作成後削除 control |
| `orchestrator/tests/test_real_repo_serialization.py` | 同上 + hold#3 の pluggy 層 negative control |
| `orchestrator/tests/test_s8b_floor_campaign.py` | negative control の順序、`runs-visible` positive control (helper 本体は不変) |
| `orchestrator/tests/test_pegasus_dispatch_compute.py` | `:5414-5415` と `:5486-5487` の 2 テストへ `poll_interval_s` 注入、bound を watchdog と明記 |
| `orchestrator/tests/flaky_test_holds.py` | `_FLAKY_TEST_HOLD_ROWS` を空にする |
| `orchestrator/tests/test_flaky_test_holds_contract.py` | live registry 依存 3 test の書き換え |

## 段 5 の所有分割 (file 重複なし)

- **子 A (snapshot 族)**: `output_snapshot_ignores.py`、`test_s8b_oracle_driver.py`、
  `test_real_repo_serialization.py`、`test_s8b_floor_campaign.py`
- **子 B (hold 族)**: `flaky_test_holds.py`、`test_flaky_test_holds_contract.py`、
  `test_pegasus_dispatch_compute.py`

統合順序は子 A を先にする。未修理の hold#2 が先に受入へ戻ることを避ける。

## 変異事前登録 (DW-M01)

実装後に確定する。登録候補と、無効化時の赤理由が一つに絞れることの確認は段 6 で行う。
本 wave は受理集合を**広げる** wave なので、`DW-M01` の「受理集合を縮小する wave」条項は
直接は当たらないが、除外集合を広げる (D-a) 側は縮小に当たるため、
承認外の過剰拒否を検出する正例 (`runs-visible`) を登録する。

---

# 裁定の訂正 (段 5 の実装子 A の報告と親の実測による)

## 訂正 1 — luna-4 の採用形が誤りだった

裁定は luna-4 を「規則由来 prefix 配下に tracked entry があれば fail-closed」で採用した。
**これは本 repository では成立しない。**

実装子 A が実装して報告し、親が現物で確認した。

- `.gitignore:24` の `output/env/pegasus/silo_ladder_rung1/job-staging/` 配下に
  **tracked file が 418 個ある** (`git ls-files -- output/env/pegasus/silo_ladder_rung1/job-staging | wc -l` = 418)。
- 統合後の焦点走で、`test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary` が
  `AssertionError: 規則由来 ignored prefix 配下に tracked entry がある: output/env/pegasus/silo_ladder_rung1/job-staging`
  で赤になった (1 failed / 3 passed / 6.82 秒)。

**正しい semantics は fail-closed ではない。** Git の ignore 規則は tracked file には適用されない。
したがって除外側も tracked path を隠してはならない。

- 変更前の `git ls-files -o -i --directory` は、tracked file を含む directory を
  collapse できないため `job-staging` を返さなかった。**418 file は今まで snapshot から見えていた。**
  規則由来 prefix にすると、この 418 file が隠れる。これが luna-4 の本当の害である。
- 正しい修理は「tracked path とその祖先 directory を除外対象から外す」。
  fail-closed は、実在する正当な状態を検査不能にするだけで、
  隠蔽の害を 1 bit も減らさない。

段 6 の fix でこの形へ直す。tracked 集合の取得コストは段 6 レビュー B の
subprocess コスト観点と一緒に評価する。

## 訂正 2 — hold#1 の処方を、poll 短縮から偽 clock 注入へ寄せる

実装子 B は `poll_interval_s=1` を注入し、10 秒の床は 2 秒へ下がった
(焦点走 4 node が 6.82 秒。以前は当該 1 テストだけで 13.5 秒)。

しかし親が同 file を読み直したところ、**この file の標準 helper `_dispatch()`
(`test_pegasus_dispatch_compute.py:222-253`) は偽 clock と `sleep=clock.sleep` を注入している。**
他の call site が `poll_interval_s=5` でも一瞬なのはそのためで、実時間は進まない。
問題の 2 テストだけが `_dispatch()` を通さず、実 clock・実 sleep で `DC.dispatch()` を直接呼んでいる。

`_acquire_control_lock` (`tools/pegasus/dispatch_compute.py:1414-1427`) は
blocking `flock(LOCK_EX)` であり poll ループを使わない。thread 間の協調は
`threading.Event` が担っている。したがって**偽 clock を注入しても協調は壊れない。**
poll ループが待っているのは偽 `_Scheduler` の状態遷移だけである。

段 6 の fix で `clock=_Clock()` と `sleep=clock.sleep` をスレッドごとに注入する形へ寄せる。
実時間の床が消えるので、`join(...)` の bound は純粋な hang watchdog になる。
偽 clock で scenario が壊れると判明した場合だけ `poll_interval_s=1` のまま据え置き、
その事実を報告に明記する。

あわせて、`join(10)` と `join(60)` の不一致を解消する。両方に「watchdog」と書いてありながら
値が 6 倍違うのは根拠が無い。
