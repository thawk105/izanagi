---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t529-activation-authority
seq: 3
title: 契約世代の活性化権限は履歴解決が先だと実測で確定し、実装せず 6 択一を返す — fuse を外しても既存 proof chain が読めなくなる (docs のみ、branch worktree-dev-wave-t529-activation-authority、実装差分がないため変異 matrix と受入全走は対象外)
---

## 本文

- **段 4 で「実装しない」と裁定した。** 設計案・入口同定・命名・pin 閉包の判定は
  `output/insights/2026-08-06_t529-activation-authority/` へ凍結してある
  (親 brief、段 2 プラン、段 3 の 2 レンズ逐語)。決定は
  {{D:activation-authority-blocked-on-historical-resolver}} と
  {{D:env-contract-activation-naming}}。
- **決め手は親の実測だった。** committed floor protocol
  (`output/s8b-freeze/floor_protocol.json`) は現行 pegasus 契約の `contract_sha256`
  `e576e9cd…` を固定しており、`env_contract.lookup("pegasus").contract_sha256` と一致する。
  `s8b_floor_contract.validate_protocol` は artifact の値と
  `contract_sha256_lookup(env_tag)` の不一致を fail-closed で拒否し、
  `s8b_ratified_freeze.py:2876-2882` はその lookup に **current** の registry lookup を渡す。
  **したがって 2 世代目を current にした瞬間、既存の certified floor / freeze / selector /
  oracle report が「過去には有効だったが current でない」という理由だけで解決不能になる。**
  fuse を外しても較正の再取得は進まず、blocker が fuse から履歴解決の不在へ移るだけである。
- **段 1 の生死確認 (`DW-G01`) は窓の実在を示したが、射程は限定される。**
  `_build_registry()` の pegasus へ `generation=2` を実編集で足して即復元し
  (復元後 tree clean、HEAD blob `abe103e5` と一致)、
  (i) 現 fuse が import 時に発火すること、(ii) fuse を外すと **実在しないファイルを指す** g2 が
  `lookup()` の返り値になることを測った。ただし言えるのは `lookup()` の意味までで、
  実行受理までは示していない。floor と oracle は claim より前に calibration bytes を読むため、
  非実在 path の g2 は両入口では write 前に落ちる。**scoping・適格性・silo は最初の write の
  後にしか calibration を検査せず、selector と P3 は同等の admission を持たない。
  この非対称性こそが共通 activation receipt を足す本当の理由である** — 段 2 と段 3 が
  独立に指摘し、親は自分の一般化を狭めた。
- **[T-530] を親の実測で裏取りした。** `loop._authorize_measurement` は
  `env_contract is None` で即 `return None` し (`loop.py:66-70`)、その直後
  `loop.py:139-145` が `layout.ensure()` で書き始める。`s8a_trigger_sweep.py:457` は
  `env_contract` を渡さずに `run_campaign()` を呼ぶ。すなわち活性化権限以前に、
  env 契約の認可を通らずに書き始める certified 経路が現存する。既存項目の裏取りなので
  新規起票はしない。
- **親の暫定裁定 4 点のうち 3 点が否定された。** (P2) 命名は
  `migration_epoch` / `bundle_hash` が既存 2 義を 3 義にするとして両レンズが否定
  ({{D:env-contract-activation-naming}})。(P3) 「acquisition receipt を要求すれば非偽造」は、
  同 receipt が自己申告値の schema にすぎず publisher の実行を証明しないとして否定。
  加えて linux 側の登録済み較正は legacy 形式で receipt を持たないため、そのままでは
  初期 record 自体が import 時に拒否される。(P4) receipt の形は案 C
  (sealed in-memory) が推奨されたが、それでは「全入口が同じ状態を使った」ことを
  成果物から監査できないと 2 レンズが独立に指摘した。入口 6 種の同定も
  selector と silo で誤りだった。
- **ユーザー裁定待ちの択一が 6 件ある。** 表と根拠は insights の README に置いた。
  重いものから、(1) 活性化の trust root をレビュー済み commit と定義して非偽造性の主張を
  弱めるか外部 trust root を導入するか、(2) 入口 receipt を process 局所の gate に縮めるか
  durable な identity に残すか、(3) fuse 解除の前に履歴解決を配線するか g2 後の旧 artifact
  拒否を受理縮小として承認するか、の 3 つが設計の骨格を決める。
- 段 3 のレンズ 1 本が上流分類器に拒否されて `rc=1`・出力ゼロになり、言い換えて再投入した
  (F102 の再発)。防御目的の明記だけでは足りず、手順書を要求する依頼の形式が引き金だった。
- 実装差分がないため、変異 matrix と受入全走は本 wave の対象外である。

## 次の一手差分

### 更新

- [T-529] **P1・ユーザー裁定待ち**: 契約世代の活性化権限。
  設計は `output/insights/2026-08-06_t529-activation-authority/` に凍結済みで、
  実装は {{D:activation-authority-blocked-on-historical-resolver}} により
  {{T:historical-contract-resolver-dispatch}} の後へ送る。
  着手前に決める択一が 6 件ある (insights の README の表)。骨格を決めるのは
  (1) 活性化の trust root をレビュー済み commit と定義して「非偽造」の主張を弱めるか、
  外部 trust root を持つ署名済み evidence を導入するか、
  (2) 入口 receipt を process 局所の制御フロー gate に縮めるか、
  activation serial と state hash を新規 run の versioned identity へ durable に残すか、
  (3) fuse 解除の前に履歴解決を consumer へ配線するか、
  2 世代目以後の旧 artifact 拒否を明示的な受理縮小として承認するか。
  残る 3 件は legacy 較正の grandfather 範囲、certified writer の閉包、silo の扱い。
  base: e851b311c5001bea141f1b81a195e3bd0b889b457b1468f61be6f564b5cb21c7

### 新規

- {{T:historical-contract-resolver-dispatch}} **P1・新規**: artifact に記録された
  contract hash から世代を解決する historical resolver と versioned predicate dispatch を
  production consumer へ配線する。現状 `s8b_floor_contract.validate_protocol` は
  artifact の hash を **current** の registry lookup と比較し、
  `s8b_ratified_freeze` と `s8b_oracle_report` がそこへ current lookup を渡すため、
  2 世代目を current にすると既存 certified evidence が読めなくなる (親が実測)。
  read-only の再検証は記録された hash から世代を解決し、current gate は新規 producer と
  resume admission に限る。**これは [T-529] の前提であり、較正再取得の真の blocker である。**
- {{T:silo-promotion-consumer-identity}} **P2・新規**: silo 昇格を実行する consumer を
  同定する。`silo_ladder_rung1.py` は成果物へ ability probe である旨と
  研究目標非適格・回復計測非適格を exact に宣言しており、昇格入口ではない。
  段 3 の 2 レンズが独立に指摘した。真の consumer が存在しないなら、
  「silo 昇格入口」という語を使う全箇所を訂正する。同定するまで、ability probe の
  writer を結線して昇格入口を守ったと報告してはならない。
