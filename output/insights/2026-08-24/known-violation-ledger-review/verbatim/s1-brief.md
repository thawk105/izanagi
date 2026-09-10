# 段 1 brief — known-violation 台帳の見直し

## 依頼 (ユーザー、逐語)
「known-violation の見直しをしてください。現在は known-violation は育っていく一方でしょうか？
すでに知られた violation について、テストされているところが間違えているならそれをなおす、
テストが間違えているならそれを直すなどして、known-violation を 0 件にする努力が必要だと思います。
タスクは適切な大きさで切り、適切でない大きさに関しては別途タスクを切り出して先送りにしてください。」

## 確定済みユーザー裁定 (前提)
- D662 決定 4/5: known-violation 登録は正規の逃げ道。増加自体は問題としないが、低優先度の残置に
  せず高優先度タスクとして随時解決する。本 wave はその「随時解決」の実行である。
- 履歴の書き換え (rebase / force / filter-branch) は禁止。push も禁止。

## 親が実測した事実 (一次資料で確認済み。推測ではない)
1. 台帳 53 件。`python3 tools/check_ai_provenance.py` は rc=0 / 5346 commit / stale 0。
   内訳 malformed-ai-agent 23、missing-codex-author 19、missing-ai-agent 11。
2. 増加は単調。減少は T-1479 の checker 是正 (19 件撤去) の 1 回だけ。
   直近 4 日 (08-20〜23) で 21 件増えた。
3. malformed 22 件は単一 incident で trailer literal 同一
   `product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator`。
   「規則が後から出来た (legacy 免除)」説は**反証済み**: `IDENT`=`[a-z0-9][a-z0-9._-]*` と
   ROLES (orchestrator 非含有) は checker 導入 commit `50c1ef4e` (2026-07-14) から在り、
   `docs/ai-provenance.md` も `f277efd446` (08-08) 時点で同文。真の違反である。
4. 前方訂正 `PR-C01` は「一回限り・`6d7141dc` で消費済み・新しい担い手を追加してはならない」。
5. **本 wave の核。** `_commit_paths()` の merge 分岐は `git diff-tree --cc` の patch 本体が
   非空かで実装面を判定する (T-1479 導入)。両親の独立追加を union しただけの merge も `--cc` は
   非空になる。missing-codex-author 19 件を「finding 対象 path の全行がいずれかの親に存在するか」
   で測ると、**merge かつ novel 行 0 が 10 件** (`a5b7045b12` `311d463f89` `5823caf328`
   `8440a14850` `e39a8d4656` `3eaf2038ec` `387a1daab0` `e86d363a87` `0c0f3e71b3` `bf92f327ca`)、
   merge かつ novel 行あり 1 件 (`b9c07cc22d`、18 行)、非 merge 8 件。述語は差別力がある。
   実測 script: `/work/1/SFC/tanab/dev-wave-jobs/known-violation-review-20260823/measure_union.py`

## scope (この wave でやること)
- **実装 1 点**: merge commit の実装面判定を「著作された行が実在するか」で行う述語へ是正し、
  finding を失う既存エントリを台帳と逐語ミラーテストから外す。
- **docs**: 53 件の全数分類、増加の実測、0 件化の到達可能性の判定、先送りタスクの切り出し。

## scope 外 (別タスクへ先送りする)
- 増加の生成器 (親作成 merge の Codex author 欠落 / `--no-edit` の trailer 欠落 /
  manager による実装面直接 commit) を止める恒久防壁の実装。
- `PR-C01` 前方訂正の拡張 (ユーザー裁定が要る)。
- 逐語ミラーテストが登録を 2 commit に割ること自体の解消。
- D661 の `_message_file_paths()` 同型偽陽性。

## 不変条件 (破ってはならない)
- 絶対規律 2。**ゲートを緩めてはならない。** 是正は「著作が実在しないものを実装面と呼ばない」
  方向だけで、著作が実在する merge を通してはならない。
- 履歴を書き換えない。既存 commit の trailer は不変。
- 台帳からエントリを外してよいのは、是正後の checker がその SHA で finding を出さなくなる場合だけ。
  外し忘れると `known-violation-stale` で rc=2、land が `RC_PROVENANCE=29` で止まる。

## 親の provisional 裁定 (攻撃対象)
- **(P1)** 既存 53 件のうち、checker 側の是正で消せるのは上記 10 件だけであり、
  残り 43 件は真の違反で AI 側の作業では 0 にできない。
- **(P2)** 「finding 対象 path の全行がいずれかの親に存在する」だけでは不十分で、
  行の**並べ替え**による著作 (親 A の signature と親 B の body を選ぶ等) を排除できない。
  述語は「両親の行順と整合する共通 supersequence であること」まで強める必要がある。
- **(P3)** D721 (pure-union 免除の却下) の射程外である。D721 が却下したのは
  「combined diff の全行に `-` が無く `+` が高々 1 個」という**形状**述語で、却下理由は
  「最終形から自動解決と手解決を区別できない」だった。本述語は解決者を問わず
  「著作された行が在るか」を直接測る。ただし D721 は現行正本なので段 4 で再裁定 package を出す。

## 成果物影響 (DW-G05)
是正しない場合、全史監査は「1 行も著作していない merge」を実装面著作と呼び続け、
そのたびに exact SHA の免除が台帳へ 1 件増える。免除は Codex author gate の恒久的な穴であり、
直近 4 日で 21 件増えた。受理集合の観点では、**本来 gate の対象外だった 10 件が
現在 exact SHA 免除として受理集合に入っており、是正で述語側の判定へ戻る。**

## 分割方針
段 2 は 1 本。段 3 は 2 レンズ並列 (sol/luna)。段 5 実装は 1 本。段 6 レビュー 2 本 + fix 1 本。
