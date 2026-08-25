---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-paper-story-a1-paired-20260824
seq: 4
title: P3 exploration namespace 族の契約を subcommand / coder 不可 driver へ広げ、A-1 を族へ入れた (コード + テスト、branch worktree-dev-wave-paper-story-a1-paired-20260824、変異 matrix = baseline PASSED・10/10 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **ユーザー裁定 (承認済み、前 wave から継続)**: 択 (b)「generic 契約に subcommand driver の形を
  追加する」。テストの判定ロジック変更の許可を含む。趣旨は「族の不変条件を保ったまま
  subcommand driver も検査できるようにする」であり、A-1 専用の抜け道を作ることではない。
  この wave はその範囲で実施した。詳細は {{D:family-admission-by-contract-registry}}。
- 前 wave の引き継ぎは残件を 3 件としていたが、**実測では 4 件**だった。
  `_EXPECTED_CALL_COUNTS` 未登録による `KeyError` が数えられていなかった。
  引き継ぎの件数を根拠にせず、計算ノードで焦点走を実測してから scope を確定した。
- 親 brief の「A-1 の measure 必須 option は 8 個」も誤りで、実体は **9 個**
  (`--dependency-prefix` が数えられていなかった)。段 2 の codex プラン起草が
  parser 本体から検出した。以後の裁定・変異・テストはすべて 9 個で書いている。
- 段 3 の敵対相談 2 本 (受理集合レンズ / 証拠束縛レンズ) は、独立に同じ急所を指した。
  最も重いのは **期待 campaign ID を production の config 生成器から作ると、
  生成器を壊す変更で期待値と実際値が同時に動き、当該検査が生き残ったまま検出力だけ消える**
  という共通変異の指摘である。plan はそのまま採用せず、
  同一性を決める literal を test 側で別に pin し、比較を順序付き tuple に変える形へ差し替えた。
- 段 4 で 9 件を採用、2 件を scope 外とした。scope 外の 2 件は裁定パッケージとしてユーザーへ返す
  (下記「次の一手」の新規項目)。変異 M10 (A-1 の build context へ coder 権限を渡す) は、
  production に権限の供給元が無く単一変異の exact mutant を定義できないため
  **登録から外した**。同じ向きは M9 (parser へ coder flag を足す変異) が担う。
- **段 5 実装子の自己申告が実測と食い違った。** 実装子は事前登録変異 11 件すべてについて
  「期待 node は単独 1 件」と報告したが、段 6 の敵対レビューが 4 件の誤りを本走前に指摘し、
  親の probe 走行が全件を実測で確定した。実測値はレビューの予測と 10 件すべて一致した。
  {{F:family-contract-assumed-one-cli-shape}} ではなく F28 の再発として failures へ記録した。
- **段 6 の焦点走で 3 件の赤を実測した。うち 2 件は既存 driver の回帰**であり、
  段 4 裁定が明示的に禁じた「既存 6 driver の受理集合を動かさない」に違反していた。
  (a) 新設した build context の検査が生成器 ID を全 driver 一律で `BACKOFF_SWEEP` と決め打ちし、
  `p3_s4_loop_trigger_gating` (実体は `S8A_TRIGGER_SWEEP`) を落とした。
  (b) driver 契約と環境契約の変数名が衝突していた。
  静的レビュー 2 本は (b) を検出したが **(a) を見落としており、親の実測が補った**。
  fix 後の焦点走は 1148 passed / 0 failed / 4 skipped。
- 段 5 実装子はテスト 2 件を改名した (裁定は改名を要求していない)。親は**維持と裁定した**。
  旧名は「flag 無しで拒否する」「flag で build へ届く」を指すが、A-1 にはその flag 自体が無く、
  旧名のままでは別の性質を同じ名前で検査することになる (D75 の同名二義化)。
  `orchestrator/tests/acceptance_duration_ledger.json` の旧 nodeid 11 件は孤児になるが、
  台帳 consumer 2 本が焦点走で緑であることを実測して確認した。
- **素材: 純増検出力を新旧両走で実測した** (`DW-M08` のテスト強化 wave 要件)。
  変更前 HEAD (`c626b978`、当時赤だった A-1 の 4 node を `--deselect`、baseline PASSED) へ
  同じ production 側変異 7 件を走らせたところ、**6 件が SURVIVED** し、1 件 (識別子変更) だけを
  既存検査が捕らえた。変更後は 10/10 KILLED。すなわち **6 件は今回足した検査だけが検出する**。
  特に「環境検査門を丸ごと外す」「証拠束縛の必須引数を任意にする」が変更前は
  誰にも検出されなかったことが、A-1 が族に入っていなかったことの実害である。
- 対照走は 1 回目が rc=125 (共有木の事後検査に失敗) で終わった。原因は**親自身**で、
  走行中に記録用 fragment 2 本を作業ツリーへ書いたためである。変異結果は使い捨て worktree の
  固定 commit で取れており影響を受けないが、緑の receipt を得るためツリーを触らずに取り直し、
  全件同じ結果を再現した。**共有木を観測する wrapper の走行中はツリーへ書かない。**
- 待ち手 (`dev_wave_wait.py producer`) が producer より先に無音で終了する事象が 3 回起きた。
  いずれも producer の生存を `ps` で実測して張り直し、作業の取りこぼしは無い。
- **段 8 の自己改善は docs を変更せず裁定へ返した。** 実測した候補は「事前登録変異の期待 node は
  対応表や子の申告から転記せず実測で導く」で、行き先は `DW-M01` (L1) または `DW-M08` (L1.5)。
  しかし `tools/check_docs.py` の層予算は L1 が残り約 9 bytes、L1.5 が約 1 byte しかなく、
  最短形 (約 85 bytes) でも入らなかった。既存の安全義務を削って場所を作ることは
  契約が禁じているため、予算引き上げの独立審査として裁定へ返す。
  規則そのものは {{F:family-contract-assumed-one-cli-shape}} と同じ fragment の F28 再発追記に
  記録済みで、失われていない。

## 次の一手差分

### 新規

- {{T:family-discovery-alias-hole}} **P2・新規**: exploration campaign root producer の discovery は
  AST の直接名・属性名しか拾わない。alias import 経由の呼出しと、`exploration_campaign_layout` を
  使わず `CampaignLayout` だけで root を作る module は族に入らない。現在該当 0 件で、
  `DW-G03` の独立 2 例に満たないため本 wave では実装せず文言を訂正した。
  discovery を強化するか、保証の文言を現状のまま運用するかを裁定する。
- {{T:autonomous-runtime-root-coverage}} **P2・新規**: `p3_autonomous_workload_trial` は
  実行時 `run_campaign` が 0 回のため、族の runtime 側 root 所在検査が空振りする。
  契約記録には `runtime_run_campaign_calls=0` を登録したが、空の assertion は足していない
  (足すと恒真な被覆に見える)。専用 runtime test を置くか、scope 外と明記するかを裁定する。
- {{T:dev-wave-docs-budget-headroom}} **P2・新規**: `docs/dev-wave/**` の層予算が満杯で、
  実測に基づく安全義務の追記が入らない (L1 残り約 9 bytes、L1.5 残り約 1 byte)。
  予算値を上げるか、既存節を意味等価に圧縮するか、L2 へ再配置するかを裁定する。
  予算のために安全義務を削る選択肢は契約が禁じている。
