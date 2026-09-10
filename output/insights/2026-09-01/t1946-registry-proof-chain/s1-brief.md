# 段 1 brief — T-1946 / D1112 択 (b)

## scope (確定)

attempt registry を certified 成果物の proof chain へ**前向きに**束縛する。
新しく作られる floor 成果物 (certified 判定の入力になるもの) の検証が、attempt registry の
identity を実際に読み、突合しなければ通らない状態にする。

**scope 外 (実装しない):**

- 既存 certified 成果物への遡及。既存の受理面 (現行 schema の artifact が今通る条件) は変えない。
- 仮想リスク向けの追加 gate・検査・台帳・一般化。本題の束縛だけを作る。
- registry の書き手側 (launcher / adapter) の機能追加。
- `S8B_RETRYABLE_FAILURE_REASONS` など受理理由集合の変更 (D1113 の射程で別件)。

## 確定済みユーザー裁定

- **T-1946 (2026-08-27 /rulings 全件、推奨どおり):** attempt registry を certified 成果物の
  proof chain へ**束縛する。既存 certified 成果物への遡及はしない。** D1112 の択 (b) と一致。
- **D1049 (ユーザー裁定):** 遡及訂正の枠は開かない。既存は可視のまま保持し残置扱いへ格下げしない。
  本 wave は「基準時点以降」と同じ形に揃える。
- **D1113 (親裁定):** 台帳側の語彙は凍結 4 語を再利用せず台帳専用の閉じた語彙を持つ。
  理由は呼び手が選べず、封じられた session record から機械的に導出する。
  本 wave が値や理由を新たに呼び手引数として受け取る形を採ってはならない。

逐語は `rulings-verbatim.md`。

## 不変条件 (破ってはならない)

1. **規律 2:** 正しさゲートを緩めない。anomaly 検出 variant の即 reject は不変。
   本 wave の変更で既存の拒否が 1 件でも受理へ変わってはならない (v4 既存経路の受理面は不変)。
2. **既存 certified 成果物の受理面は不変。** 現行 `s8b-floor-result/v4` の artifact が今通る条件は
   変えない。遡って新しい要求を課さない。
3. **恒真な保証を作らない。** 「field があれば見る、無ければ黙って通す」形は禁止。
   producer が field を落とすだけで gate が消える設計は不可。束縛は版で条件づけ、
   その版では**無条件に**要求する。
4. **adapter 遮断を破らない。** `orchestrator/campaign/s8b_attempt_registry.py` を直接 import して
   よいのは現状 `s8b_floor_attempt_launcher.py` だけである (同 module docstring が
   "The sole connection owner" と明記、meta-test が AST import を検査)。campaign / admission から
   直接 import する形は採らない。読み取り専用の経路が必要なら、その遮断契約と矛盾しない形を
   plan で明示する。
5. `verify_floor_artifact` の保証境界 docstring (`s8b_floor_stats.py` 冒頭コメントおよび
   関数 docstring) は正本である。境界が変わるなら docstring も同じ commit で改める。
   実装だけ変えて docstring に古い免責を残さない。
6. 新しい呼び手引数で registry identity を受け取り、それを信じるだけの形にしない
   (自己申告は証拠ではない)。live 経路は共有 filesystem の現在状態を読む。

## 変更面 — 実アンカー表 (行番号は base 11b44e2d1 時点)

| # | file:line | 現状 | 束縛での役割 |
|---|---|---|---|
| A1 | `orchestrator/campaign/s8b_floor_stats.py:682` | `verify_floor_artifact` — pure projection verifier。docstring が「raw session の真正性 (append-only journal・attempt registry・schedule 突合) は保証しない」と明記 | 版条件付きで registry 束縛を要求する主戦場 (ただし pure なので registry 実体は読めない) |
| A2 | `orchestrator/campaign/s8b_floor_stats.py:1036` | `verify_floor_artifact_with_live_admission` — live inspector を自ら呼ぶ公開入口。現状は holdout admission inspector だけ | registry 実体を読んで突合する自然な位置 |
| A3 | `orchestrator/campaign/s8b_floor_stats.py:412` | 保証境界 docstring 正本コメント | 境界の記述を実装に合わせる |
| A4 | `orchestrator/campaign/s8b_floor_contract.py:34` | `RESULT_SCHEMA = "s8b-floor-result/v4"` | 版で前向き条件を作るならここ |
| A5 | `orchestrator/campaign/s8b_floor_contract.py:81` | `_RESULT_KEYS` (24 key の exact 集合)。`attempts`、`holdout_admission` を含む | 新 field を足すならここ |
| A6 | `orchestrator/campaign/s8b_floor_contract.py:157` | `result_keys_for_mode(mode, perf_preflight=)` — mode 条件付き exact key 集合 | 版条件を足す位置 |
| A7 | `orchestrator/campaign/s8b_floor_contract.py:66` | `_FLOOR_HOLDOUT_ADMISSION_KEYS` — 既に `attempt_row_count` / `ledger_projection_sha256` を持つ。ただしこれは **holdout admission 台帳**の射影であり attempt registry ではない | 混同禁止。二つの台帳を区別する |
| A8 | `orchestrator/campaign/s8b_attempt_registry.py:485` | `registry_path(repo_root, *, freeze_sha256)` — 受理される唯一の registry path | 実体の所在 |
| A9 | `orchestrator/campaign/s8b_attempt_registry.py:1086` | `read_attempt_registry(repo_root, *, profile, binding)` — lock 内で replay して `RegistryRows` を返す | 読み取り API |
| A10 | `orchestrator/campaign/attempt_registry_core.py:253` | `previous_event_sha256(rows)` — 末尾 chained row の `event_sha256` を返す。空なら zero sha。**これが D1112 の言う chain head** | pin する値の候補 |
| A11 | `orchestrator/campaign/attempt_registry_core.py:239` | `chained_event_row` / `_CHAIN_KEYS` (`event_index` / `previous_event_sha256` / `event_sha256`) | chain の実体 |
| A12 | `orchestrator/campaign/s8b_holdout_admission.py:5687` | `inspect_floor_holdout_admission_evidence` — 共有 admission filesystem の現在状態を検査。保証境界 docstring 5694-5699 | 束縛を足すもう一つの候補位置 |
| A13 | `orchestrator/campaign/s8b_holdout_admission.py:6395` | inspector が組む receipt (`ledger_projection_sha256` 等) | registry identity を足すならここ |
| A14 | `orchestrator/campaign/s8b_ratified_freeze.py:3262` | ratified verifier が `verify_floor_artifact_with_live_admission` を呼ぶ | certified 経路の呼び手 |
| A15 | `orchestrator/campaign/s8b_holdout_freeze.py:1620` | holdout freeze 側の呼び手 | 同上 |
| A16 | `orchestrator/campaign/s8b_floor_campaign.py:6455` | campaign 側の自己検査呼び出し | producer 側の呼び手 |
| A17 | `orchestrator/campaign/s8b_floor_campaign.py:6605-6621` | producer が result dict を組む位置 (`"attempts": attempts` を含む) | 新 field の producer |
| A18 | `orchestrator/campaign/s8b_floor_attempt_launcher.py` | adapter の唯一の接続所有者 | 遮断契約の相手 |

## pin 閉包 (DW-O09 実測)

- `RESULT_SCHEMA` 文字列 `s8b-floor-result/v4` の pin: `s8b_floor_contract.py:34` (定義)、
  `test_s8b_floor_contract.py:180` (exact 一致 assert)、`test_s8b_floor_stats.py:596` (fixture)、
  `test_s8b_floor_stats.py:1325` (エラー文言の exact 一致)。
- `_RESULT_KEYS` の pin: `test_s8b_floor_contract.py:367` (`base = s8b_floor_contract._RESULT_KEYS`)。
- `verify_floor_artifact` の pin: `test_official_perf_closure.py:197,199,329` — file path・関数名・
  記号名を key にした閉包 pin。**関数名や module path を変えると赤になる。**
- `output/` 下の凍結 artifact bytes: 本 wave は既存 artifact を書き換えないので producer の
  出力 bytes 変更は「これから作る成果物」にだけ及ぶ。既存凍結 bytes は不変 (DW-O10 は
  新規出力のみ)。plan は producer が書く全ファイル種を列挙して確認すること。

## 成果物の形

- `orchestrator/campaign/` の実装差分 (上記アンカーの範囲)。
- `orchestrator/tests/` の正例・負例。負例は**束縛が実際に発火する**ことを示す:
  registry を削除した / chain head を改竄した / registry が別 freeze のものである状態で
  certified 検証が**落ちる**こと。正例は正常な registry で通ること。
- 既存 v4 artifact が今までどおり通る回帰テスト (遡及していないことの正例)。
- 変異事前登録 (段 4)。

## 分割方針

- 段 2: codex `plan` (read-only) 1 本。file:line 粒度で 2 案以上を比較し推奨を出す。
- 段 3: codex `consult` 2 本 (lane=sol / lane=luna)。レンズを分ける
  — (i) 恒真化・迂回可能性・遡及漏れ、(ii) 遮断契約違反・pin 閉包漏れ・既存受理面の破壊。
- 段 5: codex `author` 1 本 (実装面は親が直接編集しない)。
- 段 6: codex `review` 2 本 + fix、変異 matrix、受入。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1)** 前向き条件は **result schema の版**で作るのが最良である
  (`s8b-floor-result/v5` を新設し、v5 では registry 束縛を無条件に要求、v4 は現行規則のまま受理)。
  代案: 基準時点 (campaign_run_id / freeze_sha256 の allowlist、日時) で条件づける。
  親の provisional 裁定は版。理由は機械的で、呼び手が選べず、D1049 の「基準時点以降」と同型になるから。
- **(P2)** pin する値は `previous_event_sha256(rows)` が返す **chain head** で足りる。
  代案: chain head + `event_index` + genesis の start event hash + 台帳 identity (freeze_sha256) の組。
  親の provisional 裁定は「chain head 単独では不足で、freeze binding と row 数まで含む」。
  chain head だけだと空 registry (zero sha) と削除済み registry が区別できない恐れがある。
- **(P3)** 束縛の検査位置は `verify_floor_artifact_with_live_admission` (A2) である。
  `verify_floor_artifact` (A1) は pure projection なので実体を読めない。
  代案: `inspect_floor_holdout_admission_evidence` (A12) の receipt に registry identity を足す。
  親の provisional 裁定は A2 + A12 の併用 (A12 が実体を読み、A2 が artifact 自己申告と突合)。
- **(P4)** adapter 遮断契約 (不変条件 4) は、admission 側から registry を読むことを禁じている。
  親の provisional 裁定は「遮断は *書き込み* 経路の所有権であって読み取りではない」。
  **これは実測で確かめる必要がある** — plan は該当 meta-test の本文を読んで、
  読み取り import が赤になるかどうかを file:line で報告すること。赤になるなら設計を変える。
- **(P5)** 既存の certified 成果物に対する historical reverify 経路は v4 のまま通る。
  plan は historical reverify の実経路を特定し、v5 導入がそこを壊さないことを file:line で示すこと。

## 成果物影響 (DW-G05)

放置すると: registry を削除・不正化した状態でも certified 検証が通る。
「測り直しを追跡している」と読める proof chain が、実際には台帳の欠落を許す。
本 wave 後は、基準時点以降に作られた certified 選択結果は、その台帳が実在し chain head が
一致しなければ受理されない。既存の certified 選択の値・受理集合・参照は変わらない。
