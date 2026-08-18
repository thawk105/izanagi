# 段 4 裁定 — [T-1352] C07 consumer

裁定日時 2026-08-18 18:45 JST。裁定 inbox 再走査済み (full7 / full8 以降の新規なし)。

## 所見の裁定

| ID | real/refuted | 採否 | scope |
|---|---|---|---|
| A1 親の 4 赤は C07 の実効変異ではない | real | 採用 (記録の是正) | 内 |
| A2 未登録 evaluator は `evaluate_all` から到達不能 | real | 採用 (正直な記録) | 内 |
| A3 「入口名が不存在」と「配線追加不能」の混同 | real | 採用 (記録の分離) | 内 |
| A4 floor ref が caller の自己申告 | real | **採用 (実装)** | 内 |
| A5 params が実測後に差し替え可能 | real | **部分採用 (実装)** | 内 |
| A6 caller 計算済み delta を信頼 | real | **採用 (実装)** | 内 |
| A7 3 条件が実質 2 条件へ潰れる / holdout を跨いで平均 | real | **採用 (実装)** | 内 |
| A8 期待 cell 集合を生成行から導出 = 恒真 | real | **採用 (実装)** | 内 |
| A9 acceptance が official_status を消費しない | real | 不採用 (scope 外) | 外 |
| A10 出力先が repo 内 / 部分表の残留 | real | **採用 (実装)** | 内 |
| A11 静的検査が呼出し存在だけを見る | real | **部分採用 (実装)** | 内 |
| A12 実走・受理・receipt・certified selector 層 | real | 不採用 (scope 外) | 外 |
| B1 未登録は実効 gate でない | real | A2 と同一 | 内 |
| B2 1 手反転は成立しない (accept_trial ほか) | real | 採用 (裁定パッケージ) | 外 |
| B3 出力先の repo 外強制 | real | A10 と統合 | 内 |
| B4 4 赤の一般化 | real | A1 と同一 | 内 |
| B5 evaluator blob hash / WAVE_REQUIRED_PATHS | real | 採用 (親が実測済み) | 内 |
| B6 同名 token の誤結合 | real | **採用 (実装: decoy 負例)** | 内 |
| B7 必要層の大半が scope 外 | real | A12 と同一 | 外 |

## A1 の是正 (親の実測の正しい範囲)

親の probe は key 7 へ `_evaluate_c01` を置き、`_negative_control_case` に C07 分岐を作らずに
dict だけへ追加したため、`test_noop_and_token_only_fixtures_never_satisfy[nc_c07...]` は
C07 の判定ではなく helper の AssertionError で落ちた。したがって 4 赤のうち C07 判定に
帰属できるものは無い。**結論を支えるのは次の 2 件だけ**である。

- `test_machine_checkable_contract_and_evaluator_registry_are_bijective`
- `test_satisfiable_predicate_requires_negative_control`

この 2 件は契約 JSON の `machine_checkable` から集合を導出しており、契約を反転せずに
`_MACHINE_EVALUATORS` へ C07 を足す限り、evaluator の中身が何であっても赤になる。
`test_current_repository_gap_reason_snapshot_...` は設計上 cross-wave review で更新する台帳であり
blocker ではない。よって **(P1) は維持**する。理由は「4 赤」ではなく「契約由来の全単射 2 件」である。

## 確定した設計 (プラン v2 の差分)

1. **floor の封印 (A4)。** `verify_floor_bytes` は caller の期待値を受け取らない。
   `load_ratified_freeze()` が返す ratified freeze から期待 `path` / `sha256` / `env_tag` /
   `measurement_head` を導出し、実 bytes と突き合わせる。戻り値は provenance だけを持つ
   frozen object とし、数値・床値・threshold を一切持たない。`judge` の signature に
   floor 由来の引数を置かない (型で不可能にする)。検証失敗は例外で、publish へ進ませない。
2. **params の封印 (A5、部分)。** `judge` は raw な `delta_min` / `sd_max` / `n` を受け取らず、
   値・unit・direction・n・事前登録 source binding を持つ frozen params object だけを受ける。
   §10.2 のとおり、**制約違反の契約値は個別対比を判定不能にせず、事前登録未発効を意味する
   専用例外を送出する**。end-to-end の prereg commit 束縛は producer が無いため bundle 送り。
3. **入力の再導出 (A6)。** caller 計算済みの median / delta / 順位を受け付けない。
   correctness gate を通過した trace-disabled observation から judge 内で構成内中央値と
   対差を再導出する。gate 未通過・未検証入力は判定不能。
4. **3 条件の完全集合と holdout 分離 (A7)。** condition ID は
   `{on_off_prediction_difference, swapped_follow_through, paired_repeat_contrast}` の
   重複なし完全集合。長さ 3 だけでなく集合等価を検査する。C3 は **holdout ごと**に評価し、
   H1 と H2 を 1 本の delta vector へ混ぜない。三値の優先順位表 (判定不能 > 不成立 > 成立) を固定する。
5. **cell 集合の非導出性 (A8)。** 期待 cell 集合は生成行から導出しない。ratified manifest 由来の
   事前宣言集合を独立の引数として受け取り、生成行と欠落・余剰・重複の両方向で完全一致を要求する。
   引数が省略された場合は生成しない (既定で生成行から埋める経路を作らない)。
6. **出力の原子性と repo 外 (A10 / B3)。** 3 表は staging に全部作ってから公開する。
   途中失敗で表も receipt も残さない。出力先は絶対 path、symlink 解決後に repo working tree の
   外、既存 bytes を上書きしない (create-only)。repo 内既定 path を定義しない。
7. **静的検査の data flow (A11、部分)。** `_evaluate_c07` は「呼出しが存在する」で満足しない。
   validator と cell-set 検査の戻り値が捨てられていない (名前へ束縛される・条件式へ入る・
   返される) ことを AST で確認し、条件 ID の literal 集合がちょうど 3 要素で重複が無いことを
   確認する。完全な data flow 証明は静的には不可能であり、その限界を worklog に明記する。
8. **decoy 負例 (B6)。** `judge` / `verify_floor_bytes` は repo 内の別 module にも同名がある
   (`s8b_verdict.py`、`s8b_oracle_judge.py`)。`_evaluate_c07` は契約が宣言した path の blob だけを
   読むことをテストで pin し、別 module に 3 名を置いた decoy fixture が
   `RESULT_JUDGE_CONSUMER_INCOMPLETE` になることを確認する。
9. **holdout 三軸語の禁止 (親実測)。** 新規 file に `rr20` / `rr80` を書かない
   (`test_wave_files_do_not_contaminate_production_holdout_scan` が repo 全体を走査する)。
   H1 / H2 は抽象識別子として扱う。

## scope 外 = 裁定パッケージ候補 (ユーザーへ返す)

1. **束ね wave の「1 手反転」は成立しない。** 契約 C07 の `reachable_from` にある
   `accept_trial` (2 箇所) と `s8b_ratified_freeze.py` 側の `verify_floor_bytes` は実在しない。
   反転には (a) 契約本文の入口名を実在する acceptance 入口へ改める、
   (b) `MACHINE_CONTRACT_FUNCTION_CHECKS` へ C07 の mapping を追加する、
   (c) 新世代 g8 を発行する、の 3 つが同時に要る。欠落を exclusion pin で隠さない。
2. **acceptance 配線 (A9)。** 現行 receipt は構造的に `certifying: false` で、
   `official_status` を消費しない。certified selector が公式性能表だけを受理する配線は別 wave。
3. **実走層 (A12)。** H1/H2 の正式 workload・schedule・master seed・attempt registry・
   correctness gate・observation producer。
4. **§5 の 8 欄記入。** 本 wave が validator を実装することで §10.2 の記入解除条件のうち
   「consumer が実在する」が満たされる。記入自体は別作業。

## 変異事前登録 (DW-M01)

実装確定後に anchor を再検証する (DW-M07)。単一理由性を各変異で確認する。

| # | 位置 | 変異 | 期待 |
|---|---|---|---|
| M1 | `s8c_result_judge.py` C3 の成立式 | `mean_delta > delta_min` → `>=` | KILLED (境界テスト) |
| M2 | `s8c_result_judge.py` 標本 SD | 分母 `n - 1` → `n` | KILLED |
| M3 | `s8c_result_judge.py` cell 集合検査 | 期待集合を生成行から導出 | KILLED (欠落 cell テスト) |
| M4 | `s8c_result_judge.py` 3 条件集合 | 1 条件を重複させ 3 要素を保つ | KILLED (集合等価テスト) |
| M5 | `s8c_result_judge.py` publish | 失敗時に生成済み表を残す | KILLED (原子性テスト) |
| M6 | `_evaluate_c07` の必須検査 | entrypoint 検査 1 本を除去 | KILLED (nc_c07 直接テスト) |
| M7 | `s8c_result_judge.py` C3 の holdout 分離 | H1/H2 を 1 vector へ結合 | KILLED (holdout 分離テスト) |

## 成果物影響 (DW-G05)

本 wave 単体では C07 は `floor-judge-contract-undefined` のままで、certified 選択も台帳行も
増えない。値は「束ね wave が反転できる形と、恒真でない判定器」を作ることにある。
上記 7 点を実装しなければ、反転後の C07 は「謳うだけで発火しない」保証になり、
規律 2 が想定する reward hack をそのまま通す。
