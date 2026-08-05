# 段 6 fix 指示 — [T-490] U-1/U-2

段 6 の敵対レビュー 2 本 (rev_a.md / rev_b.md) と親の実測を裁定した結果、
**直すのは次の 2 件だけ**である。それ以外は変更しないこと。

production コード (`orchestrator/campaign/` の 3 ファイル) は**両レビューとも real 所見なし**で、
裁定どおりと確認された。**production コードを変更してはならない。**
直すのはこの wave で追加したテストだけである。

---

## FIX-1 — `_require_g13()` は fail ではなく skip にする (親の実測)

- **場所**: `orchestrator/tests/test_s1_direct_comparison.py` の `_require_g13()`
  (現在 `pytest.fail(...)` を呼んでいる)。
- **事実**: 親が実測したところ、この node が原因で対象スイートが
  **199 passed / 1 failed** になった。計算ノードには g++ 11.4 しか無く `g++-13` が存在しない。
- **リポジトリの契約**: `orchestrator/tests/README.md` の「C++ toolchain が無い環境では
  skip として数える」契約であり、先例は `orchestrator/tests/test_campaign.py:4711` の
  `_require_g13()` (`skip(...)` を呼ぶ)。
- **対処**: 先例と同じく **skip** にする。理由文言は残してよい。
- **なぜ検出力が落ちないか**: MF2(a) (実 `quarantine` の `edited_text` / `working_diff` が
  7 種すべてで byte-exact に同一) が identity の構造証明を担う。MF2(b) は toolchain のある
  環境での end-to-end 確認であり、そこでは従来どおり実走する。
- **成果物影響**: 直さないと main が全ノードで赤くなり、以後の wave が
  「既存の赤」と自分の回帰を区別できなくなる。

---

## FIX-2 — MF3a が禁止変異 M6 を殺せない (rev_a 所見 1 / rev_b 最重要所見、両者一致)

- **場所**: `orchestrator/tests/test_s1_direct_comparison.py` の
  producer 独立性テスト (`s1_measurement_freeze.CONFIGURATIONS` を monkeypatch している node)。
- **事実**: テストモジュールは冒頭で `s1_direct_comparison` を import 済みであり、
  allowlist は module import 時に評価される。したがって禁止変異
  `_PREPARE_CELL_CONFIGURATIONS = frozenset(s1_measurement_freeze.CONFIGURATIONS)` を入れても、
  import 時点の 6 値を snapshot したままになり、後から producer を 7 値へ monkeypatch しても
  テストは緑のままである。**事前登録した変異 M6 が生存する。**
- **対処**: producer を 7 値へ monkeypatch した**後で**、`s1_direct_comparison` を
  **別 module 名で隔離 import** し、その fresh module の
  `_PREPARE_CELL_CONFIGURATIONS` と `prepare_cell` が 7 個目を**拒否し続ける**ことを検査する。
  - 隔離 import の先例は同じ wave で追加した
    `orchestrator/tests/test_trigger_gate_binding.py` の
    `test_duplicate_stripped_predicate_fails_during_module_import`
    (`importlib.util.spec_from_file_location` → `module_from_spec` → `exec_module`、
    `finally` で `sys.modules` から除去) である。同じ形を使うこと。
  - fresh import した module に対して `prepare_cell` を呼ぶときは、
    checkout や resolver へ到達する前に拒否されることを確認する
    (既存の未知構成テストと同じく checkout sentinel より手前で `DriverError` になること)。
- **既存の固定 6 値等価テストは残してよい** (drift の可視化として有用)。ただしそれは
  独立性の証明にはならないので、新しい隔離 import テストを別 node として追加すること。
- **成果物影響**: 直さないと、将来 producer に 7 個目の configuration が追加されたとき、
  materializer がそれを自動認可し、4 分岐を抜けて flags-only の `src_token` / `variant_id` を作り、
  certified 選択の候補・材料レポートの configuration/binding 参照・試行台帳の受理行に
  未承認 configuration が載る。

---

## 直さないもの (nit として記録済み。触らないこと)

- `pipeline.variant_id` の比較アサートが直前の token 等価から自動的に成立する点 (rev_b の恒真性 nit)。
  **成果物影響なしと裁定した。** 削除も変更もしないこと。
- `impl.md` 内のリンク行番号のずれ。報告文書であってコードではない。
- SP1 / SP2 / SP3 (ruling.md の scope 外項目)。実装しないのが正しい。

---

## 完了報告に必ず含めること

- FIX-1 / FIX-2 それぞれの **closed / partial / regressed**。
- production コード (`orchestrator/campaign/`) を変更していないことの明示。
- 追加・変更したテストの node id。
