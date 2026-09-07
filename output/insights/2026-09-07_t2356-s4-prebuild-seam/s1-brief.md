# 段 1 brief — [T-2356] 段 4 loop の事前構築成果を driver が消費する seam

## scope

段 4 loop の Pegasus job body (`tools/pegasus/p3_s4_loop_pegasus.sh`) が scratch に用意した
FetchContent 事前構築成果を、同 job が起動する driver
(`orchestrator/campaign/p3_s4_loop.py`) の build が**実際に使う**ようにする。**それだけ。**
現状は job body が `buildcache.prepare_masstree_fetchcontent` を呼んで
`masstree-prebuild-receipt.json` を残すが、直後の driver 起動 argv は base も source dir も
receipt も渡さないため、事前構築が実行経路へ届かない死んだ経路になっている (実測、D1679 の前提を確認)。

## 確定済みユーザー裁定

- **D1679** — seam だけを起票する。同 D が再訪条件つきで見送った 4 所見 (FetchContent 依存の
  build identity、make/ar/git/nm の tool identity、condition gate record の durable 化、
  `--isolate-worktree` の TMPDIR 検査) は **scope 外**。
- **D1524** — 配線は共有 measurement pipeline (`loop.run_campaign` → `pipeline.evaluate` →
  `buildcache`) へ引数を通す形で行う。**認証経路・段 4 loop 経路だけの別経路を作らない。**
- **D1689 (2026-09-07)** — 共有経路へ通す引数は **5 本**。source dir 3 本 +
  `fetchcontent_base_dir` + `fetchcontent_dependency_receipt`。4 本案は
  `_build_v2_impl` の同値条件 (`bool(base) != (receipt is not None)` で raise) により
  build 前に必ず失敗する。
- **D1690** — v2 build identity が FetchContent 依存内容を完全には束縛しない件は本件で是正しない。
- ユーザー指示 — 本題の seam 実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外。

## 不変条件

1. **規律 2 を緩めない。** correctness gate (`quarantine`、`_require_condition_gate`、verifier) の
   述語・順序・受理集合を変えない。seam は build の依存供給だけに触る。
2. **既定経路の呼出し形と build identity を変えない。** seam 未指定 (非 Pegasus、既存 caller) では
   `run_campaign` / `evaluate` / `build_v2` の argv・cache key・記録が 1 bit も変わらない。
3. cmake の define は `buildcache._v2_commands` の既存実装だけが組む。driver 側で
   `-DFETCHCONTENT_*` の文字列を作らない。
4. admission registry の classification (`dispatch-required`) と tagged qsub command を変えない。
   変える必要が出たら pin 3 系統 (`test_p3_s4_loop_job_contract.py`、
   `admission_registry.json` + `test_hooks.py` golden 2 箇所、`tools/pegasus/README.md` §7 +
   `docs/pegasus-runbook.md` §7.0) を**同じ commit で**同期する。
5. receipt の schema version `p3-s4-loop-masstree-prebuild/v1` を変えるなら job body 契約テストも
   同じ commit。既存 field を消さない。

## 成果物の形

- `p3_s4_loop.py`: 事前構築 receipt を受け取る CLI 1 本と、その値を `campaign_options` 経由で
  `run_campaign` へ渡す配線。receipt の読み口 (exact key 集合・型・path の canonical 検査) を含む。
- `loop.run_campaign` / `pipeline.evaluate`: 5 引数の素通し (非既定時だけ渡す既存様式に揃える)。
- `p3_s4_loop_pegasus.sh`: driver 起動 argv に新 CLI と receipt path を足す。
- テスト: driver 側 (`test_p3_s4_loop.py` ほか) の受理・拒否、job body 契約テストの argv 更新。
- 変異 matrix、insight、spool fragment。

## 割れうる前提 (親の provisional 裁定 — 攻撃対象)

- **(P1) 編集面は引数が指定した 2 file では閉じない。** `loop.py` と `pipeline.py` の素通しが要る。
  実測: `evaluate` は `dependency_prefix` / `expected_toolchain_manifest` しか受けない。
  D1524 が「別経路を作らない」と裁定しているので迂回もできない。→ **編集面を 4 file + テストへ拡張する。**
- **(P2) 使う capability は `post_oracle_dependency_binding` ではない。** 後者は
  `oracle_dependency_root` / `dependency_manifest_sha256` / `archive_sha256` を要求し、
  現 receipt はそれらを持たない。`fetchcontent_dependency_receipt` は
  `{masstree_head, config_sha256}` の 2 key で、receipt の
  `sources[masstree].head_commit` と `config_h_sha256` がそのまま入る。
- **(P3) seam の入力は receipt file の path を新 CLI 引数で渡す。** env 変数にすると
  tagged qsub command (pin 3 系統目) を変えることになる。job body 内で path は既知。
- **(P4) 発火条件は既存 `dependency_prefix` と同じ「Pegasus compute site のときだけ」ではなく、
  「receipt を渡されたときだけ」にする。** site 判定と二重にすると、site 判定が偽のときに
  receipt が黙って捨てられる経路ができる。→ 割れうる。
- **(P5) 生死確認 (DW-G01) は login node で足りる。** 既存 driver を使い、login で
  `prepare_masstree_fetchcontent` を 1 度呼んで作った base と receipt を新 CLI で食わせ、
  configure argv に `-DFETCHCONTENT_BASE_DIR=` と `-DFETCHCONTENT_SOURCE_DIR_*` が
  ちょうど 1 本ずつ載ることを見る。専用機構は作らない。

## 分割方針

変更単位が小さく所有が 1 本に収まるので、段 5 は Codex 実装子 1 本。
(P1)(P2)(P4) が割れうるので段 2・3 は省かない (軽量版の免除条件に当たらない)。

## 起動時の実測 (前提の裏取り)

- 編集面の重複: 103 branch × 7 file で 0 件、95 worktree の未 commit 差分でも 0 件。
  引数の前提「稼働中の T-2294 wave も `test_p3_s4_loop.py` を触っている」は**成立しない**
  (T-2294 は worklog 1296 で着地済み、worktree も残っていない)。
- pin 閉包 (DW-O09): live な pin は上記 4 の 3 系統。file 全体 sha256 の golden は live コードに無し。
- 凍結成果物の bytes を変える producer は本件に無い (DW-O10 は不成立)。
