---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t925-l15-inventory
seq: 1
title: [T-925] docs/dev-wave 予算棚卸し — 削除可能な節は 1 件も無いことを実証し、L2 の未使用枠という別経路を発見した (docs のみ、branch worktree-dev-wave-t925-l15-inventory、計測なし)
---

## 本文

- **裁定 = 実装しない (段 4 で `4→7→8→9`)。** 削除・テスト化とも実施していない。
  `docs/dev-wave/**` の差分はゼロで、本 fragment と insights だけが成果物である。
- **層予算の実測 (段 1 前)**: L0 入口 9,500/9,500 (余白 0)、L1 10,624/10,625 (余白 1)、
  L1.5 9,564/9,566 (余白 2)、L2 単節最大 `DW-O09` 997/1,000。**3 層すべてが上限に張り付いている。**
  堰き止められた契約の行き先はこの 3 層に分散する ([T-925](2)(3) は L1.5、[T-916](c) は L1、
  [T-934](a) は L0)。予算値の定数は 1 bytes も触っていない。
- **削除候補は親と段 2 子が独立に 4 件ずつ挙げ、確定できたものはゼロ件。**
  段 3 の敵対 2 レンズはいずれも NO-GO を返した。内訳は insights が正本。
  - 親 P-a (`DW-O01` prompt 非空 34 bytes) = **refuted**。非空検査は
    `tools/dev_wave_codex.py:149` の `job_id is None` 枝のみで、明示 `--job-id` + `--dry-run` では
    prompt を読まない。実 launch は下流が止めるが、**空 prompt で rc≠0 になる負例テストが無い**。
  - 親 P-b (`DW-M05` pgrep 段落 201 bytes) = **refuted**。`DW-M05` は独自 harness を許し
    その場合の防壁を残している。先行棚卸し [T-291] が「親の待機規律であり tool の射程外」と確定済み。
    F32 は 2026-08-10 に汎用待ち手で自己一致が再発しており「発火実績なし」が偽。
  - 親 P-c (入口 fail-closed 文 170 bytes) = **refuted**。`DW-STOP` は同内容を持つが
    `core.md` 自身が読めないときに自分の読取失敗を止められない。入口の当該文は**再帰の基底**であり、
    削除すると循環した保証になる。親と段 3 レンズ 1 が独立に同じ結論へ到達した。
  - 段 2 子案 (`DW-M04` 201 / `DW-M06` 139 / `DW-O23` 333 / reasoning 散文 163 bytes) =
    いずれも **refuted**。`DW-M04` の機械代替は公式 harness にしか効かず、`DW-M06` は
    timeout 後の継続を殺す負例が無い恒真な保証、`DW-O23` は D128 が「同じ lock を保持したまま
    fold」を逐語決定しており発火実績が偽、reasoning 散文の gate 化は自己申告で迂回できる。
- **唯一の real は入口 `:116-117` (174 bytes) だが両レンズが対立した。**
  レンズ 1 は「routing が `docs/skill-self-improvement.md` に残り wave 開始時に無条件で読まれる」
  として削除可、レンズ 2 は「逐語同義と証明されていない」として不可。親の独立読解はレンズ 1 支持
  (routing 1 と routing 5 が意味を覆い、入口 `:13-14` が同文書の routing を無条件読了させる) だが、
  **`docs/skill-self-improvement.md:30-33` が節削除の実施をユーザー裁定に限るため実装しない。**
  対立を親の判断だけで押し切って安全義務を削るのは規律 2 が禁じる型である。
- **先行事例との整合**: [T-786] (2026-08-11、完全 9 段 + 変異 6/6 KILLED) が既に
  「『発火実績なし × 機械検査で義務代替済み』を両方満たす削除候補はゼロ件」「等価縮約を出し切った」と
  結論していた。本 wave は独立にその結論を再現した。**現行の L1/L1.5 は生きた義務で埋まっている。**
- **新発見 = L2 に合計上限が無い。** `tools/check_docs.py` の層予算は L1 合計・L1.5 合計・
  L2 の単節 1,000 bytes の 3 つだけで、`docs/dev-wave/*.md` にファイル単位の上限も L2 合計の上限も
  存在しない。L2 各節の空きの総和は **7,252 bytes**。新規 L2 節を 1 つ足す費用は入口の条件 dispatch
  表 1 行 (最短 79 bytes) だけである。**L0 を 180〜280 bytes 空けられれば堰き止め 4 件すべてが通る。**
  L1.5 と L1 を個別に空ける従来の枠組みより桁違いに小さい。詳細は {{T:l2-slack-routing}}。
- **受入の要否判定 (docs-only)**: 免除しない。判定手順 =
  `grep -rln "output/insights\|docs/spool" orchestrator/tests/*.py` で変更面を読む test file を
  列挙し、`test_check_docs.py` ほか **10 file が実在**したため免除条件を満たさないと判定した
  (証拠なしの免除をしない)。受入全走を実走し **10,085 passed / 65 skipped、rc=0** (tested tip
  `e7a9c8fb`、lease 保持のまま記録追記後に再走)。`python3 tools/check_docs.py` も rc=0 (違反なし)。
  変異 matrix は `DW-S04` の免除条件「『実装しない』裁定済みかつ実装差分ゼロ」に該当し免除。
- **工数**: codex 子 3 本 (段 2 プラン 1 本 `reasoning=max`、段 3 敵対 2 本並列 `reasoning=max`、
  lane sol / luna)。段 2 は artifact-root の親 directory 未作成で 1 度 rc=2 (起動前終了、成果物ゼロ)。
  `DW-O01` の「既存 `.done` は消さず再利用せず再投入を止める」に従い新 artifact 名で再投入した。
- **運用上の実測**: `tools/dev_waves/launch_authority.py` の `snapshot_authority` は live 実行時に
  `docs/dev-wave/operations.md` と `docs/dev-wave/workers.md` の working tree と authority commit を
  byte 比較して fail-closed する。**この 2 ファイルを編集した時点で codex 子が一切起動できなくなる。**
  棚卸し wave では段 2・3 の子を編集前に投入する必要がある。

## 次の一手差分

### 更新

- [T-925] **P2・棚卸しを実施、削除候補ゼロ件を実証・ユーザー裁定待ち**: 認可された棚卸しを実施した。
  親と段 2 子が独立に 4 件ずつ挙げた削除候補は、段 3 の敵対 2 レンズと親の意味検索で
  **確定できたものがゼロ件**だった (唯一の real は入口 `:116-117` 174 bytes だが両レンズが対立)。
  候補 4 件のうち (1)(4) は裁定どおり memory 既知型につき docs 追記不要、(2)(3) は L1.5 の
  余白 2 bytes に対し 184 bytes 必要で塞がったまま。実施には入口 `:116-117` の削除可否について
  個別承認が要る。予算値の引き上げは提案しない。
  base: 0a9fcb33680d2bb41ef72a08ab0c8d2bd3bf2c2d53675eb5e7bbbb6c5928d7a2
- [T-916] **P3・(c) は予算で実施不能と実測・ユーザー裁定待ち**: 裁定 (c) の `DW-S01` 配置には
  L1 に 58 bytes 要るが余白は 1 byte。但し書きの (a)「L1.5 集合内の陳腐化した節を 1 つ retire」も、
  本 wave と [T-786] が独立に retire 可能な節をゼロ件と実測したため成立しない。
  **塞いでいるのは読み込み導線ではなく予算である。** {{T:l2-slack-routing}} の L2 経路が通れば
  L1 を使わずに収容できる可能性がある。
  base: 343b9e589d928a4172dc8c71c94547aa574ef1091a173be794e50c40628586ea
- [T-934] **P2・(a) は入口の余白 0 で実施不能・ユーザー裁定待ち**: 裁定 (a) の入口追記は
  最短形で 172〜178 bytes 要るが、`.claude/commands/dev-wave.md` は 9,500/9,500 で余白 0。
  原資候補は入口 `:116-117` の 174 bytes だけで、その削除可否は [T-925] の個別承認と同じ判断に依存する。
  base: 84230bac543a950af9baa7e6866f3d969a955a787e2118d806253d92fcdc9a9f

### 新規

- {{T:l2-slack-routing}} **P2・新規 ([T-925] 段 7)**: `docs/dev-wave/**` の **L2 には合計上限が無く**、
  各節の空きの総和が 7,252 bytes ある (上限は L1 合計・L1.5 合計・L2 単節 1,000 bytes の 3 つだけで、
  ファイル単位の上限は存在しない)。新規 L2 節 1 つの費用は入口の条件 dispatch 表 1 行 (最短 79 bytes)。
  **L0 を 180〜280 bytes 空けるだけで堰き止め 4 件すべてを収容できる**見込みで、L1.5 / L1 を
  個別に空ける従来の枠組みより桁違いに安い。設計すべきは (i) 各契約の発火条件が既存 L2 節の条件と
  一致するか、一致しないなら新規 L2 節が `docs/skill-self-improvement.md:28-30` (D271) の
  「発火実績あり × 機械代替なし × 意味検索で反証も同一発火点の既存正本もなし」を満たすか、
  (ii) L2 化で読み込みが条件成立時だけになる意味変化が許容できるか、(iii) 入口 1 行の原資。
  registry (`tools/check_docs.py` の `REQUIRED_REFERENCE_SECTIONS`) と Codex 側 skill の
  同時更新を伴うため実装面で、Codex author が要る (D95)。
