# 2026-08-11 [T-798]/[T-799]/[T-820]/[T-821] 単一 finalize protocol — 実装 wave の逐語

`authority: none` / `default_effect: no-state-change` — 本書は凍結記録であり、可変状態の正本
(worklog 末尾・現行 phase doc) ではない。設計判断の正本は decisions、経緯の正本は worklog の
該当エントリ。

前段の評価 wave (本番コード未変更) の逐語は `output/insights/2026-08-11_t798-t799-fold-window/`。
本 wave はその裁定パッケージを受けた**実装 wave**である。

- `verbatim/s1-brief.md` — 段 1 brief (scope・不変条件・親の provisional 裁定)
- `verbatim/s2-plan.md` — 段 2 プラン (file:line 粒度)
- `verbatim/s3-lens-a.md` / `s3-lens-b.md` — 実装前の敵対相談 2 本
- `verbatim/s4-adjudication.md` — 段 4 裁定 (実装契約と変異事前登録の正本)
- `verbatim/s6-lens-a.md` / `s6-lens-b.md` — 実装後の敵対レビュー 2 本 (いずれも NO-GO)
- `verbatim/s6-adjudication.md` — 段 6 裁定 (must-fix / 格下げの根拠)
- `verbatim/s6-focus-review.md` — fix 後の焦点再レビュー (F1〜F5 対応表)

## 測定環境

- checkout: `.claude/worktrees/dev-wave-t798-t799-finalize`
- 実装 commit: `b9fbd291` (engine) → `920f4938` (land) → `84fbcfc7` (review fix) →
  `d673ec94` (fold_date pin) → `8759a258` (main 取り込み)
- repo 外 probe の所在: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t798-t799-finalize/probe/`
  ([T-317] 裁定に従い実行可能な probe は repo へ入れない)

## 段 1 前提実測 (存在証明であって普遍命題ではない)

1. **post-commit crash** — 本番 land は `core.hooksPath=/dev/null` で hook を無効化するため、
   main の ref を tight loop で監視する watcher から fold commit 直後に SIGKILL した (rc=-9)。
   測った 1 注入点では残骸は durable かつ clean (canonical・fragment GC ともに commit 済み、
   state 無し)、同 argv の再投入は rc=10 `stale-main`。
   **postcondition は 1 つも走っていない**ので「certified に健全」とは言えない。
2. **archive 跨ぎ T 重複** — 現行 worklog 末尾へ archive 専有 ID の新規項を実編集で 1 行足し、
   実 `tools/check_docs.py` を走らせて rc=0「違反なし」。復元後 sha256 一致・tree clean を確認。
   測ったのはこの 1 形だけである。

## 帰属の実測 (段 6)

焦点 4 ファイル走で `test_exploration_external_root_keeps_wave_clean` が落ち続けたため、
**wave 前の commit `276ab6cc` で同じ runner argv の baseline を走らせた**ところ、
同一の 1 node だけが同じように落ちた (`mutation-ledger-prewave2.json`)。
したがって本 wave の差分に起因しない。機序は `conftest.py` の autouse fixture
`_declare_default_test_site` が `orchestrator.campaign.site_policy` を `sys.modules` に
あるときだけ無効化する一方、当該テストが campaign を実行時に遅延 import することである。

## 結論 (要約)

1. **phase は復旧の権威にならない。** commit と phase 書換えは別 operation なので、
   phase を権威にすると必ず受理表の外側の相が残る。権威は fold commit の identity に置いた。
2. **採番を伴う transaction は入力 closure を束縛しないと守れない。** engine 自身の未 commit な
   書換えは HEAD を 1 bit も動かさずに採番を変えられる (敵対レンズが構成した経路)。
3. **敵対レビューは「自分が作った受理集合の拡大」を実際に見つけた。** noop 回帰を閉じる過程で
   `apply_fold` が forged noop plan を素通しするようになっており、段 6 レンズ A が検出した。
4. **単一 finalize protocol の終端はまだ閉じていない。** finalize の unlink 後に死ぬと
   結果を冪等に再取得できない。ただし段 1 実測により **wave 前も同一の残骸**であり回帰ではない。

## 変異 matrix (段 6)

`mutation-spec.json` / `mutation-ledger.json`。固定 commit `39212bd0` の使い捨て worktree、
runner は `run_tests.py --force-dispatch` の焦点 4 ファイル走。**baseline PASSED、
8/8 KILLED、MISMATCH 0・SURVIVED 0。**

- **wave 前の実コードの形へ戻す変異を 4 件含む** — M01 (`apply_fold` 末尾へ `state_path.unlink()`
  を復活)、M04 (`except BaseException` を `except Exception` へ)、M05 (receipt を 5-field へ)、
  M07 (commit の diff 集合比較を撤去)。いずれも殺された。
- **M06 は初回 probe で SURVIVED した (erratum)。** 狙った `_complete_shape` の GC 残存検査は、
  そこへ到達する時点で GC が完了しているため他層に mask される。**実効 gate である
  `_discover` の active 受理条件へ再照準**して KILLED になり、両層同時変異 (M06B) も
  同じ node が殺すことを確認した。`_complete_shape` 側は冗長 gate として単独変異の証拠から外す。
- 期待 node は probe 2 本の実測から導いた完全集合で、runner argv は probe と本走で同一である。
- baseline を緑にするため `test_exploration_external_root_keeps_wave_clean` を deselect した。
  この node は **wave 前の commit `276ab6cc` でも同じ argv で同じように落ちる**ことを実測済みで、
  本 wave の差分に起因しない (`mutation-ledger-prewave2.json`、job dir に保存)。
