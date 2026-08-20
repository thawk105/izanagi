## 総括

P1 は「実装しない」を推奨する。D499 は正式 decision であり、item2 の解除条件はユーザーの明示命令である。  
非対称な command 記述と一般論だけでは、その解除を明示したとは読みにくい。  
母集団 closure も未成立で、少なくとも `check_subprocess_bytecode_guard` と `s1_known_axes_freeze` 経路が探索外にある。  
静的所見のみで、pytest の緑は要求・主張していない。

## (P1) への裁定推奨

### 実装する解釈

「既知4候補を起点に分類・修正し、恒久保留へ新規登録しない」という command を、item2 を含む修正命令と読む解釈には一定の根拠がある。

- ユーザー逐語は「永遠にスルーしない」「テスト側か対象側を直す」と述べている（[worklog 611:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/docs/archive/worklog-phase3-0817-611.md:14)）。
- item4 だけが full-history scan の維持を明記され、item2 は保護されていない。
- item2 は実行 skip の登録ではなく「修正の保留」なので、「新規恒久保留禁止」が修正着手を要求すると読む余地はある。

ただし採用するなら、段4で「D499 item2 を supersede する明示命令」として記録すべきであり、単なる非対称性から親が確定してはならない。実装する解釈は条件付きでのみ妥当。

### 実装しない解釈（推奨）

こちらを推奨する。

D499 は正式に `docs/decisions.md:20696` に存在し、「テスト側の比例欠陥は恒久保留、削除も修正もしない、解除はユーザーの明示命令」と定めている。archive 側も「残件は母集合の未閉包のみ」と明記している（[worklog 638:487](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/docs/archive/worklog-phase3-0817-638.md:487)）。

したがって、

- item4 を保護する明示記述は、item4 の範囲を守るためのもの。
- item2 について何も書かれていないことは、解除命令ではない。
- 「恒久保留への新規登録禁止」は、既存 item2 の修正保留を解除する文言ではない。
- 「永遠にスルーしない」も、一括解除ではないと同じ記録内で限定されている（[worklog 611:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/docs/archive/worklog-phase3-0817-611.md:18)）。

item2 を実装することは、D499 の「修正しない」という処分から非同値な択一へ戻る行為であり、DW-S04 の「承認済み裁定を非同値な択一へ戻さない」に抵触する（[core.md:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/docs/dev-wave/core.md:98)）。

推奨 scope は、母集団再走査と item1/3/4 の再確認記録だけ。item2 の実装は、command 原文に `item2`、`test_dev_waves_integration.py`、または「D499 の解除・修正」を直接指定する文言が確認できた場合だけ有効とする。

## 母集団 closure への所見

- **深刻度: Critical。`check_subprocess_bytecode_guard` が未算入。**  
  [tools/check_subprocess_bytecode_guard.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/tools/check_subprocess_bytecode_guard.py:71) は `orchestrator/` と `tools/` 以下の全 `.py` を再帰列挙する。さらに [test_check_subprocess_bytecode_guard.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_check_subprocess_bytecode_guard.py:224) は real ROOT に対して実行する。これは tracked Python file 数に比例する D463(b) 型で、既知11 node の外に少なくとも1 nodeある。反証には「この node が既定走行されない、または入力集合が固定である」証拠が必要。反証されれば新規 node は取り下げるが、37 stem という記述の訂正は残る。

- **深刻度: High。`orchestrator/campaign` が tools 限定探索から漏れている。**  
  [test_s1_known_axes_freeze.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_s1_known_axes_freeze.py:86) と [test_s1_known_axes_freeze.py:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_s1_known_axes_freeze.py:486) は `M.build_document()` を real ROOT で in-process 実行する。実装側は [s1_known_axes_freeze.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/campaign/s1_known_axes_freeze.py:340)、[s1_known_axes_freeze.py:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/campaign/s1_known_axes_freeze.py:375)、[s1_known_axes_freeze.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/campaign/s1_known_axes_freeze.py:462) で `output/campaigns` の wildcard 集合を読み、[s1_known_axes_freeze.py:718](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/campaign/s1_known_axes_freeze.py:718) から全候補を処理する。少なくとも「探索対象外の real-ROOT 経路」であり、D463 第3区分か比例 node かの判定が未了。固定用途集合の cardinality 上限を示せれば第3区分として新規 D335 node から外せるが、closure 方法論には追加が必要。

- **深刻度: Medium。37 stem の算術が現 tree と一致しない。**  
  brief は [handoff.md:82](/work/1/SFC/tanab/dev-wave-jobs/t1222-population-closure/handoff.md:82) で `tools/*.py` を37 stemとするが、直接の `tools/*.py` は38本ある。特に [check_subprocess_bytecode_guard.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/tools/check_subprocess_bytecode_guard.py:1) は現 HEAD に存在し、T-1115 で追加された新しい直接 stem である。意図的除外なら除外規則と対象外理由を明記すべき。反証されれば「37 analyzed + 1 wrapper/新設 checker を明示除外」と記述を直すだけで、除外対象が本当に非比例なら node 数は変わらない。

なお、`test_campaign_import_invariant.py` の repository scan は既に growth hold に登録されているため、新規 node としては数えていない（[growth_test_holds.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/growth_test_holds.py:170)）。

## 裁定パッケージ候補

段4では少なくとも次を裁定対象にするべき。

- D499 item2 を今回の command が明示的に supersede したのか。明示性が確認できなければ S2 実装を scope から外す。
- `test_check_subprocess_bytecode_guard.py::test_real_repo_clean` を既知11に追加し、保持・修正・第3区分のどれに分類するか。
- `s1_known_axes_freeze` の2 real-ROOT nodeについて、campaign family の固定上限を証明できるか。
- 38 stem を基準に closure を再実行すること。
- 実装なし裁定なら、DW-S04 により変異 matrix は免除できるが、受入全走は免除できない（[core.md:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/docs/dev-wave/core.md:93)）。