# Phase 3 段 8a Runbook — trigger-gating 自律ループの実走手順 (Model Y 駆動)

**位置づけ:** 段 8a E/F 段 = 実 LLM (`planner-v4` / `coder-v4-autonomous-trigger-gating` /
`auditor` / `critic`) をメインセッションが spawn し、機械部分
(`orchestrator/campaign/p3_s4_loop_trigger_gating.py`) に proposal を引数で渡す実ループ。
`docs/phase3-s5-sort-runbook.md` (sort 軸) の兄弟文書 — 構造は同じだが、(1) **構文契約の
禁止識別子 grep** が pre-build に加わる、(2) **provenance 情報源記録** (D46 (a) ループ版)
が driver に自動配線されている、の 2 点が異なる。設計正本は D48/D49/D50/D51
(decisions.md) と driver docstring。本書は**運用手順**だけを持つ (設計判断・完了状況は
書かない — 正本は worklog 末尾と phase3.md)。矛盾があれば正典が勝つ。

---

## 0. 実走前ゲート (すべて満たすまで駆動を始めない)

1. **coder 定義が承認・配置済みである** — `.claude/agents/coder-v4-autonomous-trigger-gating.md`
   はユーザー明示承認が必要 (axis-onboarding §5)。草案 =
   `output/insights/2026-07-12_s8a-stage-e-coder-agent-draft.md` (承認待ちの間、実走不可)。
2. **fresh session である** — エージェント登録はセッション開始時のみ (2026-07-08 実証)。
   coder 定義を配置した commit より後に開いた session で、Agent の利用可能型に
   `planner-v4` / `coder-v4-autonomous-trigger-gating` / `auditor` が並ぶこと。
3. **計測層が single-tenant** — `pgrep -a -f 'ccbench|silo|bench'` で他ユーザー/孤児
   ベンチが無いこと (leon 等の並行 claude セッションはバイナリ実行が実際に走っているかで
   見分ける。規律4)。
4. **submodule が pinned-clean** — `git -C external/ccbench rev-parse --short HEAD` が
   `d706650` (= `axis_trigger_gating.PIN` = `pin.CURRENT_PIN`)、status --porcelain が空。
5. **test 緑** — `python3 -m pytest orchestrator/tests/ -q` が all pass。
6. **配線規模の自覚** — `default_perf` は records=100k/threads=4 (有意性を主張しない)。
   headline 性能主張はしない段 — 本軸はそもそも探索補助限定 (段 6 headline 非対象、
   D47 決定 5)。

## 0.5 起草者の firewall 自己宣言 (E 段固有 — 駆動開始前に一度)

- 本 iteration 群の入力 (leakproof_context / planner 入力 / coder 入力) を起草する
  セッションは、**偵察 insight (`2026-07-11_s8a-trigger-gating-recon.md`) とシート
  insight を開かない**。偵察由来で使ってよいのは軸の生死二値 (alive) のみ (D48 条件 7)。
- やむを得ず開いた場合 (デバッグ等) は、**必ず** `--extra-source PATH:ROLE` で provenance
  に記録する (記録義務 — 封じるのではなく監査可能にする)。
- driver は起動時に provenance ヘッダ (固定情報源 + gate 根拠) を自動で焼く。この記録は
  CLI で省略できない (欠落 = 起動拒否)。

---

## 1. 1 iteration の駆動プロトコル (メインセッションが回す)

ループ主導権はメインセッション。harness は LLM を spawn しない。1 周は sort runbook
§1 (a)〜(g) と同型 — 以下は差分のみ:

### (a) planner-v4 spawn
axis は `"silo-backoff-trigger-gating"`。direction/magnitude の意味論をメインセッションが
具体化しない — 特に「どの abort 要因を gate するか」「要因の頻度」等の機序含みの言い換えは
禁止 (D43 の敵対レビュー裁定を継承。要因選択の推理は coder の専権)。

### (b) coder-v4-autonomous-trigger-gating spawn
入力 JSON のフィールドは coder 定義 (草案) の「入力」節が正本。構築時の注意:
- `gating_spec` (骨格抜粋) は coder 定義に**固定で埋め込まれた裸の enum メンバ名リスト**を
  そのまま使う — 実 patch から都度抜粋しない (patch の per-member コメントに「YCSB では
  発火しない要因」の情報が含まれ、偵察隣接の絞り込みヒントになる。E 段レビュー must-fix)。
- `baseline` は E 段 campaign 自身の実測 (throughput/abort率) — 偵察の数値は使わない。
- whiteboard は `loop_state.json` の抽象 whiteboard (機序なし) をそのまま。

### (c) diff プレビュー
```
python3 -m campaign.p3_s4_loop_trigger_gating --preview-diff <scratch>/impl.txt
```
`passed=false` は sort runbook §1(c) と同じ扱い (auditor を呼ばず coder へ差し戻し)。

### (d) auditor spawn
`designated_source_context` には骨格 patch
(`patches/silo-backoff-trigger-gating-variant.patch`) の抜粋 + 軸定数モジュールの
`SYNTAX_CONTRACT_FORBIDDEN` を渡す (auditor 目視チェックリスト項目 13/型 16 の材料)。
auditor への入力・出力を coder に渡さない (入力隔離は auditor.md の規約どおり)。

### (e) proposal ファイル
sort runbook §1(e) と同じ (auditor.diff_digest は (c) の値をそのまま転記)。

### (f) harness 実走 (single-tenant!)
```
python3 -m campaign.p3_s4_loop_trigger_gating --run-iteration <scratch>/prop.json \
    [--extra-source PATH:ROLE ...]
```
- pre-build 検査は 3 段: diff 検疫 (構造) → **構文契約 grep (語彙: 禁止識別子 =
  subtype "syntax-contract" で機械 reject)** → auditor gate (digest 突合 + verdict)。
- **grep 緑は auditor 目視義務を免除しない** — grep が執行するのは禁止リスト上の識別子
  のみで、auditor 目視はその超集合 (恒真述語・fairness 誘導・意味的違反) を担う
  (E 段レビュー FC-8 裁定)。
- provenance: `reports/p3_s8a_trigger_loop_provenance.json` にヘッダ (入口) + iteration
  entry (checkpoint 前進の直前) が自動で焼かれる。**entry が書けないと checkpoint は
  前進しない** (fails-closed) — 破損停止時はエラーメッセージの退避パス (.corrupt.*) を
  確認して復旧する。
- fixture 経路 (`--run-iteration` なしの機械 E2E) は配線確認専用で provenance 対象外。

### (g) 停止判定と critic
sort runbook §1(g) と同じ (critic tag は `p3-s8a-trigger`、digest は
`s8a_trigger_loop_digest.txt`)。

---

## 2. リーク制御チェックリスト (毎 iteration、メインセッションが自己監査)

sort runbook §2 の全項目 (sweet-spot literal・機序・利得・WAL/reports/profile・
planner_direction の解釈非具体化・auditor violations の whiteboard 非転写) に加え、
本軸固有:
- **偵察 insight・シートを開いていない** (開いたら --extra-source で記録した)。
- coder 入力の骨格抜粋は**コメント strip 済みの固定テキスト** (coder 定義内) を使った —
  実 patch からの都度抜粋をしていない。
- coder 入力に要因の頻度・意味説明・「どの要因が効くか」の示唆を書いていない。
- provenance ファイル (reports/) を coder/planner/critic の入力に含めていない
  (記録は監査用でありループ入力ではない)。

---

## 3. 停止と継承

sort runbook §3 と同じ規約 (`L.check_stop` に完全委譲、checkpoint 継承、reflux on/off)。

---

## 4. 既知の限界 (実走前に承知しておく)

- sort runbook §4 の共通限界 (delta_pct 常に None・dry-pass は whiteboard に載らない・
  有意性を主張しない・並行 driver は想定しない) に加えて:
- **要因記録 (骨格 store) の正確性はループ中に常設監視されない** — C 段 positive control
  (D49 決定 1) で一度証明済みで、骨格 store は coder 不可触 (DiffQuarantine 行単位拒否 +
  auditor 型 16) ゆえ構造的に不変、が根拠。骨格 patch を改訂したら C 段 coverage
  (`s8a_trigger_coverage.py`) を再走すること。
- **恒真/恒偽の述語は禁止ではない** — 全集合 (恒等 gate = stock 相当) / 空集合 (真の
  BACK_OFF=0 相当) は正当な探索点 (D 偵察の ident_all / g_none に相当)。auditor は
  観察として報告してよいが reject 理由にしない。
- **fairness (型 15) の機械観測点は未実装** (規律 5、D41 決定 3 から不変)。本軸では
  thid_ の禁止識別子 grep が per-thread gate の直接経路を機械遮断するが、間接経路の
  防壁は auditor 静的目視のみ。
- worktree 隔離は既定 ON (`--no-isolate-worktree` で無効化) — backoff driver (PIN
  028f34d) と共有 tree で交互に走らせると `assert_pinned_clean` が止める (fails-closed、
  意図どおり)。sort driver とは同 PIN (d706650)。
- S2 verify の workload は既定 (rr50 相当) — 偵察 D 段の限定 (4) と同じ off-workload
  被覆が残る。
