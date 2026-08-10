---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-known-red-exceptions
seq: 1
title: 既知の失敗・依存物不在を緑に化かしていた 4 箇所を可視化・fail-closed 化した — 疑似スキップは PASS に数えられ、防壁配線の欠落は skip で逃げていた (コード + docs、受入 8277 passed / 20 skipped / 522.35 秒 / rc=0、変異 3/3 KILLED、branch worktree-dev-wave-known-red-exceptions)
---

## 本文

- 依頼は「既知のテスト失敗を例外としてスルーしているところがあれば適切に修正する。
  リワードハック禁止で、テストされている側が悪ければそれを、テストがおかしければテストを直す」。
  **赤いまま免除されているテストは 1 件も無い**ことを先に確定した。既知赤 waiver W1 (F96/F101) は
  `[T-407]` = `7f767ee8` の land で失効済みで、直近 land の受入全走も rc=0 である。
  したがって本 wave の対象は「赤にならずに緑へ化けている経路」だけになった。

- **20 skipped の内訳を診断走行で実測した** (受入形ではない、計算ノード request `900952.nqsv`、
  8037 passed / 20 skipped / 514.28 秒 / rc=0)。g++-13 不在 7、pinned Codex runtime 不在 4 (D60)、
  template patch 未適用 4、実 Silo サンプル不在 1、gnuplot 不在 1、実ビルド canary 3。
  **発火している skip はすべて具体的な依存物不在**であり、失敗を skip に化かしたものは無い。
  規約違反は静的全数走査 (AST + grep) の側だけに出た。

- **直した 4 箇所。** production コードは 1 byte も変えていない。
  - `test_calibrator.py` の F3 (計測前の単独性確認) 実プロセス番人 2 本が、`pgrep` / `/proc` 不在時に
    早期 `return` で打ち切っていた。**pytest はこれを PASS に数える。**
    `orchestrator/tests/README.md` の「print + return の疑似スキップはカバレッジ蒸発を隠すので
    使わない」に正面から違反していた。原因は同ファイルの `_run()` が `except Skip` を持たず、
    `skiputil.skip` を使うと素の runner で ERROR に化けることだった。両方を直した。
  - `test_hooks.py` の `test_settings_json_wires_all_hooks` が、`.claude/settings.json` に
    `hooks` key が無いと skip していた。**これは D30 の背景そのもの** — 「配線済み」と称しながら
    実態が `.claude/settings.json = {}` で第二防壁ゼロだった over-claim — の残骸である。
    hooks は現在 実装済・配線済 (`hooks/README.md` が正本) なので、配線が消えた構成が
    受入を緑で通る状態だった。assert failure 化した。
  - `test_dev_waves_isolation_contract.py` が conftest import 中の**あらゆる** `ImportError` を
    「pytest 不在」の skip に化かしていたのを、pytest 自体の不在だけへ狭めた。
  - `test_p3_s4_loop_trigger_gating.py` の `_pinned_clean_sub_or_skip` を削除した。git の全例外を
    「submodule 未取得」の skip に化かす死んだ helper で、`753d11c8` で 2 テストが fake template dir へ
    移行した際の取り残しである。呼び出し元 0 件を親と 3 本の子が独立に確認した。

- **巻き戻しを機械で撃つため positive control を 2 本新設した。**「依存物不在時に PASS でなく
  skip になる」ことと「hooks key 欠落が assert failure になる」ことを、それぞれ固定する。
  宣言ではなくテストで守る形にしたので、変異で歯を確認できる。

- **段 6 の敵対レビュー 2 本は割れた** (レンズ A = GO / must-fix 0、レンズ B = NO-GO / must-fix 2)。
  親は B の 2 件のうち 1 件 (hook 配線) を採用し、1 件を裁定へ返した。
  **親 brief の却下理由 2 つはレンズ B に反証され、訂正した** — `run_tests.py` の submodule gate は
  初期化しか検査せず dirty を見ない。対象 4 node は `REAL_REPO_SERIAL_NODES` に登録済みで
  xdist 並列とも衝突しない。一方でレンズ B の「小さく安全」も不完全で、
  `test_source_digest_fixed_variant_distinct` は `_require_g13()` を持たないまま
  `src_token` (既定 `cxx="g++-13"`) を呼ぶため、patch 窓だけ開けると pinned compiler 不在環境で
  skip でなく赤になる。焦点再レビューが両方を独立に検証した。詳細と択一は {{T:template-patch-test-window}}。

- **変異は事前登録 3 件すべて KILLED、実測 node は期待と完全一致、baseline PASSED。**
  M1 = `runner.py` の pgrep パターンを旧 F3 形 (`build-variants/` 接頭辞) へ巻き戻す → 期待どおり
  3 node が赤。M2 = 直した guard を `return` へ戻す → 新設 positive control 1 node が赤。
  M3 = hooks key 欠落時に helper が黙って return する形へ戻す → 新設 positive control 1 node が赤。
  **新旧差分 (`DW-M08`) は走らせていない。M2 / M3 の「旧側」は wave 前の HEAD そのものであり、
  その状態で受入全走が 8037 passed / rc=0 だったこと (本 wave の診断走行) が差分の証拠である。**

- **template patch 未適用の 4 skip は権限層に阻まれて実測できなかった。** 一時適用して
  4 node の実挙動を測ろうとしたが、submodule への patch 適用が拒否されたため迂回せず静的判断に
  切り替えた。`git apply --check` が rc=0 で当たることだけは確認している。

- **受入 tip と land tip は 3 commit 違う。** 受入全走を回したのは `34255bba` (lease 取得後に
  local main を取り込んだ merge commit) で、land したのはその上に docs のみを積んだ tip である。
  差分は本記録 fragment・insights・裁定パッケージの commit、段 8 の runbook 1 箇所、
  および受入 tip と land tip の差を書いた本項の commit だけで、実装面は 1 byte も動いていない。

- **工数。** codex 子 6 本 (実装 1 / 段 6 敵対 2 / fix 1 / 焦点再レビュー 1 / merge 監査 1、
  すべて sol)。計算ノードへの dispatch は診断走行 1、targeted 2、変異 matrix 1 (baseline + 3 変異)、
  受入全走 1。段 2 (プラン起草) と段 3 (敵対相談) は軽量版として省いた。

## 次の一手差分

### 新規

- {{T:template-patch-test-window}} **P1・新規・ユーザー裁定待ち**: template patch 未適用で
  恒久 skip する 4 node を、テスト側で `patchharness.applied()` の窓を開けて実走させるか。
  `orchestrator/tests/README.md` が「依存物不在」に数えているが、実際には repo 内に patch が
  あり pinned-clean・flock・revert 付きの既存 harness で開けられる前提であって、
  外部依存物の不在とは別分類である。回収できるのは 4 node 中 2 node で、
  `test_source_digest_fixed_variant_distinct` には `_require_g13()` が無く、窓を開けると
  pinned compiler 不在環境で赤になるため guard 追加が要る。受入 suite が実 submodule を
  4 箇所で変異させる設計変更を伴うため裁定を要する。裁定パッケージは
  `output/insights/2026-08-11_known-red-exceptions/package.md` の R1。
- {{T:s8b-git-failure-skip-narrowing}} **P3・新規**: `test_s8b_approved.py` と
  `test_s8b_protocol_builder.py` の依存物ガードが `CalledProcessError` / `UnicodeError` /
  tracked artifact 欠落まで skip に落とす。README の「具体的な不在検知」より広い。
  段 6 の両レンズが独立に挙げたが、production 側が同型失敗を fail-closed にするため
  受理集合の拡大を立証できず nit に留めた。git 実行体の不在だけを skip にし、
  非 0 終了と decode failure を赤にする形が候補。
