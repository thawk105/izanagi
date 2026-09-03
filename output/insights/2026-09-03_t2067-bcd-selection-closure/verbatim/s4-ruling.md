## 段 4 裁定 — [T-2067] 残件 (b)(c)(d)

基準 commit: `dc9a060d3`（local main と乖離 0 へ再取り込み済み）。
裁定 inbox 再走査: wave 開始後に main が 8 commit 進んだ。取り込み済み。新たなユーザー裁定・
本 wave の前提を覆す decision の追加はなかった。

## 結論

実装する。実装面の差分があるため変異 matrix と受入全走は免除しない。

## real / refuted

### real・採用

| # | 所見 | 出所 | 裁定根拠 |
|---|---|---|---|
| R1 | (d) の `sys.setprofile` による code frame 観測は、実導出の冒頭を `return True` に変える故障を殺せない。同じ code frame と引数が観測され、後段は予定どおり rule-mismatch を出す | レンズ A #1 | **D1504 が「機構そのものの証明は実 loader と実 callee を通す genuine g1 の正例と負例に担わせる」と既に定めている。** 正例が欠けている点で plan は既裁定を履行していない |
| R2 | 新規 fixture が `RatifiedFreeze` を直接構築し、実 loader を通らない | レンズ A #2 | 同じく D1504 の「実 loader を通す」要求。却下選択肢に「loader と選択 assert の両方を stub する — 機構を一度も通らない緑になる」が明記されている |
| R3 | earlier run に `launch_certificate.json` を作るのは無駄。選択走査が読むのは result / manifest / journal / admission 台帳だけ | レンズ B #2 | `s8b_holdout_freeze.py:1842-1853,1877-1909`。`validate_selected_certificate` は選択済み run 用で、launch / consumer 経路では既定 False |
| R4 | 自己申告 `eligible_for_refreeze=False` かつ導出 True の earlier run を「有効な official run」と記録するのは過大表示 | レンズ B #2 | full live verifier なら `refreeze-eligibility-mismatch` で拒否する (`s8b_floor_stats.py:1069-1077`)。記録では「production admission 台帳に裏付けられた earlier result」と書く |
| R5 | 親 brief のアンカー行が 3 件ずれ、caller 列挙が 6 件不足していた (T3 は `:872`、T4 は `:1963`、T5 定義は `:2160`、`test_s8b_oracle_manifest.py:1579,1595,1795,1836`、`test_s8b_oracle_driver.py:2336,2347`) | 段 2、レンズ B #1 | 実測で確認。段 2 の 25 caller 列挙を正とする |
| R6 | 親の probe の「6 failed」は `-k "selection or eligib"` filter 内の値であり、repo 全体の kill 数へ一般化できない。filter 外に `test_v2_candidate_enumerates_and_reads_earlier_run_through_bound_dirfds` (`:2364`) がある | レンズ A、レンズ B | 親が現物を読んで追認した。記録ではこの限定を明記する |
| R7 | `s8b_oracle_driver.py:496` は選択強制点ではない。強制点は `:664` と `:1351` | 段 2、レンズ B | 両者一致。(b) の記録を訂正する |
| R8 | `docs/phase3-8b-restart-runbook.md:274-279` が `build_manifest` を実装済み API として記す。private 化で陳腐化する | レンズ B #3 | docs は親が直す。放置すると利用者の API 参照が存在しない名前へ向く |
| R9 | 焦点走の 13 file は「lexical / direct consumer 集合」であり、全 production file を読む汎用 scanner は含まない | レンズ B #4 | 記録の表現を狭める。焦点走 file は増やさない (改名は探索 token・process site・perf predicate・issuer call のいずれも変えない) |
| R10 | `return False` 変異による launch node の赤は単独帰属できない。selection gate の後に binding / lineage / repository scan が続く | レンズ A #4、段 2 自身 | consumer node だけを clean kill とし、launch node は経路被覆の補助証拠に留める |

### real・採用しない (限界として明記する)

| # | 所見 | 裁定 |
|---|---|---|
| R11 | (c) の private 化は命名規約であって機構的閉包ではない。in-process の caller は underscore 名を呼べる。`_write_approved_manifest` も選択 token を要求せず任意の exact `OfficialManifest` を保存できる | ユーザーの依頼は「**公開**迂回口を塞ぐ」であり、private 化はその字義どおりの実装である。seal token は新機構であり、ユーザーが scope 外とした「仮想リスク向けの gate の追加」に当たる。加えて 25 箇所の test caller は低位構築面として正当に使っており、token を課すと既存 fixture を壊す。**絶対規律 7 に従い、閉じていない範囲を主張せず insight と worklog へ明記する。** `verify_manifest` が選択 token を要求しない点は (a) の裁定対象と重なるため、裁定パッケージへ送る |

### refuted

| # | 所見 | 反証 |
|---|---|---|
| F1 | (c) が受理集合を塞ぐ以外の方向へ動かす / 正当な用法を過剰拒否する | builder / writer 本体は不変で、repo 内 caller は test fixture と内部 call だけ (レンズ A #5) |
| F2 | 4 構造検査 (`test_ccbench_spawn_sites.py` / `test_official_perf_closure.py` / `test_s8c_preregistration_invariant.py` / `test_s8c_preregistration_predicates.py`) の更新が要る | 三関数に process launch は無く、pin 対象の holdout / ratified 関数名も不変 (レンズ B #5) |
| F3 | DW-O09 の pin 閉包に取りこぼしがある | generator role の閉集合は 5 つで manifest 自身を含まない。canonical holdout freeze が pin する source は `s8b_holdout_freeze.py` だけで、着手前から不一致・hold 中。`_RUN_BASENAMES` の `manifest` role は artifact basename 束縛で source pin ではない (レンズ B #6) |
| F4 | 絶対規律 2 を緩める変更が plan にある | 既存 test の入力・期待値・例外型は不変。skip / 削除 / 反転 / 現行 hash 差し込み / 揮発 payload の固定値化はいずれも無い (レンズ A #6) |
| F5 | (b) の母集合が 4 群でない | 両レンズと親が独立に 4 群で一致。`tools/`・CLI wrapper・insight script に追加 caller は無く、動的 import / `getattr` 呼出しも見つからない |

## プラン v2 (実装する内容)

### (c) 公開迂回口を塞ぐ

1. `orchestrator/campaign/s8b_oracle_manifest.py` の 3 関数を private へ改名する。
   `build_manifest` → `_build_manifest`、`build_manifest_from_ratified` → `_build_manifest_from_ratified`、
   `write_manifest` → `_write_manifest`。`build_approved_manifest` 内の内部呼出しも合わせる。
   関数本体・serializer・create-only 動作・例外型は 1 文字も変えない。
2. 段 2 が列挙した **25 箇所**の test caller を機械的に置換する。test 名・入力・期待値・例外型は変えない。
3. 公開面の負例を `orchestrator/tests/test_s8b_oracle_manifest.py` へ 1 本足す。
   旧 3 名が module の public attribute として解決できないことを parametrize で固定する。
   - 拒否の含意: 選択 gate を持たない旧 3 名は module 属性として解決できず、旧 caller は構築にも保存にも到達しない。
   - 受理の含意: `build_approved_manifest` は public のまま残る。
   - 通る正例: 既存 `test_build_approved_uses_one_active_snapshot_and_writes_valid_candidate` が
     gate 済み snapshot から candidate を構築・保存・再検証できることを引き続き示す。

### (d) 実導出を launch 経路と consumer 経路へ通す

**D1504 に従い、実 loader と実 callee を通す genuine な正例と負例を対で張る。**

1. `orchestrator/tests/test_s8b_ratified_verify.py` に helper を 1 本足す。
   `_build_launch_repo` の repo へ実 earlier official run を設置する。
   - 設置するのは `result.json` / `manifest.json` / `journal.jsonl` と
     `.git/izanagi/s8b-holdout-admission-v1` の admission 台帳だけ。
     **`launch_certificate.json` は作らない** (R3。選択走査は読まない)。
   - 既存の selected artifact と既存 admission 台帳は 1 byte も書き換えない。追記だけ行う。
   - earlier run の適格性は `inspect_floor_holdout_admission_evidence` の実導出で決まる。
     helper は導出結果を返し、test 側が期待どおりか assert する。
2. **負例** (適格な earlier run): 導出が True になる earlier run を置き、
   選択 gate が `floor-selection-rule-mismatch` で拒否することを launch 経路と consumer 経路の
   両方で固定する。`reason` と `cause` は既存 stub 版と同じ値を要求する。
3. **正例** (不適格な earlier run): 既存 `test_floor_selection_eligibility_derives_resume_as_ineligible`
   と同じ機構 (claim の `entry_kind="resume"` 化 + refreeze-disqualification marker) で
   導出が False になる earlier run を置き、選択 gate が**通る**ことを両経路で固定する。
4. **実 loader を通す** (R2 / D1504)。earlier artifact を commit したあと、
   `RatifiedFreeze` を直接構築せず `M.load_ratified_freeze(root)` で取り直したものを
   `launch_validate` / `assert_g1_floor_selection_identity` へ渡す。
   loader が拒否するなら helper が理由を出して停止する。
5. **`sys.setprofile` による code frame 観測は入れない** (R1)。
   正例・負例の対が実導出の実体を通ることを保証しており、profiler は
   `return True` 故障を殺せないうえ機構を増やす。既存 stub 版 2 test の
   「呼出し記録と引数」検査は D1504 のとおりそのまま残す。
6. 既存 stub 版 2 test (`test_launch_validate_rejects_floor_selection_rule_mismatch`,
   `test_g1_selection_helper_rejects_rule_mismatch`) は**行内容・期待値・monkeypatch を変えない。**

新規 node は 4 本。launch 負例 / launch 正例 / consumer 負例 / consumer 正例。

### (b) 母集合の数え直し (親が docs へ書く)

未強制の load-only consumer は **4 群**で確定する。

| 入口 | 呼び方 | 帰属 |
|---|---|---|
| `orchestrator/campaign/s8b_oracle_report.py:2547` | load + reverify | (a) scope 外 |
| `orchestrator/campaign/s8b_oracle_judge.py:749` | load + reverify | (a) scope 外 |
| `orchestrator/campaign/s8b_verdict.py:828` | load + reverify | (a) scope 外 |
| `orchestrator/campaign/p3_autonomous_workload_trial.py:4710` | load only (C06 予算) | (e) scope 外 |

強制済みの対照は `s8b_oracle_manifest.py:1205`、`s8c_result_judge.py:2078`、
`s8b_oracle_driver.py:664` と `:1351`。**`s8b_oracle_driver.py:496` は強制点ではない** (R7)。

## 変異事前登録 (DW-M01 / DW-M08)

実装前に登録する。各変異は位置と、赤理由が一つに絞れるかの判定を持つ。
期待 node は完全集合とし、同形式へ正規化した記録 node との完全一致だけを KILLED とする。

| ID | 位置 | 変異 | 期待赤 (完全集合) | 単独理由性 |
|---|---|---|---|---|
| M1 | `s8b_oracle_manifest.py` の `_build_manifest` 定義直後 | `build_manifest = _build_manifest` を追加 | 新 public-surface 負例の `build_manifest` case のみ | clean。属性解決の前後に別 gate は無い |
| M2 | 同 `_build_manifest_from_ratified` 定義直後 | 旧 public alias を追加 | 同負例の `build_manifest_from_ratified` case のみ | clean |
| M3 | 同 `_write_manifest` 定義直後 | `write_manifest = _write_manifest` を追加 | 同負例の `write_manifest` case のみ | clean |
| M4 | `s8b_holdout_freeze.py` の `_derive_floor_selection_eligibility` の `return inspection.derived_eligible_for_refreeze` | `return False` へ変更 | **consumer 負例 node** (clean kill)。launch 負例 node の赤は補助証拠として別記し、kill には数えない (R10) | consumer 側は clean。launch 側は後段の binding / lineage / repository scan が冗長 gate |
| M5 | 同上 | `return True` へ変更 | **consumer 正例 node** (clean kill)。launch 正例 node の赤は補助証拠 | 同上。R1 が指摘した「早期 return True」故障を殺す変異 |

**登録しない候補と理由:**

- `assert_g1_floor_selection_identity` から `_hf._assert_floor_selection_identity(...)` 呼出しを削除する変異 —
  既存 stub 版 `test_g1_selection_helper_rejects_rule_mismatch` が既に殺す。冗長 gate であり
  単独変異の証拠にならない (DW-M03)。
- 述語の恒偽化など、多数 node が一斉に赤になる変異 — 過剰決定で単独理由にならない。

**新旧両走 (DW-M08、テスト強化を含む wave):**

1. 変更前 HEAD の `test_s8b_ratified_verify.py` へ M4 / M5 を適用し、既存 stub 2 node を走らせる。
   両 node は自分で導出を monkeypatch するため**緑のまま**であることを記録する。
2. 実装後の同 file・同変異で、既存 stub 2 node + 新規 4 node を走らせる。
   既存 2 node は緑、**新規 node だけが赤**になることを記録する。
3. repo 全体では `test_s8b_holdout_freeze.py` も M4 を検出するため、
   「新テストだけが検出する」比較の対象は launch / consumer 所有 file に限定する。
   この限定を実測記録へ明記する (R6)。

## 不変条件 (実装子へそのまま渡す)

- 既存テストの期待値を変更しない。反転・緩和・skip・削除を禁じる。赤なら実装側が誤りである。
- 凍結成果物の bytes を変えない。`_GENERATOR_SOURCES` が pin する 5 本を編集しない。
- `output/s8b-freeze/` 配下、campaign WAL、`external/ccbench`、
  `orchestrator/campaign/freeze_verification_hold.py` を編集しない。
- `orchestrator/campaign/s8b_ratified_freeze.py` と `orchestrator/campaign/s8b_holdout_freeze.py` を
  編集しない (参照のみ)。
- `orchestrator/tests/test_s8b_holdout_freeze.py` と `orchestrator/tests/s8b_v2_freeze_fixture.py` を
  編集しない (参照のみ)。
- docs を編集しない。commit しない。
- 選択 gate の受理集合を緩めない。

## 段 5 の分割

実装面は Codex `role=author` 1 本。編集面は次の 5 file。

- `orchestrator/campaign/s8b_oracle_manifest.py` (production)
- `orchestrator/tests/test_s8b_oracle_manifest.py` (test)
- `orchestrator/tests/test_s8b_oracle_report.py` (test)
- `orchestrator/tests/test_s8b_oracle_driver.py` (test)
- `orchestrator/tests/test_s8b_ratified_verify.py` (test)

docs (`docs/spool/worklog/` の fragment、`output/insights/`、
`docs/phase3-8b-restart-runbook.md` の R8 訂正) は親が書く。

## 成果物影響 (DW-G05)

- (c) 未対応: 床値選択規則に束縛されない manifest を構築・封印できる公開 API が残り、
  将来の caller が certified 選択結果をその manifest の上で出しうる。
- (d) 未対応: 実導出が壊れても launch 経路と consumer 経路のテストは緑のままで
  (親が実測済み)、床値選択 identity の強制が実質空になっても検出できない。
- (b) 未対応: 事実に反した残余の数え方が後続 wave の scope 判断に使われる。

## ユーザーへ返す裁定パッケージ候補

- `verify_manifest` (`s8b_oracle_manifest.py:1019`) が選択 token を要求しない点。
  builder の private 化では覆えず、(a) の裁定対象と重なる。本 wave では実装しない。
- (c) の trust boundary を「public な名前の集合」とするか「seal token」とするか。
  本 wave はユーザー指示に従い前者で実装し、閉じていない範囲を明記する。
