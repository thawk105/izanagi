# 段 4 裁定 (親) — 受入全走の所要短縮

wave `dev-wave-acceptance-wall-20260907` / branch `worktree-dev-wave-acceptance-wall-20260907`。
これがプラン v2 の正である。段 2 プランと段 3 レンズのうち、本書が上書きした箇所は本書に従う。

## 0. 親自身の訂正 (レンズ B の指摘を受け入れる)

- **訂正 1 — D1020 の引き金は成立していない。** 親は `C < W/48` を shard ごとに当てたが、
  D1020 の式は `C > W/(48K)` で `W` は**走全体の直列総仕事量**、`K` は shard 数である。
  走全体で `W = 18,587 秒`、`K = 3` なので `W/(48K) = 129.1 秒`、`C = 161.6 秒`。
  **`C > W/(48K)` であり、引き金は成立側にない。** 親の「D1020 の再検討引き金が成立した」は
  誤りであり撤回する。D1019 / D1020 は現時点でもそのまま有効である。
- **訂正 2 — L2 の効果予測を撤回する。** 親は「最忙 worker 191.6 → 100〜120 秒」と書いたが、
  レンズ B が正しく指摘したとおり、同時 miss した worker は build を lock 待ちへ
  置き換えるだけで、build 時間が並列度に依らないなら利得はゼロである。
  **ただし build 時間は並列度に依る** — 単独 60〜77 秒に対し 11 並列で 132〜155 秒
  (T-2298 実測)。したがって L2 の機序は「重複構築の削減」ではなく
  **「同時 build 数を 11 から 5 (basis は 2) へ減らすことによる競合軽減」**である。
  効果は事前に秒で予測しない。**同一 tip の paired A/B で示す** (D531)。
- **訂正 3 — L4 の「削除候補ゼロ」は誤り。** 親の AST 走査は body 120 文字未満を除外していたため
  短い重複を落としていた。下記 §4 のとおり 2 node が実際に冗長である。
- **訂正 4 — 基準線 324.3 秒は固定 tip の値ではない。** レンズ B のとおり 75 走は複数 tip の
  混合 (collection digest 40 種、universe 20,410〜21,111 件)。**前後比較には使わない。**
  A/B は同一 tip の対走で行う。324.3 秒は「現状はこの帯にいる」という所在の記述にのみ使う。
- **訂正 5 — `worker_occupancy.duration_s` は「その worker の busy 時間」ではなく
  `TestReport.duration` (setup/call/teardown) の合計**であり、protocol 外の lock 待ち・
  scheduler gap・collection・起動を含まない。親の「wall = 最忙 worker + 残差」は
  分解として有効だが、残差を collection と同一視してはならない。

## 1. 実装する (段 5 の scope)

### 単位 A — t080 base の host 共有 cache (L2)

段 2 プランの L2 を採用する。ただし次の must-fix を必ず満たす。

- **A1 (レンズ A blocker 1 の解消・必須)。** cache key に live repository の状態を束縛する。
  最低限、`git rev-parse HEAD`、`external/ccbench` の submodule HEAD、`known_axes` /
  `holdout` / 発行済み receipt の blob sha256、および `_git_visible_output_paths` が返す
  集合の digest を key に含める。束縛できない要素があれば **cache を使わず必ず再構築する**
  (fail-closed)。実 repository の再観測を凍結値の再利用へすり替えてはならない。
- **A2 (レンズ B B-04 の解消・必須)。** lock は **publish 直前まで**に限定する。
  copytree を lock 内で行ってはならない (48 worker の copy が直列化する)。
  publish は同一 filesystem 上の staging dir へ組んでから `os.rename` で atomic に行う。
- **A3。** test へ返すのは毎回独立実体の `shutil.copytree(..., symlinks=True)` だけとする。
  hardlink・共有 working tree・共有 document object は禁止。document は `copy.deepcopy` を維持。
- **A4。** cache root は pytest の session temp tree 配下に置き、別 session・別 worktree と
  共有しない。xdist 時は `popen-${PYTEST_XDIST_WORKER}` の親を共通 root とし、
  該当祖先が無ければ fail-closed。serial 時は現行の process-local cache を維持する。
- **A5。** nodeid・入力・assertion を一切変更しない。
- **A6。** builder 途中で process が死んだ場合、次の process は partial tree を読まず
  再構築できること。
- **A7 (限界の明記)。** 同一 uid の悪意ある test が cache path を直接改変することは隔離できない。
  この限界は insight へ明記し、process 隔離や権限制御を主張しない。

**変異で殺せる positive control** は段 2 プランの一覧をそのまま事前登録とする。加えて A1 の
key 束縛について「HEAD を変えても同じ cache が返る」変異が専用 test を赤にすること、
A2 について「lock を copytree まで保持する」変異が専用 test を赤にすることを追加する。

### 単位 B — 固定費の小改修と冗長 node の削除

- **B1 (L1-A)。** `tools/acceptance_shards.py` の `_canonical_item` 二重評価を除去する。
  `pytest_collection_modifyitems` で 1 度だけ評価し、`id(item) → nodeid` の対応表を再利用する。
  `_canonical_item` の呼出し回数が `len(items)` ちょうどであること、records / selected / loads /
  report の全 bytes が旧実装と完全一致することを `test_run_tests_shards.py` で固定する。
  **閉包 gate の入力も検出力も変えない。**
- **B2 (L4)。** 次の 2 node を削除する。どちらも同一入力・同一 assertion で、
  distinct input 集合も production call 集合も縮まないことを親が現物で確認した。
  - `orchestrator/tests/test_autonomous_trial_completeness.py::test_pre_raw_failure_allows_missing_raw_response_pointer`
    (`:2274-2276`)。残す側は同 file の `test_p3_role_invalid_partial_passes` (`:2019-2021`)。
    どちらも `run, _events, report = _role_invalid_trial(tmp_path)` と `_verify(run, report)` だけ。
  - `orchestrator/tests/test_codex_reasoning_ab.py::test_f176_preserves_decision_mentions` の
    `go_condition` param (`:13240`)。残す側は
    `test_f176_preserves_legitimate_opposite_mentions` の `go_condition_not_met` param (`:13266`)。
    入力 `("NO-GO。GOの条件を満たさない。", "NO-GO")` が逐語一致し、body も同一。
  削除に伴う pin (node 件数 golden、`acceptance_duration_ledger.json`、meta-test) を
  **同一 commit で原子的に**更新する。

## 2. 実装しない (段 5 の scope 外)

- **worker の collection を自 shard へ絞る案 — 不採用。** D711 が
  「各 shard が同一の全 collection を行ってから担当外を deselect する」を明示的に要求しており、
  gate 2 (shard 間 universe 一致) と gate 3 (login の独立 collect-only) の二重化で
  自己証明を断つ設計になっている。絞り込みは gate 2 の意味を失わせる。
  **§5 の裁定パッケージ 1 としてユーザーへ返す。**
- **L1-B (duration ledger の圧縮) — 不採用。** 効果が未測定であり、
  codec と検証経路を新設する。DW-G05 / 規律 5 により、実測で必要と示せるまで足さない。
  §6 の次の一手へ送る。
- **L1-C (controller prewarm 重畳) — 不採用。** 実装条件が timeline 計装であり、
  timeline は **T-2333 としてユーザー裁定待ち**である (DW-STOP)。上限も 4.17〜4.97 秒。
- **受入の timeline 計装 — 不採用。** 同上 (T-2333)。親は既に独立な 3 者の実測
  (自測定 87.57 / 27.44 秒、D1420 の 51.7 秒、T-2298 の M-A / M-C 119 / 56 秒) を持っており、
  計装なしで collection の寄与を述べられる。
- **L3 (duration 重み割付) — 不採用。** §0 訂正 1 により D1020 の引き金は成立しておらず、
  D1019 の結論がそのまま生きる。模型利得 11.6 秒は走間ばらつき 32 秒より小さい。
- **floor_campaign の clone 共有 — 不採用。** direct consumer が 1 node で cache hit が 0 件
  (段 2 プラン)。親の実測でも 1 本目に上乗せが無く、共有できる前置きが存在しない。
- **snapshot 3 node の削除 — 不採用。** レンズ A blocker 2 と peer session の判断が一致する。
  peer の未 land 変更 (`worktree-dev-wave-acceptance-speedup-20260905`) で片側が
  共有 module 実装になり、同一入力を 2 実装で照合する独立オラクルの対になる。
  片方を消すとこの独立性が失われる。

## 3. 段 5 の分割

所有 file が重ならないので並列でよい。

- 単位 A: `orchestrator/tests/test_s8b_oracle_driver.py`、新規
  `orchestrator/tests/host_tree_cache.py`、および単位 A 専用の新規テスト file。
- 単位 B: `tools/acceptance_shards.py`、`orchestrator/tests/test_run_tests_shards.py`、
  `orchestrator/tests/test_autonomous_trial_completeness.py`、
  `orchestrator/tests/test_codex_reasoning_ab.py`、
  `orchestrator/tests/acceptance_duration_ledger.json` および削除に伴う pin。

## 4. 効果の示し方 (D531)

- 実装後、**同一 tip の paired A/B** を行う。arm は `pre` (実装前 tip) と `post` (実装 tip)。
- 主要指標は 3 shard の junit `testsuite@time` の最大値。queue 待ちは含めない。
- 走間ばらつきが 32 秒あるため、1 走ずつの比較で勝敗を宣言しない。
- 併せて shard-0 の `worker_occupancy` の最大値と、t080 系 11 node の junit 合計を記録する。
  **こちらの方が機序に近く、効果の有無を先に判定できる。**

## 5. ユーザー裁定パッケージ

1. **受入 collection の重複を絞ってよいか (D711 の再検討)。**
   - 賞金: shard あたりの固定費が約 59 秒。48 並列 collection の親実測は全 file 87.57 秒に対し
     自 shard 絞り込み 27.44 秒。T-2298 の独立実測でも collection/起動が 119 → 56 秒。
     D1420 は collection 単体を 51.7 秒と確定している。**3 者独立に同じ向き。**
   - D711 の費用前提は失効した。D711 (2026-08-23) は
     「固定費が実測 12.86 秒しかないので全 collection を K 回払っても費用はほぼ増えない」を
     理由の 1 つにしていた。現在は約 59 秒で、約 4.6 倍である。
   - D711 のもう 1 つの理由「file を positional target へ渡す形は使えない」は**再現した**
     (shard-2 で `ModuleNotFoundError: No module named 'tests'`)。ただし原因を特定した:
     `test_s8b_approved.py:31` と `test_profiler_directive.py:341` が
     `orchestrator/` を `sys.path` に載せる**他のテストモジュールの import 副作用**に
     暗黙依存している。`--ignore` 方式でも同じ失敗になる。**2 file を自己完結させれば直る。**
   - **残る本質的な論点は 1 つだけ**: D711 の gate 2 (全 shard の `observed_universe` 一致) は
     「collection plugin が file を 1 件落としても全員が同じ縮小集合に同意して緑になる」経路を
     断つためにある。絞り込みはこの二重化を弱める。gate 3 (login の独立全 collect-only) は残る。
   - 選択肢: (a) 現状維持 (D711 のまま)、(b) 2 file の import 依存を直したうえで絞り込みを採用し、
     gate 2 の代替として「各 shard が collect した node 集合が割付と exact 一致すること」を新設する、
     (c) 絞り込みは採らず、gate を保ったまま collection 自体を速くする別案を探す。
   - **親の推奨: (b) を検討する価値がある。ただし gate 2 の弱体化は正しさ防壁の変更であり、
     親の一存では決めない。**

2. **T-2333 (受入 report.json への session timeline 追加) は本 wave では不要だった。**
   親は計装なしで collection の寄与を独立 3 者の実測から述べられた。裁定を急ぐ必要はない。

3. **T-2332 (D1618 / T-2297 の前提) は本 wave の scope 外。** 触っていない。

## 6. 次の一手 (本 wave では実装しない)

- L1-B: duration ledger の worker 転送量 (約 118 MB/shard) を減らす。採否は
  「転送が固定費の何秒を占めるか」の実測後に決める。
- t080 base を collection と重畳して組む案 (build 70 秒を固定費 59 秒へ隠す)。
  T-2333 とは独立に設計できるかを検討する。
