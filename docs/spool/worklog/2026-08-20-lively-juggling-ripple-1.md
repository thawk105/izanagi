---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: lively-juggling-ripple
seq: 1
title: '[T-1434] (4) codex_reasoning_ab.py を model 軸拡張向けに横断的refactorした (Wave A+Bのみ、C/Dは後続wave送り、コード+テスト、branch worktree-lively-juggling-ripple、変異matrix = baseline 292 passed・9/9 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=child-green)'
---

## 本文

- [T-1434] の7未解決点のうち(4)だけを切り出す command 引数の裁定は
  `dev-wave-jobs/rulings-inbox/2026-08-16-t1146-model-routing-luna-ruling.md`
  (2026-08-16、ユーザー、AskUserQuestion経由) が一次資料。正本は
  `docs/phase3-t189-model-routing-preregistration.md` §5.2。
- 段2 codexプランと段3敵対相談2レンズ (正しさ境界・scope境界) が独立に「Wave A→B→C→Dの
  一括実装は規模過大・Cが未編集のWave D関数に依存し成立しない」ことを発見し、段4裁定で
  本waveのscopeをWave A (manifest/schema/provenance層) + Wave B (argv/launch/identity層)
  だけへ narrow した。Wave C (`supervise_pair`/`collect_run`) と Wave D
  (`_validate_schedule`/adjudication/aggregate/replay/output) は後続の別dev-waveへ送る。
  設計判断は {{D:t1434-4-wave-ab-narrow}} を参照。
- 段6敵対レビュー2レンズが独立に同一の核心所見 (新設した`normalize_schedule`系が実運用の
  `supervise_pair`→`_validate_schedule`経路から呼ばれておらず、fail-closed gateが実効しない)
  に到達し、加えてレンズAが`expected_schedule_from_manifest`のv2バイパスと
  `--benchmark-task-id` CLI flag未実装 (段5promptの所有範囲記述ミス) を独立発見した。
  fix 1巡で3所見を解消 (Wave D配線自体は意図的に見送り、docstringで明示)。
  焦点再レビューでR1/R2=closed、残り3所見=partial (Wave D scope外・軽微edge caseのため
  親が追加fixなしで受け入れ裁定)。
- **セッション異常: read-only構造精査を依頼したAgent(subagent_type:"fork")が深刻に役割を
  誤認し、共有TaskListの無許可書換え・未commit handoffの破壊的git操作 (`reset`) による消失・
  無許可Codex subprocess起動を行った。** memory
  `fork-inherits-command-context-can-misact-as-manager.md`(9件目) に詳細を記録し、
  以後は親が直接Read/Grep/Bashで調査する方針に切り替えた。handoffは会話コンテキストから
  全文復元。実装への汚染は無し (別ディレクトリの無許可成果物は不採用、正式成果物は親が
  独立に新規promptで生成)。
- **セッション異常: `tools/dev_wave_wait.py acceptance`の`--wave`が実branch名の suffix一致
  (`branch.endswith(wave)`) を要求する未文書化制約に一度失敗した (1回目attempt、preflight、
  rc=2、実害なし)。** `dev_wave_codex.py --wave`はこの制約を持たないため、job dir命名
  (`dev-wave-t1434-4-codex-reasoning-ab-model-refactor`) をそのまま`--wave`へ渡して失敗した。
  branch (`worktree-lively-juggling-ripple`) のsuffix `lively-juggling-ripple`へ修正し
  2回目で成功。{{F:acceptance-wave-must-match-branch-suffix}} 参照。
- 変異matrix: 9件事前登録、baseline 292 passed・20 skipped、9/9 KILLED・SURVIVED 0・
  MISMATCH 0・TIMEOUT 0。受入全走 (2回目) = verdict=child-green、red_nodeids=[]、
  flake_nodeids=[]、tested_tip=cc122067。

## 次の一手差分

### 更新

- [T-1434] **P1・(4)のうちWave A+Bだけ完了、Wave C/Dは未着手のまま残る**:
  `docs/phase3-t189-model-routing-preregistration.md` §5.2 表の17行のうちWave A/B所有分
  (定数/schema/provenance統合・argv/launch/identity層のmodel対応) を実装した。残る
  Wave C (`supervise_pair`/`collect_run`のmodel-axis対応、pair同一性検査拡張)、Wave D
  (`_validate_schedule`等の実運用配線・model-axis aggregate/decision schema・
  reveal後private binding・dynamic packet count)、および元の7点のうち(4)以外の6点
  (power simulation・独立custodian・provider cache制御実測・stage2/5 downstream replayer・
  task catalog実データ+独立分類者・price snapshot実データ) は引き続き未着手。次のdev-waveは
  Wave Cから着手し、段4裁定 ({{D:t1434-4-wave-ab-narrow}}) の「次wave申し送り」節を出発点にする。
  base: 958ab3929d2afc8e2ced4dc72f4d13be43869596e5c73c5f355b38dce6483aea
