静的レビューの結論は **NO-GO**。must-fix は 6 件です。pytest は実行しておらず、親既知の既存テスト赤は所見数に含めていません。

## 所見

### 1. runtime の「完全一致」は Python の equality spoof で通過できる

[severity: must-fix]

攻撃シナリオ:

`clocks_per_us` には exact `int` 検査がない。`registered.clocks_per_us` との `!=` を偽にしつつ、文字列化すると別値を返す object を渡せば gate を通過し、trace/bench には別の `-clocks_per_us` が渡る。`env_tag` も同様に exact `str` を要求していない。

根拠:

- runtime は値の `!=` 比較だけである。[execution_guard.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/execution_guard.py:78)
- `clocks_per_us` は実際の trace argv と bench に使われる。[pipeline.py:274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:274)、[pipeline.py:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:348)

提案:

比較前に `type(env_tag) is str`、`type(clocks_per_us) is int` を要求する。登録済み contract の値と比較する負例に、equality を偽装する object と `1800.0` を追加する。

成果物影響: 放置すると、登録値と異なる clock 引数で得た fitness が certified 選択・WAL COMMIT に入り、環境契約に従った測定として誤参照される。

---

### 2. build selector の同値 gate は subclass で迂回できる

[severity: must-fix]

攻撃シナリオ:

`ExecutionEnvironmentContract` の subclass に `__eq__`/`__ne__` を実装して登録済み authorization と等しいように見せる一方、calibration・isolation 等の field を変える。selector 同値検査を通り、後段も `isinstance` なので受理され、その forged contract hash の build namespaceを使う。

根拠:

- selector は exact 型を要求せず equality だけを見る。[execution_guard.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/execution_guard.py:91)
- pipeline と build cache は subclass を受理する。[pipeline.py:768](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/pipeline.py:768)、[buildcache.py:613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:613)
- build namespace は selector の contract hashで変わる。[buildcache.py:648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/buildcache.py:648)

提案:

`env_contract is not None` なら先に `type(env_contract) is ExecutionEnvironmentContract` を要求し、その後 authorization と比較する。custom-equality subclass の負例を追加する。

成果物影響: 放置すると、認可 contract と異なる自己署名 selector の binary が certified 選択・WALの build provenance に入る。

---

### 3. screening は認可より前に layout と WAL repair を書く

[severity: must-fix]

攻撃シナリオ:

`prepare_screening_campaign()` を呼ぶと、authorization を受け取る API がないまま `layout.ensure()` と `ensure_resumable_wal()` が走る。認可はその後、baseline callback 内の `evaluate_candidate()` で初めて行われる。不正 authorization を渡しても campaign directory と WAL repair は既に変更済みである。

根拠:

- 認可前の layout 作成と WAL repair。[screening_driver.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/screening_driver.py:101)
- 認可は後段の candidate 評価入口。[screening_driver.py:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/screening_driver.py:148)
- production caller も prepare 後に candidate を呼ぶ。[backoff_sweep.py:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/backoff_sweep.py:102)

提案:

`prepare_screening_campaign()` に authorization と runtime 値を必須化し、`layout.ensure()` より前に集中述語を呼ぶ。または書込みを行う prepare と純粋な設定生成を分離する。

成果物影響: 放置すると、認可されない run が campaign layout・WAL修復 receipt・再開状態を変更し、後続の certified 選択が参照する台帳状態を変える。

---

### 4. source commit が固定するのは adapter だけで、admission 本体は現 checkout 由来

[severity: must-fix]

攻撃シナリオ:

commit A で投入後、checkout を commit B へ進め、B の `certified_writer_admission.admit()` を弱める。wrapper は A の adapter を stream するが、その adapter は B の `$REPO_ROOT/orchestrator` を `sys.path` に追加して B の admission 本体を import するため、A の receipt の受理集合が B のコードで変わる。

根拠:

- wrapper が source commit から読むのは adapter 1 ファイルだけ。[floor_campaign.sh:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/floor_campaign.sh:83)、[t126_qualification.sh:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/tools/pegasus/t126_qualification.sh:101)
- adapter は現 checkout の orchestrator を import path にする。[certified_writer_preflight.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/certified_writer_preflight.py:44)
- 実際の gate はそこから import した `admit()` である。[certified_writer_preflight.py:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/certified_writer_preflight.py:48)

提案:

source commit 由来の admission closure 全体を、書込みなしの in-memory importer/immutable bundleで実行する。少なくとも A→B drift テストでは、B側 domain module を fail-open に変えても A job が拒否されることを検査する。

成果物影響: 放置すると、queued job の floor/T126 受理集合が receipt の `source_commit` ではなく後日の checkout に追随し、レポート・台帳が未束縛の gate 実装で生成される。

---

### 5. M2 は registry gate を削除しても後段 runtime gateに拒否される

[severity: must-fix]

攻撃シナリオ:

現在の M2 fixture は contract と runtime の `clocks_per_us` を同時にずらす。registry 同値検査だけを削除しても、runtime は `registered.clocks_per_us` と比較されるため同じ入力が拒否され続け、テストは通る。

根拠:

- M2 fixture は clock を変更し、runtime にも forged clock を渡す。[test_campaign.py:2245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:2245)
- registry check の後、runtime は authorization ではなく `registered` と比較される。[execution_guard.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/execution_guard.py:65)、[execution_guard.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/execution_guard.py:78)

提案:

runtime 3 値は登録値と同じまま、`calibration_ref` または `isolation_policy` だけを変えた exact dataclass を使う。これなら registry equality だけを削除した場合に受理される。

成果物影響: 放置すると、registry 同値 gate が将来消えて自己署名 contract の受理集合が拡大しても、変異台帳は誤って kill 済みと記録する。

---

### 6. P-2 正例は実 admission を一度も通っていない

[severity: must-fix]

攻撃シナリオ:

`certified_writer_admission.py` の任意の比較を「常に拒否」に変える。wrapper正例は環境変数だけで rc=0 を返す自己完結 stub、CLI正例は `admit()` 自体を mock しているため、actual domain admission が全 valid receipt を拒否してもテストは通る。

根拠:

- floor wrapper fixture は gate 本体を importしない stub。[test_pegasus_floor_tools.py:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_pegasus_floor_tools.py:200)
- T126 も同型の stub。[test_t126_pegasus_tools.py:735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_t126_pegasus_tools.py:735)
- CLI正例は `admission.admit` を mock している。[test_campaign.py:2431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:2431)
- actual admission を通る唯一のテストは空 `{}` receipt の負例。[test_campaign.py:2393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/tests/test_campaign.py:2393)

提案:

current registry、正しい protocol/calibration、receipt・ledger・qsub binding を持つ実 fixtureで `admit("floor")` と `admit("t126")` を直接通す。その同じ fixtureをwrapper境界正例にも使用する。

成果物影響: 放置すると、valid floor/T126 の受理集合が空になっても検出できず、予定されたレポート・qualification台帳・試行成果物が生成されない。

---

### 7. `numactl is None` の単独 branch は実効 gateではない

[severity: should-fix]

攻撃シナリオ:

[execution_guard.py:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/execution_guard.py:69) の `None` 分岐だけを削除しても、直後の exact list/tuple 検査が同じ `None` を拒否する。[execution_guard.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t609-certified-writer-closure/orchestrator/campaign/execution_guard.py:74)

したがって「この検査だけを無効化すると受理される入力」は構成不能で、この branch 単体は謳うだけで効かない。ただし no-`None` 性そのものは次の型 gateで維持される。

提案:

両者を一つの shape gate に統合するか、M4 を「69〜80行の検証を旧 falsy-collapse 全体へ置換」と明記し、単独 branch の kill と混同しない。

## 5条件の単一理由入力

| 条件 | その条件だけを消した場合に通る入力 |
|---|---|
| exact authorization 型 | `__eq__=True`、`__ne__=False` の contract subclass。runtime は登録値、site=OTHER、selector=None |
| registry 同値 | exact dataclassで runtime 3値は登録値のまま、calibration/isolationだけ変更 |
| runtime 完全一致 | 登録済み Linux authorization、`clocks_per_us=1801`、site=OTHER、selector=None。完全一致 blockを消すと通る |
| compute exact-Pegasus | site=PEGASUS_COMPUTE、登録済み Linux authorization＋Linux runtime、selector=None |
| selector 同値 | site=OTHER、Linux authorization＋Linux runtime、selector=Pegasus |

`numactl is None` の単独分岐だけは、上記所見7のとおり構成不能です。

## 既存テスト変更の監査

差分中に既存 `assert` の反転・緩和・削除、`pytest.raises` の除去、skip/xfail化はありません。

- `test_campaign.py` などの既存変更は、必須 authorization と登録済み runtime 値を呼出し fixtureへ追加したものです。
- `test_pegasus_floor_tools.py` と `test_t126_pegasus_tools.py` は新規 fixture/test の追加だけです。
- T126既存fixtureへの helper stub追加も、既存 assertion の変更ではありません。

また、既存検査を fail-open に変える削除は見つかりませんでした。新しい `except Exception` は admission/adapterでは rc=3/4 の非0へ倒れており、例外握り潰しによる受理拡大ではありません。

production caller の authorization は、15個の `run_campaign` caller、screening caller、S1、T126、S8b oracleとも registry lookupまたはregistry由来 planから渡されています。caller側で自由構築した authorization contract、すなわち自己署名は見つかりませんでした。

## 変異 M1〜M7

- M1: `None` を実際に素通りさせる変異は検出可能。ただし exact-type部分は、plain subclassが registry gateにも拒否されるため、現テストの赤は例外型差に依存し、独立した受理集合証拠ではない。
- M2: **kill不能**。runtime-vs-registry gateにmaskされる。
- M3: selector equality削除で write/refusal挙動が変わるため kill可能。
- M4: 事前登録どおり検証 block全体を旧 `tuple(numactl or ())` に戻す変異なら kill可能。`None` branch単独削除は冗長。
- M5: compute block削除で Linux contract が先へ進むため kill可能。
- M6: real wrapperが非0後に mkdir sentinelへ進むため kill可能。
- M7: preflightを最初のmkdir後へ動かすと同 sentinelで kill可能。

M6/M7テストは admissionの意味論ではなく、real wrapperの非0制御・順序を検査しているため、その限定された対象については fixture-only ではありません。一方、P-2正例は所見6のとおり actual admissionを通っていません。

## 総括

1. must-fix: **6件**

   1. runtime exactness の equality spoof
   2. selector subclass による同値 gate迂回
   3. screening の認可前 layout/WAL書込み
   4. source commit が admission closureを固定していない
   5. M2 の後段mask
   6. P-2 actual-domain正例の欠落

2. 判定: **NO-GO**

3. M1〜M7で現行テストが killできないもの: **M2**。加えて、M1のexact-type部分は有効な単一理由killになっておらず、M4の単独`None` branchは冗長です。