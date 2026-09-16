---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2586-itt-trace-seed-contract
seq: 1
title: [T-2586] ITT trace 契約に事前登録 seed の検査を足し、producer の束縛と consumer の受理集合の食い違いを閉じた (コード + テスト、branch worktree-dev-wave-t2586-itt-trace-seed-contract、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

反実仮想 ITT の trace 契約は `step_policy_seed` を一切検査せず、共通 gate は policy 2 セル在時に
非 `None` しか要求しなかった。事前登録に無い seed の成果物にも producer が
`counterfactual_preregistration` を付けて受理し、offline consumer が同じ成果物を必ず拒否する
状態を作れた。投入経路と束縛付与の両方に、型と登録済み 12 値への所属を要求する検査を足した。
詳細と限界は insight `output/insights/2026-09-16_t2586-itt-trace-seed-contract/`。

**段 2 の棄却を段 4 で覆した。** プランは凍結事前登録 §3 の「投入経路の契約は変更しない …
`_validate_backoff_trace_contract` を改訂せずに通る」を将来への禁止条文と読み、投入時の拒否を
落として束縛付与枝だけを直す案にしていた。段 3 の 2 レンズが独立に「それは当該試験の実施方針の
記述であって永久の禁止ではない」と逐語で反証した。決め手は机上でなく実測で、`.pbs` は seed を
十進構文と非空でしか見ず `--step-policy-seed 7` をそのまま producer へ渡す。**非登録 seed と
exact axes は実在の投入経路で同時成立する。**

**検査順序が保護そのものだった。** 軸検査を先に、seed 検査を後に置き、seed 違反は別 message で
上げる。逆順にすると、cells は正しく別の軸だけがずれている既存負例 3 件が seed 違反で先に落ち、
`match="one exact diagnostic cell set"` が外れて既存 assert を書き換える羽目になる。
変異 M9 はこの順序 1 つだけを動かし、期待どおり 1 node で死んだ。

**親の列挙漏れが 1 件。** 投入経路を締めると赤になる既存 test を、親はレンズの列挙 (2 件) に
実測の 1 件を足しただけで 3 件と裁定した。4 件目は実装子が指示どおり止まって報告して初めて出た。
原因は呼び出し点の全数から出さなかったことで、正誤表で全 20 呼び出し点の表を作って閉じた。
段 6 の 2 レビューと焦点再レビューが独立に 5 件目の不在を確認した。F386 へ再発として記録した。

**既存 test 4 件は入力 fixture の seed だけを直した。** assert・`match=`・期待辞書・ループ構造・
既存 parametrize case は 1 文字も変えていない。test 関数の削除・改名はゼロ (123 → 133)。
旧命題「seed 未指定でも束縛が付く」は閉じる穴そのものなので保護と数えない。失われる被覆は、
明示的な `None` と seed 引数の省略の負例を両 cohort・両層に新設して置き換えた。

**段 6 のレビューは A が所見ゼロ、B が minor 2 件。** B-1 (cohort1 の型負例が cohort2 と非対称で
`isinstance` への弱体化を殺せない) を fix 子が閉じた。fix 子は producer を一時的に弱めて新負例が
赤になることを実測し、sha256 で復元も確認している。変異 M7 はこの追加負例を含む 2 node で死んだ。
B-2 (JSON / journal の test が `main` 配線を通らない) は仮想リスク側として scope 外に裁定し、
保証範囲を insight に明記した。

**cohort1 の 12 seed は凍結原典・実装・consumer の三者で完全一致。** 親が機械照合し、段 3 の
1 レンズと段 6 の 1 レビューも独立に逐値照合した。凍結事前登録 2 件は byte 単位で不変で、
sha256 も consumer の pin と一致する。

`tools/run_tests.py` は本 wave 中、子・親を通じて `qstat -Q` preflight で rc=16 を返し続けた
(計算ノード混雑)。実測はすべて自走 harness と変異 harness の dispatch 経路で行った。

**受入全走が実在の赤を掘り当てた。** `test_ccbench_spawn_sites.py` の `_DEFERRED_GATE_MEMBERS` は
build sink を (path, kind, scope, lineno) で pin する。本 wave が producer へ 31 行足したため
2 sink の行番号がずれ (3910→3941、4303→4334)、cross-product が 28 triple 分の未審査扱いになった。
2 回の独立した受入走で同じ 4 node が決定的に赤くなっている。sink・scope・kind・定義集合は同一で、
ずれているのは anchor だけなので、pin を動的導出へ書き換えず 3 箇所・計 5 整数を現行行へ直した。
**anchor が効いている負例は合成していない** — 受入が古い anchor で 2 回とも赤くなったことが、
production で取れた負例そのものである。原因は段 1 の pin 閉包検索を自分で `head -40` で切り、
見えた範囲を閉包として扱ったこと。F376 へ再発として記録した。

**受入が 9 回とも赤になり、2 つ目の blocker を閉じた。** 本 wave の変更に帰属する赤 (行番号
anchor) を閉じた後も、shard-0 の
`test_certified_writer_authorization_caller_inventory_is_closed` が 9 回中 7 回落ち続けた。
逐語は毎回 `FileNotFoundError: '<repo>/.t316-live-<乱数>'`。同 test は repo 全体を `rglob` で
**走り終えてから** dot-dir を除外するため、同じ受入走の `test_t316_sandbox_probe.py` の fixture が
repo 直下に作る一時 dir を辿っている最中にそれが消えると落ちる。**本 wave と無関係の suite 内
競走で、どの wave にも等しく当たる。** t316 側は fixture のコメントが repo 内に置く理由
(SandboxProfile が /tmp を隠す) を明記しているので直さず、走査側を `os.walk` へ替えて
repo 直下の dot-dir を降下前に刈った。**被覆は恒等**で、走査対象は変更前後とも 420 件、
追加も削除も空集合、`.t316-live-*` を消す再現 20 回すべてで落ちない。自走 `test_campaign.py` も
変更前後とも 342 passed / 59 failed / 3 skipped で完全一致する。
**scope 外の一般化ではなく、成果を main へ届ける前提条件として閉じた。**

**段 8 の改善候補 2 件はどちらも採らなかった。** (1)「`--reasoning` の段別制約が docs から
引けない」は取り下げ — `DW-C01` に「`--reasoning` は plan/consult で必須。他段指定は rc=2」と
既に書いてあり、docs の欠落ではなく親が読んだうえで適用を誤っただけだった (dry-run が投入前に
止めたので実害なし)。(2)「隔離 session の親は投入先 worktree へ git を向けられないので、
`DW-S05-A` に成果の回収手順が無い」は実測由来だが、`docs/dev-wave/**` の L1.5 予算が満杯で
収容できなかった (追記すると 9850 > 9696 bytes)。意味等価な既存記述の削減は見つからず、
独立 3 例も無いので、D782 が委任する D730 の手順に従い「実施しない」で閉じた。上限は上げていない。
本 wave は所有 2 file の内容 copy + sha256 照合と、投入時刻起点の mtime 走査による所有外の
無変更確認で代替した。

工数: codex 子 7 本 (plan 1・consult 2・author 2・review 2・fix 1・focus 1 のうち author は
1 本目が停止報告で終了、いずれも gpt-6-astra / medium)。変異は probe 1 走 + 本走 1 走。

## 次の一手差分

### 完了

- [T-2586] 投入経路と束縛付与の双方に型・所属検査を足し、producer が事前登録に無い seed の成果物へ
  束縛を付けられない状態にした。保証範囲は producer の通常実行が書く成果物 JSON と journal JSONL。
  remaining: none
  base: 25e7cc9cef6e783b57e05ab4f915f960e87e982b5e926e3c963df8b539bbcd32
