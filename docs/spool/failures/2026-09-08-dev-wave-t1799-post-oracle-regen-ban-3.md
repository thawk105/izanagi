---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t1799-post-oracle-regen-ban
seq: 3
---

## 新規

### {{F:reused-tree-primitive-freezes-parent}}. 汎用 tree 保護 primitive を再利用したら、守りたい範囲の外まで凍結する設計になっていた [射程過大] [巻き添え]

- 事象: 段 2 の plan は判定済み材料を書込み不能にするのに
  `s8b_expected_materialization.make_snapshot_non_writable()` の as-is 再利用を提案した。
  同関数は対象 root だけでなく **その parent** の write bit も外す。本件で parent にあたるのは
  `FETCHCONTENT_BASE_DIR` そのものであり、`<base>` 直下への新規 entry 作成 (別依存の populate、
  masstree prebuild directory の作成) を巻き添えで壊す。
- 根本原因: primitive の射程 (何を守るか) を、呼び手の要求 (何を守りたいか) と照合せずに
  「同じ形の処理があるから使える」で採ろうとした。primitive 側の parent 凍結は
  元の用途 (使い捨て worktree の凍結) では正しく、共有 base では正しくない。
- 恒久対応: {{D:post-oracle-regen-ban-narrow-protection}} が保護範囲を
  「実効 build 根とその配下だけ、親には触れない」と定め、
  `orchestrator/tests/test_sort_swo_dependency_material.py::test_post_oracle_protection_leaves_binding_base_writable_for_new_entry`
  が保護中の `<base>` 直下への新規 entry 作成を実 filesystem で検査する。
- 再発検知: 上記 test を狙う変異 M4 (保護を親まで広げる) を変異 matrix へ登録済み。
  同 test だけが赤になることを実測した。

### {{F:self-inflicted-shared-state-poison}}. 新しく足した保護機構が、二重に入ったときに共有材料を恒久的に読取専用にする形になっていた [自作機構の破れ] [並行]

- 事象: 段 5 の実装は同じ根に対して 2 つ目の保護 context が入れる形だった。後から入った側は
  1 つ目が既に落とした mode を「元の mode」として採取するため、非 LIFO で退出すると
  **根が恒久的に読取専用のまま残る**。さらに 1 つ目が先に退出して write bit を戻すと、
  2 つ目の build 中に保護が消え、その窓の再生成を禁止できない。
- 根本原因: 「mode を採取して戻す」形の保護は、保護前の状態が素の状態であることを暗黙の前提に
  している。その前提を検査していなかった。親は段 4 で交差を「限界として明記する」と裁定したが、
  一時的な gap だけを見て**最終状態の破壊**を見落としていた。段 6 の敵対レビューが
  実装の行から決定的に導いた。
- 恒久対応: {{D:post-oracle-regen-ban-narrow-protection}} が「保護に入る時点で根 directory 自身が
  書込み可能であること」を前提条件として要求し、満たさなければ write bit を 1 つも触らずに
  拒否する (`post-oracle-protected-root-not-writable`)。後から入った側が必ず拒否されるため
  交差自体が起こらない。process 間 lock は作らない (D953 が別審査と裁定済み)。
- 再発検知: `orchestrator/tests/test_sort_swo_dependency_material.py::test_post_oracle_protection_rejects_overlapping_context_without_mode_change`
  が、2 つ目の context が mode を 1 つも変えずに拒否されること、および 1 つ目の退出後に
  exact 復元されることを検査する。この node を狙う変異 M5 (前提条件の恒真化) を
  変異 matrix へ登録し、KILLED を実測した。

### {{F:mutation-preempted-by-inner-guard}}. 事前登録した変異が、同じ機構の内側の検査に先取りされて狙った経路へ到達しなかった [変異の帰属] [恒真]

- 事象: 段 4 で「書込み不能化の呼出しを no-op にする」変異 (M2) を、
  「保護中に同一 bytes を再書込みできてしまう」ことを示す単一理由の変異として事前登録した。
  段 6 の敵対レビューが、その変異では**同じ関数の内側**にある
  `post-oracle-write-bits-remain` 検査が `yield` の前に拒否するため、
  狙った再書込みの成否まで到達しないと実測で示した。
- 根本原因: 変異の位置を「機構の入口」で選び、その機構が自分の内側に持つ事後検査を
  勘定に入れなかった。DW-M01 が要求する「同じ入力を拒否する層が前後にも**内側**にも無い」の
  内側を見落とした形である。
- 恒久対応: 変異を「保護後検査を通過した直後、`yield` の直前に復元を挿入する」形へ再照準した。
  build 窓だけが書込み可能になり、内側の検査はすべて通り、狙った test だけが赤になる。
  再照准後の M2 は KILLED、期待 node 完全一致で実測済み
  (`output/insights/2026-09-08_t1799-post-oracle-regen-ban/mutation-matrix.json`)。
- 再発検知: 変異 probe を全件 SURVIVED で先に走らせ、観測 node を集めてから本走の期待 node を
  確定する手順 (DW-M07) を踏むこと。今回は probe が M2 の実際の赤 node を露出させた。
