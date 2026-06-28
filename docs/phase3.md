# Phase 3 — LLM コード合成 (planner/coder/auditor)

**目的:** roadmap §2 層2(b) **コード粒度の合成**。CCBench コードの `EVOLVE-BLOCK` 領域を LLM (coder) が
diff で書き、フラグ空間の外に最適化 variant を合成する。P2-4 backoff ケーススタディ (critic 帰属が
フラグ空間外の静的 backoff 合成を駆動し certified なまま勝った) がその予告編。Phase 2 の negative result
(P2-5: フラグ探索は自明) が「なぜ合成が要るか」を動機づける。

**最終成果物 (CLAUDE.md):** 新しい CC + なぜ速いかの説明 (層3) + 試行錯誤の記録。

**設計の出所:** 多エージェント workflow (Map5→Design→Critique3→Finalize) + 敵対的安全検証で kickoff を固め、
ユーザー承認 (2026-06-29)。decisions D22。**絶対規律 (特に 1/2/3/5/6) はここで初めて load-bearing になる**
(LLM が正しさを破りうるコードを書く)。

---

## kickoff の最小スコープ (段階導入・規律5)

**完了定義を 1 点に絞る:** 「EVOLVE-BLOCK 機構 + coder.md + **純 timing variant 1 本**」が
`Tier0(compile/smoke) → pipeline.evaluate → verify → bench → WAL` を 1 周し、stock が cache-hit で
certified commit する。新機構の束を**正しさ的に枯れた足場 (純 timing) で先に通す**のが最小手。

### なぜ first target = 純 timing (静的 backoff) か。lock-sort は撤回
draft 第一候補の sort-strategy (lock 獲得経路) は 3 批判全員が high severity で撤回勧告 (実コード裏取り):
- **verifier は lock 獲得順をトレースしない** (commit 時の (epoch,tid) のみ emit, transaction.cc:517-540)
  → lock 経路の正しさを certify 不能 = **規律2 の穴**。
- silo は no-wait (競合即 abort, transaction.cc:154-157 / Options.cmake:34) ゆえ「sort=デッドロック回避」は
  誤診断。sort が動かすのは liveness で、commit 枯渇 (trace-empty abort) として現れ正しさ違反と検出されない。
- 現 CorrectnessWorkload (tuple200/thread4, pipeline.py:49-51) は同一キー競合をほぼ踏まず lock 経路の
  certify が空振り。

→ **純 timing は abort-path のタイミングにしか触れず lock/validation 論理に一切触れない** = 正しさ攻撃面が
構造的に最小、P2-4 で certified 実証済 (BACKOFF_FIXED, backoff.hh:102-106)。sort は機構が枯れた**2番目の
変異軸**に繰り延べ、そこで S2 を単独 load-bearing にする。

### EVOLVE-BLOCK 機構 (P2-4 inert-patch=D18 の一般化、新構文は発明しない)
- `// EVOLVE-BLOCK-BEGIN <id>` / `// EVOLVE-BLOCK-END <id>` で領域画定。領域内は
  `#if CCBENCH_<AXIS> > 0` (= coder 合成枝) `#else` (= stock 逐語温存) `#endif` の二枝。
- **マーカーと #else 枝は人間が一度入れる骨格 (template patch)。coder が触るのは #if 枝の中身だけ**
  (auditor のレビュー対象を局所化)。
- **閉じた領域制約:** #if 枝は既存 silo API を呼ぶ straight-line code のみ。**#include 追加・新規関数/マクロ
  定義・struct/global/型定義の追加改変を禁止** (型レイアウト変更は trace/perf 両ビルドに入り nm 検査も
  name-based hook も素通りする = observer-effect-by-data-structure 対策)。coder は対象 1 patch 以外の
  ファイルを作成/改変しない (Write hook で強制)。
- **適用の隔離:** patch は submodule working-tree への out-of-band 適用 (HEAD は dff0f1e pin 不動 →
  campaign-id 不変)。1 variant 評価ごとに clean→apply→build→revert。apply 前に対象が pinned-clean か
  assert (汚れていたら fails-closed abort)。

---

## kickoff タスク (blocking 順)

- [ ] **(blocking) cache_key + variant_id の honest 拡張**: source_digest を **preprocess 後 (`cpp -E`)
      正規化出力の sha256** で計算し、buildcache の cache_key (buildcache.py) と **variant_id (WAL キー,
      pipeline.py:41)** 両方の pre-image に織り込む。マーカーコメント挿入は生バイトを変えるが preprocess 後は
      #else 枝が原本と同一 → inert template が真に同一 digest (D18 inert 実証を継承、生 sha256 だと全 miss)。
      variant_id が現状 canonical() のみ hash ゆえ**同フラグ別 diff が WAL/critic で alias する穴**を identity
      端から端まで塞ぐ。対象は固定集合 (EVOLVE-BLOCK ファイル + Options.cmake + CMake)。Genome.canonical 生
      表現は据え置き (後方互換)。同 campaign 内で異なる source_digest が同一 variant_id を共有しない assert。
- [ ] **(blocking) EVOLVE-BLOCK template patch**: silo abort-path 周辺 (BACKOFF_FIXED 軸再利用) に骨格を 1 つ。
      既定 inert を preprocess 後ハッシュ一致 → stock genome cache-hit で実証。
- [ ] **(blocking) H3 hooks 2 本 + .claude/settings.json**: PreToolUse で (hook1) EVOLVE-BLOCK 外 / `#ifdef
      TRACE` 外への検証専用フィールド書き込み阻止 (規律1 第二防壁) (hook2) designated patch 以外への Write 拒否
      + **Bash の WAL/build-variants/cache root 書き込み制約** (Edit/Write hook は Bash 経由の echo
      リダイレクトを発火させない穴対策)。盛らない (この 2 本だけ)。現状 settings.json absent / hooks/ は README のみ。
- [ ] **(blocking) 観測者効果の二重検査**: nm の name-based 検査 (buildcache._assert_no_trace_symbols) に加え、
      trace ビルドと perf ビルドが TRACE マクロ以外で差が無いことを **両ビルドの preprocess 出力 (or trace
      シンボル除外の object シンボル集合) を diff** して assert。data-structure 由来の観測者効果を捕える。
- [ ] **coder.md 生成 + 純 timing variant 1 本で全配線 1 周**: coder.md を critic/profiler 体裁で生成
      (agent-architecture.md:66-71)。**まず「#else 枝を逐語複写する no-op variant」**を書かせ stock cache-hit
      で配線実証 → 次に静的 backoff 値 1 つの純 timing variant を Tier0→pipeline.evaluate→verify→bench→WAL で
      1 周。**COMMIT を書く唯一の経路は pipeline.evaluate()** (guided.py の replay-fake certified 経路は live
      variant に絶対再利用しない)。
- [ ] **broken-silo 回帰**: ループ前に broken-silo-norw patch で verifier が確実に G2 赤を返すことを 1 回確認
      (赤検出力の空打ちでない実証)。clean G2 は easy case ゆえ integrity-class fixture は S4 consumer 段で追加。

**新規実体化は coder のみ** (critic/profiler は既存再利用、auditor/planner は後続)。

**完了条件:** 純 timing (or inert no-op) variant 1 本が stock cache-hit で certified commit し、全配線が 1 周回る。
critic 出力は kickoff では「帰属が正しいか」の検証のみ (次手は人間。P2-5/D21 の deceptive 帯誤収束を再演しない)。

---

## 残り Phase 3 着手前 must の blocking 分類

| must | kickoff | 根拠 |
|---|---|---|
| **H3 hooks** | **blocking** | coder が C++ を書く瞬間に第二防壁が要る |
| **cache_key+variant_id 拡張** | **blocking** | inert 実証の継承 + 同フラグ別 diff alias 防止 |
| **観測者効果二重検査** | **blocking** | nm だけでは data-structure 観測者効果を見逃す |
| **S4** | 完了済 | 規律3 配線 (verify-red の構造化 anomaly を abort payload + load_rejections)。consumer 実体化は後続 |
| S2 (certify=perf) | non-blocking | 純 timing は workload 依存パスを持たない。**sort 段で gate 条件に昇格** (calibrator 実測で contention 再現・trace 規模・broken-silo 赤の 3 点) |
| S1 (別 protocol trace-hook) | non-blocking | silo 内に閉じる限り不要。別 protocol 移植で即 blocking |
| C1 (campaign-id drift) | non-blocking | apply→revert で HEAD 不動。housekeeping。並行合成/patch 常駐の段で恒久対応 |

---

## 後続段 (各々 ablation 点を残して投入)

1. **S2 縮小 verify 構成の確定** (calibrator 実走を gate 条件に) — sort 等データパス分岐変異の prep。
2. **S4 load_rejections consumer 実体化** — coder が初めて赤 variant を出す段。verify-red (cycle を断つ) と
   liveness-red (trace-empty/abort 率異常/timeout) の両対応。integrity-class fixture も positive control に追加。
3. **auditor.md 生成と起動** — lock 経路変異の段。lock 獲得が write_set を被覆するか assert + in-class positive
   control suite を own。入力隔離を構造で強制 (WAL fitness を scope に入れない)。lock 経路は auditor live を gate に。
4. **guided 検疫層を diff 検疫へ拡張 + planner.md 生成** — coder 自律期。diff が EVOLVE-BLOCK マーカー間かつ
   #if 枝内に収まるか parse 検証。
5. **sort-strategy ターゲット起動 / git worktree 隔離 / C1 恒久対応** — S2 gate を満たした後 + 並行合成の段。

---

## 残存リスク

- 純 timing first target は**新規性が薄い** (機構の配線実証が主目的、性能新規性は sort 以降)。意図的トレードオフ。
- preprocess 後ハッシュは対象ファイル集合の列挙漏れがあれば偽キャッシュヒットが復活する。固定集合に限定しテストで固定するが
  template patch の改訂で集合が動いたら漏れる残留リスク。
- broken-silo は clean G2 の easy case。coder が現実に出す赤の多くは integrity-class (verdict indeterminate) に
  なりうる → S4 consumer 段で integrity fixture を別途用意 (clean G2 だけで規律3 閉ループを certify しない)。
