---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-flaky-quarantine
seq: 1
---

## {{D:flaky-quarantine-node-id-registry}}. 環境フレークは node ID 単位で隔離し、再導入タスクを fail-closed で必須にする

**決定:**

1. 同一 tree で緑にも赤にもなるテストを隔離する機構を
   `orchestrator/tests/flaky_test_holds.py` に新設する。**scope は node ID 完全一致のみ**とし、
   file 単位・ディレクトリ単位・パターン一致で巻き込まない。
2. 登録の受理条件は次の 6 つで、1 つでも欠ければ `ValueError` で import / collection を落とす。
   黙って entry を無効化しない。
   - 同一 tree で緑と赤の両方が観測されている (少なくとも一方は受入全走と同じ collection 条件)
   - 赤の理由文字列 (failure signature) を持つ
   - 原因が特定されている
   - canonical な証拠を `docs/failures.md` の F 番号で指せる
   - 再導入タスクの slug を持つ
   - `known_failure_node_ids` が entry の key と一致する
3. 証拠は自己申告にしない。**当該 F 節の本文に、entry の test 関数名と failure signature が
   実在すること**まで validator が照合する。
4. 隔離は走行末尾の `IZANAGI_FLAKY_HOLD_SUMMARY_V1` に必ず出す。
5. **opt-in 環境変数を作らない。** 隔離された node を走らせたいときは registry から entry を消す
   (= 再導入する)。
6. 完全 collection で登録 node が現れなければ `pytest.UsageError` で止める (stale registry 検出)。
7. 変異 harness には、変異の期待失敗 node が隔離集合と交差したとき分類せず停止する
   fail-closed guard を置く。
8. 両親が同じ実装面ファイルを変更した main 取り込みでは、Codex `role=author` の合成監査を行う。

**理由:**

- 隔離は本質的に検査を走らせなくする操作であり、扱いを誤ると正しさの防壁を静かに無効化する。
  絶対規律 2 は「正しさゲートを緩める変異を許さない」と定め、最適化圧力は必ず正しさを
  攻撃しに来るという前提で設計せよと求めている。受入が赤で land できないという圧力は、
  まさにその最適化圧力である。
- 敵対レビューは「既存の F 番号を再利用し node ID だけ正しくして残りを任意の文字列にした entry が
  登録できる」ことを指摘した。これは実測されていない node を受入集合から外せる経路であり、
  赤の圧力下での最短の悪用経路でもある。証拠を台帳本文へ束縛することでこれを塞ぐ。
- node ID 単位に限る根拠は 2 つある。(a) file 粒度の見積りでは
  `matched_node_count=130` に対し `collateral_node_count=120` となり、純粋な unit 検査と
  受理検査まで受入集合から消える。(b) 親が「実 launcher subprocess を起動する node」だけへ
  scope を狭める静的判別子を作ろうとしたが、最良の判別子でも既知の赤 13 件のうち 1 件を
  取りこぼした。**取りこぼす述語に fail-closed な機構を載せることはできない。**
- opt-in 環境変数を作らないのは、受入走行へ継承されるにもかかわらず acceptance receipt の
  env projection に無く、**隔離が効いた走行と効いていない走行を受領証から区別できなくなる**ため。
  land 側で拒否するか projection へ足す必要があるが、どちらも `tools/dev_wave_land.py` の
  重く pin された受理条件に触る。
- 合成監査を義務づける根拠は実測である。両 wave が独立に `orchestrator/tests/conftest.py` を
  変更し、自動 merge は競合なしで通ったが、合成は壊れていた
  ({{F:merge-narrowing-misread}})。

**却下した選択肢:**

- file / family 粒度の隔離 — 巻き添えが重く、`test_codex_worker_launch.py` については
  そもそも環境前提が成立している (launcher は正常起動し子側の指標も全て正常) ため
  file 単位で外す論拠が立たない。D679 の粒度緩和は「ファイルの環境前提が成立していない」
  場合に閉じた話であり、白紙委任ではない。
- 既存 growth hold registry への相乗り — 解除条件が異なる。growth は恒久で
  ユーザー明示命令のみ、flaky は一時で再導入タスクにより解除される。
  相乗りすると解除の意味論が混ざり、inventory の layer-level 単数 field でも表現できない。
- 証拠を `docs/` 配下の JSON に置く — `tools/check_docs.py` の再帰列挙対象になく、
  schema も byte 予算も孤児検査も効かない。置いても検査されない。
- 非帰属判定器 (`tools/check_acceptance_reds.py`) に依存する設計 — D678 により
  受入経路で使わないと決まっており、依存すると機構ごと無効化される。

## {{D:repair-over-quarantine-for-fixture-budgets}}. テストの予算値が production の gate でないなら、隔離ではなく修理する

**決定:**

高負荷で非決定的に落ちるテストであっても、**落ちる原因がテスト側の fixture 値であり、
それが production の正しさゲートではない場合は、隔離せず修理する。**
修理は「検査対象でない limit が先に発火しない値へ変える」形で行い、
検査対象の limit の検出力を 1 つも失わないことを条件とする。

**理由:**

- `orchestrator/tests/test_codex_worker_launch.py` の helper `_base_command` が渡していた
  `max_wall = "3"` は、テストを速くするための fixture 値であり、production の既定 3600 秒とは
  別物だった。144 test のうち 22 件がこの小さい wall を渡しながら**別の limit** を検査しており、
  高負荷では wall が先に発火して assertion が壊れていた。**壊れていたのはテストの書き方であって
  被験体ではない。**
- 隔離は情報を失う側の操作である。同じ結果 (受入が緑になる) を、検出力を失わずに得られるなら
  そちらが上位である。本件では file 単位で隔離すると launcher の受理集合検査
  (起動前検証、rc 期待値、evidence / metering の完全性、process group の残留、終了検証) を
  丸ごと失うが、修理では 1 つも失わない。
- ハングの安全網は別層にある (`_run_launcher_subprocess` の `timeout=10`)。
  予算を上げても暴走の検出は失われない。
- 同型の判断が `orchestrator/tests/test_growth_test_holds_contract.py` にも当たった。
  親環境の `FORCE_COLOR` が pytest 要約行を着色し照合が外れる既知失敗 (F373) は、
  台帳の恒久対応が「起動 script で `env -u FORCE_COLOR -u COLORTERM` を前置する」という
  運用規律だったため 3 度目の再発を招いた。**運用の前置きに頼る限り、忘れた者が次を踏む。**
  テスト側が自分の subprocess の着色を明示的に切れば ambient env に関係なく決定的になる。

**却下した選択肢:**

- 予算を一律に大きくする — 本当に暴走した被験体を捕まえられなくなり、絶対規律 2 の逆方向へ動く。
  変更するのは「検査対象が wall でない node」に限り、wall 自体を検査する node は触らない。
- 隔離してから後続 wave で修理する — 修理が小さいと判明している以上、
  その間ずっと受理集合を欠いたまま走ることになる。
- 運用規律の追記で対応する — F373 が 3 度の再発でその不十分さを実証している。
