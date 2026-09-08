## 所見

1. **恒真の直接検査**

- 主張: 提案された照合は D920 型の恒真ではない。右辺は Git HEAD と一致する受領証 bytes から parse した leaf、左辺は受領証外の report・journal・campaign 現物から再計算した leaf であり、受領証の leaf 自体は再計算へ入力されない。
- 原典: `orchestrator/campaign/s8c_acceptance_receipt.py:1940-1951`, `orchestrator/campaign/s8c_acceptance_receipt.py:945-955`, `orchestrator/campaign/s8c_acceptance_receipt.py:1973-1980`, `orchestrator/campaign/trial_registry.py:6168-6173`, `orchestrator/campaign/trial_registry.py:6306-6308`, `orchestrator/campaign/autonomous_trial_completeness.py:4288-4314`, `orchestrator/campaign/autonomous_trial_completeness.py:4366-4394`, `s2-plan.md:75-87`
- 判定: **refuted**。発行時と検証時が同じ関数を使うこと自体は独立性の証拠ではないが、値の出所は別の現物 bytes である。leaf と aggregate だけを書き換えても左辺は変わらないため、同じ値同士の自己照合にはならない。
- 深刻度: **nit**
- 成果物影響: 実装されれば正当な current v5 の leaf 値は変わらず、現物と異なる leaf の受領証だけが受理集合から外れ、certified 選択は変わらない。

2. **負の対照は新検査まで到達する**

- 主張: 計画の leaf 差替え負例が既存検査に先取りされるという攻撃は成立しない。差替え値は正規 SHA-256 として schema を通り、受領証を commit し直すので HEAD 照合を通り、report・journal bytes と digest は不変で参照 hash を通り、aggregate も forged leaf 群から更新するため既存 aggregate 検査を通る。
- 原典: `s2-plan.md:142-157`, `orchestrator/campaign/s8c_acceptance_receipt.py:945-955`, `orchestrator/campaign/s8c_acceptance_receipt.py:1947-1951`, `orchestrator/campaign/s8c_acceptance_receipt.py:1973-1989`, `orchestrator/campaign/s8c_acceptance_receipt.py:2014-2027`
- 判定: **refuted**。計画どおりなら最初に赤くする差分は planned trial-leaf mismatch であり、既存 schema・参照 hash・aggregate gate は拒否理由にならない。
- 深刻度: **nit**
- 成果物影響: forged current v5 は新検査によってのみ受理集合から除外され、`VerifiedAcceptanceReceipt` とその proof 参照は生成されない。

3. **正例は検査本体を通る**

- 主張: 正例が条件不成立や検査前 return で緑になるという攻撃は成立しない。no-build fixture は `do_build=False` を report に追加し、fixture 作成時と standalone 検証時の双方で実関数 `verify_s8c_cross_binding` を呼ぶ。後者は planned schema guard と equality を通り、`_cross_binding_no_build_receipt` の本体で digest を計算する。build 正例も計画上、発行後の受領証を track して `verify_acceptance_receipt` まで通す。
- 原典: `s2-plan.md:100-120`, `s2-plan.md:126-137`, `orchestrator/tests/test_s8c_acceptance_receipt_v2.py:231-257`, `orchestrator/tests/test_s8c_acceptance_receipt_v2.py:490-516`, `orchestrator/campaign/autonomous_trial_completeness.py:4165-4188`, `orchestrator/campaign/autonomous_trial_completeness.py:4217-4230`, `orchestrator/tests/test_trial_registry.py:1822-1837`, `orchestrator/tests/test_trial_registry.py:1874-1903`
- 判定: **refuted**。no-build の 4230 行目の return は mode 本体を実行した後の正常 return であり、新 equality の手前で抜ける return ではない。正例単独は共有関数の stub を検出できないが、planned leaf 差替え負例が equality 削除・自己比較を別途殺す。
- 深刻度: **nit**
- 成果物影響: 正当な no-build と materialized build の current v5 は受理集合に残り、既存 leaf と proof 参照の値は変わらない。

4. **3 mode の実発火範囲**

- 主張: 新検査が実際に発火するのは `no-build` と materialized `build` である。`build-failure` は exact fallback cell に descriptor がないため、planned leaf 検査より前の `_verify_v2_trial_arm_execution` が拒否する。また issuer も fallback cell を leaf 発行前に拒否する。この非到達性はプラン自身が明記している。
- 原典: `orchestrator/campaign/autonomous_trial_completeness.py:336-367`, `orchestrator/campaign/autonomous_trial_completeness.py:4225-4261`, `orchestrator/campaign/autonomous_trial_completeness.py:4262-4277`, `orchestrator/campaign/autonomous_trial_completeness.py:4579-4589`, `orchestrator/campaign/s8c_acceptance_receipt.py:1425-1445`, `orchestrator/campaign/s8c_acceptance_receipt.py:1982-1989`, `orchestrator/campaign/trial_registry.py:6152-6157`, `s2-plan.md:33`
- 判定: **refuted**。build-failure では新検査は発火しないが、その mode の受領証自体が既存 gate を越えないため、任意 leaf を持つ受領証が受理される経路にはならない。プランも隠していない。
- 深刻度: **nit**
- 成果物影響: build-failure の受理集合は引き続き空であり、certified 選択や proof 参照に任意 leaf が流入する変化はない。

5. **修正範囲は current v5 に限定され、brief の API 全体 scope は満たさない**

- 主張: 4 種の現物について、current v5 では report を decode して再投入し、manifest は既存 `_assert_digest` で再読し、build では Layer 3 report・全 artifact refs・`loop_state.json` の verified bytes を再読するため、現物面は閉じる。一方、個別 leaf 再導出を current v5 のみに限定し、legacy v3/v4 は aggregate-only のまま残すため、brief の無限定な「`verify_acceptance_receipt` が leaf を現物から再導出する」という scope は満たさない。
- 原典: `s1-brief.md:17-19`, `origin-verbatim.md:6-7`, `s2-plan.md:92`, `s2-plan.md:223-237`, `orchestrator/campaign/s8c_acceptance_receipt.py:1953-1954`, `orchestrator/campaign/s8c_acceptance_receipt.py:2004-2025`, `orchestrator/campaign/autonomous_trial_completeness.py:3317-3329`, `orchestrator/campaign/autonomous_trial_completeness.py:3386-3403`, `orchestrator/campaign/autonomous_trial_completeness.py:3406-3433`, `orchestrator/campaign/autonomous_trial_completeness.py:4366-4399`, `orchestrator/campaign/s8c_acceptance_receipt.py:2043-2055`
- 判定: **real**。プランは legacy の未修正を明記しており隠してはいないが、`verify_acceptance_receipt` 全体について「任意 leaf が通らない」とは言えない。成立する修正主張は「current v5 と `require_current_verified_receipt` の経路を閉じる」までである。
- 深刻度: **must-fix**
- 成果物影響: current v5 の forged leaf は受理集合から外れる一方、v3/v4 は任意 leaf のまま `VerifiedAcceptanceReceipt` を得られる。ただし非 v5 は current capability に進めず、`certifying=False` も不変なので certified 選択の値は変わらない。

## 総括

must-fix は **1 件**です。計画の新照合自体、負の対照、no-build/build 正例には発火しない恒真性を認めませんでした。唯一の must-fix は、実装範囲を current v5 に限定しながら、親 brief が無限定に掲げた `verify_acceptance_receipt` 全体の欠陥を残す scope 不一致です。

判定不能として残した点はありません。pytest は実行しておらず、結論は指定されたコードと consumer の静的追跡によります。