---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t2591-aggregate-material-report
seq: 1
title: [T-2591] 集約床値が実 issuer から公開材料レポートまで届く正例を足した (テストのみ、branch worktree-dev-wave-t2591-aggregate-material-report、変異 新走 5/5 KILLED・観測 node は新正例 1 件のみ・旧走 5/5 SURVIVED)
---

## 本文

- ユーザー依頼は「集約成果物が材料レポートまで届く正例を作る。現状は合成 repo に prerun
  publication と raw analysis が無く、公開 builder へ渡せない。正例の実体を名指しし、性質だけの
  stub で両層を通す緑にしない。稼働中の producer layer r1/r3 design (T-2293) と編集面が重ならないか
  起動時に検査する。規律 2 を緩めない。Codex author = D95。本題の実装だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外」。
- **着手前の実測で依頼の前提の所在が変わった。** prerun publication と raw analysis が無いのは
  床値 issuer 側の合成 repo であって、材料レポート側の `immutable_publication` fixture には
  両方とも実物がある。よって正例は材料レポート側へ置き、集約入力の合成 helper を無改造で
  import する形にした。
- **決定的な実測: 材料レポート層の present-floor 投影は、issuer が実際に書いた bytes で
  通ったことが無かった。** `_write_floor_preregistration(present=True)` は authority artifact を
  その場の dict で組み立てており (`artifact_sha256` が `"1"*64`、`floor_exact` が `[0,1]`、schema v1)、
  issuer を通っていない。依頼の「性質だけの stub」はここを指していた。
  ただし「過去に一度も実測されていない」とは書かない — 静的調査で過去全体は否定できない。
  言えるのは「現行 test 集合に集約 artifact を builder へ通す node が存在しない」で、
  AST で canonical 関数 31 件と golden 31 件の完全一致を照合して確かめた。
- **編集面の重複検査は 2 回行った。** 起動時: T-2293 の編集面は `p3_autonomous_workload_trial.py` と
  同 test のみで重複 0 (land 済み)。段 5 直前: wave branch 25 本の tip を一括取得し、
  起動直後に別 session が作った床値系 5 本 (t2288-floor-spec-freeze, t2592-calibration-miss-floor,
  t2595-floor-query-legacy-symmetry, t1851-c3c-official-floor, t1338-floor-residual) はいずれも
  main tip のままで commit 0。commit 済み 7 本のうち重なるのは `t2515-calib-rr95-rr5` の 1 件だけで、
  同じ file の別 frozenset (行 52 付近と行 376) を触るため行競合しない。
- **段 3 の敵対相談が親 brief の制約自体を倒した。** 親は「許可する monkeypatch は 3 つだけ」と
  本数で書いたが、指定した `immutable_publication` fixture 自身が 3 つ以上を patch している。
  段 2 のプランは本数制約を満たすため既存 helper へ keyword 引数を足して Git seam を条件化し、
  一時 fixture に実 Git repository を作る案を出したが、**制約側の誤りに合わせてコードを曲げる案**
  として不採用にした。seam の許可を本数でなく機構上の位置で定め直した ({{D:seam-allowed-by-position}})。
- **段 3 が real な検査欠落を 1 件出した。** レポートの `analysis.floor_argument` は authority からの
  投影であって実 evaluator 引数の観測ではない。内部検査も同じ authority と比べるだけである。
  正例は `evaluate_b4_artifacts` を実物へ委譲する記録 wrapper で包んで塞いだ。この穴は変異 M3 が
  実測で裏取りした (新走 KILLED・旧走 SURVIVED)。
- **親の requirement を 1 件撤回した。** brief は「markdown にも非保証が出ること」を要求したが、
  現物を読むと `_render_markdown` は `certification_scope.not_guaranteed` を一切描画しない。
  v1/v2 共通の既存性質で集約固有の欠落ではないので撤回した。markdown への要求は
  集約 artifact の実 path・実 sha256・最大 ratio に限った。
- **段 6 のレビュー 2 本はいずれも実装に must-fix を出さなかった。** レビュー A は禁止面
  1,604 file を bytes 比較して差分ゼロを確認した。所見は変異 spec 側の 2 件
  (M3 の置換範囲、M4 の実際の拒否位置) で、いずれも親の spec では既に回避されていた形だった。
  レビュー B は実装子の報告から G6 契約の列挙漏れを 1 件出した (登録自体は正しく、焦点走で緑)。
- **親の実測で台帳値を 16 倍直した。** 実装子が登録した所要 `79.0` は**単独走**の JUnit 値で、
  module scope fixture の構築 (setup 71.22 秒) を丸ごと含んでいた。群全体を 1 回で走らせた JUnit で
  測り直すと **4.788 秒**。同じ走行で既存 `test_m9_...[True-True]` が 11.491 秒 (台帳既存値 11.0) と
  整合し、台帳の規約が群内走行の値であることが確かめられた。台帳は実装面なので親は直接編集せず、
  Codex の fix 子 1 本で 1 行だけ直した。
- **変異は DW-M08 の新旧両走を行った。** 新走 5/5 KILLED・matching=5、旧走 (新 node を deselect)
  5/5 SURVIVED・失敗 node 0 件。原データからの検算で、新走・probe とも 5 変異それぞれの失敗 node は
  ちょうど 1 件、その node は新正例そのものだった。M4 は投影側だけを変えると内部検査が先に拒否して
  赤が新正例へ帰属しないため、期待 ratio 側も同時に変える 2 層変異にした (DW-M01 単一理由性)。
- **証明範囲を限定して記録した** ({{D:material-report-reach-scope}})。この正例は
  実 Git 凍結、calibration の真正性、`write_material_report` による publish、certification の成立を
  証明しない。材料レポートの現物は `certifying=False` / `closed_world=False` / `evidence-only` /
  `not_in_effect` を宣言している。親が brief で「certification 成果物」と書いたのは現物より強かった。
- **段 8 の docs 変更で焦点走が 2 段階に赤くなり、どちらも実装の回帰ではなかった。**
  1 回目は `docs/dev-wave/operations.md` を未 commit のまま走らせたため、launcher の authority 検査が
  `working tree が authority commit と異なる` で全件 rc=2 になった (116 赤)。段 8 を commit して解消し、
  `test_dev_wave_launch_authority.py` の 6 件は緑になった。2 回目は `test_codex_worker_launch.py` だけが
  96 件赤で、署名は `codex_exit_code=-15` (SIGTERM)・`evidence_status=missing`・`metering_status=missing`。
  **同 file を単独で走らせると 211 passed・rc=0・8.90 秒**だった (負荷 130、下降局面)。
  本 wave の差分 (テスト 3 file と DW-O14 の 3 行) は launcher の process 終端挙動へ到達しない。
  F57 (launcher 族の負荷依存フレーク) と同型の非帰属赤として扱い、hold 登録はしていない。
- **最終受入全走は本記録 commit と段 8 の commit を固定した後に既存 acceptance 経路で実行し、
  耐久 receipt を共通 land が検証する。**
- **運用の実測 2 件。** (1) `git worktree add` は並行 session 多数の下で 40〜50 分かかった (2 本)。
  (2) `tools/dev_wave_submodule_init.py` は**両方の worktree で 1 回目が
  `runtime-io-failure: update-no-fetch` で落ち、同じ引数の再実行で成功した**。
  DW-O08 の「一過性に失敗しうる。1 度だけ再実行」の実例が 2 件連続した。
- 工数: codex 子 7 本 (plan 1 = medium 296.1 s / 13 call、consult 2 = medium 247.6 s / 8 call と
  356.6 s / 10 call、author 1 = medium 770.6 s / 39 call、review 2 = medium 313.5 s / 12 call と
  295.9 s / 10 call、fix 1 = medium 80.8 s / 7 call)。全子 `check_codex_output.py` rc=0。
- 一次資料 = `output/insights/2026-09-15/t2591-aggregate-material-report/README.md`。

## 次の一手差分

### 完了

- [T-2591] 集約床値が実 issuer から公開材料レポートまで届く正例を作り、事前登録した 5 変異を
  新正例 1 件だけが殺すこと、旧走ではすべて生き残ることを実測した。
  remaining: none
  base: 35f8caaec291296343e5b17bc5e3baf5929f9ddb3f59bf5fe49e825d5af1594d

### 新規

- {{T:v1-authority-real-bytes-positive}} **P3・新規**: 単一 authority (schema v1) の present-floor
  経路も実 issuer が書いた bytes で通す正例を作る。現状この経路は手書き dict の stub だけで通っており、
  本 wave は集約 (v2) 側にしか実 bytes の正例を置いていない。
- {{T:publish-aggregate-positive}} **P3・新規**: `write_material_report` (publish) が集約 authority を
  載せた成果物を書けることの正例を作る。publish は公開 builder を呼ばず別に組み立てており、
  出力先の拒否条件・campaign 非交差・commit marker が加わるため、builder の正例から推論できない。
