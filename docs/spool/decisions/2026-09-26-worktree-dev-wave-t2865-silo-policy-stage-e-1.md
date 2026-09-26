---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-26
wave: worktree-dev-wave-t2865-silo-policy-stage-e
seq: 1
---

## {{D:silo-policy-stage-e}}. silo-function-policy 軸の段階 E — planner なしの兄弟 driver を置き、方策の検査は driver 側で共有検疫の後に掛け、coder の入力は driver の 1 関数が偵察の二値と射程文と自系列の履歴だけから組む。計算ノードでの実走と投入用の job body は段階 F の前提へ送る

**決定:** D2214 決定 7・8 と D2243 項 1 に従い、軸 `silo-function-policy` の段階 E を次の形で実装する。設計の正本は D2214 と設計 insight、実装の記録は `output/insights/2026-09-26/t2865-silo-policy-stage-e/README.md`。

1. **driver は兄弟 module `orchestrator/campaign/p3_s4_loop_policy.py`。** C++ 形と IR 形を CLI の形で選び、形・性能動作点・verify 構成 (legacy + 性能構成) を campaign identity に焼く。形ごとに別 campaign になる。
2. **方策の検査は共有の `p3_s4_loop.quarantine()` を変えずに driver 側で掛ける。** 順は、共有検疫 (構造 + effect、書き込まない) → 型付き構文検査 → 単独 TU compile → auditor の digest 照合と deny-only veto → 書込 → 書いた本文から digest を再照合 → pipeline。preview・拒否の記録・実走が同じ gate 関数を通る。IR 形は `parse_policy_ir` (閉じた tagged object) → `render_policy` の後の本文に同じ gate を掛ける。
3. **planner を外したので、停止は予算 (iteration・walltime) だけ。** proposal は `{coder, auditor}` の 2 key に閉じ、`planner`・`value`・`prior_critic_reverse` を拒否する。逆方向の推奨は E では接続しない。`LoopState` に field を足さない。
4. **firewall の機械化 = coder 入力を組む関数を 1 つにする。** 段階 D の `projection.json` は固定 path から key 集合と型を検査して `binary`・`scope` だけを出す。自系列の履歴は当該 campaign の履歴 file だけから読み、justification を落とす。失敗の理由は実コードに実在する固定 reason の閉じた code 集合 (集合外は固定 code) に正規化し、verifier の witness は決定的な順で先頭 8 件と件数・全 cycle 数だけを渡す。critic 診断は既存 K2 と同じ 6 文字列 field の閉じた形だけを受ける。自由文 `scope` の内容保証は主張しない。
5. **auditor の違反型の上限は呼出し側の引数にする。** 既定 21 は不変で、本 driver だけ 26 (型 22〜26 を足した auditor 改訂に対応) を渡す。既存 3 軸の受理集合は変えない。
6. **preview で拒否された候補は `--record-reject` で WAL と履歴に記録し、iteration を 1 消費する。** gate を通る候補は記録しない。LLM の失敗の多くが構文検査・単独 TU の拒否になる見込みで、記録しないと次の coder が自分の拒否理由を受け取れない (規律 3)。
7. **coder role 2 本 (`coder-v4-autonomous-policy`・`coder-v4-autonomous-policy-ir`) と auditor 改訂は、2026-09-26 にユーザーが具体差分を明示承認した。** auditor の型 17〜21 の免除は sort IR と本軸の機械生成 IR 候補に限り、本軸の LLM 候補は監査する。型 25・26 は設計 §3.4 に合わせ、候補ごとの sanitizer と hook 計数を要求しない形にした。role 登録簿は 16 件。
8. **MOCC template proof の test は、auditor.md の whole-file sha256 の一致ではなく、proof に記録した auditor 項目と現行 auditor.md の項目の一致で束縛する。** 承認済みの auditor 改訂で whole-file sha が変わり、test が赤になった。項目の全真検査は残し、proof JSON は取り直さない。production の consumer (`require_proof_binding`) は auditor の sha を見ていない。
9. **計算ノードでの実走 (build・verify・bench) と、本 driver 用の Pegasus job body は E の完了条件から外し、段階 F の前提とする。** 既存の `tools/pegasus/p3_s4_loop_pegasus.sh` は `p3_s4_loop` 固定である。

**理由:**
- 共有 `quarantine()` に分岐を足す案 (段 2 plan、設計 §4) は、段階 C/D の診断経路 (`prepare_policy` は共有検疫の後に同じ検査を呼ぶ) の引数契約を壊すか二重 compile にする、と段 3 の 3 レンズが揃って指摘した。driver 側に置けば既存 3 軸と C/D の経路の受理集合が変わらない。
- `prior_critic_reverse` を proposal に置くと、coder 側の値で停止時点が変わる (段 3 レンズ A・B)。
- 失敗理由の自由文 (例外経路の `eval-exception: …`) と witness の全件は、coder 入力に探索と無関係な文や際限の無い量を持ち込む (焦点再レビュー 1、親の点検。段階 C の負例では cycle が 39,124 件出た)。
- auditor の上限を全域で 26 に広げると sort 軸の proposal の受理集合が変わる (段 3 レンズ C)。
- MOCC proof の置換は規律 7 (現行 bytes との差だけを理由に記録を無効にしない) に従う。束縛の意味 (MOCC 用の auditor 項目がそろっていること) は保たれている。
- 実走を E に入れると、新 driver 用 job body と契約 test の新設が要り、E の完了が計算投入の承認待ちに依存する。手順書 §3 F が実 LLM の 1 iteration を E2E の出口としている (段 3 レンズ C)。

**却下した選択肢:**
- 共有 `quarantine()` に本軸の分岐を足す — 上記。
- 形を 1 つの campaign に混ぜる — critic digest と履歴が他の形の結果を coder に見せる (段 3 レンズ A)。
- anomaly の辺の key を coder 入力の前に検証する (焦点再レビュー 2) — trace は固定骨格の計装が出し、候補は受理契約で文字列・pointer・外部名を持てないので注入経路が無い。不正 key は verifier の integrity に既に数えられる。仮想リスク向けの検査は足さない。
- MOCC template proof を取り直す — 1 job で済むが legacy 記録の上書きになり、束縛の意味を保つ test の置換で足りる。
