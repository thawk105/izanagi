# [T-597] dev-wave 4 文書の予算捻出 — 一次資料

wave = `dev-wave-t597-budget` / branch = `worktree-dev-wave-t597-budget` / 起点 main = `9cb0f24b`。
すべて共有ログインノード pegasus02 の本 worktree で実測 (F41)。

## 1. 何を求められたか

`docs/dev-wave/{core,workers,mutation,operations}.md` の aggregate 予算は 25,200 bytes で、
実測 25,187 = 余地 13 bytes。裁定済みの規約候補と他 wave の改善候補が採録できず滞留していた。
**予算上限を上げることは禁止** (T-127 裁定)、**予算のために安全義務を削除・弱化することも禁止**
(`docs/skill-self-improvement.md`)。許された手段は陳腐化記述の縮約・重複の一本化・テスト化のみ。

供給 = [T-597]、需要 = [T-592] で、両者は 2026-08-06 の同一ユーザー裁定
「陳腐化規則の削除・テスト化で予算を空けて採録、入らない分だけ見送り」の対側である
(一次控え = `rulings-inbox/2026-08-05-background-waiter-duplication.md` 末尾)。

## 2. 主経路の棄却 — 「機械が強制するから prose を削る」は成立しなかった

親 brief の主経路は `DW-M08` の手順記述を `tools/mutation_harness.py` への pointer へ縮約する案
(−259 bytes) だった。段 3 の 2 レンズが独立に、しかも別々の理由で棄却した。

| 攻撃 | 実測根拠 |
|---|---|
| 正規化義務は実装が**持っていない** | `docs/failures.md` の F95 が「`DW-M08` は正規化を定めるが、その正規化を harness 自身が持っていない」と明記。修正 [T-417] は未了 |
| canonical stdout は全経路で保証されない | `mutation_harness.py:1168-1171` — `runner_mode != "dispatch"` では dispatch stdout を読まず console を `job_stdout` にする |
| `-rf` の token 存在検査は実効性を保証しない | 後勝ちの `-rs` で FAILED summary が消える既知例がある。prose 保持でも塞がらない |
| 独自 harness には機械強制が届かない | `DW-M05` は条件付きで独自 harness を許す |
| 提案 test の 1 件が**恒真** | `mutation_harness.py:822-825` — `partition(" - ")` は separator 不在時に `(remainder,'','')` を返すため `node = remainder` は同値再代入。対象行を削除しても緑 |

さらに F71 の恒久対応欄は、その parenthetical が [T-247] wave で
「本 F の (a)(b)(c) を指す形」へ**意図的に整形されたもの**だと記録している。重複ではなく設計された再掲。

**結論: `mutation.md` は本 wave で 1 byte も変更しない。**
「実装が満たしていない義務を、実装が担うことにして削る」のは予算のための安全義務の弱化そのものである。

## 3. 実際に採った捻出経路 — 重複の一本化 (404 bytes)

いずれも「義務が効く**その瞬間に必ず読まれる**別の節が、**上位互換**の形で同じ義務を書いている」重複。

| # | 削除 | bytes | 残る担い手 |
|---|---|---:|---|
| Sup-1 | `operations.md` DW-O19 の「段 1 前提実測も復元規律に従う」 | −73 | `core.md` DW-S01 (段 1 で無条件必読) |
| Sup-2 | `workers.md` DW-S06-C の対応表要求 | −93 | `operations.md` DW-O16 (条件 16 = 焦点再レビュー直前。「表なしで root cause が閉じたと判定しない」まで持つ) |
| Sup-3 | `core.md` DW-S09 の land 結果 2 文 | −238 | `operations.md` DW-O23 (段 9 必読、再試行手順まで持つ) + 入口の終端節 (L0 常時) |

**Sup-3 は行き過ぎだった。** 段 6 の 2 レンズが独立に、(a)「landed/already-landed 以外はすべて停止」
という catch-all と (b) 報告項目の「既存 branch」が移設先に無いと指摘した。helper は
`not-landed` / `fold-failed` / `fold-recovery-failed` / `fold-rollback-failed` / `rejected` も返すのに、
`DW-O23` は postcondition failure と stale/busy しか規定していない。1 文で復元した (+102)。

その復元文が今度は成功 status 集合を core と operations で二重管理する退行を作り、
焦点再レビューが指摘した。逐語列挙をやめ `DW-O23` を参照する形にして解消 (−4)。

## 4. 採録 (2 件) と見送り

**採録** — 2026-08-06 裁定の 4 候補束のうち未採録の 2 件だけ。

- `DW-O01` (+63): 既存 `.done` は消さず再利用せず再投入を止める
- `DW-C00` (+186): 待ち手は 1 条件 1 本、通知ごとに作り直さず状態を読む、生産者と共に落とし死も待ち条件

残る 2 候補は本 wave の実測で**既に閉じていた** — pgrep 自己一致は commit `a62be201` で採録済み、
期待 node の完全一致は `_observed_status` の `failed_keys == expected_keys` で機械化済み
(本 wave で pin test を追加)。**したがって [T-592] の 4 候補は全件終端した。**

**見送り** (契約本文へ入れない、理由付き): 機構名検索と解除条件棚卸しは 2026-08-06 裁定束の外
(前者は出所自身が「新しい T / F を作らない」と書き、後者は発生元 [T-529] wave が段 3 進行中の
live candidate)。節 (H2) の削除は D94 決定 2 によりユーザー裁定必須で、
D186 が `DW-O11` の未機械化 3 経路と回収可能量 0 bytes を明記しているため実施可能な削除はない。

## 5. テスト化 — F71 の恒久対応が 4 回再発したのに無 pin だった

`F71` [恒真ゲート] の恒久対応 (c)「`rc != 0` かつ抽出 0 件は `PARSE_ERROR` で fail-closed 停止」と
`DW-M08` の `-rf` 必須は実装済みだが、**どちらも test で固定されていなかった**
(分岐を消しても既存テストは緑)。Codex author が 3 test を追加した。

追加しなかったもの: separator fallback の test (恒真)、正規化の test
(F95 のとおり `@real-repo` で成立せず、pin すると半分だけ真の保証になる)。

## 6. 変異台帳

事前登録は段 4 (`s4-adjudication.md`)。本 wave は**テスト強化だけの wave** なので
`DW-M08` に従い新旧両走を登録した。

**正本 = `mutation-ledger2.json`** (F155 の既定 recipe `--runner-mode dispatch` +
`python3 tools/run_tests.py --force-dispatch -rf orchestrator/tests/test_mutation_harness.py -p no:cacheprovider`
で harness 完走、rc=0)。baseline = PASSED。

| ID | 変異 | 新テスト (M1〜M3) | 変更前テスト (M1-old〜M3-old) |
|---|---|---|---|
| M1 | `-rf` 必須検査を削除 | **KILLED** — `test_missing_rf_is_rejected_before_runner_or_ledger` | **SURVIVED** (rc=0) |
| M2 | `_observed_status` の `rc != 0 and not failed` を削除 | **KILLED** — `test_mutation_nonzero_normal_rc_without_failed_nodes_is_parse_error` | **SURVIVED** (rc=0) |
| M3 | baseline 側の同条件を削除 | **KILLED** — `test_baseline_nonzero_normal_rc_without_failed_nodes_is_parse_error` | **SURVIVED** (rc=0) |

3 件とも kill node はちょうど 1 件で単一理由性を満たし、`-old` 側は 3 件とも素通りする。
**これが本 wave の純増検出力である。**

親が手で測った narrow 走行 (`mutation-narrow.json`) も同じ結論を出しており、独立に一致する。

### erratum — 初回結果を消さず、根本原因の誤帰属も残す (DW-M02)

M2 の初回結果は `PARSE_ERROR` / rc=16 だった (`mutation-ledger.json` に残置)。
親はここで **root cause を 2 度続けて誤った**。記録として両方残す。

1. **誤り 1: 共有ノードの外乱。** 実際に別 wave 2 本が同時に `run_tests.py` を走らせており、
   artifact の「生存中の予約」も非 0 だった。しかし静穏窓 (予約 0) で再現したため撤回。
2. **誤り 2: 自己参照仮説。** 「変異対象が変異 harness 自身なので、fail-closed 分岐を消すと
   harness が abort せず入れ子実行が増え、外側 bounded scope が倒れる」と考え、
   **検証しないまま root cause として本文へ書いた**。

**正しい正本は F155 である** (land 再試行の直前に main を読み直して判明)。同じ rc=16
(`bounded scope の memory.max / memory.oom.group を走行中に attest できない`) を
`_SCOPE_ATTEST_SECONDS = 1.0` の race として特定済みで、恒久対応は変異本走の runner を
`--runner-mode dispatch` + `python3 tools/run_tests.py --force-dispatch -rf <対象 module> -p no:cacheprovider`
にすることだった。`--runner-mode local` を指定しても `run_tests.py` は headroom 次第で
内部 dispatch へ倒れるため、mode と実態が食い違う。
**親は既存 F の恒久対応を試す前に、独自の根本原因を立てていた。**

教訓: **既存 F の恒久対応を試す前に新しい根本原因を立てない。** 本 wave では F155 の
再発として記録し、既定 recipe で本走をやり直した結果を変異台帳の正本に差し替えた。

**やり直しは自己参照仮説を決定的に否定した。** 同じ M2 変異が、runner を既定 recipe へ
変えただけで rc=1 / kill node 1 件の KILLED になった。変異内容は 1 byte も変えていない。
仮説が正しければ dispatch mode でも入れ子実行の暴走が起きるはずで、起きなかった。

再照準した narrow 走行 (`probe_nodes.py`、repo 外) の結果は有効で、`DW-O19` の復元規律
(clean 確認 → 単一変異の `git diff --stat` 確認 → 復元 bytes 照合 → clean 確認) をすべて満たす。
既定 recipe による本走と併記する。

## 7. 受入・検査の実測

| 検査 | 結果 |
|---|---|
| 受入全走 `python3 tools/run_tests.py` (静穏窓・単独) | **7101 passed / 20 skipped、rc=0** (1069s) |
| `test_mutation_harness.py` 単独 (段 5 後) | 67 passed (既存 64 + 新規 3) |
| `tools/check_docs.py` | rc=0 |
| `check_ai_provenance.py --range 9cb0f24b..HEAD` | rc=0、違反なし |
| `check_ai_provenance.py` 全履歴 | rc=1 — [T-614] が対応中の既知 7 違反。本 wave 由来ではない |
| 4 文書 byte | core 8,584 / workers 4,575 / mutation 3,674 / operations 8,301 = **25,134 / 25,200** (余白 66) |

## 8. 裁定パッケージ (ユーザーへ)

1. **待ち手規約の置き場所と dispatch 強度。** 段 3 のレンズは「`DW-O01` (codex 子起動直前) では
   land ループで読まれない」と言い、段 6 のレンズは「`DW-C00` は wave 開始でしか読まれない」と言った。
   **2 つのレンズが別の場所を否定している。** 親は `DW-C00` を選び (同節の「親は実装面を直接編集しない」と
   同型の、wave 全体を通じた manager 規律だから)、焦点再レビューは `partial` と判定して
   第 3 案「文は `DW-C00` に置いたまま、条件 dispatch に『背景 producer・待ち手の生成/再利用/停止、
   通知処理の直前に `DW-C00` を再読する』を足す」を推奨した。
   これは入口 `.claude/commands/dev-wave.md` の条件表と `check_docs.py` のハードコード表・
   対応テストの同時変更を要する = 契約変更なので実装せず返す。
   **焦点再レビューはこの 1 点を理由に NO-GO を出している。** 親は「採録した規約の内容は
   裁定どおりで完全であり、争点は dispatch の強化という増分」と判断して land したが、
   逆の判断もありうる。
2. **`-rf` の実効性 (段 3 A-3)。** token 存在検査は後勝ちの `-rs` を防がない。prose 保持でも塞がらず、
   実効 option 解析が要る。塞ぐか否か。
3. **F95 / [T-417] の未了。** `DW-M08` が定める正規化を harness が持たない状態が続いており、
   これが本 wave の主経路を棄却させた。優先度を上げるか。
4. **`DW-M08` の pointer 化は「完全機械化後」に再提案してよいか。** 本 wave では棄却したが、
   2・3 が閉じれば根拠は変わる。

## 9. 素材

- `s2-plan.md` (段 2 プラン)、`s3a-review.md` / `s3b-review.md` (段 3 敵対 2 レンズ)
- `s4-adjudication.md` (段 4 裁定、変異事前登録を含む)
- `s5-impl.md` (段 5 実装子)、`s6a-review.md` / `s6b-review.md` (段 6 敵対 2 レンズ)
- `s6c-review.md` (焦点再レビュー、closed/partial/regressed 表)
- `mutation-ledger.json` (harness 台帳、M2 の初回 erratum を含む)、`mutation-narrow.json` (再照準後の実測)
- いずれも `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t597-budget/`
