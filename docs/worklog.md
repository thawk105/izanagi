# Izanagi 作業ログ (worklog)

セッションごとの進捗を時系列で記録する。git 履歴や各正本に入らない協議・異常・持ち越しを束ねる
「作業の索引」であり、commit 内容の再説明はしない。役割分担:

- 設計判断と却下案 → `docs/decisions.md`
- CCBench の構造的事実 → `docs/ccbench-anatomy.md`
- CCBench のバグ等の知見 → `output/insights/`
- タスク分解 → `docs/phaseN.md`
- **このファイル = それらを束ねる日誌 (各セッションの索引)**

## 新規エントリの書式 (D35)

過去エントリは凍結し、次の規約は新規エントリに適用する。

- 本文化するのは、ユーザー承認・協議の決着、棄却 finding (refuted)、未コミット事象・セッション異常と
  救出、エージェント工数、人間判断待ち・持ち越し、次の一手など **git に入り得ない情報だけ**
- commit は「hash + 件名 (+ 位置づけ 1 行)」まで。連続群は「先頭..末尾 (N 本)」で表し、内容を再掲しない
- 監査の finding 全文と裁定は insight / audit JSON に凍結する。worklog はレンズ数、real/refuted 数、
  最重要 1〜3 件、一次資料ポインタの 10〜15 行に留める
- 論文素材になる段落は行頭に「素材:」を付ける。持ち越しは逐語再掲せず「変わらず (前エントリ参照)」
  とする
- docs(worklog) だけの commit は prose の body を付けず、件名 + 必須 trailer だけにする

### 次の一手の ID 規約 (D70)

「次の一手」の項目が黙って落ちる経路を塞ぐため、各項目に安定 ID を付け、`tools/check_docs.py` が
保存則を機械検査する。ID は角括弧で囲んだ `T-` + 連番で、**表記は 1 つに正規化する** —
1〜999 は 3 桁ゼロ埋め、1000 以上は先頭ゼロなしで書く。冗長なゼロ埋め (4 桁で 1 を表す等) は
同じ数値の二表記になるため**不正形式として赤にする**。

- **位置**: トップレベル list item (インデント無しの `1. ` または `- `) の**先頭**に置く。
  インデントされた子項目は原子として扱わない — **1 原子 = 1 トップレベル項目 = 1 ID** に平坦化する
  (子項目 `(a)(b)(c)` に原子を詰めると、その分は機械検査の網から外れる)
- **採番**: 現行 worklog (「ローテーション」節より後) + `docs/archive/worklog-*.md` + 見送り台帳に
  現存する有効 ID の最大値 + 1。並行セッションは番号を予約したとみなさず、統合直前に再走査して
  未統合側を振り直す (`landed` = main へ統合された時点)
- **不変性**: 一度 land した ID は変更・再利用しない
- **保存則 (機械検査)**: あるエントリの「次の一手」に現れた ID は、後続エントリのトップレベル項目
  (消化または継続) か、見送り台帳のトップレベル項目 (理由付き見送り) に現れなければ赤になる。
  ローテーション境界 (アーカイブ最新の末尾エントリ → 現行の先頭エントリ) も検査対象
- **この節と決定記録には有効 ID を書かない** (採番母集団と sink の自己汚染を避けるため、
  例示は `T-NNN` のようなプレースホルダで書く)

## ローテーション

Phase 境界または現行ファイルの肥大時 (`tools/check_docs.py` の閾値超過が
知らせる) に、過去分を `docs/archive/worklog-<範囲>.md` へ**移動**し、現行ファイルを軽く保つ
(ブート時に読むのは末尾エントリのみ、の運用を軽く保つため。2026-07-05 導入、D35)。
アーカイブは凍結 (訂正注記のみ追記可)。既存アーカイブの一覧は `docs/archive/README.md`。

---
## 2026-07-22 (9) — 裁定 5 件の確定 — 全件推奨どおり: [T-083] (a) 採用・[T-084] 全採用・[T-012] 縮小 (計測なし)

/rulings 経由のユーザー裁定 (ここが記録の正本)。提示 5 件 + 発火待ち 1 件のうち、裁定可能な全件が
**推奨どおりで確定**。運用系の執行を同セッションで実施した。

- **[T-083] = (a) 最短復帰案の採用。** プロセス freeze をこのエントリの発効をもって宣言 —
  supervisor real 開放・dev-wave 自己改善・task-run 拡張・[T-082] 全 caller 移行・新規裁定
  パッケージ化は 8b + 層3 の 1 cycle 完走まで停止、新規 T 番号は実走 blocker のみ。執行 =
  phase3 現行チェックポイントへ 2026-07-22 改訂を追記 (科学レーン: 一回限り移行契約 → protocol
  凍結 → 予測封印 → [T-011] 受諾 → floor (Pegasus 単独) → v2 → oracle → 層3)
- **[T-084] = 5 述語すべて採用。** 執行 = `.claude/commands/dev-wave.md` へ計画 gate G1〜G5 を
  配線 (brief と裁定段で適用)
- **[T-012] = 縮小。** task-run 記録は dev-wave 実行時のみ (既存の段 0 組み込みで充足)。常時
  運用化と CLAUDE.md への新規配線は行わない。pilot 凍結は維持
- **push = 今 push (ユーザー実行待ち)。** main はこのエントリの取り込み後 origin+9。AI は push
  しない規約のため、お手元の `git push` が残作業
- **[T-011] = 発火時に読む (現計画どおり)。** 移行契約 wave 後の floor 直前に発火する

### 消化した ID

- [T-083] 最短復帰案 — **裁定: (a) 採用・執行済み** (phase3 改訂 + プロセス freeze 宣言)
- [T-084] 無駄防止 5 述語 — **裁定: 全採用・dev-wave へ配線済み**
- [T-012] task-run 台帳 — **裁定: 縮小で確定** (dev-wave 実行時のみ記録、pilot 凍結維持)

### 次の一手

1. [T-080] **(T-083 (a) により再構成) 一回限りの移行契約 wave が次の実装 wave** — W 列の最小抽出
   ([T-068][T-077][T-078] を統合)。以降 protocol JSON 実凍結 → 予測封印 → [T-011] 受諾 → floor
   実測 (Pegasus 単独) → v2 候補 → oracle → 層3。W 列の恒久一般化は oracle 後に再開 (D75/D76 は
   破棄しない)
2. [T-068] **移行契約 wave へ統合 (T-083 (a))**: 発効と同時に閉じる
3. [T-077] **移行契約 wave へ統合 (T-083 (a))**: 人間同席再 pin で解消
4. [T-078] **移行契約 wave へ統合 (T-083 (a))**: 外部固定 fixture 契約で再定義
5. [T-066] 恒真隠蔽除去: freeze 公開前に並行実装。変わらず
6. [T-067] exact 化の残り: oracle 前に並行、floor は止めない。変わらず
7. [T-001] ruling-B 単独: floor と並行、公式 report 発行前までに完了
8. [T-002] P-A1(a) Stage 1 + P-C3 ([T-006] 同梱): 同上
9. [T-009] **延期 (T-083 (a) 処置表)**: AGENTS.md 追記は 1 cycle 後
10. [T-060] **延期 (同)**: WAL 用語運用の明文化は 1 cycle 後
11. [T-010] **延期 (同)**: B-008 再試験は 1 cycle 後に再評価
12. [T-011] floor 実測直前に発火 (現計画どおり)。移行契約 wave の次に来る
13. [T-082] **延期 (T-083 (a) 処置表)**: 公式 consumer の必要分のみ移行契約 wave 内で実施、全 caller
    移行は 1 cycle 後
## 2026-07-22 (10) — [T-080] 一回限りの移行契約を実装 — 機構完了・人間 receipt 発行待ち (D78、branch worktree-dev-wave-ruling-ac、計測なし)

/dev-wave 1 回。[T-083] (a) 科学レーンの第 1 手 = 移行契約 wave ([T-068][T-077][T-078] 統合)。
設計判断・残余の正本 = D78、逐語・変異台帳 = `output/insights/2026-07-22_t080-migration-contract.md`。
成果 commit = a0e090f / 689af34 / a1f2db6 / 6767695 (+ 本記録)。**凍結 3 JSON・legacy checker 2 本を
含む no-touch 12 file は 0 byte 変更** (git diff で機械確認)。

- **中身**: sidecar receipt (`output/t080-migration/legacy-freeze-repin.receipt.json`) + 4 状態機械
  (発効後削除 = 明示 refusal) + ancestry 4 分類 (D73 (3)) + H_mig blob closure (R7 (b) の legacy
  前倒し) + generator M 化 (R11) + 決定論 field 全再導出 + 凍結検索式に束縛した live 層2 +
  observation 伝播 (GateDecision/WAL/report) + [T-078] の S2-4.6 承認 fixture (predicate mutant
  1→0→1 実証)。draft/finalize は worktree==H_mig で再構成を実走し、失敗なら receipt 不生成
- **検証**: 敵対相談 2 (両 NO-GO・27 所見) → 親裁定 J1..J13 → 敵対レビュー 2 (両 NO-GO・17 所見) →
  fix F-1..F-8 → 焦点再レビュー (NO-GO・FR1..FR10) → fix G-1..G-7。親の実測で拾った決定打 2 つ —
  `_verify_head(current_head=…)` が等価比較のみでありmonkeypatch を全廃できること、公式 gate が
  一度も通っていないため WAL の「歴史許容」自体が不要なこと
- **変異 matrix (親実測、最終)**: 3 巡 — 1 巡目 12 KILLED + M07 帰属不成立 (二重防御マスク) + M13 等価除外 → 2 巡目 (fix1 後・再登録) 14/14 KILLED → 最終 (fix2 後) **16/16 KILLED** (M15 = 凍結検索式束縛・M16 = key-absent 拒否を追加。unexpected 0・missing 0)。M13 は gate 単層化で等価変異から復活、
  M07 は二重防御マスクを両層同時変異で裏取り (1 巡目の帰属不成立を erratum として台帳に記録)
- **受入 (親環境)**: 全走 **2697 passed / 18 skipped / 0 failed** (baseline 2618 + 新規 79)。
  collected-node 三点比較 = base からの消失 0。check_docs / check_codex_agents 緑
- **公式 gate は依然 4 拒否 (期待状態)**: holdout design_source drift / S-1 source drift /
  floor-null / budget-null。receipt 発行 (下記) で前 2 件が消え、{floor-null, budget-null} の
  2 件 exact になる — floor 実測まで残るのは設計どおり

### ユーザー引き渡し — receipt 発行手順 (発効はここから。所要 ~10 分)

前提: 本 wave の main 取り込み後、**clean な main で** (handoff 残ファイルなし)。

```bash
# 1. draft 生成 + 検証 (AI 生成不可 — H_mig = 発行時 HEAD で人間が実行)
T080_BASIS="$(git rev-parse HEAD)"
python3 orchestrator/campaign/t080_freeze_migration.py draft \
  --basis "$T080_BASIS" --out output/t080-migration/legacy-freeze-repin.receipt.draft.json
python3 orchestrator/campaign/t080_freeze_migration.py validate-draft \
  --path output/t080-migration/legacy-freeze-repin.receipt.draft.json
python3 -m json.tool output/t080-migration/legacy-freeze-repin.receipt.draft.json
```

確認事項: 13 repin の旧→新 hash と provenance_resolved commit・diff 行数 / H_mig / artifact raw
hash 2 件 / D75 §14 の承認済み損失 (worktree drift 受理は R7 (b) の帰結)。

```bash
# 2. finalize + R commit (receipt 1 file のみ・AI-Agent: none)
python3 orchestrator/campaign/t080_freeze_migration.py finalize \
  --draft output/t080-migration/legacy-freeze-repin.receipt.draft.json \
  --confirmed-by 'thawk105' --confirmed-at "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
  --out output/t080-migration/legacy-freeze-repin.receipt.json
rm -- output/t080-migration/legacy-freeze-repin.receipt.draft.json
git add -- output/t080-migration/legacy-freeze-repin.receipt.json
git diff --cached --name-only   # receipt 1 file だけであること
git commit -m '[T-080] activate legacy freeze migration receipt' -m 'AI-Agent: none'
```

```bash
# 3. post-R 受入 (gate は rc=2 が正 — 拒否 2 件 {floor-null, budget-null} を確認)
python3 orchestrator/campaign/t080_freeze_migration.py verify \
  --path output/t080-migration/legacy-freeze-repin.receipt.json
python3 tools/run_tests.py            # 全走 0 failed
python3 tools/check_docs.py && python3 tools/check_ai_provenance.py
```

失敗時 (push 前): `git reset --hard HEAD~1` で R を落とし、修正後に手順 1 からやり直す。
push 後は履歴を書き換えず、別 path の人間裁定 wave で supersede (D78 (7))。

### 消化した ID

- [T-080] **最小抽出 = 移行契約として実装完了** (機構 + テスト + 変異裏取り)。W 列の恒久一般化は
  oracle 後 (D75/D76 は破棄しない)。**receipt 発行のみ残 — ユーザー実行**
- [T-067] 残り (exact 化の残余) — 本 wave の [T-067] 系 helper 維持 + real-repo 2 状態 exact 化で
  前進したが、部分消化のまま (残余は D73 (10) から変わらず)

### 次の一手

1. [T-080] **receipt 発行 (ユーザー、上記手順) が唯一の残工程** — R commit が発効。次 wave =
   protocol JSON 実凍結 + selector 予測封印 (科学レーン第 2 手、T-083 (a) の順序どおり)
2. [T-068] **R commit で「移行契約により superseded」として確定的に閉じる** (D78 (9))。それまで開いたまま
3. [T-077] **R の design_source 再 pin + generator M 化で閉じる** (同上)。それまで開いたまま
4. [T-078] **S2-4.6 承認 fixture (predicate mutant 1→0→1 実証済み) — R commit 時点で閉じる** (同上)
5. [T-011] floor 実測直前に発火 (現計画どおり) — §5-(viii) 残存限界のユーザー受諾。
   floor 実測は **Pegasus 単独** → v2 候補 + 承認 → oracle 実走 → 層3
6. [T-066] 恒真隠蔽除去: freeze 公開前に並行実装。変わらず
7. [T-067] 部分消化・継続: exact 化の残余は D73 (10) から変わらず
8. [T-001] ruling-B 単独: floor と並行、公式 report 発行前まで。変わらず
9. [T-002] P-A1(a) Stage 1 + P-C3 ([T-006] 同梱): 同上。変わらず
10. [T-009] 延期 (T-083 (a) 処置表): AGENTS.md 追記は 1 cycle 後
11. [T-060] 延期 (同): WAL 用語運用の明文化は 1 cycle 後
12. [T-010] 延期 (同): B-008 再試験は 1 cycle 後に再評価
13. [T-012] 延期 (同): pilot 凍結維持。本 wave の task-run start は凍結どおり拒否された (fail-closed 実績)
14. [T-082] 延期 (同): 公式 consumer の必要分は本 wave で充足、全 caller 移行は 1 cycle 後

## 2026-07-23 (1) — wave2: protocol 実凍結の人間 CLI + selector 予測封印の実走配線 (D79、branch worktree-dev-wave-ruling-ac、計測なし)

/dev-wave 1 回 (科学レーン第 2 手 — worklog (10) 次の一手 1 の「次 wave」)。実凍結の実行と
予測封印の実走は行っていない (ユーザー手番 receipt → protocol commit が先行)。両工程を実行
可能にして引き渡す。設計判断の正本 = D79、逐語・変異台帳 =
`output/insights/2026-07-22_wave2-protocol-seal.md`。成果 commit = e8e0bd4 / 5a2e2f5 / 605958d /
868f1d0 / 48e3e0f / e0fedd8 / 65b5c64 / d7ed08f / f6f2d32 / d4b6271 (+ 本 docs 分)。

- **中身**: (1) missing 意味論の v1 確定 — R3 裁定「missing セルは choice_id=null で凍結」の実装
  (provenance null 固定、SCHEMA bump なし)。(2) protocol 自由値 4 種の承認定数単一源化
  (master_seed / pegasus / stock_common / 0.03 — canonical 774 bytes / sha256 261cec1c… を親が
  独立再導出確認)。(3) freeze-protocol 人間 CLI (承認定数のみ・confirm + isatty + T-080 receipt
  active 検査。isatty は誤操作防壁であり認証ではない — D79 (3))。(4) selector 実走配線 =
  ClaudeHeadlessProvider (inline agents で role TOCTOU 遮断・repo 外 cwd・env allowlist・envelope
  意味検証 + 未知 field 許容・provenance 実測化) + journal run_header 証拠鎖 + seal CLI (opt-in・
  protocol blob 承認再導出照合・reload verify)。(5) official preflight の prediction 必須化 +
  exact allowlist (verify 済み bytes 直接束縛)。PRODUCTION_PROVIDER sentinel・official 拒否集合・
  凍結 3 JSON (0 byte) は不変
- **検証**: 敵対相談 2 (REJECT/NO-GO・28 所見 — R3 乖離・5 値 pin 欠如・preflight allowlist
  1 件のみ等を検出) → 親裁定 → 実装 4 単位 (S→A→R→F、worktree 分離) + 親ハンク 2 → 敵対
  レビュー 2 (REJECT/NO-GO・13 所見) → FIX-1..7 → **FIX-7 の下流波及 72 テストを親の全走が検出**
  (実装子の限定実走は親の全走を代替しない、の再実例) → fixture 追随 (親ハンク 4) → 焦点再
  レビュー (closed 6 / partial 4 + 新規 3) → FIX2-1..4。親の実測 = G1 生死確認 (合成 payload、
  本番 payload 不使用)・envelope 実形 20 keys・isatty live 発火・--mcp-config 可変長引数の罠
- **変異 matrix (親実測、3 巡)**: 事前登録 12 件 (M10 は等価変異のため登録見送り — 台帳に理由
  明記)。1 巡目 12/12 KILLED だが帰属 erratum 3 件 (M1 = 診断差先行 → テストを 2 段検査へ /
  M6 = 記載乖離 → 束縛照合ループ除去に訂正 / M13 = 置換不足 → 拡大) → 最終 (fix2 後)
  **12/12 KILLED・survived 0・injection failed 0**
- **受入 (親環境)**: 全走 **2764 passed / 18 skipped / 0 failed** (baseline 2697 + 67)。
  collected-node 三点比較 = base 2715 → 2782、消失 0。check_docs / check_codex_agents /
  check_ai_provenance (288 commits) 緑。task-run start は pilot 凍結どおり拒否 (fail-closed 実績)
- **運用制約の発見**: `_assert_namespace_clean` は output/s8b-freeze 配下の untracked を dirty
  拒否する — **seal 実走と証拠 commit は一体で行う** (下記手順 (iii) に反映済み)

### ユーザー引き渡し (ii) — protocol 実凍結 (receipt 発行後の clean main で、所要 ~3 分)

前提: worklog 2026-07-22 (10) の receipt 発行 (R commit) が完了していること。**対話 shell で
直打ちする** (パイプ・リダイレクト・script 経由は isatty 検査が拒否する)。

```bash
set -euo pipefail
# 1. 実凍結 (承認定数のみから組立て。receipt 未発効なら機構が拒否する)
PYTHONPATH=orchestrator python3 -m campaign.s8b_floor_campaign freeze-protocol --confirm-user-freeze
# 期待: {"status":"frozen","path":"output/s8b-freeze/floor_protocol.json","byte_length":774,"sha256":"261cec1c…"}

# 2. 独立照合
test "$(wc -c < output/s8b-freeze/floor_protocol.json)" -eq 774
printf '%s  %s\n' '261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac' \
  'output/s8b-freeze/floor_protocol.json' | sha256sum -c -

# 3. commit (この 1 file のみ・AI-Agent: none)
git add -- output/s8b-freeze/floor_protocol.json
git diff --cached --name-only   # floor_protocol.json 1 行だけであること
git commit -m '[protocol] freeze floor protocol (s8b-floor-protocol/v2)' -m 'AI-Agent: none'
```

失敗時: 「post-write 検証失敗。自動削除しないため commit 禁止」が出たら commit せず停止して
AI に調査を依頼 (ファイルは残る)。commit 前なら rm で消してやり直してよい。

### 親 AI 引き渡し (iii) — selector 予測封印 (protocol commit 後・floor データ閲覧前)

次 wave の AI が実行: (1) FROZEN_MANIFEST へ floor_protocol.json を pin する commit →
(2) `PYTHONPATH=orchestrator python3 -m campaign.s8b_prediction_runner seal --provider
claude-headless --pre-oracle-head "$(git rev-parse HEAD)"` (clean tree 必須。claude 実呼び出し
4 セル ~5 分) → (3) `PYTHONPATH=orchestrator python3 -m campaign.s8b_selector_freeze verify
--path output/s8b-freeze/selector_predictions.json` → (4) **即座に** predictions +
selector-runs 一式 + FROZEN_MANIFEST 更新を AI trailer commit (namespace clean 検査は
commit 前の状態を拒否する — seal と commit は一体)。claim-crash が起きたら再試行せず、
missing 行込みの封印 (R3 どおり) をそのまま commit する。

### 消化した ID

- 科学レーン第 2 手 (protocol JSON 実凍結 + 予測封印) の**機構は完了** — 残 = ユーザー手番
  (receipt → protocol 凍結) と AI 実走 (予測封印)。floor 実測はその後

### 次の一手

1. [T-080] **receipt 発行 (ユーザー、worklog (10) 手順) → 続けて protocol 実凍結 (ユーザー、
   本エントリ (ii)) → protocol commit 後に予測封印の実走 wave (AI、本エントリ (iii) —
   manifest pin → seal → 証拠 commit。M6 台帳 erratum の残余もそこで吸収)** — ユーザー 2 手番は
   同じ機会に実行できる (receipt → protocol の順)
2. [T-068] R commit で「移行契約により superseded」として確定的に閉じる (D78 (9))。それまで開いたまま
3. [T-077] R の design_source 再 pin + generator M 化で閉じる (同上)。それまで開いたまま
4. [T-078] S2-4.6 承認 fixture — R commit 時点で閉じる (同上)。それまで開いたまま
5. [T-011] floor 実測直前に発火 — §5-(viii) 残存限界のユーザー受諾。floor 実測は Pegasus 単独。
   **floor 実測 wave の blocking 前提 (D79 (7)) はこの手前で消化**: launch_validate の exemption
   拡張 (selector 証拠の三軸語 hit — 置き場所再設計含む) / certificate の allowlist 束縛
   (official 解禁前 MUST) / protocol→seal→commit→floor の統合 E2E / 検証側 lineage 照合
   (worklog 2026-07-18 (9) §5-(ix) 系、変わらず)
6. [T-066] 恒真隠蔽除去: freeze 公開前に並行実装。変わらず
7. [T-067] 部分消化・継続: exact 化の残余は D73 (10) から変わらず
8. [T-001] ruling-B 単独: floor と並行、公式 report 発行前まで。変わらず
9. [T-002] P-A1(a) Stage 1 + P-C3 ([T-006] 同梱): 同上。変わらず
10. [T-009] 延期 (T-083 (a) 処置表): AGENTS.md 追記は 1 cycle 後。変わらず
11. [T-060] 延期 (同): WAL 用語運用の明文化は 1 cycle 後。変わらず
12. [T-010] 延期 (同): B-008 再試験は 1 cycle 後に再評価。変わらず
13. [T-012] 延期 (同): pilot 凍結維持 (本 wave の task-run start も凍結どおり拒否)。変わらず
14. [T-082] 延期 (同): 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-23 (2) — wave3: floor 実測 blocking 前提 2 件のコード機構 (D80、branch worktree-dev-wave-ruling-ac、計測なし)

/dev-wave 1 回 (次の一手 1 がユーザー手番待ちのため、次の一手 5 の blocking 前提から protocol
JSON 非依存の 2 件を選択)。**D79 (7) 4 件中 2 件のコード機構完了** — 実 pin・完全同型 E2E・
lineage 照合は oracle 結線 wave の残余であり、blocking 前提の全消化ではない。設計判断の正本 =
D80、逐語・変異台帳 = `output/insights/2026-07-23_wave3-floor-prereq.md`。成果 commit =
5d2be97 / 8835fa7 / 6c89323 / af8ff49 / 437334a (+ 本 docs 分)。

- **中身**: (1) launch_validate の selector 証拠 exact exemption (§5-(ix)-9 追認方向) —
  predictions/journal/raw/宣言済み envelope を H 錨定 (100644・H==worktree bytes・宣言 sha 一致・
  重複拒否) で免除、payload は非免除 (characterization 固定)。(2) H 錨定 drift-free 証拠鎖 —
  ancestry・sources+protocol+parser の pre_oracle_head blob 照合・journal↔rows↔envelope 相互
  対応 (schema 版数固定・decision_method/choice_id は封印文書同士の直接等値)。現在意味定数への
  依存を launch 射影から排除 (F29/F31 型結合の構造的排除)。(3) runner: envelope 書き込み直後の
  journal 宣言 record・seal の未宣言ファイル fail-closed・.lock 削除。(4) preflight allowlist の
  宣言由来有界化 + freeze namespace 全被覆 (未知ファイル/symlink/phantom 拒否・chain record も
  digest へ) + clean_scan_digest v3 canonical preimage + cert の identity/strict 分離 (既存
  caller 無変更)・発行前独立 2 回 scan
- **main の既存回帰を発見・修復**: wave2 docs commit 441babc の凍結台帳 L642 の三軸語 conjunction
  逐語引用が repo scan invariant + oracle driver 系 11 テストを赤にしていた (受入全走が docs
  commit 前で未検出 — failures F34 新設)。**L642 のみ «» defang + erratum 付記 (5d2be97、原文 =
  441babc)**。凍結逐語への例外編集の正本参照 = D80 (7) と本エントリ
- **検証**: 敵対相談 2 (NO-GO×2・must 12 — 捏造 bundle の免除・rglob 無上限 allowlist・
  verify_prediction_freeze の source 結合等) → 親裁定 v2 (P2 差替え/P6 反転/scope 外 3 件) →
  実装 2 単位 (A→B 直列・worktree 分離) → **親の全走が統合破損 83 件を検出** (実装子の限定実走は
  親の全走を代替しない、の再々実例) → 敵対レビュー 2 (NO-GO×2・must 3 系統 + 親ハンク名指し
  検査 = 所見なし) → fix1 (FIXW-1..7) → 焦点再レビュー (closed 9 / **regressed 1** — fix1 の
  journal 射影弱めすぎ N-01/N-02 を対応表が検出) → fix2 (schema 版数固定 + journal↔row 直接
  等値)。G1 生死確認は brief 前に実測済み (conjunction 証拠の初回 commit 導入 →
  closure-hit-mismatch、2 軸のみ → 通過、事後改竄は namespace-dirty/history-mutated が先行)
- **変異 matrix (親実測、B-057)**: 事前登録 M1-M10 + fix2 で M11/M12 追加。最終 (437334a)
  **12/12 KILLED・survived 0・injection failed 0・復元検査全緑**。帰属 erratum 3 件 (M9 空 tree
  不成立→同一 tree 化 / M7 基準改定「拒否 + cert 不発行」/ M4 helper-leaf kill) + M2 の受理集合
  拡大直接捕捉を手動裏取り — 台帳詳細は insights
- **受入 (親環境)**: 全走 **2815 passed / 18 skipped / 0 failed** (baseline 2764+18)。collected 三点比較 = base
  2782 → 2833 (+51)、真の消失 0 ([control] は c0/c1 へ分割)。check_docs / check_codex_agents /
  check_ai_provenance (295 commits) 緑。task-run start は pilot 凍結どおり拒否 (fail-closed —
  「final report により凍結済み」の新文言。発火条件の再提示は最終報告へ)

### 消化した ID・残余

- D79 (7) blocking 前提: **(a) exemption 拡張 + (b) cert 束縛 = コード機構完了** (本 wave)。
  残 = (c) 統合 E2E (実 protocol JSON 後)・(d) lineage 照合 (§5-(i)〜(viii) 系裁定待ち、
  oracle 結線 wave で再評価) — 変わらず
- scope 外 real 所見 → **ユーザー裁定パッケージ 3 件** (D80 (8)): 初回導入捏造の完全閉鎖 /
  durable digest preimage + resume・ratified の歴史的 cert 照合 / content TOCTOU (受諾リスト
  記載済み・追加処置なし推奨)。いずれも oracle 結線 wave での D79 (7) 第 3 項再評価と同梱を推奨

### 次の一手

1. [T-080] **receipt 発行 (ユーザー、worklog (10) 手順) → protocol 実凍結 (ユーザー、worklog
   2026-07-23 (1) (ii)) → 予測封印の実走 wave (AI、同 (iii))** — 変わらず (本 wave はこれと独立)
2. [T-068] R commit で「移行契約により superseded」として確定的に閉じる (D78 (9))。変わらず
3. [T-077] R の design_source 再 pin + generator M 化で閉じる (同上)。変わらず
4. [T-078] S2-4.6 承認 fixture — R commit 時点で閉じる (同上)。変わらず
5. [T-011] floor 実測直前に発火。**blocking 前提の残 = 統合 E2E (protocol 凍結後) と lineage
   照合 (oracle 結線 wave 再評価)。exemption 拡張と cert 束縛のコード機構は本 wave で完了**。
   D80 (8) の裁定パッケージ 3 件はこの手前で裁定
6. [T-066] **部分消化。** stock_common・system_gate/ident_all の flags golden 化と自己無矛盾
   positive control は本 wave (2026-07-23 (3)) で完了。comparator/predicate/source record の
   独立 golden 化と `test_s1_measurement_freeze.py` の恒真 fixture 本体は未消化のまま — 詳細は
   同エントリと D81
7. [T-067] 部分消化・継続: exact 化の残余は D73 (10) から変わらず
8. [T-001] ruling-B 単独: floor と並行、公式 report 発行前まで。変わらず
9. [T-002] P-A1(a) Stage 1 + P-C3 ([T-006] 同梱): 同上。変わらず
10. [T-009] 延期 (T-083 (a) 処置表): AGENTS.md 追記は 1 cycle 後。変わらず
11. [T-060] 延期 (同): WAL 用語運用の明文化は 1 cycle 後。変わらず
12. [T-010] 延期 (同): B-008 再試験は 1 cycle 後に再評価。変わらず
13. [T-012] 延期 (同): pilot 凍結維持 (本 wave の task-run start も凍結どおり拒否)。変わらず
14. [T-082] 延期 (同): 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-23 (3) — [T-066] 部分消化: stock_common・system_gate/ident_all の flags golden 化 (D81、branch worktree-dev-wave-ruling-ac、計測なし)

/dev-wave 1 回 (次の一手 6 [T-066] は floor と独立に並行実装可)。生死実験で恒真隠蔽を実測確認
(`_stock_common()` 破壊 → `test_s1_measurement_freeze.py` 0 件赤) してから着手。設計判断・逐語・
変異台帳の正本 = D81・`output/insights/2026-07-23_t066-stock-common-trigger-flags-golden.md`。
成果 commit = 58010d4。

- **中身**: `test_s1_known_axes_freeze.py` へ test-local `EXPECTED_STOCK_COMMON`/
  `EXPECTED_TRIGGER_FLAGS` + 型厳密 (`type is int`) 比較 helper を追加し、stock_common (4 flags) と
  system_gate/ident_all (5 flags) の golden 欠落を閉じた。実 `build_document()` の自己無矛盾性 +
  単一フィールド改竄検出の positive control も追加。production ファイルは無変更 (self-hash
  blocker のため、`campaign/s1_known_axes_freeze.py` へ定数を足すと generator.sha256 が変わり
  既存凍結を壊すことを実測で確認し、test-local 定数へ変更した)
- **敵対レビュー (段6) が親裁定の技術的根拠の誤りを検出**: 「comparator/predicate/source の
  独立 golden 化は dangling frozen_at_head (D71(7)(a)) により到達不能」という scope-out 根拠は
  誤りだった。正しくは D71(7)(b)、`if doc != expected_doc` は761行目でなく765行目、かつ現行
  worktree の canonical file は ancestry でなく S-1 source drift (`s8a_trigger_sweep.py` 等) で
  先に止まる。より重要な点として、test-owned な `build_document()`(引数なし)は canonical file の
  ドリフトに非依存で `verify_document()` に自己無矛盾で通ることを実測確認し、fix ラウンドで
  self-consistency + tamper 検出の positive control を追加した
- **T-066 は未完了と明記**: comparator・predicate・source record (path/sha256/key/lines)・
  p2_2/backoff_fixed/sort の flags 等は依然として外部固定 golden が無く、sort comparator を
  名前を保ったまま差し替える攻撃が現行の全 assertion (今回追加分含む) を通過することを両レビューが
  実測した。`test_s1_measurement_freeze.py` の `K.build_document` monkeypatch echo 本体も無変更
- **新事実の追記**: `test_verify_rejects_one_byte_freeze_tamper` (canonical file 対象) は
  S-1 source drift により無改竄でも同じ理由で red になる可能性が高く、positive control として
  false green の疑いがある (本 wave では検証・修正せず棚卸しのみ)
- **受入 (親環境、repo root から)**: fix 前 2815 passed/18 skipped (baseline 一致)、fix 後
  **2816 passed / 18 skipped / 0 failed** (新規テスト1件分の増加のみ、退行 0)。凍結成果物
  (`known_axes_freeze.json`=`354f4b87…`・`measurement_freeze.json`=`203de36b…`・
  `holdout_freeze.json`=`315b1eb8…`) sha256 は実装前後で不変。repo scan invariant
  (`test_s8b_repo_scan_invariant.py`) も docs commit 前に再走し緑
- **事故と復旧**: 受入全走を最初 `orchestrator/` cwd で実行し無関係な2件 (`test_run_tests_task_run.py`、
  nested pytest subprocess の plugin import パス依存) が偽赤化。`git stash push -u -m <tag>` で
  差分退避 → repo root で再現無し確認 → `git stash apply <sha>` で復元 → `stash drop` で片付け、
  以後は repo root から実行して解消 (baseline と一致)。変異検証の一時バックアップに使った `/tmp`
  ファイルが共有ジョブ環境で他プロセスに削除される事故も発生したが、対象が git 管理下だったため
  `git diff`/`git checkout` で問題なく復元できた
- **検証**: brief 前生死実験 (実測) → codex プラン起草 (max、self-hash 衝突を検出) → 親裁定 v1.1
  (test-local 定数へ変更) → 敵対相談 2 (max、正しさ境界/整合実効性、両方で計 5+4 所見) → 親裁定
  v1.2 (system_gate/ident_all を scope に追加、型厳密比較導入、comparator 等は scope 外と裁定) →
  実装 (codex high、1 単位) → 親の変異 M1-M3 実測 (単一理由で kill、復元確認) → 親の受入全走
  (baseline 一致) → 敵対レビュー 2 (max、両方 NO-GO — scope-out 根拠の事実誤認を検出) → 親が
  自分で裏取り (誤りを確認) → fix ラウンド (self-consistency positive control 追加、codex high) →
  親の受入全走・repo scan invariant 再走

### 次の一手

1. [T-080] receipt 発行 (ユーザー、worklog (10) 手順) → protocol 実凍結 (ユーザー、worklog
   2026-07-23 (1) (ii)) → 予測封印の実走 wave (AI、同 (iii))。変わらず (本 wave はこれと独立)
2. [T-068] R commit で「移行契約により superseded」として確定的に閉じる (D78 (9))。変わらず
3. [T-077] R の design_source 再 pin + generator M 化で閉じる (同上)。変わらず
4. [T-078] S2-4.6 承認 fixture — R commit 時点で閉じる (同上)。変わらず
5. [T-011] floor 実測直前に発火。blocking 前提の残 = 統合 E2E (protocol 凍結後) と lineage
   照合 (oracle 結線 wave 再評価)。D80 (8) の裁定パッケージ 3 件はこの手前で裁定。変わらず
6. [T-066] **部分消化。** stock_common・system_gate/ident_all の flags golden 化と自己無矛盾
   positive control は完了 (本エントリ)。comparator/predicate/source record の独立 golden 化と
   `test_s1_measurement_freeze.py` の恒真 fixture 本体、および D81 (7) の新事実棚卸し
   (`test_verify_rejects_one_byte_freeze_tamper` の positive control 疑義) は次 wave へ持ち越し
7. [T-067] 部分消化・継続: exact 化の残余は D73 (10) から変わらず
8. [T-001] ruling-B 単独: floor と並行、公式 report 発行前まで。変わらず
9. [T-002] P-A1(a) Stage 1 + P-C3 ([T-006] 同梱): 同上。変わらず
10. [T-009] 延期 (T-083 (a) 処置表): AGENTS.md 追記は 1 cycle 後。変わらず
11. [T-060] 延期 (同): WAL 用語運用の明文化は 1 cycle 後。変わらず
12. [T-010] 延期 (同): B-008 再試験は 1 cycle 後に再評価。変わらず
13. [T-012] 延期 (同): pilot 凍結維持 (本 wave の task-run start も凍結どおり拒否)。変わらず
14. [T-082] 延期 (同): 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-23 (4) — [T-066] 消化完了: 外部固定 golden 全面拡張・measurement 恒真 fixture 除去・consumer 逐語結線 (D82、branch worktree-dev-wave-ruling-ac、計測なし)

/dev-wave 1 回 (次の一手 6 [T-066] 残余)。brief 前実測で D81 (7) 疑義を確定 (canonical への
verify は無改竄でも改竄でも同一の source drift 理由で FreezeError = tamper test は false-green)
してから着手。設計判断・逐語・変異台帳の正本 = D82・
`output/insights/2026-07-23_t066-golden-continuation-verbatim.md`。
成果 commit = d50f714 / 4c01a05 / 6982579 / e2217c4 (基準 1a41090)。

- **中身**: (a) test 専用 golden 台帳 `orchestrator/tests/s1_expected_goldens.py` を新設 —
  comparator/predicate 逐語・全 flags・SWEEP_US・source layout + exact key-set・campaign 20 path
  bytes pin・CMake lines literal・measurement 側 (comparisons 12 対・master_seed・schedule_hash)。
  canonical 両凍結と機械照合して生成し、独立性を AST guard 化。型厳密比較 (bool≠int≠float、
  None≠欠落)。(b) measurement の D68 (7) 型隠蔽 (K.build_document echo + generator hash 動的注入)
  を全削除し、実材料 module fixture + function スコープ複製へ再設計。M→K 結線検査・cells 射影
  厳密化・pin.CURRENT_PIN 結線・hermetic seam 2 件を追加。(c) known-axes の false-green tamper
  2 件を fresh doc + 理由厳密化へ修正し、negative control 3 件 (generator sha / 非 ancestor head /
  ccbench pin) を新設。(d) prepare_cell → quarantine の逐語受け渡し検査 (canonical 実値
  parameterize 込み) を新設。(e) conftest + serialization 両面へ known-axes 4 + measurement
  10 node を登録 (前 wave の self-consistency 未登録も同時に閉鎖)。production・凍結成果物は
  1 byte も無変更
- **変異 matrix**: 11 変異全 kill、全て新テストのみが検出 (HEAD テストとの差分実証)。K.py bytes
  変更が HEAD の canonical 依存テストへ落とす false-reason 赤は MU-CTRL (comment のみ対照) で
  分離。diagnostic sensitivity pin 枠は空
- **受入 (親環境、repo root)**: 統合後 2826 → fix 後 **2832 passed / 18 skipped / 0 failed**
  (baseline 2816 + 新規 16、退行 0)。1 回目全走で test_dev_waves_integration に /dev/shm 一過性
  偽赤 1 件 — 単独・全走再走とも緑で環境起因と裁定。凍結 3 JSON sha256 不変。repo scan
  invariant + 三軸語検査 (insights 凍結前) とも hit ゼロ緑
- **検証**: brief 前実測 (E1・golden/canonical 全一致・baseline) → codex プラン (max) → 敵対相談
  2 並列 (max、両 NO-GO 計 19 所見: consumer 境界・SWEEP_US・M→K 結線等を採用、pin 相互一致は
  既存 test_s8b_approved で refuted、時間懸念は実測 0.08s で refuted) → 裁定 v2 + 変異事前登録
  9 件 → 親ハンク (golden 台帳) → 実装 3 単位並列 → 親 integration → 敵対レビュー 2 並列 (max、
  両 NO-GO、must-fix 13 → 採用 10 / P2 維持・裁定パッケージ・nit 据置) → helper v2 + fix 3 単位
  並列 → 変異再走 (MU-J/MU-K 追加) → 焦点再レビュー 1 本 (**GO**、closed 11 / partial 4 =
  裁定どおり / regressed 0)
- **裁定パッケージ (ユーザーへ、D82 (9))**: fresh clone / CI で submodule 未 init のとき
  measurement 統合検査 10 node が可視 skip になる現状を hard-fail 化するか。推奨 = 現状維持
  (可視 skip は既裁定の方針で、hermetic seam 2 件が部分緩和。変えるなら infra 側の裁定)

### 次の一手

1. [T-080] receipt 発行 (ユーザー) → protocol 実凍結 (ユーザー) → 予測封印の実走 wave (AI)。
   変わらず (worklog 2026-07-23 (1))
2. [T-068] R commit で「移行契約により superseded」として確定的に閉じる (D78 (9))。変わらず
3. [T-077] R の design_source 再 pin + generator M 化で閉じる (同上)。変わらず
4. [T-078] S2-4.6 承認 fixture — R commit 時点で閉じる (同上)。変わらず
5. [T-011] floor 実測直前に発火。blocking 前提の残 = 統合 E2E (protocol 凍結後) と lineage
   照合 (oracle 結線 wave 再評価)。D80 (8) の裁定パッケージ 3 件はこの手前で裁定。変わらず
6. [T-066] **消化完了 (本エントリ、D82)。** backlog nit のみ残置 (fake quarantine signature・
   skip 判定重複・素 runner の pytest 依存 — いずれも既存条件)。新規裁定パッケージ 1 件
   (submodule 未 init の可視 skip を hard-fail 化するか — 推奨: 現状維持)
7. [T-067] 部分消化・継続: exact 化の残余は D73 (10) から変わらず
8. [T-001] ruling-B 単独: floor と並行、公式 report 発行前まで。変わらず
9. [T-002] P-A1(a) Stage 1 + P-C3 ([T-006] 同梱): 同上。変わらず
10. [T-009] 延期 (T-083 (a) 処置表): AGENTS.md 追記は 1 cycle 後。変わらず
11. [T-060] 延期 (同): WAL 用語運用の明文化は 1 cycle 後。変わらず
12. [T-010] 延期 (同): B-008 再試験は 1 cycle 後に再評価。変わらず
13. [T-012] 延期 (同): pilot 凍結維持 (本 wave の task-run start も凍結どおり拒否)。変わらず
14. [T-082] 延期 (同): 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-23 (5) — [T-001] ruling-B 消化: oracle session record の issuer/env_tag 照合 (session-only 防御 gate)、pipeline-env を新事実裁定パッケージへ (D83、branch worktree-dev-wave-ruling-ac、計測なし)

/dev-wave 1 回 ([T-001] ruling-B、承認済み単独 wave)。正本 = D83・
`output/insights/2026-07-23_ruling-b-verbatim.md`・同 `-mutation-ledger.json`。
code commit = 59b0e4d (基準 1ce9a2a)。

- **中身**: oracle report consumer (`s8b_oracle_report.py`) に session record (SESSION_STAGE) の
  record-level identity 検査 `_session_identity_issues` を追加。fail-closed で (a) 全 session record の
  issuer=共有定数 `model.S8B_ORACLE_SESSION_ISSUER` ("oracle-session")、(b) campaign 内 env_tag 一貫
  (常時)、(c) manifest.run_contract.env_tag が非空 str のときその値と一致、を検査し違反を
  protocol_violation へ (terminal 有/無の両経路)。driver:605 の literal も同定数へ (WAL bytes 同値)。
  identity 違反時は T-080 observation を unavailable 化 (provenance 漏れ防止)、ただし元 malformed-T080
  issue は保持 (規律3 anti-masking)。docstring に honest な枠組み (正規 producer は踏まない防御 gate・
  pipeline env 非検査・manifest authority は [T-002]・真正性証明でない) を明記
- **変異 matrix**: 5 kill (issuer/manifest-env/consistency/T-080-taint/全SESSION record全称性) + 1
  diagnostic-sensitivity-pin (注入点 = 受理集合不変で status のみ変化ゆえ kill 外) + 1 equivalent
  (driver 定数化)。**全変異で HEAD テスト (99件) は 1 件も検出せず** = 検出力は全て新テストが買った
- **受入 (親環境、repo root)**: 全走 **2842 passed / 18 skipped / 0 failed** (baseline 2832 + 新 8 →
  fix で +2 = 2842、退行 0)。report.py は committed へ内容比較で clean 復元。repo scan invariant 緑
  (逐語凍結後の三軸語 hit 増なし)
- **検証**: brief 前実測 (gate 実在・覆す事実なし) → codex プラン (max) → 敵対相談 2 並列 (max、両
  NO-GO、pipeline-env へ収束) → 裁定 + 変異事前登録 → 実装 A→B (high) → 全走 2840 → 敵対レビュー 2
  並列 (max、両 NO-GO、must-fix 5 採用 + 裁定パッケージ 3) → fix 1 単位 (max) → 全走 2842 → 統合
  commit → 変異本走 → 焦点再レビュー (**GO**、closed 5 / regressed 0)
- **裁定パッケージ (ユーザーへ、D83 (5))**: **PKG-1 (新事実、要裁定)** = pipeline record env が未検査で
  性能証拠 (bench_done.tps) の env 整合性を session-only では保証できない (敵対相談 2 + レビュー 2 が
  独立指摘)。正式裁定は session record のみ (2026-07-20(14)) ゆえ黙って拡張せず新事実付きで戻す。
  設計択一 = (a) 独立 wave で pipeline env 照合 / (b) 射影 env フィルタ / (c) [T-002] 上流固定、推奨=(a)。
  **PKG-2** = manifest 真正性検証は [T-002] 担当 (下記次の一手)。**PKG-3** = 親 brief の「env フィルタを
  変えない」前提は偽 (フィルタ不在) — D83 で訂正

### 消化した ID

- [T-001] **ruling-B 消化 (D83)。** session-only の防御 gate を実装。承認済み単独 wave を実行順どおり消化
- [T-066] 既に D82 で消化 (前エントリ次の一手に残置していたため保存則で明示)

### 次の一手

1. [T-080] receipt 発行 (ユーザー) → protocol 実凍結 (ユーザー) → 予測封印の実走 wave (AI)。変わらず
2. [T-068] R commit で「移行契約により superseded」として確定的に閉じる (D78 (9))。変わらず
3. [T-077] R の design_source 再 pin + generator M 化で閉じる (同上)。変わらず
4. [T-078] S2-4.6 承認 fixture — R commit 時点で閉じる (同上)。変わらず
5. [T-011] floor 実測直前に発火。blocking 前提の残 = 統合 E2E (protocol 凍結後) と lineage 照合。
   D80 (8) の裁定パッケージ 3 件はこの手前で裁定。変わらず
6. [T-067] 部分消化・継続: exact 化の残余は D73 (10) から変わらず
7. [T-002] P-A1(a) Stage 1 + P-C3 ([T-006] 同梱): 公式 report API を VerifiedManifest のみ受理へ。
   **ruling-B の env authority (manifest 宣言 env) の真正性検証はここに依存 (PKG-2)。** 変わらず
8. [T-085] **新規裁定パッケージ (PKG-1、要裁定)**: pipeline record env 未検査で性能証拠の env 整合性が
   session-only では未保証。設計択一 (a)独立 wave で pipeline env 照合 (推奨) / (b)射影 env フィルタ /
   (c)[T-002] 上流固定。正式裁定は session record のみゆえ黙って拡張せず新事実付きで戻す
9. [T-009] 延期 (T-083 (a) 処置表): AGENTS.md 追記は 1 cycle 後。変わらず
10. [T-060] 延期 (同): WAL 用語運用の明文化は 1 cycle 後。変わらず
11. [T-010] 延期 (同): B-008 再試験は 1 cycle 後に再評価。変わらず
12. [T-012] 延期 (同): pilot 凍結維持 (本 wave の task-run start も凍結どおり拒否)。変わらず
13. [T-082] 延期 (同): 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-23 (6) — [T-002] 消化: P-A1(a) Stage 1 + P-C3 + [T-006] — 公式 report API の verified 化 (D84、branch worktree-dev-wave-ruling-ac、計測なし)

/dev-wave 1 回 (引数「早く正規路線に行けるようタスクを選んで」→ 正規路線の AI 手番はユーザー手番
待ちのため、承認済み実行順 (D83 (1)) の第 3 手 = [T-002] を選定)。正本 = D84・
`output/insights/2026-07-23_t002-stage1-verbatim.md`・同 `-mutation-ledger.json`。
code commit = 0c2a573 + 34ce18b (基準 7b6d472)。

- **中身**: (a) Stage 1 — `build_observations` の受理 = {VerifiedManifest, LegacyManifest} exact。
  VerifiedManifest は closure seal + 使用時**全** canonical hash 照合 (self-hash 除外版による
  top-level 注入すり抜けをレビューが live 実証 → fix)。CLI は D65 承認本文どおり active ratified
  freeze 自己解決 → launch_validate → 同一 document/sha を verify_manifest へ (--freeze 引数なし、
  --repo-root seam)。(b) P-C3 — `_GENERATOR_SOURCES` (key→canonical path、5 leaf) を authority に
  exact key set + path 束縛 + 実 hash 検査。非恒真検証 (root A→B) をテスト固定。(c) T-006 —
  宣言レベル ghost 検出 (mapping=block ごと/list=id ごと) + 構造化 manifest_issues (top-level
  additive) + ghost のみ中央 taint + T-080 sibling None (metamorphic 固定)
- **裁定の要点**: 親 brief P2 (--freeze 任意パス) は D65 承認本文の制約 (active ratified +
  launch_validate) を落とした過小実装 (F31 型) — 相談 2 本が独立指摘し訂正。相談 C2-M6 (全 row
  taint が red を隠す) は judge の binary-mismatch 先例 + D68 (4) で反証採用。レビュー R2-4 は
  親裁定 R6 の契約誤り (run-contract issue の early-return 波及は HEAD に無い) を検出 → ghost のみ
  中央適用へ訂正。実装子の raw string campaign_ids 受理拡大 (親プロンプトの曖昧語が誘発) は fix で
  拒否へ復元
- **変異 matrix**: 事前登録 MUT-1..8 (全て受理集合の期待方向 kill、可用性 kill 不成立 — F28 対策で
  MUT-1 compound 化/MUT-2 legacy 降格化/MUT-3 3-key 直接 witness 新設)。最終 commit (34ce18b) で
  8/8 KILLED・witness 全命中・SURVIVED 0。1 巡目のハーネス欠陥 (pytest -q に -rf なし → FAILED 行
  0 で全件誤分類) は erratum として台帳へ
- **受入 (親環境、repo root)**: 全走 **2878 passed / 18 skipped / 0 failed** (baseline 2842 + 36、
  退行 0)。check_ai_provenance 312 件違反なし。三軸語 scan hit 0 (positive control 57)。凍結成果物
  (FROZEN_MANIFEST 8 件・s1/s8b freeze) は 1 byte も不変。発行済み oracle manifest 0 件を機械確認
  済みのため SCHEMA_VERSION 据え置き (D79 (1) 同型)
- **検証**: brief 前実測 → codex プラン (max) → 敵対相談 2 並列 (max、両 NO-GO) → 裁定 v2 + 変異
  事前登録 → 実装 3 直列単位 (high) → 統合・全走 → 敵対レビュー 2 並列 (max、両 NO-GO、must 14)
  → fix (closed 6/6 主張) → 統合 commit → 変異本走 → 焦点再レビュー (NO-GO、closed 4/partial 2/
  regressed 0) → fix2 → 最終全走 + 変異再走 (8/8 KILLED)

### 消化した ID

- [T-002] **P-A1(a) Stage 1 + P-C3 + [T-006] 消化 (D84)。** 承認済み実装 wave を実行順どおり消化。
  Stage 2 (observations→judge→combined の hash 連鎖)・Stage 3 (legacy 廃止) は D65 の段階設計
  どおり未着手のまま残る (各段階は個別にユーザー承認)

### 次の一手

1. [T-080] receipt 発行 (ユーザー) → protocol 実凍結 (ユーザー) → 予測封印の実走 wave (AI)。変わらず
2. [T-068] R commit で「移行契約により superseded」として確定的に閉じる (D78 (9))。変わらず
3. [T-077] R の design_source 再 pin + generator M 化で閉じる (同上)。変わらず
4. [T-078] S2-4.6 承認 fixture — R commit 時点で閉じる (同上)。変わらず
5. [T-011] floor 実測直前に発火。blocking 前提の残 = 統合 E2E (protocol 凍結後) と lineage 照合
   (oracle 結線 wave 再評価)。D80 (8) の裁定パッケージ 3 件はこの手前で裁定。変わらず
6. [T-067] 部分消化・継続: exact 化の残余は D73 (10) から変わらず
7. [T-085] **裁定パッケージ (PKG-1、要裁定)**: pipeline record env 未検査 (D83 (5))。変わらず。
   なお ruling-B の env authority の真正性は本 wave の Stage 1 で manifest 検証必須化まで前進した
   が、manifest 発行主体の連鎖 (Stage 2) は未着手
8. [T-009] 延期 (T-083 (a) 処置表): AGENTS.md 追記は 1 cycle 後。変わらず
9. [T-060] 延期 (同): WAL 用語運用の明文化は 1 cycle 後。変わらず
10. [T-010] 延期 (同): B-008 再試験は 1 cycle 後に再評価。変わらず
11. [T-012] 延期 (同): pilot 凍結維持 (本 wave の task-run start も凍結どおり拒否)。変わらず
12. [T-082] 延期 (同): 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-24 (1) — [T-080] post-R テスト負債 11 件 fix (test-only、branch worktree-dev-wave-ruling-ac、計測なし)

R commit (8bec195) の legacy freeze migration receipt 発効で赤化した `test_s8b_oracle_driver.py`
11 node を test-only で復旧 ([T-067] 由来の real-repo 2 状態 exact 化負債の顕在化)。code commit =
c9d71fd (基準 8bec195、+67/-18 の 1 本のみ、production・凍結成果物・output/・external/ccbench 無変更)。
D 番号なし (test-only、設計判断は insight の発火条件つき残余に記録)。正本 =
`output/insights/2026-07-24_t080-postr-test-debt-fix.md` (§監査後記 込み)・同 `-mutation-ledger.json`・
`2026-07-24_t080-postr-audit-verbatim.md`。

- **消化の経緯**: 別 job の前セッションが impl (c9d71fd、dev-wave codex ループ) を land 後、bg job への
  spoof 注入で停止し `~/tmp/p1.txt` で引き継いだ。本 job (c4f664a6) はユーザー指示で独立検証・監査して
  消化。p1.txt は注入形状 (記憶汚染誘導・main 書換のロンダリング・既成事実埋め込み) と判定しデータ扱い・
  不実行、実 git 状態を独立検証してから着手。「working tree に worklog 新エントリがあるはず」は実態と
  食い違い (未作成) → 本エントリを新規執筆
- **独立実測 (親、cwd=worktree)**: 全走 2878 passed / 18 skipped / 0 failed (受入主張と一致、退行 0)、
  check_ai_provenance 316 件違反なし。docs commit 後に test_s8b_repo_scan_invariant を再走 (F34: 後付け
  記録 bytes の認証)
- **敵対監査 (codex 2 レンズ、gpt-5.6-sol/max/read-only、独立コンテキスト、insight/台帳を非採用で審査)**:
  正しさ境界レンズ・整合/consumer/揮発/F型レンズとも **GO、コード blocker 0**。E3/E4 の reward-hack 疑い
  (G12 子が receipt-free root で claim 競合を回避?) は early-return が verify_receipt() 内に閉じ実 claim
  (`_acquire_g12_claim`→O_EXCL) が走ることのコード追跡で refuted。real 所見 = 記録精度/手順 3 件のみ
  (コード正しさでない): hermetic/決定論的 の語彙過大 (errata、insight §監査後記)、F34 手順ギャップ
  (repo-scan 再走で closure)、E6 inline set の helper 委譲 (minor 残余)
- **変異 matrix (前セッション本走、台帳が正本)**: MUT-1/MUT-2 KILLED・REC-1 kill 集計外・SURVIVED 0。
  帰属は codex B が静的に妥当と確認 (本走の再実行はせず、実測値は環境束縛で非再認証)

### 消化した ID

- [T-080] **post-R テスト負債 11 件 fix 消化 (test-only)。** R 発効で顕在化した負債を解消。[T-080]
  本体 (protocol 実凍結) は未着手のまま (ユーザー手番)

### 次の一手

前エントリ (2026-07-23 (6)) から変わらず — 本 wave は test-only の負債解消で下記いずれも前進なし:

1. [T-080] receipt 発行 → protocol 実凍結 (ユーザー) → 予測封印の実走 (AI)。変わらず
2. [T-068] R commit で「移行契約により superseded」確定 (D78 (9))。変わらず
3. [T-077] R の design_source 再 pin + generator M 化で閉じる。変わらず
4. [T-078] S2-4.6 承認 fixture — R commit 時点で閉じる。変わらず
5. [T-011] floor 実測直前に発火 (統合 E2E + lineage 照合、D80 (8) 裁定 3 件は手前)。変わらず
6. [T-067] 部分消化・継続: exact 化の残余 (D73 (10))。変わらず
7. [T-085] 裁定パッケージ PKG-1: pipeline record env 未検査 (D83 (5))。変わらず
8. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
9. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
10. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
11. [T-012] 延期: pilot 凍結維持。変わらず
12. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-24 (2) — [T-080] selector 予測封印 実走 (科学レーン AI 手番、branch worktree-t080-prediction-seal、計測なし)

/dev-wave 1 回 (科学レーン第 2 手の AI 側工程)。protocol 実凍結 (c8cbd17、ユーザー手番) の後、
selector の**盲検予測を封印**した。機構は wave2 (D79) 配線済みで本 wave は実行 (新規 production
code 変更なし)。正本 = `output/insights/2026-07-24_t080-prediction-seal.md` (材料レポート)・
同 `-verbatim.md` (plan + 相談2 + レビュー2 逐語)・同 `-mutation-ledger.json`。

- **成果**: commit A=7766407 (FROZEN_MANIFEST へ floor_protocol.json pin、件数 8→9、seal 前の
  clean 基準)。commit B=82803d6d (seal + prediction/selector-runs 13 を pin、件数 9→23)。
- **封印**: seal rc=0/status:sealed。pre_oracle_head=7766407 (HEAD 完全一致)、protocol 承認定数
  再導出と HEAD blob 照合・holdout v1 trust root 照合・reload verify・宣言照合まで seal 内通過。
  body_sha256=69c7ad3e…、file sha=5884c83f…。4 agent (opus-4-8/high) + 2 static = 6 行、missing
  ゼロ。盲検 = descriptor + 固定6候補のみ (3 キー固定 + forbidden-key scan)。独立 verify (step3) 緑。
- **検証**: codex 起草プラン → 敵対相談 2 レンズ (正しさ+盲検 / freeze-pin+consumer、P1-P6 裁定) →
  執行 (fail-fast・seal rc=0 gate・commit 機械閉包: staged 集合厳密一致/untracked なし/HEAD blob==
  manifest sha/三集合一致) → 敵対レビュー 2 レンズ。**両レビューが provenance 誤記 (R1/F2) へ独立収束**
  → headless selector を `model=claude-opus-4-8; reasoning=high` へ message-only amend (tree 同一)。
  親ハンク・trust chain・consumer 波及は refuted/closed。
- **変異**: FROZEN_MANIFEST ゲート (sha256 直接 recompute-compare、多層マスクなし) に単層 2 件 —
  MUT-1 (prediction sha 改変)・MUT-2 (件数 23→22) とも KILLED、SURVIVED 0。台帳が正本。
- **受入**: 全走 **2878 passed / 18 skipped / 0 failed** (baseline 一致・回帰ゼロ)。中心 96 passed。
  check_docs / check_codex_agents / check_ai_provenance (320) 緑。repo scan invariant 緑 (F34)。
- **残余**: R2 (manifest exact key-set 未検査) は durable assert 化を [T-086] PKG-2 へ繰延 (本
  commit OID 82803d6d 保持・下流 ratification 前が条件)。R3/R4 = 初回導入捏造・HOME 盲検境界の
  既知残余 (D80 同型)、実走は genuine (session ID 一意・token/cost 実在・実行体 bytes 一致)。

### 消化した ID

- [T-080] **科学レーン第 2 手 完了** — protocol 実凍結 (c8cbd17、ユーザー) + 予測封印
  (82803d6d、AI)。floor 実測はこの後 ([T-011])。

### 次の一手

1. [T-080] 科学レーン第 2 手 **完了** (protocol 実凍結 + 予測封印)。残工程は floor 実測 (下記 5)
2. [T-068] R commit で「移行契約により superseded」確定 (D78 (9))。変わらず
3. [T-077] R の design_source 再 pin + generator M 化で閉じる。変わらず
4. [T-078] S2-4.6 承認 fixture — R commit 時点で閉じる。変わらず
5. [T-011] floor 実測直前に発火 (統合 E2E + lineage 照合)。予測は封印済で floor が予測を変えられ
   ない盲検が成立。**初回導入捏造 (R3) / HOME 盲検境界 (R4) の残余をここで lineage 照合として扱う**。
   Pegasus 単独。変わらず
6. [T-086] **PKG-2 (新規)**: FROZEN_MANIFEST の exact key-set / lineage を durable assert 化
   (同数 path 差し替え検出)。本 commit OID 82803d6d 保持・下流 ratification 前に導入が条件
7. [T-085] 裁定パッケージ PKG-1: pipeline record env 未検査 (D83 (5))。変わらず
8. [T-067] 部分消化・継続: exact 化の残余 (D73 (10))。変わらず
9. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
10. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
11. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
12. [T-012] 延期: pilot 凍結維持 (本 wave の task-run start も凍結どおり拒否)。変わらず
13. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず

## 2026-07-24 (3) — command/reference anti-bloat 実装 (branch skills-anti-bloat、計測なし)

ユーザー依頼 (2026-07-24): dev-wave コマンドの肥大化 (4 日で約 3KB→30KB) を質を落とさず解消し、
二度と肥大化しない恒久機構を設ける。cleanup-branches / rulings も自己改善能力は保ちつつ同型化。
codex を起草・実装・敵対レビューに使い、親 (Claude) が brief・裁定・独立検証・統合を担った。

- **分割**: dev-wave を fail-closed dispatcher へ (29,880→8,420 bytes, 72% 減、最長行 2,314→137 字)。
  段別/条件別手順を `docs/dev-wave/{core,workers,mutation,operations}.md` へ、自己改善規律を
  3 command 共通の `docs/skill-self-improvement.md` へ分離。事故譚は failures の F 番号へポインタ化し、
  各 F の恒久対応欄へ現行実体 back-ref を追記。入口は「読み込み契約」で段・条件ごとに参照節を
  fail-closed dispatch し、義務は逐語強度で保存 (凍結不変集合 INV-01..51 + 落ちた MUST 4 件を復元)。
- **恒久 teeth**: `tools/check_docs.py` に byte・最長行・interface・段別/条件別 dispatch 完全一致・
  孤児見出し・規範 allowlist・`docs/dev-wave/**` 再帰閉包を追加 (肥大と構造孤児化を赤にする)。
  義務本文の lint 化はせず、文言保存は敵対監査・人間レビューの領分と正本に明記 (check_docs の
  既存境界に整合)。予算超過は「可視・可審査な予算 bump commit」に強制する。自己改善の入口
  無条件追記 (肥大化の根) は廃止し、教訓を正本へ routing する契約へ置換。
- **手順**: codex 設計草案 → 敵対レビュー 2 (設計) → 実装 → 敵対レビュー 2 (成果物) → FIX-1〜6 →
  親独立検証。レビューは checker の恒真化リスク (段別 dispatch 潰し・SELF 契約外・孤児逃がし) と
  実義務の弱化 (両層変異裏取りの「必要なら」化) を摘出し、全件 hardening / 復元した。
- **親独立検証**: check_docs 違反なし。受入全走 **311 passed** (repo scan invariant=F34 緑・
  dev_waves supervisor 9 本・check_docs 87〈positive control +15〉・codex_agents)。checker 自体を
  敵対 mutation テスト — 段 6 の S05 継承行削除 → 赤、孤児 H2 追加 → 赤、いずれも sha256 で復元確認。
- 作業ツリーはユーザー規約どおり親が commit し、push はしない (ユーザー審査へ引き渡す)。

### 次の一手

前エントリ (2026-07-24 (2)) の科学レーンから変わらず。本作業は command hygiene の独立実装:

1. [T-080] 科学レーン第 2 手完了。残工程は floor 実測 (下記 5)
2. [T-068] R commit で「移行契約により superseded」確定 (D78 (9))。変わらず
3. [T-077] R の design_source 再 pin + generator M 化で閉じる。変わらず
4. [T-078] S2-4.6 承認 fixture — R commit 時点で閉じる。変わらず
5. [T-011] floor 実測直前に発火 (統合 E2E + lineage 照合)。Pegasus 単独。変わらず
6. [T-086] PKG-2: FROZEN_MANIFEST の exact key-set / lineage durable assert。変わらず
7. [T-085] 裁定パッケージ PKG-1: pipeline record env 未検査 (D83 (5))。変わらず
8. [T-067] 部分消化・継続: exact 化の残余 (D73 (10))。変わらず
9. [T-009] 延期: AGENTS.md 追記は 1 cycle 後。変わらず
10. [T-060] 延期: WAL 用語運用の明文化は 1 cycle 後。変わらず
11. [T-010] 延期: B-008 再試験は 1 cycle 後に再評価。変わらず
12. [T-012] 延期: pilot 凍結維持。変わらず
13. [T-082] 延期: 全 caller 移行は 1 cycle 後。変わらず
