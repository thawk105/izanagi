# 段 1 brief — [T-987] 床値 v2 再測定の束縛を記録基準へ緩める

作成: 2026-08-17 09:05 JST / 親 (manager) / branch `worktree-dev-wave-t987-floor-rebind` / base `699c9cae`

## 確定済みユーザー裁定 (一次資料で照合済み)

`docs/archive/worklog-phase3-0816-595-596.md` の [T-987] 項 (2026-08-16 /rulings 全件 第 3 回):
2026-08-16 の択 (b) (= 現 gitlink で床値を再測定して v2 を作る) は維持し、条件
「再測定は世代移行 wave と同一 chain でのみ実施する」を**記録基準 (再測定の事実と入力を記録するだけ)
へ緩める**。択 (a)「権限束の完成を待つ」は採らない。
旧条件の本文 = 同 `-0816-574.md` / `-0816-579.md` の [T-987] 項。一次控え §3 =
`dev-wave-jobs/rulings-inbox/2026-08-16-flagship-cc-experiment-blockers.md`。

## 裁定の前提を覆す実測 (段 4 で再裁定する)

裁定文が閂として挙げた 2 点は、**裁定時点で既に成立していない**。

1. 「sanctioned な発行経路が存在しない ([T-478] (d))」→ **偽**。AI 再封印 issuer
   `reseal_protocol()` (`orchestrator/campaign/s8b_floor_campaign.py:1067`、core は
   `_reseal_protocol_at_root` 同 :936) が commit `230fc757` (2026-08-16 14:27 JST) で着地済み。
   ただし **production caller はゼロ**で、呼び手は `orchestrator/tests/test_s8b_protocol_builder.py` のみ。
2. 「凍結 protocol の再発行が要る」→ 該当する凍結 pin 検査は既に機械的に**保留 (held)** 済み。
   `orchestrator/campaign/freeze_verification_hold.py:19-21` の `HELD_CHECK_IDS` に
   `s8b-floor.protocol-bytes-expected-pin` と
   `s8b-floor.sealed-protocol-ccbench-pin-current-head` が登録され `HELD = True` (同 :14)。

帰結: 裁定の**結論 (束縛を記録基準へ緩める) は不変**だが、緩める対象は「機械 gate の拒否」ではなく
**台帳に書かれた裁定条件と、それを支える記録の欠落**である可能性が高い。

## scope

- **in**: 床値 v2 再測定を「同一 chain」束縛から外し、代わりに**再測定の事実と入力を記録する経路**を
  実装する。記録の必須性は fail-closed とする (記録が作れないなら再測定を進めない)。
- **in**: 台帳 (worklog fragment / decisions fragment) への裁定反映。
- **out**: 世代移行 ([T-419]) 本体の実装。凍結チェーン検証の保留解除 (ユーザー明示命令のみ)。
  床値 v2 の実走そのもの (計測は本 wave の成果物ではない)。

## 不変条件 (破ったら失格)

- **規律 2**: 正しさゲートを 1 つも緩めない。`HELD_CHECK_IDS` を増やさない。
  既存の受理判定 (anomaly 検出・certified 判定) の受理集合を変えない。
- `freeze_verification_hold.HELD_CHECK_IDS` / `HELD_CHECK_ID_COUNT` / `HELD_CHECK_IDS_SHA256` の
  3 つ組は自己整合 pin であり、編集するなら 3 つ同時 (同 :39-48)。**本 wave では編集しない**。
- 凍結 artifact の bytes を変えない (DW-O09)。新規 chain record は create-only で追加のみ。
- 記録は「通った証拠」に読めてはならない。保留 marker と同じく status を明示する。

## provisional 前提 (親の裁定であり攻撃対象)

- **(P1)** 現時点で床値 v2 再測定を実際に拒否する機械 gate は**存在しない**。束縛は台帳上の
  裁定条件のみ。→ 段 2 の plan 子が全経路を file:line で確定すること。P1 が偽なら scope は
  「その gate を記録基準へ置換する」へ移る。
- **(P2)** 記録の置き場は既存の chain record 機構 (`_CHAIN_RECORD_PATTERNS`
  `orchestrator/campaign/s8b_floor_campaign.py:265-272`、消費は `_assert_freeze_allowlist` 同 :3846 →
  `clean_scan_digest` 同 :3904) を**流用**するのが最小であり、新 namespace を作らない。
- **(P3)** 記録すべき「入力」は最低限 (contract_sha256, ccbench_pin, protocol path+sha256,
  再測定を許した根拠 = 裁定 ID, held check の一覧) で足りる。

## 成果物影響 (DW-G05)

実装しない場合: 床値 v2 が永久に測れず、8b oracle 本走の比較対象 (床値表) が g1 のまま固定される。
その結果、certified 選択の verdict が使う `floor` 表と `scale tolerance`
(`orchestrator/campaign/s8b_verdict.py:954-982` が `freeze.floor_protocol` から引く) が
現 gitlink の実測値と乖離したままになり、faster/no-difference の判定境界が旧世代の値で決まり続ける。

## 成果物の形

1. 記録経路の実装 + テスト (Codex author、D95)。
2. `output/insights/2026-08-17_t987-floor-rebind/` の逐語一式と変異台帳。
3. `docs/spool/` の worklog / decisions fragment (canonical 直編集はしない)。

## 分割方針

段 2 = plan 子 1 本 (read-only)。段 3 = 敵対 2 レンズ (レンズ A: 規律 2 侵食 / 受理集合変化、
レンズ B: 記録の恒真化 = 「書くだけで何も担保しない」欄の作成)。段 5 = 実装子 1 本。
段 6 = 敵対レビュー 2 本 + fix 子。**軽量版にはしない** — 凍結・proof chain 面に触れるため
(DW-C00 の「正しさ防壁に触る」に該当)。
