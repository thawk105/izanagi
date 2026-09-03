# 裁定パッケージ — 受入全走を 5 分に収めるために要る判断

本 wave は依頼の「長時間を要するテストが妥当か検査しろ」に答え、律速を同定した。
そのうち**本 wave が実装しない 2 件**について、ユーザーの判断を仰ぐ。
どちらも「実装しなかった」のではなく「**実装すると既存の検査契約を変えるので、
AI が独断で決めてはいけない**」と判断したものである。

## 前提 — 測って分かったこと

受入全走の wall を決めているのは、テストの重さではなく **直列化される鎖**である。
worker を増やしても鎖は縮まない。

| 直列化の源 | 台帳 worker-time | 中身 |
|---|---:|---|
| 鎖 X: `real-repo` xdist group | **303.7 秒** | 96 node が 1 worker に固定される |
| 鎖 Y: `certified_evidence` の排他 lock | **258.1 秒** | 17 test が lock 保持のまま直列に走る |
| 最長単体 node | 140.0 秒 | 32 反復の相互比較 (前 wave が分割不能と裁定) |

走行外費用 78.2 秒を足した下限モデルの現状予測は **381.9 秒**で、
前 wave の実測最遅 shard **388.3 秒**と誤差 1.6% で一致する。

| 筋書き | K=2 x 32 worker | K=3 x 32 worker |
|---|---:|---:|
| 現状 | 6.37 分 | 6.37 分 |
| 本 wave の実装 (二乗の除去) だけ | **6.37 分 (変わらない)** | **6.37 分 (変わらない)** |
| + 鎖 X を解く | 5.61 分 | 5.61 分 |
| + 鎖 X + 鎖 Y | **4.19 分** | **3.64 分** |

**5 分に入れるには鎖 X と鎖 Y の両方が要る。片方だけでは届かない。**

## 裁定 1 — 鎖 X: `real-repo` group の読み手を並行化してよいか

### 何が起きているか

`orchestrator/tests/conftest.py:2001` が `REAL_REPO_RESOURCE_NODES` の 96 node すべてへ
一律に `pytest.mark.xdist_group("real-repo")` を付ける。`--dist loadgroup` では
同じ group は 1 worker に固定されるため、96 node が直列に走る。

一方 `conftest.py:1152` には `{"read": fcntl.LOCK_SH, "write": fcntl.LOCK_EX}` があり、
**実行時の資源保護はすでに読み書き lock として実装されている。**
node ごとの access を集計すると:

| parent | ccbench | node 数 | 台帳秒 |
|---|---|---:|---:|
| read | read | 52 | 221.6 |
| read | (なし) | 34 | 78.5 |
| (なし) | read | 6 | 3.6 |
| read | **write** | 3 | 0.0 |
| (なし) | **write** | 1 | 0.2 |

**書き手は 4 node で実質 0 秒、残り 92 node (303.7 秒) は読み取り専用**である。
読み手どうしは共有 lock で本来は並行に走れるのに、group 固定がそれを禁じている。

### なぜ AI が勝手に直さないか

**素朴な修正は跨ホストの競合を作る。**段 3 のレンズ B が指摘し、親が採用した。

`real-repo` group は 2 つの役割を兼ねている。

1. 内側: 1 worker への直列化。
2. 外側: **同一 shard = 同一ホストへの affinity。**
   `tools/acceptance_shards.py:74-84` の `REAL_REPO_GROUP_CONFLICT_EDGES` は
   「別 shard は別ホストになりうるので local の flock では競合を閉じられない」ために
   競合する group を同じ shard へ連結する契約である。

したがって「書き手 4 件だけを group に残す」と、読み手が別 component・別 shard・
**別ホスト**へ移りうる。そうなると local の共有 lock は書き手との競合を閉じない。
これは速くするために防壁を外す形であり、**絶対規律 2 が禁じる変更**である。

さらに、現行の grouping は次の 2 つのテストが**意図的に検査している**。

- `test_acceptance_schedule_order.py::test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`
- `test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes`

直すにはこれらの期待値を変える必要がある。`DW-S05-B` は実装子に期待値変更を禁じており、
これは実装の詳細ではなく設計判断である。

### 提案する設計 (両レンズが一致した方向)

**全 96 node の shard affinity は保ったまま、xdist の worker grouping だけを read/write で割る。**
そのために `ItemRecord`・component 構成・closure gate へ、
`xdist_group` とは独立した shard-affinity 属性を足す。

これは `conftest.py`、allocator の schema、closure gate、上記 2 テストを跨ぐ変更であり、
専用の wave (プラン + 敵対検査 2 本 + 変異) を要する。

### 判断していただきたいこと

1. この方向で専用 wave を立ててよいか。
2. shard affinity 属性を新設することを認めるか (`ItemRecord` の schema が変わる)。
3. 上記 2 テストの期待値変更を認めるか。

## 裁定 2 — 鎖 Y: `certified_evidence` の lock 範囲

### 何が起きているか

`orchestrator/tests/test_p3_b4_raw_record_producer.py:1174-1239` の fixture は、
共有 tmp に evidence を 1 度だけ作り file lock で worker 間を直列化する。
しかし **`yield` が `flock(LOCK_EX)` の内側にある**ため、lock を test 本体の実行中ずっと保持する。
17 test が完全に直列化され、台帳で 258.1 秒 (各 test 本体は 6.8〜19.0 秒)。
evidence の構築自体は cache 済みなので、**lock 区間は構築ではなく本体そのもの**である。

### こちらは裁定 1 より軽い

repo には既に `conftest.py:1369` の session fixture `real_repo_fixture_lock` があり、
`_real_repo_fixture_lock_context(parent, ccbench)` として読み書きを宣言できる。
「最初だけ排他で seed を作って解放し、以後は確認済み reader を共有 lock、
書き手だけ排他」にすれば、**どのテストの期待値も変えずに**直列を短くできる見込みがある。

段 3 のレンズ B が現物で確認したところ、共有 path を触ると言えるのは
`test_m17_terminal_receipt_validation_survives_original_replacement` と
`test_m18_symlinked_evidence_is_rejected_with_regular_control` の **2 件**である
(親が最初に数えた 7 件は字句 heuristic による過大評価だった。他は `tmp_path` 配下を書いている)。

保守的に 7 件を書き手として残しても直列は 258.1 → 105.2 秒になり、
鎖 X を解いた後の critical path は最長単体 node 140.0 秒が支配するため**それで十分**である。

### 判断していただきたいこと

これは期待値を変えないので、**通常の dev-wave として起票してよいか**だけを確認したい。
反対がなければ次の一手として起票する。

## 裁定 4 — dev-wave の L1.5 予算をわずかに上げたい (段 8 の自己改善が収まらない)

本 wave で実測した改善候補が 1 件あり、**byte 予算に収まらないため実装できなかった。**

**候補:** `DW-S06-A` (段 6 敵対レビュー) へ次の義務を足したい。

> must-fix は従う前に前提を実測する (`DW-S01` の義務を段 6 へ適用)。前提が誤った推奨は防壁を壊す。
> 複数レンズの一致は裏取りにならない — 同じ誤った前提を共有しうる。

**根拠 (本 wave の実測):** 段 6 のレンズ D が「splitter に終端空要素を足せ」という must-fix を出した。
CPython の `ast._splitlines_no_ff` は終端空要素を作らない (`if next_line:` のときだけ append) ため、
**従っていれば stdlib との一致を壊し、guard 文字列と証拠 JSON を変えていた。**
さらに段 3 のレンズ A も同じ誤った前提を書いており、**2 レンズが独立でなかった。**
親が実測 (C-2 の全 25 ケースを pytest 抜きで再現、失敗 0 件) して反証し、
段 6 のレンズ C も独立に同じ結論へ達したことで確定した。

**既存正本との関係:** `DW-S01` は「brief 前に承認済み裁定と引数の前提を実測する」と定めるが、
**段 6 のレビュー所見については同じ義務が無い。**発火点が違うため既存正本では代替されない
(親が `docs/decisions.md`・`docs/dev-wave/**`・`docs/failures.md` を意味検索して確認)。

**なぜ実装しなかったか:** 追記すると
`docs/dev-wave/**` の L1.5 unique footprint が 9925 bytes となり、予算 9696 bytes を 229 bytes 超える。
`docs/skill-self-improvement.md` は「予算のために安全義務を削除・弱化してはならない」
「予算の変更は実装せず裁定パッケージへ送る」と定めている。余裕は約 23 文字分しかなく、
義務の意味を保ったまま収める書き方が見つからなかった。既存文の圧縮で捻出する案は、
他の安全義務を薄めるため採らなかった。

**判断していただきたいこと:** L1.5 予算を 229 bytes 以上 (例: 9696 → 10000) 上げてよいか。
上げない場合、この義務は記録に残るだけで機械的には強制されない。

## 裁定 3 — 「5 分」の測定面を固定したい

段 3 のレンズ B が指摘した。現在「5 分」がどの量を指すかが決まっていない。

- 受入形の shard は既定 K=2、`IZANAGI_ACCEPTANCE_SHARDS=3` の明示時だけ 3 (`tools/run_tests.py:253-297`)。
- worker 上限は 32 (`:65` `_NPROC_CAP = 32`)。
- 前 wave が記録した 297.5 秒と 388.3 秒が同じ測定面かどうか不明。

**固定してほしい点:** canonical command、K、worker 数、queue 待ちを含むか、
collection から teardown までを含むか、最大 shard の wall か全体の wall か。
レンズ B は「最大 shard の execution wall を対象にし、連続 3 走すべて 270 秒以下」
のように 10% 程度の余裕を持つ形を推奨している。

これが決まらないと、修正後に「依頼を満たした」と判定できない。
