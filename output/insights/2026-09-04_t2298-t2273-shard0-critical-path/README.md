# [T-2298][T-2273] certified_evidence の read/write lock 化と、受入 shard-0 の律速の実測

- authority: none (可変状態の正本は worklog と decisions。本書は一次資料の置き場)
- default_effect: no-state-change
- wave: `worktree-dev-wave-t2298-certified-evidence-lock` (base = local main `1b7822110`、実装 commit `b47cf3975`)
- 実測日: 2026-09-04〜05 (Pegasus login pegasus02、計算ノード bnode019 / bnode080 / bnode095 / bnode035)

## 1. 何をしたか

1. `orchestrator/tests/test_p3_b4_raw_record_producer.py::certified_evidence` を「seed 生成だけ `LOCK_EX`
   (double-check 付き、metadata は temp + fsync + `os.replace`)、以後は読み手 `LOCK_SH`、書き手 `LOCK_EX`」へ変えた。
   書き手は共有 seed を一時的に変える M17 / M18 の 2 本だけで、別 fixture `certified_evidence_writer` を取る。
   17 consumer の assertion と node id は不変。lock 意味論の正例・負例、実 fixture の mode 別保持、yield 位置と
   mode 転送の AST、atomic metadata (production seed の call edge と write→flush→fsync→replace の順序)、
   writer 直接 path mutation の閉包 AST を足した (検査 10 本)。設計判断は decisions の当該 D。
2. 受入 shard-0 の律速を、既存 artifact (当日 9 走の junit / report.json) と新規 3 走 (M-A / M-B / M-C) で測った。
   詳細は `measurements.md`、生の解析出力は `measure/`。

## 2. 前提の反証 (段 1 の実測で覆った 3 点)

### 2.1 D1593 の「鎖 1 = real-repo group 303.7 秒の 1 worker 直列」は現行 run に存在しない

- `orchestrator/tests/conftest.py` の `pytest_collection_modifyitems` wrapper は yield 前に全 real-repo resource node へ
  `xdist_group("real-repo")` を付け、**yield 後に `_strip_real_repo_loadgroup_suffix` が process-memo 4 node 以外の
  `@real-repo` suffix を剥がす**。xdist の loadgroup は suffix で group を決めるので、剥がされた node は worker に
  固定されない。この strip は commit `5ac638955` (2026-08-26) で入り、D1593 を起草した wave の tested_tip
  `62531b9a` の祖先である (`git merge-base --is-ancestor` rc=0)。
- 2026-09-04 21:16 走の shard-0 `report.json`: `group_to_workers["real-repo"]` は 38 worker、junit で suffix が残るのは
  process-memo の 4 件 (合計 0.0 秒) だけ。
- D1593 の 303.7 秒と 258.1 秒は `acceptance_duration_ledger.json` の合計値であり、走行の実測ではない。台帳は
  LPT 割付の hint であって権威ある測定ではない (D104 決定 4)。F832 と同じ型の再発として failures に記録した。
- 「過去の実測が虚偽」とは言わない。言えるのは「D1593 起草時点のコードに strip は在り、数字は台帳合計」まで。
- したがって D1618 (T-2297) が承認した「shard affinity を保ったまま worker grouping を read/write で割る」の
  **runtime 効果は既に在る**。未了なのは D1618 が要求した明示契約 (ItemRecord の affinity 属性、payload / parser、
  component と closure gate、`test_g6_*` の期待値) である。「T-2297 実装済み」とは言えない。scope の再裁定は
  worklog の次の一手 (ユーザー裁定待ち) へ送った。

### 2.2 「certified_evidence 鎖 = 258.1 秒」は台帳値で、現行は junit 合計 84.9 秒

- 21:16 走 shard-0 junit (setup+call+teardown) で 17 consumer の合計 84.9 秒。M-A (非 shard 全走) では consumer の
  setup 合計 ≈ 90 秒。fixture 内の lock 待ちは setup に含まれる (pytest の CallInfo 計測範囲)。
- 待ちは worker 間で重なるので、合計は critical path の wall ではない (段 3 レンズ B)。したがって本改修の効果は
  worker-time と鎖の解消であり、**単独で最遅 shard を 5 分へ入れる量ではない** (21:16 走の 411.9 秒から 84.9 秒を
  全部引いても 327 秒)。

### 2.3 t080 stub-free e2e (145〜155 秒/node) は build でも直列性検査でもない

M-B (`-n 0`、bnode019、2 回) の phase 内訳: base 構築 60〜77 秒 = 受領証発行の子 python 30 秒 + `git add -A` 7 秒 +
git 可視 output の複製 ≈ 10 秒 + submodule add 1 秒 + commit 2 秒、`verify_receipt` 1 回 2.3〜11.7 秒。
base は process 内 memo なので xdist worker ごとに繰り返され、受入では 11 node が 11 worker で各自 base を組む。
48 worker 同時では isolated (ledger 55 秒、M-B 単独 67〜72 秒) の 2 倍超になる。

## 3. shard-0 の wall 分解 — 分かったことと分からないこと

- 当日 9 走: shard-0 wall 251〜412 秒、最大 worker 占有 149〜234 秒 (常に item 2 個の worker = t080 系)。
  shard 1/2 の wall − 占有 は 57〜73 秒で一定、shard-0 は 95〜207 秒。
- M-A (全 suite 非 shard、bnode095): wall 487 = collection/起動 119 + test 361 + 7。48 worker 完全均衡、
  report に現れない待ち (2 秒超) は 0 件。M-C (shard-0 の 111 file 非 shard、bnode080): wall 250 = 56 + 190 + 5、隠れ待ち 0。
- 占有は setup/call/teardown の和で、`pytest_runtest_protocol` wrapper 内の real-repo lock 待ちは junit の testcase にも
  占有にも出ない (testsuite の wall には出る)。M-A / M-C はどちらも wrapper 待ちを timeline (report.start/stop) で
  観測できる形で取り、隠れ待ちは無かった。
- 受入形と非受入形の差 (0〜160 秒) は受入 plugin 側 (全 20452 node の collection と deselect、LPT 並べ替え、report 生成)
  と host 差の混合で、report.json に session timeline (collection 終了、各 worker の最初/最後の test、lock 取得/解放) が
  無い限り確定しない。これは裁定パッケージへ送った (新規 field、本 wave の scope 外)。
- 「shard-0 固有の原因」は因果として未証明 (host・時刻の交絡を切っていない。段 3 レンズ B)。

## 4. 段 3 / 段 6 のレビューで直したこと

- lens A (段 3): 実 fixture が yield まで lock を保持する配線が未検査 → 実 scope の NB 負例と yield 位置 AST を追加。
  seed 完了印 `evidence.json` が非 transactional → temp + fsync + `os.replace`、残骸掃除。
- lens B (段 3): 鎖 1 反証の射程、wall 表現、T-2298 の効果の限定、T-2297 の状態、shard-0 因果の格下げ (§2, §3 に反映)。
- lens C / D (段 6、独立に同一): 実 scope の検査が両 mode に `LOCK_EX|LOCK_NB` を当て、mode 定数化の退行が緑 →
  read では競合 SH 成功 / EX 失敗、write では SH 失敗を検査し、AST で `access_mode` の転送と wrapper の yield 入れ子を固定。
  lens C: atomic metadata 検査が production seed の call edge と replace の実体を固定していない → AST と assertion を追加。
- lens E (焦点再レビュー): 直接公開の検出が path 構文依存、fsync の順序未検査 → receiver 非依存の禁止と
  write→flush→fsync→replace の観測へ。fix は 2 巡で閉じ、以後は変異 h / i / j で裏取りした。

## 5. 変異

3 段で回した (probe → 本走)。harness は `tools/mutation_harness.py`、runner mode dispatch、統合 commit `b47cf3975` の
HEAD blob 束縛。spec と台帳は `mutation/`。

### 5.1 probe (全件 SURVIVED 期待で観測 node を集める、runner = 対象 file 全体、14 変異 + baseline)

baseline PASSED。負例 13 件はすべて赤 node を観測 (MISMATCH = 観測)。等価変異 1 件 (`locked = False` → `bool(0)`) は SURVIVED
(harness の SURVIVED 検出の正例)。

| 変異 | 観測した赤 (lock 検査) | 帰属 |
|---|---|---|
| a 書き手を LOCK_SH | writer_blocks_nonblocking_reader、fixture_scope_holds_both_modes | 主 + 実 scope |
| a2 writer wrapper が read | yield_is_inside_lock_ast (wrapper mode AST)、writer closure | 2 検査 |
| b 読み手が本体 lock を取らない | reader_blocks_writer、seeded_reader_never_requests_exclusive、seed_double_check、holds_both_modes | 帰属非一意 (事前登録どおり) |
| c / c2 M17 / M18 の書き手宣言を外す (alias 形) | writer closure のみ | 単一 |
| d double-check を外す | seed_double_check のみ | 単一 |
| e 読み手を LOCK_EX (旧挙動) | two_readers、seeded_reader no-EX、seed_double_check、holds_both_modes | 帰属非一意 (事前登録どおり) |
| f unlock してから yield | reader_blocks_writer、writer_blocks_reader、holds_both_modes | 実 scope 系 3 本 (yield AST は緑 = 予告どおり) |
| g helper 内を直接 write | atomic_replaced のみ | 単一 |
| h 共通 scope の mode を "write" 定数化 | holds_both_modes (主)、yield_is_inside_lock_ast (mode 転送、冗長) | 主 + 冗長 |
| g2 seed が metadata を直接公開 | seed_publishes_only_through_atomic_helper_ast のみ | 単一 |
| i helper を残して joinpath 直接公開を併置 | 同上のみ | 単一 (lens E MF-2A の反例を殺す) |
| j fsync を write の前へ | atomic_replaced のみ | 単一 (lens E MF-2B の反例を殺す) |

b / e / f では並走している reader consumer も赤になった (b: assembly 1 本、f: 8 本)。書き手 M17 / M18 の一時変異
(receipt の上書き、role_file の symlink 化) を排他なしの reader が観測した実例で、lock が実際に競合を防いでいる証拠。
ただし競走依存で非決定的なので、本走の完全一致集合には入れず、runner を `-k certified_evidence` (lock 検査 10 本) に絞った。
probe の台帳に原記録を残す (DW-M08 の「初回を probe と明記」に該当)。

### 5.2 本走 (KILLED 期待、期待 node = probe の lock 検査集合、runner = `-k certified_evidence`)

HEAD `b47cf3975`、baseline PASSED、**13/13 KILLED、等価 1 件 SURVIVED、14/14 期待一致 (MISMATCH 0、TIMEOUT 0、PARSE_ERROR 0)**。
期待 node 数: a 2、a2 2、b 4、c 1、c2 1、d 1、e 4、f 3、g 1、h 2、g2 1、i 1、j 1 (完全一致)。
b / e の帰属非一意は事前登録どおり冗長 gate として記録し、単独変異の証拠には主検査 (b: reader_blocks_writer、
e: two_readers) だけを数える。

## 6. 受入

段 6 の受入 (実装 tip `b47cf3975` + main `0679f61f4` の merge `7b585a1f1`、canonical `dev_wave_wait.py acceptance`、K=3、
48 worker): **verdict child-green、20488 passed / 68 skipped / 赤 0**。receipt は `acceptance-1-receipt.json`。

D1620 の面 (最遅 shard の wall、junit testsuite の time):

| 走 (2026-09-05) | shard-0 | shard-1 | shard-2 (p3_b4 を載せた shard) |
|---|---:|---:|---:|
| 本 wave (新 lock、00:24、bnode035 / 047 / 038) | 303.4 | 179.3 | 204.5 |
| 同時刻の別 wave (旧 lock、00:23、bnode009 / 017 / 018) | 331.9 | 203.3 | 223.4 |

同時刻の対走で、`test_p3_b4_raw_record_producer.py` の 17 consumer の junit 合計は 346 秒 → 290 秒、同 file を載せた
shard-2 の wall は 223 → 205 秒。ただし host が違い、shard-0 の差 (332 → 303) は本改修と無関係 (p3_b4 は shard-2)。
**5 分以内は達成していない (最遅 shard 303.4 秒)。** 21:16 走 (411.9 秒) との差は主に host と負荷の差であり、
本改修の寄与ではない。新 lock でも consumer が 10〜28 秒かかるのは、seed 生成 (≈ 10 秒) を最初の読み手が EX で
行う間に他の読み手が並んで待つこと (host あたり 1 回) と、書き手 2 本の EX 窓の間の待ちで、設計どおりの挙動である。

land 用の最終受入は記録 commit 後に同じ実装面で再走する (値は worklog の land 記録と receipt に残る)。

## 7. 主張しないこと

- 本 wave が最遅 shard を 5 分以内へ入れたとは主張しない。
- T-2297 が実装済みとは主張しない (runtime 効果はある、明示契約は未了)。
- D1593 の過去の測定が虚偽だったとは主張しない (台帳合計であった、と言う)。
- M-C の `test_p3_b4_raw_record_producer.py` の値と赤 1 件は、実装子の編集中に走った汚染で HEAD の値ではない。
- 受入の対走比較は host が違うため統制されていない。言えるのは同 file の consumer 合計と同 shard の wall の向きまで。
