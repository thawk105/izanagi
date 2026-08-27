# 段 4 裁定 — [T-1675]

親が段 2 プランと段 3 の 2 レンズを real/refuted・採用/不採用・scope 内外に裁定する。

## 0. 親自身の誤りの訂正

段 1 brief は `test_s8b_holdout_freeze.py:1599, :1959` を「承認 loader の既存負例」と書いた。
これは誤りで、両者は pin を `None` にする pin-gate の負例であり `_load_budget_approval` へ到達しない
(レンズ A 所見 5 前半 = real)。ただしレンズ A の後半「同 loader を直接対象にした既存テストが
見当たらない」は refuted である。`test_v2_candidate_budget_approval_compares_canonical_numeric_bytes`
(:1909-1926) と negative-zero の parametrize (:1928-1950) は pin を fixture の実 hash に設定して
loader を通過し、canonical 比較と `_validate_budget` へ到達する。親が実測して確認した。

## 1. 停止級の裁定 — `ratify` は実装しない

**real・採用・実装しない。** 段 2 プランの中核である ratify CLI (承認 JSON の発行、pin 定数の
書き換え、TTY からの承認者入力) は、次の既裁定と正面から衝突する。

- **D287 (2026-08-11、本 pin を作った wave 自身の裁定、未 supersede):**
  「approval を発行する CLI・API・`--approver` 引数・既定補完は作らない。」
  「pinned literal なら、AI が承認者になるには人間がコード diff をレビューして定数を置くしかない。」
- **D526:** 批准台帳に「追記 API・CLI・自動更新処理を作らない」。
  「批准値を持つ台帳を wave 側で作って land する — 弱化した本人が批准する形になる」を却下。
- **D883 / D905 (ユーザー裁定):** 批准の執行は「AI が成りすませない実行主体の新設」だけを採る。
  平文承認へ移す案は却下済み。「設計が着地するまで批准は進めない。」

TTY 案は D905 が却下した平文承認そのものである。レンズ A が独立に同じ結論へ到達した
(所見 1「TTY は人間性の防壁になっていない」「fake TTY 正例は、むしろプログラムが承認者を
供給できることを実証する設計」)。親はこれを real と裁定する。

**成果物影響:** ratify を実装すると、承認の主体が「人間の reviewed diff」から「TTY を操作した
主体」へ移る。approval の `approver`・予算値・`approved_at`・approval hash・source pin が
AI の操作で確定しうるようになり、D1161 の「AI は自分を承認者にしない」が機械的に破れる。

これは scope 外の real 所見なので実装せず、裁定パッケージでユーザーへ返す (DW-S04)。

## 2. 到達性の裁定 — 「1 コマンド後に builder が通る」は本 wave では到達不能

**real・採用。** レンズ B の端から端の検査と親の実測が一致した。

- `output/env/*/calibration/s8b-floor-official/` は現物に存在しない (親が実測)。
  `build_v2_g1_candidate` は official path 規約を満たす eligible な `result.json` と、同一 run の
  `manifest.json` / `journal.jsonl` / build admission / 統計整合 / `eligible_for_refreeze=true` を
  要求する。
- `BUDGET_APPROVAL_REL` の consumer は `build_v2_g1_candidate` **ただ 1 つ**である。
  `s8b_floor_campaign.py` / `s8b_budget.py` / `s8b_oracle_driver.py` は承認 artifact を読まない
  (親が実測、grep で 0 件)。承認は official floor campaign の**起動**を塞いでいるのではなく、
  official 実行後の**再凍結 candidate 生成**で消費される。
- レンズ B 所見 3 (real): ratify 直後は producer source が HEAD と食い違う一方、candidate の
  `generator` は captured HEAD blob から作られるため、実際に実行した pin 設定済み source と
  記録が食い違う。これは「1 コマンド直後に安全に通る」と両立しない。

**裁定:** 依頼文と D1161 の「残る閂は承認 1 件」は、承認が**ユーザーが負う最後の判断**である
という意味では正しい。しかし機構としては、承認だけで v2 candidate が通るわけではない。
この差は worklog と裁定パッケージに正直に書く。実装で埋めない。

## 3. 数値の裁定 — 現時点の推奨は保留、AI は数値を確定しない

**real・採用。** 両レンズと T-986 dossier が一致する。D964 (staged 運搬)、D979 (生涯観測上限)、
D926 (official nonce 束縛) はいずれも 2592/1296 も 2400/1200 も承認していない。
dossier は保留判断に必要な情報を持つが、正の operational approval を支持する根拠は持たない。

**裁定:** AI は推奨値を数値として出さない。根拠・限界・択一を読める形にするところまでを作る。

## 4. 本 wave の実装 scope (縮小して確定)

D287 に適合し、かつ D1161 の「AI が起草してユーザーが確認する」半分を実際に前進させる部分だけを
実装する。次の 2 単位を Codex `role=author` が書く (D95)。親は実装面を直接編集しない。

### 単位 A — `tools/s8b_budget_approval_preflight.py` (新規)

**発行しない。書き込まない。検証と表示だけを行う。**

- `skeleton` 副命令: 承認 JSON の骨組みを **repo 外の `--out`** へ create-only で出す。
  `approver` と `approved_at` と `budget` の値を**持たない**。数値も持たない。
  これが D1161 の「AI が起草する」に当たる。
- `verify --candidate <path>` 副命令: **人間が書いた**承認 JSON を読み、
  `_load_budget_approval` が課す全条件 (exact key 集合、canonical bytes 一致、固定 scope、
  非空 approver、canonical UTC timestamp、`_validate_budget`、holdout 集合の完全一致) を
  検証し、通れば raw の sha256 と、pin 行の逐語を**表示するだけ**にする。
  file を書かず、canonical path へ触らず、production 定数を書き換えない。
- `--approver` 引数を持たない (D287 が名指しで禁止)。承認者の既定補完もしない。
- 承認者・予算値を argv・環境変数・git config・active v1 の `confirmed_by`・skeleton から
  取得する経路を持たない。

### 単位 B — `orchestrator/tests/test_s8b_budget_approval_preflight.py` (新規)

依頼された 2 つの負例を、恒真にならない形で固定する。

- **N1 (AI が承認者欄を埋めない):** tool の argv 面と実装に承認者を供給する入力源が
  存在しないことを固定する。`--approver` 系の option が argparse に無いこと、
  skeleton 出力が `approver` key を持たないこと、環境変数・git config・v1 の `confirmed_by` を
  読む経路が無いことを検査する。
- **N2 (草案だけでは gate が開かない):** skeleton 出力を canonical path へ置き、
  その正しい sha256 を pin に与えても `_load_budget_approval` が拒否することを固定する。
  **ただしレンズ A 所見 6 (real) のとおりこれは過剰決定である** — key 検査だけを外しても
  approver / timestamp / budget 検査が拒否する。したがって
  **単一理由の gate として主張せず、契約テストとして記録する** (DW-M03)。
- `verify` が canonical path・source・repo 内の何も変更しないことを、実行前後の bytes 比較で固定する。
- **レンズ B 所見 5 (real・採用):** 新規 test file は
  `test_every_test_file_is_self_runnable_or_allowlisted` の母集合に入る。
  self-runner を付けるか `orchestrator/tests/README.md` の allowlist へ登録する。
  これを欠くと全テストが赤になる。

### 単位 C — docs (親が書く)

`docs/s8b-budget-approval-user-turn.md` に、順序・根拠・限界・ユーザー手番の内容を書く。
2592/1296・2400/1200 を copy-ready な command として書かない。

## 5. 採用しなかった所見

- レンズ A 所見 4 (approved_at の発行前検証欠落)・所見 7 (承認者 fallback の個別負例)・
  所見 8 (anchor 負例の HEAD drift): いずれも ratify を前提とする。ratify を実装しないため moot。
  裁定パッケージの添付資料として残す。
- レンズ B 所見 6 (要確認、`python3.10` と import bootstrap): 単位 A の実装子契約へ入れる。
  Pegasus 実行を前提にする記述は docs に書くが、本 tool は login node 前提とする。
- レンズ B 所見 4 (fixture が CLI から builder までを接続しない): ratify を実装しないため
  接続すべき production 配線が無い。moot。

## 6. 変異事前登録 (DW-M01)

実装面の差分があるため変異 matrix は免除されない。単一理由性を確認できたものだけ登録する。

| ID | 変異位置 | 期待 | 単一理由性の根拠 |
|---|---|---|---|
| MU-1 | `verify` の canonical bytes 一致検査を素通しへ反転 | KILLED | 他層に同じ入力を拒否する検査が無い (loader は別 process。tool 内の唯一の判定点) |
| MU-2 | `verify` の scope 固定値比較を素通しへ反転 | KILLED | 同上 |
| MU-3 | `verify` の holdout 集合完全一致を部分一致へ緩める | KILLED | 同上 |
| MU-4 | `skeleton` の出力先 repo 外制約を外す | KILLED | 配置 gate はここだけ |
| MU-5 | `skeleton` の出力へ `approver` key を追加 | KILLED | N1 が唯一の判定点 |
| MU-6 | `verify` を write する形へ変える (canonical path へ出力) | KILLED | 無変更検査が唯一の判定点 |

**登録しない (過剰決定のため):** N2 の draft-loader 経路 (レンズ A 所見 6)、
`_validate_budget` 側の数値・holdout 検査 (loader が同じ入力を拒否する。レンズ A の恒真表と一致)。

## 7. ユーザーへ返す裁定パッケージ

段 9 の報告に添える。実装しない。

1. **承認 bytes を誰が置くか。** D287 は「人間がコード diff をレビューして定数を置く」を要求し、
   D758 決定 2 と D905 は「行の貼り付け・コマンドの実行を人間手番に置く設計は採らない」と
   している。前者は本 pin の固有裁定、後者は enforcement closure 批准の裁定であり、射程が違う。
   本 wave は D287 を優先して preflight までに留めた。
   択一: (a) D287 を本 pin について維持する (現状の実装)、
   (b) D905 の「成りすませない実行主体」を本 pin へも設計する別 wave を起こす。
2. **予算数値。** 保留 / 2592・1296 / 2400・1200。現証拠の推奨は保留。
3. **順序。** 承認は official floor campaign の起動を塞いでいない。
   official 実行 → 承認 → v2 candidate の順で使われる。承認を先に確定する必要があるか。
