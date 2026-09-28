# 段 4 裁定 — [md_3] Cicada を izanagi の正しさ検査器に通せるようにする (2026-09-29 04:1x JST)

入力: s1-brief.md、plan.md (段 2)、consult-a.md (C1〜C7)、consult-b.md (F1〜F9)。裁定 inbox を段 4 直前に再走査 (最新 2026-09-28 full39、Cicada の語 0 件)。local main は wave 開始後 51f896352 → 539556aa1 に進んだ (取り込みは段 6 受入の post-claim merge / 段 9)。
ユーザーは朝まで不在 (マネージャー連絡)。needs input 相当の判断は相談 2 本の賛否を材料に親が決め、根拠をここと fragment に残す。

## R0. peer 連絡の採用 (自分で裏取り済み)

- patch は `patches/ledger.json` に登録しない (`orchestrator/campaign/silo_ladder_rung1_contract.py:516-517` が entries ≠ 1 を拒否、現 ledger 1 件)。登録は `patches/README.md` だけ。
- patch の追加行の `#if` 条件に「どの patch の文脈行・削除行にも現れない語」を書くと、`orchestrator/tests/test_ccbench_spawn_sites.py:2917` (`_patch_added_define_interfaces`、`:657-747`) が condition_meaning_gate の DEFINE_SPECS との不一致で赤にする。DEFINE_SPECS は所有外。→ **新 patch の `#if` / `#elif` 条件に書いてよい語は `TRACE` だけ** (`TRACE` は既存 patch の文脈行に出現済みを実測)。壊し patch は裸マクロを持たない。
- `IZANAGI_[A-Z0-9_]+` の語を新 patch に含めない (`orchestrator/tests/test_p3_s4_loop.py:8682`)。

## R1. 所見の裁定

| ID | 裁定 | 採否と内容 |
|---|---|---|
| C1 読んだ版の忠実性 | real (予防) | 採用。読んだ時点の wts を TRACE 専用に保存し、commit 時の emit はその値を使う。emit 時に `ver_->ldAcqWts()` と照合し、不一致件数を終了時に stderr へ 1 行 (`CICADA_TRACE_READ_WTS_MISMATCH n=<n>`)。対照で n>0 なら事実として記録し段 6 で扱う。影響: 別版の ID を R に出すと辺が欠け、壊れた variant が巡回 0 に見える。 |
| C2 / F3 正例の帰属 | real | 採用。R4 の診断と帰属規則。発火件数だけで成功としない。同じ cell の stock 対照を必ず置く。 |
| C3 / F2 判定の上限 | real | 採用。一次資料・README・fragment では「Cicada の YCSB point read/update 履歴の巡回検出が可能になり、stock 対照で巡回 0 を観測した」と書き、certified・正しさゲート通過とは書かない。campaign の受理経路 (`orchestrator/campaign/pipeline.py`) への接続と X/P 相当の証拠面は scope 外。insight の「後続に要るもの」に記録 (研究前進の裁定パッケージ候補、起票はしない)。 |
| C4 版順の前提 | real (should) | 採用 (軽量)。起動器が TRACE build の stderr に出す `initial_wts` と trace を照合し、全 W の wts > initial_wts、verifier の version_dups / genesis_commits / orphan_reads が 0 であることを記録。一次資料では版 ID を「wts による版順」と書き、commit 時刻順と呼ばない。 |
| C5 flag 境界 | real (should) | 採用。受理構成 = 実測した CMake 値 (TRACE=1、INLINE_VERSION_OPT_CICADA=0、SINGLE_EXEC=0、WRITE_LATEST_ONLY=0、REUSE_VERSION=1、INLINE_VERSION_PROMOTION=1 (OPT=0 で不活性)、group_commit=0) を README と insight に固定。他は未検証と明記。 |
| C6 / F7 TRACE=0 の証拠 | real | 採用。`transaction.cc` と `ycsb_cicada.cc` (ほか patch が触る TU 全部) について、無 patch と instr patch の TRACE=0 build の (a) 同じ compile command の前処理出力の比較、(b) `objdump -d` の実行 section 命令列の比較 (正規化規則を保存)、(c) nm / strings の trace 残存 0 を計算ノードで取る。判定の根拠は (b)、(a) は差分調査用。 |
| C7 / F8 置き場 | real | 採用。R2。 |
| F1 verifier production を変えない | 論点 (real) | **親裁定: production code を変えない。** 理由: (1) 現行 parser / DSG は protocol 非依存で Cicada の v2 trace を読める (plan・相談 A/B とも確認)、(2) 形式的な差分は campaign_lock の source closure (`orchestrator/campaign/campaign_lock.py:58-63`) と既存 protocol の判定を揺らすだけで判定能力を増やさない (DW-G05)、(3) si の同型の先例 (T-2847) も verifier を変えていない。依頼の「検査器側の読み込みを実装する」は、Cicada 形の fixture テストで現行の読み込みが Cicada の版表現 (初期版 = genesis、wts 分割、read-only の古い snapshot、理由付き G2) を受理・検出することを固定する形で満たす。生死確認で具体的な受理失敗が出た場合だけ、その一点を最小修正する (その時は campaign_lock の束縛更新と既存 protocol の回帰確認を scope に入れる)。この読み替えは insight と worklog fragment に明記する。相談 B の「ユーザー裁定へ回す」は、マネージャー連絡 (ユーザー不在、codex と決めて進める) により親が決めて記録する形に置き換える。 |
| F4 初期値の伝達 | real | 採用 (plan どおり)。`ycsb_cicada.cc` の main で TRACE 専用変数へ `initial_wts` を渡し、未設定なら trace 実行を失敗させる。 |
| F5 拒否コード | real | 採用。D1464 の fail-closed は残す: 既存の `#if INLINE_VERSION_OPT` / `#if INLINE_VERSION_PROMOTION` の内側 (`cc/cicada/include/transaction.hh:199-215` 付近) に `#if TRACE` + `#error` を置く (新しい `#if` 条件に書く語は TRACE だけ、R0)。`SINGLE_EXEC` と `group_commit` の汎用拒否コードは作らず、起動器の条件固定と未対応範囲の記録で足りる。 |
| F6 件数照合 | real | 採用。C 行の件数は emit する set から書く (独立証人とは主張しない)。benchmark の commit counter を verifier の `--expected-commits` に渡す。emitter 内の二重照合と起動器独自の合計検査は作らない。 |
| F7 fixture の数 | real | 採用。Cicada 形 fixture は 2 本: `cicada_g1_genesis_readonly` (初期版 = (1,0) の R、read-only txn の古い snapshot の R、書く txn の wts 分割版、下位 32 bit ≥ 2^31 の tid を含む → indeterminate・巡回 0・integrity 0) と `cicada_g2_write_skew` (wts 分割版での rw+rw の G2、理由に key と版) 。焦点走は正例が帰属できない場合だけ。 |
| F9 検索陰性の書き方 | real (nit) | 採用。一次資料で「今回の検索式と対象では」と書く。 |

## R2. 置き場 (D fragment)

trace hook は `patches/instr-cicada-trace.patch` (無マクロの無条件計装、変更は `#if TRACE` の内側だけ) として置く。**試作・実走用の置き場**であり、D16 の本来の置き場 (`izanagi-trace` 枝) への移送と gitlink の前進は人間の判断として保留する (si の [T-2847] と同じ根拠。D16 の T-109 例外は D579 により流用しない — これは例外の適用ではなく、gitlink を動かさない依頼の制約下での試作配置)。壊し patch は D16 どおり永久に patch。decisions fragment 1 件に記録する。

## R3. プラン v2 (段 5 の単位)

- **単位 L0 (Codex author、先行):** `patches/instr-cicada-trace.patch` と repo 外起動器 `.cicada-launcher/launch_cicada_run.py` (単位 worktree 内に書かせ、親が job dir へ退避)。
  - hook: 書く txn は `cpv()` 成功後・set clear 前 (`cc/cicada/transaction.cc:895-913` 付近) に C/R/W/E、read-only は `commit()` の早期 return 前 (`:934-937`) に C/R/E。txid は emit 開始時に `next_txid()` で 1 回。C 行は `C <txid> <thid> <hi> <lo> <read_count> <write_count>` (thid は整数 cast)。書く txn の版 = 自分の wts、read-only の C 版 = 自分の wts (どちらも `(wts>>32, wts&0xffffffff)`)。R の版は読んだ時点に保存した wts (C1)、`== initial_wts` なら `(1,0)`。W の op は U/I/D。abort 経路は何も出さない。
  - `ycsb_cicada.cc` の main で `initial_wts` を TRACE 専用変数へ渡し、TRACE build は stderr に `CICADA_TRACE_INITIAL_WTS=<n>` を 1 行出す。
  - D1464 の `#error` (R1 F5)。共有 header (`include/trace.hh` ほか) は変えない。
  - 起動器: si の `launch_si_run.py` を雛形に target `ycsb_cicada.exe`・`--protocol cicada`・Cicada の CMake 値 (C5) を固定・記録、YCSB flag は Cicada の名前。benchmark の commit counter を `--expected-commits` へ渡す。patch hash・適用順・toolchain・raw trace・stdout/stderr・verifier JSON を保存。TRACE=0 同一性 (C6) の mode を持つ。
- **単位 C (Codex author、L0 と並列):** `orchestrator/tests/test_verifier.py` に Cicada 形 fixture の test を足し、fixture は `orchestrator/tests/fixtures/cicada_g1_genesis_readonly/`・`cicada_g2_write_skew/`。verifier production は変えない。
- **生死確認 (親、L0 統合後):** R5 の L0 job。成立しなければ壊し patch を作らず事実を返して止める。
- **単位 B (Codex author、生死確認成立後):** 壊し patch 3 本と、起動器の帰属解析 (R4)。

## R4. 壊し patch と帰属 (事前登録)

各 patch は instr patch の上に重ねる無条件 patch (裸マクロなし、既定で重ならない = 別 checkout の正例 build にだけ当てる)。1 本ごとに壊す site は 1 つ。

| patch | 壊し方 | 事象 (event) | 帰属規則 |
|---|---|---|---|
| `broken-cicada-skip-read-recheck.patch` (md_3「version consistency check を飛ばす」) | validation の read set 再検査 (`transaction.cc:543-570`) で不一致を見ても abort しない | 不一致を見て abort を飛ばした read 要素: tx_wts・key・read_wts・visible_wts | witness の巡回に、tx_wts の txn から key 上で rw 辺 (u_ver = read_wts の版) がある |
| `broken-cicada-no-rts-update.patch` (md_3「rts を更新しない」) | `readTimestampUpdateInValidation()` の呼出し (`transaction.cc:536` 付近) を外す | 元なら rts を引き上げた read 要素 (ver の rts < tx_wts): tx_wts・key・read_wts | witness の巡回に、tx_wts の txn から key 上の rw 辺があり、その先の版の wts < tx_wts |
| `broken-cicada-stale-read-ro.patch` (md_3「古い版を読んだまま commit させる」) | read-only txn の可視版選択 (`read_internal`、`transaction.cc:79-138`) で、txn 内の偶数番目の読みに限り、可視版の 1 つ古い committed 版を選ぶ (read-only は validation を通らないので他の検査に止められない) | 古い版を選んだ読み: tx_wts・key・chosen_wts・skipped_wts | witness の巡回に、tx_wts の txn から key 上で rw 辺 (u_ver = chosen_wts の版) がある |

- 診断: 事象は thread ごとに溜め、その txn が commit したときだけ stderr へ `CICADA_BREAK_EVENT slug=<slug> tx_wts=<n> key=<hex> a_wts=<n> b_wts=<n>` (thread あたり先頭 200 件まで) を出し、abort なら捨てる。終了時に `CICADA_BREAK_FIRED slug=<slug> reached=<n> changed=<n> committed=<n>`。`IZANAGI_` の語を使わない。診断は verifier の判定に使わず、帰属解析 (起動器) だけに使う。
- 分類: 「期待した経路で検出」= non-serializable かつ帰属規則を満たす witness が 1 つ以上、かつ同じ cell の stock 対照が巡回 0。「検出したが帰属不能」= 巡回ありだが規則を満たす witness なし。「盲点」= committed>0 で巡回 0。「未発火」= changed=0。
- 未発火・盲点・帰属不能の patch は、事前登録の焦点 cell (tuple 50、thread 8、ほかは同じ) で 1 回だけ再走してよい。
- **完了判定: 3 本のうち 2 本以上が「期待した経路で検出」。** 満たさなければ判定を緩めず、事実を一次資料に書いて段 4 へ戻る。

## R5. cell と job (事前登録)

共通 = `ycsb_tuple_num=200 ycsb_zipf_skew=0.9 extime=1 clocks_per_us=<計算ノードの値、起動器が記録>`、group_commit=0、CMake 値は C5。

| cell | YCSB | 使い道 |
|---|---|---|
| K | rratio 50、rmw false、max_ope 10 | write skew (読みと書きが別 key)。stock 対照、skip-read-recheck、no-rts-update |
| W | rratio 0、rmw true、max_ope 5 | 生死確認のみ (RMW) |
| R | rratio 90、rmw false、max_ope 4 | read-only txn が多い条件。stock 対照、stale-read-ro |

| job | build × cell × thread | 期待 |
|---|---|---|
| L0 (生死確認) | stock+instr の K・W × t1・t4、TRACE=0 同一性 (C6) | 全 run で framing violation 0、integrity 0、巡回 0、indeterminate、commit 数一致、`READ_WTS_MISMATCH n=0`、TRACE=0 の命令列一致・trace 残存 0 |
| J1 | stock+instr の K・R × t4 (対照) + skip-read-recheck の K × t4 + no-rts-update の K × t4 | 対照は L0 と同じ。正例は R4 |
| J2 | stock+instr の R × t4 (対照) + stale-read-ro の R × t4 | 同上 |

見積り: build 1 本 ≈ 2〜3 分 (未実測)、run 1 本 ≈ 数十秒。L0 ≈ 10 分、J1 ≈ 15 分、J2 ≈ 10 分、焦点再走 ≤ 10 分、変異 matrix・受入 ≈ 40 分。合計 ≈ 1.5 node 時間 < 2 (L0 実測後に更新)。

## R6. 変異 (DW-M01 事前登録)

- **実系の変異 = R4 の壊し patch 3 本** (Cicada の実装への単一 site の変異。kill = 分類「期待した経路で検出」)。
- **verifier 側の新テストの検出力 (DW-M08):** 変異 M-V1 = 版の圧縮表現で tid 成分の扱いを 31 bit に狭める (site は `orchestrator/verifier/dsg.py` の版 pack、段 2 plan の `dsg.py:37-69`。実装後に一意な置換位置を確定し、同じ入力を止める層が他に無いことを確認してから本走)。期待: 新 test `cicada_g1_genesis_readonly` (tid ≥ 2^31 を含む) が KILLED。変更前 HEAD のテスト集合では SURVIVED を期待 (観測値をそのまま記録)。単一理由性が確認できなければ登録を取り下げ、実効 gate へ再照準する。
- 単位 L0・B の patch と起動器は repo 外の実走で検証し、pytest の変異 matrix の対象外 (起動器は repo 外)。

## R7. 所有 (素集合)

- L0: `patches/instr-cicada-trace.patch`、`.cicada-launcher/launch_cicada_run.py` (repo 外へ退避)。
- C: `orchestrator/tests/test_verifier.py`、`orchestrator/tests/fixtures/cicada_g1_genesis_readonly/**`、`orchestrator/tests/fixtures/cicada_g2_write_skew/**`。
- B: `patches/broken-cicada-skip-read-recheck.patch`、`patches/broken-cicada-no-rts-update.patch`、`patches/broken-cicada-stale-read-ro.patch`、`.cicada-launcher/launch_cicada_run.py` (L0 統合後の版から)。
- 親: `patches/README.md` 節、insight、fragment、job dir の script。

## R8. 追補 (04:05 前後、単位 U-C の報告を受けて)

`orchestrator/tests/test_verifier.py` の fixture 一覧固定 test 2 本 (`test_all_v2_fixture_files_have_clean_framing` の `_V2_FIXTURE_FILES`、`test_capacity_all_fixture_results_match_frozen_baseline` の `frozen`) が新 fixture を未収載として赤にした。両者は一覧の完全一致を要求する登録簿であり、新 fixture の登録は既存 entry・既存の判定を変えない追随である (登録しないと新 fixture が framing 検査と列指向 builder / 基準 builder の同値検査から外れる)。→ 既存 entry を 1 byte も変えずに cicada の 4 file と 2 entry を足す。`frozen` の新 hash は test 自身と同じ手順 (`_capacity_tuple_result` と一致を確かめた `verify_trace_dir` の `result_to_dict` に `trace_dir` を入れた sort_keys JSON の sha256) で求め、verifier production は変えない。

## R6 erratum (05:0x、login self-run の観測、事前登録は書き換えない)

M-V1 (`orchestrator/verifier/dsg.py:44` の `_packed_version` で `| tid` → `| (tid & ((1 << 31) - 1))`) の login self-run (`PYTHONPATH=. python3 orchestrator/tests/test_verifier.py`、DW-O19 で復元・sha256 一致・porcelain 0):
- 新 HEAD 0c092586b: 基準 143 passed / 0 failed → 変異 139 passed / 4 failed。赤 = `test_capacity_all_fixture_results_match_frozen_baseline`・`test_capacity_packed_versions_preserve_bounds_duplicates_and_notes`・`test_cicada_g1_genesis_readonly_versions`・`test_cicada_g2_write_skew_versions_and_reasons`。
- 変更前 HEAD 51f896352: 基準 141 passed / 0 failed → 変異 140 passed / 1 failed。赤 = `test_capacity_packed_versions_preserve_bounds_duplicates_and_notes`。
- **事前登録の「変更前 HEAD では SURVIVED」は外れた** (既存の packed 境界 test が同じ変異を検出する)。M-V1 は新テストだけが検出する差分を示さない。新テストは同じ変異を追加 3 node で検出する (Cicada の版表現の回帰 pin)。再照準はしない: verifier は protocol 非依存で、Cicada 形 fixture にだけ効く verifier 側の単一 site 変異は今回の検索で見つけていない。実系の検出力の証拠は R4 の壊し patch 3 本である。
- dispatch final は段 6 の最終実装 commit で、M0 (等価のコメント変更、SURVIVED 期待) と M-V1 (新 HEAD: 上の 4 node で KILLED、変更前 HEAD: 上の 1 node で KILLED) を再登録して走らせる。
