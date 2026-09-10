あなたは izanagi の開発 wave の**実装子 (fix 担当)** である。コードとテストだけを編集する。
**docs は編集しない。commit もしない。** cwd は wave の worktree である。

## 必読 (読めなければ即停止し、その旨だけを出力する)

- 敵対レビュー (直す対象): `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s6-revA.md`
- 参考 (回帰なしの確認): `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s6-revB.md`
- 裁定 (scope の正本): `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/s4-adjudication.md`
- `orchestrator/campaign/env_contract.py` と `orchestrator/tests/test_env_contract.py` の全文
  (この wave の commit `0324d627` で追加された部分を含む)

## 直すもの (レンズ A の should-fix 3 件のみ)

**問題の本質**: 事前登録した変異 M1 / M6 が「狙った検査を消しても、後段の bootstrap fuse や
隣接検査が同じ入力を拒否する」ため、赤の理由が一つに絞れていない。変異が形式上 KILLED でも
**帰属が成立していない**。これは本 repo の規律違反 (DW-M01) なので、実効 gate へ再照準する。

### fix-1 — 構造・連番・隣接の各検査を、fuse に遮られずに撃てるようにする

`validate_generations` の内部を、**bootstrap fuse を含まない検査部分**と
**fuse** に分ける。fuse なしの内部 validator を test から直接呼べるようにし、
その**受理集合**を直接検査する (「別の例外 message になったこと」ではなく
「入力が受理されるようになったこと」で欠陥を検出する)。

- 隣接検査の負例は、`is_valid_successor` の呼出しを削除したときに
  **受理されてしまう**ことで赤になるようにする。
  レンズ A の提案どおり、呼出しの実在を spy で確認する形でもよい。
- 連番検査の負例も同様に、fuse なしの内部 validator の受理集合で撃つ。
- tuple 型検査の負例は、**空 list を使わない** (空 list は fuse でも落ちる)。
  有効な `GenerationEntry` を 1 件入れた list を使い、tuple 型だけを狙う。

内部 validator を公開 API として増やすかは実装の裁量だが、増やすなら
**`_` 始まりの private** にし、production の呼び出し経路を変えないこと。

### fix-2 — hash 一意性検査の負例を collision seam で撃つ

現在の duplicate fixture は「同じ contract を g1/g2 に置く」ため、
一意性検査を消しても no-op successor として隣接検査に拒否される。
**異なる `env_tag` の 1 世代列を 2 本作り、その `contract_sha256` が同じ値になる seam** で
撃つように変える (canonical preimage に `env_tag` が入るため、通常の source drift では
作れない。実効上は collision guard である旨をテストの docstring に書く)。

これが実装困難なら、fix せずに**「M6 の単一理由性は成立しない。production では
SHA-256 collision 時だけ発火する」と報告せよ**。テストを甘くして通す方向は禁止。

### fix-3 — module-level の結線を固定する

`validate_generations(GENERATIONS)` の module-level 呼出しが、
index / `REGISTRY` の構築より**前**に存在することを AST で固定するテストを足す。
現状はこの結線を削除しても既存テストの観測値が変わらない。

### fix-4 (レンズ B の nit、ついでに閉じる)

`REGISTRY` の反復順序と `lookup()` の例外 message を pin する。
`list(ec.REGISTRY) == ["linux-baremetal", "pegasus"]`、未知 tag と非 hashable 入力の
完全な `str(exc)` を検査に加える。

## 絶対に守ること

- **既存テストの期待値を変更しない。** 反転・緩和・skip・削除・xfail 化を禁じる。
  赤なら実装側が誤りである。期待値のほうが誤りだと判断したら、
  **実装を変えずに報告して止めよ**。
- ただし **commit `0324d627` でこの wave が追加したテストは編集対象である**
  (帰属を成立させるための作り直しが本 fix の目的)。既存 = `0324d627` より前から
  tracked だったテスト、と読むこと。
- `ExecutionEnvironmentContract` / `_canonical_obj()` / `contract_sha256` / `lookup()` /
  `REGISTRY` の外部から見た挙動を変えない。基準値は pegasus
  `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`、linux-baremetal
  `1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7`。
- `orchestrator/campaign/env_contract.py` と `orchestrator/tests/test_env_contract.py`
  **以外の file を編集しない。** docs も凍結成果物も触らない。
- 裁定が scope 外とした機能 (`CurrentContract` / activation record / receipt /
  consumer 移行) を実装しない。
- 指示にない受理集合の拡大・縮小をしない。
- env 固有 literal を `_build_registry` の FunctionDef の外へ出さない。
- 期待値に working tree の hash など揮発する診断 payload を焼き込まない。

## 検査と報告

- **pytest を実走してはならない** (login node で重い処理を走らせない規律)。
  **緑だと主張してはならない。**「実装済み・未実走」と書け。
  受入全走と変異走行は親が計算ノードで行う。
- テストを新設・改名したなら、それを制約する meta-test の有無を静的に確認して報告せよ。
- 完了報告に次を書け。
  - fix-1 / fix-2 / fix-3 / fix-4 それぞれについて `closed` / `partial` / `見送り` と理由。
  - **変異 M1 / M6 が fix 後に「狙った検査の削除でだけ赤になる」ことの論証**
    (どのテストが、どういう理由で赤になるか)。
  - 所有外の caller・共有 fixture・consumer test への波及可能性の静的な列挙。
  - 現行の受理・拒否挙動が変わっていないことの確認。

## 総括

出力の末尾に `## 総括` 節を置き、直した内容を 10 行以内でまとめる。
