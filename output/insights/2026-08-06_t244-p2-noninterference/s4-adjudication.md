# 段 4 裁定 — [T-244] P2 U-1〜U-3 実装 wave

基準 tip = `bf6128b6` (local main を段 3 後に ff-only 取り込み、provenance 全 1459 commit 違反ゼロ)。
段 3 の敵対 2 レンズは**独立に NO-GO** を返した (レンズ A = BLOCKER 4 / MAJOR 4 / MINOR 1 / NIT 1、
レンズ B = BLOCKER 4 / MAJOR 7)。親は全件を real/refuted に裁定した。

## 決定 (1): 実装する。ただし scope を縮小し、名乗りの上限を先に固定する。

遷移は `4→5→6→7→8→9`。段 3 の所見は**プラン v1 を否定したが、実装可能な中核を否定していない**。
中核 = 「critic へ届く候補識別子チャネルを実経路で塞ぎ、宣言済み declassification を除いた
sink 等価性を実 renderer 上の関係テストで固定する」。これは恒真にならず、現行 baseline で赤くなる。

**U-1 の解釈について、停止せず実装可能な読みを採る。** 両レンズは「origin scope の不透明 ID」を
「reflux origin ledger の `origin_id` へ束縛した ID」と読み、authority が `origins: []` (U-10 未決) の
ため実装不能だと指摘した。この事実は裁定より前の worklog (241) に既記録であり、`DW-S04` が停止を
許す「裁定時点で未見の新事実」に当たらない。よって親は
**「候補の実 ID を復元できない、1 origin (= cap=1 の 1 campaign) の中でだけ意味を持つ不透明 ID」**
という読みで実装し、`origin_id` 束縛版との差を決定 (3) の名乗り上限と裁定パッケージ V-1 で明示する。
どちらの読みでも pseudonymization 層は必要なので、実装が無駄になる経路はない。

## 決定 (2): 所見の裁定台帳 (19 件)

| # | 所見 | 裁定 |
|---|---|---|
| A-B1 / B-BL3 | baseline-red が到達不能 fixture と fake renderer による人工物 | **real・採用**・scope 内 → 必須是正 1 |
| A-B2 | `P` に S 依存の観測結果を入れており非干渉条件が循環 | **real・採用**・scope 内 → 必須是正 2 |
| A-B3 / B-BL1 | campaign-local ordinal は裁定の origin-scope ID ではない。`variant` の型が二義化 | **real・採用**。停止理由にはせず → 決定 (1)(3) と V-1、必須是正 3 (key 改名) |
| A-B4 | `(campaign_id, label)` の逆引きが一意でない | **real・採用**・scope 内 → 必須是正 4 (逆引きの正本を限定し、非一意なキーを逆引きと名乗らない) |
| A-B5 / B-BL4 | declassification 会計が省略可能かつ自己申告 (fail-open) | **real**。v3 schema bump は **scope 外** → 名乗り縮小 + V-2 |
| B-BL2 | projector opt-in のため現役 critic consumer 7 箇所が生 ID のまま | **real・採用**・scope 内 → 必須是正 5 (projector 必須化と全 consumer 移行) |
| B-MA1 | account が開示 payload を独立再検証できない | **real**、scope 外 → V-2、名乗り縮小 |
| B-MA2 | U-3 の test-only 二値は artifact identity に接続されない | **real・採用** → 必須是正 6 (production 定数化) + V-3 |
| B-MA3 | liveness `extra` は開集合で、2 key の射影だけでは閉じない | **real**。現描画 2 key は射影 (scope 内)、exact schema 化は scope 外 → V-4 |
| B-MA4 | 「候補集合不変」は WAL に限る。report/journal/receipt へ波及 | **real・採用** → 影響表を分離記述 |
| B-MA5 | mutant 12 件に複合変異・dormant・test-only が混在 | **real・採用** → 決定 (4) で原子化・分類 |
| B-MA6 | 所有分割が production 正本 `p3_s4_loop.py` を落としている | **real・採用** → 決定 (5) で所有改訂 |
| B-MA7 | 前 wave の real 所見を閉じた扱いにできない | **real・採用** → 決定 (3) の close matrix |
| A-M1 | build 経路は未実測。「毎世代 5 bit」は過大 | **real・採用** → 主張から build 経路を除外 |
| A-M2 | digest 再描画が tag / reflux ablation の同値性を固定していない | **real・採用**・scope 内 → 必須是正 7 |
| A-M3 | 「凍結 pin なし」から「provenance 不変」は導けない | **real・採用** → 影響表を分離 |
| A-M4 | 名乗りが実装内容を超えている | **real・採用** → 決定 (3) |
| A-m1 | 「既存被覆は key-set だけ」は事実でない | **real・採用** → 純増を「S-dependency の関係 oracle がない」へ縮小 |
| A-n1 | U-3 golden hash の preimage が byte 規範として曖昧 | **real・採用**・scope 内 → 必須是正 8 |

親の provisional 裁定: **(P1) 縮小して採用** (campaign-local pseudonym としてのみ成立、origin 束縛は未了)。
**(P2) 採用** (test 層 oracle、production runtime gate 化は却下)。
**(P3) 縮小して採用** (production 定数として置き、artifact 搭載はしない)。
**(P4) 採用**、ただし棚卸しは親が不完全だった (liveness `extra` 2 key と `digest.py:683` の
verify-abort を落とし、`683` を screening と誤記していた。両レンズが是正)。

## 決定 (3): 名乗りの上限と close matrix

**名乗ってよい:**
- 8c critic recipient 境界の **campaign-local pseudonymization** (cap=1)。
- 宣言済み declassification `D` を除いた **critic sink 等価性の regression 検査** (no-build 経路)。
- auditor 開示の **自己申告 annotation** (policy 定数 + sunset 条件 + producer test)。
- **IR emitter/golden 変更検出 ID** (production 定数)。

**名乗らない:** origin-scope ID、non-interference / indistinguishability、P2 の充足・部分充足、
cap-lift、build 経路の閉鎖、proof chain 保全、U-1 / U-2 / U-3 の「完了」。
前 wave の real 所見のうち A-B1・A-B2・A-B3・A-B4・B-B1・B-B2・B-B3・A-M1・A-M2・B-M1・B-M2 は
**open のまま残す** (close matrix を段 7 の記録に所見 ID 単位で書く)。

## 決定 (4): 変異事前登録 (`DW-M01`)

実装前に次を登録する。すべて**単一 field の原子変異**とし、複合変異を作らない。
実装子は各変異の置換 anchor が一意であることを報告する (`DW-M04`)。

| # | 対象 | 変異 (old→new) | 種別 |
|---|---|---|---|
| M1 | 8c critic payload の候補 label | pseudonym → raw variant | 受理集合/sink |
| M2 | verify-red renderer の `variant` | 射影 → raw | sink |
| M3 | verify-red renderer の `src_token` | 射影 → raw | sink |
| M4 | liveness renderer の `variant` | 射影 → raw | sink |
| M5 | liveness renderer の `src_token` | 射影 → raw | sink |
| M6 | liveness `extra.build_attempt_id` | 射影 → raw | sink |
| M7 | liveness `extra.build_admission_receipt_sha256` | 射影 → raw | sink |
| M8 | diff-quarantine renderer の `variant` | 射影 → raw | sink |
| M9 | diff-quarantine renderer の `src_token` | 射影 → raw | sink |
| M10 | verify-abort renderer の `variant` | 射影 → raw | sink |
| M11 | projector 引数 | 必須 → 既定 raw の opt-in | 受理集合 |
| M12 | digest 再描画の `tag` / `reflux` | 明示引き回し → 既定値 | 等価性 |
| M13 | 未知 ID の拒否規則 | 未知だけ拒否 → 全 ID 拒否 | **正例** (過剰拒否検出) |
| M14 | U-2 policy の `forbidden_json_pointers` | `["/diff_digest"]` → `[]` | diagnostic pin |
| M15 | U-3 composite identity | golden 側 hash を落とす | 受理集合 |

M14 は現 sink bytes を変えないため `DW-M08` の **diagnostic sensitivity pin** として別枠に数える。
M13 は正例であり、kill = 正常経路が赤くなることの検出である。

## 決定 (5): 所有分割 (B-MA6 の是正)

- **単位 A (critic 描画層)**: `orchestrator/critic/digest.py`, `orchestrator/campaign/p3_s4_loop.py`,
  `p3_s4_loop_sort.py`, `p3_s4_loop_trigger_gating.py`, `p3_s4_red.py`,
  `orchestrator/tests/test_critic.py`, `orchestrator/tests/test_p3_s4_loop.py`
- **単位 C (IR identity)**: `orchestrator/campaign/reflux_ir.py`, `orchestrator/tests/test_reflux_ir.py`
- **単位 B (8c supervisor)**: `orchestrator/campaign/p3_autonomous_workload_trial.py`,
  `orchestrator/tests/test_p3_autonomous_workload_trial.py` — A の API に依存するため **A の完了後**に
  A の所有パス限定 patch を展開してから投入する。

A と C を並列、B を後続とする。

## 決定 (6): 必須是正 8 件 (実装子への指示に落とす)

1. 関係テストは**実 admitted WAL と実 `make_critic_digest` / `render_rejections`** を通す。
   fake renderer と到達不能 fixture を使わない。
2. `P` は **S より前に決まる入力**に限定する。harness outcome / metrics / rejection の class・件数は
   `P` に入れず、**明示的 declassification `D(S, trace)`** として宣言し、sink bytes は `D` を除いて比較する。
3. critic payload の候補欄は `variant` を流用せず**別 key へ改名**する (二義化回避)。既存 key-set
   境界テストを同一変更単位で追随させる。
4. 逆引きは `(campaign_id, label)` を正本と名乗らない。同一 generation record 内の raw harness 値を
   正本とし、それ以外の逆引き経路を主張しない。
5. `render_rejections` / critic 向け digest API は **projector を必須引数**にし、生描画が要る診断経路は
   明示的な raw 指定を渡させる。production の全 critic consumer (7 箇所) を移行する。
6. U-3 の複合 identity は **production 定数**として置く。production は golden module を import しない
   (既存独立性検査を壊さない)。
7. digest 再描画は `tag` と `reflux` を明示的に引き回し、**on / off 双方**で「識別子箇所以外は
   byte-for-byte 同一」を検査する。
8. U-3 の golden 側 preimage は **byte 規範**を固定する (開始・終了 offset、indent、末尾 comma、改行の
   包含可否、preimage length)。期待値を同じ test 内で観測値から組み立てない。

## 決定 (7): 裁定パッケージ (ユーザー判断待ち、本 wave では実装しない)

| # | 択一 | 親の推奨 |
|---|---|---|
| V-1 | **U-1 の「origin scope の不透明 ID」の解釈。** (a) 1 campaign 内でだけ意味を持つ不透明 ID で充足とする、(b) reflux origin authority の `origin_id` へ束縛する形を正とし U-10 解決後に再実装する | **(a) を暫定充足とし、U-10 解決後に (b) へ昇格**。本 wave は (a) を実装し、U-1 完了は名乗らない |
| V-2 | **declassification account の fail-open を閉じるか。** (i) payload / report を v3 へ上げ auditor attempt で account を必須化し、canonical payload bytes へ cross-bind する、(ii) 自己申告 annotation のまま残す | **(i)**。ただし report schema・trial registry・acceptance receipt hash へ波及するため独立 wave |
| V-3 | **U-3 の複合 identity を artifact へ搭載するか** (trigger binding record / origin manifest)。搭載すると WAL 受理集合と既存 record の exact key 集合が変わる | **搭載する**。ただし後方互換の設計が要るため独立 wave |
| V-4 | **liveness `extra` の開集合を critic recipient schema で閉じるか。** 現状は producer が任意 key を merge でき、renderer が全値を描画する | **閉じる (未知 key 拒否)**。本 wave の射程外の残余として明記する |
