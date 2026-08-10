---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t721-source-closure
seq: 1
title: source closure を enforcement 閉包 8 path へ広げた — 実装は裁定どおりだが「certified 経路が source-bound」は名乗れないと段 3 で反証された (コード + docs、受入 7958 passed / 20 skipped / rc=0、変異 SURVIVED 0、branch worktree-dev-wave-t721-source-closure)
---

## 本文

- **ユーザー裁定 (2026-08-10、command 引数「裁定どおり (b) で実装」) に基づく実装 wave。**
  [T-671] R1 の source closure を enforcement 閉包へ広げた。閉包は単一定数なので production の
  変更は path 6 本の追加だけで、検証の意味論・停止点・fail-closed は不変。設計は
  {{D:enforcement-source-closure}}。
- **裁定の目的そのものが段 3 で反証された。** 「これで certified 経路が source-bound を名乗れる」
  という前提は成立しない。`pipeline.py` は verifier / calibrator / buildcache / build_admission /
  source_digest へ、`execution_guard.py` は env_attestation / site_policy へ判定を委譲しており、
  6 module は閉包になっていない。さらに `pipeline.evaluate` と低層 WAL writer は `ident` を
  通さずに書けるため、停止点も certified sink の支配点ではない (S8b oracle driver が実在の
  別経路)。**実装は止めず、名乗りを実測可能な範囲へ限定して land した。** 残余は
  {{T:enforcement-transitive-closure}} と {{T:certified-sink-gate}} へ分離した。
- **親が閉包拡張の副作用を実測し、テスト側で塞いだ。** 閉包 8 path のうち 1 本 (`loop.py`) に
  未 commit 差分があるだけで共有 v2 fixture の生成が `contract-loader-drift` で落ちる
  (clean 16 passed → dirty 6 failed、赤 6 件すべて fixture 生成側で gate 本体ではない)。
  gate を検査していない 16 の consumer が偽の赤になり、実装子が「テストを緩めて緑にする」誘因を
  生むため、共有 fixture と `test_layer3_report` の既定 binding を「記録 commit の blob digest から
  作る」test-only 経路へ移した。**production の capture / verify_live / verify_committed は
  1 行も変えていない。** 稼働中の [T-720] (同 6 module の import 形を統一中) に直接当たる問題だった。
- **敵対レビュー 5 本はすべて NO-GO** (段 3: A must-fix 6 / nit 4、B must-fix 5 / nit 1、
  段 6: L1 must-fix 6 / nit 2、L2 must-fix 1 / nit 3、焦点再レビュー must-fix 1)。
  **production の fail-closed に緩みは 1 件も見つからず、所見はすべて検出力の欠落だった。**
  最大のものは「事前登録した変異 M4 (live 検証の disk 比較を無効化) が SURVIVE する」で、
  live drift テストが `ensure_campaign_identity` 経由だったため先行する capture が drift を弾き、
  live 検証を壊しても緑のままだった。完全な binding を作ってから disk だけを汚し live 検証を
  直接呼ぶ 8 path のテストを足して塞ぎ、**再走で KILLED になった**。
- **親の裁定・説明を 3 件訂正した。** (i) brief の「受理集合は縮むだけ」は誤りで、v2 wire の
  受理言語は exact-2 から exact-8 への**置換**である (既存 32 artifact は全件 v1 のため実際の
  受理結果は不変)。(ii) 自己 hash 循環の根拠に挙げた F36 は無関係 (F36 は placeholder の空証明)。
  (iii) `test_campaign.py` の赤を「失敗集合が毎回変わるフレーク」と説明したが、実際は local 実行で
  常に同じ 5 件 (exploration output root の `/tmp` Git 祖先汚染) が落ち、6 件目だけが時間依存
  だった。計算ノードでは 272 passed。
- **変異 matrix: 9 変異で SURVIVED 0** (KILLED 4 / MISMATCH 5)。MISMATCH 5 件はすべて
  **厳密な superset** (事前登録した期待 node は全件落ちたうえで他も落ちた、欠落 0)。
  `DW-M02` に従い初回結果を消さず erratum として残した。焦点再レビューが expected/observed を
  独立に再照合し missing=0 を確認している。最終 commit で再走しても同結果。
  台帳は `output/insights/2026-08-10_t721-source-closure/`。
- **受入 lease の待ち手が 1 度空振りした。** 24 分待って acquired を得た時点で main が 15 commit
  進んでおり、runbook 7.3 の「取り込みは親が事前に済ませ、待ち手は `HEAD..main == 0` の検査に
  留める」に従って lease を返した。**4 wave 稼働時はこの形が飢餓する**ため、待ち手を
  「acquired の直後に merge commit として取り込んでから投入する」形へ変えて再投入し、
  2 度目で緑を得た。
- **実装子は 3 回とも sandbox から dispatch できず pytest 0 件実走で「実装済み・未実走」と
  報告した。** prompt に「実走できなければ緑を主張するな」と書いたことで偽の緑は出ていない。
  実測はすべて親が行った。
- **受入全走を 2 回した。** 1 走目は tip `654a199a` で 7958 passed / 20 skipped / rc=0、486.74 秒
  ([T-201] の history scan 置換を取り込んだ効果。従来 1248 秒)。記録・自己改善 commit と
  main 取り込みを重ねた後、2 走目を tip `a684b3b8` で行い 7973 passed / 20 skipped / rc=0、
  485.61 秒。**この受入値を記録する commit 自体は、その走行の対象に含まれない。**
- **land tip は受入 tip と異なる。** 受入 (`a684b3b8`) の 485 秒の間に main が 8 commit 進み、
  land は「tested main が tested wave tip の祖先でない」で rc=23 拒否された。**受入 lease は
  受入投入の排他であって land を止めない**ため、受入所要より main の前進が速い区画では
  受入 tip での land は原理的に成立しない。差分は他 wave が各自の受入を通して land 済みの
  commit と、その merge commit だけである。

## 次の一手差分

### 完了

- [T-721] source closure を enforcement 閉包 8 path へ拡張し、名乗りを実測可能な範囲へ限定した。
  残余 (推移閉包・全 sink への gate・wire key 改名) は新規 3 項へ分離した。
  remaining: none
  base: 06f755aa906fbe60baa4afc9d9dc95eb3a8bbf5697fe5983cc0a93d62cbf4878

### 新規

- {{T:enforcement-transitive-closure}} **P2・新規**: source closure を**推移閉包**へ広げるか。
  現在の 8 path は閉包ではなく、`pipeline.py` が verifier / calibrator / buildcache /
  build_admission / source_digest へ、`execution_guard.py` が env_attestation / site_policy へ
  判定を委譲している。qualification 側の 37 path 集合が規模の目安。
  成果物影響 = これがない限り「certified 経路が source-bound」とは永久に名乗れず、
  委譲先の差し替えは成果物のどの値からも検出できない。
- {{T:certified-sink-gate}} **P2・新規**: 全 certified sink に source gate を課すか。
  `pipeline.evaluate` と低層 WAL writer は `ident.ensure_campaign_identity` を通さずに書け、
  S8b oracle driver が実在の別経路である。gate receipt / capability の設計が要る。
  成果物影響 = clean な lock を作った後に drifted code から直接 WAL を書いた成果物を、
  gate を通ったものと区別できない。
- {{T:source-closure-wire-rename}} **P3・新規**: `contract_loader_*` の wire key を
  enforcement 閉包の実体に合わせて改名するか。現在 v2 lock が 0 本のためコスト最小の窓で、
  波及は 9 ファイル・116 出現。certified campaign が 1 本でも走ると key 名は成果物へ永久に残る。
  敵対レビュー 2 本のうち 1 本は改名を推し、1 本は correctness hole ではない (nit) と判定した。
  成果物影響 = 将来の監査者が「loader 2 module だけを hash すべき」と誤読し、enforcement source
  identity を縮小する危険。
- {{T:local-run-tmp-git-ancestor}} **P3・新規**: local 実行モードで
  `test_campaign.py` の exploration output root 系 5 件が常に赤くなる。`/tmp` 配下の一時 layout が
  Git 祖先を持つことを拒否する検査に当たっている。計算ノード実行では緑。
  成果物影響 = なし (診断のみ)。ただし local 実行の緑を回帰判定に使えない。
