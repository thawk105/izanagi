---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t733-source-closure-transitive
seq: 1
title: [T-733] enforcement source closure を exact 24 path から exact 62 path へ広げた (code + tests + insight、branch worktree-dev-wave-t733-source-closure-transitive、変異 5/5 KILLED)
---

## 本文

- **依頼文と D1075 が言う「現行 8 path」は現行コードでは 24 path だった。** 親が着手時に実測して
  brief へ出し、段 4 で再裁定した。D1075 が名指しした委譲先のうち verifier 面は
  D442 / D473 の系列ですでに収載済みで、未収載は calibrator / buildcache / build_admission /
  source_digest / env_attestation / site_policy の 6 種だった。
- **親の測定が 2 回誤り、どちらも子が検出した。** 1 回目は相対 import の階層解決の不具合で
  1 段目の委譲先を 30 と測った (正しくは明示 36)。段 2 の plan 子が指摘し、親が script を直して
  再現・確認した。2 回目は明示 import しか見ておらず、実行時に必ず走る package 初期化 2 file を
  落としていた。段 3 の 2 レンズが独立に同じ 2 file を挙げた。最終的に exact 62 path で確定した
  ({{D:closure-first-layer-includes-package-init}})。
- **親の brief の別の誤りも訂正した。** 「閉包の成長は受理集合を狭める方向だけ」は誤りで、
  exact key 集合の検査は旧集合から新集合への非互換な置換である。旧 map を拒否する一方、
  旧コードが拒否した新 map を受理する。規律 2 の意味での弱体化ではないが「狭まるだけ」とは書けない。
- **外部 root の lock 11 件が decode 不能になることを親が実測した。** レンズ B は 5 件と申告したが、
  `/work/1/SFC/tanab/b10-backoff-grid-runs5` と `/work/1/SFC/tanab/izanagi-measurements` を
  親が自分で走査すると 11 件すべてが現行 exact-24 map だった (B10 格子 3 件、
  paper-story A-2 認証 8 件)。閉包をどの大きさへ広げても同じ代償が出るので、段階の切り方の
  問題ではない。**ただし本 wave が作る回帰ではない** — 旧 grammar の拒否は
  `test_v2_rejects_legacy_exact_two_source_blob_keys` と
  `test_v2_rejects_pre_wave_exact_twelve_source_blob_keys` が過去の拡張から一貫して固定している。
  **親は段 4 で「repo 側 consumer はこの 11 件を decode 経由で読んでいない」と裁定したが、
  これは誤りだった。** 親が確認したのは `test_b10_extended_figure_provenance.py` (外部 source を
  file bytes の SHA-256 で束縛する) だけで、別 file の `test_plot_b10_extended_backoff.py` を
  見ていなかった。同 test は `tools/plotting/plot_b10_extended_backoff.py` の
  `load_measurements()` を実 root に対して呼び、そこで外部 lock を `artifact_admission` 経由で
  decode する。受入全走で
  `test_throughput_ci_is_wal_t95_and_abort_has_no_ci_in_canonical_data` が
  `CampaignLockCodecError: authority.contract_loader_blob_sha256s の exact key 集合が不正` で
  落ちた (1 failed / 19869 passed / 92 skipped)。**閉包拡張に帰属する回帰である。**
  さらに同じ decode 経路は fig2c の生成器そのものなので、図の再生成も現状では通らない。
  したがって歴史 grammar の扱いを決めない限り本 wave は land できない。
- **段 2 が提案した「pre-T733 exact-24 map を拒否するテストの新設」は採らなかった。**
  上記が裁定待ちである以上、先にその方針を凍結してしまうためである。既存の exact-2 / exact-12
  拒否テストが、受理を緩める変異を十分に検出することを変異走行で確かめた。
- **段 6 の敵対レビューは real 所見 1 件だけだった。** 定数は裁定の逐語どおりに更新されていたが、
  docstring 3 箇所が「24 を 62 に置換しただけ」の旧説明のままで、裁定が要求した限定が抜けていた。
  fix で docstring から保証内容を消し、2 定数を正本として参照するだけにした
  ({{D:closure-scope-string-states-what-it-is-not}})。
- **変異は probe → 再照準 → 本走の 3 段になった。** probe で M02 (新規 member の bytes を変える)
  だけが生存した。テスト側の drift 検査は実チェックアウトではなく合成 fixture リポジトリを
  使うため、実物のファイルを触っても検知経路に乗らないことが原因だった。DW-M02 に従って
  記録側の照合を無効化する変異へ再照準し、63 件で検出された。初回の生存結果は消していない。
- **固定 known-answer の値は子の計算を信用せず親が独立に計算して照合した。**
  順序付き path 列の SHA-256 と合成 fixture の E1 の両方が一致した
  ({{D:closure-order-pinned-by-known-answer}})。
- 受入全走 (attempt 1): `1 failed, 19869 passed, 92 skipped`。唯一の赤は上記の
  `test_plot_b10_extended_backoff.py::test_throughput_ci_is_wal_t95_and_abort_has_no_ci_in_canonical_data`
  で、非帰属ではなく本 wave の閉包拡張に帰属する。**land していない。**
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2、fix 1)。変異走行は probe 2 回 + 本走 1 回。

## 次の一手差分

### 更新

- [T-733] **P1・ユーザー裁定待ち**: 第 1 層として exact 24 path から exact 62 path へ広げる実装は
  branch 上で完成し、変異 5/5 KILLED まで通した。しかし受入全走で
  fig2c の生成経路が外部の旧 grammar lock を decode できずに落ちるため land していない。
  旧 grammar の扱い ({{T:historical-grammar-registry}}) を決めるまで進めない。
  base: 2e830bbb64bfb811c16385cf9f5c1b7614d38ad4a39191136ecbc95d9e1d654e

### 新規

- {{T:closure-second-layer}} **P2・新規**: enforcement source closure の残り 69 module を収載するか。
  第 1 層 62 path の代償 (受入検査 190 件増、閉包 member 編集のたびに epoch が動く) を
  実測したうえで、全 131 へ広げるか、収載を止めて文言で閉じるかを決める。
  成果物影響 = 決めない限り「certified 経路が source-bound」を推移閉包の意味では名乗れない。
- {{T:historical-grammar-registry}} **P1・ユーザー裁定待ち**: 旧 grammar の campaign lock を
  どう扱うか。外部 root に exact-24 map の official lock が 11 件あり (B10 格子 3 件、
  paper-story A-2 認証 8 件)、閉包を広げると decode できない。これは T-733 の land を止めている。
  択一は (a) `HISTORICAL_RAW` に限って旧 grammar を読む versioned decoder を作る、
  (b) 11 件を新閉包で発行し直す、(c) 損失を受け入れて fig2c の生成経路を別の束縛へ移す。
  いずれも現行 certified 経路を緩めないことを必須条件とする。
  成果物影響 = 決めない限り T-733 が land できず、fig2c の再生成も通らない。
- {{T:qualification-schema-binding}} **P2・新規**: qualification schema の live bytes を
  記録 blob と結ぶか。`qualification/artifacts.py` などが live schema を直接使って受理を決める一方、
  `qualification/identity.py` は記録 commit blob を検証するだけで、実際に読んだ live bytes との
  等値を確かめていない。成果物影響 = schema の live bytes を緩めると、同じ campaign epoch と
  記録 code identity のまま qualification receipt の受理集合が広がりうる。
