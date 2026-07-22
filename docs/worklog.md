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
