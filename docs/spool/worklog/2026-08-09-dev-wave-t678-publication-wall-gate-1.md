---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t678-publication-wall-gate
seq: 1
title: [T-678] receipt 公開直前の最後の可逆点で wall gate を再評価する形へ直した — 字義どおりの「publication 完了後」は create-only 制約で実装不能と確定した (コード + docs、受入 7685 passed / 20 skipped、変異 4/4 KILLED・事前登録一致、branch worktree-dev-wave-t678-publication-wall-gate)
---

## 本文

- **依頼は「publication 完了後にも wall gate を再評価する」だった。** 段 4 で**字義どおりには
  実装不能**と裁定し、範囲を正式に縮約した。receipt は create-only 公開のため、final path が
  可視化された瞬間に別 consumer が `accepted` を読める。その後の再評価は受理を取り消せず、
  取り消せない再評価で process rc だけを変えれば receipt と rc が矛盾する。
  実装したのは「output publication・published audit・**公開する exact bytes の write + fsync** を
  終えた後、receipt 可視化の直前 = 最後の可逆点での再評価」である。設計判断は
  {{D:late-admission-gate-at-last-reversible-point}}。
- **塞げない残余を隠さない。** `os.link` / `os.replace` 自体、親 directory の fsync、
  staged temp cleanup、lock 解放、return から process 終了までは gate の外に残る。
  レンズ A の指摘どおり**この残余は 10〜20 秒に限定されず任意に長くなり得る**。
  字義どおりの保証には commit protocol の再設計が要るため裁定パッケージ候補として返す
  ({{T:publication-commit-protocol}})。
- **段 3 が親 brief を 2 点倒した。** (i)「accepted receipt の wall 値と上限が矛盾したまま通る」は
  誤りで、checker は accepted の `actuals.wall_clock_s > limit` を拒否する。実際の欠陥は
  staging / publication の時間が `actuals` に入らないことである。(ii)「受理集合は狭まるだけ」も
  不正確で、採用案は receipt temp の二度目の write を消すため「一度目は成功し二度目だけが失敗する」
  冗長な失敗面が無くなる。拡大ではなく重複の解消として意図的に受け入れ、不変条件を
  「publication I/O が成功した**論理 job** について狭まるだけ」へ書き換えた。どちらも裁定文で撤回した。
- **効く範囲も縮約した。** `tools/codex_worker_launch.py` の production caller は repo 内に存在せず
  ([T-595] 実測)、現行 `DW-O01` は raw `codex exec` を使う。したがって本 gate が守るのは
  dogfood receipt と、[T-665]/[T-662] の集約案が採られた場合だけである。**現行 dev-wave の
  子成果採用条件は本 wave では変わらない。**
- **段 6 のレビューは must-fix 1 件。** 追加 node の「変更前赤」が意図した inode 検査ではなく
  観測器の `AttributeError` に依存していた。これを kill と数えると、二重 temp write へ戻った変異を
  検出済みと誤認する。fix はテスト観測器のみ (production 無変更) で、
  `_write_json_temp` を receipt path 限定で数え「temp 作成 1 回 + final receipt の inode 同一」という
  production から見える形へ置換した。焦点再レビューで 2 件とも closed。
- **`DW-M01` の「過剰拒否を検出する正例」は変異として登録できなかった。** `tools/mutation_harness.py` は
  失敗 node 集合の**完全一致**で KILLED を判定するが、過剰拒否の波及は受理経路の 23 test 関数以上に
  及び期待集合を正確に予測できない。正例の義務は baseline 緑と、MT1〜MT4 の各走で
  `test_positive_p1_normal_job_is_accepted` が緑のままであることで担保した。乖離は `DW-O12` に従い
  ここに記録し、harness 側の改善候補として {{T:mutation-positive-control-subset}} を起票した。
- **主張しないこと。** 実障害で 10〜20 秒級の停滞が起きる頻度・実在、F57 の原因がこの穴であること、
  フレークが消えたこと。親実測は 4 秒の論理的注入であり、`write` / `fsync` / `os.link` / lock 競合と
  同じ機序ではない。F57 は複数 producer が混在し、本 wave はそれを閉じない。
- **provenance 検査 rc=1 は本 wave 由来ではない。** 統合 commit 後の full-history 監査が挙げた
  23 件はすべて main の祖先 (別 wave の `role=orchestrator` 形式違反ほか) で、
  `git merge-base --is-ancestor` で全件確認した。本 wave の commit は 1 件も含まれない。
- **受入は 2 回走らせた。** 1 走目 (main `b409bd28` 取り込み時点) は 7660 passed / 20 skipped。
  lease 待ちの間に main が進んでいたため land 対象 tip にならず、取り込み直して再走した。
  2 走目 = land 対象 tip `03374f20` で **7685 passed / 20 skipped** (1379 秒)。
  この記録 commit だけが 2 走目より後で、差分は docs のみ (コード変更なし)。
  なお lease 取得後の main 差検査を段 8 で足したところ、3 回目の投入前に実際に発火して
  (peer が `2169a06c` を land 済み) 走行前に止めた。無駄な全走を 1 回防いでいる。
- エージェント工数: Codex 8 session (plan 1 / 段 3 相談 2 / 実装 1 / 段 6 レビュー 2 / fix 1 /
  焦点再レビュー 1)。親 = brief・実測 probe 1 本・裁定・統合 commit・変異・受入 2 走・記録。
- 一次資料と逐語 = `output/insights/2026-08-09_t678-publication-wall-gate/`。

## 次の一手差分

### 完了

- [T-678] launcher の受理判定を最後の可逆点へ移し、staging と published audit の費用を
  gate に含めた。字義どおりの「publication 完了後」は create-only 制約で実装不能と確定し、
  残余と再設計の要否は {{T:publication-commit-protocol}} へ分けた。
  remaining: none
  base: 0ff549a16abfe53ccc7453876a0c5dd3b4e301b1d3427ecee6359cc1780ceb53

### 新規

- {{T:publication-commit-protocol}} **P2・新規・ユーザー裁定待ち**: create-only 制約の下で
  「receipt publication 完了後の受理再評価」を成立させる commit protocol を再設計するか裁定する。
  候補は schema 世代更新・2 段 receipt・可視化と admission の分離。現状は最後の可逆点までしか
  塞げず、`os.link` / directory fsync / lock 解放の停滞は任意に長くなり得る。
- {{T:receipt-post-commit-exception}} **P3・新規**: receipt の atomic create 後に例外
  (`_fsync_parent` 失敗・lock unlock 失敗) が起きると、final path に `accepted` receipt が残ったまま
  fallback が output を消し process rc=2 を返す組合せを構成できる。既存欠陥で本 wave は悪化させて
  いないが、受理主張と成果物の実在が食い違う。
- {{T:atomic-publish-output-rollback}} **P3・新規**: `_atomic_publish` は output の final path へ
  直接書き、例外時に rollback しない。write / fsync が失敗すると `output_published_by_run` が
  false のままなので fallback も消さず、launcher-error receipt と partial output が併存しうる。
- {{T:launcher-interrupt-rc-split}} **P3・新規**: `KeyboardInterrupt` / `SystemExit` では
  launcher-error receipt (rc=2) を書いた後に例外を再送出するため、receipt の `launcher_rc` と
  OS process の rc が分離する。receipt を発行しないか rc を正規化するかを決める。
- {{T:staged-temp-replacement-window}} **P3・新規**: staged temp を `Path` で保持する間、
  同一 UID の別 process による置換を束縛していない。artifact directory を単一 writer 境界として
  明文化するか、fd / inode / hash の再束縛を入れるかを決める。
- {{T:replace-invalid-publication-pin}} **P3・新規**: receipt publication の `os.replace` 経路
  (invalid partial の置換) について、staged temp の同一性と cleanup が回帰テストで固定されていない。
  `os.link` 経路だけが新テストで固定されている。
- {{T:mutation-positive-control-subset}} **P3・新規**: `tools/mutation_harness.py` は失敗 node 集合の
  完全一致でしか KILLED を判定できないため、受理集合を縮小する wave が `DW-M01` の要求する
  「過剰拒否を検出する正例」を変異として登録できない。波及が広い正例向けに部分集合一致
  (期待 node が実測失敗集合に含まれること) を許す枠を設けるか裁定する。
