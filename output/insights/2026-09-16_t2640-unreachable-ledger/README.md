# [T-2640] 未記帳の到達不能 commit 30 件を記帳し、全件を救出した

`docs/decisions.md` D2044 項 7 (2026-09-16 ユーザー裁定) の実施記録。
裁定の逐語は「未記帳の到達不能 commit 30 件を既存 schema で記帳し、救出または喪失受容を具体的に
判断する。台帳契約は変えない。」

## 結論

**30 件すべてを救出した。`accepted-loss` は 1 件も使っていない。**

`docs/unreachable-object-ledger.md` の `## entry` 節へ 30 件の entry を追記し、
すべて `status=rescued`、`rescue_ref=refs/rescue/t2640/<40 桁 OID>` とした。
台帳契約 (1〜115 行) は 1 bit も変えていない。

救出後、監査は**要確認の到達不能変更を 0 件**と報告する。`--ledger-check` は rc=0 を返し、
`ledger_notification_due=false`、`notifications=[]`、`issues=[]` になった。
常時 due だった通知は止まった。

## なぜ全件救出か (`accepted-loss` を使わなかった理由)

親の段 1 brief は「内容が main に完全一致で残っている 16 件は `accepted-loss` にする」を
provisional 裁定としていた。**段 2 plan と段 3 の敵対 2 レンズが独立に blocker と判定し、撤回した。**

台帳 (`docs/unreachable-object-ledger.md`) は `accepted-loss` を
「**人間が喪失を明示的に受容した場合**」と定める。D2044 項 7 は AI へ具体的判断を命じるが、
当該 16 OID についての喪失受容文ではない。理由文も「旧 wave の spec という類型だけで個々の
喪失受容を代替できない」と述べている。内容照合の結果を人間の受容へ読み替えることは、
裁定の拡大解釈である。

**全件救出は D2044 項 7 の「救出または喪失受容」の一方であり、追加の承認待ちを作らずに閉じられる。**
代償も小さい — 30 件の ref が恒久的に延命する object は `git rev-list --objects <30 OID> --not --all`
の実測で **322 個 (commit 40 本)** だけである (repo は in-pack 171,779 + loose 4,616)。

## 何が起きていたのか

監査は「到達不能 commit が導入した path が main と全 local branch tip に不在」を要確認として報告する。
30 件はすべて 8〜9 月の旧 wave の記録 commit で、**main 側の insight 配置が 2 度変わったために
path 一致では不在に見えていた**。

1. dir 再編: `output/insights/<日付>_<task>/` → `output/insights/<日付>/<task>/`
2. gzip 圧縮: `114c5c4dfc8e` (`[T-201] output/insights/ の tracked bytes を gzip 圧縮で削減した`)
   が `.json` を `.json.gz` へ置き換えた

このため、53 組の (commit, path) のうち **37 組は main に内容が残っている** — ただし
**直接一致は 0 組で、37 組すべてが gzip 展開後の Git blob OID 一致**である。

## 30 件という集合は 3 経路で一致した

1. `audit_dangling_commits.py` 単独 (repo 外走査なし) — rc=1、85.194 秒、30 commit / 53 pair。
2. `check_branch_rescue.py --ledger-check` の `unledgered_commits` — 30 件。集合は 1 と完全一致。
3. `audit_dangling_commits.py --offrepo-root <dev-wave-jobs>` — **3708.671 秒**かけて
   repo 外 15 万 dir / 85 万 file を走査し、**抑止 0 件、findings 30**。
   repo 外に同一実体があっても報告は減らなかった。

3 の所要は同 tool の所要上限 300 秒を 12 倍超過している (上限超過は開示されるが rc には混ざらない)。
`/cleanup-branches` がこの形を毎回要求する以上、実運用では重い。

## 30 件 (`保全` = 監査報告 path のうち候補集合内で blob OID 一致を確認できた数)

| oid (先頭 12) | commit 日 | 保存形態 | 保全 | 件名 |
|---|---|---|---|---|
| `c5d79e7050fe` | 2026-08-11 | packed | 3/3 | docs(t657): 段 0 裁定実施 wave の記録を凍結する |
| `f1feb592af5b` | 2026-08-11 | packed | 1/1 | docs(t817): 実測で裁定の前提が覆ったので実装せず再裁定へ返す |
| `1aa5ae77aa86` | 2026-08-11 | packed | 0/1 | test(mutation): [T-812] 受入 lease 自己保持の変異 spec を事前登録する |
| `c3e2218c383e` | 2026-08-11 | packed | 0/1 | test(mutation): [T-812] 受入 lease 自己保持の変異 spec を事前登録する |
| `accabf0b5d9e` | 2026-08-12 | packed | 2/2 | docs(t930): 保留の迂回封鎖を記録し、裁定 fragment を相乗りさせる |
| `6902920cdf39` | 2026-08-16 | packed | 1/1 | docs(t1109): 変異を最終 commit で再走した結果へ更新する |
| `4a62da8c3c33` | 2026-08-16 | packed | 3/3 | [T-1155] / [T-1178] wave の記録 |
| `4c2b48059154` | 2026-08-17 | packed | 4/4 | docs(t1250): 第 4 世代の変異台帳・逐語・台帳 fragment を記録する |
| `66dccb28fedc` | 2026-08-17 | packed | 1/1 | untracked files on worktree-dev-wave-t190-failure-artifact (stash) |
| `e0a80472fb37` | 2026-08-17 | packed | 0/1 | [T-1262] 変異事前登録と材料レポートを置く |
| `2620635f7488` | 2026-08-17 | packed | 1/1 | [T-1262] 変異結果と台帳 fragment を記録する |
| `cd066a0487af` | 2026-08-18 | packed | 7/7 | docs(s8b): [T-1086] の記録 |
| `0decf0a4eae5` | 2026-08-18 | packed | 1/1 | docs(s8c): [T-1348] 変異 spec (probe) と段 1-6 の逐語を記録する |
| `aab5adbbcb59` | 2026-08-18 | packed | 3/3 | docs(s8c): [T-1348] C09 / C10 consumer 配線の記録 |
| `2f5b2c1773e9` | 2026-08-18 | packed | 1/1 | docs(s8c): [T-1348] 変異 spec (probe) と段 1-6 の逐語を記録する |
| `3905db91ed81` | 2026-08-18 | packed | 3/3 | docs(s8c): [T-1348] C09 / C10 consumer 配線の記録 |
| `0b92c254b830` | 2026-08-18 | packed | 1/1 | docs(s8c): [T-1348] 変異 spec (probe) と段 1-6 の逐語を記録する |
| `2ba0ade14cdd` | 2026-08-18 | packed | 3/3 | docs(s8c): [T-1348] C09 / C10 consumer 配線の記録 |
| `cbd9d812141f` | 2026-08-19 | packed | 2/2 | feat(s8c): [T-1379] 条件 5 (C05) を machine_checkable へ昇格する |
| `cb0d93052593` | 2026-08-21 | packed | 0/1 | feat(pegasus): enable AI-driven rr20 rr80 calibration registration |
| `8c2e4e3f8ed8` | 2026-08-21 | packed | 0/1 | 同上 |
| `c0439777fcf2` | 2026-08-21 | packed | 0/1 | 同上 |
| `5b3ff770ddf2` | 2026-08-21 | packed | 0/1 | 同上 |
| `c7a57d642fe7` | 2026-08-21 | packed | 0/1 | 同上 |
| `3ea6ed742860` | 2026-08-26 | packed | 0/1 | 受入全走の結果を記録する |
| `75d55ccd8d19` | 2026-09-08 | packed | 0/1 | [T-2265] 段 7 記録 |
| `1d41c41714b6` | 2026-09-09 | loose | 0/1 | docs: 中断した worktree delta manifest wave の実測を残す |
| `f181f703d1d6` | 2026-09-09 | loose | 0/1 | docs(t2487): [T-2487] 段 1 の実測だけを残して wave を中断する |
| `c656d831e30e` | 2026-09-09 | loose | 0/3 | docs(lock-audit): 理由なし worktree lock 133 本の所有者証拠 |
| `54d4dd9b3eb2` | 2026-09-09 | loose | 0/1 | docs(t2487): [T-2487] 段 1 の実測だけを残して wave を中断する |

保全 16 件 / 未保全を含む 14 件。**この区分は解決 status を分けていない。全件を救出した。**

未保全 16 組の内訳は、同一 handoff file `docs/handoff/2026-08-21-rulings-calibration-main-land.md`
が 5 commit (**内容は 3 種類**: blob `64281f…` / `a83bfd…` / `8c44a8…`)、`[T-812]` の変異 spec が
2 commit (互いにも `.gz` とも不一致)、`[T-2487]` の中断記録が 2 commit、lock 監査が 3 組、
その他が各 1 組である。

## この照合が言えること・言えないこと

- **言える:** 監査が報告した path について、main `d97c423bdd14e0b416cb4f585d350e6c2b251287` の
  basename または basename + `.gz` の候補集合に、gzip 展開後の Git blob OID 一致があったか。
- **言えない:** commit 全体が main へ着地したこと。別 basename への改名。mode / object type の同一性。
  探索範囲外に同一内容が在るか否か。
- したがって `assessment_verdict` は実測どおり全件 `indeterminate` であり、
  `resolution_note` も「一致を確認できた / できなかった」に留めている。
  **内容照合を `landed` の代用にしていない。**

## 判定器は本 repo では判定できない

`tools/check_branch_landed.py` を 30 件すべてに実走した (`evidence/landed-index.tsv`、
生 stdout は job dir に全件保存)。**30/30 が rc=2 = `indeterminate`、reason は `assessment-timeout`、
issue は `git command timed out: log`。** 原因は同 file の `COMMAND_TIMEOUT_SECONDS = 5.0` で、
CLI から変えられない (`--timeout-seconds` は全体予算で per-command ではない)。
`--timeout-seconds 300` を渡しても 9.7 秒で倒れる。

**本 wave では直さない (scope 外)。** 裁定へ返す。

## 通知が止まる条件 (実装の逐語)

`tools/check_branch_rescue.py` の `_ledger_check` より。

- `unledgered-audit-finding`: 監査が報告した OID に有効な entry が無い場合。
  → 30 件の entry を作ったので消える。**加えて救出 ref により監査の報告自体が 0 件になった。**
- `stale-ledger-resolution`: 監査が再報告し、かつ status が
  `rescued` / `reachable-again` / `object-missing` の場合。`accepted-loss` は除外される。
  → 救出済み object は通常 ref から到達可能なので `git fsck --unreachable` に出ず、再報告されない。
- `pending-ledger-entry`: 下界 ≤ 現在なら `deadline-passed`、現在 < 下界 ≤ 現在+7 日なら `urgent`。
  監査の報告有無によらない。→ `pending` を 1 件も残していないので発火しない。
- rc は `technical_incomplete` が優先して 2、完全かつ通知ありなら 3、それ以外 0。

**`accepted-loss` を選んでいたら、その object は到達不能のまま残り、独立した dangling 監査
(`tools/audit_dangling_commits.py` 単独実行) の rc=1 は残り続けた。** 全件救出はこの面も閉じる。

## 実行した手順 (逐語)

```bash
# 1. 監査 (素の形、repo 外走査なし)
python3 tools/audit_dangling_commits.py                      # rc=1, 85.194 秒, 30 commit / 53 pair
python3 tools/check_branch_rescue.py --ledger-check           # rc=3, unledgered 30, notifications 30

# 2. 着地判定を 30 件すべてに実走 (assessment_report_sha256 の出所)
python3 tools/check_branch_landed.py --repo <REPO> --timeout-seconds 300 <OID>   # 30 回

# 3. 保存形態 (tools/check_branch_rescue.py の _pack_index と同じ方法)
for f in .git/objects/pack/*.idx; do git verify-pack -v "$f"; done   # 26 packed / 4 loose

# 4. 救出 ref の作成と再検査 (30 件それぞれ)
git check-ref-format refs/rescue/t2640/<OID>
git --no-replace-objects cat-file -t <OID>                   # commit
git update-ref --no-deref refs/rescue/t2640/<OID> <OID> 0000000000000000000000000000000000000000
git --no-replace-objects show-ref --verify --hash refs/rescue/t2640/<OID>
git --no-replace-objects rev-parse --verify refs/rescue/t2640/<OID>^{commit}
git --no-replace-objects merge-base --is-ancestor <OID> refs/rescue/t2640/<OID>

# 5. 最終照合 (救出後に 1 回だけ。これが受理の証拠)
python3 tools/check_branch_rescue.py --repo <WAVE-WORKTREE> --ledger-check   # rc=0
```

台帳 entry の生成・照合・監査に使った一回限りの収集コードは job dir
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2640-unreachable-ledger/`) に置き、**repo へ入れていない**。
出力はすべて `evidence/` に保存してある。

## 規律 6 の内容監査

救出対象 30 commit の 53 blob を**データとして**読み、指示めいた文字列を機械走査した
(`evidence/content-audit.json`)。**hit 0 件。** author は全件 `thawk105@gmail.com` (本 repo 所有者)。
working tree へ展開せず、checkout / cherry-pick / script 実行はしていない。

## 一次資料

| file | 中身 |
|---|---|
| `evidence/audit-dangling-commits.txt` | 監査 stdout 全文 (rc=1、30 commit / 53 pair) |
| `evidence/ledger-check-before.json` | 記帳前の台帳照合 (rc=3、unledgered 30) |
| `evidence/ledger-check-after.json` | **救出後の台帳照合 (rc=0、通知 0、監査報告 0 件)** |
| `evidence/findings.json` | 30 commit と 53 path |
| `evidence/commit-evidence.json` | commit ごとの日時・保存形態・main 側の同題 commit |
| `evidence/content-match.json` | 53 path の内容照合 (main を固定 OID へ束縛、`--no-replace-objects`) |
| `evidence/content-audit.json` | 規律 6 の内容監査 |
| `evidence/rescue-refs.json` | 30 本の ref 作成と 3 種の再検査の rc・stdout |
| `evidence/landed-index.tsv` | 30 件の着地判定の rc と stdout の sha256 |
| `evidence/packed-hits.txt` | pack membership の実測 |
| `evidence/retention-facts.md` | 保持 field の実測と導出規則 |
| `evidence/entries-rescued.txt` | 台帳へ入れた 30 行そのもの |
| `verbatim/s1-brief.md` | 段 1 brief (P1 は段 3 で撤回された) |
| `verbatim/s2-plan.md` | 段 2 plan |
| `verbatim/s3-lensA.md` | 段 3 レンズ A (正しさ境界と契約整合) |
| `verbatim/s3-lensB.md` | 段 3 レンズ B (実効性と scope) |
| `verbatim/s4-adjudication.md` | 段 4 裁定 |

`evidence/content-match.json` は `same_basename_non_matches` の全列挙だけを件数と先頭 5 件へ
縮めてある (`README.md` のように repo 中に何百もある名前の列挙は判断に効かないため)。
判断に効く `source_blob` / `source_mode` / `exact_matches` / `gz_matches` / `match_found` は無削除。

## 成果物の面

**tracked な実装差分はゼロ** (コード・テスト・script・機械設定を 1 行も変えていない)。
一方で**共有 Git common directory へ 30 本の ref を足している**。これは台帳の commit だけでは
再現されない状態変更であり、別 clone で台帳だけを見ても救出済みにはならない。
`refs/heads/` ではないので `git branch -a` や `git worktree list` の項目は増えない。

## 裁定へ返す項目

**`tools/check_branch_landed.py` の per-command 5 秒上限が本 repo 規模に合っていない。**
30/30 が `assessment-timeout` で `indeterminate` になることを実測した。判定器は着地の有無を
この repo では一切判定できない。[T-2639] の path 優先判定 (未 land) と同じ面である。
