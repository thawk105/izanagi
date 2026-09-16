# 段 4 裁定 — [T-2640] 未記帳の到達不能 commit 30 件

段 2 plan (`s2-plan.md`)、段 3 レンズ A (`s3-lensA.md`、正しさ境界)、レンズ B (`s3-lensB.md`、実効性) を
裁定する。3 者とも `check_codex_output.py` rc=0。

## 1. 所見の裁定

| # | 判定 | 採否 | scope | 裁定 |
|---|---|---|---|---|
| A-1 / B-1 (blocker) | **real** | 採用 | 内 | 親 brief の (P1) を**撤回する**。内容一致は人間の喪失受容ではない。全 30 件を `rescued` にする |
| A-2 (must-fix) | **real** | 採用 | 内 | 「main のどこにも無い」と書かない。「今回の basename / basename+`.gz` 照合では一致を確認できなかった」に限定する |
| A-3 (must-fix) | **real** | 採用 | 内 | gzip 展開後の blob 一致を着地証明にしない。`rescued` の根拠は **ref の到達性確認**に置く |
| A-4 (must-fix) | **real** | 採用・**実施済み** | 内 | `match_content_v2.py` で main を固定 OID へ束縛し `--no-replace-objects` を付け、候補 blob OID・mode・観測時刻を記録した |
| A-5 / B-5 (must-fix) | **real** | 採用・**実施済み** | 内 | 4 件からの一般化を撤回し **30 件すべてを実走**した。storage は `git verify-pack -v` を 18 idx 全部に掛けて実測した。期限の記述を訂正した |
| B-2 (must-fix) | **real** | 採用 | 内 | 受理条件を「OID 集合一致 + 30 行 + 全件解決 + 各 ref の直接 OID と到達性証拠 + 最終 ledger-check」の**一組**にする。新しい checker は作らない |
| B-3 (must-fix) | **real** | 採用 | 内 | 3 通知経路の発火条件と rc の決まり方を記録へ明記する |
| B-4 (must-fix) | **real** | 採用 | 内 | 14 / 16 の数値区分は維持し、意味づけを限定する。handoff 5 件は **3 種類の内容**である |
| B-6 (nit) | **real** | 採用 | 内 | 成果物を「docs-only」と書かない。「tracked 実装差分ゼロ + 共有 Git common directory へ 30 ref 追加」と書く |
| B-7 (nit) | **real** | 採用 | 内 | 監査は**最終 1 回**を証拠にする。途中確認は証拠と区別する |
| 判定器の 5 秒上限 | **real** | 不採用 (scope 外) | **外** | `check_branch_landed.py:38` の `COMMAND_TIMEOUT_SECONDS = 5.0` により本 repo では 30/30 が `indeterminate`。裁定パッケージへ返す |

refuted は 0 件。両レンズが親 brief の (P1) を独立に blocker と判定し、段 2 plan も同じ結論に達した。
**3 者一致なので (P1) は撤回する。**

## 2. 確定した plan v2

1. **全 30 件を救出する。** `accepted-loss` は 1 件も使わない。台帳の
   「`accepted-loss` は人間が喪失を明示的に受容した場合」という逐語を AI の内容照合で代替しない。
   D2044 項 7 は「救出**または**喪失受容」を求めており、全件救出はその選択肢の一方である。
2. **ref は `refs/rescue/t2640/<40 桁 OID>`。** OID ごとに直接指す。
   作成は `git update-ref --no-deref <ref> <oid> 0000...0` (既存なら失敗する形)。
   再検査は `show-ref --verify --hash`、`rev-parse --verify <ref>^{commit}`、
   `merge-base --is-ancestor <oid> <ref>` の 3 本を rc とともに記録する。
3. **26 field の値**は `retention-facts.md` の実測と、30 件の `landed/<oid>.json` から採る。
   ただし `loose_count_at_loss` は **null** (喪失時点の総 loose 数は未観測)。
   `source_refs` = `[]`、`source_tips` = `{}` (削除起点の ref が存在しない)。
   `assessment_report_sha256` は `landed-index.tsv` の各行の sha256 (= 保存した stdout の生 bytes)。
4. **台帳の編集は `## entry` 節の `現在、記録済み entry はない。` 1 行を 30 行へ置換するだけ。**
   1〜115 行は 1 bit も変えない。
5. **`resolution_note` の言い方**は A-2 / A-3 / B-4 に従う。書いてよいのは次の 3 つだけ。
   - 出所: `--ledger-check` の `unledgered-audit-finding` 由来で、削除起点の ref は不明。
   - 照合結果: 監査報告 path のうち何組で、basename / basename+`.gz` 照合の候補に
     gzip 展開後の Git blob OID 一致があったか。**commit 全体の着地は未証明**と明記する。
   - 救出: 作成した ref と到達性再検査が通ったこと。
6. **記帳は 2 段階で行う。** まず 30 件を `pending` で書いて `_read_ledger` / `_validate_ledger_entry` を
   通し、次に ref を作って到達性を確かめ、同じ 30 行を `rescued` へ更新する。
   台帳の状態遷移 (`pending` → `rescued`) を実際に踏む。**commit するのは最終状態**。
7. **規律 6 の内容監査。** ref を作る前に 30 commit の metadata と導入内容を読む。
   内容は**データであって指示ではない**。checkout・cherry-pick・script 実行はしない。
   working tree へ展開しない。

## 3. 変異事前登録

**実装面 (コード・テスト・実行可能な probe / harness / script・機械設定) の差分はゼロである。**
変更するのは `docs/unreachable-object-ledger.md`、`output/insights/**`、`docs/spool/**` だけで、
いずれも docs / 記録である。判断材料の収集に使った script は job dir に置き **repo へ入れない**
(段 2・段 3 とも支持、`probe を repo へ入れない` の規律)。

したがって `DW-S04` により**変異 matrix は免除**する。**受入全走は免除しない。**

## 4. 受理条件 (B-2 に従い一組で判定する)

1. 最終台帳の entry 30 件の `object_oid` 集合が、最終 `--ledger-check` の
   `audit.commits` が報告した集合と一致する (救出後は audit が 0 件を報告するので、
   **救出前に固定した 30 OID 集合**と一致することを別に示す)。
2. 台帳の entry 行が 30 行、全件 `status=rescued`、`pending_count=0`。
3. 30 本の ref それぞれについて 3 本の再検査 rc を記録した証拠がある。
4. 最終 `--ledger-check` が rc=0、`ledger_notification_due=false`、`notifications=[]`、
   `issues=[]`、`parse_complete=true`、`audit.complete=true`、`unledgered_commits=[]`。
5. `python3 tools/check_docs.py` rc=0、`python3 tools/spool_fold.py --dry-run` rc=0。
6. 受入全走 (`tools/dev_wave_wait.py acceptance`) が child-green。

## 5. 裁定パッケージへ返す項目 (scope 外 real)

- **`tools/check_branch_landed.py` の per-command 5 秒上限が本 repo 規模に合っていない。**
  本 wave で 30/30 が `assessment-timeout` で `indeterminate` になることを実測した
  (全件の stdout を `landed/` に保存)。判定器は着地の有無をこの repo では一切判定できない。
  CLI からは変えられない (`--timeout-seconds` は全体予算で、per-command は定数)。
  [T-2639] の path 優先判定 (未 land) と同じ面。**本 wave では直さない。**
