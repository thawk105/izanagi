---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-15
wave: dev-wave-t2607-t316-gate-tree
seq: 2
---

## {{D:t316-gate-tree-alignment}}. t316 は patch を当てた使い捨て木を条件関門と両 build で共有し、CCBench が参照しない変数を共有 configure から外す

**決定:** t316 probe の S6 を次の形にする。

1. `patchharness.checkout` で pin から使い捨て木を作り、**patch を当てる前に**その木へ
   `_git_source_identity` を掛けて結果を受領証の識別子として残す。patch 適用後の木を clean と
   記録しない。
2. `patchharness.applied` の内側で outside と inside の両 build を行う。条件関門と両 build は
   同じその木を使い、control には素の submodule を直接渡す。
3. 共有 configure list から、patch 適用後の CCBench が参照しない 3 変数
   (`RULE_LAUNCH_COMPILE`、`IZANAGI_GFLAGS_SRC_HEAD`、`IZANAGI_GLOG_SRC_HEAD`) を除く。
   関門へ渡す引数からだけ除くのではなく、共有 list そのものから除く。
4. 使い捨て木の置き場は、`TMPDIR` が未設定か `/tmp` 配下のとき scratch の兄弟へ移す。
5. `condition_meaning_gate.py`、受領証の schema、`verdict_s6` の拒否枝、inert exact pair の表は
   変更しない。

**理由:**

- **検査する木と build する木を一致させることが、この族の修正の不変条件である** (A-2 の
  2026-09-02 の教訓)。関門にだけ patch 木を渡す形はこの不変条件を破るので D1994 が却下している。
- 関門は素の木で fail-closed に正しく拒否していた。直すべきは関門ではなく、供給しない条件を
  要求していた driver の側である。
- **未参照 3 変数の除去を同時に行わないと閉じない。** D1994 は赤の原因を 2 つ挙げ、どちらも
  単独で赤にすると書いている。patch を当てても、CCBench が参照しない変数は両アームで未使用変数
  警告を出し、rc=0 でも stderr 非空を `configure-failed` にする規則に当たる。F855 の恒久対応
  「driver から未使用変数を除去」が t316 へ未適用だった。
- 共有 configure の `-D` を引き直したところ、参照されないのはこの 3 件だけだった。
  `CMAKE_C_COMPILER` 族は、CCBench 本体が `LANGUAGES CXX` でも FetchContent で入る mimalloc が
  `project(libmimalloc C CXX)` なので使われる。
- **置き場の修正は本番で発火する欠陥への対応である。** sandbox は `/tmp` を空 directory の
  read-only bind で置き換えるが、`patchharness.checkout` は `TMPDIR` (既定 `/tmp`) の下に木を作る。
  probe の PBS は `TMPDIR` を export せず、修正前の受領証の scratch は `/scr` 直下だった。
  つまり本番で `TMPDIR` は未設定であり、inside build から requested 木が見えない。
- **「関門ごと落とす」形は採れない。** D1625 (ユーザー裁定) が却下欄で「probe の exact 一致検査を
  外す — 受理集合を gate の表より広げる」を明示的に却下している。加えて `verdict_s6` の拒否枝
  4 本は inert 要求の有無と独立した現行契約であり、define を消しても外さなければ go にならない。
- この択一は実測では決まらない。案の不成立は契約上の帰結であって経験的事実ではないので、
  実測は択一の決定ではなく採用案の到達確認に使った。

**却下した選択肢:**

- **未参照変数 3 件だけを除去する** — `CCBENCH_BACKOFF_FIXED` が残るので赤は解けない (D1994)。
- **関門にだけ patch 木を渡す** — 検査する木と build する木が別物になる (D1994)。
- **関門の stderr 非空判定を緩める** — 共有の正しさ防壁の受理集合を広げる。絶対規律 2 に反する (D1994)。
- **条件要求ごと落として関門を呼ばない** — D1625 の却下欄そのものに当たる。
- **`buildcache.prepare_masstree_fetchcontent` を t316 へ導入する** — 関門の緑が永続 cache の残留
  生成物に依存する点は実在するが、cache を掃除したときに初めて発火する。本 wave の本題ではないので
  別項へ送り、限界として insight へ明記する。
- **使い捨て木の置き場を決める helper へ並行呼び出し対策を入れる** — 本番の呼び手は直列 1 箇所で、
  発火する経路を名指しできない。仮想リスク向けの機構を足さず、限界として insight へ明記する。
