# protocol JSON 実凍結 + selector 予測封印 wave (科学レーン第 2 手)
- 目的: protocol 凍結のユーザー引き渡しパッケージ + 予測封印の実走配線を完成させる
- 状態: 作業中
- 最終更新: 2026-07-22 (段 5 実装中 — S/A 完了 commit 済み、R/F 並列実行中)
- 基準コミット: fcf0533 (main == HEAD で開始)。wave commit: e8e0bd4 (単位 S) / 5a2e2f5 (単位 A)

## 段 5 実装の現在地

- 単位 S (missing null 凍結) = **受入済み・commit e8e0bd4** (親環境 25 passed)
- 単位 A (承認定数 4 種) = **受入済み・commit 5a2e2f5** (親環境 10 passed + 承認定数から
  canonical 774 bytes / 261cec1c… 再導出一致を親が独立確認)
- 単位 R (runner: journal header / ClaudeHeadlessProvider / seal CLI / missing 準拠化) =
  codex 実行中 (worktree wave2-unit-r、5a2e2f5 起点)
- 単位 F (freeze-protocol CLI + preflight allowlist 拡張) = codex 実行中 (worktree
  wave2-unit-f、同起点)
- 単位 F = **受入済み・commit 605958d** (親環境 243 passed / 2 skipped — skip は既知の
  real-build canary)。**isatty 防壁の live 発火を親が確認**: 非 tty (AI Bash) からの
  freeze-protocol は拒否・書き込みゼロ。CLI 実行経路 = `PYTHONPATH=orchestrator python3 -m
  campaign.s8b_floor_campaign freeze-protocol --confirm-user-freeze`
- R/F 完了後: 所有ファイル限定 patch → wave worktree へ commit → 親の全走 + 変異 matrix +
  レビュー 2 本

### 手順パッケージ草稿 (段 7 で worklog へ確定転記)

**(ii) protocol 実凍結 (ユーザー、receipt 発行後の clean main で、対話 shell 直打ち):**

```bash
set -euo pipefail
PYTHONPATH=orchestrator python3 -m campaign.s8b_floor_campaign freeze-protocol --confirm-user-freeze
# 期待: {"status":"frozen","path":"output/s8b-freeze/floor_protocol.json","byte_length":774,"sha256":"261cec1c…"}
test "$(wc -c < output/s8b-freeze/floor_protocol.json)" -eq 774
printf '%s  %s\n' '261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac' \
  'output/s8b-freeze/floor_protocol.json' | sha256sum -c -
git add -- output/s8b-freeze/floor_protocol.json
git diff --cached --name-only   # この 1 file だけであること
git commit -m '[protocol] freeze floor protocol (s8b-floor-protocol/v2)' -m 'AI-Agent: none'
```

失敗時: 「post-write 検証失敗。自動削除しないため commit 禁止」が出たら停止して AI に調査を
依頼 (ファイルは残る)。receipt 未発効なら「T-080 receipt が発効状態でない」で拒否される
(先に worklog 2026-07-22 (10) の receipt 手順)。

**(iii) 予測封印 (親 AI、protocol commit 後・floor データ閲覧前):** R の seal CLI 確定後に
コマンド列を確定。直後に FROZEN_MANIFEST へ protocol を pin する AI commit → seal 実走 →
predictions + selector-runs + manifest 更新の AI commit (trailer 付き)。

## 完了した中間成果

- クラス 3 起動手順済み: worklog (10) 末尾・phase3 現行チェックポイント・handoff 残なし・git clean
- task_run start は「pilot は final report により凍結済み」で拒否 (fail-closed 仕様どおり、上限は触らない)
- 親の前提実測 (すべて実 API の read-only 呼び出し、模擬なし):
  - v1 freeze bytes == V1_FREEZE_SHA256 (315b1eb8…) 一致
  - ccbench gitlink d706650… == s8b_approved.CCBENCH_FULL_SHA 一致 (submodule init 済み)
  - build_protocol_document in-memory dry-run OK (write なし):
    master_seed=2026-07-18T17:16:12+09:00 / env_tag=pegasus / stock_configuration=stock_common /
    extime_s=5 / wired_min_rel_floor=0.03 → canonical 774 bytes、sha256=261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac
  - selector plan 6 セル OK (agent 4: rr20/rr80 × on/swapped、static 2: c06)
  - PRODUCTION_PROVIDER = unwired sentinel (fail-closed) — 実走の唯一の残欠
  - T-080 receipt 未発行 (ユーザー手番残)。公式 gate 4 拒否 = 期待状態
- **P6 生死確認 (G1) 成功**: `claude -p --agent selector-8b "<合成payload>"` が rc=0、
  strict schema (8b-selector-output/v1、3 キー逐語、fence なし、c06 選択) をそのまま返した。
  合成 payload = read 50%/skew 0.5/records 12345 (実在 holdout rr20/rr80 と非同値 —
  本番 payload 未使用)。証跡 = wave tmp の liveness-out.txt。
  provenance 8 field = child_id/model/role_file_sha256/started_at/finished_at/
  fresh_context(true 固定)/declared_tools([] 固定)/observed_tool_events([] 固定)
  (s8b_selector_freeze.py:223-252)

## 未完の作業と次の一手

- 段 1 brief 確定済み → 段 2 プラン受領済み (wave tmp/plan-out.md、281 行) → **段 3 敵対相談
  2 本並列実行中** (consult-a = 正しさ境界 / consult-b = 整合・実効性、いずれも reasoning=max) →
  段 4 裁定 → 段 5 実装 → 段 6 レビュー 2 + 変異 → 段 7 記録 → 段 8/9
- 段 2 プラン骨子: 実装 2 単位 (単位 1 = provider + seal CLI: s8b_prediction_runner.py +
  test 同系。単位 2 = freeze-protocol CLI: s8b_floor_campaign.py + test_s8b_protocol_builder.py)。
  P1..P7 概ね維持 + flock 単一駆動ロック + envelope strict parser + user-freeze capability
  (--confirm-user-freeze + 正規 path 完全一致) + claim-crash missing は「prediction file なし
  終端」固定 (choice_id=null 凍結は schema 拡張が要るため wave 外)。変異事前登録 M1..M8。
  新規テスト 12 件。期待赤ゼロ
- 親の追加実測 (段 2 と並行): claude CLI の codex 提案 argv 全実在 (--tools /
  --strict-mcp-config / --permission-mode dontAsk 含む)。envelope 実形 = top-level 20 keys
  (codex 想定 7 + 運用 13: modelUsage/usage/total_cost_usd/stop_reason 等)。**「未知 field 拒否」
  は CLI バージョン揮発で false red の懸念 — 裁定で要対処**。modelUsage に claude-opus-4-8 実在
  (haiku 補助も混ざる)。test_s8b_protocol_builder.py は既存

### brief (段 1 確定版)

**scope:** (i) selector 予測封印の実走配線 (production provider) + テスト、(ii) protocol JSON
実凍結のユーザー引き渡しパッケージ、(iii) 予測封印実走の手順パッケージ。実凍結の実行と
予測封印の実走は本 wave に**含めない** (ユーザー手番 receipt → protocol commit が先行)。

**確定済みユーザー裁定:** 順序 = receipt (T-080) → protocol 凍結 → 予測封印 → floor 実測
(T-083 (a) + F4 凍結順序)。実凍結 = ユーザー工程 (builder → write → commit `AI-Agent: none`、
C4-7)。master_seed / env_tag / wired_min_rel_floor=0.03 (F1) / extime_s=5 / reps=5 /
n_sessions=8 等は承認済み単一源 (s8b_approved)。予測 6 セル = on/swapped 4 (selector agent
独立 1 回・再試行なし・fallback なし・missing=判定不能、§9 項 4/5) + off 2 (static c06)。
journal は at-most-once (R3 層)。selector-8b agent = opus/high/tools なし (frontmatter pin)。

**親の provisional 裁定 (攻撃対象):**
- (P1) 成果物 = 上記 scope (i)(ii)(iii)。実凍結・実走は wave 外
- (P2) provider 配線 = subprocess `claude -p` (headless) で selector-8b を呼ぶ callable を新設。
  既定 PRODUCTION_PROVIDER は unwired sentinel のまま。実走 CLI は明示 opt-in でのみ注入
- (P3) protocol 凍結用 CLI サブコマンド (build+write) を追加 (ユーザーが python -c を打たない)。
  AI はこの CLI を実 output/s8b-freeze へ向けて実行しない
- (P4) FROZEN_MANIFEST への floor_protocol.json / selector_predictions.json 追加は実凍結後の
  後続 commit (本 wave では足さない — ファイル未存在で赤くなる)
- (P5) receipt と protocol 凍結に機構的依存なし (builder は v1 bytes+gitlink+env contract のみ
  検証) — ユーザー手番の順序としてのみ receipt 先行を維持
- (P6) G1 生死確認: 配線実装前に headless `claude -p` の selector-8b 呼び出しを**合成 payload**
  (本番 payload 使用禁止 — cherry-pick 汚染防止) で確認
- (P7) 予測封印の commit = AI trailer 付き AI commit (runner 実走は AI 工程。§9 項 6 の「承認後」
  = F 系パッケージ承認済みと解釈)

**不変条件:** 凍結 3 JSON・legacy checker 0 byte 変更 / official gate 拒否集合不変 (4 拒否) /
AI は output/s8b-freeze/ へ書かない (テスト tmp 除く) / PRODUCTION_PROVIDER 既定 fail-closed
維持 / at-most-once・strict parser 唯一経路・fallback なし不変。

**計画 gate:** G1=P6 で先行確認 / G2=本 wave は floor 実測の直接前提で blocker 該当 /
G3=該当なし / G4=発火素材実在 (holdout_freeze.json + 受領済み master_seed/env_tag) /
G5=レビュー must-fix に影響 1 行必須。

**並列分割:** 実装 1 単位 (provider 配線 + 凍結 CLI — ファイル所有素、codex workspace-write)。
手順パッケージ 2 本は親。レビュー 2 本並列。

### 段 4 裁定 (親、確定) — 相談 A (REJECT・16 所見) / B (NO-GO・12 所見) を受けて

一次裏取り済みの決定打: (1) R3 裁定 (ruling-package.md:228-236) は「missing セルは choice_id=null
で凍結され §6 該当条件が判定不能へ倒れる」を承認済み — 現実装の freeze 全体拒否は承認との乖離
(B-1/A-1 REAL・blocker)。(2) floor preflight の freeze_allowlist は holdout freeze 1 件のみ
(s8b_floor_campaign.py:2445、A-5 REAL)。(3) journal に run header 無し (A-3 REAL)。

**採用 (scope 内、プラン v2):**
- 単位 S: missing row = agent_provenance **null 固定** へ変更 (s8b_selector_freeze、R3 承認の実装)。
  SCHEMA_VERSION は bump しない (v1 文書は実走前で 1 つも存在しない — v1 の意味を承認どおり確定)
- 単位 A: s8b_approved に protocol 自由値 5 種を承認定数として追加 (単一源)
- 単位 R: runner — journal 先頭 run header (schema/pre_oracle_head/protocol sha/freeze sha/
  provider 種別/parser sha)・ClaudeHeadlessProvider (inline agents = role bytes 束縛で TOCTOU 遮断、
  neutral cwd、--setting-sources ""、env sanitize、実測済み argv)・envelope は必須 field+意味検証で
  未知 field 許容・envelope raw bytes を artifact 保存・model は modelUsage 実 slug・child_id =
  session_id・lock を drive_journal 内蔵・writer O_EXCL/O_NOFOLLOW+read-back・seal CLI
  (--provider opt-in、protocol bytes 承認再導出照合、post-write は destination reload 検証)・
  claim-crash missing は R3 どおり null 行凍結 (旧・全体拒否テストの書き換え = 誤固定の是正)
- 単位 F: freeze-protocol CLI (引数レス = 承認定数から組立て、--confirm-user-freeze +
  **isatty(stdin) 機械防壁** + T-080 receipt active 検査前置) + preflight freeze_allowlist 拡張
  (protocol/prediction/journal/payload/raw/envelope)。official 拒否集合は不変
- 手順: protocol commit 直後に AI が FROZEN_MANIFEST pin commit (逐次 pin)。prediction AI commit
  に manifest 同梱。手順パッケージは set -e + && 連結
- C4-7 論点 (B-6/A-4): isatty+receipt+confirm で「人間・受領後・明示確認」に狭める = C4-7 の意図の
  実装であり緩和ではない — 再裁定に送らず D に記録

**scope 外 (登録のみ):** A-6 late forge の verifier 拡張 = oracle 結線 wave の blocking 前提へ /
advisory lock 超の排他 = 脅威モデル外の残存限界 / prediction schema への journal hash 追加 =
journal header + manifest pin で代替 (§9 承認 schema を変えない)

**G1 拡張実測 (親、成功):** inline agents (--agents JSON) + --agent selector-8b-inline +
neutral cwd + --setting-sources "" + --strict-mcp-config + --mcp-config <file> +
--no-session-persistence + stdin (--input-format text) → rc=0・strict 出力・
modelUsage=[haiku補助, claude-opus-4-8]。**罠: --mcp-config は可変長引数 — 直後に positional を
置くと巻き込む (ファイル渡し + 後続オプション挟みで回避)**。証跡 = wave tmp の
inline-out.json / stdin-out.json

### 裁定準備の親メモ (段 4 で使う)

- `_normalise_rows` (s8b_selector_freeze.py:482-485) は **missing row にも provenance 8 field を
  要求** — claim-crash では構造的に組めず、codex の「freeze 全体拒否」記述は正確。runner 実装は
  §9 項 5 の文言 (choice_id=null 凍結) より安全側に広い (実験全体判定不能で停止)。G2 適用で
  1 cycle 後送り + 残存限界記録が親の暫定見解
- FROZEN_MANIFEST は実在 8 ファイル (codex 記述どおり)。AI trailer 構造化形式確認済み
- brief 不変条件「AI は output/s8b-freeze/ へ書かない」は protocol JSON に限定して読み替えが必要
  (予測封印 selector_predictions.json は承認済み設計 (§9 項 6) どおり AI 工程で同領域へ書く)。
  brief の記述が過剰に広かった — 裁定で明確化する
- **下流 gate 整合の懸念 (親発見)**: launch_validate の (ix)-9 `exempt_exact` モード
  (s8b_holdout_freeze.py:295-310) は s8b-freeze の prefix 除外を無効化し exact 免除だけにする。
  descriptor 生値を含む payload_*.json を output/s8b-freeze/selector-runs/ に置くと floor 実走時に
  三軸 scan hit する可能性 — 証拠集合の置き場所 or 免除集合拡張は floor 実走 wave の前提として
  裁定に含める

## 落とし穴・気づき

- codex プロンプトに防護パス (output/s8b-freeze 等) を書く場合は Write ツールで作る
  (guard_bash が heredoc + 防護パスを fail-closed 拒否)
- selector plan の CLI 直接実行は import エラー — `PYTHONPATH=orchestrator python3 -m
  campaign.s8b_selector_freeze plan` で回避
- 実装子の real-repo 系テスト赤は sandbox の submodule index.lock 起因の偽赤がありうる —
  親環境で再現確認してから帰属
- wave 専用 tmp = /home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-protocol-seal/

## dev-wave 改善候補

(気づき次第追記)
