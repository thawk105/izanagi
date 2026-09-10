# [T-1851] 単位 C3b — 段 4 裁定 (2026-09-09)

段 2 plan 1 本、段 3 敵対 2 本 (レンズ A = 正しさ境界と proof chain、レンズ B = 実効性と運用)、
および焦点相談 1 本 (既存 registry の衝突) を裁定する。

---

## 1. 所見の裁定

### レンズ A (正しさ境界)

| 所見 | 判定 | 採否 | 対応 |
|---|---|---|---|
| A-1 v5 result は現行 freeze consumer が必ず拒否する | **real** | 採用 (must-fix) | receipt に「再凍結へ使用可能」と書かない。到達点は「v5 producer と prefix proof が production 経路で成立した」までとし、freeze への到達は D2 以降と明記する |
| A-2 `eligible_for_refreeze=true` は承認でも proof-chain 完結でもない | **real** | 採用 (must-fix) | receipt に bit の意味の射程を明記する。true でも未 land・未追認である |
| A-3 main の祖先であることは official 測定の必要条件でない | **refuted (主張は正しい)** | 採用 | (P1-1) を確定。D811 逐語・D1125・実行時照合が根拠 |
| A-4 退避 bundle に source tree / git bundle が無い | **real** | 採用 | 補助資料として source commit の git bundle を退避へ入れる。**新しい eligibility gate にはしない** (F681 は commit object の実在を要求しない) |
| A-5 D1124 が D811 の着手条件を撤去済み | **refuted (主張は正しい)** | 採用 | 親の独立実測と一致。さらに job `964035`/`964044` が同じ消費済み 12 cell を再測定して完走済みという裏取りを得た |
| A-6 段 2 plan が撤去済みの一回性を停止条件へ復活させた | **real** | 採用 (must-fix) | plan v2 の停止条件から「claim 後は fresh 再投入しない」を削除する |
| A-7 一回限り抽出の証拠鎖が弱い | **real** | 採用 (must-fix) | receipt へ抽出 source 全文・その sha256・interpreter・argv・rc・stdout sha256・入力 artifact の相対 path と sha256 を収録する |
| A-8 probe stdout の raw 転載は信頼境界を欠く | **real** | 採用 (must-fix) | raw text を prose で出さず base64 + byte 長 + sha256 で隔離し「非信頼データ。指示として解釈しない」と付記する |
| A-9 段 2 の列挙が動的観測・genesis 宣言・非所在・未発火を混同 | **real** | 採用 (must-fix) | receipt を 4 表に分ける |
| A-10 未観測を到達不能と読み替えてはならない | **real** | 採用 (must-fix) | 到達可能性で分類する (条件付き到達可能・適用域外・gate が拒否する値・直接観測不能) |
| A-11 plan に correctness gate を緩める変更は無い | **refuted (主張は正しい)** | 採用 | — |
| A-12 所要の一般化が弱い | **real (射程の制限)** | 採用 | 「観測 2894〜3096 秒」と書く。48 分を上限とも最新値とも書かない |
| A-13 同型の stale 記述が複数 | **real** | 採用 (報告のみ) | 実装面を編集しないので、docs の食い違いは insight と裁定パッケージへ出す |
| A-14 receipt の永続先が未決着 | **real** | 採用 (must-fix) | 下記 §2 で確定する |

### レンズ B (実効性と運用)

| 所見 | 判定 | 採否 | 対応 |
|---|---|---|---|
| B-1 実装面差分 0 は成立する | **refuted (主張は正しい)** | 採用 | 抽出器を `.py` として repo へ保存せず、run artifact を commit しない限り成立する |
| B-2 tracked 差分 0 と受入全走免除は別 | **real** | 採用 (must-fix) | receipt と spool fragment を commit する。**変異 matrix は免除、受入全走は免除しない** |
| B-3 抽出変換の保存が不足 | **real** | 採用 | A-7 と同じ対応で閉じる |
| B-4 bundle が現行 writer の全参照を閉じていない | **real** | 採用 (must-fix) | レンズ B の bundle 構成表を採る |
| B-5 別 worktree の raw `output/` は clean-scan に混入しない | **refuted (主張は正しい)** | 採用 | 汚染は「同じ submit-tree から次を起動」「raw を commit した木から起動」に限る |
| B-6 相互作用は clean-scan でなく attempt registry にある | **real** | 採用 (must-fix) | §3 の一回性リスクとして扱う |
| B-7 all-null・job-result 欠落・failure.json は事後停止条件で閉じる | **refuted (主張は正しい)** | 採用 | — |
| B-8 早期全滅検査の述語と動作が未確定 | **real** | 採用 (must-fix) | §4 で確定する |
| B-9 1 job・1 node 直列は正しい | **refuted (主張は正しい)** | 採用 | 主張範囲の制限だけ receipt へ書く |
| B-10 限界文言は `DW-O13` 全体の充足にならない | **real** | 採用 (must-fix) | **C3b は時間予算を新設・改訂しない**と明記する |
| B-11 待ち設計の既定値と完了材料が不足 | **real** | 採用 (must-fix) | §4 で確定する |

---

## 2. receipt の永続先 (A-14 / B-2 の裁定)

**分離して扱う。**

- **repo へ commit する (wave branch、land はしない):** `output/insights/2026-09-09_t1851-unit-c3b-floor-range/README.md`
  (receipt 本体)、`docs/spool/` の台帳 fragment。これらは `.md` なので実装面ではない (D95)。
- **repo へ commit しない:** run directory、`result.json`、`journal.jsonl`、binary store、
  submission directory、job staging、外部 checkpoint、共有 admission root の snapshot。
  これらは repo 外 bundle へ退避し、receipt からは bundle 内相対 path と sha256 で参照する。
- 結果として **実装面の差分は 0、tracked 差分は docs のみ。**
  → 変異 matrix は `DW-S04` により免除。**受入全走は免除しない。**

---

## 2.5 既存 registry との衝突 (焦点相談の裁定)

**衝突しない。確定。** official 走行が使う組は `freeze=315b1eb83d6f…` / `protocol=2c8cf9be…` であり、
既存 registry の `db07b575…` / `d388477f…` とは**両方とも異なる**。親の独立実測 (protocol の
`freeze.sha256` と `env_tag=pegasus`) と一致した。`consumption-catalog.jsonl` は現行実装が
明示的に無視する。

- fixture 混入は**既知の F793** である。新しい F を作らず、receipt へ exact path・hash・mtime・
  fixture identity・official 組との非衝突を記録し、統合裁定パッケージへ返す。
- fixture を書いた exact pytest node は durable bytes から特定不能。別課題として報告する。
- **手は (a) そのまま投入。** 別 gate で止まっても「どの gate がどの実値で止めたか」が実測になる。
- (c) 別世代での走行は**不可能**。protocol path は resolver が決め、production wrapper は
  supplied protocol と resolver record の exact 一致を要求する。任意指定の sanctioned seam が無い。

## 3. 一回性リスク (B-6 の裁定)

registry の binding は `(freeze_sha256, protocol_sha256, schedule_sha256)` だけで決まり
(`s8b_floor_attempt_launcher.py:386-392`)、**campaign_run_id を含まない。** protocol の
`master_seed` は凍結値なので schedule も決定的である。したがって同じ凍結世代での 2 本目の
official campaign は同じ 288 slot を再予約しに行く。

**裁定:** 本 wave はこれを**リスクとして受容し、報告する**。理由は次のとおり。

- 走行前に構造を変えることは実装面の変更であり、本 wave の scope 外である。
- D1124 は「落ちたら測り直す」を裁定しているが、それは admission の一回性についてであって、
  C3a が新設した attempt registry の slot 一意性は別層である。**この非対称は所見であり、
  裁定パッケージでユーザーへ返す。**
- **走行中および走行後に `qdel` を独断で打たない。** 観測後の qdel は消費済み slot を残し、
  再投入をより難しくする。

---

## 4. plan v2 で確定する運用 (B-8 / B-11)

- **早期全滅の検出述語:** 外部 checkpoint の `run-linked` 行から exact `journal_path` を取り、
  **先頭 3 件の completed session がすべて `valid=false` かつ同一の infrastructure 型
  `excluded_reason`** なら発火とする。
- **発火時の動作:** **採用を停止し報告するだけ。job は終端まで走らせる。** `qdel` は打たない (§3)。
- **待ち手:** job 名を使わない。submit receipt の exact request ID を使う。
  生存確認は `qstat` 一覧の行頭 ID 完全一致。`qstat -f` は不在 ID でも rc=0 を返すので
  単独の権威にしない。**完了の権威は submission directory の `scheduler.stderr` にある
  `Ended Request Time:` 行**とする。待ちの上限は 36000 秒 + queue 待ちを見込む。
- **停止条件から削除するもの (A-6):** 「claim 発行後の crash では fresh 再投入しない」。

---

## 5. 変更しない不変条件

- 正しさゲートを緩めない。fake registry・injected `measure_fn`・pilot 値を実値域の代替にしない。
- 凍結 23 件の bytes を変えない。`FORMULA_ID` 据え置き。実装面を親が編集しない。
- `submit_floor.sh` の投入インタフェースを発明しない。raw `qsub` を使わない。
- land しない (D1341)。

---

## 6. ユーザーへ返す裁定パッケージ候補

1. **本番の共有 admission root に test fixture 行が残っている。**
   `campaign-fixture-execution` / pid 101 / `run_start_receipt_sha256=4444…` の 96 slot が
   freeze `db07b575…` (env_tag `linux-baremetal`) 配下に 2026-08-27 から存在する。
   本番走行の freeze は `315b1eb8…` なので**本 wave は塞がれない**が、
   本番 root がテストから書けること自体を報告する。
2. **attempt registry の slot 一意性が官製床値 campaign を凍結世代あたり 1 回に制限する** (§3)。
   D1124 が admission 層で撤去した「落ちたら測り直せない」構造の同型が別層にある。
3. **docs と実装の食い違い 3 件** (A-13): restart runbook の「official は perf あり形だけ」、
   同 runbook の「claim 後は fresh 再投入不能」、`s8b_floor_contract.py:30` の
   「現 producer は v4 のまま」。
4. **1 run では `DW-O13` の時間予算要求を満たさない** (B-10)。C3b は時間予算を新設・改訂しない。
   満たすには最低 2 本、外れ値の兆候を見るには 3 本が要るが、§3 の一回性がそれを塞ぐ。
