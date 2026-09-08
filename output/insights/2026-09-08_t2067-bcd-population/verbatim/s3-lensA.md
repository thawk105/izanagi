## 所見 1 — `:496` は条件付きで production CLI から到達可能

**所見:** 段 2 の中核主張は成立する。ただし、通常の不変な filesystem snapshot では発火せず、二回の読込み間で状態が変わる TOCTOU trace に限られる。

**根拠 (file:line):**

- 初回の [s8b_oracle_driver.py:615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:615) と core 内の [同:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:459) は、どちらも `_load_verified_freeze(Path(freeze_path))` を同じ引数で呼ぶ。adapter も同じ `_freeze_io.load_verified_freeze` へ委譲する（[同:361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:361)）。
- leaf loader の失敗条件は、read の `OSError`、UTF-8/JSON 不正、top-level 非 object である（[s8b_freeze_io.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_freeze_io.py:49)–67）。両呼出しとも `expected_hash` は渡さないため、同じ bytes・権限のままなら一回目失敗／二回目成功にはならない。
- 具体的な成功 trace は次のとおり。

  1. `--root` は active v2 generation を正常に解決できる repository、`--freeze` は root 外の任意 path とする。CLI は freeze path を canonical path に限定しない（[s8b_oracle_driver.py:1982](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:1982)–1985）。
  2. `:615` の時点ではその path が存在しないため `read_bytes()` が `ENOENT` で失敗する。
  3. `:616` の catch 後、別 process がその path へ active generation と完全に同じ v2 bytes を作成する。invalid JSON の完成、`chmod`、一過性 `EIO/ESTALE` の解消でも同型である。
  4. `:619` から core に入り、`:459` の二読目が成功する。floor/budget 非 null なので [同:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:487) の v2 枝へ進む。
  5. production `main` は `ratified` を渡さないため [同:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:493) から `:496` を実行する。active SHA と二読目の SHA が同一なら [同:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:503) は拒否を追加しない。
  6. known-axes/T-080 が正常で manifest を省略すれば、最初の loader error は捨てられているため [同:589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:589) から allowed decision を返せる。公開入口は [同:2055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:2055)。

core caller の網羅結果は以下である。

| core 入口 | 状態 | `launch_validated` / `ratified` / `ratified_error` 無しの v2 |
|---|---|---|
| `:619` | 初回 raw load 失敗 | 上記の二読 TOCTOU でのみ成立 |
| `:632` | `is_v2 == False` と判定済みの同一 `verified` object | production では不成立 |
| `:646`, `:655` | v2、`ratified_error` が必ず非 null | 不成立 |
| `:677` | `launch_validate` 成功後 | `launch_validated` 非 null |
| `:702` | `run_block` 専用 wrapper | `launch_validated` 非 null |

ほかの return は `ratified_error` の早期拒否（`:607`）と `launch_validate` 例外の直接拒否（`:665`–676）である。したがって条件を満たす経路は `:619` の一つだけである。

**成果物への影響:** 母集合へ「standalone gate の二読 fallback」1 群を追加し、未強制群を C06 だけでなく計 2 群と記録する必要がある。

**判定:** **must-fix**。v2 fallback は二読目で許可へ反転させず、`LaunchValidatedFreeze` が無ければ fail-closed にすべきである。

## 所見 2 — `gate_check(ratified=...)` 注入 seam に production caller は無い

**所見:** 注入 seam 単独は scope 外の仮想リスクであり、新しい母集合要素ではない。

**根拠 (file:line):**

- `ratified` は公開 signature に存在する（[s8b_oracle_driver.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:594)–598）。
- `orchestrator/campaign/**/*.py` と `tools/**/*.py` を import alias 解決付きで全走査した production call は [同:2055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:2055) の `main` 一件だけで、渡す keyword は `freeze_path`, `manifest_path`, `root` の三つだけである。
- `ratified=` を渡す実例は test の [test_s8b_oracle_driver.py:5496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_driver.py:5496) などであり、production caller ではない。
- 通常 v2 経路では注入値も [s8b_oracle_driver.py:664](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:664) の `launch_validate` を通る。注入値が raw authority になるのは所見 1 の初回 load failure fallback と組み合わされた場合だけである。

**成果物への影響:** `ratified=` seam を独立した未強制群として数えず、実在する `:619 → :496` 群だけを載せる。

**判定:** **nit**。seam 向けの追加 gate・台帳・一般化は勧めない。

## 所見 3 — direct loader 母集合は 9 callsite、追加の bypass consumer は無い

**所見:** 段 2 の 9 callsite inventory は再現できた。分類だけが「強制済み 7、未強制 2」に訂正される。

**根拠 (file:line):**

| callsite | 強制状況 |
|---|---|
| [s8b_oracle_manifest.py:1205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_manifest.py:1205) | `:1206` で狭い選択 API |
| [s8b_oracle_report.py:2547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_report.py:2547) | `:2548` で狭い選択 API |
| [s8b_oracle_judge.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_judge.py:749) | `:750` で狭い選択 API |
| [s8b_verdict.py:828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_verdict.py:828) | `:829` で狭い選択 API |
| [s8c_result_judge.py:2076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8c_result_judge.py:2076) | `:2078` で狭い選択 API |
| [s8b_oracle_driver.py:644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:644) | `:664` で full launch validation |
| [s8b_oracle_driver.py:1335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:1335) | `:1351` で full launch validation |
| [p3_autonomous_workload_trial.py:4957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/p3_autonomous_workload_trial.py:4957) | 未強制 C06、D1371 の不実装対象 |
| [s8b_oracle_driver.py:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:496) | 所見 1 の未強制 production fallback |

loader 非経由候補も確認した。

- `_build_manifest` は JSON を直接読む（[s8b_oracle_manifest.py:818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_manifest.py:818)–839）うえ floor を使うが、production caller は 0 件である。実在する builder は ratified object と選択検査を経由する `build_approved_manifest`（`:1198`–1260）。
- `resolve_active_generation` は generation bytes を公開する低位 API（[s8b_ratified_freeze.py:1317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_ratified_freeze.py:1317)–1415）だが、production caller は同 module 内の loader と active-chain 再検査だけである。
- `s8b_holdout_freeze.verify_document` は generation schema を明示拒否する（[s8b_holdout_freeze.py:932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_holdout_freeze.py:932)–942、`:1005`）。v2 の代替 loader にはならない。
- generic loader を使う n-pilot は明示的に non-authoritative（[s8b_oracle_n_pilot.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_n_pilot.py:2)–6）で、v1 verifier を通す（`:605`–615）。批准 floor claim の入口ではない。
- `read_floor_source_blob` の production 使用は verdict の [s8b_verdict.py:849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_verdict.py:849) だけで、その前に `:828`–830 の選択検査がある。

**成果物への影響:** direct callsite 総数 9 は維持し、追加は新 callsite ではなく `driver:496` を未強制 production 群へ再分類する一件だけとする。

**判定:** **nit**（所見 1 の分類訂正を除き、新たな must-fix bypass は無い）。

## 所見 4 — AST 走査には構造的盲点があるが、追加の実在 target 経路は無い

**所見:** 「AST で 9 件」は直接・通常 alias の inventory としては妥当だが、一般的な実行到達性の全称証明ではない。今回、盲点形に target-specific な production 呼出しは見つからなかった。

**根拠 (file:line):**

| 盲点形 | repository 内の具体例 | target への影響 |
|---|---|---|
| `getattr` | 動的 qualname 解決は [p3_b4_wiring_probe.py:1203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/p3_b4_wiring_probe.py:1203)–1208 | 対象 module 集合 `:60`–90 に driver/ratified module は無い |
| module 属性の別名束縛 | test の `real_load = ...load_ratified_freeze`（[test_s8b_oracle_driver.py:5438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_driver.py:5438)） | test のみ |
| 暗黙 re-export | [s8c_result_judge.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8c_result_judge.py:26)–29 が loader を module 属性へ束縛する | `__all__` は `:33` で除外し、production importer も無い |
| `partial` | [issue_env_contract_activation.py:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/tools/issue_env_contract_activation.py:206)–215 | generic 例のみ。target を部分適用する箇所は 0 |
| 三重引用符内の子 process script | [test_s8b_oracle_driver.py:4717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_driver.py:4717)–4732 | test の `run-block` 起動であり production inventory 外 |
| `__main__` | [s8b_oracle_driver.py:2075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:2075)–2076 | 実在入口だが `main:2055` として既に所見 1 に畳まれる |
| package entry point | 射影された campaign/tools 内に target の別登録なし | 追加なし |
| `importlib` | 動的 module import は [p3_b4_wiring_probe.py:1256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/p3_b4_wiring_probe.py:1256)–1267 | bounded module 集合に target は無い |

非 Python file の切らない検索でも、target 名は s8c の証拠契約 JSON に宣言として現れるだけで、実行入口は無かった。

**成果物への影響:** 母集合の説明を「projected production Python における直接・通常 alias callsite 集合」と限定し、全動的 Python 実行の閉包とは記さない。

**判定:** **nit**。実在 target caller が無いため、盲点一般向けの新規 gate・検査は勧めない。

## 所見 5 — loader caller を exact 固定する権威ある閉包テストは不在

**所見:** 段 2 の「`load_ratified_freeze` caller exact-set メタテストは無い」という結論は正しい。

**根拠 (file:line):**

- `orchestrator/tests/**/*.py` の `load_ratified_freeze` 全 hit を切らずに確認し、さらに各 test function について target 名と `ast.parse`／production scan の併存を検査したが、global caller equality は 0 件だった。
- 最も近い [test_s8b_ratified_freeze.py:2501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_ratified_freeze.py:2501)–2511 は `RatifiedFreeze(` constructor の禁止であって loader caller 閉包ではない。
- [test_s8c_preregistration_invariant.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8c_preregistration_invariant.py:46)–108 は C01/C06/C07 の必要関数表であり、全 production caller の equality ではない。
- 対照的に、`build_observations` は [test_s8b_oracle_report.py:5706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_report.py:5706)–5812、`_gate_check_validated` は [test_s8b_oracle_driver.py:5503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/tests/test_s8b_oracle_driver.py:5503)–5517 で明示的な caller equality を持つ。loader には同型がない。

**成果物への影響:** 9 callsite の現時点の根拠は独立 AST inventory とし、「repo の権威ある caller closure test に由来する」とは記さない。

**判定:** **nit**。この consult から新規の一般化メタテストは提案しない。

## 総括

(a) `s8b_oracle_driver.py:496` は、安定した同一 filesystem 状態では到達しないが、`:615` 失敗後に別 process が active v2 と同一 bytes を配置し、`:459` が成功する具体的な二読 TOCTOU trace で公開 `gate-check` CLI から到達可能。段 2 の中核主張は条件付きで成立する。

(b) 母集合へ追加すべき入口は **1 群**、[s8b_oracle_driver.py:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:496)（入口 [同:2055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population/orchestrator/campaign/s8b_oracle_driver.py:2055)）。direct loader callsite は 9 のまま、未強制群は C06 と driver fallback の **2 群**。

(c) **must-fix は 1 件**。C06 は D1371 の裁定どおり触らず、D1241 / D1313 の advisory・non-certifying 上限も変更しない。テスト実走・書込みは行っていない。