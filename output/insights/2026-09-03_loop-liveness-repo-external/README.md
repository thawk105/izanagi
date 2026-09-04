# 開発ループ・進化探索ループが止まる 3 つの実体 — git 管理外依存を閉じ、5 分上限の律速を特定した

authority: none
default_effect: no-state-change

ユーザー依頼「受入全走は 5 分以内でないと困る。開発ループ・進化探索ループが回らなくなる
リスクを分析し、可能であれば解決してほしい。ホームディレクトリ下の古い AI セッションログを
掃除したら全ての dev-wave がコケ続けた。git 管理外のファイルに izanagi のテストが依存して
いたのは衝撃的だった」に対する wave の記録である。
状態の正本は worklog、採用済み判断は decisions とする。

一次資料は同 directory の `measurements-1-collection-cost.md`、`measurements-2-two-disputes.md`、
`measurements-3-acceptance-floor.md`、`external-binding-census.md`、`verbatim/` (段 2 プラン、
段 3 敵対 2 本、段 4 裁定、段 6 レビュー 2 本の逐語)。

## 結論 — 「回らなくなる」には 3 つの実体があり、性質が違う

| # | 実体 | 現況 | 本 wave の扱い |
|---|---|---|---|
| 1 | **テスト自体の所要** | 最悪の走で 297.5 秒 = **4.96 分**。既に 5 分の線に触れている | **解決しない。** 律速を特定して次の一手へ |
| 2 | **計算ノードのキュー待ち** | 本 wave 実行中に実行中 0 本・待ち 7 本を観測。焦点走 1 本が 20 分超待ち、1 度は空振り | 観測のみ。機構は作らない |
| 3 | **git 管理外ファイルへの依存** | 5 file・3 root が束縛。防護が正しいのは 1 file だけだった | **実装で閉じた。** 4 file を修理 |

**1 と 3 は別の問題である。** ユーザーは両方を同じ依頼で挙げたが、1 は費用の問題、
3 は可用性の問題であり、打つ手も測り方も違う。本 wave が実装で閉じたのは 3 だけである。

## 実体 1 — 受入 5 分上限の律速は「最長単体テスト 1 個」で、並列度では下がらない

`orchestrator/tests/acceptance_duration_ledger.json` (19519 entry) から出した分解。
**この値は LPT 割付のための scheduling hint であり、権威ある性能測定ではない** (D104 決定 4)。

```
総仕事量            : 11956.5 s (3.32 CPU 時間)
144 worker 完全詰め : 83.0 s     (48 worker x 3 shard)
最長単体 node       : 140.0 s
```

**最長単体 node (140.0 秒) が完全詰めの理論値 (83.0 秒) を上回っている。**
したがって shard 割付・詰め込み・worker 増加のどれでも、受入 wall を 140 秒より下へ持って行けない。
これは 2026-09-01 の床分解 (`output/insights/2026-09-01_t2097-acceptance-floor-decomposition/`) の
結論 5「割付・詰め込みで取れるのは 9.54 秒だけ」と、独立の道筋で整合する。

床分解の共通 report 外費用 56.3 秒と shard-0 固有 21.9 秒を足すと:

| 走 | 最長単体 | 合計 wall | 分 |
|---|---:|---:|---:|
| 最良観測 | 118.6 s | 196.8 s | 3.28 |
| 中央付近 | 126.1 s | 204.3 s | 3.40 |
| **最悪観測** | **219.3 s** | **297.5 s** | **4.96** |

最長単体は 14 走で 118.6〜219.3 秒に動く。**最悪の走は既に 5 分の線に触れており、
上限超えは運の問題になりつつある。**

### 素朴な分割は採れない — 検査を消して速くする形になる

最長 node は `test_p3_autonomous_workload_trial.py:1836`
`test_role_sink_bytes_vary_only_at_declared_declassifications` で、本体は
`for value in range(32):` の単一 node 内ループである (`do_build is False` なのでビルドを含まない)。
1 反復あたり約 4.4 秒。保留登録簿にも flaky 登録簿にも載っておらず、毎回の受入で実走している。

**32 個へ parametrize すればよい、とは言えない。** `:1941-1952` にループを跨ぐ assertion がある。

```
assert len(set(sink_bytes["planner"])) == 1
assert len(set(sink_bytes["auditor"])) == 32
assert len(set(trusted_variants)) == 32
assert _critic_relation_equivalent(sink_bytes["critic"])
```

このテストの目的は 32 ケースの個別検証ではなく、**32 本の role sink 出力を相互比較して
非干渉性 (宣言された declassification 以外では byte が変わらないこと) を確かめること**である。
32 node へ素朴に割ると相互比較がどの node からも消え、**検査を消して速くする形 =
絶対規律 2 が禁じる reward hack** になる。

[T-1933] が最長 node 短縮に 2 度失敗しているが、攻めたのは `test_s8b_oracle_driver.py` 系の
別 node で、手段は cache 共有と process-memo grouping だった。**分割は試されていない。**
次の一手は「相互比較を保ったまま 32 本の生成を並列化できるか」の生死確認 (`DW-G01`) である。

## 実体 2 — キュー待ちは「1 本が遅い」より広い害を持つ

本 wave の実行中、焦点走 1 本を投入したところ次が起きた。

- 1 回目: 既定の queue-wait 900 秒を超えて `rc=16 queue-wait-timeout`。**テストは 1 行も走らなかった。**
- 2 回目: D612 の opt-in 上書き (3600/600) を付けて再投入。20 分超えても QUE。
- 同時刻の `qstat`: **7 本 QUE、実行中 0 本。**

**5 分上限は、単走の所要としてだけでなく列の回転率を決める量として読むべきである。**
1 本あたりのノード占有が長いほど列が詰まり、並行する全 wave の待ちが伸びる。
本 wave はこの点について新しい機構を作っていない。観測として記録するに留める。

## 実体 3 — git 管理外への束縛は 5 file・3 root あり、正しく防護されていたのは 1 file だけだった

### 全数の出し方と、字句走査の限界

`orchestrator/tests/*.py` の string literal のうち絶対 path・home 相対に見えるものは **1796 件**
あり、**字句だけの走査は gate として成立しない。** 「実在する repo 外 path、system prefix
(`/usr /proc /dev /tmp /bin /sbin /lib /etc /var /sys /opt`) を除く」へ絞ると 195 件、
断片 (`/`、`//`、`/./` 等の path 結合の右辺) を除くと意味のある束縛先は 3 root になる。

| # | file:line | 束縛先 | 変更前の防護 |
|---|---|---|---|
| 1 | `test_codex_reasoning_ab.py:128` | `~/.codex/sessions` | **内容単位で skip。唯一の正しい先例** |
| 2 | `test_t189_oracle_wiring_slice.py:38,84` | `/work/1/SFC/tanab/dev-wave-jobs` | 根 directory の有無だけ |
| 3 | `test_t1434_t1222_science_slice.py:21` | 同上 | **無し** |
| 4 | `test_b10_extended_figure_provenance.py:21-23` | `/work/1/SFC/tanab/b10-backoff-grid-runs5` | **無し** |
| 5 | `test_plot_b10_extended_backoff.py:15-17` | 同上 | **無し** |

`test_pegasus_tools.py:427,461` の `/work/SFC/tanab/github/{gflags,glog}` と
`test_claude_session_ledger.py:1773` の `~/.claude/projects` は、**値としての文字列を assert して
いるだけで filesystem を読まない。** 族の条件は「literal に repo 外 path が現れる」ではなく
「**実行時にその path を読む**」でなければならない。

### 4 と 5 は論文図の provenance を検証している

`/work/1/SFC/tanab/b10-backoff-grid-runs5` は
`docs/paper-story/figures/fig2c_b10_extended_backoff.{png,pdf}` の provenance を検証するための
外部測定 root で、22 file の sha256 を照合する。ここが剪定されると論文図の provenance 検査が
hard red になり、**その時点で全 wave の受入が同時に落ちて land が止まる。**
2026-09-01 に `~/.codex/sessions` の 2026/07 消失で起きたのと同じ形である
(同時刻の別 wave 3 本が同数で落ちた)。

### 字句走査では原理的に見つからない動的依存が 1 件ある

`orchestrator/tests/output_snapshot_ignores.py:91-111` は
`git rev-parse --git-path info/exclude` と `git config --get core.excludesFile` が返す path を
`expanduser()` して bytes を読む。consumer は `test_s8b_oracle_driver.py`、
`test_s8b_floor_campaign.py`、`test_real_repo_serialization.py` の 3 本。

**現物を確認した結果、現在の寄与は 0 件である。**
`core.excludesFile` は未設定 (rc=1)。`.git/info/exclude` は 10 行あるが、
`_rule_candidates` (`:121-140`) が `**` を含む規則を捨て、静的前置が `output/` で始まる規則しか
採らないため 10 行すべて対象外。不在時は `b""` を返すので **file を消しても挙動は変わらない。**
**危険なのは削除ではなく、`output/` で始まり `**` を含まない規則の追加である。**

なお `core.excludesFile` が未設定でも git 自身は `~/.config/git/ignore` を尊重するため、
この helper は git の実 ignore 集合を過小に見積もる。別の忠実度の穴である。

## 副産物 — 成長比例の保留機構は collection 時の費用を構造的に見られない

`orchestrator/tests/conftest.py:2027-2030` は `pytest_collection_modifyitems` の中で
`pytest.mark.skip` を付ける。これは **module の import が終わったあと**である。したがって
module 直下で repo を走査する成長比例費用は、D335 の保留機構、shard 分割、`--deselect` の
いずれでも消えない。

`test_p3_exploration_namespace.py:147` の `_CAMPAIGN_DRIVERS = _discover_campaign_drivers()` が
まさにその位置にあり、保留登録簿に載っていない。この module の collector は 3.437 秒 =
全 file collector 合計 12.542 秒の **27.4%**、次点 (0.542 秒) の 6.3 倍の外れ値である
(`output/insights/2026-09-02_acceptance-collection-internals/`)。

## 副産物 — 既存の次の一手 [T-2242] の効果見積りは向きが逆だった

[T-2242] は「全 187 file の `ast.parse()` は残し、source text に対象 identifier が無い file で
`ast.walk` を省く。単一 process で 3.44 秒のうち**約 2.7 秒が上限**」と書いていた。

実測の成分は次のとおりで、**費用の 76% は `ast.parse`、`ast.walk` は 21%** である。

| 成分 | 所要 | 比率 |
|---|---:|---:|
| `read_text` | 0.090 s | 3% |
| `ast.parse` | 2.522 s | 76% |
| `ast.walk` | 0.703 s | 21% |

**旧見積り 2.7 秒は反証された。** 同じ probe で prefilter を `ast.walk` の前に置いた場合の
saved は **0.629 秒**、residual は **2.686 秒**だった。数値が近いことは同一量であることを
意味しない。取れる量ではなく取り残る量に近い値である。

正しい置き場所は `ast.parse` の**前**である。

## 実装したこと 1 — 字句 prefilter を NFKC 正規化 source に対して置く

素朴な実装 (生 source に対する部分文字列判定) は**採れない**。段 3 の敵対レンズが見つけ、
親が現物で検算した反例がある。

```python
layout.ｅxploration_campaign_layout(x)   # 先頭が全角 e (U+FF45)
```

この source は ASCII の `exploration_campaign_layout` を**含まない**が、Python は識別子を
NFKC 正規化する (PEP 3131) ため、`ast.parse` 後の `Attribute.attr` は
`exploration_campaign_layout` に**なる**。生 source prefilter はこの file を捨て、
AST 経路は driver として発見する。**これは「族から外す条件」であり D872 決定 1 に抵触する。**

`unicodedata.normalize("NFKC", source_text)` に対して判定すれば必要条件が回復する。

| 経路 | 187 file の所要 | 反例を捕まえるか | 発見集合 |
|---|---:|---|---|
| 無 prefilter (現行) | 1.718 s | — | 7 件 |
| 生 source prefilter | 0.247 s | **捕まえない** | 7 件 |
| **NFKC 正規化 prefilter** | **0.285 s** | **捕まえる** | 7 件 |

**83.4% 削減**、正規化の追加費用は 0.038 秒、発見集合は完全一致。
段 6 のレンズ A は、識別子 token の境界が空白や ASCII 記号で区切られる以上、識別子の NFKC 結果は
source 全体の NFKC にも連続部分文字列として必ず残ると論証し、行継続・コメント分断・BOM・
非 UTF-8 encoding 宣言・隣接文字列リテラルの各反例候補を個別に否定した。

**遅延化は不可能である。** `_CAMPAIGN_DRIVERS` は 5 箇所の `@pytest.mark.parametrize` へ
`ids=` 込みで渡されており、collection 中に値が要る。

### 受け入れた検出力の損失

marker を持たない構文不正な campaign file は、prefilter 後は `ast.parse` されないので
構文エラーが出ない。**失う範囲は 3 module 分**である。campaign 186 module のうち
test suite の source で名前が挙がるのは 183 で、残る 3 本
(`p2_5`, `s6_amendment_20260713_fence`, `s6_proposal_rounds_power`) は自分の file 以外
どこからも名指しされていない。既存の repo 全体走査 `test_campaign_import_invariant.py` は
`growth_test_holds.py` で 6 node が恒久保留されており実走しない。
**この 3 本にテスト被覆が無いこと自体が別の穴**であり、次の一手として起票した。

## 実装したこと 2 — repo 外束縛 4 file に内容単位の guard を置く

「根 directory が在るか」ではなく「**そのテストが実際に読む file が全部在るか**」を見る。
要求集合は checked-in artifact から導出する (t189 は 4 file、t1434 は 21 file、B-10 は各 22 file)。

- **欠落は `os.stat` の `FileNotFoundError` だけを skip とする。** `Path.exists()` は使わない。
  `ENOTDIR` と `ELOOP` でも False を返すため、**非 directory component や symlink loop という
  構造的な壊れ方を「欠落」として隠してしまう**からである (段 3 レンズ A の指摘)。
- guard の粒度は「その node が読む file」に合わせる。reader-A の output だけを読む 3 node は
  その 1 file だけを guard し、無関係な 20 file の不在で skip させない。
- `test_physical_rejects_symlink_component` は guard しない (外部内容の実在が前提でない負例)。
- skip 理由に欠けた relative path を列挙し、「完全な入力集合なら全 assertion が走る」旨を明記する。
  **後から「テストを緩めて緑にした」と「外部入力が無いので測れなかった」を区別できる。**
- B-10 2 file の素 runner `_run()` に `except Skip` を足した
  (`test_plot_backoff_ci.py:441-460` が先例)。skip のみなら rc=0。

**資源が完全に在る環境で走る assertion は 1 つも減っていない。**

## 作らなかったもの — 全数走査 gate

段 2 のプランは登録簿 JSON とメタ gate 2 本を設計したが、**段 4 で却下した。**

- 段 3 の両レンズが独立に「全 test source 走査は D335 が禁じる成長比例 gate の新設」と判定した。
- 親の実測でも `O(file 数)` である (字句 prefilter 付きで 345 file 中 16 file を parse、0.610 秒)。
- **決定的な先例:** 既存の repo 全体走査 `test_campaign_import_invariant.py` は
  まさにこの理由で `growth_test_holds.py` に 6 node 恒久保留されている。新設すれば同じ扱いになる。
- `DW-G03` の「独立 2 例」も成立しない。段 3 レンズ B が git 履歴を引き、
  dev-wave-jobs 系 2 file は同一作者・同日 (`56ae5e848` / `f24550a01`)、
  B-10 系 2 file は**同一 commit** (`637dafa17`) と示した。

したがって `DW-G03` の「単発事故は局所修復を既定とする」に従い、既知 4 file の局所修理に留めた。
**全数性を機械で保証したいが、その gate 自体が成長比例になる**というジレンマは
ユーザー裁定へ返す。

## 親自身が間違えた箇所 (記録として残す)

1. **「repo 外束縛は 3 件が全数」** — 誤り。`git grep` で `/home/` と `expanduser` だけを引いたため
   `/work/` 配下を取り逃した。AST で全 string literal を集めて実在判定する走査を書き直して 5 件に訂正した。
2. **「字句 marker は AST 発見の必要条件」** — 誤り。NFKC 正規化により破れる。段 3 レンズ A が指摘し、
   親が現物で検算した。
3. **「`DW-G03` の独立 2 例は満たす」** — 誤り。段 3 レンズ B が git 履歴で否定した。
4. **「最長 node を 32 個へ parametrize すればよい」** — 誤り。ループを跨ぐ assertion があり、
   割ると非干渉性検査が消える。親が node 末尾を読んで自己訂正した。
5. **「2.7 秒は取り残る量である」** — 言い過ぎ。旧見積りが反証されたことと、別測定の
   residual が 2.686 秒だったことは言えるが、数値の一致は同一量を意味しない (段 3 レンズ A の指摘)。
6. **焦点走を実装子と同時に投入した** — `DW-O26` の「同一 worktree からの dispatch は直列にする」
   違反。実装子が orphan hold で 1 件も実走できなかった。

## 主張しないこと

- 48 worker x 3 shard の受入 wall が何秒短くなるか。**転移係数を持っていない。**
- 単一 process の削減量を 145 回分足し合わせた wall 改善。
- 計算ノードの collection 約 51.7 秒が同じ比率で減ること。
- 受入が 5 分以内になること。**本 wave は最長単体 node に触れていない。**
- repo 外束縛が「全数防護済み」であること。固定既定値 5 module・3 root については閉じたが、
  動的 git ignore 入力と、`/mnt` 等の将来の prefix は覆っていない。

## 変異検査 — 8/8 KILLED、SURVIVED 0、MISMATCH 0

一次資料は同 directory の `mutation-spec.json` (事前登録) と `mutation-ledger.json` (harness の生台帳)。
`repo_head=2f81522e8c51ae83ea1a0f260397f54bcbaf4487`、baseline `PASSED`。

```
KILLED 8 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0
registered 8, completed 8, matching 8
```

**8 件すべてが事前登録した exact な期待赤 node 集合と完全一致して KILLED になった** (`DW-M08`)。
`MISMATCH 0` は、赤の出方が予想と違うものが 1 件も無かったことを意味する。

| 変異 | 何を壊すか | 何が守ったか |
|---|---|---|
| `MUT-A1-MARKER-NOT-NECESSARY` | marker を `run_campaign` へ | 7 件 pin、bounded fixture、既存の registry exact |
| `MUT-A2-NFKC-DROPPED` | NFKC 正規化を外し生 source で判定 | bounded fixture の NFKC 正例のみ |
| `MUT-A3-NAME-PIN-TAMPERED` | 7 件 pin の `p3_kickoff` を 1 文字変更 | 名前 pin のみ |
| `MUT-B1-T189-ROOT-ONLY-GUARD` | t189 の欠落判定を根 directory の有無へ | t189 の missing-one 正例のみ |
| `MUT-B2-T189-GUARD-DOES-NOT-SKIP` | t189 の `pytest.skip` を `return` へ | 同上 |
| `MUT-B3-T1434-ROOT-ONLY-GUARD` | t1434 の欠落判定を根 directory の有無へ | t1434 の missing-one 正例のみ |
| `MUT-B4-B10-PROV-ROOT-ONLY-GUARD` | B-10 provenance 側を同上 | B-10 provenance の missing-one 正例のみ |
| `MUT-B5-B10-PLOT-ROOT-ONLY-GUARD` | B-10 plot 側を同上 | B-10 plot の missing-one 正例のみ |

### この変異が実証したこと

- **`MUT-A2` は「新しいテストだけが検出する差分」である** (`DW-M08` がテスト強化 wave へ要求する形)。
  生 source prefilter は現行 7 driver に対しては同じ結果を返すので、
  実 repo を見るどの検査でも区別できない。区別するのは bounded fixture の全角 `ｅ` 正例だけである。
  段 3 のレンズ A が見つけた穴が実際に塞がれていることの、機構を通った証拠になる。
- **`MUT-B1/B3/B4/B5` は 2026-09-01 に全 wave を止めた偽実装そのものを殺している。**
  「根 directory は在るが要求 file が 1 件欠ける」正例が 4 file それぞれで発火した。
- **`MUT-B2` は guard が実際に発火していることを示す。** `pytest.skip` を `return` に変えると
  guard が素通りして本体が走り、赤になる。

### 変異が確かめていないこと

- 資源が完全に在る環境での既存 assertion の不変性。これは焦点走 (233 passed) が担う。
- 計算ノード 48 並列での wall。変異は正しさの検査であって性能の測定ではない。
- 動的 git ignore 依存 (`output_snapshot_ignores.py`) と、`/mnt` 等の将来の prefix。
  どちらも本 wave の scope 外で、次の一手へ送った。

## 受入全走の実測 — 最遅 shard 388.3 秒 = 6.47 分。上限を 29% 超えている

段 9 で実走した受入全走 (`verdict=child-green`、`tested_main=ddf8cccab`、`tested_tip=d8f2a7e5b`、
`effective_scheduler=loadgroup`、**20135 passed / 92 skipped / 赤 0**) の junit から出した実測。

| shard | pytest wall | 仕事量の合計 | 最長単体 | 48 worker 完全詰め |
|---|---:|---:|---:|---:|
| **0** | **388.3 s = 6.47 分** | 6243.4 s | 153.1 s | 130.1 s |
| 1 | 236.5 s = 3.94 分 | 6933.9 s | 72.6 s | 144.5 s |
| 2 | 188.0 s = 3.13 分 | 2820.9 s | 82.3 s | 58.8 s |

**上限 5 分 (300 秒) を最遅 shard が 88 秒 = 29% 超えている。**

### 親の分析は 3 点で誤っていた (実測による訂正)

**訂正 1: 律速は「最長単体テスト 1 個」ではない。**
本 insight の上の節は duration ledger から「最長単体 140.0 秒が完全詰めの 83.0 秒を上回るので
並列度では下がらない」と論じた。**実測では shard-0 の最長単体は 153.1 秒、完全詰めは 130.1 秒で、
差は 23 秒しかない。** wall 388.3 秒との差 235 秒は最長単体では説明できない。

**訂正 2: 支配的なのは file 単位の束縛である。**
shard-0 の仕事量 6243.4 秒のうち、`test_s8b_oracle_driver` が 1881.4 秒、
`test_s8b_floor_campaign` が 1764.9 秒で、**2 file で 58% を占める。**
`tools/acceptance_shards.py` の割付は file 単位なので、この 2 file は分割されず同じ shard へ乗る。
さらに shard-0 の最長 3 件はすべて `test_s8b_oracle_driver` の中にあり
(153.1 / 148.6 / 145.0 秒、合計 446.7 秒)、**同一 file の重い node が同居している。**

**訂正 3: [T-1933] が攻めた対象は「別 file」ではなく、まさにこの file だった。**
上の節で親は「[T-1933] が攻めたのは `test_s8b_oracle_driver.py` 系の別 node で、
現在の最長 node はその対象ではない」と書いた。**実測ではこの file が現在の律速そのものである。**
[T-1933] の負結果 (cache 共有と process-memo grouping がどちらも効かなかった) は、
まさに今の律速に対する 2 回の失敗であり、「未試行」ではない。

**訂正 4: duration ledger の値は現況と食い違う。**
ledger は `test_role_sink_bytes_vary_only_at_declared_declassifications` を 140.0 秒として
最長に位置づけていたが、実測では 82.3 秒で shard-2 の最長にすぎない。
ledger は LPT 割付の hint であって権威ある測定ではない (D104 決定 4) という但し書きは
本 insight の上の節にも書いたが、**親はその値から「律速は何か」という構造的結論まで引いてしまった。
これは hint の目的外使用である。**

### 実測から言える、5 分へ届かせる道筋

- **file 単位の割付が効いていない。** shard-1 は仕事量が最大 (6933.9 秒) なのに wall は 236.5 秒で、
  shard-0 より 150 秒速い。仕事量ではなく**重い node の集中**が wall を決めている。
- したがって次の一手は「最長単体 node の分割」ではなく、
  **`test_s8b_oracle_driver` と `test_s8b_floor_campaign` の 2 file を跨いで node を再配分できるか**である。
  現行の `_components()` は file と xdist group の二部グラフを union するため、
  file 内の node を別 shard へ出すには割付の粒度自体を変える必要がある。
- ただし [T-1933] が同 file に対して 2 度失敗している。3 度目を試みる前に、
  **なぜ 145〜153 秒かかるのか**を先に測るべきである (build か、直列性検査か、外部 command か)。
