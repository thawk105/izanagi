# 段 4 裁定 (親) — [T-1505] 床値救出 attempt registry

段 2 plan と段 3 敵対 2 レンズ (sol=正しさ境界 / luna=整合性・実効性) の全所見を裁定する。
親は所見をコードで独立検算してから real/refuted を決めた。検算した file:line を各項に書く。

## 0. 結論 (先に書く)

**本 wave は「共通 core の抽出 + 8c 互換 facade + 8b domain profile の生死確認」までを実装し、
8b の production 配線・trusted launcher・再抽選規則は実装しない。** 実装しない 3 点は
いずれも**ユーザー裁定を要する**ことが 2 レンズと親の検算で確定したためである。
command 自身が「ユーザー裁定が要ると判明したらそこで返す」と指示しており、これに従う。

**D672 は覆らない。** D672 が閉じたのは reuse 形状 (共通 core + 8c facade + 8b adapter) であり、
本 wave の所見はその形状を否定せず、実装条件を狭めるだけである。

## 1. 裁定表

凡例: real=コードで裏取り済み / refuted=誤り / 採用=本 wave で実装 / 送出=裁定パッケージへ返す。

| # | レンズ | 所見 | 判定 | 採否 | 親の検算 |
|---|---|---|---|---|---|
| A1 | sol C1 | `record_attempt_terminal` の明示 `failure_reason` が分類受領証の理由を上書きでき、echo は忠実に記録されるが `failure_reason == echo` は検査されない。値を見た後に `retryable-failure` + `preempted` を付けて次 slot を取れる | **real** | 採用 (profile 化) | `trial_registry.py:3385-3389` (上書き)、`:2504-2511` (echo 一致のみ検査)、`:2253-2262` (null matrix は集合所属のみ)、`:2367-2382` (observation 無しなら次 slot 可) |
| A2 | luna C1 | crash は分類器ごと殺すため、**別 process が死んだ attempt を閉じる経路が原理的に無い**。terminal は分類を実行した pid/tid が要る | **real (最重要)** | 送出 + core 設計に穴を開ける | `trial_registry.py:3366-3370` (owner = `(os.getpid(), threading.get_ident())`)、`:2367-2382` |
| A3 | luna C2 | `session-start` (journal) と registry `start` の crash cut が未設計。片側だけ残る cut で現行 resume が session を永久 skip する | **real** | 送出 | `s8b_floor_campaign.py:5036-5039` (forward-only)、`:5128` 系の started_seqs |
| A4 | luna C3 / sol M6 | 凍結 budget は cell 全体 (`n_sessions + retry_slots_per_cell`) だが、提案 core の集約軸は反復込み `series_key` しかない。素直に実装すると受理 retry 数が `n_sessions` 倍になる | **real** | 採用 (core に `budget_key` を持たせる) | `s8b_holdout_admission.py:1133-1141`, `:1291-1296` (`attempts = n_sessions + retry_slots`) |
| A5 | sol C2 | 「後続 attempt は診断専用」が集計へ接続されていない。`cell_stats()` は全 valid session を数えるので、成功した診断 attempt が欠測反復を置換する | **real** | 送出 | `s8b_floor_stats.py:273-295` (`valid = ... and n_valid == n_sessions`)、`s8b_floor_campaign.py:5381-5391` |
| A6 | sol H3 / luna H5 | §10.5 の「単一 registry の唯一性を全履歴で担保」は既存 shared root では満たせない (削除・同一 bytes 再構成を検出できないとコード自身が明記) | **real** | 送出 (満たしたと**書かない**) | `s8b_holdout_admission.py:4-11`, `:4054-4058` |
| A7 | sol H4 | C01–C12 の要求列挙が不完全かつ一部誤読。C03 の存在検査が使う `_functions()` は**再束縛を除外しない**別関数である | **real** | 採用 (検査設計を訂正) | `s8c_preregistration_evidence.py:293-298` (module 版、除外なし) vs `:834-847` (explorer 版、除外あり)。C03 は前者を使う (`:1624`) |
| A8 | sol H4 | `create_attempt_registry_genesis` は required 関数だが到達性検査には含まれないため、後段再束縛で乗っ取れる | **real** | 採用 (実装で禁止、変異で登録) | `s8c_preregistration_evidence.py:1624-1641`, `:1695-1708`, `:1731-1741` |
| A9 | sol H4 | `test_reflux_formal_consumer.py` が `trial_registry.py` を含む**固定 14 file** の source scan を pin する。新 core はその集合外になる | **real** | 採用 (同 commit で追随) | `orchestrator/tests/test_reflux_formal_consumer.py:22-37` |
| A10 | sol H5 | 親 brief の「救出後の床値が**楽観側へ**偏る」は一般化不能。floor は分散と stock median の max なので方向はデータ依存。保証できるのは「estimand が変わり得る」まで | **real (親の誤り)** | 採用 (brief 訂正) | `s8b_floor_stats.py:325-405` |
| A11 | luna M9 / sol M7 | 親 brief のアンカー誤り: attempt registry の既定 path は `output/s8c-trial-registry/...` ではなく `output/s8c-preregistration/attempt-registry.jsonl`。C03 の範囲は `:1613-1778` (親は `:1730` で切っていた) | **real (親の誤り)** | 採用 (訂正済み) | `trial_registry.py:57-59`、`s8c_preregistration_evidence.py:1748-1778` |
| A12 | luna M9 | 「pilot wave と編集面の重なりなし」は `git diff --name-only main...` だけからは導けない (未 commit・未追跡・semantic conflict を見ない) | **real (親の測定法の弱さ)** | 採用 (測定法を強化) | 下記 §4 |
| A13 | luna H6 | consumer (`assemble_result`)・resume checker・stats・refreeze 判定・docs が取り残されている。registry だけ作れば「実装したふり」になる | **real** | 送出 (本 wave は production 配線をしないので発生しない) | `s8b_floor_campaign.py:5679-5703`, `:7094`、`s8b_holdout_admission.py:4355` |
| A14 | luna H4 | production `measure_point()` は launch/wait/parse 一体の API であり、`s8b_floor_campaign.py` の編集だけでは二相化できない | **real** | 送出 | `s8b_floor_campaign.py:6790-6817` |
| A15 | 親 | 欠測反復は cell を丸ごと失格にする。段 2 の「安全策」は D496 決定 3 の「行き止まりを作らない」に抵触する | **real** | 送出 | `s8b_floor_stats.py:288` |
| A16 | 親 | rep 単位の耐久記録が無い (session 終了時に初めて journal へ落ちる) ため、段 2 の checkpoint continuation 案は現行実装では不可能 | **real** | 送出 | `s8b_floor_campaign.py:5366` |
| A17 | 親 | 床値 campaign はまだ 1 度も観測を開始していない (claim 0 件・consumption 0 件)。したがって §10.5 の事前割当は**今ならまだ正当に成立する** | **real** | 記録 | 共有 root 実測 (2026-08-23): claims 24 = n_pilot 12 + oracle_driver 12、attempt-ledger 132 行すべて n_pilot |
| A18 | 親 | 未知の event 種別は拒否される。したがって core に「引き取り (recovery)」event を足しても、8b profile にだけ許可すれば **8c の受理集合は証明可能に不変** | **real (打開策)** | 採用 (設計に反映、実装は profile 表まで) | `trial_registry.py:2090-2106` (`{label}.event is unknown`) |

**refuted は無い。** 2 レンズの所見はすべて real だった。

## 2. 本 wave で実装するもの (plan v2)

### (V1) 共通 core の抽出 — `orchestrator/campaign/attempt_registry_core.py` (新設)

- 対象は `trial_registry.py:1818-3431` のドメイン非依存部分だけ。
  `:3432-3557` の 8c 固有 acceptance は移さない。
- ドメイン束縛は呼び手が注入する: slot codec、binding codec、schema profile、
  registry layout (path)、retryable 理由集合、**budget key** (A4)、**遷移 policy**。
- **遷移 policy には A1 の穴を閉じる項を必ず持たせる**
  (`require_terminal_reason_equals_classification`)。
  **8c profile は今日の挙動 (False) を保ち、8b profile は True にする。**
  → 8c の受理集合は不変のまま、8b は規律 2 の穴を継承しない。
- **A18 の recovery event は本 wave では event 表の拡張点だけを用意し、実装しない**
  (DW-G04: 発火条件を満たす既存 artifact path が無いため設計メモに留める)。

### (V2) `trial_registry.py` の互換 facade 化

- C03 が要求する 13 関数は**実 `def`** として残す。再 export にしない。
- `assert_trial_registry_acceptance` の本体は動かさない (C02/C08/C09/C10 が壊れる)。
- **A8 を踏まえ、facade 6 関数のいずれについても top-level 再束縛を書かない。**
- 8c の受理集合・拒否理由・例外文言・event/receipt bytes を 1 bit も変えない。

### (V3) 8b domain profile の生死確認 (DW-G01 の最安確認)

- 8b の profile を**データとして**定義する (slot 識別・schema・budget key・閉じた理由集合)。
- core を 8b profile で駆動する**状態機械テストだけ**を書く。
- **`s8b_*.py` の production から新 core を import も call もしない。**
  → 途中状態が production から到達不能であることを保つ (luna の切断点 1 と同じ)。

### (V4) 不変の機械証明

- C01–C12 の `(id, status, reason_code)` snapshot 同値。
- 既存 event/receipt canonical bytes の golden 同値。
- 例外文言の同値。
- A9 の固定 14 file 集合への追随。

## 3. 実装しないもの (裁定パッケージへ送出)

| 送出項 | なぜ本 wave で決められないか |
|---|---|
| **R-a. 死んだ process の attempt を誰がどう引き取るか (A2)** | terminal の owner 束縛を緩めるか、新しい recovery event を作るかは**受理集合の変更**であり、§10.5 にも規定が無い。設計正本の追記が要る |
| **R-b. 観測開始後の crash をどう扱うか (A5/A15/A16)** | 「永久欠測 (= その cell を失格)」と「次 attempt を主値へ昇格 (= estimand の変更)」の択一。前者は D496 決定 3 の行き止まり禁止に抵触し、後者は床値の意味を変える。**どちらもユーザー裁定** |
| **R-c. 8b の閉じた再走理由集合と、その正本証拠源 (A14)** | 受理集合を変えるため author 判断で確定してはならない。scheduler accounting を読む authority が未設計 |
| **R-d. §10.5「単一 registry の全履歴唯一性」をどう満たすか (A6)** | 既存 shared root では満たせない。Git content commit への pin 等、別機構が要る |
| **R-e. journal / registry / marker / attempt-ledger の権威分担と crash cut (A3/A13)** | 4 台帳の conflict truth table と recovery owner が未定義 |

## 4. 親の訂正 (自分の誤りを直す)

- brief の「既定 path」欄を `output/s8c-preregistration/attempt-registry.jsonl` へ訂正する
  (受領証 dir は `output/s8c-trial-registry/classification-receipts` で正しい)。
- brief の I1 に `output/s8c-preregistration/**` を加える。
- brief の C03 範囲を `:1613-1778` へ訂正する。
- brief の「床値が楽観側へ偏る」を「estimand が変わり得る (方向はデータ依存)」へ訂正する。
- consumer の「15/11/60 参照」は grep hit 数であり計数規則が無いので、
  **編集影響の見積り根拠から外す**。
- 稼働 wave との重なりは、`git diff` に加えて
  (i) 相手 worktree の `git status --short`、(ii) 本 wave の編集面 file 集合との突合、
  で再測定する (§5 参照)。

## 5. 稼働 wave との重なり再測定 (A12 への対応)

本 wave の編集面は `orchestrator/campaign/trial_registry.py`、新 core、
`orchestrator/tests/**` に限る。8b production file は触らない。
床値 pilot wave が触るのは 8b 実行系と output であり、集合として交わらない。
段 9 直前に相手 worktree の未 commit 差分も含めて再測定する。

## 6. 変異事前登録 (DW-M01)

各変異は「同じ入力を拒否する層が前後に無い」「無効化時の赤理由が一つ」を実装後にコードで確認し、
確認できなければ登録を取り下げて実効 gate へ再照準する。

| M | 変異位置 | 期待する赤 | 単一理由性の根拠 |
|---|---|---|---|
| M1 | core の「前の slot が terminal かつ retryable かつ観測開始なし」検査を無効化 | 8b profile 状態機械テストの「観測後 retry 拒否」が赤 | 8c 側は同じ入力を acceptance で拒否しないため二重拒否にならない (`:2367-2382` が唯一の層) |
| M2 | 8b profile の `require_terminal_reason_equals_classification` を False へ | 「値を見た後の理由付け替え」正例が赤 | 8c profile は元から False なので 8c 側テストは変化しない = 帰属が一意 |
| M3 | facade の `reserve_attempt_slot` を実 `def` から再 export へ | C03 snapshot テストが `manifest-registry-proof-undefined` で赤 | A7 の検算どおり、再 export は `FunctionDef` を消すので存在検査が唯一の落ち先 |
| M4 | `create_attempt_registry_genesis` を top-level 再束縛で差し替え | **A8 用の新規テストだけが赤** (C03 は落ちない) | A8 のとおり C03 は到達性を検査しないので、新規テストが唯一の層 |
| M5 | core の budget key 集約を反復込みへ戻す | 8b profile の cell-global budget テストが赤 | 8c は budget key を使わないので 8c 側は不変 = 帰属が一意 |
| M6 | core の未知 event 拒否を無効化 | 8c/8b 双方の unknown-event テストが赤 | 二層 (8c/8b) だが**同じ core の 1 箇所**なので理由は一つ |

**変異 matrix の実行は段 6。baseline 緑を先に確認する。**

## 7. 並列分割 (plan v2)

luna の指摘どおり、A/B 同時開始は core API が競合面になるため危険。次の順にする。

- **段 5-A (先行・単独):** core の注入型と 8c/8b 両 profile の**型契約だけ**を確定する。
  実装は空でよい。所有 = 新 core module。
- **段 5-B (A 完了後・並列 2 本):**
  - B1 = core 本体の実装 + `trial_registry.py` facade 化 + 8c 不変テスト。
  - B2 = 8b profile データ + core を 8b profile で駆動する状態機械テスト + A8 用テスト。
- 編集面: B1 = `trial_registry.py` と core 本体、B2 = 8b profile file と新規テスト。
  A9 の固定 14 file 追随は B1 が持つ。
