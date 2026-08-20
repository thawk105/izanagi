---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1445-buildcache-toolchain-hit-check
seq: 1
title: [T-1445] buildcache.pyのv2 build cacheへhit時のtoolchain完全一致検査を追加した (D602の恒久対応、コード+テスト、branch worktree-dev-wave-t1445-buildcache-toolchain-hit-check、変異matrix = baseline 126 passed・2/2 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- D602 が「次wave scope」として明示的に切り出した既知の限界 (v2 build cache hit 時に
  toolchain 束縛を検査しない) の恒久対応。設計は {{D:buildcache-hit-time-toolchain-provenance}}
  を参照。
- **段3 敵対相談レンズBが段1 brief の誤りを実コードで反証した。** brief は「hit 不一致時に
  campaign 全体が fatal stop する」と懸念したが、`BuildCacheError` は `RuntimeError` を
  継承し `pipeline.py` の既存 `except (RuntimeError, subprocess.SubprocessError)` が捕捉して
  `_abort("build-error", ...)` に変換するため、実際の影響は該当 variant 1 件の
  `build-error` abort (non-retryable terminal) に留まり campaign プロセス自体は継続する。
  親が実コードを直接確認し訂正した (`buildcache.py:110-111` の `BuildCacheError(RuntimeError)`
  定義、`model.py:119-124` の `RETRYABLE_ABORT_REASONS` に `build-error` が含まれないこと)。
- 段2 codex プランと段3 敵対相談2レンズが独立に、`expected_toolchain_manifest`/
  `declared_use_class` が cache digest (`_v2_identity` の preimage) に無関係であることを
  実コードで確認し、official/非official caller が同一 digest を hit しうる cross-lane 衝突が
  repo/API 上成立することも確認した (pipeline.py の共有 cache_root、screening_driver.py の
  expected 有無切替)。この裏取りに基づき、新2 field を既存 `expected_keys` へ常時混入する
  よりシンプルな代案は不採用と確定した (混入すると official が書いた entry を非official が
  読めなくなる)。
- 段6 敵対レビュー2レンズ (正確性・境界条件/回帰・後方互換) → fix → 焦点再レビューで
  real所見4件 (DW-M01単一理由性の担保、expected付き非official経路のテスト欠落、completion
  fields assertion、docstring精度) をすべて closed にした。fix後の親実走
  (`orchestrator/tests/test_buildcache_v2.py`) = 126 passed。
- 変異matrix (`tools/mutation_worktree.py --runner-mode dispatch --detached`、DW-M01 段4
  事前登録2件) = baseline 126 passed・m01 (provenance dict 比較の反転)・m02 (optional_pair
  集合拡張の撤回) とも KILLED、`matches_expectation=true`、MISMATCH 0・SURVIVED 0・TIMEOUT 0。
  expected_nodes は段4裁定時点の親の机上予測 (実コード読解に基づく) だったが、実測と完全一致した。
- **段4裁定確定後に気づいた手続き上の見落としを記録する (git に入らない経緯)。** `DW-O13`
  (gate・検証を新設する可能性、最遅:段2前) を段2投入前に読み損ね、段6直前に気づいた。遡って
  D75 (freeze族恒久設計固有の決定、本waveとは無関係) を確認し、DW-O13 の実体 (実成果物の
  field実在確認・識別子の非曖昧化) は段1brief・段2プランP1-1節・段3 lensAの三重の実コード
  検証で既に満たされていたと判断し、段2からの機械的再実行はしなかった。この判断自体を
  裁定パッケージ候補とする (下記次の一手)。
- 別件として、`tools/dev_wave_wait.py producer --receipt-file` に codex 自身の `--receipt`
  出力と同一 path を渡すと、codex_worker_launch.py がseal した本来の receipt
  (model/reasoning/effort_authority 等を含む) が producer-receipt スキーマで上書きされる
  ことに気づいた (段2・段3×2・段5の4回で発生)。AI-Agent trailer の model/reasoning は
  DW-O01 の docs権威 (`model: 全段gpt-5.6-luna`) と自分の dispatch argv 記録 (--reasoning
  明示または docs由来 max) から復元し、commit の provenance監査は新規違反なしで通った。
  段6以降は wait 用 receipt-file を別 path にして再発を防いだ。

## 次の一手差分

### 完了

- [T-1445] `orchestrator/campaign/buildcache.py`/`orchestrator/tests/test_buildcache_v2.py`
  へ D602 の恒久対応を実装し、段6敵対レビュー・fix・変異matrix (2/2 KILLED) まで完了した。
  remaining: none
  base: 24331073a033149f17333c2dbacbef620392a263026ba2393d509269a42601df

### 新規

- {{T:buildcache-stale-cache-abort-recovery}} **P3・新規**: `expected_toolchain_manifest`
  付きで hit した v2 cache entry が provenance 不一致/欠落で `BuildCacheError` を返すと、
  該当 variant は `build-error` (non-retryable terminal) abort になり、cache entry を
  削除するだけでは同一 campaign の再評価にならない (WAL 側の再評価手段が別途要る)。
  この復旧手順を runbook 化するかどうかをユーザーへ諮る。一次資料は
  {{D:buildcache-hit-time-toolchain-provenance}} 本文の「運用影響の訂正」節。
- {{T:legacy-official-caller-v2-migration}} **P3・新規**: `declared_use_class="official"`
  を渡すが v2 の `expected_toolchain_manifest` 経路を使わない legacy `build()` 呼び出し
  (`backoff_repro.py`/`demo.py`/`s8a_trigger_sweep.py`/`s6_sort_sweep.py`/
  `sanity_silo.py`、`run_campaign` が `env_contract` 非指定時に legacy 経路へ入るため)
  を v2+expected 経路へ移行するかどうかをユーザーへ諮る。移行すれば本 wave の hit 時
  provenance 検査の恩恵を受けるが、scope 判断は別 wave に委ねる。段3 敵対相談レンズBの
  DW-G04 検証で発見。
