# [T-1621] 受入 suite の順序依存 — 静的棚卸しと負の対照の実測

`authority: none` / `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本文書は探索の妥当性文書
(measurement record) であり、裁定台帳ではない。

- 起点: `docs/archive/worklog-phase3-0824-886-887.md` entry 887 の T-1621、裁定正本 D746 / D747、
  失敗台帳 F515 / F516 / F517。
- 測った checkout: branch `worktree-dev-wave-t1621-suite-order-dependence`、base `0d23466f`。
- 実行環境: Pegasus (計算ノード dispatch と login node の両方)。pytest 9.1.1 / pytest-xdist 3.8.0。

---

## 1. なぜ測ったか

D746 が受入全走の work unit 投入順を所要降順へ変えた。D746 自身が
「順序を変えれば順序依存のテストは緑と赤が入れ替わりうる」「潜在的な順序依存があれば
受入全走が赤になって露見する」と書いている。**露見を待つのではなく先に測る**のが T-1621 である。

この repo で順序依存を検出する既存手段は**受入全走 1 本だけ**であり (F517 の再発検知)、
しかも D746 が確定させた 1 つの順序しか踏まない。

---

## 2. 最大の構造的発見 — D746 は直列連鎖の内部順を 1 つも変えていない

`orchestrator/tests/conftest.py:947 _reorder_acceptance_items_by_duration` の実装は
**work unit 単位**の並べ替えである。unit を作り、unit ごとの所要合計で降順に並べ、
`reordered = [item for unit in ordered_units for item in unit["items"]]` と展開する。
**unit 内の item は連続かつ元の相対順のまま**動く (D746 の決定 4 が明記する契約でもある)。

`--dist loadgroup` では ungrouped node が 1 件 = 1 work unit になる
(`xdist/scheduler/loadgroup.py::_split_scope`、xdist 3.8.0 で確認)。したがって
**「unit 内順序」が存在するのは `xdist_group` marker を持つ node だけ**である。

権威ある group 名は 3 つだけである
(`orchestrator/tests/test_real_repo_serialization.py:125 _XDIST_GROUP_NAMES_GOLDEN`)。

| group | 宣言 | collection 上の node | 台帳直列所要 |
|---|---|---|---|
| `real-repo` | `conftest.py:338 REAL_REPO_SERIAL_NODES` 69 件 | 72 | 102.6 秒 |
| `s8c-preregistration-candidate` | `test_s8c_preregistration_invariant.py:30` | 5 | — |
| `dev-waves-runtime` | `test_dev_waves_integration.py:838` ほか | 12 | — |

**結論: D746 の受入緑は、この 3 連鎖の順序依存について証拠になっていない。**
しかも `real-repo` こそが、suite で唯一「親 repo status と共有 submodule」という
可変共有状態を触る集合である (`conftest.py:335` の宣言どおり)。
事前確率が最も高い場所が、そのまま唯一の未検査面として残っていた。

---

## 3. 順序独立性は設計されている (ただし「証明」ではない)

conftest には既知の共有状態を隔離する機構が 4 つある。**これらは隔離機構であって、
suite の順序独立性の証明ではない。**各機構には発火しない条件がある。

| 機構 | 守る範囲 | 発火しない条件 |
|---|---|---|
| `REAL_REPO_SERIAL_NODES` (`conftest.py:338`) | 単一 pytest invocation 内で、手登録された親 repo / 共有 ccbench 利用 node を 1 work unit へ閉じ込める | 未登録 node、collection / import 時、別 invocation、子 process、新 thread、loadgroup 以外。既存の別 `xdist_group` があれば marker を追加しない (`:1317-1323`) |
| `REAL_REPO_EXECUTION_PRIORITY` (`conftest.py:469`) | real-repo slot 内で 2 node を先頭へ固定 | 同一 group でなければ実行直列を保証しない。**さらに下記 5 のとおり 2 node とも既定で skip される** |
| receipt memo prewarm (`conftest.py:477`, `:1420`) | 登録 33 関数 / 36 node の memo を test scheduling 前に controller が 1 度だけ用意し `workerinput` で配る | consumer registry 外、collect-only、controller metadata 取得不能 |
| autouse 隔離 3 本 (`conftest.py:521`, `:537`, `:550`) | task-run 記録 env 4 名と layout の process pin 2 種を**毎テストの前と後**で戻す | collection / import 時、他の env / cwd / `sys.path` / `sys.modules` / cache、子孫 process、共有 filesystem |

`orchestrator/tests/real_repo_receipt_memo.py:597 _ReceiptMemo.get()` は **一切書かない**。
prewarm 済み process state か既存 session cache だけを読み、無ければ `cache-missing` で
fail-closed する。**「最初に走ったテストが書き手になる」意味論が設計から消してある。**
T-1621 の依頼が挙げる「共有 output tree の first-writer 判定」は、少なくともこの経路については
実在しない。

`orchestrator/campaign/patchharness.py:315 _guard_real_shared_checkout` は、
`REAL_REPO_SERIAL_NODES` 未登録の pytest node が実共有 submodule を checkout しようとすると
RuntimeError で fail-closed する live positive control である。**ただし守るのは `checkout()` の
1 callsite だけ**で、`_PYTEST_NODE` が無ければ無条件 return する。collection / import 時、
子 process、新 thread、直接 git、`applied()` は guard 外である。

---

## 4. 負の対照 — grouped 連鎖 3 本すべてを反転した

### 方法

pytest は argv に並べた nodeid の順をそのまま collection 順にする。全 node が同一 group なら
work unit が 1 個になり、D746 の並べ替えは unit 内順序を保存するので、
**argv 順がそのまま実行順になる。** これを仮定にせず、junit XML の testcase 出現順で毎回検証した。

`tools/run_tests.py` は targeted 走にも既定で `--dist loadgroup` を付けるので、
**ungrouped な 2 node の AB / BA は D746 に所要降順へ潰される** (段 3 の敵対 2 レンズが独立に指摘)。
本 wave が grouped 連鎖だけを対照に採ったのはこのためである。

### 結果

| 連鎖 | node | 実行 | 実行順の逆転検証 | outcome 差 |
|---|---|---|---|---|
| `real-repo` | 72 | 31 (skip 41) | 優先 2 node を除く 70 node が完全逆転。位置ずれ平均 35.3 (完全逆順の理論値 35.0) | **0** |
| `s8c-preregistration-candidate` | 5 | 5 | 完全逆転 | **0** |
| `dev-waves-runtime` | 12 | 12 | 完全逆転 | **0** |

`real-repo` の正順は 2 回走らせ、**計算ノード (222.28 秒) と login node (312.62 秒) で同一 outcome**
(31 passed / 41 skipped) だった。実行 venue と worker 数を跨いで再現している。

優先 2 node が逆転しないのは設計どおりである。`pytest_collection_finish` の
`_prioritize_real_repo_items` (`conftest.py:1400`) が `REAL_REPO_EXECUTION_PRIORITY` の 2 node を
real-repo slot の先頭へ常に戻すためで、`conftest.py` を編集しない限り反転できない。

### positive control — 検出網が実在する順序依存を捕まえることの証明

「全部緑だった」に意味を持たせるには、その測り方が実在する順序依存を検出できる証明が要る。

- 対象: `s8c-preregistration-candidate` group の 2 node
  (`test_candidate_freeze_matches_contract_and_generation_chain` と
   `test_candidate_freeze_batch_is_bounded_by_frozen_touch_points`)。どちらも hold されていない。
- 一時注入: module global `_T1621_ORDER_PROBE = False` を足し、前者の先頭で `assert ... is False`、
  後者の先頭で `global` して `True` にする。
- 結果: **A 単独 = 1 passed / A→B = 2 passed / B→A = A が赤**
  (`IZANAGI_FAILURE rank=1 category=failed when=call nodeid="...
   test_candidate_freeze_matches_contract_and_generation_chain@s8c-preregistration-candidate"`)。
- tracked file の一時変異は同 wave 内で復元した。復元後の `git hash-object` は
  `git rev-parse HEAD:<path>` = `dff5e4635795c39e084555b4e9b547efcf52e285` と一致する。

**この positive control が証明するのは「同一 group・同一 worker 内の module global 漏れを
検出できること」だけである。** worker 跨ぎ、ungrouped、collection / import 時の面には別の
control が要り、本 wave では作っていない。

---

## 5. 検出力の限界 — real-repo 連鎖は 43% しか走っていない

`real-repo` 72 node の junit を数えた実測。

| 状態 | 件数 |
|---|---|
| 実行 (passed) | **31** |
| `GROWTH_TEST_HOLDS` による skip | 34 |
| 条件付き未実走 (template patch 未適用) | 4 |
| slow real-build canary | 3 |

growth hold は `correctness_gate: true` かつ `release_condition: explicit-user-command-only` である。

**`REAL_REPO_EXECUTION_PRIORITY` の 2 node は両方とも growth hold で skip される。**
すなわち、repo が唯一明示的に認めている順序依存は、既定の受入では発火していない。

---

## 6. 方法論の教訓 — この repo で grep は文字列リテラル内のコードを実コードと誤認する

本 wave で親が grep 起点に立てた主張が **3 回**、同じ機序で誤っていた。
この repo は生成する子スクリプトや内側 pytester 用 suite を三重引用符の文字列として持つため、
`grep` はその中の `@pytest.fixture(scope="module")` や `os.environ[...] = ...` を実コードとして拾う。

| grep が挙げた箇所 | 実体 |
|---|---|
| `test_acceptance_schedule_order.py:566` の `scope="module"` fixture | 内側 pytester 用 suite の文字列 |
| `test_mutation_harness.py:65` の `scope="session", autouse=True` fixture | 一時 git repo へ書き出す template 文字列 |
| `test_campaign_import_invariant.py:1385` の `os.environ["PYTHONPATH"] = ...` | 生成子スクリプトの文字列 |
| `test_buildcache_v2.py:2215` の `os.environ["PATH"] = ...` | 生成子スクリプトの文字列 |

AST (`ast.parse` + `walk`) で数え直すと、外側 suite の実 scope fixture は **9 件**であり、
すべて `autouse=False` で、いずれもテストが変更しない共有外部状態の読み取り snapshot である
(repo scan、`decisions.md` の bytes、submodule から作る known-axes 文書、git commit snapshot、tmp)。

**在否を数える走査は AST で行う。grep の hit 数を inventory として使わない。**

---

## 7. 測っていないこと (未判定として明記する)

1. **ungrouped 15063 node の順序依存。** 1 node = 1 unit なので「unit 内順序」が存在しない。
   その順序依存は unit 間 / worker 跨ぎの型であり、本 wave では測っていない。
   targeted AB / BA は D746 に再整列されるため、実装ゼロでは作れない。
2. **worker を跨ぐ overlap 依存。** 共有 submodule の apply / revert 窓
   (`patchharness.py:246-263`。flock は writer 同士だけを直列化し、lock を取らない reader とは競合する)、
   patch lock、`/tmp` の memo 2 種 (`real_repo_receipt_memo.py`、`sort_swo_oracle_receipt_memo.py`)、
   外部 process / socket。serial 対照では原理的に踏めない。
3. **held-out 41 node。** growth hold 34 件の release は明示ユーザー裁定が要る。
4. **collection / import 時の順序依存。** D746 は collection hook の post-yield で初めて順序を変える。
   その時点で全 test module は import 済みなので、import 順は摂動されない。
5. `REAL_REPO_EXECUTION_PRIORITY` の 2 node を含む edge は、`conftest.py` を編集しない限り反転できない。

---

## 8. 撤回した親の主張 (記録として残す)

親は当初「D746 の land 時の受入全走が、既にほぼ最大の順序変更に対する負の対照として成立していた」
と主張した。素の collection 順 15152 node と台帳による所要降順を突き合わせ、
正規化平均位置ずれ 0.315 を根拠にした。**この強い形は撤回する。**

- 測定に使った `--collect-only` は D746 の並べ替えを**明示的に無効化する**
  (`conftest.py:999 _acceptance_options_allow_reordering` が `collectonly` で False を返す)。
  よって得た順序は「実 D746 後の順」ではない。
- 実装は item 粒度ではなく unit 粒度である。未知の擬似 cost も「第 96 位の既知 **unit**」であり、
  親が使った「第 96 位の既知 item = 6.30 秒」とは別の量である。
- 正規化平均絶対変位は完全逆順で約 0.5、ランダム置換で約 0.333 である。
  0.315 は「ランダム置換とほぼ同じ」であって「ほぼ最大」ではない。
- 直接 `python3 -m pytest` で採った集合は canonical な受入 collection と一致しない。

**書けるのは「非 canonical な collect-only 集合に item 粒度の offline proxy を当てた距離が
0.315 だった」までである。** 一方、2 の構造的発見 (unit 内順序が保存される) は proxy ではなく
実装から出ているので、そのまま残る。

---

## 9. 還元判断

CCBench への還元候補ではない (izanagi 側の受入 harness の話である)。
**還元判断: 該当なし。**

scope 外と裁定した real 所見は `docs/worklog.md` の当該エントリと次の一手へ送る。
