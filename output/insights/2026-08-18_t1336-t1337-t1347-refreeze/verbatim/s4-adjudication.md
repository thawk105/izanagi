# 段 4 裁定 — plan v2 (2026-08-18 13:1x JST)

段 2 plan + 段 3 レンズ A / B (両者 NO-GO) を裁定する。裁定 inbox 再走査 (13:09 JST) の結果、
本 wave の 3 裁定に対する更新は無い (13:00 追加の 1 件は T-688 codex 枠で無関係)。

## 0. 親 brief の誤りの訂正 (先に確定する)

| brief の記述 | 裁定 | 根拠 |
|---|---|---|
| 「受理集合を広げない」を不変条件に置いた | **撤回する。** 正しくは「**correctness gate (legacy + S2) を一切変えない**。性能判定の受理集合は裁定により変わる — 消える保証を名指しする」 | A-1 は real。床値比較を別の判定式へ置換する裁定は、定義上どこかで受理側が動く。規律 2 が守るのは正しさの gate であって性能主張の閾値ではない。裁定は「撤去して置換せよ」であり、親が不採用にできない (DW-S04) |
| 「テスト編集不要」 | **撤回する。** 実装面の差分は `orchestrator/tests/test_s8c_preregistration_core.py` の **2 literal** = `FIELD_NAMES` の床値欄名 (56 行) と `field_hash` (585 行) | A-10 / B-7 が real。親が全件検索で確定: 床値欄名の逐語は同 file 1 箇所のみ、`4d082de6…` は同 file 585 行 + 歴史 record g1〜g5 (不変につき触らない) |
| 「8b 文書の編集は凍結鎖を壊さない」 | **言い換える。** 正しくは「**編集前から mismatch (pin `1829af7f…` / 現物 `5fbdd7ef…`) であり、当該検査は HELD のため新たに発火しない。鎖は未検証のまま**」 | A-11 が real。HELD は健全性の証明ではない |
| 生成 command `prepare` | **`prepare-revision` に訂正** | plan / B-2 が real。実測済み |
| (P5) 変異 matrix 免除・(P6) 実装子ゼロ | **改める。** 実装差分が 2 literal 生じるため免除条件を満たさない | DW-S04「実装差分ゼロの wave だけ免除」 |

## 1. 所見の裁定

### 採用 (real・scope 内)

| ID | 裁定 | 反映先 |
|---|---|---|
| A-1 | real。不変条件の方を訂正する (上表) | 8b §10 の「消える保証」節 |
| A-2 | real・blocker。数値欄に**型・範囲・単位・方向**の制約を規範として凍結する。`n` は整数かつ 2 以上、`delta_min` は有限の正、`sd_max` は有限の非負。契約値が不正なら個別 cell の判定不能ではなく**事前登録自体を未発効へ倒す** | 8b §10 判定表 + 8c §4 記入規約 |
| A-3 | real・must-fix。判定入力を**対差の有限な平均と標本 SD だけ**に限定する。共分散・相関・比率の null / 非有限は理由付き診断に留め、成立可否へ伝播させない | 8b §10 |
| A-4 | real・blocker。順位表は `descriptive_only`、公式表は三値 `official_status` を持ち、certified consumer は後者だけを受理する。**消える保証 4 件** (床値超・scale adequacy・oracle unique-best・両構成 eligibility) を名指しする | 8b §10 |
| A-5 | real・blocker。失敗分類は**閉じた集合**とし、信頼側が性能出力を読める前に確定する。primary value が一度封印された attempt は再走不能。全 attempt を報告する | 8b §10 項 8 改訂 |
| A-6 | real・blocker。freeze ごとに**唯一の master registry root** を測定前に固定し、slot は schedule 行・run-start 受領証・raw output hash・terminal status へ一対一に束縛する。第二 registry と出力 bytes の再利用を拒否する | 8b §10 項 8 改訂 + 8c §6 条件 4 |
| A-7 | real・blocker。各観測の時刻・実行環境・実装 identity を保存し、**連続 / 復旧による時間差 / 意図的な過去比較**を区別して主張強度を別ラベルにする。時間差のある結果を無修飾の「同時対測定」と報告しない | 8b §10 (D496 決定 3 改訂と整合) |
| A-8 | real・blocker。T-1347 の規範は「key を落とす」でなく**非干渉性**として書く: `off` の role payload と provider へ送る bytes が、真の holdout を跨いで byte 同一であること。`descriptor_binding.arm_binding_digest_sha256` が真の holdout と arm から導出される事実を親が実測 (`s8c_arm_inputs.py:455-492` → `p3_autonomous_workload_trial.py:740-748,1912`) | 8c §4 の新規範 |
| A-12 | real・must-fix。**epoch 境界**を明記する: g6 は仕様のみを発効させ測定を認可しない。新 decider / 証拠契約 / registry / judge が発効するまでの run は legacy・exploratory であり、後から formal へ昇格・再解釈・混合しない | 8b §10 + 8c §6 |
| B-1 | real・must-fix。§5 の**値と prose は保護 hash に入らない**。よって本 wave は §5 の値セルと説明文を**一切変更しない** (欄名 1 行のみ変更)。plan の「検定 JSON から `reopen_requires` / `reporting` を除く」は**不採用** — 世代 record に記録されない変更になる | 作業手順 |
| B-2 | real。`prepare-revision` + 6 失敗経路の事前確認 | 作業手順 |
| B-4 | 部分採用。条件 4 / 7 の**本文は改訂する**が証拠契約 (`orchestrator/` 配下 = 実装面) は触らない。代わりに「C04 / C07 の証拠契約と評価器は旧意味のままであり、両条件は引き続き非充足。受理集合は 1 bit も広がらない。追随する wave が `DECIDER_VERSION` を v3 へ bump し g7 を発行する」を規範本文へ明記する | 8c §6 |
| B-6 | real。8c が所有する右列と条件 4 / 7 だけを変更し、8b 旧本文は触らない | 作業手順 |
| B-8 | 部分採用。1 世代を維持する (裁定の条件)。`revision_reason` に 3 タスク ID と日付を書き、復元可能性の限界を 8c へ明記する。per-component hash の追加は**後続 wave** (record schema 変更 = 実装面) | 8c + 後続 |
| B-9 | real。全文書を確定してから g6 を 1 度だけ生成し、commit 後に検証する | 作業手順 |
| B-10 | 同意。`DECIDER_VERSION` は **v2 のまま**。判定器・評価器・射影を変更しないため | 作業手順 |

### 部分採用 (限界として記録し、実装は後続)

| ID | 裁定 |
|---|---|
| A-9 / B-3 | real。`ruling_reference` は見出し存在しか検査せず、D496 の本文は改訂前の文言 (決定 3 = campaign 全体の測り直し) のままである。**しかし本 wave 内で解けない** — 本改訂を承認する新 D の番号は land 時の fold が採る一方、`prepare-revision` は生成時に参照を要求する。裁定: `ruling_reference = D496` (**改訂の対象**である決定を指す。承認した決定ではない) とし、`revision_reason` へ 3 タスク ID と裁定日を書き、この限界を 8c §6 へ名指しで残す。裁定本文 digest の束縛は後続 wave |

### 不採用 (refuted または scope 外)

| ID | 裁定と理由 |
|---|---|
| B-5 の勧告部分 | **refuted (勧告として)。** 事実 (pin 不一致・HELD) は real で採用済みだが、勧告「8b v2 再凍結・pin 更新・hold 解除後の再検証を先に完了せよ、できないなら 8b を編集するな」は採らない。(i) mismatch は本 wave の編集**前から**存在し、我々の編集が作るものではない。(ii) 凍結検証の保留は 2026-08-12 のユーザー裁定であり、解除は**ユーザーの明示命令のみ** (`freeze_verification_hold.REASON.release`)。子の勧告で再武装しない。(iii) 8b を編集しないと 3 裁定のうち 2 件が発効しない。限界として記録し、pin 更新は後続へ起票する |
| A-6 / A-5 / A-7 の**実装** | scope 外。本 wave は規則を凍結するのみ。registry・judge・時刻記録の実装は後続 wave |
| A-8 の**実装** | scope 外。`_COMMON_PAYLOAD_KEYS` / `ROLE_PAYLOAD_ALLOWLIST_SHA256` / `_common_payload` / binding digest の改訂は後続 wave |
| B-4 の「条件 4 / 7 を変更しない」案 | 不採用。条件 4 は「8b §9 項 8 (再走なし) に整合している」を要求しており、放置すると事前登録が**上書き済みの規則への整合**を要求し続ける。documented divergence の方が矛盾より小さい |

## 2. plan v2 (確定)

### 成果物と所有

| # | 成果物 | 担当 |
|---|---|---|
| 1 | `docs/phase3-8b-descriptor-design.md` に新規 `## 10. 再凍結 2026-08-18` を**末尾追記** (旧本文は 1 byte も変えない) | 親 (docs) |
| 2 | `docs/phase3-8c-preregistration.md` の §3 右列 2 行・§4 (新規範 1 項 + 標本設計 + 記入規約 3 項)・§5 欄名 1 行・§6 条件 4 / 7 + 現在地段落・§7 起動形 5 項 | 親 (docs) |
| 3 | `orchestrator/tests/test_s8c_preregistration_core.py` の 2 literal | **Codex `role=author` 実装子 (D95)** |
| 4 | `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g6.json` | 親 (`prepare-revision` を 1 回) |
| 5 | spool fragment (worklog 1 / decisions 1) + insight package | 親 (docs) |

### 順序 (B-9 / B-1 に従う)

1. 親が 8b §10 と 8c 改訂を書く (§5 は欄名 1 行のみ。値セルと prose は不変)。
2. 三軸 canonical 綴り 0 件・結合文字 0 件・`git diff --check` を確認。
3. 実装子が test の 2 literal を直す (新 hash は親が実測して渡さず、**子が実 markdown から導出**する)。
4. 親が統合 commit を作る。
5. `prepare-revision` で g6 を 1 度だけ生成 → 別 commit ではなく同一 commit に含めるため、
   **g6 生成 → 全部を 1 commit** の順にする (生成は commit 前、markdown 確定後)。
6. 段 6 敵対レビュー 2 本 → fix → 変異 matrix → 受入。

### 変異事前登録 (DW-M01)

実装差分が 2 literal あるため matrix を免除しない。ただし変異対象は
**「§5 欄名集合の凍結が実際に発火するか」**の 1 実効 gate である。登録する変異:

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| m1 | `test_s8c_preregistration_core.py` `FIELD_NAMES` の新欄名 | 旧床値欄名へ戻す | KILLED (443-444 の実 markdown 照合が赤) |
| m2 | 同 `field_hash` | g5 の旧値 `4d082de6…` へ戻す | KILLED (585 行の corpus 照合が赤) |
| m3 | `docs/phase3-8c-preregistration.md` §5 の新欄名 | 旧床値欄名へ戻す | KILLED (同上・逆方向) |

m1〜m3 はいずれも「前後に同じ入力を拒否する層が無い」ことを確認済み
(欄名逐語の全件検索 = 1 file、hash 逐語の全件検索 = 1 file + 歴史 record)。
m3 は **wave 前の実コードの形**そのものである。

### 不変条件 (確定版)

- correctness gate (legacy + S2) と build 分離を一切変えない。
- 観測済み値の後出し差し替えを許さない (事前登録の目的)。
- §5 の値セルと prose を変更しない。欄名 1 行のみ。
- 三軸 canonical 綴りを 8b / 8c / spool / insight / `revision_reason` のいずれにも書かない。
- 凍結 record は g6 の 1 本だけ。`DECIDER_VERSION` は v2 のまま。
- 8b の旧本文 (§5.2 / §6 / §9) を 1 byte も変えない。
