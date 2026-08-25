---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1135-prereg-blockers
seq: 1
---

## {{D:c03-fix-belongs-to-approval-activation}}. C03 述語の名前一覧訂正は単独で実施せず、承認権限 activation の改訂単位へ同梱する

**決定:** 8c 条件3 (C03) の producer 到達性検査が要求する関数名一覧は、`registered-effective` 時代の
generic 名 (`reserve_attempt_slot` / `record_attempt_terminal`) のままであり、D618 が確定させた
formal 経路 (`reserve_formal_attempt_slot` / `record_formal_attempt_terminal`) を受理しない。
この不一致は real である。**しかし本 wave では実装しない。** 訂正は、承認権限を開ける
改訂単位 (証拠契約の反転・評価器 registry 登録・`DECIDER_VERSION` bump・新しい条件凍結 record の
発行) と同じ commit へ同梱する。

**理由:**
- **訂正しても閂が 1 本も外れない。** 起動可否を決める conjunction は
  `all(item.status is PredicateStatus.SATISFIED for item in predicates)` の 1 本だけであり、
  `UNSATISFIED` も `EVIDENCE_UNDEFINED` も等しく非受理である。C03 の訂正で変わるのは
  gate レポートの status 欄と status count、および activation report digest だけで、
  起動可否・certified 選択・材料レポートの数値はいずれも不変である。
- **代償が非対称に重い。** D529 は「判定器・評価器・射影で拒否理由の意味を変える変更」に対し、
  bytes 差の有無に関わらず版 bump と新世代 record を要求する。C03 の拒否理由は
  「構造的不成立」から「証明未定義」へ変わるので、この要求に真正面から当たる。
  診断ラベルの付け替えのために版と世代を 1 つずつ消費することになる。
- **やり直しが利かない。** 同じ D529 が「凍結の妥当性検査は tip でなく履歴グラフ全体を走る。
  契約を変えた commit を祖先に残すと、後から正しい世代を足しても拒否され続ける。分割は後から
  接合できない」と定める。単独で撃つ価値のない改訂に、後戻り不能の履歴を使わない。
- **同梱すれば世代を二度消費しない。** 承認権限を開ける改訂単位は、どのみち版 bump と
  世代発行を伴う。C03 の訂正をそこへ入れれば、追加の世代を要さず、履歴汚染のリスクも取らない。
- 段3 の敵対相談 2 レンズが独立に、単独実施を NO-GO と判定した。

**却下した選択肢:**
- 述語の名前一覧だけを本 wave で選言へ広げる — 上記のとおり閂は外れず、版と世代を消費する。
  さらにレンズ A が指摘したとおり、`_declared_call` は名前の到達可能性しか見ないため、
  formal 名を受理するだけでは「formal wrapper が厳格 profile へ委譲している」ことを
  何も証明しない。厳格性の証明を伴わない受理形の追加は受理集合の実質的な緩みであり、
  絶対規律 2 に抵触する。
- producer 側を generic 名へ戻す — D618 が確定させた formal 経路を捨てることになる。
  formal profile は generic に `require_terminal_reason_equals_classification=True` を
  1 つ足した真に厳しい側であり、戻すことは正しさ防壁の後退である。

## {{D:formal-noncertifying-launch-does-not-consult-predicates}}. 8c 正式系列の閂は経路によって別物であり、非 certifying 経路は 12 述語を一切見ない

**決定:** 「8c 正式系列の残 blocker」を 1 つの集合として扱わない。certifying 経路と
非 certifying 経路では閂が構造的に別物であり、台帳では分けて記す。

- **certifying 経路の閂は承認権限ただ 1 つである。** 受理判定は 12 述語すべてが
  `SATISFIED` であることを要求するが、`SATISFIABLE_CONDITION_IDS` は空集合であり、
  さらに評価器が `SATISFIED` を返しても registry がそれを `ERROR` へ書き換える。
  したがって個々の述語をどれだけ直しても、この経路は開かない。
- **非 certifying 経路は 12 述語を参照しない。** `admit_registered_formal_noncertifying` が
  要求するのは明示 opt-in、trial manifest の読み込み、`validate_condition_freeze_at`、
  launch binding の 4 点だけである。C03 / C05 / C08 はこの経路の閂ではない。
- **どちらの経路も、事前登録 artifact が 3 つとも不在であることに阻まれている。**
  `trial-manifest.v1.json`、`prereg-effective-binding.v1.json`、`schedule.v1.json` の
  いずれも repository に存在しない。

**理由:**
- 実測で、正式系列を止めているものが述語のコード欠陥ではなく、承認権限と artifact の不在で
  あることが確定した。述語を blocker 集合として並べる書き方は、直せば進むという誤った期待を
  生む。実際には C03 を直しても起動可否は 1 ビットも動かない。
- 経路を混ぜたまま「残 blocker」と数えると、非 certifying 経路にとって閂でないものを
  閂として数え、逆に真の閂 (manifest の不在) を見落とす。

**却下した選択肢:**
- 3 artifact を本 wave で生成して commit する — D549 が、暫定 authority で
  `schedule.v1.json` を正式 artifact として commit することを明示的に却下している。
  同じ理由が他の 2 artifact にも当てはまる。権威の実体供給が済むまでは、生成した bytes が
  後から再現不能になる。
