追加の実欠陥は見つかりませんでした。親が既知とした2件は重複指摘として除外します。

### 1. consumer 網羅

判定: refuted（consumer 取り残しなし）。

`tools/` と `orchestrator/` 全体を `rg` で検索した結果、対象定数の consumer は以下で閉じています。

- Registry・層予算・H2検査・typed-edge 閉包: [tools/check_docs.py:4247](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/tools/check_docs.py:4247)、[tools/check_docs.py:4881](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/tools/check_docs.py:4881)、[tools/check_docs.py:5236](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/tools/check_docs.py:5236)
- synthetic fixture: [orchestrator/tests/test_check_docs.py:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/orchestrator/tests/test_check_docs.py:803)
- 層・外延 pin: [orchestrator/tests/test_check_docs.py:2257](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/orchestrator/tests/test_check_docs.py:2257)、[orchestrator/tests/test_check_docs.py:2702](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/orchestrator/tests/test_check_docs.py:2702)
- 外延・条件配線 pin: [orchestrator/tests/test_check_docs.py:6700](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/orchestrator/tests/test_check_docs.py:6700)
- exact visible section pin: [orchestrator/tests/test_check_docs.py:8072](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/orchestrator/tests/test_check_docs.py:8072)

`_OPERATION_NUMBERS` と `_ALL_OPERATIONS` に O26 を入れていない点も意図どおりで、O26 は L2 registry と条件18からのみ到達します（[tools/check_docs.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/tools/check_docs.py:614)、[tools/check_docs.py:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/tools/check_docs.py:646)）。

### 2. 条件番号18と節番号O18/O26

判定: refuted（採番空間の衝突なし）。

条件18は `(operations, DW-O18)` と `(operations, DW-O26)`、条件26は `(core, DW-C01)` で、path を含む typed pair として分離されています（[tools/check_docs.py:721](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/tools/check_docs.py:721)、[orchestrator/tests/test_check_docs.py:6738](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/orchestrator/tests/test_check_docs.py:6738)）。

### 3. O23/O25 順序検査

判定: refuted（意図せず緩んでも厳しくもなっていない）。

順序 pin は従来どおり O23 と O25 の相対順だけです（[tools/check_docs.py:4893](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/tools/check_docs.py:4893)）。O26 を O25 後へ追加しても、メモリ上の復元検証は `O23=18, O25=19, O26=20` で通りました。

### 4. typed-edge 閉包

判定: refuted（3ケースとも正しく発火）。

- 通常状態: 条件18が O18/O26 を展開し、registry 閉包は欠落なし。
- O26だけ削除: 条件18の契約不一致に加え、`undispatched=DW-O26`。
- 条件18行全体を削除: row count 不一致に加え、O26 の閉包違反。O18 は段5/6/7にも残るため、O18を誤って欠落扱いしない。

grammar primitive も複数節を正しく展開しています（[tools/check_docs.py:2364](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/tools/check_docs.py:2364)、[tools/check_docs.py:2460](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/tools/check_docs.py:2460)、テストは[orchestrator/tests/test_check_docs.py:3238](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/orchestrator/tests/test_check_docs.py:3238)。

### 5. 親の3箇所の byte 圧縮

判定: refuted（既存 pin 非抵触）。

- manager 文の圧縮: [.claude/commands/dev-wave.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/.claude/commands/dev-wave.md:7) は exact H2 pin の対象外。
- `DW-Oxx` と `fix` の空白圧縮: [.claude/commands/dev-wave.md:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/.claude/commands/dev-wave.md:85) は D4 regex pin（[tools/check_docs.py:772](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/tools/check_docs.py:772)）を通過。
- `入口・referenceへ` の圧縮: [.claude/commands/dev-wave.md:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/.claude/commands/dev-wave.md:118) は正規表現・literal・table pin の対象外。
- 条件 dispatch table は構造エラーなし、command は 9,487 bytes / 上限9,500、最長行121 / 上限140。

O26 の literal は外部確定文面と完全一致し、470 bytes です（[tools/check_docs.py:446](/work/1/SFC/tanab/izanagi/.claude/worktrees/crispy-leaping-sparkle/tools/check_docs.py:446)、`dw-o26-section-text.md:1`）。現在の `operations.md` が HEAD 復元中のため、直接の `check_docs.py` は O26欠落の2件で赤くなりますが、これは共有コンテキスト記載済みの一時状態です。

## 総括

追加の real 所見はありません。consumer、採番分離、順序 pin、typed-edge 閉包、圧縮編集はいずれも妥当です。