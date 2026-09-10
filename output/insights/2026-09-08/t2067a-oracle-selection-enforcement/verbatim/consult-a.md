## 所見

severity: must-fix  
根拠: `/home/SFC/tanab/.claude/jobs/2abe6e84/tmp/t2067a/artifacts/t2067a/plan.md:16-17,79-81` は選択済み `result.json` 全体を earlier path へ複製する。一方 `orchestrator/campaign/s8b_ratified_freeze.py:3501-3543` は bound artifact から導出した hit と全 repo scan の hit を完全一致させるため、複製した result の workload 軸が未申告 hit となる。scan-neutral な先例は `orchestrator/tests/test_s8b_ratified_verify.py:838-855` の `b"{}"` で、同 file:1173-1178 はそれを置いたまま historical reverify が成功すると固定している。  
攻撃シナリオ: 計画どおり full result copy を置くと、新しい選択強制を削除しても report、judge、verdict は後段 reverify の `closure-hit-mismatch` で拒否する。3 負例とも「1 行を消すと受理される入力」にならない。earlier result を `b"{}"` にし、eligibility だけを True に差し替えれば、強制ありでは `floor-selection-rule-mismatch`、強制なしでは reverify 通過となり単一帰属を作れる。  
成果物への影響: 現案の負例では受理集合縮小を証明できず、単なる拒否理由の前倒しを D1526 の実装証拠として認定してしまう。

severity: must-fix  
根拠: `/home/SFC/tanab/.claude/jobs/2abe6e84/tmp/t2067a/artifacts/t2067a/plan.md:57-60` は既存 2 テストで選択強制を単純 no-op にするが、両テストは既に loader も `object()` へ差し替えている (`orchestrator/tests/test_s8b_verdict.py:1147-1152,1203-1208`)。`docs/decisions.md:46861-46885` の D1504 は呼出しと引数を記録する stub を要求し、loader と selection assert の双方を stub して機構を一度も通さない形を明示的に却下している。  
攻撃シナリオ: loader、selection、reverify を全て差し替えると、選択 gate が呼ばれない、別 object を受ける、root を取り違える変異でも、後段の schema mismatch または freeze mismatch だけで rc=2 になり既存テストは緑を保つ。loader-backed g1 fixture へ移して実 gate を通すか、少なくとも D1504 の記録 stub と呼出し照合を各テストへ入れる必要がある。  
成果物への影響: combined verdict の拒否テストを選択強制の被覆として数えられず、正しさ gate の到達性に欠けたまま certified verdict 経路を完了扱いにできてしまう。

severity: should-fix  
根拠: `/home/SFC/tanab/.claude/jobs/2abe6e84/tmp/t2067a/artifacts/t2067a/plan.md:110-115` は非 g1 を「拒否されない」とする。選択 helper 自体は `orchestrator/campaign/s8b_ratified_freeze.py:3591-3592` で return するが、直後の reverify が同 file:3126-3129 で `generation_number != 1` を `certificate-generation-scope` として拒否する。3 CLI はそれぞれ report:2548、judge:750、verdict:829 で reverify を必ず呼ぶ。  
攻撃シナリオ: loader が正規の active g2 を返しても、新しい 1 行は通過する一方、従来どおり reverify で rc=2 になる。「g2 も正常系として受理維持」という読みでは正例を構成できない。  
成果物への影響: 実装による過剰拒否はないが、受理集合と g2 の report、judge、verdict 利用可能性を成果物や worklog に誤記する。

severity: nit  
根拠: `orchestrator/tests/test_s8b_ratified_freeze.py:972-977` は `build_production_emitter_g1` の build、measure、provenance が固定 seam で、実測代表 bytes ではないと明記する。ただし同 file:1126-1175 は実 g1 generation、approval、active pointer を作り、同 file:1199-1201 は実 loader を通す。  
攻撃シナリオ: 実 build または eligibility 導出の退行は新 CLI 負例単独では検出できない。ただし `_derive_floor_selection_eligibility` だけを差し替え、`assert_g1_floor_selection_identity` 本体は実行するという計画の主張はコード上正しい。  
成果物への影響: 直接の受理集合変更はない。「実 g1」ではなく「production-shaped、実 loader-backed g1」と記すべき証拠精度の問題に限られる。

## 親前提の判定

(P1) refuted — `verify_manifest` 自体に選択 token がなく、将来の直接 consumer が素通りできる API 非対称は実在する。しかし現 production caller は `orchestrator/tests/test_s8b_oracle_manifest_contract.py:31-35,99-104` の4 fileに閉じ、driver は `s8b_oracle_driver.py:664,1351` で launch selection 済み、残る3 fileが本 wave の対象である。新 consumer は inventory を赤にし、公開 API 閉包は残件 (c) 側で扱うべきで、D1526 の3経路実装へ token 化を追加する根拠にはならない。

(P2) refuted — `_GENERATOR_SOURCES` は `s8b_oracle_manifest.py:65-73` の5 fileだけで verdict を含まない。reviewed spec も同集合を `s8b_oracle_spec.py:164-166` で検証する。combined verdict の evidence は `s8b_verdict.py:740-750` の入力成果物 hashだけで、自身の source hashを持たない。現 verdict source hashの literal参照もなく、verdict変更に再 pinは不要である。

(P3) refuted — load直後、reverify前が妥当である。reverify内部へ入れると `test_s8b_ratified_verify.py:1173-1178` の historical 成功契約と D1503 (`docs/decisions.md:46835-46856`) を破る。後段へ置くと同じ selection 違反が先に別理由で落ち、選択強制の到達と理由を固定できない。

## 総括

強制は恒真ではない。loader-backed fixture は active g1を作り、g2だけが helper内で素通りする。  
現 production checkoutには active v2世代がなく、実 production CLIは loaderで止まる。  
must-fixは負例を scan-neutral にすることと、verdict既存テストの純 no-op化を撤回することの2件。  
pytestは指示どおり未実行で、結論は静的検査に基づく。