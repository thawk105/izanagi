# n-pilot R>=32 (R=33) 拡張実測 — admission 機構の改訂設計ノート

事前登録は `output/insights/2026-08-16_t1142-n-pilot-prereg/preregistration.md`。
既存の R=11 実測は同ディレクトリの `measured_distributions.md`。
**本文書は「投入スクリプトの準備」を試みた結果、admission 機構の再設計が必要と判明したため
実装を見送り、将来の実装 wave がそのまま使える設計を記録したものである。実装は本 wave では
行っていない。**

## 0. 経緯 (なぜこの文書があるか)

dev-wave (2026-08-20) で、事前登録済み目標 R>=32 (コード上の制約により最小値は 33、
32 以上かつ 3 で割り切れる最小値) までの拡張実測のための Pegasus 投入スクリプトを準備しようと
した。着手前に pegasus02 上でこの git checkout の admission 状態を直接確認したところ、
「既存 11-round 実測の上に追加する」という当初想定は admission 機構の設計上構造的に不可能
であることが判明し (§1)、正しい実装には admission 機構自体の非自明な再設計が要ることが
段2 codex plan と段3 敵対相談 2 レンズ (計 15 件の real 所見) で判明した (§2, §3)。
実装規模が「投入スクリプトの準備」という当初 scope を大きく超え、かつ変更対象が
「一発勝負」という統計的整合性を守る安全装置 (admission の排他 claim) であるため、
本 wave では実装せず、改訂アーキテクチャを設計として確定するに留めた。裁定の全文は
decisions.md の該当 D を参照。

## 1. 新事実 — 既存 admission 機構の排他 claim (実測で確認済み)

`orchestrator/campaign/s8b_holdout_admission.py:1612` の
`reserve_n_pilot_holdout_observations()` は、cell を
`(freeze_sha256, freeze_holdout_key, configuration_id, ccbench_pin, env_tag,
observation_role)` の 6 項目 (`campaign_run_id` を含まない) で一意化した key を排他的に
claim する。一度 claim された key は二度と reserve できない
(`_write_exclusive()` → 既存なら `FileExistsError` →
"n pilot holdout cell key was already consumed")。

pegasus02 実機で `$(git rev-parse --git-common-dir)/izanagi/s8b-holdout-admission-v1/
ledger.jsonl` を直接読み、`observation_role="n_pilot"` の 12 cell 全部が
`campaign_run_id="t1142-run-1"` / `attempt_count=11` で既に `admit` 済み、対応する
132 attempt (12×11) 全部が `consumed/` に存在することを確認した。**したがって、同じ
(freeze/holdout/config/pin/env_tag) の組み合わせでの新規 reserve は必ず reject される。**

CLI (`orchestrator/campaign/s8b_oracle_n_pilot.py:main()`, 2147行) は「1回の呼び出し =
1回の reserve + 即時全量 `run_sessions()`」の不可分設計で、`--rounds` は「1 (生死実験) か
`protocol.pilot_rounds // protocol.allocation_count`」のみ許容する。3 allocation を素朴に
3回 CLI 呼び出しすると各回が独立に同じ key を reserve しようとして 2 回目以降が必ず
reject される — これが実際に既存 R=11 実測で allocation 2/3 が失敗した理由そのものである
(`measured_distributions.md` §6 と整合)。

## 2. 段2 codex plan の要約

段2 (codex, reasoning=max, read-only) は「observation_role に新しい世代
(`n_pilot_r33`) を追加し、durable receipt を新設して reserve/consume を分離する」設計を
提案した。要点:

- 1 回の reserve で 33 round 分 (396 attempt) の schedule 全体を確保する。
- durable JSON receipt (schema `s8b-n-pilot-reservation/v1`) を新設し、3 本の独立した
  consume-only job (各々 binary を独自に build) がそれぞれ 11 round ずつを global offset
  (0/132/264) で consume する。
- `aggregate_results()` の allocation identity を `campaign_run_id == attempt_id` から
  `{role, campaign_run_id, allocation_index}` の組へ変更する。
- CLI に `--reserve-only`/`--consume-only`/`--campaign-run-id`/`--allocation-index`/
  `--admission-manifest` を追加する。
- job script (`tools/pegasus/oracle_n_pilot.sh`) に reserve/consume mode を追加する。

段2 plan 全文: `stage2-plan.md` の逐語は本 wave の job dir に残しており、次段の実装子が
必要なら親 (次 wave の manager) が改めて渡す。**以下の統合設計 (§4) には段2 plan の有効な
部分をすべて取り込んである。**

## 3. 段3 敵対相談 (2レンズ、計 15 件の real 所見)

### 3.1 sol レンズ (正しさ境界) — real 所見 4 件中 3 件 (残り 1 件は親実測で解消済み)

1. **[real] role 新設だけでは一発勝負の保証として不十分。** `_OBSERVATION_ROLES` は単なる
   allowlist で、`n_pilot_r33`、将来の `n_pilot_r34` も同様に追加できてしまう。
   `irreversible_pilot_approved=True` も単なる bool で世代の一度限り性を証明しない。
   **世代を明示した固定 allowlist、protocol の pilot_rounds/campaign/decision pin、または
   role 以外の機械的な一回限り承認が必要。**
2. **[real] build 独立性が cache_root 共有で壊れうる。** `build_binaries()` は外部
   `cache_root` を受け取り、allocation index による cache namespace が無い。aggregate は
   binary SHA 等だけを比較し `cache_hit` 状態を検査しない。**allocation ごとに専用 cache
   root を強制するか、共有 cache を禁止して `cache_hit=False` を検証する必要がある。**
3. **[real] receipt の exact schema validator が未規定。** claim row をそのまま receipt に
   コピーする実装だと workload (三軸) が漏れ規律7違反になりうる。**receipt の exact key
   set・guarded writer (`write_guarded_result()`)・full claim の持込み禁止を実装契約に
   固定すべき。**
4. [refuted、対応不要] 既存 `n_pilot`/`oracle_driver` role への影響は claim path の
   digest 分離により実装上は問題ない。K=3・allocation 差の presence/direction-only 使用、
   親 brief の admission 解釈、receipt フィールド自体に三軸が含まれないこと、はいずれも
   refuted (正しい)。「live ledger 実数がこの相談資料からは再計算できない」という指摘は、
   親が pegasus02 で直接確認済みのため実務上解消している。

### 3.2 luna レンズ (整合・実効性) — real 所見 11 件

1. **claim file だけでは `_NPilotCellState` を再構成できない。** 実際の attempt 対応表・
   freeze・`pilot_reps` は process-local の `id(token)` 辞書にしかない。claim file 単独
   でなく ledger row・protocol/freeze canonical bytes・freeze から再導出した neutral
   holdout signatures を同時に読む必要がある。**観測 token は receipt から再構成せず、
   consume プロセス内で新規発行する設計にする。**
2. **`consume_n_pilot_attempt_ticket()` に新しい関数契約が必要。** 現行 signature は
   token と `schedule_index` だけで、token から claim path や campaign を導けない。
3. **reserve/consume/result/aggregate の全経路に新 role を明示的に渡す実装が要る。**
   現行は `OBSERVATION_ROLE_N_PILOT` をハードコードしている。またreserve API 自体は
   `pilot_rounds=33`/`allocation_count=3` を検証していない — admission 境界でも検査すべき。
4. **all-or-nothing claim 発行に rollback 機構が無い。** 現行は 1 件ずつ `O_EXCL` 作成、
   途中失敗時の rollback/commit journal が無く、プロセス死や fsync エラーで claim の一部
   だけが残りうる。**staging + commit marker か回復可能な transaction が必要。**
5. **global schedule offset が `run_sessions()` の coverage check と整合しない。**
   現行は `n_pilot_admissions` の key が `0..len(schedule)-1` を要求する。local/global
   どちらの index 空間を使うか設計で明示する必要がある。
6. **「3 個の 11-round schedule 連結」は `complete-block-v1` の canonical な 33-round
   生成と一致しない。** `build_schedule()` は `replicate_index` を seed の domain
   separation に使うため、`build_schedule(n=11)` を 3 回呼ぶと replicate 0〜10 が 3 回
   反復するが、`build_schedule(n=33)` は replicate 0〜32 になり異なる。**推奨は reserve
   時に `build_schedule(n=33)` を一度だけ生成し、132-row ずつ 3 allocation へ slice する
   方式。** ただしこの場合、各 allocation の local schedule は同一でなくなるため
   aggregate の変更も要る。
7. **`aggregate_results()` は global claim との対応を検証していない。** result JSON に
   `schedule_sha256`・global `schedule_index` が無く、result が本当に claim を消費した
   ことを aggregate 単独では証明できない。**receipt digest・global schedule hash・
   allocation の start/end index を result identity に含める必要がある。**
8. **`{role, campaign_run_id, allocation_index}` への変更は aggregate だけでは完結しない。**
   `_result_document()` の引数・main の reserve 呼出し・result producer・aggregate の
   parsed tuple と並べ替え処理を同時に変更しないと、producer が自分で生成した result を
   自分で拒否する状態になる。
9. **CLI mode の相互排他・必須引数規則が未定義。** 具体例: `--aggregate ... --reserve-only`
   同時指定が拒否されない、`--reserve-only --consume-only` が両方 true にできる、
   `--allocation-index` の範囲外を拒否しない、等。**reserve-only は rounds=33、
   consume-only は rounds=11、両 mode とも confirmation 必須、aggregate とは完全排他に
   する必要がある。**
10. **job script だけでなく `tools/pegasus/submit_oracle_n_pilot.sh` (submission wrapper)
    も変更対象。** 段2 plan のアンカー表にこの wrapper が無いのは実効性上の欠落。
    現状 `--build-only`/`--rounds` しか受け付けず、新 mode の campaign/allocation/manifest
    をここから渡せない。
11. [refuted、対応不要] `s8b_oracle_report.py`/`s8b_verdict.py` は n-pilot の
    observation role や claim 構造を直接参照しない。`oracle_driver` の既存挙動は新 role
    追加だけなら壊れない。

**段3 luna 総括: 「段2 plan は方向性 (reserve/consume 分離) としては実装可能だが、現案は
durable state・canonical schedule・global claim binding・CLI/job wiring が未完成で、
そのままでは実行不能」。**

## 4. 統合改訂アーキテクチャ (次の実装 wave への申し送り)

以下は §2-3 の real 所見をすべて解消する形へ統合した設計方針。次の実装 wave の段1 brief /
段2 plan はここから始めてよい (再調査は不要、ただし着手前に本 repo の該当箇所が本文書作成後に
変更されていないか差分確認は必要)。

1. **世代の一回限り性を role allowlist だけに頼らない。** `n_pilot_r33` という新
   observation_role を追加すること自体は正しい方向だが、それだけでは「role をいくらでも
   追加すれば再測定できる」という抜け穴を機械的に塞げない (sol 所見1)。追加の防御として、
   新しい role を admission コードへ追加する行為自体を「decisions.md への記録 + 新しい
   role 名の追加が該当 D を pin する check_docs.py 検査」のような形で縛ることを検討する
   (D223/D243/D514 の exact-pin と同型)。
2. **build 独立性: allocation ごとに専用 cache root を強制する。** 3 つの consume-only
   job (allocation) は、同じ `cache_root` を共有してはならない。呼び出し側 (job script /
   submission wrapper) が allocation index ごとに異なる cache root を渡すことを admission
   境界または driver 側で検証し、`cache_hit=True` の場合は独立実行の保証が壊れたとして
   拒否するか、明示的に diagnostics へ記録する。
3. **canonical 33-round schedule は `build_schedule(n=33)` を 1 回生成し、132-row ずつ
   3 スライスへ分割する** (「3 個の 11-round schedule を連結」ではない — luna 所見6)。
   reserve はこの 396-row schedule 全体に対して 1 回だけ行う。各 allocation の local
   schedule (aggregate へ渡す 11-round 分) は、この global schedule の該当スライスから
   導出し、global index との対応 (schedule_sha256 と start/end index) を result identity
   に含める (luna 所見7)。
4. **durable receipt は「claim file 単独」ではなく「claim file + ledger row + protocol/
   freeze canonical bytes」を束ねた形にし、観測 token は receipt から復元せず consume
   プロセス内で毎回新規発行する** (luna 所見1)。`consume_n_pilot_attempt_ticket()` は
   token ではなく receipt (+ 検証済み freeze) を受け取る新しい契約に変える (luna 所見2)。
5. **reserve API 自体が `pilot_rounds`/`allocation_count`/role の整合性を検証する**
   (現行は CLI の `load_protocol()` だけに依存している、luna 所見3)。
6. **claim 発行は all-or-nothing の transaction にする。** 12 cell 全部の claim path が
   未使用であることを lock 内で検査してから一括作成する設計 (段2 plan) だけでは、
   プロセス死や fsync エラーへの回復力が無い (luna 所見4)。staging 領域 + commit marker
   方式か、既存 claim の partial 状態を検出して安全にロールバックできる仕組みを設計する。
7. **CLI 新モードの相互排他表を明示的にバリデーションする。** luna 所見9 が列挙した
   6 つの誤った引数組み合わせすべてを拒否できることをテストで担保する。
8. **`tools/pegasus/submit_oracle_n_pilot.sh` を変更面に含める** (luna 所見10、段2 plan
   の見落とし)。
9. **変更が及ぶファイル一覧 (見込み):**
   - `orchestrator/campaign/s8b_holdout_admission.py` (世代管理・durable receipt・
     transaction化・consume契約変更)
   - `orchestrator/campaign/s8b_oracle_n_pilot.py` (CLI新モード・schedule生成・
     aggregate/_result_document書き換え)
   - `orchestrator/campaign/s8b_oracle_manifest.py` (schedule slice 方式を使うなら
     `build_schedule()` の呼び出し方だけ変更、関数自体の変更は不要と見込む)
   - `tools/pegasus/oracle_n_pilot.sh` (reserve/consume mode)
   - `tools/pegasus/submit_oracle_n_pilot.sh` (同上)
   - `orchestrator/tests/test_s8b_holdout_admission.py` (大幅拡張)
   - `orchestrator/tests/test_s8b_oracle_n_pilot.py` (大幅拡張)
   - 新しい pilot protocol document (`design.pilot_rounds=33`)

## 5. 既存実測データの扱い

既存 R=11 実測 (`measured_distributions.md`, campaign_run_id="t1142-run-1",
observation_role="n_pilot") は**削除・改変しない**。「事前登録が求める規模には未達だが、
対象条件の between-run 実測が 0 件だった状態を初めて埋めた予備的下限」として、そのまま
保存し続ける。新しい R=33 実測は、新しい observation_role 世代・新しい campaign・
新しい protocol document で発行する、別個の独立試行として扱う。

## 6. 本 wave がやらなかったこと

- admission 機構・CLI・job script・submission wrapper の実装 (§4 は設計のみ、コード変更は
  一切していない)。
- 新しい pilot protocol document の実際の生成。
- qsub による実際の投入 (D87、AI は qsub しない)。
- 「新しい git clone を使えば admission root が分離され再 claim できる」という回避策の
  採用 — 段2 plan が明示的に却下済み (「一度きりの安全装置を回避する」ため)。本文書の
  設計もこの回避策を前提にしない。
