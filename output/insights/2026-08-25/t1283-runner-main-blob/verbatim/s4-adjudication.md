# 段 4 裁定 — [T-1283] 受入全走の実行器を tested main の blob へ束縛する

親が段 3 の 2 レンズ (sol=正しさ境界、luna=整合と実効性) の所見を real/refuted と scope 内外へ裁定し、
プラン v2 を確定する。実測はすべて base main `bb7753fa` の worktree で行った。
裁定時点の local main は `a068b7f5` から `9dc26fd4` へさらに進んでいる (snapshot)。

## 裁定 inbox の再走査

wave 開始後に main へ D843〜D874 が入った。本件に触れるのは次の 3 件で、いずれも本 wave の
scope を変えない。

- **D862** (待ち手は呼び出し受領証を発行する): 「待ち手自身の権威の所在は変えない」と明記しており、
  本 wave の I2 (待ち手の tip 束縛を変えない) と整合する。
- **D867** (git 環境変数の除去漏れは当該箇所だけ直し、族一般化は 2 例目を待つ): 対象箇所は
  `s8b_ratified_freeze.py` 系の指紋計算であり本 wave の編集面ではない。ただし
  「実行環境の浄化を族へ一般化するのは独立 2 例目を実測してから」という先例として、
  レンズ A 所見 3 の裁定根拠に使う。
- **D871** (変異 matrix はレビュー通過後の必須検査): 段 6 でそのまま従う。

## レンズ A (正しさ境界) の裁定

| # | 所見 | 判定 | scope | 対応 |
|---|---|---|---|---|
| 1 | tip 待ち手が受領証を直作成できる経路は残る | real | 外 | D440/D583 が意図的に開けたまま。保証の記述を「実行器の単独差し替えでは偽造できない」に限定する |
| 2 | launcher bootstrap は tip を発行者にしうる | real | 外 | 既存 bootstrap 面。新設ではない。記録のみ |
| 3 | PATH 解決の `python3` / 素の `git` で実行体をすり替えうる | real | **外** | 下記で詳述。裁定パッケージへ |
| 4 | land 自身の実行権威が自己検証されない | real | 外 | 既存の trust-root 欠落。裁定パッケージ候補として記録 |
| 5 | gate が効く層の整理と未被覆面 | real | 内 (記述) | 保証を層ごとに限定して worklog へ書く |
| 6 | M3 と digest 照合先変更は独立保証としては弱い | real | 内 (記述) | primary guarantee は「suite 前 equality」と「land の独立 equality」。M3 は seam の故障注入検査と位置づける |
| 7 | P4 の実測対象は receipt が確定した tested pair | real | 内 | 採用。受入投入前でなく **受領証発行後**の値で確認する |
| 8 | forward-main で着地する tip の実行器は未検査 | real | 外 | 既存の landing 契約。裁定パッケージ候補として記録 |
| 9 | Git failure の retryable 分類が広い | real | 外 | `_runner_tree_entry` / `_acceptance_blob_content_sha256` の既存挙動であり本 wave は変えない。記録 |
| 10 | tip 読取失敗時の fallback 変異を殺すテストが無い | real | 内 | 採用。負例テストを 1 本追加する |

### 所見 3 を scope 外とする理由

レンズは scope 内と判定したが、親は **scope 外**と裁定する。根拠は 3 点で、いずれも実測または既裁定である。

1. **D838 が命じているのは blob の照合であって実行体の解決ではない。** 裁定文の対象は
   「実行器 (`tools/run_tests.py`) を tested main 側の blob と照合する」ことである。
2. **被判定側 (wave の tip) はこの経路へ到達できない。** PATH は待ち手を起動する運用者の環境に属する。
   tip が PATH を握るには待ち手 (`tools/dev_wave_wait.py`) を書き換える必要があり、それは D440 が
   意図的に開けたままにし D583 が残余 (i) として記録した経路に吸収される。つまり所見 3 は
   新しい攻撃面を足さない。
3. **D867 が同型の判断を先例として置いている** — 実行環境の浄化を族へ広げるのは独立 2 例目を
   実測してから。

なお修正費用は小さい。待ち手は launcher を `sys.executable` で起動しているのに
(`tools/dev_wave_wait.py:3047`)、launcher が実行器を起動する所だけ素の `python3` である
(`tools/acceptance_launcher.py:214`)。この不整合は 1 行で揃う。この事実を添えて裁定パッケージへ送る。

## レンズ B (整合と実効性) の裁定

| # | 所見 | 判定 | scope | 対応 |
|---|---|---|---|---|
| 1 | fixture の digest 一律 main 化で中心負例が偽の緑になる | real | 内 | **must-fix**。下記 v2 に反映 |
| 2 | 過去 v5 受領証の再検証 | real (懸念)、実測で空 | 内 | 下記の実測により移行処理は不要と裁定 |
| 3 | claim 後 merge 前に main の実行器が変わると無関係 wave も再受入 | real | 内 (記述とテスト) | equality は緩めない。runbook へ書き、負例と正例をテストに置く |
| 4 | 静的な赤緑判定表・identity まで見る必要 | real | 内 | 採用 |
| 5 | テスト consumer の列挙不足 | real | 内 | 採用。検証一覧へ追加 |
| 6 | hit 数 2 箇所の不一致 | real | 内 | 採用。code 15→13、docs 105→103 |
| 7 | `dev_wave_wait.py` の参照範囲 2158-2234 → 2158-2237 | real | 内 | 採用 (プランの参照のみ) |
| 8 | 実測の一般化 (`HEAD == main` は stale) | real | 内 | 採用。SHA 付きの観測には snapshot と明記する |

### 所見 2 の実測 — 移行処理は不要

tracked な JSON を全件 (1495 file) parse し、`schema_version` が
`dev-wave-acceptance-receipt` で始まるものを数えた。母集合は tracked JSON 全件、除外はなし。

- 受領証は 1 件 (`output/insights/2026-08-21_t1434-wave-d/acceptance-receipt-4.json`、v5、child-green)。
- その `tested_main=46fbce3d` と `tested_tip=5f1c0d6c` の `tools/run_tests.py` は content SHA-256 が
  ともに `b4ac7959...` で一致する。

したがって tracked な範囲に **実行器が分岐した v5 受領証は 0 件**であり、新 land が過去の
受領証を遡って拒否する事例は無い。legacy 用の migration reader は作らない。
(この実測は tracked 成果物に限る。走行中 wave の未追跡受領証は対象外だが、そこで分岐していれば
拒否するのが本変更の目的そのものである。)

## プラン v2 (確定)

段 2 プランを土台に、上記の裁定を反映した確定版。

### 実装

1. `tools/acceptance_launcher.py`
   - `_read_runner_blob` の revision 引数を一般化し、呼び出し側が渡した revision の blob を読む。
     main 欠落時に tip へ落ちる fallback は作らない。
   - `_launch` は次の順で動く。(a) `tested_main` から実行予定 bytes を読む、(b) `tested_tip` から
     比較用 bytes を別に読む、(c) 一致しなければ `blob_runner` を **一度も呼ばずに** `LauncherFailure`、
     (d) 一致したときだけ main 由来の buffer を `_run_blob` へ渡す。
   - 実行後の M3 独立再取得の対象を `tested_main` へ移す。
   - `_SCHEMA_VERSION`、receipt の root field、canonical JSON は変更しない。
   - **`_run_blob` の interpreter は変更しない** (所見 3 は scope 外)。
2. `tools/dev_wave_land.py`
   - `main_runner_entry` の取得を verdict 分岐の外へ出し、`tip_runner_entry` と同じ共通検査に置く。
   - 共通検査で main/tip 双方の entry が blob であること、object ID が一致することを要求する。
   - `runner_executed_sha256` の照合先を `main_runner_entry` 側にする。
   - 非帰属枝には checker の main/tip equality だけを残す。
   - `retryable_same_request` の既存分類を保つ。新しい rc も理由文字列も足さない。
3. `tools/dev_wave_wait.py` は変更しない。

### gate の禁止 (署名) と通る正例

- **禁止**: `tested_main` の `tools/run_tests.py` と `tested_tip` の `tools/run_tests.py` の
  object ID が異なる受入走行は、suite を起動せず受領証も発行しない。同じ受領証は land も拒否する。
- **通る正例**: `tested_main` と `tested_tip` が別 commit であっても、両者の
  `tools/run_tests.py` の object ID が等しければ、`child-green` の受領証は発行され land も通る。

### テスト (確定)

`orchestrator/tests/test_acceptance_launcher.py`

- `test_matching_main_and_tip_runner_blobs_execute_tested_main_source` — 通る正例。
  reader の revision 呼び出し順が main, tip, main であること、`blob_runner` が受け取った buffer が
  **main 側 reader が返した object そのもの (identity)** であること、suite が 1 回だけ起動され
  受領証が出ることを固定する。内容一致だけでは main 由来を証明しないため、同内容の別 object を
  用意して identity を見る (レンズ B 所見 4)。
- `test_main_tip_runner_blob_mismatch_is_rejected_before_execution` — main/tip で異なる bytes。
  `blob_runner`・outcome・completion・受領証書き込みのいずれにも到達しないことを固定する。
- `test_missing_tested_main_runner_is_rejected_before_execution` — main 読取だけ失敗。
  tip に実行器があっても suite を起動しない。
- `test_missing_tested_tip_runner_is_rejected_before_execution` — **新規** (レンズ A 所見 10)。
  main 読取成功・tip 読取失敗で、main の bytes を tip の代用にしないことを固定する。
- `test_m3_runner_digest_mismatch_is_rejected` (既存、改稿) — reader を 3 回に対応させ、
  実行後の main 再取得だけを drift させる。

`orchestrator/tests/test_dev_wave_land.py`

- **fixture は一律変更しない** (レンズ B 所見 1、must-fix)。`_Repo._acceptance_receipt` に
  runner digest の基準 revision を選ぶ引数を足し、既定は現行と同じ挙動にする。
  divergence 系のテストでは旧 launcher 相当の **tip digest** を明示的に渡し、
  拒否理由が digest 不一致でなく main/tip equality 違反であることを分離する。
  あわせて `_runner_tree_entry` の revision 呼び出しを spy し、`tested_main` と `tested_tip` の
  exact な組が引かれたことを確認する。
- `test_land_rejects_child_green_runner_blob_divergence` — 現行
  `test_child_green_accepts_different_main_and_tip_runner_blobs` を反転改稿。
- `test_land_accepts_child_green_matching_main_and_tip_runner_blobs` — 通る正例。別 commit・同一
  object ID。main と tip の両 revision が引かれたことを spy で確認する。
- `test_land_child_green_runner_path_absence_is_permanent_rejection` — tip digest を明示し、
  main 欠落だけが拒否理由になるようにする。`release_safe=True`、`retryable_same_request=False`。
- `test_land_child_green_runner_lookup_process_failure_is_retryable` — tested-main lookup だけを
  rc=128 にする。tip lookup まで失敗させると旧実装でも拒否するため偽の緑になる。
- `test_land_rejects_non_attributable_runner_blob_divergence` — 既存負例を維持。
- 既存 E2E `test_real_waiter_receipt_is_consumed_by_real_land_end_to_end` は実行器を main 側 commit へ
  含める形へ直す。これは実装差を検出しない **既存互換正例**として分類する。

### 変異事前登録 (DW-M01 / B-057)

| ID | 変異 | 殺すテスト | 単一理由性の確認 |
|---|---|---|---|
| M1 | launcher の main/tip equality を `_run_blob` の後へ移す | `test_main_tip_runner_blob_mismatch_is_rejected_before_execution` | 前段に同じ入力を拒否する層は無い。赤理由は「suite が起動された」の 1 つ |
| M2 | land の runner equality を非帰属枝の中へ戻す | `test_land_rejects_child_green_runner_blob_divergence` | fixture が tip digest を渡すため digest 検査では拒否されず、equality 欠落だけが赤理由になる |
| M3 | `_read_runner_blob` へ渡す revision を `tested_tip` へ戻す | `test_matching_main_and_tip_runner_blobs_execute_tested_main_source` | equality が成立する fixture のため content では区別できず、revision 呼び出し順と object identity だけが赤理由になる |
| M4 | tip 読取失敗時に main の bytes を tip の代用にする | `test_missing_tested_tip_runner_is_rejected_before_execution` | 他の負例は tip 読取例外を起こさないため、この変異を殺す層は他に無い |
| M5 (過剰拒否の正例) | land が `tested_main` でなく `locked_main` の実行器を引く | `test_land_accepts_child_green_matching_main_and_tip_runner_blobs` | 受理集合を縮小する wave の承認外過剰拒否を検出する正例として登録する |

**登録しない変異**: 「land の digest 照合先を tip へ戻す」。main/tip の object ID 一致を先に
要求するため、どちらの blob へ照合しても結果が同値になる (レンズ A 所見 6)。等価変異であり、
登録すると発火しない gate を数えることになる。

### 運用記述 (docs)

- `docs/pegasus-runbook.md` の受入節へ、(a) 実行器の読み元が tested main であること、
  (b) suite 起動前に main/tip の一致を要求すること、(c) 実行器を編集する wave は全 verdict で
  受入を通せないこと、(d) 判定器を編集する wave は非帰属判定だけが不能で child-green は通ること、
  (e) **claim 後・内部 merge 前に main 側で実行器が更新されると、実行器を編集していない wave も
  一度拒否され再受入が要ること** (レンズ B 所見 3) を書く。
- launcher の `tested-tip-bootstrap` 記述は変更しない。

### 本 wave 自身の受入

受領証は tested main 側の **旧** launcher が v5 で発行し、tip 側の **新** land が検証する。
新 land が要求するのは受領証の `tested_main` / `tested_tip` における実行器 object ID の一致であり、
本 wave は `tools/run_tests.py` を編集しないので成立する。確認は推定でなく、
**受領証発行後**に受領証が束縛した tested pair に対して実測する (レンズ A 所見 7)。
snapshot として base `bb7753fa` と当時の main `a068b7f5` では実行器はともに blob `b1b1b374` だった。

## 段 5・6 へ渡す条件

- 実装面は Codex `role=author` が書く。親は直接編集しない (D95、I4)。
- 実装子は docs を編集せず commit もしない。
- レンズ B 所見 1 の must-fix (fixture を一律変更しない) は実装子の prompt に個別に明記する。

---

## 段 6 レビュー後の裁定訂正 (2026-08-25)

段 6 のレビュー 2 本が、上記のテスト設計に誤りを 2 件、実装の副作用を 1 件見つけた。親が再裁定する。

### 訂正 1 — divergence 負例の digest 基準は tip でなく main (レビュー A 所見 1、must-fix)

上の「テスト (確定)」節は「divergence 系テストでは旧 launcher 相当の **tip digest** を明示し、
拒否理由が digest 不一致でなく main/tip equality 違反であることを分離する」と書いた。**これは逆である。**
実装は受領証の `runner_executed_sha256` を **main 側 blob** と照合するため、tip digest を持つ受領証は
equality gate が消えても main digest 不一致で拒否される。つまり tip digest は equality の検出力を
消してしまう。

正しい設計は、`test_land_rejects_child_green_runner_blob_divergence` の受領証へ **main 側 digest** を
持たせることである。こうすると main/tip の blob が異なるまま digest だけは main と一致するため、
equality gate を外した変異 M2 だけが land を通り、テストが殺す。
非帰属側の divergence 負例は旧実装にも equality があったため、tip digest のままでよい。

### 訂正 2 — 過剰拒否の正例は locked_main と tested_main を区別できていない (レビュー A 所見 2、must-fix)

M5 (`land が tested_main でなく locked_main の実行器を引く`) の指定殺し手
`test_land_accepts_child_green_matching_main_and_tip_runner_blobs` は、fixture で
`locked_main == tested_main == repo.base` となるため、変異しても値が変わらず殺せない。
`locked_main != tested_main` で locked_main 側の実行器だけが異なる正例を用意し、
tested pair の受領証が受理されることと exact な lookup revision を固定する。

### 訂正 3 — 複合故障時の分類優先順位は変わる。新しい順序を意図として採る (レビュー B 所見 1)

runner 検査を共通部へ移した結果、非帰属判定で「実行器の divergence」と「判定器 lookup の rc=128」が
**同時に**起きた場合の分類が変わる。旧実装は一時的失敗を先に見て `retryable_same_request=True`、
新実装は divergence を先に見て `False` になる。上の「プラン v2」は「既存分類を保つ」と書いたので、
これは自分が凍結した指示との差である。

**親は新しい順序を採る。** 理由は、実行器の divergence は当該受領証について恒久的に成立するため、
再試行しても決して受理されないからである。旧順序は受理されえない request を再試行対象にし、
lease を保持し続ける。新順序は恒久拒否を先に確定し lease を解放する。受理集合はどちらでも同じ
(divergent 受領証は両方で拒否される) ので、規律 2 に反する緩和ではない。

代わりに**この挙動をテストで固定する**。非帰属判定で divergence と checker lookup rc=128 を同時に
注入し、`retryable_same_request=False` の恒久拒否になることを負例として置く。

### 訂正しない指摘

- main 側 object ID の SHA 形式再検査が恒真 (レビュー A 所見 5) — tip 側にも同型の既存検査があり、
  対称性のために残す。独立した gate としては数えない。
- 実 `_read_runner_blob` の Git 非ゼロ分岐と malformed `ls-tree` の未検査 (レビュー A 所見 7)、
  `del tip_source` (レビュー B 所見 4) — いずれも nit。本 wave の scope を広げない。
