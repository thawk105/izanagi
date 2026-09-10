# 段 1 brief — [T-1784][T-1847] 受理記録の正となる置き場所を 1 本に固定する

- wave: `dev-wave-t1784-admission-single-path`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path`
- base commit: `24014bdb259d971571f22b54a8f10a49352b825f` (local main と同一)

## scope

B-4 の pre-run admission record について、**検証器が受理する record の置き場所を、
driver_kind から一意に決まる repository-local な canonical path だけに限る。**
それ以外の path に置かれた record は、内容が正しくても受理しない。
編集面は `orchestrator/campaign/p3_b4_admission_record.py` と、その呼び手 2 本
(`p3_b4_closed_critic.py` / `p3_b4_launcher.py`) の必要最小の追随、および対応テストに限る。

## scope 外 (実装しない)

- **§5 残り 9 欄の型検査。D1332 (2026-09-01 ユーザー裁定) が「見送る」と決着済み。**
  再訪条件「記入時の型の誤りが実際に 1 件観測されたとき」は成立していない (§5 は D1060 により 1 欄も未記入)。
  依頼引数はこれを本 wave の主目的 (1) としていたが、引数の前提は既裁定に覆されている。
- §5 の欄を埋める・§5.1 の規範を足す・記入者/レビュー者を指名する (T-1769 / D1266)。
- `orchestrator/campaign/p3_b4_wiring_probe.py` と同テスト (稼働中 t1909 wave の所有)。
- 外部 append-only ledger、署名 token、送信前 attest 層 (T-1842 / T-1843、いずれも別裁定)。
- 仮想リスク向けの一般化・互換層・新 gate・新台帳。

## 確定済みユーザー裁定

- **D1050:** 受理記録の正となる置き場所を **1 本に固定する**ことで、複数 path から都合のよい方を
  選べる余地を閉じる。内容同一性検査だけで足りるとする案は却下済み。
- **D998:** 検証は provider 作成より前。**警告・環境変数・CLI flag の逃がし道を作らない。**
- **D1000:** §5 の機械検査は構文的非空と期待値行 grammar に限る。**関数名・例外文言・docstring・
  テスト名は検査範囲を越える語を使わない。** 証明できないことは docstring に逐語で列挙する。
- **D1332:** §5 残り 9 欄の型検査は見送る。

## 不変条件

- 絶対規律 2 を緩めない。受理集合は**狭くする方向にだけ**変える。既存の拒否は 1 件も緩めない。
- D1000 の命名規律を新しい検査にも適用する。新しい例外文言・関数名は「置き場所が canonical か」
  以上のことを主張しない。**「record が正当である」「§6 前提条件を充足した」と読める語を使わない。**
- 逃がし道 (環境変数・CLI flag・既定引数・警告降格) を作らない。
- `p3_b4_admission_record.py` は `projection_closure_manifest()` の閉包 member であり
  (`p3_b4_closed_critic.py:646`)、本 wave の編集で `projection_sha256(kind)` の値は 3 driver とも変わる。
  **これは想定内である** — §5 の期待値行は未記入で、committed record も存在せず、literal hash を
  pin する test / 台帳は 0 件 (test は `C.projection_sha256(kind)` と独立再計算で live 導出)。

## 成果物の形

- 検証器 1 箇所の canonical-path 関門 + 負例テスト。
- 変更後も既存の全拒否経路が同じ署名で拒否し続けることを示すテスト。
- module docstring に「この関門が証明すること・しないこと」を逐語で追記。
- worklog / decisions fragment (段 7)。

## 分割方針

実装面は 1 単位 (同一 module + その直近呼び手 + テスト) で素集合に割れないため、
Codex `role=author` 1 本。段 6 の敵対レビューは異なるレンズ 2 本。
受理集合を狭める変更なので**軽量版にしない** — 段 2・3・5・6 をすべて行う。

## 実アンカー表

|対象|位置|役割|
|---|---|---|
|`verify_b4_admission_record`|`orchestrator/campaign/p3_b4_admission_record.py:671`|唯一の chokepoint。3 呼び手すべてが通る|
|`_repository_relative_regular_file`|同 `:415`|record path を repo 相対へ解決。関門はこの直後|
|`PREREGISTRATION_REPOSITORY_PATH`|同 `:45`|同種の固定 path 定数の既存の置き場所|
|`_SECTION5_SOURCE_CELL_CONTRACT_FAILED`|同 `:56`|例外文言の既存様式 (D1000 の命名規律の実例)|
|module docstring|同 `:1-29`|証明しないことの逐語列挙先|
|`create_b4_closed_critic_pair`|`orchestrator/campaign/p3_b4_closed_critic.py:1231,1268`|呼び手 1|
|`assert_b4_certified_arm_pair`|同 `:1904,1931`|呼び手 2 (certified pair の関門)|
|`projection_closure_manifest`|同 `:623-648`|閉包に検証器の bytes を含む|
|launcher 内部呼び|`orchestrator/campaign/p3_b4_launcher.py:347,352,520,536,562`|呼び手 3|
|launcher CLI `--admission-record`|同 `:637`|運用者が path を選べる唯一の外部入口|
|テスト fixture (`admission.json` を repo root へ置く)|`orchestrator/tests/test_p3_b4_admission_record.py:218-225,699`|canonical path 化で追随が要る|
|closed critic 側 fixture|`orchestrator/tests/test_p3_b4_closed_critic.py:153,465,520,770`|同上|

## (P1) 親の provisional 裁定 — 段 3 の攻撃対象

- **(P1-a) 「1 本」は driver ごとに 1 本と読む。** record schema の
  `expected_closed_critic_projection_closure_sha256` は単一値で、検証器は
  `projection_closure_sha256_by_driver[driver_kind]` と照合する。§10 は
  「admission record を **driver ごとに発行する**」と書く。よって canonical path は
  `driver_kind` の全域関数であり、運用者に選択の余地が無いことをもって「1 本」を満たす。
  対立案: 全 driver で単一 file とし、record 側に 3 値を持たせる (schema 変更を伴う)。
- **(P1-b) canonical path はコード側の定数で固定してよく、文書側の規約の着地を待たない。**
  path 名は §5 の値欄でも §5.1 の解除条件でもなく、D1050 が既に「1 本に固定する」と裁定済み。
  対立案: 事前登録文書に path を明記するまで実装しない (= D1050 を実装しない)。
- **(P1-c) 関門は `verify_b4_admission_record` 1 箇所で足りる。** 3 呼び手すべてがここを通り、
  CLI もここへ収束する。対立案: CLI 側でも独立に検査する (二重化の要否)。
- **(P1-d) canonical path はまだ実在しないので、既存成果物を壊さない。** repo に
  `p3-b4-prerun-admission/v1` の record file は 1 件も存在しない。

## DW-G05 成果物影響

放置すると、運用者は同じ内容の record を複数 path に置き、実走後に都合のよい方を
certified pair の関門へ渡せる。proof chain の根が「どの record を選んだか」で分岐し、
事前登録との束縛が実質的に効かなくなる (D1050 の理由そのもの)。

## 受入・実測環境

- login node 上の `python3 tools/run_tests.py` (受入全走) と焦点走。計算ノード dispatch は不要。
- 性能計測・build・campaign 実走は行わない。
