---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2182-k2-eval-wiring
seq: 1
title: [T-2182] K2 宣言アームの評価経路を Pegasus へ配線した — 依頼が挙げた前提 4 件は着地済みで、実際の停止点は condition gate への offline 依存の未配線だった (コード + テスト + insight、branch worktree-dev-wave-t2182-k2-eval-wiring、変異 5/5 KILLED・期待 node 完全一致)
---

## 本文

- **依頼と持ち越し本文が挙げた前提 4 件は、4 件とも main に着地済みだった。** 専用 env タグ・
  calibration の取り直し・binding の固定・provenance の追跡は [T-2232] (2026-09-05) と
  [T-2406] (2026-09-08) で入っていた。持ち越しは 2026-09-02 時点の写しのままで、記述どおりに
  着手していたら既存実装を作り直していた。着手前の一次資料照合で判明した。
- **実際に欠けていたのは 2 点である。** job body が driver へ K2 引数を渡す口と、
  condition gate へ offline の FetchContent 情報を渡す配線。**後者が評価経路の実際の停止点で、
  env の受け口だけを足しても 2026-09-02 と同じ場所 (supply=preprocess-failed) で止まる。**
- **段 3 の子は「受け口が別 wave 所有の file にあるので依存待ち」と判定したが、これは
  2026-09-02 の記述に依拠した stale な判断だった。** 親が現物を確認すると
  `condition_meaning_gate.capture_define_inputs` は既に `configure_args` を受け取っており、
  同 file は 1 byte も変えずに済んだ。子の所見は real、scope 判定は不採用とした。
- **driver 入口で manifest と coder role を相互必須にする裁定は、段 5 で撤回した。**
  実装子が停止し、既存テストが「K2 と宣言したが取得結果が 0 件」の経路を意図して守る正例だと
  示した。ユーザーが gate の追加を scope 外と明示しているので撤回し、裁定パッケージへ回した
  (下記「新規」)。**親が段 4 で採用したのは誤りで、既存の登録済み正例を確かめていなかった。**
- **段 6 レビューが偽の帰属を 1 件見つけた。** K2 の負例テストが、K2 の関門ではなく
  AI worktree container の guard によって赤くなっていた。専用 checkout では同じ変異が
  素通りする。repository root を tmp ベースへ変え、sentinel 実行体の非実行を stderr 検査より
  先に確かめる形へ直した。
- **job body への変異は 48 件の定数マスクを作る。** `test_registered_fragment_mutants_have_one_static_failure`
  が自身で fragment 変異を注入する meta-test のため、job body を変異させると parametrized 族が
  一律に赤くなる。runner argv を期待 node 6 件へ絞ってマスクを外し、単一理由の kill を取った。
- **親の手順の誤りが 2 件あった。** (a) 敵対レビュー 2 本を、fix 子が編集中の worktree へ
  向けた。2 人が別の版を読み、片方は既に直った赤を must-fix として報告した。(b) 変異走行中に
  insight を staging し、harness が untracked file を検出して中止した (rc=2)。どちらも
  再投入で回復したが、段 8 の改善候補とした。
- 受入は 22085 passed / 68 skipped / 6 failed。恒常赤は所要時間台帳の被覆率 1 件だけで、
  本 wave の新 nodeid に帰属する。実測値を add-only で足して 99.363690% にした。残る 5 件
  (codex launcher 4 件・campaign lock corpus 1 件) は再走で緑になる一過性で、非帰属である。
- **Pegasus で評価経路が通ったとは主張しない。** 本 wave は配線までで実投入していない。
  完了条件 4 件のうち達成は依然 1 件 (知識 manifest の受領証) である。

## 次の一手差分

### 更新

- [T-2182] **P1・部分完了**: K2 入力経路の生死確認は済み、評価経路の配線も入った
  (job body の K2 env seam と、condition gate への offline FetchContent 情報の受け渡し)。
  残るのは固定 SHA の専用 checkout からの実投入で、condition gate を越えて WAL の
  BUILD_START へ到達するかを実測する。完了条件 4 件のうち達成は依然 1 件で、残る 3 件
  (provenance 束縛・stock と異なる identity・gate の terminal verdict) は実投入で初めて測れる。
  手順は `tools/pegasus/README.md` §7、run card は
  `output/insights/2026-09-02_t2182-k2-arm-liveness/README.md`。
  base: 71b24a2d47f3beed4d60033bb87303abaa87862ecfe68df9f8ca09c0606feaf0

### 新規

- {{T:k2-manifest-only-fail-open}} **P2・ユーザー裁定待ち**: driver の `--run-iteration` で
  `--knowledge-manifest` を渡し `--coder-role` を省くと、campaign identity と知識受領証は K2 に
  束縛される一方、coder 出力は非 K2 schema で読まれ K2 consumer (schema・anomaly・参照 index) を
  通らない。K2 として記録された候補が K2 検査を受けずに WAL の BUILD_START と certified 選択へ
  入りうる。**単純な相互必須化はできない** — 既存テスト
  `test_main_manifest_only_accepts_legacy_flattened_proposal` が
  `retrieval_result.status = "completed_empty"` / `sources: []` の manifest で
  「K2 と宣言したが取得結果が 0 件」の経路を意図して守っているためである。推奨案は
  「manifest の sources が非空のときだけ `--coder-role` を必須にする」で、これなら上記正例を
  1 件も壊さずに閉じられる。Pegasus の production 経路は [T-2182] の job body 側で既に閉じて
  いるので、残るのは driver 直接起動の経路だけである。裁定を求める点は「この閉じ方を採るか、
  現状のまま (job body だけで守る) を維持するか」である。
