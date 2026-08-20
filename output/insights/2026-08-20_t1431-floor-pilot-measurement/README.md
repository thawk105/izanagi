# [T-1431] 床値 (floor value) pilot 実測 — 試行記録と新規 blocker

## 要約

D581 (decisions.md:23453) に従い、`orchestrator/campaign/s8b_floor_campaign.py` の pilot mode で
床値の実測を試みた。**投入・admission・toolchain束縛・protocol解決・依存ビルド (gflags/glog) までは
全て成功したが、mocc protocol の実ソースビルド準備段階 (`source_digest.resolve`) で新規の
fail-closed 停止に遭遇し、床値の実測値は得られなかった。** [T-1256] (既知の落とし穴として指定されて
いた pilot 承認フラグ問題) は本試行で解消済みと実証した。新たに発見した blocker は floor 実測に
固有ではなく、mocc protocol を使う限り (pilot/official を問わず) 再現する構造的な gap であり、
本 wave の scope 外と判断して実装せず記録に留める。

## 環境・実行パラメータ (D581 が求める記録)

- **実行環境**: Pegasus, queue=gen_S, nodes=1, elapstim_req_s=36000 (10h 割当)
- **投入元 commit**: `9fb5216624aed75a77ed9dff9760333e2cd2b9bb` (main HEAD 相当、worktree
  `dev-wave-t1431-floor-measurement` 経由)
- **submission nonce**: `70b9b8a087bb1e6d9af4ac248ff3c040`、request ID = `926261.nqsv`
- **投入コマンド**: `tools/pegasus/submit_floor.sh --confirm-irreversible-pilot-holdout`
  (標準投入経路、`--dry-run` で先に qsub argv を確認してから実投入)
- **ccbench pin**: `511c9538e4e8efa54b45cda62e72389ed3b706ec` (`external/ccbench` gitlink)
- **floor protocol**: `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json`
  (`resolve-current-protocol` の live 解決結果、rc=0。トップレベル `floor_protocol.json` の
  `ccbench_pin` は旧値 `d706650c…` のまま — 世代別ファイルが正で実行に影響なし)
  - `contract_sha256=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`
  - `stock_configuration=stock_common`、`n_sessions=8`、`reps=5`、`retry_slots_per_cell=2`
- **最適化 / build**: `buildcache.build_v2` 経由、trace-disabled (規律1)。実際の compiler/cmake
  実体は job-staging 配下の `compiler.path`/`compiler.version`/`cxx.path`/`cxx.version`/
  `cmake.path`/`cmake.version` に記録済み (bundle 退避対象、本 README では値を転記しない —
  一次資料は job-staging ディレクトリ自体)
- **perf**: 未到達 (build 段階で停止したため perf probe 前)
- **ワークロード**: 未到達 (12 セル中 0 セルが計測開始に到達)

## 成功した部分

1. **[T-1256] は既に解消済みと実証した。** `tools/pegasus/submit_floor.sh` (line 44, 489) は
   `--confirm-irreversible-pilot-holdout` を受け取ると `qsub -v` へ
   `IZANAGI_CONFIRM_IRREVERSIBLE_PILOT_HOLDOUT=<nonce>` を正しく載せる。`--dry-run` で2回
   (main checkout、wave worktree それぞれ) 実証済み。追加のコード修正は不要だった。
2. **preflight (投入前、本日実測) は全て green だった**:
   - `git ls-tree HEAD external/ccbench` = `511c9538e4e8efa54b45cda62e72389ed3b706ec`
   - `python3 orchestrator/campaign/s8b_floor_campaign.py resolve-current-protocol` = rc=0、
     現行 ccbench pin と整合する protocol へ解決
   - `python3 orchestrator/tests/test_frozen_artifacts.py` = 5 passed, 0 failed
   - oracle gate-check: rc=2、refusals = 厳密に `["floor-null: freeze.floor が null",
     "budget-null: freeze.budget が null"]` の2件のみ (設計どおり)
   - `qstat -u tanab` = 投入直前空 (T-139 等との競合なし)
3. **投入後の job 進行**: checkpoint.jsonl (`/work/1/SFC/tanab/izanagi-job-evidence/pegasus/926261.nqsv/70b9b8a087bb1e6d9af4ac248ff3c040/checkpoint.jsonl`)
   が示す通過段: bootstrap → static-admission → attempt-setup → policy → submit-binding →
   source-identity → allocation-reservation → gflags-build → glog-build → protocol-resolution →
   floor-driver (起動、run_dir 発行) まで全て正常に entered。toolchain 束縛検査 (R-4) も通過した
   (`job-staging/0:926261.nqsv/compiler.*`, `cxx.*`, `cmake.*` に実測値が残っている)。
4. job 全体の所要時間: 13:10 投入 → 13:15:06 実行開始 → 13:15:51 終了 (約 45 秒の実行、
   ほぼ全てが gflags/glog 依存ビルドに費やされた)。

## 新規 blocker: `source_digest.py` が mocc protocol の実供給マクロを認識しない

### 事象

`s8b_floor_campaign.py`(driver) が `build_cells` → `_prepared_binding` → `prepare_cell`
(`orchestrator/campaign/s1_direct_comparison.py:716`) → `source_digest.resolve()` →
`assert_conditional_macros_covered()` (`orchestrator/campaign/source_digest.py:557`) で
`RuntimeError` を投げ、driver 全体が rc=1 で終了した (floor_campaign.sh はこれを正しく検出し
`pilot floor driver returned nonzero` として fail-closed 停止・受入不能と記録した — floor_campaign.sh
自体の挙動は正しい)。

エラー全文 (`job-staging/0:926261.nqsv/floor-driver.stderr`):

```
RuntimeError: source_digest: cc/mocc/transaction.cc の条件指令が未知マクロ
['MQLOCK', 'RWLOCK', 'TEMPERATURE_RESET_OPT'] を参照 — 実 TU 供給マクロ・先行する #define・
CONTEXT_MACROS・builtin のいずれでもなく、digest はこの条件枝をどの文脈でも覆えない
(TU 注入マクロ GLOBAL_VALUE_DEFINE 型の identity 死角、偽 cache hit の運び屋) ため fails-closed
で停止 (T-148)。既知の文脈マクロなら CONTEXT_MACROS への登録 (= 両文脈 digest 化) が正しい封鎖で、
この検査の緩和ではない (規律2)。
```

### 根本原因 (file:line 裏取り済み)

`orchestrator/campaign/source_digest.py` の `parse_supplied_macros()` (269-291行) は、protocol の
実 TU 供給マクロ集合を次の正規表現だけで静的抽出する:

```python
_SUPPLY_RE = re.compile(r"(\w+)=\$\{CCBENCH_(\w+)\}")
```

一方 `external/ccbench/cc/mocc/CMakeLists.txt`:

```cmake
ccbench_add_protocol(mocc
  SOURCES   transaction.cc util.cc lock.cc
  WORKLOADS ycsb tpcc bomb sbomb
  OPTIONS
    RWLOCK
    TEMPERATURE_RESET_OPT=${CCBENCH_TEMPERATURE_RESET_OPT}
    KEY_SORT=${CCBENCH_KEY_SORT}
    INSERT_READ_DELAY_MS=${CCBENCH_INSERT_READ_DELAY_MS}
    INSERT_BATCH_DELAY_MS=${CCBENCH_INSERT_BATCH_DELAY_MS}
)
```

- **`RWLOCK`** は裸オプション (`=${CCBENCH_...}` を伴わない) であり、`_SUPPLY_RE` の
  `(\w+)=\$\{CCBENCH_(\w+)\}` という形には構造的に一致しない。ccbench 側は実際に `-DRWLOCK` で
  TU へ供給している (`ccbench_add_protocol` の OPTIONS はそのまま compile definition になる設計、
  `docs/protocols_ja.md` 等 ccbench 側 docs 参照)。
- **`TEMPERATURE_RESET_OPT=${CCBENCH_TEMPERATURE_RESET_OPT}`** は `_SUPPLY_RE` の形に一致する
  はずだが、それでも「未知」と判定された。これは `parse_supplied_macros(options_text,
  protocol_cmake_text)` へ渡される `protocol_cmake_text` が、実際には mocc の
  CMakeLists.txt を指していない (別 protocol のものか空) 疑いが強いことを示す — 正規表現の
  マッチ対象自体が違う可能性。この一次資料は未確認 (呼び出し元の特定まではしていない)。
- **`MQLOCK`** は現行 `cc/mocc/CMakeLists.txt` の `OPTIONS` に存在しない (`grep` で確認、
  ccbench 全体でも `-DMQLOCK` を注入する経路は見つからなかった) — 現行ビルド設定では
  常に未定義 (`#ifdef MQLOCK` ブロックは死コード)。コード中コメント (transaction.cc:635-637)
  は「RWLOCK: アップグレード時に該当」「MQLOCK: アップグレード機能が無いので不要」と対の
  実装であることを示唆しており、両者は排他的な選択肢である可能性が高い (要検証)。

### 影響範囲

- **floor 実測固有ではない。** `source_digest.resolve()` は EVOLVE-BLOCK 変異の identity 計算にも
  使われる共通経路であり (docstring より)、stock (未改変) の mocc ソースをビルドしようとする
  限り、pilot でも official でも、floor 以外の s8b/s1 系 campaign でも同じ壁に当たる可能性が高い。
- **stock configuration で発生した。** `stock_configuration=stock_common` は「LLM 変異を含まない
  基準構成」であり、EVOLVE-BLOCK の変異内容とは無関係。ccbench 側のソース/CMakeLists 構造と
  `source_digest.py` の想定パーサ形式の drift が原因であることを示す。
- 12 セル中 mocc protocol を使うセルが何個あるか (floor protocol の6構成の内訳) は今回未確認
  (`freeze` フィールドは `{path, sha256}` の参照だけで具体構成一覧は別ファイル)。

### この場で修正しなかった理由

- 修正は correctness/observer-effect 境界 (CLAUDE.md 絶対規律1・2・6、D23、T-148 の設計意図) に
  直接触れる `source_digest.py` の実装面変更であり、Codex `role=author` を要する。
- `_SUPPLY_RE` を単純に緩めて裸オプションを拾うだけでは不十分な可能性が高い —
  `CONTEXT_MACROS` は現在 1 要素までしか許容しない設計制約
  (`_merge_defines` 305-310行、「単発文脈列は結合枝を覆えない」) があり、MQLOCK が将来
  文脈マクロとして必要になった場合はこの制約と正面から衝突する。まず
  `protocol_cmake_text` が正しい file を指しているかの検証、次に RWLOCK/TEMPERATURE_RESET_OPT が
  「実 TU 供給マクロ」(defines 側で解決すべき) なのか「文脈マクロ」(CONTEXT_MACROS 側で
  解決すべき) なのかの切り分け、MQLOCK が真に死コードなら `assert_conditional_macros_covered`
  が要求する被覆から除外してよいか、という複数の設計判断が要る。
- 段階導入の原則 (CLAUDE.md 規律5) — 本 wave の scope は「実測の実行」であり、identity 計算
  基盤の設計変更は独立した wave として brief・plan・段3 敵対相談を経るべき規模と判断した。

### 推奨する次の一手

新しいタスクとして起票し、次を段1 brief の出発点にする:

1. `orchestrator/campaign/s1_direct_comparison.py:716` 周辺の `prepare_cell` から
   `source_digest.resolve()` への呼び出し経路を遡り、`protocol_cmake_text` に何が渡っているかを
   実際に確認する (TEMPERATURE_RESET_OPT が既にマッチ形式なのに落ちる理由の一次資料)。
2. RWLOCK のような「裸オプション」を `_SUPPLY_RE` がどう扱うべきか設計する
   (単純に正規表現を緩めるだけで「実 TU 供給集合」の正確性を保てるか、`ccbench_add_protocol`
   の OPTIONS 全項目を「値の有無を問わず供給される」ものとして扱ってよいか、を検証してから)。
3. MQLOCK が本当に死コードなら、`assert_conditional_macros_covered` が要求する被覆から
   除外してよい条件 (ccbench 側で二度と有効化されない保証があるか) を明確にする。
4. 再発防止として、mocc (または全 protocol) に対する `source_digest.resolve()` の実運用相当
   テストを追加する ([テスト代表性] gap — 既存 `test_s8b_floor_campaign.py` は
   `cmake`/`gcc-13`/`g++-13`/`nm` が揃わない環境で skip され、Pegasus 実機でこの経路が
   一度も実行されていなかった。`docs/phase3-8b-restart-runbook.md` §1 にも同じ既知の穴が
   明記されている)。
5. 修正後、本 insight の「投入パラメータ」節をそのまま再利用して床値 pilot を再投入できる
   (admission・toolchain・protocol は全て健全と確認済みのため、再投入時にゼロから preflight
   し直す必要はない)。

## 一回性 key の消費について

**確認済み: 本試行はチケットを 1 枚も消費していない。** admission root
(`s8b_holdout_admission.shared_admission_root` = `.git/izanagi/s8b-holdout-admission-v1`、
全 worktree 共有) の `claims/` `consumed/` 両ディレクトリを実測したところ、
本 job 実行時刻 (2026-08-20 13:15 前後) 以降に作成された file が 0 件だった。
`build_cells` (cell 単位の attempt ticket 消費より前の段階) で停止したため、という
設計上の予想と一致する。次回の再投入は `retry_slots_per_cell=2` を全 12 セルぶん
フルに保持した状態から開始できる。

## 証拠の所在 (repo 外へ退避済み)

全証拠 (submission receipt・job staging・job evidence checkpoint・run directory・単一テナント
claim marker) を repo 外の 1 bundle へ退避済み:

`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1431-floor-measurement/evidence-bundle/`
(`README.md` に元 path との対応表、`MANIFEST.sha256` に全 78 file の sha256。
`sha256sum -c MANIFEST.sha256` で整合性検査済み、rc=0)。

repo 内の元 path (`output/env/pegasus/calibration/s8b-floor-pilot/…`、`output/env/pegasus/floor/
attempts/submissions/…`、`output/env/pegasus/floor/job-staging/…`、`output/claims/`) は
holdout clean-scan 汚染 (将来の official 床値 job の起動証明を止める) を避けるため削除済み。
