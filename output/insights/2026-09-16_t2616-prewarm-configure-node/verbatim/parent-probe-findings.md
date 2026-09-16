# 親が実測・現物確認した事実 (段 3 以降の子へ射影する)

## 0. 段 2 の plan が反証した親 brief の前提 (訂正、2026-09-16 11:00)

段 2 の plan 子が現物で 2 件を反証した。**訂正後を正とする。**

1. **brief の (P2) は偽である。** insight README:51-57 は「shard-1 / shard-2 で
   `IZANAGI_MEMO_PREWARM_V1` の barrier が 0.09 / 0.12 秒だったのは **consumer が不在**のため」と
   記録している。つまり「受入 shard 走なら consumer は必ず居る」は成立しない。
   受入 shard 走であることを発火条件にすると、**consumer 不在の shard-1 / shard-2 でも
   28.3 秒相当の解決が走る**。その wall 影響は実測しなければ分からない
   (collection と重なって 0 になる可能性も、最遅 shard が入れ替わる可能性もある)。
2. **brief の (P3) が書いた「`test_memo_barrier_*` は 10 本」は誤りで、現物は 9 本である**
   (T:4712 / 4724 / 4734 / 4777 / 4787 / 4827 / 4845 / 4858 / 4877)。
   親の grep の数え違いであり、10 本目は存在しない。**存在しない test を根拠にしないこと。**

さらに plan は、親が項 4 で書いた読解とは別の、**コードから証明できる退行**を挙げた。
`pytest_configure_node` の冒頭に「spec が無ければ return」を置くと、**非受入 probe への
nonce 伝播まで飛ぶ**。その結果 worker 側の必須読取り (C:2603 / C:2660) が `UsageError` を
送出する。これは「probe の入れ子 xdist 走行で worker が crash する」という前 wave の (b) の記述と
形が一致する。**ただし前 wave がその実装をしていた証拠は無い** — 有力候補であって同定ではない。


すべて 2026-09-16、base commit 262c2993e、worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2616-prewarm-configure-node` で確認した。
**実測**と**現物読解**を区別して書く。

## 1. 発火条件は時点として成立する (現物読解)

`tools/acceptance_shards.py:873-891` の `pytest_configure` が
`setattr(config, "_izanagi_acceptance_shard_spec", spec)` を行う。spec の出所は
`_plugin_spec()` (:797-814) で、環境変数 `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1`
(`PLUGIN_SPEC_ENV`, :51) を読む。

xdist 3.8.0 の実体
(`/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/`) では
`dsession.py:83` の `DSession.pytest_sessionstart` が `:90` で
`self.nodemanager.setup_nodes(...)` を呼び、`workermanage.py:325` の
`WorkerController.setup()` が `:342` で `self.config.hook.pytest_configure_node(node=self)`
を呼ぶ。`pytest_configure` は `pytest_sessionstart` より前なので、
**`pytest_configure_node` の時点で shard spec は必ず読める。**

## 2. plugin は argv で載る。env だけでは載らない (現物読解)

`tools/run_tests.py:1499` が shard 子の argv へ `-p tools.acceptance_shards` を入れ、
`:1517` が同じ子の env へ `PLUGIN_SPEC_ENV` を入れる。
`orchestrator/tests/conftest.py` は env を直接読まず `getattr(config,
"_izanagi_acceptance_shard_spec", None)` だけを見る (:1485, :2067, :2118)。

**したがって、argv を継がない入れ子 pytest では spec は None になる。**
env だけ継いでも conftest 側の判定は False のままである。

## 3. probe の入れ子 xdist 走行の実体 (現物読解)

`orchestrator/tests/test_real_repo_serialization.py:5041`
`test_receipt_memo_real_xdist_order_has_no_worker_payer`。

- `pytest -n 1 -q -p orchestrator.tests.conftest -p receipt_order_plugin <合成 test>` を
  **cwd=ROOT (実 repo)** で subprocess 起動する。
- 合成 plugin は **`pytest_sessionstart` の中で** `suite_conftest._receipt_memo_module`
  を `FakeMemo` へ差し替える。
- trace に対し `prewarm-controller` がちょうど 1 回、`prewarm-worker` が 0 回、
  `worker-hook` が `controller-hook` より前、を要求する。
- env は `PYTEST_XDIST_WORKER` / `PYTEST_XDIST_WORKER_COUNT` /
  `PYTEST_XDIST_TESTRUNUID` / `IZANAGI_RECEIPT_MEMO_NONCE` の 4 つだけ pop する。
  **`IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1` は pop しない** (項 2 により、argv に
  `-p tools.acceptance_shards` が無いので spec は立たないが、env は継承される)。

## 4. 【訂正・撤回】この項の結論は誤りだった (2026-09-16 11:20)

**下の項 4 の結論は誤りである。段 3 の相談 A が反証し、親が現物で確かめて追認した。**

`DSession.pytest_sessionstart` には **`@pytest.hookimpl(trylast=True)` が付いている**
(`xdist/dsession.py:82`)。pluggy は trylast の impl を list の**先頭**へ挿入し
(`pluggy/_hooks.py:464` の `self._hookimpls.insert(start, hookimpl)`)、`_multicall` は
`reversed(hook_impls)` で回す (`pluggy/_callers.py:93`)。したがって **trylast は最後に呼ばれる**。

**正しい順序は「probe plugin の `pytest_sessionstart` (FakeMemo 差し替え) →
`DSession.pytest_sessionstart` → `setup_nodes()` → `pytest_configure_node`」である。**
差し替えは間に合う。親は「登録順の LIFO」だけを見て `trylast` を見落とした。

**よって (b) の機序として親が挙げた候補は撤回する。** 残る code-proven な候補は、
段 2 plan と相談 A がともに [real] とした「`pytest_configure_node` 冒頭の早期 return が
nonce 伝播ごと飛ばし、worker が `conftest.py:2603` / `:2660` で `UsageError` を投げる」である。

以下は撤回した読解の原文である (記録として残す)。

## 4. (撤回済み) 差し替えは `pytest_configure_node` に間に合わない (現物読解)

xdist の `dsession` は `plugin.py:278` の `pytest_configure` の中で
`config.pluginmanager.register(session, "dsession")` により登録される。
`-p receipt_order_plugin` は config 初期化時に載るので、**登録は dsession より先**である。
pluggy は tryfirst/trylast の指定が無い限り**後から登録した plugin の hook impl を先に呼ぶ**
(LIFO) ので、`DSession.pytest_sessionstart` は `receipt_order_plugin.pytest_sessionstart`
**より先**に走る。

**帰結: prewarm を `pytest_configure_node` へ移すと、この probe では FakeMemo が入る前に
起動する。** 差し替え seam が効かず、入れ子走行の中で本物の resolver が実 repo を解決しにいく。
これが前 wave の (b) の赤 2 件の有力な機序である。**ただしこの因果自体はまだ実走で確かめていない
(読解である)。**

## 5. 同期実行は node setup を止める (現物読解、未実測)

`pytest_configure_node` は `setup_nodes()` の中から node ごとに**同期的に**呼ばれる。
ここで prewarm を同期実行すると worker の起動列が止まる。
依頼文が「**barrier を外す**」「**worker 側は cache を最大 120 秒待ち `.pending` / `.failed`
marker で失敗を共有する**」と書いているのは、**起動だけを collection 前に置き、待ちは worker 側へ
移す**という設計であることを示す。`pytest_configure_node` の中で完了まで待つ形ではない。

## 5b. prewarm の実測所要と 120 秒の根拠 (前 wave の実測、一次資料 = insight README)

前 wave が計測行から採った内訳は次である (受入 shard-0、走 F)。

```
IZANAGI_MEMO_PREWARM_V1 {"barrier_s":28.329, "hook":"xdist_node_collection_finished",
                         "oracle_environment_memo_s":0.132, "receipt_memo_s":28.328}
```

**receipt 側の prewarm 実所要は 28.328 秒**、oracle 側は 0.132 秒。
insight の「215 対 1」は**秒ではなく両者の比**である (28.328 / 0.132 ≒ 215)。

よって暫定の 120 秒は **実測 max 28.33 秒の約 4.24 倍**にあたる。母集合は受入 shard-0 の
1 走 (n=1)。観測 regime は「受入全走の shard-0、48 worker、lustre 上の実 repo」で、
適用対象と同じ regime である。**n=1 なので分布の裾は未知**であり、段 2 / 段 3 はこの点を
攻撃対象にしてよい。

## 5c. なぜ collection 前でなければ効かないか (前 wave の実測、決定的)

| 走 | 構成 | wall | 開始待ち | 実行窓 | 最長単体 |
|---|---|---|---|---|---|
| F | barrier あり (現行) | 307.9 秒 | 25.5 秒 | 220.6 秒 | 212.6 秒 |
| G | barrier 撤去、**collection 後**に背景化 | 320.0 秒 | 0.1 秒 | **256.7 秒** | 247.6 秒 |
| H | 起動を **collection 前**へ | **279.8 秒** | 0.1 秒 | **217.0 秒** | 208.0 秒 |

- **G が失敗した理由**: prewarm は実 repo (lustre) を走査する I/O であり、t080 群も同じ
  lustre I/O を使う。collection 後に背景化すると両者が競合し、barrier で節約した 25.4 秒が
  実行窓の **+36.1 秒**になって返ってきた。**28.3 秒は「無駄な待ち」ではなく実際の I/O である。**
- **H が成功した理由**: collection (約 63 秒) は import 主体で lustre I/O をあまり使わない。
  そこへ隠すと実行窓が伸びない。

**したがって「collection 前」は本質的であり、「collection 後の背景化」では代替できない。**

## 5d. 倒してはならない方向 (前 wave の明文)

insight README は次を明記している。

> **「cache が無いので既定値」「worker が自分で resolver を呼ぶ」へ倒してはならない。**
> production resolver を呼べる唯一の経路が prewarm である性質を壊すためである。

変えてよいのは 2 点だけである。(1) controller は背景で書き、collection hook を待たせない。
(2) worker の `get()` は cache を上限つきで待つ (現行の即時失敗を待ちへ)。

## 5e. consumer 不在 shard の追加費用は、H の 279.8 秒に既に含まれている (現物読解)

insight README は H の実装について「**consumer の有無は collection 前に確定できないので、
実装は『全 controller で起動する』を選ばざるを得なかった**」と明記している。
つまり **H = 全 3 shard の controller が同時に prewarm した構成**である。

したがって「consumer 不在の shard-1 / shard-2 でも 28.3 秒相当の lustre 走査が走る」
「3 shard が同時に lustre を叩いて prewarm 自体が遅くなる」という懸念は、
**279.8 秒という実測値の中に既に入っている**。新しい発火条件が H より発火範囲を**狭める**方向なら、
lustre 競合は H 以下になる。**H より広げる設計だけが未測定の領域に入る。**

なお `RECEIPT_MEMO_CONSUMER_NODES` は **34 node** である (conftest.py:712 以降)。

## 5f. 待ちは既存の flock が既に実装している (現物読解、2026-09-16 11:10)

`_ReceiptMemo.prewarm` (R:494-579) の `write_once()` は **`self._locked(...)` の内側**で
`_resolve_now()` を呼ぶ (R:545-575)。したがって **cache の `flock` は解決の全所要
(実測 28.328 秒) のあいだ保持される**。一方 reader 側の `read_existing()` も同じ
`self._locked(...)` の中にあり、`_locked` は R:452 で **blocking な `fcntl.flock(LOCK_EX)`**
を取る。

**帰結: writer が先に lock を取っていれば、worker は現在のコードでも公開まで待つ。**
プロセス跨ぎの待ち機構を新規に作る必要はない。相談 B の [refuted] 所見
「未公開 cache は現行でも常に即赤、は成立しない」はこの構造を指している。

残る欠落は 1 点だけである。**reader が writer より先に lock を取った場合**、
`path.exists()` が偽なので R:622-625 が即 `cache-missing` を投げる。
早期起動では `pytest_configure_node` の直後に worker が走り出すので、この競走は実際に起きる。
よって必要なのは「**早期 job が announce 済みかどうか**」を worker が知る手段と、
announce 済みなら lock を解放して期限まで retry する経路だけである。
`.pending` / `.failed` marker はこの 1 点のためにある。

**設計上の含意**: 依頼文の「worker 側は cache を最大 120 秒待ち」は、
既存 flock の上に「announce 済みなら本体不在でも即赤にしない」を足す**最小の差分**で足りる。
待ち機構の作り直しではない。

## 6. 現行コードでの基準値 (実測)

`python3 tools/run_tests.py
"orchestrator/tests/test_real_repo_serialization.py::test_receipt_memo_real_xdist_order_has_no_worker_payer"
-p no:randomly` → **rc=0、1 passed、5.10 秒** (32 worker、loadgroup)。
投入時の `/proc/loadavg` は `26.44 51.69 47.26`、96 core。
