## 所見

1. **must-fix — smoke が C の成功と F の abort・再試行を確認していない。** [driver:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/orchestrator/campaign/vhash_forwarding_prototype.py:406) は many_ops の `attempts` だけを合算する。[patch:149](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/patches/cicada-forwarding-variant.patch:149) の F は `attempts` を増やさない。C が全試行に失敗し、F が一度も発火しなくても、C の `attempts>0` だけで主計測へ進める。**成果物:** 動作を確認していない C/F の throughput が比較図に載る。**修正案:** C の `success>0` と F の `f_aborts>0` を別々に確認し、F 側の abort 後の再試行・完了も計数で拘束する。

2. **must-fix — inert 比較の前処理正規化が不足している。** [patch:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/patches/cicada-forwarding-variant.patch:15) と [patch:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/patches/cicada-forwarding-variant.patch:100) は `#if` の外に空行を追加する。[driver:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/orchestrator/campaign/vhash_forwarding_prototype.py:139) は行 marker だけを除き、空行を比較に残す。既定 macro でも pin と patch のハッシュが異なり、smoke が停止する可能性が高い。**成果物:** inert receipt が得られず、計測へ進めない。**修正案:** pin と patch に同一 argv を使う現状を保ち、正規化を契約に明記して空行を扱うか、追加の空行をなくす。実際の前処理一致は親の smoke で確定する。

3. **should — gate 登録が plan v2 の inert 値契約から外れる。** [condition_meaning_gate.py:251](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/orchestrator/campaign/condition_meaning_gate.py:251) の新規 3 entry は `inert_values=("0",)` を設定せず、[test_condition_meaning_gate.py:3549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/orchestrator/tests/test_condition_meaning_gate.py:3549) も空集合を固定している。**成果物:** 明示的な `-D…=0` を inert な対照として扱うという裁定と、gate の受理集合が食い違う。**修正案:** 3 entry と登録簿テストを plan v2 の値に合わせる。

4. **should — 図の欠測とゼロを混同し得る。** [make_figures.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/output/insights/2026-09-29/vhash-forwarding-prototype/make_figures.py:53) と [driver:283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/orchestrator/campaign/vhash_forwarding_prototype.py:283) は欠けた counter field を `0` として足す。parser は `threads` が list かだけを確認するため、欠落した `success` や `f_aborts` が正常なゼロとして図に入る。**成果物:** 欠測を失敗率や abort 数の実測値と誤認する。**修正案:** counter schema と必須 field をレコード受理時に検証する。

## 反例

stock validation との照合では、`forward_visible` の pending 条件 `< ts'`（[patch:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/patches/cicada-forwarding-variant.patch:87)）と read 検証の `>= ts`（[pin transaction.cc:550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/external/ccbench/cc/cicada/transaction.cc:550)）に境界差がある。ただし `ts'` の低 8 bit は自身の thread id であり、256 thread 以下では他 thread の版と同時刻にならない。今回の静的検査では、この差から **serializability 違反となる具体的 interleaving は確定できなかった**。

## 閉じた段 3 反例

`later_ver_` の破棄と `new_ver_->wts_` の書換えは前進成功箇所にあり（[patch:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/patches/cicada-forwarding-variant.patch:210)）、前進後の INSERT・DELETE・scan も abort する（[patch:273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/patches/cicada-forwarding-variant.patch:273)、[patch:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/patches/cicada-forwarding-variant.patch:289)、[patch:302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-forwarding/patches/cicada-forwarding-variant.patch:302)）。段 3 の三つの C++ 反例はコード上では閉じている。gate receipt も compile 条件の証拠と表示される。一方、C/F の実行証拠は所見 1 のため未完である。

## 総括

**段 6 の受入前に、smoke の発火・成功判定と inert 比較を修正・実測する必要がある。** M1〜M4 のテストは対象の分岐を直接検査し、M5 は登録 inventory で検出する構造だが、変異を実際に殺した実測結果はこの静的レビューにはない。対象の実装ハンクには Codex `role=author` の記録があり、欠落は確認しなかった。テスト・build・計測は実施していない。