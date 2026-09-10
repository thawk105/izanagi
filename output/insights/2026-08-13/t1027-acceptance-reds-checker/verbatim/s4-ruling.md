# 段 4 裁定 — [T-1027] 非帰属 checker

- 裁定: 2026-08-13 09:35 JST、親 (claude)
- 入力: `brief.md` / `plan.md` / `consult-a2.md` (レンズ A) / `consult-b.md` (レンズ B)
- 裁定 inbox 再走査済み (08:00 JST 以降の 2 件はいずれも本 wave の前提を覆さない)

## 0. 親 brief の訂正 (レンズ A [B] を採用)

**brief の不変条件は向きが逆だった。** brief は
「不完全な collection から `attributable` を出してはならない」と書いたが、
`attributable` (rc=1) は**停止する側**であり、危険な方向ではない。
禁止すべきは **判定不能な入力から `non-attributable-only` / rc=0 を出すこと**である。
rc=0 が「取り込んでよい」と読まれるからである。

**確定した不変条件 (実装・変異・レビューの正本):**

> collection の完全性、selector の一意性、単独 rerun の帰結のいずれかを証明できない入力から、
> `status=non-attributable-only` または rc=0 を出してはならない。証明できない場合は rc=2 で止まる。
> rc=1 (attributable) 側へ倒すことは安全側であり禁止しない。

## 1. 採用する所見 (real・scope 内・must-fix)

| # | 出所 | 内容 | 成果物影響 |
|---|---|---|---|
| R1 | 親の実測 (レンズ B [B] を親が独立確認) | `_completed` の既定 `timeout=120.0` が dispatch の実測所要 **211 秒 / 212 秒** に負ける。receipt 経路を直しても collection がここで落ちる | 直さなければ checker は永久に rc=2。実運用到達がゼロ |
| R2 | plan A | collection の権威を relay stdout から **dispatch receipt の `scheduler_logs.stdout.tail`** へ移す。receipt path は `[Pegasus dispatch] receipt を <path> へ保存しました` の**非 relay 行**から一意に取り、location / schema / request binding / 完全性を検査 | 部分 collection による誤 selector 解決を閉じる |
| R3 | plan B | **footer 完全性 gate**。`N tests collected` の selected 件数と、path に一致する unique nodeid 件数の一致を必須にする。欠落・複数・未知書式・0 件は rc=2 | 黙って部分集合が match する経路を構造的に閉じる |
| R4 | plan A / レンズ B [B] | dispatch が probe worktree 内に作る成果物を、**検証済み nonce directory に限って** `finally` で除去する。root 全体・glob・未検証 path は削除しない。削除失敗は rc=2 | 直さなければ collect 修正の直後に既存の指紋 gate で再停止する |
| R5 | レンズ A [B] | **単独 rerun の rc=1 だけで非帰属としない。** 当該 selector が実際にその走行で FAILED/ERROR したことを rerun 自身の出力で裏取りする。session-level error による rc=1 を非帰属の根拠にしない | rc の過剰解釈で誤って受理集合が広がるのを閉じる |
| R6 | レンズ B [M] | collection と rerun の選択集合を **argv 決定にする**。`PYTEST_ADDOPTS` 等、pytest の選択に効く環境変数を無効化して子へ渡す | 環境経由の deselect が footer と整合したまま通る経路を閉じる |
| R7 | レンズ A [M] | **footer 欠落を production path のテストで固定する。** seam から `InvalidInput` を投げるだけのテストは恒真であり、これを検出力の証拠にしない | 恒真テストが「謳うだけで発火しない assert」になるのを防ぐ |
| R8 | レンズ A [M] | 権威 tail に **U+FFFD (decode 置換文字) があれば拒否**する。`errors="replace"` は byte 長を保つことがあり、長さ一致は lossless の証明にならない | 壊れた nodeid 集合から非帰属を導く経路を閉じる |
| R9 | レンズ A [M] | checker receipt に **collection の出所** (receipt path または nonce、request ID、権威 stdout の sha256) を記録する | どの collection から非帰属を導いたかを台帳から監査可能にする |

## 2. 変異事前登録 (DW-M01)

**wave 前の実コードの形を含む変異** = M0 / M5 / M7 (いずれも現行 main の実コードそのもの)。

| ID | 位置 | 変異 | 期待 node | 単一理由性 |
|---|---|---|---|---|
| M0 | 権威 stdout の選択 | `authoritative_stdout` を **wave 前の `result.stdout.splitlines()`** へ戻す | `test_truncated_relay_uses_complete_dispatch_receipt` | receipt/schema は有効で前段を通り、relay 側だけ nodeid 欠落 → footer 件数の 1 つの不一致で赤 |
| M1 | footer 件数 gate | 件数比較を恒偽化 | `test_collection_footer_count_mismatch_fails_closed_before_rerun` | source・grammar・selector すべて有効。落とすと rc=1 → rc=0 へ反転 |
| M2a | receipt 完全性 | `omitted_bytes != 0` 検査を恒偽化 | `test_dispatch_receipt_with_omitted_scheduler_stdout_fails_closed` | 他 field をすべて有効に固定。**M2b と分離** (レンズ A [M] の指摘) |
| M2b | receipt 完全性 | `size != len(tail.encode())` 検査を恒偽化 | `test_dispatch_receipt_size_mismatch_fails_closed` | `omitted_bytes == 0` かつ size 不一致の独立負例。M2a では殺せない |
| M3 | request binding | `request.task` / `args` 不一致条件を恒偽化 | `test_dispatch_collection_receipt_requires_bound_request_args` | location と残り schema は正しく、別走行の request だけが不正 |
| M4 | receipt location | 許可 path 形の判定を恒偽化 | `test_dispatch_receipt_outside_probe_root_fails_closed_before_rerun` | 外部 receipt の内容は他をすべて有効にする。location 検査は 1 helper に集約 |
| M5 | footer grammar | count=1 の期待 noun を `test` → `tests` にする | `test_single_test_collection_footer_is_accepted` | **正例 (過剰拒否の positive control)**。新 gate が受理集合を承認外に縮めないことを示す |
| M6 | rerun 裏取り | rerun 出力の FAILED/ERROR 照合を外し、**wave 前と同じく rc だけ**で非帰属にする | `test_rerun_rc_one_without_matching_outcome_fails_closed` | R5 の検出力。rc=1 は同じ、出力だけが不一致という単一理由 |
| M7 | timeout | dispatch 対応 timeout を **wave 前の `120.0`** へ戻す | `test_dispatch_commands_use_dispatch_aware_timeout` | command_runner へ渡る timeout の literal pin。他層は timeout を検査しない |
| M8 | 環境正規化 | `PYTEST_ADDOPTS` 無効化を外す | `test_collection_environment_neutralizes_pytest_addopts` | 子へ渡る env の pin。argv 検査は env を見ないため mask しない |

**登録から外すもの** (plan の除外理由を追認 + 追加):

- 現行 `if not nodeids` の単独無効化 — 新 footer gate が同じ入力を後段で拒否する等価変異。
- relay header の `omitted_bytes` 検出だけの無効化 — receipt 欠落・schema・footer gate が
  同じ入力を拒否し続け、受理集合が変わらない (レンズ A [N] も同じ結論)。
- 診断文字列の退行変異 — rc と分類集合が変わらない。B-057 の semantic kill ではない。
- `_selector_from_collection` の no-match gate 無効化 — 完全性 gate より後段で、
  今回の打ち切り入力には到達しない。

## 3. refuted / 格下げ

- **レンズ A [B] 「delimiter の非一意写像」→ [N] へ格下げ。**
  反例が成立するには nodeid の関数名部分に **literal `@`** が要る。pytest が `@` を出せるのは
  parametrize id の `[...]` 内だけで、その場合 suffix は `[` で始まり現行実装が既に拒否する。
  Python 識別子に `@` は入らず、path 部分は `::` より前にある。
  **到達可能な入力を構成できないため blocker としない。** なお R5 (rerun の裏取り) が
  入ることで、仮に誤解決しても rerun 出力の nodeid 不一致で捕まる方向へ強くなる。
  この判断は記録に残し、反例が構成できた時点で再訪する。
- **brief の relay 上限の一般化** (レンズ A [N]) — 指摘は正しい。rc=0 は 4 KiB、rc!=0 は 64 KiB。
  brief の記述を「成功走の relay 上限」と限定する。collection は rc=0 必須なので結論は変わらない。

## 4. scope 外だが real (裁定パッケージ候補 — ユーザーへ返す)

1. **[B] 直した checker を呼ぶ production consumer が無い。** `dev_wave_wait.py` /
   `dev_wave_land.py` に caller が存在しない。本 wave では編集禁止 (t907-t908-t910 wave の担当、
   rulings9 #1)。**したがって本 wave の「実運用到達」= 実データで緑になること**であり、
   land 経路への結線ではない。結線時は **exact rc=0 かつ `status=non-attributable-only`
   かつ log hash 束縛 ([T-1019]) を同時に**検査する必要がある (レンズ A [M])。
2. **[M] 赤 n 件で dispatch が 2n 回走る。** 現行は reference ごとに fresh probe worktree +
   collection + rerun。実測 211 秒/dispatch なら 10 件で約 70 分。
   path 単位の collection 再利用は `test_each_node_uses_a_fresh_probe_worktree` の
   不変条件と衝突するため、**本 wave では実装しない**。別 wave で設計する。
3. **[M] dispatch producer 側の容量。** relay ではなく上限のない collection artifact を
   提供する案、および選択に効く環境を receipt へ束縛する案。`tools/pegasus/**` は scope 外。

## 5. 段 5 への指示

- 実装単位は 1 つ (編集面が `tools/check_acceptance_reds.py` +
  `orchestrator/tests/test_check_acceptance_reds.py` の 2 file)。Codex `role=author`、
  `reasoning=high`、`sandbox=workspace-write`。
- R1〜R9 をすべて実装する。R1 の timeout は dispatch 自身の deadline
  (walltime 3600 秒 + grace 300 秒 = 3900 秒) を**上回る**値にし、
  dispatch がタイムアウトの権威になるようにする。120 秒は誤り。
- 既存テストの期待値を変更しない。既存 `test_ignored_artifact_from_node_fails_closed` は
  無変更で残し、限定 cleanup が任意 ignored artifact の無視へ広がっていないことを保つ。
- production を fail-open にしない。期待値が誤りと判断したら実装を変えず報告して止める。
