---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-10
wave: dev-wave-t692-r3-xdist-walltime
seq: 1
---

## {{D:xdist-group-closure-audit}}. 実 repo 競合閉包の収集監査を marker の形・個数・名前集合・provenance の 4 面へ広げる

**背景:** D63 は実 repo working tree と共有 ccbench submodule の reader / writer を
単一 `xdist_group("real-repo")` へ閉じ込めると決めた。しかし収集監査は
`REAL_REPO_SERIAL_NODES` と独立 golden の**集合一致**しか見ておらず、marker の与え方を見ていなかった。
その結果 `test_ruleops.py` の実 checkout reader が `@pytest.mark.xdist_group(name="real_repo")` と
kwargs + underscore で書かれ、canonical `real-repo` とは**別 group**として 2026-08-04 から
今日まで排他が効かないまま残った ([T-438])。xdist は group 名が違えば別 worker へ配るため、
実 submodule を patch する writer と同時に走りうる。

**決定 (1): 監査対象を全 collected item の全 `xdist_group` marker にする。**
canonical node だけでなく suite 全体を見る。検査する不変条件は 4 つ。

- marker は 1 node につき最大 1 個 (二個目は xdist が名前を結合して別 scope になる)
- group 名は positional 引数 1 個で与える (`kwargs={"name": ...}` 形を拒否)
- 実際に現れた group 名の集合が独立 golden と**完全一致**する
- canonical node の関数ソースに**手書きの `xdist_group` decorator が無い** (provenance)。
  conftest の hook は既存 marker があれば付与を skip するため、手書きが正しい名前でも
  「hook 由来である」ことは保証されない

**決定 (2): 各不変条件に合成負例の positive control を必ず添える。**
恒真ゲートを禁じる。負例は互いに独立させ、1 つの負例が 2 つの検査を同時に発火させない
(kwargs 形の負例は positional も 1 個持たせ、group 名集合の負例は marker の形を正しくする)。
これを守らないと、片側の検査を消す変異が別の検査に殺されて**単一理由性が検証できない**。
本 wave では実際に、分離前は kwargs 負例が `len(args) == 1` でも落ちて MT4 を殺せなかった。

**決定 (3): `real-repo` group 内の実行順を定数で固定し、`pytest_collection_finish` で適用する。**
独立解決を行う CLI node を先頭、共有 cache barrier をその次に置く。
`pytest_collection_modifyitems` の非 wrapper hook では pytest 本体の `--ff` / `--nf` が
post-yield で items を再配置して上書きするため、collection の**最後**で適用する。

**この順序は wall の性質であって D63 の排他ではない。** 同一 group は単一 worker が
逐次実行するので、順序が崩れても相互排他は崩れない。崩れるのは受入 wall の短縮効果だけである。
排他が崩れうるのは group の**外**にいる実 repo reader であり、それは別途裁定へ返した。

**却下した案:**

- **並列度 (`_NPROC_CAP` / `default_test_jobs`) の引き上げ** — 計算ノードでは既に affinity 全数
  48 worker で、実効並列度は 11.74 相当しかない。critical path 下界は最大 group の直列和
  (1388.80 秒) が決めるので worker を増やしても動かない。
- **`DEFAULT_WALLTIME` の単独引き上げ** — 期限が延びるだけで消費は縮まない。
- **reader / writer の flock 化 (D63 保証機構の置換)** — 理論下界は最良 (約 691 秒) だが
  分類漏れ 1 件で偽緑を作る。D63 自身が bare な reader/writer 分割を明示的に却下している。
- **収集順で group 外の 2 解決を意図的に重ねる案** — 段 2 の推奨案 (期待 wall 約 876 秒) だが、
  段 3 の両レンズが「同時開始は未測定の仮定。非重複なら 1529.17 秒」と計算し、
  かつ group 外 payer との意図的な並走を新規に作るため却下した。
