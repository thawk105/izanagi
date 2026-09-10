# 段 4 裁定 — [T-678] 最終 publication 後の wall gate 再評価

親裁定。段 2 プラン (P1′) と段 3 レンズ A / B (ともに NO-GO) を突き合わせ、
real / refuted、採用 / 不採用、scope 内 / 外を確定する。

## 0. 依頼文言との差 — 最重要の裁定 (A8 / B-3)

**両レンズの主張は real。** 依頼「publication 完了後にも wall gate を再評価する」は、
receipt が create-only 公開である限り**字義どおりには実装できない**。final path が可視化された
瞬間に別 consumer が `accepted` を読めるため、その後の再評価は受理を取り消せない。
取り消せない再評価で process rc だけを変えれば「receipt=accepted かつ rc≠0」という
不変条件 3 違反を作る (親 brief P1 の論拠は維持)。

**裁定。** 本 wave は依頼を次へ**正式に縮約**して実装する。

> 最後の可逆点 — output publication、published output を含む audit、
> **公開する exact bytes の temp write + file fsync** をすべて終えた後、
> receipt final path の可視化直前 — で wall gate を再評価する。

縮約の意味は次の 2 点で、記録にそのまま書く。

- **塞げる区間** = 現行 gate (`:1739`) から exact bytes の fsync 完了まで。
  ここには従来 gate 外だった `_audit_receipt_value` と receipt の serialize / write / fsync が入る。
- **塞げない残余** = `os.link` / `os.replace` 自体、`_fsync_parent`、staged temp cleanup、
  receipt lock の unlock / close、`_run_supervised` の return から process 終了まで。
  レンズ A の指摘どおりこの残余は 10〜20 秒に限定されず**任意に長くなり得る**。

**「publication 完了後に塞いだ」とは書かない。** 字義どおりの保証が要るなら commit protocol の
再設計 (schema v3、2 段 receipt、または receipt の可視化と admission の分離) が必要で、
これは受理契約と consumer を変える設計択一なので **裁定パッケージ候補 S-A** としてユーザーへ返す
(`DW-S04`「scope 外の real 所見は実装せず裁定パッケージで返す」)。

## 1. 所見の裁定表

| ID | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| M1 (A) | 親 4 秒観測は狭い因果主張のみを支持し、10〜20 秒級・F57 原因へは一般化不可 | real | 採用 (主張を狭める) | 内 |
| B-2 | 同上 (F57 は複数 producer 混在、単独再走で非再現) | real | 採用 (主張を狭める) | 内 |
| A1 | P1′ は二度目の receipt temp write を消すため、I/O failure trace では受理集合が拡大する | real | 採用 (不変条件 1 を書き換え) | 内 |
| A2 / B-1 | 現行 `DW-O01` は raw `codex exec` で gate を通らない。効くのは dogfood と将来配線だけ | real | 採用 (記録の主張を限定) | 配線は外 → S-B |
| A3 | staged temp の所有契約が二義的 (helper / caller の二重所有) | real | 採用 (所有を一方へ固定) | 内 |
| A4 | atomic create 後の例外で `accepted receipt / rc=2 / output 不在` を構成できる | real・**既存欠陥** | 不採用 (本 wave では直さない) | 外 → S-C |
| A5 / B-6 | flip の output 削除に parent fsync が要る。例外 fallback の削除は durable でない | real | **採用** (正常 flip と fallback の両方に入れる) | 内 |
| A6 / B-4 | accepted 時の `actuals.wall_clock_s` は staging 前の値。late gate は checker から検証不能 | real | 採用 (意味を固定して記録、schema は変えない) | 内 |
| A6 補 | 親 brief の「actuals と limit が矛盾する」は**誤り** (checker は accepted の actuals>limit を拒否する) | real | **親 brief の当該主張を撤回** | 内 |
| A7 | 新規 2 node では順序・exact temp reuse・例外整合を固定しきれない | real | 一部採用 (node 2 を identity 検査へ、audit-delay node を追加) | 内 |
| B-5 | flip 以外の停止 (publication 例外・outer timeout) では診断が消える | real | 不採用 (本 wave では直さない) | 外 → S-D (既出 S5 と同族) |
| B-7 | `LAUNCHER.time.monotonic_ns` の monkeypatch は共有 module を汚す。正規 seam がない | real | **採用** (launcher 局所の clock seam を新設) | 内 |
| B-8 | 提案 2 node では publication gate の検出力を測れない | real | 採用 (下記の変異事前登録で再照準) | 内 |
| B-9 | 偽陽性率は現資料から見積もれない | real | 採用 (率を書かない。予算値は変えない) | 内 |
| C1 | `_atomic_publish` は output の rollback を持たない | real・既存欠陥 | 不採用 | 外 → S-E |
| C2 | KeyboardInterrupt / SystemExit で receipt rc と process rc が分離する | real・既存欠陥 | 不採用 | 外 → S-F |
| C3 | staged temp を Path で保持する間の置換窓 | real・理論 | 不採用 (同 UID 単一 writer 前提を明記) | 外 → S-G |

### A1 の裁定 (受理集合)

P1′ を**採用する**。ただし brief 不変条件 1 の「狭まるだけ」は**そのままでは偽**なので次へ置換する。

> 不変条件 1′: **publication I/O が成功した論理 job** の集合について、受理は狭まるだけとする。
> P1′ は receipt temp の二度目の write を除去するため、「一度目は成功し二度目だけが失敗する」
> という**冗長な失敗面**は消える。これは受理集合の拡大ではなく、同じ bytes を二度書く重複の解消と
> して意図的に受け入れる。記録にこの差を明記する。

理由: gate の目的は「実際に公開する bytes の write / fsync 費用を受理判断に含める」ことであり、
gate の後に同じ bytes をもう一度書く現行構造では目的が達成できない (P1 のままでは
「二度目の write だけが停滞する穴」が残る、というレンズ A・段 2 双方の指摘が一致)。

### A5 / B-6 の裁定 (durable cleanup)

正常 flip の output 削除に `_fsync_parent` を入れる。**加えて `_publish_launcher_error_receipt` の
output 削除にも入れる** — 本 wave は「accepted を取り消したら published output は残らない」を
テストで固定する。同じ削除を担う例外 fallback が durable でなければ、その不変条件は半分しか
真でない。1 行の追加で閉じるため in-scope とする。
*成果物影響:* これを入れないと、crash 後に「受理されなかった job の output が残る」状態が
残り得る。receipt (not_accepted / launcher_error、`output_sha256=null`) と filesystem 上の
output が矛盾し、成果物の採否判断が filesystem 側の残骸に依存する。

### A6 / B-4 の裁定 (記録の意味)

`wall_clock_scope` の literal と `schema_version=2` は**据え置く** (P2 採用)。
`actuals.wall_clock_s` は **receipt object 構築時点**の値であり、late admission gate が観測した
時刻とは別である、という事実を記録・docstring に明記する。late gate は self-asserted で
checker から独立検証できない。schema へ束縛するなら v3 の別裁定 (S-A に含める)。
*成果物影響:* 明記しないと、accepted receipt の低い wall 値を読んだ人間が「公開まで予算内だった」
と誤読する。

### B-7 の裁定 (clock seam)

production に launcher 局所の `_monotonic_ns()` 間接層を新設し、module 内の
`time.monotonic_ns()` 呼出しをこれ経由へ揃える。テストは `LAUNCHER._monotonic_ns` を差し替える。
共有 `time` module を patch しない (`DW-O14`: monkeypatch は最後の手段、正規 seam を先に探す)。
*成果物影響:* seam が無いと、gate のテストが同一 pytest worker の他テストの時刻を汚し、
新しいフレーク (F57 族の再生産) を作る。

### M1 / B-2 の裁定 (主張の縮約)

親実測 (4 秒 sleep) が支持するのは「`_stage_receipt_write` の費用が最終 admission に入らない」
という**局所的因果**だけである。次は**主張しない**。

- 実障害で 10〜20 秒級の停滞が起きる頻度・実在。
- F57 の原因がこの穴であること。F57 は launcher / git timeout / PBS walltime / 並行 wave 競合の
  複数 producer が混在し、本 wave はそれを閉じない。
- 「フレークが消えた」こと (S4 = [T-680] の別裁定事項)。

## 2. プラン v2 (実装する形)

段 2 プランの構造を採り、次を修正して確定する。

1. **helper 契約 (`tools/codex_worker_launch.py:445-484, 1625-1628`)**
   - `_stage_receipt_write` は fsync 済み temp の `Path` を返す (削除しない)。
   - `_atomic_create_json_reserved` は「呼出側が用意した fsync 済み temp を公開する」形へ変える。
   - **所有は helper が消費する側へ一本化する (A3)**: helper へ渡した時点で temp の所有権は
     helper へ移り、成功時も例外時も helper が後始末する。helper へ渡す前の例外だけ caller が
     `finally` で unlink する。docstring にこの一文を固定する。
   - `_atomic_create_json` は自分で temp を作って新 helper へ渡す (早期 launcher-error 経路の
     外部挙動は不変)。
2. **clock seam (B-7)**: `_monotonic_ns()` を新設し module 内を揃える。
3. **`_run_supervised` の順序 (`:1727-1762`)**
   - `outcome != "accepted"` の candidate: audit → stage → publish (再評価しない。理由は段 2 の
     「拒否理由の分類を変えない」を採用)。
   - accepted candidate: output 公開 → hash 照合 → `_audit_receipt_value(check_published_output=True)`
     → `_stage_receipt_write` (exact bytes の write + fsync) → **`_latch_final_job_limit`** →
     `attempts[-1]["accepted"]` がまだ真なら staged temp をそのまま公開して rc=0。
   - flip したら: staged temp を破棄 → published output を unlink → **output の親を `_fsync_parent`**
     → `output_published_by_run=False` → `_receipt` 再構築 → `_audit_receipt_value(False)` →
     再 staging → 公開 → rc=1。
   - flip 判定は `receipt["outcome"]` ではなく `attempts[-1]["accepted"]` を見る (段 2 の指摘どおり
     `_receipt` は attempts を深いコピーしない)。
   - 再評価は **1 回だけ** (P4)。`accepted=True → False` の単調遷移なので十分。
4. **fallback (`:1765-1798`)**: output unlink 後に `_fsync_parent` してから flag を false にする。
5. **schema・literal・truth table・closed field 集合は不変** (P2)。

## 3. テスト (プラン v2)

`orchestrator/tests/test_codex_worker_launch.py` へ次を追加する。既存 assert の期待値は変更しない。

| node | 固定する性質 | 変更前に赤である理由 |
|---|---|---|
| N1 `..._staging_wall_overrun_flips_to_not_accepted_and_removes_output` | staging 費用が gate に入り、flip が `not_accepted` / `max_wall_clock_s` / rc=1 / output 不在 / temp 残骸なし | 変更前は stage 後に latch が無く rc=0・accepted・output 残存 |
| N2 `..._audit_wall_overrun_flips_to_not_accepted` | published output を含む audit の費用も gate に入る (A7 の抜け道を塞ぐ) | 変更前は audit 後に latch が無い |
| N3 `..._accepted_publication_reuses_the_staged_receipt_temp` | stage が返した **同一 Path (inode)** がそのまま公開経路へ渡る | 変更前は stage の temp を捨てて公開時に別 temp を書く |
| N4 (正例・既存) `test_positive_p1_normal_job_is_accepted` | 予算内の正常経路は accepted / completed / rc=0 / output 存在のまま | 過剰拒否の検出用 (`DW-M01` の正例要件) |

- 遅延注入は `LAUNCHER._monotonic_ns` の差し替え (論理時計) で行い、実 sleep を使わない。
  外側 timeout 10 秒は据え置き、広げない。
- N3 は呼出回数でなく **Path / inode の同一性**を観測する (A7 の提案を採用)。
- 実 sleep による実時間対照は**親が段 6 で一時変異として実測**する (テストには入れない)。

## 4. 変異事前登録 (`DW-M01`)

production を変更する wave なので通常 matrix。単一理由性は grep で確認してから走らせる。

| ID | 変異位置 | 変異内容 | 期待赤 node | 単一理由性の根拠 |
|---|---|---|---|---|
| MT1 | `_run_supervised` の staging 後 `_latch_final_job_limit` 呼出し | 呼出しを削除 | N1, N2 | この gate を読む assert は新 node のみ |
| MT2 | `_stage_receipt_write` の返り値 | temp を削除して `None` 相当にし、公開時に新 temp を書く形へ戻す | N3 | temp identity を読む assert は N3 のみ |
| MT3 | flip 時の published output unlink | unlink を削除 | N1 (output 不在 assert) | output 不在を flip 文脈で読むのは N1 |
| MT4 | flip 時の `_receipt` 再構築 | 再構築せず staged accepted bytes を公開 | N1, N2 (outcome assert) | outcome flip を読むのは新 node |
| MT5 (正例) | `_latch_final_job_limit` の比較 | `>` を `>=` でなく常に真へ (過剰拒否) | N4 (既存正例) + 既存 accepted 群 | 承認外の過剰拒否を検出する正例 (`DW-M01`) |

## 5. 裁定パッケージ候補 (scope 外・ユーザーへ返す)

- **S-A**: create-only 制約下で「publication 完了後」の字義を満たすには commit protocol の再設計
  (schema v3 / 2 段 receipt / 可視化と admission の分離) が要る。要否と方式の裁定。
- **S-B**: `DW-O01` を launcher 経由へ集約するか ([T-665]/[T-662] の候補案 (a) と同一論点)。
  集約しない限り本 gate は dev-wave の採用集合に効かない。
- **S-C**: atomic create 後の例外 (`_fsync_parent` 失敗・lock unlock 失敗) で
  `accepted receipt / process rc=2` が併存しうる既存欠陥の扱い。
- **S-D**: publication 例外・outer timeout で失敗原因が receipt に残らない ([T-679] と同族)。
- **S-E**: `_atomic_publish` の output rollback 不在。
- **S-F**: KeyboardInterrupt / SystemExit で receipt rc と process rc が分離する。
- **S-G**: staged temp の置換窓 (同 UID 単一 writer 前提の明文化 or fd/inode 束縛)。

## 6. 撤回する親 brief の主張

- 「accepted receipt の `actuals.wall_clock_s` と limit が矛盾したまま通る」は**誤り**。
  checker は accepted receipt の `actuals.wall_clock_s > limit` を拒否する
  (`tools/codex_worker_launch.py:2105-2122`)。実際の欠陥は
  **staging / publication の時間が `actuals` に入っていない**ことである。
- 不変条件 1「受理集合は狭まるだけ」は不変条件 1′ (上記 A1) へ置換する。
- 依頼文言「publication 完了後」は §0 のとおり縮約する。
