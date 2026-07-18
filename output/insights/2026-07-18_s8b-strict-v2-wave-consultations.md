# 2026-07-18 strict v2 verifier wave — プラン・敵対相談逐語・裁定表 (凍結)

- **wave:** F1〜F7 + B-1/B-2 裁定完結 (worklog 2026-07-18 (6)、§9 承認状態) で解禁された実装群の統合。
  記録の正本 = `docs/phase3-8b-descriptor-design.md` §9 承認状態、裁定資料 =
  `output/insights/2026-07-16_s8b-floor-protocol-package.md` (F6 = 択 a、F7 = 推奨案、不変)
- **方式:** 標準ループ。Explore 4 (sonnet) 実査 → 親プラン起草 → codex exec, model=gpt-5.6-sol,
  reasoning=max, sandbox=read-only, cwd=worktree、並列 4 本 → 親裁定 → workflow 実行 → 親検算
- **スコープ規律 (δ-1 同型):** 本 wave は machinery + テストのみ。実 approval record / active pointer /
  v2 世代 file / protocol JSON の実凍結・発効は生成しない (master_seed / env_tag はユーザー記入欄)。
  v2 候補世代の実生成も floor 実測後 (F6a 発効順序 3) — builder 実装のみ行い呼び出さない

---

## §1 プラン draft v1 (codex 相談前)

### レーン分割

**Lane R — F6a 承認束縛 machinery (新モジュール `orchestrator/campaign/s8b_ratified_freeze.py`)**

`s8b_freeze_io.py` docstring が「ratified 型・strict parse の追加は load_ratified_freeze の責務で
本モジュールには追加しない」と明記するため、新規 leaf モジュールに置く (freeze_io の primitive は
import してよい。subprocess git を使うため freeze_io より重い層)。

- R1 世代 file 契約: `output/s8b-freeze/holdout_freeze.v2.g<N>.json`、create-only、strict canonical
  JSON。v2 header (新設 field) = schema_version="8b-holdout-freeze/v2"・generation_number・
  supersedes_sha256 (直前世代 bytes hash、g1 は v1 bytes hash)・refreeze_note・frozen_at_head
  (pre-generation source head へ再定義)・floor_protocol {path, sha256}・floor_source {path, sha256}・
  env_tag。F5 transition table を検証器として実装: (i) v1→g1 で変わってよい field = floor / budget /
  refreeze_note / schema_version / generator.sha256 / design_source.sha256 / frozen_at_head / env_tag /
  floor_protocol / floor_source / experiment_numbers / v2 header、(ii) gN→gN+1 = floor・budget・
  experiment_numbers 系 + header のみ。**それ以外の diff は拒否**。experiment_numbers は consumer
  (統計 judge) 不在のため本 wave では schema に予約のみで凍結しない (F5 の恒真保証拒否)
- R2 approval record 検証: path = `approvals/<generation_sha256>.json` を**世代 bytes hash から導出**
  (header に approval path を持たない — D2″)。内容 = strict canonical JSON
  {generation_sha256, approver, approved_at, scope} (exact keys)。検証連鎖 =
  (a) record 存在 ∧ (b) filename・内容の hash が世代 bytes hash と一致 ∧ (c) 導入 commit が
  `git log --diff-filter=A --format=%H -- <path>` でちょうど 1 件 ∧ HEAD ancestry
  (`merge-base --is-ancestor`) ∧ (d) その commit の trailer が `AI-Agent: none` **逐語かつ唯一**
  (`git interpret-trailers --parse`、check_ai_provenance.py:46-54 と同判定を module 内に実装 +
  新規テスト。既存 checker は CLI 専用のため import しない) ∧ (e) 導入後の path 改変履歴なし =
  `git rev-list HEAD -- <path>` が 1 件 ∧ worktree bytes == 導入 commit blob bytes
- R3 revocation tombstone: `revocations/<generation_sha256>.json`。**過去に一度でも導入されていれば
  revoked** (`git log --diff-filter=A -- <path>` 非空。worktree から削除されても不可逆)。schema =
  strict {generation_sha256, revoked_at, reason}
- R4 active pointer: `output/s8b-freeze/active/<pointer_sha256 連鎖>` 形の create-only record 連鎖
  {generation_number, path, sha256, parent_active_sha256, approval_sha256}。現 active = 連鎖の一意な
  head。複数 successor・pointer 不正・approval 不成立・revoked → **active なし fail-closed**。
  「最新 = 有効」禁止 (D4: g999 攻撃)。pointer record 自体も R2 と同じ commit 検証 (user commit +
  `AI-Agent: none`) を要求。⚠ pointer の具体トポロジー (単一 file 上書き vs create-only 連鎖) は
  本プランの主要な未確定点 — codex に攻撃させる
- R5 型分離: `RatifiedFreeze` (frozen dataclass) だけを実走 consumer が受理。
  `build_candidate_generation(...)` は `CandidateFreeze` を返し、consumer に渡せない
  (F6a 発効順序 5)。builder は本 wave で実装するが実呼び出しはしない
- R6 v1 側 guard 追随: `s8b_holdout_freeze.GENERATION_SCHEMA_FIELDS` (現行の先取り列挙は F6a 確定
  schema と field 名不一致 — approved_by vs approver 等) を新旧 union に更新し、v1 経路が v2 形
  document を確実に拒否し続ける

**Lane V — F7 strict v2 検証意味論 (同モジュール)**

- V1 source blob 照合: `git cat-file blob <frozen_at_head>:<path>` の bytes sha256 と世代の
  design_source / generator 記録の一致 (worktree bytes 照合の v1 方式から移行、D5')。世代 file と
  approval は後続 commit (frozen_at_head 自己参照回避)
- V2 二層未知性 (launch certificate、D6'): 層 1 = v1 凍結時点の snapshot 整合 (既存
  zero_hit_output_sha256 再計算を流用)。層 2 = `search_repository()` を現時点で再実行し、現在の
  conjunction hits が**申告済み計測 closure と完全一致**することを要求。closure は v2 世代の
  `measurement_closure` field: floor campaign 登録 artifact の {path, sha256,
  expected_conjunction_hit} 列。検証 = 現 hits 集合 == {closure 中 expected_conjunction_hit=true の
  path 集合} (集合完全一致・bytes hash 照合込み)。未申告 hit 1 件で fail-closed (裁定済みの代償)。
  ⚠ closure の粒度 (全登録 artifact vs hit 予告付き) は代替案として codex に攻撃させる
- V3 consumer 統一: (a) oracle driver gate_check の v2 分岐 — `"freeze-v2-verifier-not-implemented"`
  refusal を load_ratified_freeze 経由の実検証に置換。v1 分岐 (floor/budget 両 null) の二重読込
  (s8b_oracle_driver.py:126-151 の verified 経由 + :140 の path 再読込) を verified.document の
  引き渡しに一本化 (TOCTOU 除去)。(b) s8b_oracle_manifest の freeze fallback 読込
  (build_manifest :477 / verify_manifest :614-617) を strict 化。(c) s8b_verdict の floors 入力は
  ratified freeze 由来へ (Lane M6 と接続)
- V4 floor driver は v1 bytes sha256 pin のまま (F7 項 4、実装済み) — floor は v2 世代誕生**前**に
  走るため load_ratified_freeze の consumer にしない (発効順序上の非依存を明記)

**Lane M — manifest per-pair + B-1 + run contract pin**

- M1 `_validate_execution_snapshot` (s8b_oracle_manifest.py:402-434) を per-pair table 形
  `by_holdout.<h>.{pairs, scale_ref, scalar_alt}` (exact 3 keys、diagnostics は freeze 非持込) へ。
  pairs = configuration_id → 有限正 or null (machine_anomaly の null 伝播を受理し、消費側で判定不能へ
  倒す)。key 集合は freeze の構成集合と完全一致
- M2 B-1: `_canonical_bytes` (:46-53) と `_atomic_create_json` (:559) へ allow_nan=False
- M3 `_load_json_object` (:79-86) へ parse_constant 拒否 (NaN リテラル侵入の読込側 fail-closed)。
  duplicate key 拒否も併せるかは codex に諮る (既存 artifact の再検証破壊がないか)
- M4 `test_s8b_binding_driftguards.py` の既知 drift characterization (manifest NaN 受理 vs report
  拒否) を統一後挙動へ書き換え
- M5 `_validate_run_contract` (:293-306) に `bench_max_rounds == 1` の完全一致 pin (F3 裁定)
- M6 s8b_verdict per-pair 追随: `_floor_value` / `_floor_exceeded` (:200-261) は per-pair 形を
  渡すと**例外なしで INDETERMINATE に静かに倒れる** (実査で確認)。シグネチャを
  (floors, holdout, on_choice, off_choice) に変え、§6「oracle floor 超」= 当該 pair の floor
  (`pairs[on_choice]`、on == off なら差 0 で不成立側) で判定。CLI `--floors` の schema 文言も更新

**Lane O — oracle 結線**

- O1 binary full-sha256 照合: `pipeline.evaluate(expected_perf_sha256=...)` (実装済み・未配線) を
  driver `run_block` の evaluate 呼び出し (:570-587) に配線。期待値 = floor artifact 記録の
  `binary_sha256` (build_cells :631) を同一 (holdout, configuration) セルへ突合。
  `_outcome_for` (:322-340) の固定表に `bench-binary-mismatch` を追加 (追加しないと
  status="error" に落ちる)。⚠ ビルド非再現 (タイムスタンプ埋め込み等) なら恒常 abort になる —
  同一 buildcache 前提の妥当性と fallback 不要性を codex に攻撃させる
- O2 scale gate consumer (δ-7): driver が stock cell の実測 median と freeze floor の
  `scale_ref` を比較し、相対差 > scale_adequacy_rel_tolerance (protocol 由来、freeze v2 の
  floor_protocol 束縛経由) なら当該 holdout を scale-inadequate として**判定不能へ倒す**
  (採り直しによる数値改善方向には使わない — F1 裁定と同じ方向制約)
- O3 driver の NUMACTL ハードコード (s8b_oracle_driver.py:41) を env_contract lookup へ置換し
  contract_sha256 を run 記録へ (δ-12 の oracle 側)
- O4 γ-4 oracle receipt (floor/oracle 共通 receipt 設計) — 本 wave での要否を codex に諮る
  (スコープ肥大の懸念があれば延期台帳へ)

**Lane P — B-2 probe 縮小**

- P1 `calibrator/runner.py` `competing_bench_pids` (:191) の除外を `_self_and_descendant_pids`
  BFS から **{os.getpid()} のみ**へ。BFS helper は呼び手が消えるため削除 (盛らない)
- P2 `s8b_floor_campaign.py` `strict_probe` (:495) も同一縮小。docstring :484 の「B-2 未裁定のため
  変えない」を裁定済みへ更新
- P3 テスト反転: `test_calibrator.py:670-686` (実子プロセスは**検出される側**へ反転)・:431-459
  (monkeypatch 書換)・:688-709 (helper 削除に伴い削除)。実査のライフサイクル解析 (probe と計測は
  厳密逐次・子は reap 済み・孤児は現行でも検出対象 = B-2 前後で挙動不変) を裁定表へ記録

**Lane J — protocol JSON 凍結準備**

- J1 builder: `build_protocol_document(master_seed, env_tag)` — 承認 pin 値
  (formula v2 / n_sessions=8 / reps=5 / retry_slots_per_cell=2 / session_cv_max=0.10 /
  cell_cv_max=0.15 / scale_adequacy_rel_tolerance=0.10 / allowed_excluded_reasons 4 行 /
  wired_min_rel_floor / freeze {path, sha256} / ccbench_pin / stock_configuration /
  schedule_algorithm / extime_s) を機械組立てし validate_protocol を通す + canonical bytes +
  sha256 報告 + create-only writer。**本 wave ではファイルを実生成しない** (テスト内 tmp のみ)
- J2 δ-12: protocol へ `contract_sha256` key を追加し、値 = `lookup(env_tag).contract_sha256`
  との完全一致 pin (env contract fingerprint 束縛)。`_PROTOCOL_KEYS` 17→18 の変更は wave3 実装
  規約の改訂であり数値裁定の変更ではないことを明記 — codex に確認させる
- J3 ユーザー向け凍結手順 (master_seed/env_tag 記入 → builder 実行 → user commit) を
  pegasus-runbook でなく phase3 系文書のどこに置くか含め docs レーンで起票

### 横断規律

- 凍結対象の sha256 不変を毎 commit 照合: `2026-07-16_s8b-floor-protocol-package.md` /
  `2026-07-16_s8b-freeze-v2-design-material.md` / 相談逐語 3 本 / `output/s8b-freeze/holdout_freeze.json`
- `s8b_holdout_freeze.py` の編集封印は F7 裁定完結で解除。ただし編集は v1 実 artifact の generator
  drift を追加で広げる (v1 verify は既に drift 不合格 = 既知状態。v2 連鎖は v1 を bytes hash でのみ
  束縛し、v1 の worktree 照合を再実行しない)
- commit 順: P → M → R+V → O → J → docs (各 commit green + AI-Agent trailer + 凍結 sha256 照合)
- mutation 検証: 新 verifier へ ~15 mutant (hash 照合除去 / trailer prefix 化 / ancestry 反転 /
  revocation 無視 / 「最新=有効」化 / closure 完全一致→部分集合化 / per-pair null→0 扱い /
  bench pin 除去 / NaN 許容化 / probe 除外再拡大 / scale gate 緩和 / bin_sha256 prefix 照合化 等)
  を植え、テストが全滅させることを機能ゲートにする
- Workflow 配員: 実装 = opus (R+V は high、M/O = high、P/J = medium)、レーン内敵対レビュー =
  opus ×2 レンズ (意味論レンズ + fail-open/回帰レンズ)、テスト・mutation 実行 = sonnet、
  fable 子なし。push なし (Pegasus 運用)

### 既知の主要リスク (codex への攻撃招請点)

1. active pointer のトポロジー (R4) — create-only 連鎖 vs 上書き file。乗っ取り・分岐・fail-closed
   判定の健全性
2. 「導入後の path 改変履歴なし」の git 検証 (R2e) — rename/再導入/削除→再作成/shallow clone/
   worktree 差の攻撃面
3. launch certificate の closure 粒度 (V2) — expected_conjunction_hit 予告方式の fail-open 穴
4. binary sha256 照合の再現性前提 (O1) — 非決定ビルドで恒常 abort にならないか
5. per-pair 化に伴う verdict の静かな縮退 (M6) — 移行期の混在形入力
6. B-2 反転の未知の自己フラグ経路 (P) — 実査解析の見落とし
7. スコープ規律 — 本 wave のどこかが事実上の「発効」になっていないか

---

## §2 codex 敵対相談 逐語 (gpt-5.6-sol, reasoning=max, sandbox=read-only, 並列 4 本)

### C1 — Lane R (F6a 承認束縛 machinery)

結論: must-fix 10 件、should-fix 1 件。

1. active の一意性が `HEAD` ローカルにすぎない

- severity: must-fix
- 攻撃シナリオ: 共通 pointer P から branch A は g2、branch B は g3 への child pointer を作る。別 worktree で各 branch を開けば、各 `HEAD` には successor が一つしかないため、双方が異なる active 世代として実走できる。後で merge して fork を検出しても遅い。同様に、branch A の revocation は branch B や revocation 前の detached HEAD から見えない。
- 根拠 file:line: [output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:36)、[同:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:45)、[docs/phase3-8b-descriptor-design.md:398](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/phase3-8b-descriptor-design.md:398)
- 提案: activation 専用の単一 canonical ref を定め、実走時は「捕捉した `HEAD` がその ref の tip と完全一致」を必須にする。ref は non-force-push・直列更新を前提にする。これを置けないなら「active/revoked は現在の `HEAD` に対してのみ成立」と保証を縮小し、canonical ref 外での実走を拒否する。全 ref 列挙は未信頼 ref による DoS を招くので代替にならない。

2. genesis と edge 不変条件が未定義で、g999 を構造的に拒否できない

- severity: must-fix
- 攻撃シナリオ: `parent_active_sha256=null` の第二 root を追加すると、現記述にはそれを不正とする規則がなく、複数 head による恒久 DoS になる。また、parent が現 g1 のまま `generation_number=999`、g999 path を指す pointer を作った場合、文書差分の transition 検査だけでは番号の飛びを拒否できない。
- 根拠 file:line: [output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:24)、[同:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:45)、[output/insights/2026-07-16_s8b-floor-protocol-package.md:400](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-16_s8b-floor-protocol-package.md:400)
- 提案: genesis は唯一の `parent_active_sha256=null`、`generation_number=1` と固定する。child は `N=parent.N+1`、path は正規形 `holdout_freeze.v2.gN.json`、世代本文の番号も N、`supersedes_sha256` は parent 世代 hash と完全一致させる。pointer filename は canonical bytes の SHA-256、`approval_sha256` は実 approval record bytes の SHA-256 と定義する。単一上書き file は branch fork を隠すため採用しない。

3. fork 検出後の回復経路がなく、revocation は無権限の永久 DoS になる

- severity: must-fix
- 攻撃シナリオ: 同じ parent に二つの valid child が到達すると active はなくなるが、pointer は create-only で pointer 自身の取消方式がない。孫を追加しても親の fork は残る。さらに R3 は tombstone path が一度 add された事実だけで revoked とするため、AI trailer の commit や誤った commit 一つで世代を永久停止できる。
- 根拠 file:line: [output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:42](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:42)、[同:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:45)、[output/insights/2026-07-16_s8b-floor-protocol-package.md:397](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-16_s8b-floor-protocol-package.md:397)
- 提案: pointer SHA を鍵にした不可逆 cancellation tombstone を追加し、「複数の live successor」のみを fork と定義する。取消 record と generation revocation にも approval と同じ導入 commit・trailer・immutability 検査を要求する。revoked generation の子孫を全失効させるか、修正世代で復帰可能にするかも固定する。

4. generation の導入 commit が検証対象外で、発効順序を一 commit で迂回できる

- severity: must-fix
- 攻撃シナリオ: generation、approval、active pointer を一つの `AI-Agent: none` commit に追加する。approval と pointer は各 path で add 一回、bytes/blob 一致、trailer 唯一を満たすため、現プランの R2/R4 を通る。Candidate が inactive だった時点も、AI 生成物を AI trailer commit に置いた証拠も存在しない。
- 根拠 file:line: [output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:24)、[同:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:33)、[output/insights/2026-07-16_s8b-floor-protocol-package.md:405](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-16_s8b-floor-protocol-package.md:405)
- 提案: generation path にも一意な導入・以後不変の履歴検査を適用する。generation 導入 commit は構造化 AI trailer 必須、approval/pointer 導入 commit と不一致、後者二つは同一 commit とする。`diff-tree` で candidate commit の追加対象を generation のみに、承認 commit を当該 approval と pointer の二追加だけに限定する。`frozen_at_head` は generation 導入 commit の親と一致させる。

5. `git log` / `rev-list -- <path>` の件数は DAG のイベント台帳ではない

- severity: must-fix
- 攻撃シナリオ: branch A で AI が record を追加し、branch B で同じ path/bytes を human commit として追加して mergeする。path が両親に TREESAME なら、既定の path history simplification は片親だけを辿り、human 側一件だけを返し得る。revocation を一方の親で追加し、merge tree では削除側を採れば、HEAD ancestor に revocation commit があっても同じ理由で検索から落ち得る。shallow boundary では完全な導入履歴自体を証明できない。
- 根拠 file:line: [output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:36)、[同:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:41)、[同:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:43)
- 提案: shallow repository は即拒否する。捕捉済み commit H から path 制限なしの全 DAG を辿り、各 commit/parent の tree entry `(mode, blob_oid)` から導入・変更・削除・再導入を自前で判定する。immutable record は最小導入 node が一つ、以後同一 blob/modeのみとする。merge add/add、merge での削除、rename、delete/recreate、cherry-pick、root commit、shallow clone を実 Git repository の統合テストにする。

6. 「逐語」判定が参考実装のコピーでは成立しない

- severity: must-fix
- 攻撃シナリオ: 参考実装は key を小文字化し value を `strip()` するため、`ai-agent :   none` や末尾空白付き `AI-Agent: none   ` を受理する。`git interpret-trailers --parse` 自身も表記を正規化するので、その出力だけから元の逐語性は復元できない。`trailer.separators` の local config でも parse 規則が変わる。
- 根拠 file:line: [output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:38)、[tools/check_ai_provenance.py:46](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/tools/check_ai_provenance.py:46)、[同:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/tools/check_ai_provenance.py:51)、[docs/ai-provenance.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/ai-provenance.md:38)
- 提案: raw commit object の message bytes と Git の parse 結果を併用する。parse 上の AI-Agent 値が厳密に `["none"]` であり、対応する raw trailer line が byte-for-byte `AI-Agent: none` であることを要求する。separator を `:` に固定し、body 内の偽行、複数行、大小文字、空白、continuation、末尾空白、alternate separator のテストを置く。

7. `frozen dataclass` は型遮断にも不変性にもならない

- severity: must-fix
- 攻撃シナリオ: caller が `RatifiedFreeze(document=candidate.document, ...)` を直接構築すれば Candidate を実走型へ昇格できる。さらに `frozen=True` は field の再代入しか止めず、内部 `dict` の `floor` や `budget` は検証後に変更できる。nominal type を保ったまま承認 hash と異なる値が consumer に届く。
- 根拠 file:line: [output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:51)、[orchestrator/campaign/s8b_freeze_io.py:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_freeze_io.py:30)、[orchestrator/campaign/s8b_floor_campaign.py:1341](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:1341)
- 提案: side-effecting public entrypoint 自身が `load_ratified_freeze` を呼び、外部から Ratified object を注入させない。Ratified の constructor は loader 内だけに閉じ、payload は再帰的 immutable な型へ変換して raw mutable dict を公開しない。Candidate を渡したとき副作用前に拒否するテストと、loader 外での constructor 使用を拒否する静的検査を置く。「任意 Python コードに対して偽造不能」ではなく「公開 API から昇格不能」までに保証を限定する。

8. F5 と F6 の最終 schema が衝突したまま

- severity: must-fix
- 攻撃シナリオ: F5 は v2 header に `change_reason`, `approved_by`, `approved_at`, `approval_scope` を列挙する一方、F6 は承認を外部 record の `approver`, `approved_at`, `scope` に移している。R1 の明示 header は `change_reason` も approval fields も列挙せず、R6 は新旧 union で済ませる。実装ごとに旧 self-approval field を受理するか、正当世代を拒否するかが分裂する。
- 根拠 file:line: [output/insights/2026-07-16_s8b-floor-protocol-package.md:342](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-16_s8b-floor-protocol-package.md:342)、[同:349](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-16_s8b-floor-protocol-package.md:349)、[同:387](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-16_s8b-floor-protocol-package.md:387)、[output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:54](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:54)
- 提案: F6 後の exact schema を一つ明記する。generation から approval assertion fields を全廃し、`change_reason` を残すか否かを確定する。transition table は「header」や「experiment_numbers 系」でなく変更可能な JSON Pointer の完全列挙にする。旧 `approved_by/approval_scope` は v2 loader でも必ず未知 key として拒否する。

9. `GENERATION_SCHEMA_FIELDS` の union は v1 経路の境界にならない

- severity: must-fix
- 攻撃シナリオ: `_reject_unratified_generation` は `s8b_holdout_freeze.verify_document` を通った場合しか発火しない。`load_verified_freeze` は任意の top-level dict を返し、manifest の build/fallback も path を直接 parse する。残存 caller が Candidate v2 をこの経路で読み、`Mapping` を受け取る budget/materialization consumer に渡せば union は一度も評価されない。
- 根拠 file:line: [orchestrator/campaign/s8b_holdout_freeze.py:632](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_holdout_freeze.py:632)、[orchestrator/campaign/s8b_freeze_io.py:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_freeze_io.py:41)、[orchestrator/campaign/s8b_oracle_manifest.py:471](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_manifest.py:471)、[同:614](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_manifest.py:614)、[orchestrator/campaign/s8b_budget.py:96](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_budget.py:96)
- 提案: union は defense-in-depth と明記し、境界扱いしない。実走側の raw path fallback と `(dict, sha)` API を撤去して Ratified object のみへ統一する。floor 前の v1 loader は別の pre-ratification 経路として隔離する。実走 module が `load_verified_freeze`、直接 JSON load、Candidate constructor を参照しないことを静的検査する。

10. 検証に linearization point がなく、状態を混成できる

- severity: must-fix
- 攻撃シナリオ: approval を H0 で検証した後、pointer 検査前または run marker 作成前に `HEAD` が H1 へ進み、revocation または別 active pointer が入る。各 command が文字列 `HEAD` を再解決すると、一つの commit に同時存在しなかった部品を組み合わせられる。load 後の revocationも、現在の driver 構造では marker 作成前に反映されない。
- 根拠 file:line: [output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:36)、[同:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:41)、[orchestrator/campaign/s8b_freeze_io.py:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_freeze_io.py:41)、[orchestrator/campaign/s8b_oracle_driver.py:419](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_driver.py:419)、[同:462](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_driver.py:462)
- 提案: 開始時に commit H を一度捕捉し、全履歴・tree・blob query を H に固定する。pointer 列挙は worktree directory でなく H の tree から行い、各 artifact は一度だけ bytes を読み、その同じ bytes を hash・canonical parse・戻り値に使う。Ratified object と manifest/WAL に `activation_head` を記録する。run marker 直前に canonical ref tip と H の一致を再確認し、「H 後の revocation は進行中 run を止めるか、次回 launch から効くか」を明文化する。関連 namespace の dirty state は拒否し、無関係な dirty file は対象外とする。

11. hooks を防壁に数える記述は事実と違う

- severity: should-fix
- 攻撃シナリオ: AI が approval/pointer JSON を書き、`AI-Agent: none` で commitする。`guard_write` は `output/s8b-freeze/` を保護せず、`guard_bash` の防護 tree にもなく、Codex には hook 自体が未配線である。provenance checker は `none` の構文しか検査しないため、そのまま通る。
- 根拠 file:line: [hooks/guard_write.py:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/hooks/guard_write.py:45)、[hooks/guard_bash.py:56](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/hooks/guard_bash.py:56)、[hooks/README.md:13](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/hooks/README.md:13)、[同:106](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/hooks/README.md:106)、[tools/check_ai_provenance.py:67](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/tools/check_ai_provenance.py:67)、[output/insights/2026-07-16_s8b-floor-protocol-package.md:423](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-16_s8b-floor-protocol-package.md:423)
- 提案: 現 F6a の保証を「Git 内容による規約 attestation。人間性の機械証明なし」とだけ記録し、hooks を層に数えない。approval/active/revocation path を両 guard 核と将来の Codex adapter で拒否するのは誤操作抑止にはなるが、認証保証にはしない。AI 偽装を脅威モデル内で塞ぐなら、allowlist 鍵署名へ再裁定する。

### C2 — Lane V (F7 検証意味論)

結論: must-fix 8件、should-fix 2件。

1. `measurement_closure` が承認済み transition table に存在しない

- severity: must-fix
- 攻撃シナリオ: 正直に `measurement_closure` を追加すると v1→g1 の「列挙外 diff 拒否」により正当な g1 自身が不合格になる。通すために unknown key 許容や事後の場当たり的 whitelist を入れると、F5 の exact transition 契約が崩れる。
- 根拠 file:line: `output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:28-31,65-68`、`docs/phase3-8b-descriptor-design.md:384-389`、`output/insights/2026-07-16_s8b-floor-protocol-package.md:344-352`
- 提案: 実装前に、`measurement_closure` の配置・exact keys・世代間変更可否を F5 transition table へ明示追認する。代替は、既存 `floor_source` が指す機械 artifact 自体を closure 正本と定義し、新 top-level field を増やさないこと。generic な「v2 header その他」は認めない。

2. closure は launch certificate ではなく事後ホワイトリストになっている

- severity: must-fix
- 攻撃シナリオ: v1 後、floor 開始前に未申告測定を行い、その artifact を削除・移動してから official floor を実行する。v2 は floor 後に初めて生成されるため、現在残る official artifact だけを closure に載せれば完全一致する。v1 が真に zero-hit なら集合差分を保存しない数学自体は正しいが、事前時点を証明する証拠がない。
- 根拠 file:line: `output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:63-68,76-77`、`output/insights/2026-07-16_s8b-floor-protocol-package.md:461-465`、`orchestrator/campaign/s8b_holdout_freeze.py:297-315`
- 提案: floor 前に create-only certificate を発行し、正本 v1 hash、clean-scan digest、protocol、schedule、attempt ID、許可出力 namespace を束縛する。floor journal/artifact は certificate ID を必須とし、v2 closure はその append-only lineage から機械導出する。事後申告だけでは通さない。

3. `search_repository()` の列挙面に恒常的な盲点がある

- severity: must-fix
- 攻撃シナリオ: hit を `.gitignore` 対象、`output/s8b-freeze/`、CCBench 内の untracked file、tracked/untracked symlink に置く。これらは現在検索されず、未申告 hit が存在しても closure 完全一致が成立する。repo root の「非 ignore な untracked regular file」は列挙されるため、問題は untracked 全般ではなくこの盲点群である。
- 根拠 file:line: `orchestrator/campaign/s8b_holdout_freeze.py:32,179-212,232-233`、`.gitignore:18-24`
- 提案: security boundary で `--exclude-standard` に依存しない。対象 root を filesystem から列挙し、ignore 対象と submodule の untracked も含める。symlink・gitlink・非 regular file は黙って除外せず拒否または明示 inventory 化する。盲点を残すなら「未申告測定を確実に検出」という主張を scope 内限定へ弱める。

4. `expected_conjunction_hit: bool` は hit の型と一致しない

- severity: must-fix
- 攻撃シナリオ: search 結果は rr80/rr20 ごとの独立した path 集合だが、closure は path 当たり boolean 一つしか持たない。全 holdout の union で比較すれば「rr20 だけ hit」を「rr80 の許可 hit」にも転用できる。各 holdout に同じ予告集合を適用すれば正当 artifact を恒常拒否する。また bytes hash は内容を固定するだけで、boolean が内容から正しく導かれたことを証明しない。
- 根拠 file:line: `output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:65-69`、`orchestrator/campaign/s8b_holdout_freeze.py:270-294,326-332`、`output/insights/2026-07-16_s8b-floor-protocol-package.md:463-465,484-485`
- 提案: closure は全 artifact の `{canonical_path, sha256}` に限定し、`hits_by_holdout` は verifier がその同一 bytes から導出する。保存するなら `{rr80: bool, rr20: bool}` を冗長記録として再計算照合する。path は root-relative・正規化済み・一意・regular file に固定する。通常の内容変更は同一スナップショットの SHA 照合で落ちるため、問題は予告値の自己申告と読取競合である。

5. g1 の v1 trust root が攻撃者選択になっている

- severity: must-fix
- 攻撃シナリオ: v1 の `per_axis_counts`、確認者、scope 等を変更し、必要なら `zero_hit_output_sha256` を再計算する。その改変済み bytes hash を g1 の `supersedes_sha256` に入れ、同じ改変値を g1 にコピーすれば transition diff は見えない。毎 commit の手続的 SHA 照合は runtime verifier の trust anchor ではない。
- 根拠 file:line: `output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:24-31,139-143`、`output/s8b-freeze/holdout_freeze.json:3-15`、`orchestrator/campaign/s8b_holdout_freeze.py:710-729`
- 提案: canonical v1 bytes SHA-256 と導入 commit/blob を one-time migration trust root として固定する。現在の v1 SHA は `315b1eb8…`。さらに実査では v1 の `frozen_at_head=2e20d441…` は non-shallow repo 内に存在せず `git cat-file -t` が失敗するため、黙って grandfather せず、この不整合を明記した人間承認 migration record が必要。v1 は `RatifiedFreeze` ではなく exact-hash の `LegacyFreeze` として型分離する。

6. `frozen_at_head` が実際の generation 親 commit に束縛されていない

- severity: must-fix
- 攻撃シナリオ: generation 作者が任意の古い ancestor を `frozen_at_head` に指定し、その commit の design/generator hash を記録する。`git cat-file` 照合は通るが、それが実際の pre-generation source state だった証拠はない。現在のプランが unique-add/history を要求するのは approval record であり、generation file 自身ではない。
- 根拠 file:line: `output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:24,36-41,60-62`、`output/insights/2026-07-16_s8b-floor-protocol-package.md:458-460,484-487`
- 提案: generation の一意な導入 commit `G` を検証し、非 merge の `G^ == frozen_at_head` を要求する。`G` には generation file と closure artifact、またはその immutable CAS manifest を同時収録し、導入後変更なしを検査する。approval/active は別 commit `A` に置く。この形なら sibling artifact の SHA を generation に入れても自己参照しない。

7. selector・manifest・verdict に ratification bypass が残る

- severity: must-fix
- 攻撃シナリオ: selector CLI は任意 freeze を strict parse するだけで、active・approval・generation chain を検査せず job/prediction を作れる。`build_manifest()` と `verify_manifest()` fallback も parser を strict 化するだけなら未承認 candidate の floor/budget を消費できる。verdict CLI が `--floors` を残せば、ratified freeze と無関係な floor で最終判定を操作できる。
- 根拠 file:line: `docs/phase3-8b-descriptor-design.md:406-410`、`output/insights/2026-07-16_s8b-floor-protocol-package.md:466-468`、`orchestrator/campaign/s8b_selector_freeze.py:253-303,685-706,724-729`、`orchestrator/campaign/s8b_oracle_manifest.py:471-478,614-617`、`orchestrator/campaign/s8b_verdict.py:449-467`
- 提案: production API は path/Mapping ではなく `RatifiedFreeze` のみ受け取る。selector の pre-v2 経路は exact-hash `LegacyFreeze` に限定する。manifest fallback は削除するか内部で active pointer から ratified load する。verdict は `--floors`/`--holdouts` を廃止し、ratified freeze から両方を導出して generation SHA を証拠へ残す。floor driver の protocol-pinned v1 bytes 経路だけを明示例外にする。

8. current search・closure hash・実走が単一 snapshot ではない

- severity: must-fix
- 攻撃シナリオ: 列挙直後に未申告 hit file を作れば固定済み `rel_paths` に入らず検証を通る。closure path を search 時と hash 時で差し替えれば、hit 判定と SHA 判定を異なる bytes から得られる。さらに O1 が後で floor artifact を再読込して binary hash を得るなら、ratified load 後の差し替えが実走へ到達する。`frozen=True` dataclass も中身が `dict` なら深い不変性を提供しない。
- 根拠 file:line: `orchestrator/campaign/s8b_holdout_freeze.py:297-315`、`output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:63-68,98-100`、`orchestrator/campaign/s8b_freeze_io.py:30-38`、`orchestrator/campaign/s8b_oracle_driver.py:419-451`
- 提案: closure は generation commit blob/CAS から一度だけ読み、その raw bytes と深い immutable parse 結果を `RatifiedFreeze` に保持する。current repository search は immutable filesystem snapshot 上で行うか、列挙前後 digest の一致と launch lock を要求する。HEAD・active・revocation は最初の書込み直前にも再確認し、実走は検証済み snapshot を使用する。

9. manifest は gate 内で依然二重読込される

- severity: should-fix
- 攻撃シナリオ: `verify_manifest()` が正当な A を検証した直後に、同じ freeze SHA だけを持つ不正な B へ差し替える。後段は B の `freeze.sha256` しか見ないため、standalone `gate_check` は、現在 disk 上にある B を一度も完全検証せず `allowed=True` を返し得る。`run_block` は後で再検証して停止するが、gate の契約は偽になる。
- 根拠 file:line: `orchestrator/campaign/s8b_oracle_driver.py:172-195,445-450`、`orchestrator/campaign/s8b_oracle_manifest.py:586-617`
- 提案: `verify_manifest()` を bytes/hash/document を束ねた `VerifiedManifest` 返却にし、freeze hash 照合・gate・`config_for_block` まで同一 object を使う。gate 後の再読込を削除する。

10. 高コスト検証を必須に保つ構造と mutation が不足している

- severity: should-fix
- 攻撃シナリオ: repo 全走査を HEAD keyed cache へ置換すると、HEAD を変えない ignored/untracked hit 追加がキャッシュをすり抜ける。あるいは current search 自体を削除して closure の記録値だけを見る最適化をしても、現在列挙された mutation は「完全一致→部分集合」しか殺さず、search 未実行を保証しない。v2 では既存 `_assert_search_pass` が正当な expected hit まで拒否するため、これを外した際に陽性対照も失う危険がある。
- 根拠 file:line: `output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:63-68,145-148`、`orchestrator/campaign/s8b_holdout_freeze.py:352-372`
- 提案: static ratification と dynamic launch validation を型で分け、実走には full scan 済み `LaunchValidatedFreeze` を必須にする。skip flag は作らない。`_assert_search_operational` を分離して陽性対照を維持する。search-call 除去、HEAD-only cache、ignore/submodule/symlink、per-holdout 取り違え、走査中 file 追加、v1 anchor 改変、selector/manifest/verdict bypass を mutation/統合テストへ追加する。

### C3 — Lane M + Lane O

## 確定所見

1.

- severity: must-fix
- 攻撃シナリオ: floor producer の `pairs` は `configuration_id` で stock を除外する。一方 M1 は全構成集合との一致、M6 は opaque な `choice_id` (`c01` 等) で `pairs[on_choice]` を引く。このままでは正当な freeze を validator が拒否するか、verdict が欠測扱いで恒常的に `INDETERMINATE` になる。`on=stock_common` には pair 自体が存在しない。
- 根拠 file:line: [s8b_floor_stats.py:291](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_stats.py:291), [s8b_floor_stats.py:334](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_stats.py:334), [s8b_selector_input.py:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_selector_input.py:22), [s8b_verdict.py:315](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_verdict.py:315), [2026-07-16_s8b-floor-protocol-package.md:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-16_s8b-floor-protocol-package.md:75), [同:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-16_s8b-floor-protocol-package.md:86)
- 提案: F1 裁定どおり verdict は holdout→scalar のまま維持し、検証済み prediction の `binding_key` を使う trusted projector を置く。期待 pair key は `configuration集合 - {stock_configuration}`。`on==off==stock` を floor 不要の `REFUTED` とするか、floor 欠測の `INDETERMINATE` とするかは現裁定から一意に決まらないため、§9 に明文化してから実装する。

2.

- severity: must-fix
- 攻撃シナリオ: `pairs[on]` が正しいのは off が stock 固定の場合だけだが、`s8b_verdict` の CLI は prediction freeze を検証せず、任意の非空 off choice を受理する。off を非 stock に改変すると、実際には「on 対 off」を比較しながら「on 対 stock」の floor を適用できる。
- 根拠 file:line: [phase3-8b-descriptor-design.md:288](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/phase3-8b-descriptor-design.md:288), [s8b_selector_freeze.py:464](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_selector_freeze.py:464), [s8b_verdict.py:114](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_verdict.py:114), [s8b_verdict.py:460](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_verdict.py:460)
- 提案: `VerifiedPrediction` 相当の型を導入し、ratified freeze に対する prediction の完全検証後にだけ projector/verdict へ渡す。off の `choice_id=c06`、`binding_key=stock_common`、binding hash の一致を機械検査する。

3.

- severity: should-fix
- 攻撃シナリオ: M1 の「exact 3 keys」だけでは、top-level floor への旧フィールド混入、`scale_ref=null` なのに有限 pair、`scalar_alt` が pair 最大値と不一致、といった混在・自己矛盾を拒否できない。現 validator は `by_holdout` 以外を無視する。
- 根拠 file:line: [s8b_oracle_manifest.py:402](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_manifest.py:402), [s8b_floor_stats.py:293](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_stats.py:293), [s8b_floor_stats.py:384](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_stats.py:384), [wave plan:81](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:81)
- 提案: `floor` 自体も exact `{by_holdout}`、各 holdout も exact 3 keys にする。pair 集合、有限正/null、`scale_ref=null ⇒ 全pair・scalar_alt=null`、`scalar_alt=max(pairs)` または null の相関を検証する。欠落 key と明示 null は別理由にする。

4.

- severity: should-fix
- 攻撃シナリオ: プランは更新対象テストとして driftguard しか挙げていないが、manifest・driver・report の主要 fixture はすべて scalar floor を生成する。M1 適用直後に広範囲が赤化し、場当たり的に validator を緩める圧力が生じる。
- 根拠 file:line: [wave plan:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:88), [test_s8b_oracle_manifest.py:108](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/tests/test_s8b_oracle_manifest.py:108), [test_s8b_oracle_driver.py:51](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/tests/test_s8b_oracle_driver.py:51), [test_s8b_oracle_report.py:52](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/tests/test_s8b_oracle_report.py:52)
- 提案: 共通 v2 freeze fixture を作り、この3群も M commit の明示対象に含める。scalar 全件、holdout 間混在、stock key 混入、pair 欠落/余分、明示 null の負例を追加する。

5.

- severity: must-fix
- 攻撃シナリオ: `_outcome_for` に `bench-binary-mismatch` を足すだけでは、返せる既存 outcome がない。mismatch は `build_done` 後・verify 前なので、`build-failed`、`bench-failed`、`verify-inconclusive` のどの証拠表にも適合せず、report が protocol violation にする。
- 根拠 file:line: [pipeline.py:447](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/pipeline.py:447), [s8b_oracle_driver.py:322](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_driver.py:322), [s8b_oracle_report.py:24](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_report.py:24), [s8b_oracle_report.py:408](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_report.py:408)
- 提案: `binary-mismatch` を driver・report の閉表・証拠 truth table・judge の unknown 伝播まで通す。可能なら全セルを開始前に検査して gate refusal にし、pipeline 側 reason は TOCTOU 用の第二防壁とする。

6.

- severity: must-fix
- 攻撃シナリオ: floor artifact の `binary_sha256` は「floor がその bytes を実行した」証拠になっていない。build 時に一度 hash を記録した後、各 session は path をそのまま実行し再ハッシュしない。また `verify_floor_artifact` は `binaries` を一切検証しない。結果として、floor が差し替え後 binary を測り、oracle が差し替え前 hash と一致しても照合は緑になり得る。
- 根拠 file:line: [s8b_floor_campaign.py:608](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:608), [s8b_floor_campaign.py:800](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:800), [s8b_floor_campaign.py:1146](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:1146), [s8b_floor_stats.py:434](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_stats.py:434), [s8b_floor_stats.py:616](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_stats.py:616)
- 提案: floor session の実行直前に full hash を照合して journal へ記録する。floor manifest/result/journal の hash 束と、exact `(holdout_id, configuration_id)`→binary record 集合を検証する最小 receipt を v2 freeze に pin する。文字列 `cell_id` だけで突合せず、内部 identity field と完全集合で照合する。

7.

- severity: must-fix
- 攻撃シナリオ: 「同一 buildcache」前提は現 CLI で成立しない。floor は固定 output root の cache を使うが、oracle は `--output-root` に連動して cache root も変える。別 output root、cache eviction、同名コンパイラの更新で再ビルドされると、一回限りの oracle が hash mismatch で不可逆に潰れる。cache key はコンパイラ名を含むだけでバージョンを含まない。
- 根拠 file:line: [s8b_floor_campaign.py:608](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:608), [s8b_floor_campaign.py:1648](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:1648), [s8b_oracle_driver.py:560](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_driver.py:560), [s8b_oracle_driver.py:729](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_driver.py:729), [buildcache.py:105](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/buildcache.py:105)
- 提案: WAL の output root と binary store を分離し、floor-built bytes を content-addressed・immutable に保存する。oracle は全 expected binary の存在/hash を run marker 前に検査し、欠落時は再ビルドせず refusal。再ビルドを許すなら、異なる checkout/build directory での clean build 二回一致を機能ゲートにし、compiler/linker/CMake の実 version と再現ビルド flags を pin する。

8.

- severity: must-fix
- 攻撃シナリオ: scale gate を driver に置くと、最終 `median_of_medians` 前の部分 stock 値で判定して schedule 順依存になる。全測定後に計算しても、report/judge/verdict に scale 状態の schema・伝播路がないため消失する。また「相対差」の分母が未規定で、`scale_ref=100, oracle=111` は `/scale_ref` なら11%、`/oracle` なら9.91%と判定が分岐する。
- 根拠 file:line: [wave plan:104](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:104), [phase3-8b-descriptor-design.md:315](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/phase3-8b-descriptor-design.md:315), [s8b_oracle_judge.py:82](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_judge.py:82), [s8b_oracle_report.py:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_report.py:35), [s8b_verdict.py:315](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_verdict.py:315)
- 提案: oracle judge 完了後、stock の `median_of_medians` に対して `abs(observed-scale_ref)/scale_ref > tolerance` を評価する。ちょうど±10%は adequate と固定し、stock 非 eligible・`scale_ref=null` は当該 holdout の第3条件だけを判定不能にする。trusted floor projector に統合すれば既存 verdict の scalar 契約を維持できる。

9.

- severity: must-fix
- 攻撃シナリオ: M5 は `bench_max_rounds` しか pin しないため、manifest は任意の正の `clocks/reps/extime` を受理し、driver はその値を実行に使う。O3 で numactl だけ env contract 化すると、floor は contract の clocks、oracle は manifest の clocks という非対称が残る。
- 根拠 file:line: [s8b_oracle_manifest.py:293](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_manifest.py:293), [s8b_oracle_driver.py:284](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_driver.py:284), [s8b_oracle_driver.py:570](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_driver.py:570), [s8b_floor_campaign.py:1385](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:1385), [phase3-8b-descriptor-design.md:381](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/phase3-8b-descriptor-design.md:381)
- 提案: run contract を自由入力から組まず、ratified freeze・verified protocol・env contract から導出する。`ccbench_pin/env_tag/reps/extime/bench_max_rounds=1/clocks_per_us/numactl/contract_sha256` を完全一致で束縛し、nested key 集合も exact にする。generic な `pipeline.evaluate` の default=3 は変更せず、oracle adapter が常に1を明示する。

10.

- severity: must-fix
- 攻撃シナリオ: `contract_sha256` を WAL に書くだけでは恒真記録になる。report は `WalRecord.env_tag` も contract hash も動的 host 情報も検証しない。さらに floor の machine pin は `p2_2.ENV_TAG=linux-baremetal` 固定なので、Pegasus contract を追加しても floor が必ず拒否する。O4 を延期すると、F4 が要求した allocation/node/process 同一性と host/boot/job/cpuset/toolchain 証拠がないまま oracle が解禁される。
- 根拠 file:line: [env_contract.py:147](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/env_contract.py:147), [p2_2.py:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/p2_2.py:36), [s8b_floor_campaign.py:1349](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:1349), [phase3-8b-descriptor-design.md:368](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/phase3-8b-descriptor-design.md:368), [s8b_oracle_driver.py:466](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_driver.py:466), [s8b_oracle_report.py:496](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_report.py:496)
- 提案: γ-4 は延期せず、本 wave に最小共通 execution guard/receipt として入れる。両 driver が同じ lookup、contract hash 一致、実行機 attestation、hostname/boot/job/cpuset/UTC、module/toolchain/job-script hash、single-process/allocation 条件を記録し、report が manifest/protocol と照合する。`p2_2.ENV_TAG` pin は共通 guard に置換する。Pegasus registry entry 未登録中は実走拒否を明示する。

11.

- severity: should-fix
- 攻撃シナリオ: duplicate-key 拒否を任意にすると、manifest に同名 `run_contract` 等を二つ置き、Python の last-wins 値を実行させながら先頭値を人間レビューへ見せられる。manifest hash/id も parse 後の dict から作るため、この曖昧性を検出しない。
- 根拠 file:line: [s8b_oracle_manifest.py:79](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_manifest.py:79), [s8b_oracle_manifest.py:586](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_oracle_manifest.py:586), [s8b_verdict.py:409](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_verdict.py:409), [phase3-8b-descriptor-design.md:406](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/phase3-8b-descriptor-design.md:406)
- 提案: M3 で `object_pairs_hook` による duplicate 拒否まで必須化する。top-level だけでなく nested object の重複も負例にする。既存 writer は Python dict から生成するため、この変更で正当な生成経路は壊れない。

確認できなかった点: pinned CCBench submodule はこの worktree で未初期化、ネットワークも利用不能だったため、実ソースの `__DATE__/__TIME__/__FILE__` 検索と二重 clean build は実施不能だった。したがって、それらが現物に存在するという攻撃は所見に含めていない。

攻撃不成立として除外したもの:

- 有限な正当 JSON に対する `allow_nan=False` は canonical bytes・pretty writer bytesを変えないため、`manifest_sha256` が変わる反例は見つからない。
- oracle driver は verified manifest の値を `pipeline.evaluate(..., bench_max_rounds=...)` に明示渡しするため、`pipeline.py` の汎用 default=3 自体は抜け道ではない。問題は第9所見の「残りの run contract が未束縛」である。

### C4 — Lane P + Lane J + 横断

総合判定: この順序・仕様のまま着手してはいけない。must-fix が6件ある。

1.

- severity: must-fix
- 攻撃シナリオ: M1 が `pairs` に stock を含めるよう要求しているため、正規の floor artifact が必ず schema 不一致になる。生成側は stock を基準値として除外し、非 stock 構成だけを `pairs` に入れている。
- 根拠 file:line: [plan:81](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:81)、[s8b_floor_stats.py:334](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_stats.py:334)、[floor package:74](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-16_s8b-floor-protocol-package.md:74)
- 提案: `pairs` の期待集合を「ratified freeze の構成集合 − stock_configuration」と定義する。stock key の混入、非 stock key の欠落、余分な key をそれぞれ拒否するテストを追加する。

2.

- severity: must-fix
- 攻撃シナリオ: M6 の `pairs[on_choice]` は名前空間が違う。prediction の `on_choice` は `c01` 等の choice ID だが、floor の key は構成名である。正規入力でも lookup が失敗するか、攻撃者が注入した偽の `c01` floor を参照する。
- 根拠 file:line: [plan:91](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:91)、[s8b_selector_input.py:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_selector_input.py:22)、[s8b_selector_freeze.py:510](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_selector_freeze.py:510)、[s8b_floor_stats.py:322](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_stats.py:322)
- 提案: ratified freeze から検証済み `binding_key` を取得し、それで floor を引く。`on_choice` を直接 key にしない。M1〜M5 は先行可能だが、この変換を伴う M6 は R+V と同一 commit に移す。

3.

- severity: must-fix
- 攻撃シナリオ: builder が正しい値を生成しても、`validate_protocol()` の直接呼び出し経路は固定 pin を強制しない。別の有効構成を stock にする、`wired_min_rel_floor=1`、`extime_s=999`、任意の ccbench pin や freeze path/hash を与えても通過できる。builder→validator の正常系テストだけでは自己整合しか検査しない。
- 根拠 file:line: [s8b_floor_campaign.py:251](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:251)、[s8b_floor_campaign.py:258](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:258)、[s8b_floor_campaign.py:285](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:285)、[s8b_floor_campaign.py:287](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:287)
- 提案: 承認済み固定値を一つの immutable 定義に集約し、builder と validator の双方がそれを参照する。テスト側には独立した golden canonical bytes/hash を置き、全固定 field の一項目 mutation を拒否させる。

4.

- severity: must-fix
- 攻撃シナリオ: `freeze` と `ccbench_pin` の充填元が未確定である。実行時に現在の freeze bytes や `CURRENT_PIN` を読む実装にすると、ファイルや HEAD が変わるたびに「現在値を正しい pin として追認」できる。F7 が要求するのは特定の v1 bytes の固定である。
- 根拠 file:line: [plan:123](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:123)、[phase design:406](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/phase3-8b-descriptor-design.md:406)、[pin.py:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/pin.py:28)
- 提案: v1 freeze の正規 path と既知 SHA-256、完全な ccbench commit ID を承認定数として固定する。builder は現在値を採用せず、現在 bytes/checkout が固定値と一致することを検証してから組み立てる。

5.

- severity: must-fix
- 攻撃シナリオ: Lane P は二重実装を残す。共有 helper は strict rc 契約を持つ一方、floor 側は独自 `pgrep` parser のままで、`rc=1` に stdout/stderr が付いていても clean、`rc=0` で stdout 空でも clean になる。さらに計画された B-2 反転テストは calibrator 側だけなので、floor 側だけ自己+子孫除外へ回帰しても検出できない。
- 根拠 file:line: [s8b_floor_campaign.py:471](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:471)、[s8b_floor_campaign.py:490](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:490)、[runner.py:167](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/calibrator/runner.py:167)、[floor package:190](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-16_s8b-floor-protocol-package.md:190)、[test_s8b_floor_campaign.py:671](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/tests/test_s8b_floor_campaign.py:671)
- 提案: raw stdout を保持する構造化された共有 probe を作り、両経路から使う。少なくとも `rc=1+output`、`rc=0+empty`、自プロセス、実子、foreign PID を両 consumer で検査する。helper 削除時は [runner.py:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/calibrator/runner.py:153) と [test_calibrator.py:397](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/tests/test_calibrator.py:397) の子孫除外記述も同時に消す。

6.

- severity: must-fix
- 攻撃シナリオ: 「probe と計測が逐次だから残存子は問題にならない」という解析は、計測中だけ存在する外部 competing process を扱えていない。`pgrep` は時点スナップショットなので、pre-probe 後に開始し post-probe 前に終了したプロセスは完全に不可視で、汚染された計測が採用される。pipeline の bench/verify と between-run settle は post-probe すらない。
- 根拠 file:line: [s8b_floor_campaign.py:813](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:813)、[s8b_floor_campaign.py:825](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:825)、[pipeline.py:241](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/pipeline.py:241)、[pipeline.py:597](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/pipeline.py:597)、[between_run_floor.py:69](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/between_run_floor.py:69)
- 提案: official floor の前提として、計測期間全体を覆う監視または排他 attestation を追加する。裁定済み機構を変えられないなら、この race を残余リスクとして明示し、受容を改めて裁定させる。計測中だけ competitor を起動して終了させる統合テストを置く。

7.

- severity: should-fix
- 攻撃シナリオ: create-only writer に「テストは tmp のみ」という運用上の約束しかない。`output/s8b-freeze/` は hook の保護対象ではないため、default path や fixture の誤り一つで実 protocol JSON を生成し、この wave の非発効境界を破れる。
- 根拠 file:line: [plan:127](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:127)、[hooks/README.md:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/hooks/README.md:39)、[hooks/README.md:106](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/hooks/README.md:106)、[s8b_floor_campaign.py:1334](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/campaign/s8b_floor_campaign.py:1334)
- 提案: writer に production default path を持たせず、明示的な出力先を必須にする。テストでは repository 内の `output/s8b-freeze` を拒否し、実行前後の tree が不変であることと、official mode が引き続きゼロ副作用で拒否されることを検査する。

8.

- severity: should-fix
- 攻撃シナリオ: `contract_sha256` は F4 を機械的に実現する合理的な実装だが、現行の正本には protocol key として記録されていない。非正本の consultation やコードコメントだけに残すと、後から「凍結案にない18番目の key」を無断 schema 変更として争われる。
- 根拠 file:line: [phase design:362](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/phase3-8b-descriptor-design.md:362)、[plan:131](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:131)、[wave3 consultations:74](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-floor-v2-wave3-consultations.md:74)
- 提案: §9 と worklog に「F4 の実装解釈として exact `contract_sha256` pin を追加した」と記録する。実 protocol がまだ存在しないため新しい数値裁定や schema version bump は不要だが、その判断理由も明記する。

9.

- severity: should-fix
- 攻撃シナリオ: sha256 照合対象が不完全かつ「相談逐語3本」と曖昧で、機械検査できない。登録済み freeze には `known_axes_freeze.json` と `measurement_freeze.json` もあり、前者は B-2 holdout freeze から直接参照される。
- 根拠 file:line: [plan:137](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:137)、[output/README.md:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/README.md:28)、[holdout_freeze.json:9](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/s8b-freeze/holdout_freeze.json:9)
- 提案: exact path→SHA-256 の manifest を作り、少なくとも `output/s1-freeze/{known_axes_freeze,measurement_freeze}.json`、`output/s8b-freeze/holdout_freeze.json`、裁定根拠として使う insight 全件を列挙する。各 commit では hash 検査に加えて明示的な diff allowlist を使う。

10.

- severity: should-fix
- 攻撃シナリオ: mutation 数を約15に固定しても、境界変換の破壊を検出できない。列挙には stock pair 混入、choice ID/config ID 混同、floor 側だけの B-2 回帰、固定 protocol field の直接 validator bypass、production path writer、official-mode 発効が含まれていない。
- 根拠 file:line: [plan:145](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:145)、[test_s8b_floor_campaign.py:123](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/tests/test_s8b_floor_campaign.py:123)、[test_s8b_floor_campaign.py:671](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/orchestrator/tests/test_s8b_floor_campaign.py:671)
- 提案: 件数目標を捨て、上記の信頼境界ごとの mutant matrix にする。共有 runner と floor consumer の probe mutant は別々に数え、protocol の固定 field は一項目ずつ変異させる。

11.

- severity: should-fix
- 攻撃シナリオ: `docs` を最後の独立 commit にすると、実装完了 commit で phase checkpoint が未更新になる。さらに計画に handoff の節目更新・最終吸収削除と worklog 一回更新が明記されていない。現在の phase3 は F6/F7/B1/B2 が未裁定という古い状態を保持している。
- 根拠 file:line: [plan:142](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/output/insights/2026-07-18_s8b-strict-v2-wave-consultations.md:142)、[CLAUDE.md:153](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/CLAUDE.md:153)、[docs/phase3.md:54](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/phase3.md:54)、[handoff README:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/handoff/README.md:10)、[handoff README:12](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-v2-prereqs/docs/handoff/README.md:12)
- 提案: 波の完了を成立させる実装 commit に phase checkpoint を含める。worklog は全検査後に一度だけ更新し、handoff は各節目で更新した後、内容を正本へ吸収して完了 commit で削除する。単独の最終 docs commit は説明資料だけに限定する。

---

## §3 親裁定表 (real/refuted と採否)

事実検証 (親が直接実施): v1 bytes sha256 = `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`
(C2-5 の主張と一致) / v1 の `frozen_at_head` 2e20d441… は **repo に存在しない dangling** (C2-5 確認。
2026-07-17 の Claude-Session trailer 廃止 = 履歴書換えの帰結と推定) / .gitignore は生ログ・ビルド
キャッシュ系を隠すが floor WAL 置場 (`output/env/`) は非 ignore (C2-3 は部分的に real)。

| ID | 裁定 | 採否と反映 |
|---|---|---|
| C1-1 active の HEAD ローカル性 | real 部分 | H-pure 検証へ (検証開始時に H を 1 回捕捉し、record 列挙・blob 読取を H の tree に固定。判定は「H に対する純関数」)。canonical ref 強制は Pegasus オフライン運用で検証不能 — 「active/revoked は検証 commit H に相対」と保証を縮小し限界として記録 (§5-vi) |
| C1-2 genesis/edge 不変条件 | real 採用 | genesis = parent null 唯一 + gen=1。child N=parent.N+1、path 正規形 gN、supersedes = parent 世代 bytes hash 完全一致、pointer filename = pointer canonical bytes sha256、approval_sha256 = approval record bytes sha256 |
| C1-3 fork 回復なし・revocation DoS | real 採用 | revocation / pointer-cancellation record にも R2 同等の user-commit 検証 (`AI-Agent: none` 逐語 + 導入一意 + 不変) を要求。無効 record (AI trailer 等) は「検証エラー → active なし fail-closed」(可用性 DoS は fail-closed 設計の許容内)。fork 回復 = pointer cancellation tombstone。revoked 世代の successor は独立承認済みなら資格維持 (§5-vii 追認) |
| C1-4 単一 commit 迂回 | real 採用 | 機械検査に追加: 世代導入 commit ≠ approval commit / approval commit の diff-tree は {approval record, active pointer} の追加のみ / 世代を `none` commit で導入した場合は拒否 |
| C1-5 path history simplification | real 採用 | 履歴検査を「∀C ∈ rev-list(H): entry(C,path) ∈ {absent, expected_blob_oid}」の全 DAG 不変条件へ再設計 (`git cat-file --batch-check` で一括)。導入 commit 集合 = parent に absent な commit 全件に user-commit 検証。shallow repo は即拒否。merge add/add・削除→再作成・cherry-pick を実 git repo 統合テストへ |
| C1-6 逐語 trailer 判定 | real 採用 | interpret-trailers parse == ["none"] ∧ raw message bytes に行 `AI-Agent: none` が逐語存在 ∧ 他の AI-Agent 系行なし、の二重判定。git 呼出しは trailer 設定を明示 pin |
| C1-7 frozen dataclass の限界 | real 採用 | payload を再帰 immutable 化 (MappingProxyType/tuple)、constructor は loader 内限定 (静的検査テスト)、保証は「公開 API から昇格不能」に限定して記録 |
| C1-8 F5/F6 schema 衝突 | real 採用 | v2 header の exact field 列挙を確定 (§4)。approval 系 field (approved_by 等) は世代から全廃し v2 loader は未知 key として拒否。transition table は JSON Pointer 完全列挙。§5-i 追認 |
| C1-9 GENERATION_SCHEMA_FIELDS union の限界 | real 採用 | union は defense-in-depth と明記。実境界 = consumer が RatifiedFreeze のみ受理 + raw fallback 撤去 + 静的検査 (実走 module が load_verified_freeze/直接 JSON load を参照しない) |
| C1-10 linearization point | real 採用 | C1-1 と同じ H 固定 + activation_head を RatifiedFreeze/manifest/WAL へ記録 + run marker 直前の HEAD 一致再確認 + 対象 namespace の dirty 拒否 |
| C1-11 hooks を防壁に数えない | real 採用 | 文言修正 + guard_write に s8b-freeze 配下の拒否を追加 (誤操作抑止であり認証でないと明記、hooks/README 契約に従う) |
| C2-1 measurement_closure が transition 外 | real 採用 | v2 header exact 列挙に `measurement_closure` を含め、F5「v2 header」の実装解釈として §5-i で追認に載せる |
| C2-2 事後ホワイトリスト化 | real 採用 | launch certificate を floor campaign official 開始時に create-only 発行 ({v1 hash, clean-scan digest, protocol sha256, UTC, run id})。journal が certificate hash を束縛、closure は certificate 起点の lineage から導出。certificate 以前に削除された痕跡は原理的に検出不能 — §5-viii の限界として明記 |
| C2-3 列挙盲点 | real 部分 | closure artifact は世代 commit G に **commit することを必須化** (blob 検証で担保)。search の列挙は現行境界を維持しつつ symlink/gitlink を黙殺せず拒否/明示 inventory 化。ignored 領域 (build cache 等) の盲点は scan コスト (GB 級) との交換で受容し、§5-viii で境界を明記 (v1 と同じ認識限界) |
| C2-4 bool 予告と hit 型の不一致 | real 採用 | 予告 bool を全廃。closure = {canonical_path, sha256} のみとし、hits_by_holdout は verifier が同一 bytes から導出して per-holdout で完全一致比較 |
| C2-5 v1 trust root | real 採用 | v1 canonical path + bytes sha256 (315b1eb8…) を verifier 定数で固定。v1 は `LegacyFreeze` へ型分離。dangling head は migration 記録に明記 (head 検証は履歴書換えで恒久不能、bytes hash で束縛) — §5-viii |
| C2-6 frozen_at_head 未束縛 | real 採用 | 世代導入 commit G は非 merge で G^ == frozen_at_head を要求。G には世代 file + closure artifact を同時収録。approval/active は別 commit A |
| C2-7 selector/manifest/verdict bypass | real 採用 | manifest fallback 削除 (VerifiedManifest 単一 object)、verdict の floors/holdouts 外部入力を廃止 (ratified freeze から導出)、selector CLI に v1 pin 定数 (Lane J の承認定数) の一致要求を追加 |
| C2-8 単一 snapshot 不成立 | real 採用 | closure/世代/approval は H の blob から一度だけ読み bytes を hash/parse/戻り値に共用。search は列挙前後 digest 一致で締める。O1 期待 hash は RatifiedFreeze 内の検証済み floor artifact から取得 (再読込禁止) |
| C2-9 manifest gate 二重読込 | real 採用 | verify_manifest → VerifiedManifest {bytes, sha256, document} 返却。gate と run_block が同一 object を使用、再読込削除 |
| C2-10 高コスト検証の構造維持 | real 採用 | 静的 ratification と LaunchValidatedFreeze (full scan 済み) を型で分離、skip flag なし。`_assert_search_operational` (陽性対照) を分離維持。mutation matrix へ search 未実行系を追加 |
| C3-1 pairs の stock 除外と choice_id 名前空間 | real 採用 | pairs 期待集合 = 構成集合 − stock_configuration。verdict は trusted projector (ratified freeze の catalog で choice_id → binding_key 解決) を経由し scalar 契約を維持。on==off は floor 照会なしで不成立側、off≠stock は判定不能 + protocol violation 記録 — §5-iii 追認 |
| C3-2 verdict が任意 off を受理 | real 採用 | VerifiedPrediction 型を導入し、prediction freeze の検証 (off = stock binding の機械検査) 後にのみ projector/verdict へ |
| C3-3 shape 相関検査 | real 採用 | floor = exact {by_holdout}、per-holdout exact 3 keys、pair 集合完全一致、scale_ref null ⇒ 全 null、scalar_alt == max(pairs) or null を検証 |
| C3-4 fixture 赤化圧力 | real 採用 | 共有 v2 freeze fixture を新設し manifest/driver/report のテスト群を Lane M の明示対象に含める。負例 (scalar 全件・混在・stock 混入・欠落/余分・明示 null) を追加 |
| C3-5 bench-binary-mismatch の閉表不適合 | real 採用 | driver outcome 表 + report 証拠 truth table + judge unknown 伝播まで一貫して通す。可能な全セル事前検査 → gate refusal を第一防壁、pipeline 照合を第二防壁 (TOCTOU) に |
| C3-6 floor が実行 bytes を証明しない | real 採用 | floor session 実行直前の full-hash 再照合 + journal 記録 (receipt)。verify_floor_artifact に binaries 検証 ((holdout, configuration) 完全集合 + hash 一致) を追加 |
| C3-7 同一 buildcache 前提不成立 | real 採用 | content-addressed binary store (env scope 永続領域) へ floor が計測 bytes を保存。oracle は run marker 前に全期待 hash の存在+一致を検査、欠落は refusal (再ビルド fallback なし)。cache key の compiler version 非含有は既知限界として記録 |
| C3-8 scale gate の分母・タイミング・伝播 | real 採用 | judge 完了後に stock median_of_medians で相対差 (分母 scale_ref、Fraction 厳密、ちょうど tol は adequate) を判定。stock 非 eligible / scale_ref null → 当該 holdout の第 3 条件のみ判定不能。report/verdict schema に scale 状態を追加 — §5-iv 追認 |
| C3-9 run contract 未束縛の残余 | real 部分 | bench_max_rounds==1 exact pin + env 系 (numactl/clocks_per_us/env_tag/contract_sha256) は env contract から導出・完全一致。ccbench_pin は承認定数と一致。reps/extime は experiment_numbers 裁定まで manifest 入力のまま — 残余未束縛として §5 延期台帳に明記 |
| C3-10 contract_sha256 恒真記録・ENV_TAG pin・γ-4 | real 採用 | 最小共有 execution guard/receipt を本 wave に実装 (両 driver 共通: contract lookup + contract_sha256 一致 + hostname/boot_id/cpuset/UTC 記録、report が manifest と照合)。floor の p2_2.ENV_TAG pin は共有 guard へ置換。G12 の完全強制 (walltime 予約・allowlist・attestation) は Pegasus 登録段のまま (runbook §7) |
| C3-11 manifest duplicate key | real 採用 | M3 で object_pairs_hook による重複拒否 (nested 含む) を必須化 |
| C4-1 pairs stock 混入 | real 採用 | C3-1 と同一修正 |
| C4-2 choice_id/config 名前空間 | real 採用 | C3-1/2 と同一。M6/M7 (projector/verdict) は R+V 後の Lane O commit へ移動 (順序矛盾の解消) |
| C4-3 builder/validator 二重定義 | real 採用 | 承認済み固定値を単一 immutable 定数 module に集約し双方が参照。独立 golden bytes/hash テスト + 全固定 field の一項目 mutation 拒否テスト |
| C4-4 freeze/ccbench_pin 充填元 | real 採用 | v1 freeze path+sha256 (315b1eb8…) と ccbench full commit id を承認定数化。builder は現在値を採用せず、現物が定数と一致することを検証してから組立て |
| C4-5 probe 二重実装残存 | real 採用 | 構造化共有 probe (raw stdout 保持) を単一実装化し、runner と floor の双方が消費。rc=1+出力 / rc=0+空 / 自 PID / 実子 / 他者 PID を両 consumer で検査。B-2 反転テストも両側 |
| C4-6 計測中の時間窓 | real 記録 | 裁定済み機構 (probe→measure→post-probe) の既知限界として §5-viii へ明記。機構変更は再裁定事項のため行わない。performance_anomaly (CV gate) が部分的緩和である旨も記録 |
| C4-7 builder の production path 事故 | real 採用 | writer に default path なし・明示出力先必須。テストは実 freeze 配下を拒否 + 実行前後 tree 不変検査。C1-11 の hooks 追加が第二防壁 |
| C4-8 contract_sha256 の記録 | real 採用 | §5-v の追認事項として worklog / §9 追記案に記録 (F4 の実装解釈、schema 変更でなく凍結前の key 追加) |
| C4-9 凍結 sha256 対象の曖昧さ | real 採用 | exact path→sha256 の frozen-artifacts manifest (テストとして機械検査) を新設。s1-freeze 2 file + holdout_freeze + 裁定根拠 insight 全件を列挙 |
| C4-10 mutation matrix | real 採用 | 件数目標を捨て信頼境界別 matrix へ (stock pair 混入 / choice-config 混同 / floor 側 B-2 回帰 / validator bypass / production writer / official 発効 / search 未実行 / HEAD cache 化を追加) |
| C4-11 docs commit 規約 | real 採用 | 完了 commit (最終 docs commit) に phase3 checkpoint + worklog + handoff 吸収削除をまとめる。worklog はセッション末 1 回 |

**refuted: 0 件。** 43 所見全てを real (採用 38 / 部分採用 3 / 記録のみ 2) と裁定。

---

## §4 確定プラン v2 (§1 からの主要差分)

1. **検証は H-pure**: 開始時に HEAD=H を捕捉し、record 列挙 (`ls-tree`)・blob 読取・履歴検査を全て H に固定。
   履歴不変条件 = 「∀C ∈ rev-list(H): entry(C,path) ∈ {absent, expected_oid}」(batch-check 一括)。
   shallow 拒否。activation_head を成果物へ記録
2. **v2 世代 schema (exact)**: v1 field (approval 系なし) + v2 header =
   {schema_version, generation_number, supersedes_sha256, refreeze_note, frozen_at_head, env_tag,
   floor_protocol, floor_source, measurement_closure}。closure = [{canonical_path, sha256}]。
   transition = JSON Pointer 完全列挙
3. **発効トポロジー**: 世代導入 commit G (非 merge、G^ == frozen_at_head、世代 + closure artifact を
   同時収録、`none` trailer なら拒否) ≠ approval commit A (diff = approval + active pointer のみ、
   `AI-Agent: none` 逐語)。genesis/連番/正規 path 規則。revocation・cancellation も user-commit 検証。
   v1 は LegacyFreeze (bytes 定数 315b1eb8… で束縛、head 検証は migration 記録で免除)
4. **launch certificate**: floor official 開始時に create-only 発行 → journal 束縛 → closure 導出。
   floor は session 直前 binary 再 hash receipt + content-addressed binary store へ保存。
   verify_floor_artifact が binaries を検証
5. **oracle**: RatifiedFreeze のみ受理 (refusal marker 置換)。期待 binary hash は freeze 内の検証済み
   floor artifact から (store 照合、欠落 = refusal)。bench-binary-mismatch を outcome/report/judge へ
   一貫。scale gate は judge 後・分母 scale_ref・Fraction。run contract は env contract + 承認定数から
   導出 (reps/extime は残余)。共有 execution guard/receipt が p2_2.ENV_TAG pin を置換
6. **verdict**: trusted projector (choice_id→binding_key 解決 + scale 状態 + pair floor) を導入し
   scalar 契約維持。VerifiedPrediction 型。CLI の floors/holdouts 外部入力を廃止
7. **probe**: 構造化共有 probe 単一実装 + B-2 (自 PID のみ) を両 consumer で。テスト両側反転
8. **protocol builder**: 承認定数 module 単一源 (v1 pin / ccbench full sha / 数値 pin / contract_sha256)。
   default path なし。§5-v の追認付きで key 18 個
9. **横断**: frozen-artifacts manifest テスト新設 / guard_write へ s8b-freeze 追加 (誤操作抑止) /
   mutation は信頼境界別 matrix / commit 順 = P → M → RV-core → RV-verify → O → J → docs(完了)

### 実行順とワークフロー配員 (C4-2/C4-11 反映)

- W1 (並列): Lane P (probe 統一 + B-2) / Lane M (manifest strict + per-pair + fixture + VerifiedManifest)
  — M6/M7 (verdict) は含めない
- W2: Lane RV-core (s8b_ratified_freeze.py + hooks + frozen manifest テスト)
- W3: Lane RV-verify (F7 verifier + launch certificate + floor receipt/store + LegacyFreeze 移行定数)
- W4: Lane O (driver v2 結線 + projector/VerifiedPrediction + report/judge 伝播 + 共有 guard)
- W5: Lane J (承認定数 + builder)
- W6: mutation matrix (信頼境界別) + 全テスト
- 各レーン: 実装 opus (high) → 敵対レビュー opus ×2 (裁定整合レンズ / fail-open・回帰レンズ、
  verdict=fix-required も修正対象) → 修正 opus → 再レビュー。機械実行 sonnet。fable 子なし。
  親が各 W 後に独立検算し commit (AI-Agent trailer + 凍結 sha256 照合)

## §5 ユーザー追認待ち (裁定文言の実装解釈) と限界記録

追認待ち (次回ユーザー接点で提示):
- (i) v2 header の exact field 列挙 + measurement_closure の追加 (F5「v2 header」の実装解釈)
- (ii) 世代導入 commit の機械制約 (非 merge・G^==frozen_at_head・closure 同梱・approval 別 commit) —
  F6a 発効順序の機械化
- (iii) §6 縁: on==off → floor 照会なしで不成立側 / off≠stock → 判定不能 + violation 記録
- (iv) scale gate: 分母 = scale_ref、ちょうど ±10% は adequate、判定は judge 後 (F1 実装解釈)
- (v) protocol key に contract_sha256 追加 (F4 実装解釈、17→18 key)
- (vi) active/revoked 判定は「検証 commit H に相対」(canonical ref 強制は Pegasus オフラインで不能)
- (vii) revoked 世代の successor は独立承認済みなら active 資格維持
- (viii) 限界の明記: v1 frozen_at_head dangling (履歴書換え由来、bytes hash 束縛で代替) /
  certificate 以前の削除済み痕跡は検出不能 / ignored 領域は scan 境界外 (v1 と同じ) /
  計測中の probe 時間窓 (C4-6、機構は裁定済みのまま)

**(i)〜(vii) は 2026-07-18 ユーザー承認済み** (裁定の記録の正本 =
`2026-07-18_s8b-c22-consultations.md` §5「検証器実装スコープの確定」)。(i)(ii) の closure schema は
案A (measurement_closure 新欄) で確定。(viii) の限界受け入れは floor 実測直前に最終承認。

延期台帳 (完了と数えない): reps/extime 等 run contract 残余の束縛 = experiment_numbers 裁定後 /
G12 完全強制 = Pegasus 登録段 (runbook §7) / selector 側 LegacyFreeze 完全統一の残余は
prediction 封印 wave で再点検
