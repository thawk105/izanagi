# [T-222] dispatch_compute.py の accounting evidence へ scheduler group 束縛を追加 — 段1 brief

## scope
`tools/pegasus/dispatch_compute.py:924-946` の `_accounting_present` は accounting footer
(NQSV `qstat` 由来の stderr tail) から Request ID / Started Request Time / Ended Request Time /
Elapse の4フィールドだけを束縛し、`Group Name` フィールドを一切見ない。`Group Name` を
policy account (`DEFAULT_PROJECT = "SFC"`, line 44; qsub 提出時に `-A` で使う値、line 1714) へ
exact 束縛する検査を追加する。scope はこの1関数と呼び出し側2箇所、および対応する
テストファイル1つに閉じる。

## 確定済みユーザー裁定
- [T-193] 閉鎖裁定 (`docs/archive/worklog-phase3-0801-91-92.md:263-270`): 「main を正本にする」の
  執行をもって [T-193] 閉鎖。取り込み分 = accounting footer の `Group Name` exact 束縛は
  [T-222] へ独立残務として切り出し済み (本 ID の残件として扱わない、とユーザーが明言)。
- 実装方針そのもの (「やるかどうか」) は先行 wave の裁定で確定済み:
  `output/insights/2026-07-30_dev-wave-improve-wave/s9-t193-ruling.md:64`
  「移植する: accounting footer の `Group Name` を policy account へ exact 束縛する。」
  本 wave はこの確定済み方針の main への適用形 (「どう実装するか」) だけを決める。

## 不変条件
- 正しさ防壁 (accounting evidence gate) の受理集合が変わる: Group Name が policy account と
  不一致の job は今後 `_accounting_present` が False を返す。受理集合の変化は段4で明記して裁定する。
- 既存4フィールドの挙動 (Request ID 完全一致・他3フィールド非空行の存在) は変えない。回帰させない。
- テストを甘くして緑にしない (F27)。`orchestrator/tests/test_pegasus_dispatch_compute.py` の
  fake accounting footer 生成 (`_Scheduler._finish`, line 86-110) に `Group Name:` 行が無いため、
  実装後は必ず全既存テストが赤になる — fixture のデフォルト値へ正しい `Group Name` を足す形で
  直すこと。「検査を無効化」「対象フィールドを検査対象から外す」方向の変更は禁止。

## 成果物の形
1. `_accounting_present` (または呼び出し側) が `Group Name:` フィールドを抽出し、期待値
   (`DEFAULT_PROJECT`) と exact 一致することを要求する。
2. `orchestrator/tests/test_pegasus_dispatch_compute.py` の fixture 更新 (Group Name 行を
   policy account 値で追加) — 既存テストは全部緑のまま。
3. 新規テスト: (a) Group Name が policy account と一致 → True (既存契約の延長)、
   (b) Group Name が不一致 → False、(c) Group Name 行が欠落 → False。
   既存の `test_accounting_requires_matching_request_id_and_all_nqsv_fields` /
   `test_accounting_accepts_measured_nqsv_shape_only_when_id_matches` (line 2238, 2242) と
   同じ形式・同じ file に置く。

## 並列分割方針
単一実装単位 (所有パス: `tools/pegasus/dispatch_compute.py`,
`orchestrator/tests/test_pegasus_dispatch_compute.py` のみ)。分割不要。

## 変更面アンカー表
- `tools/pegasus/dispatch_compute.py:44` — `DEFAULT_PROJECT = "SFC"` (policy account の定義元)
- `tools/pegasus/dispatch_compute.py:924-946` — `_accounting_present` 本体
- `tools/pegasus/dispatch_compute.py:1935` — 呼び出し箇所1 (ループの break 条件)
- `tools/pegasus/dispatch_compute.py:1944-1946` — 呼び出し箇所2 (grace 期限時の記録用)
- `tools/pegasus/dispatch_compute.py:1714` — `"-A", DEFAULT_PROJECT` (qsub 提出、Group Name の由来)
- `orchestrator/tests/test_pegasus_dispatch_compute.py:86-110` — `_Scheduler._finish` (fake footer 生成)
- `orchestrator/tests/test_pegasus_dispatch_compute.py:2206-2250` — 既存契約テスト群

## 参考資料 (未 land の先行実装。設計そのものは段3敵対相談・段6変異検証まで通過済みだが、
対象コードが main の現行形と異なるため鵜呑みにせず main の実形に合わせて再導出すること)
- `output/insights/2026-07-30_dev-wave-improve-wave/s2-plan-r5.md` — regex 案
  `re.compile(r"Group Name:[ \t]+(\S+)\Z", re.ASCII)` (ただし対象は resume 側の別関数
  `validate_nqsv_accounting` であり、本 wave の対象 `_accounting_present` とは呼び出し文脈が違う)
- `output/insights/2026-07-30_dev-wave-improve-wave/s6-mutation-r5.md` — mutation
  「accounting footer の Group Name 照合を外す」→ KILLED の実例
- `output/insights/2026-07-30_dev-wave-improve-wave/s6-review-r5-a.md:85` — 実データ整合の実例
  (`final-receipt.json` の `"Group Name:             SFC"` と `policy.account "SFC"` の一致)
- `codex/dev-wave-improve` branch 自体は既に存在しない (未 land のまま削除済み)。line 番号は
  当時の branch 上のものであり main と対応しない。

## 判断が割れうる前提 (親の provisional 裁定、攻撃対象)
- (P1) 期待 Group Name の受け渡し方法: `_accounting_present` 内で module 定数 `DEFAULT_PROJECT` を
  直接参照するか、引数として渡すか。親の provisional 裁定: 直接参照 (既存シグネチャ
  `(stderr_record, request_id)` を維持し呼び出し側2箇所を変えずに済む方が変更面最小)。
  テスト容易性 (期待値を変えたテストを書きたい場合) とどちらが勝るかは段3で攻撃させる。
- (P2) mismatch 時の型: `_accounting_present` は bool 述語関数のままとし、mismatch は False を
  返すだけ (呼び出し側の既存 `accounting-grace-expired` 経路に自然に乗せる)。専用の即時
  `DispatchError` は投げない — 関数の型 (bool 述語) を変えると呼び出し側 (1935, 1944-1946) の
  ロジックも変える必要がありスコープが広がるため。先行実装 (`validate_nqsv_accounting`) は
  「検証専用関数」で例外を投げる型だったが、これは別関数であり本関数の型とは異なる。

## DW-G05 成果物影響
実装しない場合: scheduler group が policy account と異なる job の accounting evidence を
`_accounting_present` が誤って True 判定し続ける (accounting 証跡の quiet corruption を防げない)。
ただし main 経路でこの mismatch が実際に発生した実例は無く (理論的ギャップ)、現行の
certified 選択結果・proof chain への実影響は確認されていない。
実装する場合: mismatch する job は accounting evidence 未確認のまま grace 期限を迎え、
`marker_valid` が True (compute marker 自体は観測済み) なら `DispatchError
("result/log/accounting-grace-expired")` (line 1983) を送出する経路に落ちる
(`marker_valid` が False なら従来どおり F47 latch 経路。Group Name 単独の mismatch では
compute marker の可否と無関係なため通常は前者)。既存の受理集合を狭める方向の変更であり、
緩める方向ではない。
