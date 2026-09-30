# 段 6 裁定 1 — review-a / review-b の所見 (対象 8f112994d)

| # | 所見 | 裁定 | 対応 |
|---|---|---|---|
| RA1 | `-DSILO_ORDER_VARIANT=foo` 等の未定義識別子が #if で 0 と評価され #error を通る | real (現象) / must-fix としては refuted → nit | 放置時の成果物影響の主張「候補のつもりで stock を測り台帳が食い違う」は成り立たない: Phase 3 の identity は前処理後 bytes の hash (D23、source_digest.resolve) で決まり、`foo` の build は STOCK の identity で記録される。genome の値は driver のコードが整数で与える。関数方策の patch (SILO_POLICY_VARIANT) も同じ形。一次資料の限界に 1 行で記し、fix しない。 |
| RB1 | template test が repo 外 (job dir) の api-header-canonical.hh を読む | real, must-fix | repo 内 `orchestrator/campaign/silo_lock_order_api.hh` (axis.API_HEADER) を比較元にする。 |
| RB2 | gate と実骨格 patch を通しで結ぶ test が無い。template test は名前つき対照を手で再記述し gate を通さない | real, must-fix | 既存の module fixture の checkout (pinned clone + 実 patch) で、実物の `silo_lock_order_hand/version_desc.cpp` を `order_gate` に渡し、(a) 合格して hole がその本体になる、(b) 文法で拒否される候補 (例: 状態 field に禁止名) では transaction.cc が 1 byte も変わらない、を検査する test を足す。手書き複製の対照本文 (template test 134〜142 行付近) は削り、実物の file を読む。 |
| RB3 | template test の pin 直書き・件数の並走衝突 | real, should-fix (pin 部分) / 件数は親の統合時の検査 | test の pin は `axis_silo_lock_order.PIN` を使う。件数は main 取り込み時に親が両側の literal と実数を照合する (追補裁定 1 の注意)。 |
| RB4 | compile・template test の重複 | nit | RB2 の手書き複製の削除だけ行い、共通化はしない。 |

fix の単位: 横断所見 (test_silo_lock_order_template.py と test_silo_lock_order_gate.py、A・B 両方の成果物を要する) なので 1 つの Codex fix 単位に寄せる。統合 commit 8f112994d から作った作業木 lock-order-f で行う。production file は変えない (test だけ)。

既存テストの期待値を変更しない。新しい test の期待は「受理 (gate 合格で hole が対照本体になる)」と「拒否 (文法拒否で source 不変)」の 2 文で書く。通る正例: version_desc.cpp が実 patch の hole に order_gate 経由で書かれる。

## 訂正 (焦点再レビュー focus-1 の指摘を受けて、2026-09-30 追記)

RA1 の降格理由のうち「`foo` の build は STOCK の identity で記録される」は誤り。Phase 3 の identity を決める前処理 (`orchestrator/campaign/source_digest.py` の `_cpp_normalize`) は `-Werror=undef` 付きで走るので、`#if` が未定義の識別子 `foo` を評価した時点で前処理が失敗し、identity を確定せず fail-closed で止まる (同 file の preprocess 失敗時の RuntimeError)。結論 (must-fix としては refuted、nit) は変えない: 誤った値の build は台帳に候補として記録される前に止まる。一次資料にはこの訂正後の理由を書く。

変異の再照準: M5 (gate が文法検査より前に write) の検出 test に、RB2 の実 patch 上の拒否 test も加わる (M5 の期待 node に追加登録する。単一理由性は fix 後に親が確かめる)。
