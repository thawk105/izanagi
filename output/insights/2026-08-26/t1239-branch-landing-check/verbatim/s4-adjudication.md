# 段 4 裁定 — [T-1239]

base main は wave 中に c83b5b2c → **a068b7f5** へ前進した (親が `git reflog show main` で実測)。
裁定 inbox を再走査したが [T-1239] の裁定文に更新は無い (worklog はローテーションし、
現在は 4 箇所すべて番号だけの持ち越し)。

## 親が実データで裏取りした所見 (real 確定)

| 所見 | レンズ | 親の実測 |
|---|---|---|
| receipt 不在は未着地の証拠にならない | sol + luna | **real**。`roadmap-workload-hint` の decisions fragment は FOLDED.md に無いが本文は D568 として着地済み。fold 前に別 wave 名へ `git mv` され whole-file sha が変わったため (F82 の 4 度目に記録あり)。今 fold すると D568 が二重採番される |
| `git cherry` が merge commit を落とす | sol | **real**。`git rev-list <b> --not main` と `git cherry` の行数が 4 本で食い違う。t1484 (2 対 1)、t1458 (2 対 1)、unitB/C (4 対 2) |
| tip の net tree は中間 commit の固有内容を落とす | sol | **real** (機序として)。上記 4 本が merge を持つ以上、tip 比較だけでは削除で失う内容を測れない |
| P4 の本数が誤り | luna | **real**。`.codex/worktrees/` は 15 本で detached は 11 本。brief の「detached 15 本」は親の誤り |
| 検査中に main が動く | luna | **real**。c83b5b2c → a068b7f5 |
| 逐語 subsequence でも偽陽性を作れる | sol | **real** (反例が構成的)。親は反例を実行していないが、重複節の例は論理的に成立する |

## 裁定 — 採用 (scope 内)

**A1. 判定対象を「tip の net 差分」から「branch 削除で失われる commit closure」へ変える。**
`git rev-list <branch> --not <main>` の全 commit を列挙し、各 commit が
**全ての親に対して**導入した tree entry の状態を証明対象にする。
merge commit も対象に含める。closure が空でない branch を net-empty だけで `landed` にしない。
成果物影響: これを入れないと、判定表が `landed` と書いた branch を削除したとき
中間 commit の固有内容が台帳に残らないまま到達不能になる。

**A2. 逐語照合を `landed` の十分条件から外す。**
sol が「最も安全」とした選択肢を採る。逐語層は `observations` へ記録するだけとし、
verdict を `landed` へ動かさない。exact blob 一致だけを内容の十分条件とする。
成果物影響: これを入れないと、重複した節・頻出行を持つ file で偽 `landed` が出て
削除候補一覧へ混入する。

**A3. receipt 不在は `not-landed` にせず `indeterminate` にする。**
そのうえで非決定の `ledger_probe` 層を足す — fragment の frontmatter を除いた本文から
構造単位を取り、`docs/worklog.md` / `docs/decisions.md` / `docs/failures.md` /
`docs/phase3.md` / `docs/archive/` を検索して hit 数と hit 先を `observations` へ載せる。
**この層は verdict を動かさない。** 完全な本文比較器 (re-home 追跡・placeholder 採番の
canonical 化) は scope 外とし裁定パッケージへ回す。
成果物影響: これを入れないと、着地済み fragment 3 本を未 fold 一覧へ再投入し、
D568 を二重採番する。

**A4. 証明単位を `(path, mode, object type, oid)` の同時状態にする。**
別々の main commit から mode と blob を独立に拾って合成しない。
成果物影響: これを入れないと、実行権限や submodule pointer が着地していない branch を
`landed` と誤判定する。

**A5. `not-landed` は closed-world の負証拠がある場合だけ返す。**
列挙・履歴探索が打ち切られていないことを確認し、打ち切り・timeout・上限超過・parse 不能・
shallow・replace ref・ref 移動はすべて `indeterminate` に倒す。
同一 path の exact blob 不一致だけを未着地の証拠にしない (別 path への移植を排除できない)。
成果物影響: これを入れないと、移植・rename で着地した内容を未着地と報告し、
回収対象と台帳件数を過大にする。

**A6. JSON へ判定の射程を明示する。**
`assessment_scope: "D720-condition-1-only"`、`condition2: {"status": "not-checked"}`、
`land_authorized: false` を必須 field にする。
各層の outcome は `matched` / `not-matched` / `not-applicable` / `not-run` / `error` /
`truncated` を分離する。`changed_files` が確定できないときは `null` と `files_enumerated: false`。
`git cherry` の行数が closure の commit 数より少ない場合は
`patch_id.status` を `complete` にせず、落ちた merge 数を出す。
成果物影響: これを入れないと、「検査していない」が「検査して問題なし」と読まれ、
条件 2 未検査のまま回収 land へ進む。

**A7. 補助証拠の名前を `observations` にする。** `auxiliary_evidence` は verdict と誤読される。
task ID 検索の対象へ `docs/failures.md` と `docs/phase3.md` を足す。
task ID hit は単独で verdict を動かさない (P3 は維持)。
成果物影響: 誤読による削除判断を減らす。判定値そのものは変わらない。

**A8. 履歴走査の実測を JSON へ出す。** 「候補上限」と「走査量上限」を別概念として持ち、
走査時間と候補数を記録する。親の「1 秒未満」観測を一般則にしない。
成果物影響: 判定表の `indeterminate` がどこで増えたかを後から説明できる。

## 裁定 — 不採用 / scope 外 (裁定パッケージへ)

**B1. `/cleanup-branches` への配線と非祖先 branch の削除経路 (luna blocker 2)。**
real だが **実装しない。** ユーザー裁定が「branch の削除はユーザー指示があるときだけ」と
明示しており、`ahead=0 のみ削除`を`checker=landed でも削除`へ広げるのは削除権限の拡大にあたる。
`.claude/commands/cleanup-branches.md` は 3,949 bytes で上限 3,983 まで残り 34 bytes しかなく、
入口へは入らない。**裁定パッケージ**として、expected-tip CAS を伴う削除経路の可否を返す。

**B2. 完全な fragment 本文比較器 (re-home 追跡・canonical 化)。**
A3 の非決定 probe で当面の実害は防げる。決定的な比較器は schema と canonical 化の設計が要り、
本 wave の scope を超える。**裁定パッケージ**。

**B3. originless baseline 型の semantic comparator。**
`indeterminate` に残す方針を維持する。「生成物らしいものを除外する」一般則は
都合の悪い file を外す抜け道になるので作らない。**裁定パッケージ**。

**B4. D720 条件 2 の機械化。** 本 wave では手動監査必須を維持する。**裁定パッケージ**。

## P1〜P4 の確定

- **P1 (3 値) — 維持。** 両レンズが同意。
- **P2 — 改訂。** branch 単位の連言は維持。file 単位の無条件選言は**撤回**し、
  変更の種類ごとの証明規則 (A2・A4) に置き換える。判定対象は A1 により commit closure。
- **P3 — 維持。** task ID hit は verdict を動かさない。検索範囲だけ A7 で広げる。
- **P4 — 撤回して書き直す。** 本数が誤りだった。新 P4:
  **`.codex/worktrees/` の detached HEAD child 11 本 (`t1563-fix1〜7` / `t1563-unit-a/b`) を
  撤去候補とする。** 撤去前に 1 本ずつ (a) 占有 rc=0、(b) HEAD commit が
  `refs/heads/main` から到達可能、(c) lock 理由が空、(d) directory mtime が 1 時間以上前 —
  の 4 点を測り直す。(b) が成立しないものは残す (detached HEAD は唯一の到達根になりうる)。
  branch 付きの `.codex` 4 本と `.claude` の無署名 lock 2 本は**触らない**。

## 変異事前登録 (B-057、DW-M01)

実装前に登録する。各変異は判定式を 1 箇所だけ持つ形へ実装させ、前後に同じ入力を拒否する層を
置かないことを実装後に親が確認する。全件 KILLED を期待する。

| # | 変異 (無効化する規則) | 期待赤の単一理由 |
|---|---|---|
| M1 | receipt 不在で `indeterminate` を返す → `not-landed` を返す | re-home 済み fragment の判定が `not-landed` になる |
| M2 | 逐語層を非決定にする → `landed` の十分条件に戻す | 重複節の負の対照が `landed` になる |
| M3 | commit closure を監査する → tip の net 差分だけ見る | 中間 blob 消失の負の対照が `landed` になる |
| M4 | merge commit を closure へ含める → `git cherry` の行だけ見る | merge-only 負の対照が `landed` になる |
| M5 | `(mode, oid)` を同時要求 → 独立に合成 | mode/content 分離の負の対照が `landed` になる |
| M6 | 打ち切り時に `indeterminate` → `not-landed` を返す | 候補上限超過の case が `not-landed` になる |
| M7 | `assessment_scope` / `condition2` / `land_authorized` を出す → 落とす | schema test が赤 |
| M8 | blob 一致で path を要求 → 任意 path の一致を許す | 同一 blob 別 path の負の対照が `landed` になる |
| M9 | 開始・終了で ref を再取得 → 再取得しない | ref 移動 case が `indeterminate` にならない |
| M10 | branch 合成で `indeterminate` を伝播 → `landed` を優先 | 合成 test が赤 |

`DW-M08` に従い期待 node は完全集合で登録する。実装後に親が実 node を採取して確定させる。
テスト強化だけの wave ではないため新旧両走の登録は不要。

## 段 5 の分割

実装単位は 1 本。`tools/check_branch_landed.py` と
`orchestrator/tests/test_check_branch_landed.py` は同じ受理集合を定義するため素集合に分けられない。
