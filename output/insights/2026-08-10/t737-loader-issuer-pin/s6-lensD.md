親申告の `83 passed / 6.88秒` は受入全走の値であり、変異結果ではありません。以下の変異判定は静的予測で、pytest・mutation harness は未実走です。

## 所見 D-01 — production loader の KILLED が calibration mask になる

file:line: [`test_env_contract_activation.py:87`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:87>)、[`env_contract.py:535`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/env_contract.py:535>)、[`s4-adjudication.md:108`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s4-adjudication.md:108>)

問題: 変更前は transition gate が先に負例を拒否するが、G/P 縮退 mutant は最後の不正 row を通過させる。その後 production loader は存在しない `output/synthetic-activation/...` の calibration を検証し、別理由で fail-closed する。loader test は transition message を要求するため raw node は赤くなるが、受理集合は変わらず、DW-M03 上の有効な kill ではない。

放置時の成果物影響: mutation ledger の layer 1 KILLED 数と「production loader が量化点を検出した」というレポート参照が過大になり、実際には calibration が拒否した受理集合を transition gate の証拠として記録する。

修正案（実装しない）: synthetic calibration を実際に通過できる fixture にするか、loader node を `MASKED/diagnostic-only` として KILLED から除外する。issuer node は current state を差し替えているため、fail-open の有効 kill として分離する。

静的に予測される raw node 対応は次のとおりです（実走未確認）。

| mutant | raw で赤くなる想定 | M03上の有効 kill |
|---|---|---|
| G-N1/N4/N8/N64 | loader G/P、issuer G/P の4本 | issuer G/P。loader G/P は calibration mask |
| P-N1/N4/N8/N64 | P negative の loader/issuer 2本 | issuer P。loader P は calibration mask |

したがって、G 縮退で P negative が raw で赤くなること、P 縮退で G negative が raw で緑のままになること自体は成立します。ただし前者の loader 側を transition kill と数えるのは不成立です。

## 所見 D-02 — 純増 frontier の「実測」表現が過大

file:line: [`s4-adjudication.md:137`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s4-adjudication.md:137>)、[`test_env_contract_activation.py:646`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:646>)

問題: 事前登録・変更前 HEAD 走行の対象は N=1,4,8,64（一部は N=4,64）のみで、N=5〜63 は mutation 実測されていません。`4 ≤ N ≤ 64` は M=65 fixture に対する静的な envelope であり、プログラム全体の実測 frontier ではありません。

放置時の成果物影響: 台帳とレポートが未実走の N=5〜63、実 registry が65件を超えた場合まで「実測済み」と参照し、将来の受理集合の変化を見落とす。

修正案（実装しない）: 「実測 `{4,8,64}`」「M=65 fixture に対する静的推論 `4≤N≤64`」「N≥65 は fixture-equivalent」と分けて記録する。N≤3 の純増ゼロは既存の second/third/fourth node（[`test_env_contract_activation.py:1013`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:1013>) など）から静的には整合しますが、変異実走は未実走です。

## 反証のない点

- Spec C の `OVERREJECT` は、[`test_env_contract_activation.py:1712`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:1712>) と [`test_env_contract_activation.py:2415`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2415>) の positive 2 node を受理から拒否へ変えるため、両 node が有効 kill になる静的予測です。positive だけに runner argv を絞る判断も妥当です。
- Spec B の G/P-N4、N64 の SURVIVED 期待は静的に正しいです。変更前 suite の最大 fixture は4 envで、`[:4]` は全 row、`[:64]` は当然全 rowを含むため、既存 node の挙動は変わりません。実走は未実走です。
- 層名は限定付きなら正確です。層1は synthetic registry/authority を使った `current_activation_state()` の負例経路、層2は synthetic registry を注入した `issuer.main()` integration で、E2E ではありません。`ident` 経路未被覆も real です。

## 残る穴

1. `ident.py:217`、[`ident.py:292`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/ident.py:292>)  
   leaf を直接呼ぶため certified lock/admission 経路は未検証。放置時は未承認 transition の activation tuple が `admission_status="admitted"` 側へ入り得る。修正案: ident 経路を別 node で pin する。

2. [`test_env_contract_activation.py:1659`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:1659>)  
   M=65 production-loader negative の変異 kill が calibration mask に覆われる。放置時は layer 1 の検出力参照が transition gate を証明しない。修正案: valid calibration fixture または明示的な mask 分類を用意する。

3. [`s4-adjudication.md:156`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s4-adjudication.md:156>)、[`s4-adjudication.md:158`](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s4-adjudication.md:158>)  
   M=65 synthetic registry は実 registry の成長や `[:len(GENERATIONS)]` 型の縮退を検出しない。放置時は実件数依存の弱体化が受理集合へ残る。修正案: registry 件数との関係を別 pin または再裁定 trigger にする。

## 総括

(a) 変異事前登録は訂正が要ります。raw expected node と、有効 kill／calibration mask を分離してください。

(b) **NO-GO**。mutation は未実走で、さらに layer 1 の KILLED 主張に mask があるため、そのまま land させられません。

(c) 「layer 1 が変異を殺した」と「4≤N≤64を実測した」は撤回・限定が必要です。層名そのものと `ident` 未被覆の主張は維持できます。