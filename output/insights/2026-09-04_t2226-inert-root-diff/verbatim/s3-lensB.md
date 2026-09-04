## A-2 への到達性

- 結論: 計画どおり実装されれば、現在の `preprocess-root-dependent-builtin` 関門は A-2 の inert supply で緑へ到達する。静的検査上、別の理由で必ず赤のままになる反証はない。ただし実走していないため、configure や toolchain の偶発失敗まで含む「A-2 全体が緑」は未確認。

- 実 path は次の構造になる。

  - `source_root`: compute job が渡す clean な `external/ccbench`。`run_workload` が resolve する (`paper_story_a2_certification.py:3039-3041`)。
  - `variant_root`: `patchharness.checkout` が `$TMPDIR/izanagi_wt_*/wt` に作る別 worktree (`patchharness.py:346-364`)。A-2 はここへ patch を当てる (`paper_story_a2_certification.py:589-605`)。
  - `stock_root`: clean な元 `source_root` (`paper_story_a2_certification.py:606-612`)。
  - requested build root: 別の `TemporaryDirectory` 配下の `requested`、control build root: 同じ一時 base 配下の `stock` (`condition_meaning_gate.py:1747-1779`)。
  - CMake はそれぞれの source/build root を `-S/-B` に置き、同じ dependency prefix と `FETCHCONTENT_BASE_DIR` を追加する (`condition_meaning_gate.py:1582-1589`, `paper_story_a2_certification.py:598-611`)。

  したがって計画の二対応、`variant_root -> source_root` と `requested build -> stock build` は実際の差へ届く。

- 現行赤の根拠も成立する。owner TU は `ERR` を実際に展開する (`external/ccbench/cc/silo/transaction.cc:106`, `:690`)。`ERR` は `NNN` を介して `__FILE__` を出す (`external/ccbench/include/debug.hh:54-64`)。現行 gate は dependency 内の `__FILE__` を記録し (`condition_meaning_gate.py:2028-2063`)、inert 時だけ source/control root を needle に加えて赤にする (`condition_meaning_gate.py:2409-2433`)。

- ただし brief の「inert cell」は単数化しすぎている。A-2 は 2 workload、4 cell (`paper_story_a2_certification.v2.json:31-43`, `:81-117`) で、全 genome に `BACKOFF_NOINLINE=0` が加わる (`paper_story_a2_certification.v2.json:45-50`, `paper_story_a2_certification.py:561-573`)。1 workload あたり stock cell は `BACKOFF_FIXED=-1` と `BACKOFF_NOINLINE=0` の2 inert arm、adopted cell も `BACKOFF_NOINLINE=0` の1 inert armを持つ (`paper_story_a2_certification.py:613-629`)。A-2 全体では6 inert supply 評価である。

- 計画の新正例は `BACKOFF_FIXED=-1` だけである (`s2-plan.md:102-115`)。A-2 の残る default-equality 経路、`BACKOFF_NOINLINE=0` の root-only 差を直接覆わない。実装を `request.stock_comparison` に誤って限定すると、こちらは `stock-inert-mismatch` のまま残る。新正例は両 macro を parameterize すべきである。

  成果物影響: この漏れが実装へ入れば全 workload が condition admission 前に停止し、certified result、raw material、trial ledger は作られない。

- 「構造的に常時赤」は現在の A-2/CMake 経路には当てはまるが、gate 一般の不変条件ではない。compile argv の source operandが相対表記なら `__FILE__` が absolute root needle を含まない可能性がある。gate は compile argv を解決後の absolute pathへ書き換えていない (`condition_meaning_gate.py:1939-1992`)。brief の結論は現構成についての実測命題として扱うべきで、「あらゆる構成で構造的」と一般化してはいけない。

## 効く層の網羅

- arm record 発行層に型上の阻害はない。`_issue_arm_record` は evidence を含めて digest を作り、直ちに integrity 検査する (`condition_meaning_gate.py:923-987`)。tuple/int/bool は canonical JSON 化できる (`condition_meaning_gate.py:680-709`)。

- admission 層にも reason whitelist はない。green record の schema/integrityを先に検査した後、受理判断は supply の `terminal_status == "green"` と meaning 非 red だけである (`condition_meaning_gate.py:3733-3748`)。新 reason が schema に登録されれば A-2 admission は通る。反証なし。

- A-2 集計層も reason/evidence を exact 比較しない。record をそのまま canonical JSON 化し (`paper_story_a2_certification.py:686-696`)、不受理時だけ reason/detail を診断へ使う (`:674-684`)。summary に receipt を付け (`:3140-3142`)、CLI stdoutへ出す (`:4208-4215`)。

- ただし condition receipt は A-2 の cell raw recordや certification reportへ直接取り込まれず、`summary.condition_gate_receipts` と scheduler stdoutに留まる。これは既存の証拠伝搬境界であり、新 reason 固有の不整合ではない。

- scope 外で実際に壊れる層が1件ある。T316 の admission 自体は新 green を受け入れるが、その後の `_condition_gate_family_valid` が旧 reason/comparison を exact 要求する (`t316_sandbox_backend_probe.py:346-374`)。実 CCBench 側は source を別 rootへ copyして stock controlを作る (`t316_sandbox_backend_probe.py:1873-1882`) ため、`__FILE__` 差は新 reasonになる。結果は `S6_CONDITION_GATE_UNPROVEN` (`t316_sandbox_backend_probe.py:386-390`)。

  成果物影響: T316 receipt の S6/overall verdict が `go` にならず、sandbox backend の採用判断を前進させない。

## consumer と schema の整合

- 指定された3 consumerの観測は以下で確定する。

  - `test_t316_sandbox_probe.py`: supplied fixtureには `__FILE__`/`__BASE_FILE__` がなく、requested/control bytes は raw identical。引き続き `stock-inert-preprocess-identical` / `stock-inert-identity` (`test_t316_sandbox_probe.py:138-180`)。
  - `test_backoff_sweep.py`: 同じ supplied/stock fixtureを使うため、引き続き旧 reasonで digest equality (`test_backoff_sweep.py:146-164`)。
  - 実 T316 probe: actual sourceと別 rootの copyを比較するため、新 `stock-inert-preprocess-root-location-only` / `stock-inert-root-location-only`。しかし旧 exact consumerが拒否する (`t316_sandbox_backend_probe.py:367-374`)。

- schema の3点整合には反証なし。

  - 新 reason の場合だけ required keyを28件へ増やせば、既存2 greenの exact key集合は不変 (`condition_meaning_gate.py:3302-3323`)。
  - status contractを `("stock-inert-root-location-only", False)` とすれば、raw mismatchから来る digest inequalityと整合する (`condition_meaning_gate.py:3399-3412`)。
  - tuple row、exact int、exact bool は canonical digestで受理可能 (`condition_meaning_gate.py:680-709`)。

- ただし計画された validator は replacement pairの形だけを検査し、実際の `-S/-B` rootとの一致を束縛していない (`s2-plan.md:77-80`)。`requested_configure_argv` と `control_configure_argv` には実 rootが存在する (`condition_meaning_gate.py:1582-1589`, `:2235-2239`)。新 green schema検査で各 `(kind, requested_root, control_root)` をそれぞれの exact `-S/-B` 値へ照合すべきである。そうしないと evidence は任意の別 root対応を主張でき、digestからも再検証不能になる。

  成果物影響: admission集合は直ちには広がらないが、材料レポートや試行台帳に記録される「置換した root」の参照が実 configure と食い違い得る。

- red recordへの3 field追加は拒否されない。integrity validator は green だけ arm-specific schemaへ送る (`condition_meaning_gate.py:3685-3689`)。red は一般 mapping検査と canonical digestだけを通る (`:3682-3704`)。したがって exact tuple/int/boolなら発行可能である。

  ただし classified redの record digest/record IDは従来から変わる。成果物影響: 新規 trial ledgerや診断 receiptの参照 IDは変わるが、redは admissionされないため受理集合は広がらない。

## 非 inert 経路と同型 driver への波及

- 非 inert 経路については反証なし。compiler/comparable argv検査後、root builtin、closure equality、bytes differenceを従来順のまま `if not stock_identity` 内へ移せば、`requested-default-difference` の受理集合は変わらない (`condition_meaning_gate.py:2396-2451`, `s2-plan.md:17-29`)。helperを inert 分岐からだけ呼ぶことが条件である。

- `s5_permutation_coverage` は `requested=1/default=0`、stock rootなしの非 inert requestだけなので不変 (`s5_permutation_coverage.py:77-104`)。

- 一方、変更は A-2専用ではなく、別 rootの stock comparisonを使う全 driverへ届く。

  - `backoff_sweep` とその helper利用者。patched working treeと別 checkoutを渡す (`backoff_sweep.py:105-129`, `:361-374`)。同 helperを使う `backoff_repro`, `backoff_requested_us`, `backoff_profile`, `backoff_overthrottle`, `backoff_extended_sweep` も location-only inertを新たに受理する。
  - `s1_direct_comparison` は variant用 worktreeとは別に stock worktreeを作り (`s1_direct_comparison.py:814-824`)、default equalityも inert扱いする (`:194-210`, `:266-304`)。
  - `screening_driver` は default equalityまたは spec-declared inertを全て stock comparisonにし、別 checkoutを与える (`screening_driver.py:78-107`, `:201-219`)。
  - `paper_story_a1_paired` (`paper_story_a1_paired.py:6594-6658`)、T1683 (`t1683_rr5_cost_probe.py:146-223`, `:236-243`)、`silo_ladder_rung1` (`silo_ladder_rung1.py:2110-2169`) も同型。
  - SS2PL studyも requested==default armへ別 stock rootを渡す (`run_ss2pl_lock_study.py:1989-2033`)。

- これらは D1523 が `evaluate_define_supply_effectuation` の inert 経路全体を対象にした結果なので、意味上は意図された拡張である。ただし plan の影響範囲記述は不十分であり、各 driverの新 reason receiptと admission変化を列挙すべきである。

  成果物影響: 従来 root builtinだけで拒否されていた driverが campaign/buildへ進み、新しい試行台帳・材料・測定結果を生成可能になる。受理集合は「root-only mismatch」の分だけ全 driverで広がる。

- 計算費用には強い反証がある。計画は `SequenceMatcher(..., autojunk=False)` を全行へ適用する (`s2-plan.md:31-43`)。実 preprocessing は `-P` 付きであり linemarkerを消している (`condition_meaning_gate.py:1990-1992`) ため、plan/brief の「linemarkerが差分anchorになる」という前提も誤りである。

- `SequenceMatcher` の worst caseは時間 `O(N*M)`、同程度なら `O(N^2)`。owner TU自体は741行、masstree cacheの C/C++ sourceだけでも約3.2万行で、標準C++ headersを展開した `-P` 出力は現実的に10万から30万行規模と見積もる。このとき worst-case比較量は `10^10` から `9*10^10`。さらに `autojunk=False` は空行や反復template行を popular tokenとして除外しないため、この worst-caseは机上だけではない。helperには subprocessの120秒 timeout (`condition_meaning_gate.py:1473-1502`) も掛からない。

  stock cellは2 inert arm、adopted cellは1 armなので、1 cellあたりそれぞれ最大2回/1回この計算を行う。好条件なら秒単位でも、反復行分布によって数十分以上へ跳ね得るため実用上予測不能である。

  成果物影響: scheduler walltimeまで pure Python差分が終わらず、cell record自体が発行されない可能性がある。

- 安い等価判定が成立する。

  1. raw bytes一致を先に受理する。
  2. `splitlines(keepends=True)` の行数不一致を即 red。
  3. 対応行を `zip` し、raw同一行は通過、不一致行だけ requested側へ一方向・最長一致・一回走査の root置換を施す。
  4. control行と byte完全一致を要求する。
  5. 不一致行の連続 run数を interval countとする。

  これは総 bytes数に対して `O(B)`。root置換は改行を生成しない実 A-2 pathなので、location-only差は行数と位置を保存する。insert/delete/reorderを再同期しない分、`SequenceMatcher` より弱くならず、むしろ fail-closedな受理部分集合になる。一般POSIX pathの改行だけは正例を偽赤にするため、rootに CR/LF があれば分類不能 redと明示すればよい。

## 親 brief の実測と一般化の検査

- 「DW-O09閉包0件」: 反証なし。`FROZEN_MANIFEST` は23件で、列挙は `output/s1-freeze`, `output/s8b-freeze`, 2026-07-16 insightだけ (`test_frozen_artifacts.py:41-88`)。現 `condition_meaning_gate.py` の SHA-256 literalもコード/成果物に存在しなかった。

- ただし T316は gate pathを runtime hash対象に含める (`t316_sandbox_backend_probe.py:2277-2283`, `:2327-2337`)。これは literal pinではないので refreeze不要だが、新規 T316 receiptの `runtime_sha256` は変わる。

- 「consumerは3件」: broadな件数としては誤り。旧 reasonの exact期待は、列挙された3箇所以外に `test_condition_meaning_gate.py:594`, `:613`, `:658`, `:691` の4件がある。gate自身の status contractも旧 reasonを exact keyとして持つ (`condition_meaning_gate.py:3399-3406`)。外部 exact読取だけでも7箇所・4ファイルである。

  一方、location-only新 reasonを実際に観測して壊れる既存 consumerは実 T316 probeだけで、6件の既存テストは root builtinを持たない raw-identical fixtureなので旧 reasonのままである。

  成果物影響: 件数漏れ自体は nitではないが、追加4テストの期待変更は不要。T316だけは実 receipt/verdictを変える。

- 「A-2 inert cellは構造的に常時赤」: 現構成については裏取りできた。ただし正確には6 inert armであり、root builtin tokenの存在だけではなく、activeな `ERR`展開と absolute `__FILE__`出力までが根拠である。briefはこの中間条件を省いて一般化している。

## 裁定パッケージ候補

- T316 reason contract:

  - 選択肢A: T316 validatorに旧 raw-identicalと新 root-location-onlyの両契約を明示許可する。
  - 選択肢B: T316は raw byte identity専用として新 reasonを拒否し、S6を引き続き inconclusiveとする。
  - 推奨: A。live recordは共通 gateの exact schema/integrityを既に通り、T316固有 validatorでは2組の `(reason, comparison, digest relation)` を閉じた集合として検査する。
  - 成果物影響: Aなら実 T316 S6が条件 gateを通過可能、Bなら新 gateを入れてもT316 verdictは前進しない。

- 比較アルゴリズム:

  - `SequenceMatcher` を捨て、行数一致＋同位置1対1比較へ変更する。
  - これは受理集合を広げず、実 A-2 pathについては等価であるため、新たな意味裁定ではなく計画修正で処理可能。
  - 成果物影響: verdictは維持しつつ、cell record未発行となる計算時間リスクを除ける。

- evidence root binding:

  - replacement rowを各 configure argvの exact `-S/-B`へ束縛する。
  - field追加なしで実装可能であり、これも計画補強で処理可能。
  - 成果物影響: trial ledgerに残る root対応が実 configureと一致することを機械検査できる。

- A-2 default-equality被覆:

  - 新正例を `BACKOFF_FIXED=-1` と `BACKOFF_NOINLINE=0` で parameterizeする。
  - 成果物影響: A-2の全6 inert armが同じ実装分岐へ到達することを固定できる。

## 総括

計画の中心判定には到達性があり、A-2を別の構造的理由で赤に残す反証はない。しかし、このままの計画は受入不可である。

必須修正は4点である。

- `SequenceMatcher` を線形の行数一致＋対応行比較へ置き換える。
- A-2の `BACKOFF_NOINLINE=0` root-diff正例を追加する。
- evidenceの root pairを configure argvの `-S/-B`へ束縛する。
- T316の旧 reason exact契約を別裁定または同時scopeで解く。

実走は行っておらず、pytest緑は主張しない。