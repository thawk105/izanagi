---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t1815-cli-entrypoint
seq: 1
---

## {{D:cli-transport-repair-is-not-decider-semantics}}. 壊れた CLI transport の復旧は判定器の受理意味変更ではない

**決定:** 判定器・評価器・射影の module を `__main__` として起動したときだけ実行される
bootstrap を直す変更は、8c 事前登録の凍結規範がいう「受理集合・拒否理由・射影された判定入力の
意味を変える変更」に当たらない。`DECIDER_VERSION` を bump せず、次世代の条件契約 record も
発行しない。

**理由:**

- 規範は「判定は判定器 module が commit `C` 時点の git blob だけから再計算する」と定義する。
  その再計算を行う権威 API (`activation_report_at` / `effective_at`) の出力は、任意の commit に
  ついて修正前後で同一である。変わるのは `__main__` 起動時の module identity だけで、
  判定器として import されたときには一度も実行されない。
- 規範は bump に「同じ commit で次世代 record を発行する」ことを課すが、
  `_assert_history_transition` は `protected_sha256` が親と同じまま generation を進める record を
  `spurious-revision` で機械拒否する。凍結範囲 (§1〜§4・§6・§7 の規範本文、§5 の欄名集合、
  発効ブロック、証拠契約の意味内容) を変えない wave では、版だけの新世代は**発行できない**。
  bump を選ぶことは、scope 外の保護対象文書の改訂を強制することと同義になる。
- 受理集合 (`effective=true` になる commit 集合) と、判定器が返しうる reason code の集合は
  どちらも不変である。壊れていたのは transport であって、規範がいう意味論ではない。

**却下した選択肢:**

- 版を bump して新世代 record を発行する — 上記のとおり `spurious-revision` で拒否されるため、
  発行するには保護対象文書を編集する必要が生じる。CLI の起動経路を直すために発効判定の入力を
  動かすことになり、順序が逆である。
- `_normalize_predicate_results` の型検査を緩めて二重実体化に耐えさせる — 規律 2 に反する。
  診断を良くするために正しさ検査を弱める方向は採らない。

## {{D:real-process-cli-check-uses-synthetic-repo}}. 実プロセス CLI 検査は合成 repo で行い、実 repo の全評価を新設しない

**決定:** CLI を実プロセスとして起動する回帰検査は、判定器・評価器・射影の 3 module と証拠契約の
**live bytes を copy した合成 repo** を対象に行う。実 repository HEAD に対する全評価の subprocess を
新たに足さない。

**理由:**

- 実 repository HEAD の全評価は、並行 wave で混雑した login node で 39〜119 秒を要する
  (親の 3 連走実測、load average 76)。起動形ごとに oracle と subprocess の 2 評価を払う設計は
  最悪 8 評価になり、suite 全体の時間上限を単独で超える。
- 合成 repo は同じ production 入口・同じ module identity の境界・同じ結果正規化層を通る。
  三 module の blob 一致検査を通過するので評価器まで到達し、証拠契約を置けば 12 条件が
  8 種類の reason へ分かれる非一律な oracle になる。**1 走 0.2〜0.3 秒**である。
- 一律な期待値 (12 件すべて同じ reason) は、壊れた側の一律 `evaluator-exception` と形が同じで
  oracle として弱い。証拠契約を置いて非一律にする。

**却下した選択肢:**

- 実 repo HEAD に対する 4 起動形の全評価 — 上記の時間予算に反する。
- `sitecustomize` と `atexit` で module identity を実プロセス観測する — production 入口の
  答えを直接比べる方が安く強く、観測用の仕掛けを足さずに済む。
- 期待値を literal で焼き込む — 評価器が別の理由で変わったときに偽赤になる。
  同じ commit の library 判定を oracle にする。

**この検査が pin するもの:** CLI と library の transport 等価性だけである。判定の意味の
正しさは既存の predicate / invariant テストが持つ。
