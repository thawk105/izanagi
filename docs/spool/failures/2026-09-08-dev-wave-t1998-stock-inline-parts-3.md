---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t1998-stock-inline-parts
seq: 3
---

## 新規

### {{F:substring-presence-test-walks-past-disabled-predicate}}. 部分文字列の存在検査は、無効化された述語を素通りする [恒真ゲート] [テスト代表性]

- 事象: 新設した投入器の「出力先が repository の外であること」を検査するテストが、
  投入器の source text に `target == repo or repo in target.parents or target in repo.parents`
  という部分文字列があることだけを見ていた。変異走行でこの述語を
  `if False and (target == repo or ...)` へ書き換えたところ、**部分文字列は残るのでテストは緑のまま**で、
  変異が生き残った (probe 1 回目、M9)。同型の穴が `.git` 祖先の拒否と receipt の hardlink 拒否にもあった。
- 根本原因: shell script 内の python 断片を「読める形」でしか検査していなかった。
  述語の**存在**は述語が**効いていること**を含意しない。存在検査は、述語を無効化する変異に対して恒真である。
- 恒久対応: 当該 script から python 断片を取り出して実際に実行し、repository の内側を指す入力で
  `SystemExit` になること、外側では通ることを検査する挙動テストへ変えた
  (`orchestrator/tests/test_t1998_launcher_contract.py` の repo 境界 / `.git` 祖先 / hardlink の 3 件)。
  部分文字列検査は残してよいが、それだけを根拠にしない。
- 再発検知: 変異事前登録で当該述語を `if False and (...)` へ倒す変異を持ち、
  KILLED を要求する (本 wave の M9)。probe で SURVIVED になった時点で穴が露見する。

### {{F:stray-gitlinks-without-gitmodules-block-every-wave}}. `.gitmodules` の無い gitlink を commit すると、以後の全 wave の受入 preflight と provenance 監査が赤になる [手順漏れ] [恒真ゲート]

- 事象: local main の tip `c12e25078` が `.codex/worktrees/` 配下の gitlink 110 件を
  `.gitmodules` の entry 無しで取り込んだ。これは commit した wave の成果物ではなく、
  同じ checkout で別 session が作った Codex worktree の管理 dir である。
  main を取り込んだ wave で 2 つのことが同時に起きる。
  (a) `git submodule foreach --recursive` が `No url found for submodule path` で rc=128 になり、
  受入待ち手が `stage=preflight-index-flags rc=70 source_rc=128` で
  **テストを 1 件も走らせずに止まる**。
  (b) provenance 監査が当該 commit を「実装面に Codex role=author がない (110 paths)」として
  違反に数える。`--range c12e25078^..c12e25078` 単独で 1 件中 1 違反であり、
  DW-O25 の全史監査が赤になるので land できない。
- 因果の実測: 同じ wave の受入 1 回目 (main 取り込み**前**、commit `0b761064b`) は
  preflight を通過して merge 段まで進んだ。main を取り込んだ 2 回目 (commit `3c888a8c2`) だけが
  preflight で落ちる。差分は main の取り込みだけである。
- 根本原因: 広い staging が、同じ checkout に別 session が作った worktree 管理 dir を拾った。
  gitlink は `.gitmodules` を伴わなくても commit できるので commit 時点では何も止めない。
  **壊れるのは次に main を取り込む別 wave の側である。**
- 恒久対応: **未実施。** 他 session の commit を書き換えないので報告に留めた。候補は
  (1) main 側で当該 gitlink を取り消す commit、(2) 受入 preflight の前に `.gitmodules` と
  index の gitlink 集合の一致を検査する gate。どちらもユーザー裁定が要る。
- 再発検知: main の gitlink path 集合と `.gitmodules` の `path =` 集合の一致検査。
  不一致なら次の wave の受入は必ず preflight で落ちる。

### {{F:mutation-masked-by-asymmetric-negative-fixture}}. 片側だけを変える負例は、対称な層に mask されて狙った層の証拠にならない [テスト代表性]

- 事象: 2 つの arm の toolchain manifest から canonical digest を再計算して記録値と照合する層を
  検査するつもりの負例が、target 側の digest だけを変えていた。変異でその**再計算を丸ごと消しても**、
  後段の arm 間一致比較が代わりに赤にするので緑にならず、変異が生き残った (probe 1 回目、M12)。
  負例は通っていたが、通していたのは狙った層ではなかった。
- 根本原因: 片側だけを変える負例は、arm 間の対称性を見る層と、各 arm の内容を見る層の
  両方を同時に発火させる。前者が先に赤にすると後者の証拠にならない。
  「その層だけが赤にする入力」になっていない。
- 恒久対応: 両 arm が**同じ**非 canonical な digest を持つ負例を足した。arm 間比較と result 投影は通り、
  canonical 再計算だけが単独で拒否する
  (`orchestrator/tests/test_t1998_stock_inline_pair.py::test_shared_noncanonical_toolchain_digest_is_rejected`)。
- 再発検知: 各層に対する変異を事前登録し、probe で SURVIVED になった変異は
  「他層の mask」を先に疑う (`docs/dev-wave/mutation.md` の DW-M02)。
