# [T-1222] 成長比例の既知漏れ 4 件を判定し、実際に成長していた 1 件を直した

wave: `dev-wave-t1222-growth-leak-fix` (2026-08-17)
commit: `1122d724` → `7b40d111` → `8548d2d1`

ユーザー裁定 (2026-08-17 /rulings 全件 第 4 回) は「4 件を恒久保留へ登録する案を却下。
各件についてテスト側か対象側かを判定し、該当する側を直す」だった。

## 4 件の判定

| # | 対象 | 判定 | 処置 |
|---|---|---|---|
| 1 | `test_codex_agents.py` 7 node | `neither` (欠陥なし) | 実装なし。D463 第 3 区分 |
| 2 | `test_dev_waves_integration.py` 1 node | `test-side` 欠陥は実在 | **ユーザー裁定へ返す** |
| 3 | `test_s8c_preregistration_invariant.py` 1 node | `target-side` | **本 wave で実装** |
| 4 | `test_check_ai_provenance.py` 2 node | 直さない | **ユーザー裁定へ返す** |

## D463 が要求する成長率の実測

`git ls-tree -r -l` を 30 日前・14 日前・7 日前・現在の 4 時点へ適用した。

| 入力集合 | 30 日前 (2026-07-18) | 現在 (2026-08-17) | 倍率 |
|---|---|---|---|
| `.claude/agents` | 13f / 84,264 B | 13f / 83,157 B | **1.0 (微減)** |
| `.codex/role-adapters` | 13f / 171,155 B | 13f / 172,000 B | **1.0** |
| `test_dev_waves_integration.py` | 不在 | 119,456 B (14 日前から不変) | **1.0** |
| `tools/task_runs` | 不在 | 7f / 138,785 B (14 日前から不変) | **1.0** |
| `docs` 全体 | 2,047,235 B | 14,999,488 B | **7.3** |
| `docs/archive` | 674,988 B | 9,979,917 B | **14.8** |
| commit 総数 | 487 | 4,192 | **8.6** |

**実際に成長しているのは項目 3 (docs) と項目 4 (commit 履歴) だけである。**

## 項目 3 の真因と効果

比例源は `check_docs.main()` が**同じ file を `newline=None` と `newline=""` の 2 通りで
読んでいた**ことだった。`main()` 1 回の内側にだけ生きる読取 cache で物理読取を共有した。

| | `Path.open` 総数 | distinct | 平均 | 2 回以上 open |
|---|---|---|---|---|
| 変更前 | **1,141** | 673 | 1.695 | **468** |
| 変更後 | **673** | 673 | 1.000 | **0** |

`main()` median 4.539 → 4.173 秒。**「比例が消えた」とは言えない** — 消えたのは重複 open/decode で、
安全検査 (約 462 回) と本文の二重走査は残り、node は依然 `Θ(corpus bytes)` である。

受理集合の同一性は、故障を注入した状態で新旧の全出力を **raw stdout (append 順のまま)** で
比較して確かめた (差分ゼロ、rc=1 も一致)。ただし **identity が全一致したまま本文だけ変わる
差し替えは依然 stale** になる。「あらゆる条件下で完全同一」とは主張しない。

## 段 6 レビューが見つけた実在欠陥 3 件

いずれも「本 wave が直したはずのものを既定テストが守っていない」型で、親が実測で再現した。

1. **cross-mode 共有に専用の防壁が無い。** その分岐だけを無効化する変異は当時の新設 4 node を
   全通過しながら `Path.open` を 673 → 1,140 へ戻した。**改善を丸ごと消しても誰も気づけなかった。**
2. **読取権限剥奪の見逃し。** 初回読取後に `chmod 000` すると、旧挙動は `None` +
   `PermissionError` finding を返すのに、cache 有りでは cached text を返し finding を出さなかった。
   identity が `st_mode` を含まなかったため。**受理集合が広がっていた。**
3. **identity fixture の過剰決定** (size・inode・mtime が同時に変わる)。DW-M03 に抵触。

いずれも**検査を足す方向**で閉じた。新設 9 node はすべて `tmp_path` と `REPO` monkeypatch だけを
使い実 corpus へ到達しない (D335 が禁じる成長比例テストを新設していない)。
`GROWTH_TEST_HOLDS` は 59 のままで、恒久保留の新規登録はゼロである。

## 変異 matrix (`tools/mutation_harness.py`、固定 HEAD `8548d2d1`)

**6/6 KILLED、MISMATCH 0、SURVIVED 0、PARSE_ERROR 0。**

初回登録は 6 件中 3 件が MISMATCH だった。**変異が検出されなかったのではなく、
親の期待赤 node 集合が不正確だった** (MB/MC で cross-mode node を書き漏らし、MF で ctime node を
余計に書いた)。probe の実測から完全集合を再導出して本走した (DW-M08、archive 606 と同型)。
`mutation-ledger-probe.json` が初回、`mutation-ledger-final.json` が本走である。

## 段 6 レビュー関門が repo 自身の非 NFC fixture で塞がった

`--stage review` 3 本と `--stage fix` 1 本が `evidence_status=invalid` で不受理になった。
子はいずれも正常完走しており、**内容の問題ではない**。

根本原因は `orchestrator/tests/test_check_docs.py:4718, 4741` が NFC 検査用に持つ
**意図的な非 NFC 行**である。段 6 の子はこの file を読むのが仕事なので、その行が codex の
stdout event 列へ載り、launcher の `parse_jsonl` が拒否する。
**回避策**: 当該領域を読ませず、NFC 清潔と確認済みの `git show <commit>` で差分を監査させる。
これを prompt へ書いた fix2 以降は evidence が通っている。

不受理となった 3 本の逐語は `verbatim/s6-*-unaccepted.md` に保全した。
**上記の実在欠陥 3 件はすべてこれらが出したものである。**

## 親の遵守漏れ 3 件

1. 進捗報告の時刻 4 件を実測せず推定で書いた (F1 の再発)。
2. 独自変異 script を段 4 で事前登録せずに使った (DW-M05 違反)。標準 harness で回し直した。
3. identity を足した差分を commit しないまま同じ file へ変異を当て、`git checkout --` で
   巻き戻した (DW-O19 違反)。復旧に fix 1 巡を要した。

## ファイル

- `mutation-spec.json` — 本走に使った spec (期待 node 再導出後)
- `mutation-ledger-probe.json` — 初回 (3 MISMATCH)
- `mutation-ledger-final.json` — 本走 (6/6 KILLED)
- `verbatim/s2-plan.md`, `verbatim/s3-lens{A,B}.md`, `verbatim/s4-adjudication.md`
- `verbatim/s6-*-unaccepted.md` — 不受理だが実在欠陥を出した段 6 レビュー 3 本
