---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1546-verifier-fixture-independence
seq: 3
---

## 新規

### {{F:parent-overconstrained-uniqueness-reddened-meta-test}}. 親の fix 指示が「一意」を過剰に定義し、任意入力の分岐で正当に増える呼び出しを勘定に入れず既存メタテストを赤にした [誤前提] [手順漏れ]

- 事象: 段 6 の fix 指示で AST メタテストの契約を 1 node から 3 node へ一般化させる際、
  「検証呼び出しが node 内で一意」と書いた。fix 子はそのとおり実装したが、
  `test_real_silo_serializable` は任意入力 `output/runs/silo-sample` が置かれた機体のために
  `if os.path.isdir(...)` の中で**正当に 2 回目**の検証を呼ぶ。既存メタテストが
  `node 内の検証呼び出し全体が一意でない` で赤になった。fix 子は `qstat -Q` の preflight 失敗
  (rc=16) で子を起動できず未実走のまま報告しており、**親が素の Python で test 関数を直接呼ぶ
  焦点実走を行って初めて赤が出た** (login node では pytest が guard に拒否される)。
- 根本原因: 塞ぐべき穴は「node 直下の無条件 assignment が別 fixture で 2 個目を持てる」ことで
  あって node 全体の呼び出し回数ではなかった。親が穴の形を確かめずに一段強い述語を書いた。
- 恒久対応: 過剰な述語だけを外し `node 直下の検証 assignment 全体が一意` を残した
  (`orchestrator/tests/test_skip_classification.py` の
  `test_real_silo_node_always_verifies_tracked_fixture_without_skip`)。
  `DW-S06-B` の「受理・拒否の含意の向きを 2 文へ分け、通る正例を添える」を、production の
  受理集合だけでなく AST 契約のようなメタテストにも適用する。
- 再発検知: 外したあとも穴が塞がったままであることを、細工した写しに対して契約を実行して実測した
  (別 fixture への 2 個目の直下 assignment / 結果束縛の再束縛 とも拒否)。同契約は
  結果束縛名の一意性と後続 golden からの参照も固定するので、同型の緩和は同 node が拒否する。

### {{F:frozen-pre-registration-diverged-from-own-spec}}. 親が凍結した変異事前登録と、親自身が書いた spec が別物になっていた [手順漏れ] [変異]

- 事象: 段 4 の裁定で「`report.py` の `_reason_to_dict` から `key` を落とす」変異を事前登録した
  のに、そのあと親が書いた `mutation-spec.json` では「r8 規模で外部 `anomalies` を空にする」
  別の変異になっていた。段 6 のレビューが指摘するまで親は気づいていなかった。
- 根本原因: 裁定文と spec を別作業として続けて書き、凍結物との照合を挟まなかった。
  `DW-O12` は「受理集合を変える指示を子へ出す直前に、この wave で凍結済みの事前登録・判定式を
  再読する。凍結は自分が直前に書いたものでも拘束する」と定めており、その再読を怠った。
- 恒久対応: **差し替えずに両方登録した。** 裁定どおりの変異を復活させ、spec 側の版を別 ID で
  追加登録し、経緯を段 4 裁定文へ日付つきで追補した。凍結した事前登録を後から書き換えて辻褄を
  合わせない。差分が見つかったら追加登録し、裁定文に追補する。
- 再発検知: 変異 harness は `KILLED` 期待の失敗 node 集合が登録値と完全一致することを要求する
  (`tools/mutation_harness.py`、`DW-M08`)。登録と実体がずれた変異は `MISMATCH` として
  ledger に残るため、両走行の `MISMATCH: 0` が照合済みの証拠になる。
