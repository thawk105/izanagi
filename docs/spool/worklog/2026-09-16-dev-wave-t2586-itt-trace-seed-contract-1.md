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

工数: codex 子 7 本 (plan 1・consult 2・author 2・review 2・fix 1・focus 1 のうち author は
1 本目が停止報告で終了、いずれも gpt-6-astra / medium)。変異は probe 1 走 + 本走 1 走。

## 次の一手差分

### 完了

- [T-2586] 投入経路と束縛付与の双方に型・所属検査を足し、producer が事前登録に無い seed の成果物へ
  束縛を付けられない状態にした。保証範囲は producer の通常実行が書く成果物 JSON と journal JSONL。
  remaining: none
  base: 25e7cc9cef6e783b57e05ab4f915f960e87e982b5e926e3c963df8b539bbcd32
