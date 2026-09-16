# [T-2617] 親 brief と一次資料 (段 1)

wave = `dev-wave-t2617-acceptance-collection-cost`
worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2617-acceptance-collection-cost`
基準 = main `262c2993e`

## 1. 依頼 (逐語)

> [T-2617] 受入 1 走の collection 約 93 秒と、収集終了から最初のテスト開始までの 25.6 秒の内訳を
> 確定し、短縮の可否を判定する。D1830 は「残余の動く分は主に collection に出る」とし、D1728 は
> 自 shard 絞り込みを D711 の禁止ごと維持している。絞り込み以外の手があるかを先に調べ、無ければ
> その結論を insight に構造化して残す — 判断は codex 子と 2 レンズで詰めて決め、裁定へ返して
> 止まらない。[T-2616] と同じ受入経路を触るので、両方が走る場合は編集面の重複を起動時に検査する。
> 全体 5 分が絶対上限という既存の上限は緩めない。本題の内訳確定だけ。仮想リスク向けの追加実装は
> scope 外。規律 2 を緩めない。Codex author = D95。

## 2. 研究前進

受入全走が 5 分を超え続ける限り、1 wave あたりの実測サイクルが長くなり Phase 3 の合成・認定の
試行回数が直接減る。本 wave は「どこを削れば効くか / 削れないならなぜか」を確定して、
以後の wave が同じ探索を繰り返さないようにする。完了判定は (a) 2 区間の内訳が数値で決まること、
(b) 絞り込み以外の lever の実在・非実在が根拠つきで言えること、(c) それが insight に残ること。

## 3. scope

- **やる:** 2 区間の内訳確定と短縮可否の判定、insight への構造化。
- **やらない:** 短縮策の実装、観測 field の追加、gate・検査の新設、テストの削除・skip・selection 縮小。
- **成果物:** `output/insights/2026-09-16_t2617-acceptance-collection-cost/` (README + 逐語)、
  worklog / decisions fragment。**実装面の差分はゼロを目標とする** (docs-only)。

## 4. 触れてはならない既裁定 (逐語の要旨。子は原文を確認すること)

- **D711** (`docs/decisions.md`): 各 shard が同一の全 collection を行ってから担当外を deselect する。
  gate 2 = 全 shard の `observed_universe` 完全一致、gate 3 = 独立 login collection との一致。
- **D1728**: 自 shard 絞り込みは採らない。gate 2 の代替述語も新設しない。
  費用は正しさ防壁を弱める理由にならない。
  **再訪条件 = 「受入 wall が再び実害として観測され、かつ独立な全体集合から導いた期待割付を
  供給する設計が具体的に示されたとき。費用の増加だけでは再訪しない。」**
- **D1729**: 受入 report の観測 field 追加 (両端時刻、lock 定義変更) は行わない。schema は v1 のまま。
  **再訪条件 = 「受入 wall が再び実害として観測され、かつ内訳の確定なしには次の一手が決まらない
  ことを示せたとき。」**
- **D1830**: 残余 = `collection + dispatch + 実行中の遊び + teardown` (定義からの恒等式であって
  観測の完全性の検証ではない)。動く分は主に collection に出る。
- **D1894** (2026-09-09): 次の短縮対象は最大 worker 占有。
  **「3 shard 共通の collection と shard-0 の dispatch は今回の対象にしない」**。
- **D2003** (2026-09-14): 別系列化は collection を縮めず実行母集合を分ける。
- **D532**: テストの削除・skip・selection の縮小で速くするのは規律 2 に反し検討対象にしない。
- **絶対規律 2**: 正しさゲートを緩める変異を許さない。

## 5. 親が段 1 で実測した一次資料 (すべて 2026-09-16、逐語)

### 5.1 実走 28 本の shard-0 内訳 (計算ノード、repo 外成果物から再構成)

源 = `/work/1/SFC/tanab/.izanagi-acceptance-shards/<digest>/shard-0/` の `report.json` の
`session_timeline` と `junit.xml` の `<testsuite name="pytest">` 属性。
`pre` = `collection_finished_epoch_s − junit の timestamp`、
`disp` = `min(workers[].first_test_started_epoch_s) − collection_finished_epoch_s`。単位は秒。

```
10:03:21 pre=56.2 disp=28.4
10:01:00 pre=57   disp=30.1
09:58:06 pre=55.7 disp=27.7
09:53:47 pre=55.9 disp=27.7
09:52:14 pre=55.7 disp=25.5
09:38:07 pre=56.5 disp=31
09:37:53 pre=55.8 disp=20.7
09:32:51 pre=56.8 disp=31.3
09:29:47 pre=56.7 disp=34.4
09:19:24 pre=56.7 disp=24.8
09:17:44 pre=56.6 disp=24
09:15:04 pre=55.4 disp=28.9
09:01:15 pre=56.5 disp=26.2
09:05:58 pre=55.9 disp=29.5
08:56:57 pre=56.7 disp=27.3
08:55:58 pre=55.6 disp=21.2
08:48:27 pre=56.3 disp=25.8
08:33:17 pre=55.4 disp=35.1
08:37:24 pre=55.7 disp=25.9
08:32:59 pre=56.5 disp=30.6
08:31:37 pre=55.6 disp=29.1
08:22:48 pre=56.4 disp=30.1
08:21:50 pre=56.5 disp=26.2
08:05:51 pre=56.1 disp=41.1
08:09:10 pre=55.9 disp=28.1
08:13:47 pre=55.4 disp=34
08:05:43 pre=57   disp=26.2
07:57:23 pre=59.1 disp=35.1
```

同じ 28 走の junit `time` (最遅 shard の wall) は 296.2〜604.5 秒に散り、host は bnode002 /
bnode003 / bnode006 / bnode019 / bnode021 / bnode022 / bnode025 / bnode028 / bnode029 / bnode030 /
bnode031 / bnode032 / bnode033 / bnode034 / bnode037 / bnode041 / bnode074 / bnode075 / bnode076 /
bnode077 / bnode080 / bnode082 / bnode095 / bnode098 / bnode099 / bnode101 / bnode102 / bnode116 /
bnode118 / bnode119 / bnode120 / bnode125 / bnode131 に散っている。
**`pre` は 55.4〜59.1 秒、幅 3.7 秒。wall が 2 倍違う走でも `pre` は動かない。**

### 5.2 同一 session の 3 shard (session `8259cf7fff14f3387347ab25a65a379c`)

| shard | junit wall | host | tests | worker | pre | disp | 実行窓 | 尾 |
|---|---|---|---|---|---|---|---|---|
| 0 | 307.1 | bnode030 | 8564 | 48 | 56.2 | 28.4 | 215.2 | 7.2 |
| 1 | 223.1 | bnode026 | 7833 | 48 | 56.3 | 0.1 | 163.5 | 3.3 |
| 2 | 211.8 | bnode040 | 7623 | 48 | 56.5 | 0.1 | 152.2 | 3.0 |

**`pre` は 3 台の別ノードで 56.2 / 56.3 / 56.5。`disp` は shard-0 だけが 28.4 で他は 0.1。**

### 5.3 `disp` の内側 (既存の計測行が現行コードに残っている)

同 session の shard-0 の job stderr (`shard-0/dispatcher.log` に転記されている) の逐語:

```
IZANAGI_MEMO_PREWARM_V1 {"barrier_s":31.321978736006713,"hook":"xdist_node_collection_finished",
"oracle_environment_memo_s":0.1312759759966866,"receipt_memo_s":31.320316853001714}
```

**`disp` のほぼ全部が `_prewarm_receipt_memo` 1 本である** (`receipt_memo_s` / `barrier_s` = 0.99995、
`oracle_environment_memo_s` は 0.13 秒)。実体は
`orchestrator/tests/conftest.py:876 _prewarm_receipt_memo` →
`memo_module.prewarm_real_repo_receipt` で、その内側が実 repo (lustre) を走査する
production の resolver である。shard-1 / shard-2 が 0.1 秒なのは consumer が選択に入らないため。
この帰属は 2026-09-14 の wave (`output/insights/2026-09-14_acceptance-5min-floor/README.md`) が
215 対 1 の比で先に確定しており、本 wave の実測はそれを別走行で再現したものである。

### 5.4 `pre` の内側 — 親が login node で採った対照 (4 条件)

同一 worktree、同一 command
`python3 -m pytest orchestrator/tests --collect-only -q -p no:cacheprovider`。
`/usr/bin/time` の逐語と、pytest 自身が報告する collection 所要。

| # | 条件 | load (1 分) | wall | user CPU | sys CPU | %CPU | pytest 報告 |
|---|---|---|---|---|---|---|---|
| 1 | 新規 worktree、`__pycache__` 不在、page cache も冷 | 44.6 | 129.2 s | 53.0 s | 2.7 s | 43% | 125.37 s |
| 2 | 1 の直後 (`__pycache__` 在) | 約 50 | 43.0 s | 17.4 s | 1.6 s | 44% | — |
| 3 | 2 の直後 (`__pycache__` 在) | 96.4 | 20.8 s | 16.5 s | 1.7 s | 87% | 18.23 s |
| 4 | `__pycache__` を消し page cache は温 | 93.7 | 74.5 s | 56.4 s | 3.2 s | 80% | 71.52 s |

いずれも `23970 tests collected`。
**bytecode 再コンパイルの費用は 1 process あたり user CPU で約 40 秒 (56.4 − 16.5)。**

### 5.5 5.4 の regime 判定 — 計算ノードの受入は「温」である

- `.gitignore:2` が `__pycache__/` を無視するので、`__pycache__` は checkout に残り続ける。
- 実測: `orchestrator/tests/*.py` は 380 file。稼働中の 5 つの wave worktree の
  `orchestrator/tests/__pycache__` の entry 数は 380 / 380 / 381 / 378 / 380 (版は `cpython-310`)。
  主 checkout は 677。**受入が走る checkout の bytecode cache は事実上充足している。**
- したがって 5.4 の #1 と #4 (冷) は計算ノードの受入 regime ではない。regime は #3 に近い。
- **未確認:** 計算ノードの job 環境に `PYTHONDONTWRITEBYTECODE` が立つかどうか
  (`tools/acceptance_launcher.py:70-71` は立っていれば `sys.dont_write_bytecode = True` にする。
  `tools/check_subprocess_bytecode_guard.py` は `orchestrator/` と `tools/` の python subprocess に
  この guard を要求する checker である)。**立っていても既存 `.pyc` の読み出しは止まらない**ので
  5.5 の結論は変わらないが、子は配線を確かめてほしい。

### 5.6 単独 collection と 48 worker collection の差

- login node の単独 process (温、5.4 #3) は collection 18.23 秒 / user CPU 16.5 秒。
- 計算ノードの受入は 48 worker で `pre` = 約 56 秒。**差は約 38 秒。**
- 親は `-n 48` を login で再現しようとしたが、`--collect-only` では xdist が働かず
  `IZANAGI_EFFECTIVE_SCHEDULER_V1 {"effective_scheduler":"serial"}` になり
  14.75 秒 / 105%CPU で終わった。**48 worker 並列 collection の login 再現はできていない。**
- **この 38 秒の帰属は未確定である。** 親の候補は (a) 48 process 分の重複 collection の CPU と
  lustre metadata 競合、(b) execnet による 48 worker の bootstrap、
  (c) `tools/acceptance_shards.py` の分割 plugin が worker ごとに払う費用 —
  `pytest_collection_modifyitems` が `records_from_items(items, repo)` を呼び、
  その中の `_canonical_item` (761 行) が item ごとに `Path(item.path).resolve()` を 1 回する。
  23970 item × 48 worker = 約 115 万回。加えて `allocate`、`_digest` の sha256 が 2 回。
  **親の login 計測にはこの plugin が載っていない** (`IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1` 未設定)
  ので、(c) は親の 18.23 秒に含まれていない。

## 6. 親の provisional 裁定 (攻撃対象)

- **(P1-A)** 「collection 約 93 秒」は直接観測ではなく残差であり、かつ 2026-09-14 の 1 走の値である。
  現行の中心は **56 秒台**で、走を跨いでほぼ動かない。D1830 の「動く分は主に collection に出る」は
  当時のデータでは正しいが、**現行の `pre` はむしろ最も動かない成分である。**
- **(P1-B)** 「25.6 秒」の内訳は**確定済み**である。99.995% が `_prewarm_receipt_memo` であり、
  これは [T-2616] が所有する打ち手 (起動を collection 前へ移す) の対象そのものである。
  本 wave が新たに決めることはない。
- **(P1-C)** `pre` の 56 秒のうち、単独 process の collection で説明できるのは約 18 秒。
  残り約 38 秒は 48 重の並列実行と分割 plugin の per-item 費用に帰属する見込みだが**未確定**。
- **(P1-D)** 絞り込み以外の lever の候補は次の 3 つ。いずれも collection の**集合**を変えないので
  D711 の gate 2 / gate 3 にも D1728 にも D2003 にも触れない、と親は読む。
  1. 分割 plugin の per-item 費用を下げる (`Path.resolve()` の呼び出し回数、digest の再計算)。
  2. `_prewarm_receipt_memo` の内側 (production resolver の lustre 走査) を速くする。
     ただし 5min-floor wave が「production は触れない」と結論している。
  3. 何もしない。`pre` は 5 分の上限に対して固定費 56 秒であり、
     削っても最長単体テスト (208〜214 秒) の床は動かない。
- **(P1-E)** **D1728 の再訪条件は満たされていない。** 本 wave は「独立な全体集合から導いた期待割付を
  供給する設計」を示していない。よって絞り込みは採らない。これは覆さない。

## 7. 子への問い

1. **5 の一次資料と 6 の provisional 裁定を攻撃せよ。** 数値の帰属、一般化、regime 判定 (5.5)、
   残差と直接観測の取り違え、`disp` の帰属の再現性。
2. **(P1-C) の 38 秒の帰属を、repo の実装から file:line 粒度で詰めよ。**
   login で再現できていない以上、静的な読解で候補を絞り、
   **どの観測をすれば帰属が決まるか**を、D1729 の「観測 field を足さない」制約の下で示せ。
3. **絞り込み以外の lever が他にあるか。** 親の (P1-D) 以外を探せ。
   D711 / D1728 / D2003 / D532 / 絶対規律 2 のどれにも触れないことを、
   **受理集合が変わらないという形で示せ**。触れるものは「触れる」と書いて候補から外せ。
4. **短縮の可否の結論を 1 行で述べよ。** 「できる / できない / 条件つきでできる」のどれかと、
   その条件。親は裁定へ返して止まることをしない。子の判断を求めている。
