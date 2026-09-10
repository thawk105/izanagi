# 段 4 裁定 — [T-1218] 床値 再封印の残る裁定 (2026-08-17 01:4x JST)

base = main `3a4c3d43` を wave branch へ ff-only 取り込み済み (開始時 `5a19b8ab` から 10 commit)。
submodule は `--init --recursive` 済み。`s8b_floor_campaign.py` の対象行は merge 後も不動
(742 / 750 / 760 / 892 / 946 / 973)。

## 段 4 直前の裁定 inbox 再走査で見つかった新事実 (wave 開始後に着地)

`2026-08-17-rulings-full4-11rulings.md` (本日 01:09 JST、worklog (611) で land 済み)。

- **[T-1255] 床値 v2 protocol の実凍結 = 「ユーザー手番ではない。AI が実行する」。**
  履行は「`freeze_protocol` の tty 防壁を明示 flag + AI provenance へ置き換えたうえで凍結を実行する」
  実装 wave であり、**別タスク ID の所有**である。本 wave (T-1218) の (P2)「実発行しない」と整合する。
- **[T-419] (3) 「床値 protocol path の shell 層・driver 層の配線 = 実施」。**
  受理集合を変えない配線漏れとして裁定済み。**この配線が resolver 意味論の前提**である。

いずれも T-1218 の裁定 (案 3・機械化なし・FROZEN_MANIFEST 非登録) を覆さない。段 4 を続行する。

## 所見の裁定

| # | レンズ | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|---|
| A-1 | A | contract gate 全削除で **組単位の発行前拒否**まで失われる | **real** | **採用** | 内 |
| A-2 | A | (P1) resolver を consumer 結線より先に入れると admission と実 driver の authority 分裂 | **real** | **採用 (P1 を撤回)** | 内 |
| A-3 | A | (P1) は singleton 受理へ gitlink 前提を混ぜ、未裁定の縮小になる | real | (P1) 撤回により消滅 | — |
| A-4 | A | D460 が resolver を「現行 contract で exact 1 件」「pin を選択条件にしない」と定めており未 supersede | **real** | **採用 (P1 撤回で D460 を触らない)** | 内 |
| A-5 | A | stale-contract × HEAD-pin の交差変異が未登録 | real | (P1) 撤回により消滅 | — |
| A-6 | A | 「同じ commit OID」照合では二重 HEAD 読みを殺せない | real | (P1) 撤回により消滅 | — |
| B-1 | B | 撤去は 2 gate ちょうど。片方だけ残すと即 NO-GO | real | 採用 (plan v2 に固定) | 内 |
| B-2 | B | (P1) の exact 件数を明文化すべき | real | (P1) 撤回により消滅 | — |
| B-3 | B | 実発行と 6 consumer 結線は後続 wave | real | 採用 = (P2) 維持 | 外 ([T-1255] / [T-419](3) / [T-1214]) |
| B-4 | B | D444 は決定 5 だけを限定 supersede、fragment で書く | real | 採用 | 内 |

### A-2 / A-4 の裁定理由 (親の (P1) を自分で撤回する)

1. **既裁定 D460 が正面から禁じている。** D460 の本文は resolver を「現行 env 契約の contract hash に
   一致する record を exact 1 件」と定め、理由節に **「選択条件に ccbench pin を入れてはならない」**
   と明記する。T-1218 の裁定は D444 決定 5 を落としただけで、D460 には触れていない。
   親が独断で非同値な択一へ戻さない (`DW-S04`)。
2. **fail-closed より悪い状態を作る。** 実 driver `tools/pegasus/floor_campaign.sh` は固定 legacy path を
   `--protocol` に渡す。pin 優先 resolver を先に入れると、admission は versioned protocol を authority と
   して PASS し、実測は legacy protocol で走る **authority 分裂**が起こりうる。
   resolver を触らなければ、曖昧時は `count!=1` で fail-closed に止まる。
   「間違ったものを certify する」より「止まる」を選ぶ (規律 2)。
3. **所有が別タスクにある。** 配線は [T-419](3) が「実施」と裁定済み、実発行は [T-1255] の所有。
   resolution 意味論はその atomic な wave で決めるべきもので、本 wave の裁定範囲外。

**この撤回で本 wave に残る既知の残件 (記録する):** contract gate 撤去後、同一 contract の 2 件目が
置かれると `resolve_current_floor_protocol` は `count=2` で fail-closed になり、床値 submit の
admission が止まる。D460 の却下理由が「index が同一 contract hash の 2 件目を上流で既に拒否しており
production では到達不能」としていた分岐が、本 wave で**到達可能に変わる**。
これは事実の記録であって D460 の決定の変更ではない。

## plan v2 (確定形)

1. **index の contract 単位封鎖を撤去** — `_index_protocol_record` の `same_contract` 列挙・分岐・
   error 文 (`:753-762`) を削除する。直前の組単位一意性 (`:748-752`) は**変更しない**。
2. **issuer の contract 単位封鎖を、組単位の発行前拒否へ置換** — `_reseal_protocol_at_root` の
   `occupied_contract_paths` 一式 (`:966-975`) を削除し、代わりに
   **`target_pair` が scan 済み index の key に既出なら、writer を呼ぶ前に拒否**する。
   - error message には既存 record の exact path を載せる。
   - **`_reseal_published_artifact_error` を使ってはならない** (この経路は artifact を作っていない。
     「取り除くまで発行できない」文言は、正規の既存 artifact の削除を誘導する)。
3. **resolver は変更しない。** `resolve_current_floor_protocol` (`:892-911`) は現状のまま。
4. **`FROZEN_MANIFEST` は触らない。** 23 key・held/keep 分割・逐語 assert をすべて不動にする。
   「登録してはならない」逆向き gate も足さない。
5. **記録** — `docs/spool/decisions/` に D444 決定 5 だけの限定 supersede fragment、
   `docs/spool/worklog/` にエントリ、`output/insights/2026-08-17_floor-reseal-rulings/` に一次資料。

### gate 署名 (禁止と、通る正例)

- **禁止 (発行前・writer 呼出し前):**
  `(target_contract.contract_sha256, ccbench_gitlink(HEAD)) ∈ keys(scan_floor_protocol_index_at_commit(HEAD))`
  なら `FloorCampaignError` で拒否し、destination を作らない。
- **通る正例:** legacy anchor が `(C, P_old)` のとき、HEAD gitlink が `P_new != P_old` なら
  `(C, P_new)` は発行できる (= 裁定が採った案 3 の実行形)。

### テスト計画

| nodeid | 種別 | 内容 |
|---|---|---|
| `test_reseal_protocol_public_entry_accepts_same_contract_with_new_pin` | 反転 (正例) | legacy と同一 contract・HEAD pin 違いで発行成功、導出 path、index 2 件、legacy bytes 不変 |
| `test_reseal_protocol_rejects_second_issue_for_same_pair_before_write` | 反転・改名 (負例) | 同一組の 2 件目を **write 前に**拒否。destination 未生成、先行 bytes 不変、message に既存 path |
| `test_reseal_protocol_rejects_pair_already_held_by_legacy_anchor` | 新設 (負例) | HEAD gitlink == legacy pin のとき、versioned path は空いていても拒否。artifact 未生成 |
| `test_floor_protocol_index_accepts_same_contract_with_different_pin` | 反転 (正例) | index が同一 contract・pin 違いの 2 件を受理する |
| `test_floor_protocol_index_includes_legacy_and_rejects_duplicate_pair` | **不変** | 組単位一意性の番人 |
| `test_current_floor_protocol_resolver_rejects_two_current_contract_matches` | 新設 (残件の記録) | 同一 contract 2 件で `count=2` の fail-closed。resolver を勝手に「直す」変更を赤にする |
| 既存 admission 回帰 (`test_campaign.py` の floor admission 群) | **不変** | 今日の受理挙動が 1 bit も変わらないことの回帰 |

## 変異事前登録 (`DW-M01`)

runner scope = `orchestrator/tests/test_s8b_protocol_builder.py` + `orchestrator/tests/test_s8b_floor_contract.py`
(`--force-dispatch`、`-rf`)。期待 node の完全集合は probe 走 (全件 SURVIVED 期待) で観測してから確定する。

| ID | 変異 | 期待 |
|---|---|---|
| M1 | `_index_protocol_record` へ contract 単位拒否を再挿入 | index の正例が赤 |
| M2 | issuer へ contract 単位拒否を再挿入 | issuer の正例が赤 |
| M3 | 組単位一意性 (`:748-752`) を削除 | duplicate-pair test が赤 |
| M4 | 新設の発行前 pair 拒否を削除 | legacy-pair 衝突 test が赤 (artifact が生成されてしまう) |
| M5 | create-only writer を上書き可にする | 同一組 2 件目 test が赤 |
| M6 (過剰拒否の正例) | 発行前 pair 拒否を常時発火にする | 同一 contract・pin 違いの正例が赤 |

M1〜M6 はいずれも、同じ入力を拒否する層が前後に無いことをコードで確認してから登録する。
M4 は「artifact が残る」ことを assert する負例が単一理由で受け止める。

## この wave でやらないこと

- 実 repo での versioned artifact 実発行 ([T-1255] 所有)。
- resolver・shell 層・driver 層・固定 path consumer 6 件の結線 ([T-419](3) / [T-1214] 所有)。
- `FROZEN_MANIFEST` への追加、逆向き gate の新設、pointer namespace 束縛 ([T-1216] 所有)。
- 既存凍結 bytes・held check 2 件・凍結チェーン保留状態の変更。
