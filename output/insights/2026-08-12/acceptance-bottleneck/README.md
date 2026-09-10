# 受入全走のボトルネック — 実測と裁定の逐語 (2026-08-12)

wave: `dev-wave-acceptance-bottleneck` / branch: `worktree-dev-wave-acceptance-bottleneck`
base: `a70a5acd` / 実装 tip: `be5018eb`

依頼は「受入全走のボトルネックを特定し、それを改善してください。並列化やより賢い仕組みで」。
**結論は「並列化は答えではない。受入は既にスケジュール下界に張り付いており、律速は鎖の中身」。**

## 1. 同定 (計算ノード、48 worker、非受入形 `-q --junitxml`)

| 量 | before (`a70a5acd`) | after (`be5018eb`) |
|---|---|---|
| pytest wall | 196.5 秒 | **161.2 秒** |
| `@real-repo` group の直列鎖 (床) | 176.7 秒 | **152.0 秒** |
| 直列総和 | 4631.9 秒 | 4110.4 秒 |
| 結果 | 0 failed | 9305 passed / 0 failed / 31 skipped |

**スケジュールでは 1 秒も取れない。** junit からの greedy シミュレーションは
before で現状順 202.6 秒 / LPT 176.7 秒 / 下界 176.7 秒、after で 197.3 / 152.0 / 152.0 秒。
**現状順と LPT の差は worker への到着順の綾であり、下界そのものは鎖の長さで決まる。**
[T-813] (438) がノード横断シャーディングを「受理集合を保てない」として不採用にしたのと合わせ、
**残る手は鎖の中身を等価に速くすることだけ**である。

## 2. 律速の内訳 (cProfile、repo 外 probe、計算ノード)

- **88.27 秒の `test_cli_subprocess_returns_rc_2_on_gate_refused`** (鎖の 50%):
  `verify_receipt` 55.2 秒 = `inspect_receipt_history` 30.1 秒
  (`_batched_history_touches_path` の diff-tree **28.0 秒**、descendant 2,460) +
  `_verify_holdout_live_scan` 24.3 秒 (`search_repository`: 11,988 file、re.search 107,721 回)。
- **152.11 秒の `test_verify_replays_complete_fake_codex_experiment`** (group 外の単体最長):
  `verify_snapshot` 47 呼 108.2 秒 = git subprocess 2,554 本 (poll 75.0 秒) +
  `_filesystem_file_set` 94 呼 **60.0 秒** (`_joinrealpath` 16.7 秒 +
  `_collections_abc.__contains__` 18.1 秒 = 親解決の重複が約 35 秒)。

## 3. 決定的発見 — diff-tree の 88% は `-C` 1 オプション

descendant 2,460 に対する argv 別実測 (login、read-only):

| argv | wall |
|---|---|
| 現行相当 `--root --raw -m -r -M -C --full-index --always -z` | **20.27 秒** |
| `-C` 抜き (`-M` 維持) | **2.37 秒** |
| `-M -C` 抜き | 0.93 秒 |
| pathspec 限定 (意味論不可) | 0.24 秒 |

## 4. 等価性の論証 — 要件は「論理和の不変」

`inspect_receipt_history` の 3 検査 (状態 OID / mode・kind / diff-tree) はいずれも同一の
refusal `receipt.history_mutated` を `_append_refusal` の dedup 付きで積み、
`issued_but_missing` も同じ値にする。**よって観測面は 3 つの論理和だけ**であり、
各項が個別に一致する必要はない。

`-C` 除去の差分は 2 形に限られる。

1. **receipt を source とする copy**: `-C` 無では destination が `A` になるが、
   destination OID clause (`dst_oid == expected_oid` かつ `dst_path != receipt`) が発火する。
   この clause は **status を見ない**ので `-C` の有無に依存しない。
2. **receipt を destination とする copy**: 親が descendant なら親側が receipt を欠くので
   **状態検査**が発火する。親が非 descendant (外部辺) のときだけ差が残る。

rename は `-M` を維持するので `R` として拾う。**残る差は「外部辺を跨ぐ copy-into-receipt」1 形**で、
これを現行 `-M -C` 付き command へ回して論理和を返す。
**command 形・parser・`--always` framing・fail-closed の例外種別・refusal 文字列は不変。**

実データ対検証 (`probe_c_equivalence.py`): 実履歴 descendant 2,460 で
現行 / `-C` 抜き / `-M -C` 抜きの両 clause 発火集合が**完全一致 (いずれも空)**。
**外部辺 commit は現 repo に 0 件。** これは happy path の非退行であり、検出力の同値は
合成履歴 control と変異が示す。

## 5. 敵対検証が親の設計を潰した (段 3)

BLOCKER 5 件。うち**親が自分で実測して確認した 2 件が決定打**。

- `git log --find-object` と `--pickaxe-all` は git 2.34.1 で**相互排他**
  (`fatal: --pickaxe-all and --find-object are mutually exclusive`)。
  段 2 プランの W1 設計は**そもそも実行不能**だった。
- `git hash-object --no-filters -answer` は `error: unknown switch` で拒否されるが、
  `-- -answer` は OID を返して**受理される**。`--` の追加は受理集合の変更である。
  sol と luna が独立に指摘し、親が実測で確認した。よって git batch 化は全面不採用
  (削減見込みも約 1.8 秒にすぎず、attribution 自体が誤っていた)。

## 6. 親自身の誤り 6 件 (すべて撤回済み)

1. 「状態検査 + `--find-object` の 2 本組で被覆できる」(実行不能)
2. 「W3 の git 呼びは batch へ畳める」(受理集合が変わる)
3. 効果見積りの帰属 (twins「2 本 87.6 秒」は各 87.6 秒の取り違え、
   同 tip の親計測 196.5 秒と brief の 177〜181 秒の不一致)
4. micro-probe の argv 取り違え (測ったのは提案 argv ではなかった)
5. 「+5%/日 → 約 19 日で倍」(増加モデル未定義)
6. 段 4 で sol の TOCTOU 所見へ「(a) は走査構造を変えないので非該当」と答えたが、
   **走査構造は不変でも resolve の呼び出し回数を変えていた** (段 6 で撤回、F1 で解消)

## 7. 段 6 の BLOCKER と、速度を諦めた取引

luna が「memo が sibling の `resolve()` 例外を握り潰す」を指摘。
段 4 裁定が「例外面を一切変えない」と約束していたので**約束の側を守り**、
`resolve()` は path ごとに毎回呼び、memo するのは
「解決済み親が root `.git` 配下か」という純粋な判定だけに縮小した。
**profile 上 `resolve()` 側 16.7 秒は取り戻せず、判定側 18.1 秒だけが残る。
速度のために例外面を変えない取引として意図的に選んだ。**

## 8. 焦点走の赤 1 件 — production ではなくテストの誤り

`pathlib._NormalAccessor.scandir = os.scandir` は **class 生成時に束縛**されるため、
`monkeypatch.setattr(os, "scandir", ...)` は `Path.rglob` に届かない。模擬が一度も発火せず、
参照実装側の assert が落ちていた。実 `chmod(000)` へ置き換え、拒否が本当に効いたことを
確かめてから本題に入る形にした (root では素通りするので黙って緑にせず理由付き skip)。

## 9. 変異 matrix — 8/8 KILLED

`mutation/mutation-ledger.json` (v2、`repo_head=be5018eb`、baseline PASSED、
KILLED 8 / MISMATCH 0 / SURVIVED 0、期待 node と実測が完全一致)。
**初回は probe** (`mutation-ledger-probe.json`、期待を `SURVIVED` で登録) で、
観測した失敗 node の完全集合から v2 を再登録した。

特筆すべき 2 件:

- **M2b** (`return ... or bool(external_edge_commits)` = 外部辺を持つだけで拒否する過剰拒否) は、
  段 6 で追加した negative control `test_external_edge_receipt_addition_is_accepted_negative_control`
  **ちょうど 1 本**に殺された。sol が「この変異を殺せるテストが無い」と指摘した穴が、
  実際に塞がったことの直接証拠である。
- **M12** (`resolve()` を loop から実質的に外す = **fix 前の実コードそのものの形**) は 6 node に
  殺された。恒久ルール「禁止したい形を wave 前の実コードが使っていたなら逐語を変異に登録する」に従い、
  段 6 の BLOCKER 対処が本当に検出されることを示した。

## 10. 測定精度についての警告 (成果より重要かもしれない)

**触っていない file に +77.3 秒の悪化が出たが、帰属は本 wave ではない。**
`test_campaign_import_invariant` は worker ごとに約 40 秒の同じ構築を重複して払う構造で、
payer が **4 worker (計 161.8 秒) から 6 worker (計 239.2 秒) へ増えた**だけである
(単価は 41.96→41.21 / 39.85→39.44 秒などで不変)。テスト所要が変われば xdist の割り当ても
変わるため、この重複は走行ごとに揺れる。

**含意: この suite で性能を語るとき、同一コードでも走行間で 80 秒級の差が出うる。**
n=1 の前後比較で 80 秒未満の差を主張してはならない。
本 wave の -35.3 秒 (wall) はこの幅の内側に見えるが、
**鎖 -24.7 秒と node 別 -40.9 秒は機序が特定済み**なので別である。

## 11. 裁定へ返した 3 件

- **holdout live scan 24.3 秒** — 受入の床に残る最大項。ただし `holdout_freeze.json` の
  generator pin と T-080 receipt の `metadata_fields` が `_verify_source` で
  **現行 worktree bytes と完全一致を要求**する (blob 救済なしの設計) ため、
  1 byte でも変えると freeze 再発行が要る。再発行の可否が裁定事項。
- **受理集合を強める 3 案** — `A` を mutation 扱い / exact blob の deletion を duplicate 扱い /
  introduction 以前から在る同一 OID の別 path を拒否。検出力は上がるが受理集合の変更であり、
  規律 2 の「緩めない」と対称に「勝手に強めない」を守って見送った。
- **`git hash-object` の leading-dash 拒否** — 正当なファイル名を option 誤認で拒否する。
  直すと受理集合が広がる。意図か否かの裁定が要る。
