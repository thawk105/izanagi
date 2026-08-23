---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: dev-wave-t1484-floor-restart-registry
seq: 4
---

## {{D:attempt-registry-core-profile-policy}}. attempt 状態機械の共通 core は遷移 policy を profile 注入とし、8c は今日の挙動を保つ

**決定:**

1. D672 の共通 core は `orchestrator/campaign/attempt_registry_core.py` に置き、
   slot codec・binding codec・schema/event 表・path layout・retryable 理由集合・
   budget key・遷移 policy を `DomainProfile` で注入する。
   8c は `orchestrator/campaign/trial_registry.py` の**実 `def` による委譲 facade**、
   8b は `orchestrator/campaign/s8b_attempt_profile.py` の profile とする。
2. **facade を再 export で書いてはならない。** `s8c_preregistration_evidence.py` の
   条件 C03 は `ast.FunctionDef` の実在を要求するため、再 export では拒否理由が変わる。
   同じ理由で facade 6 関数の top-level 再束縛も禁じる。
3. **正しさ検査の強弱は profile の項目にする。** 具体的には
   `require_terminal_reason_equals_classification` を置き、**8c は今日の挙動である `False`、
   8b は `True`** とする。8c 側を締めると受理集合が狭まり D672 の実装条件に反するためである。
4. **core は semantic handler を持たない event を fail-closed で拒否する。**
   profile の event 表に名前があるだけの event に terminal の semantic を与えない。
5. **8b の再走理由集合は空のままとし、中身は決めない。** 受理集合を変える判断であり、
   `docs/phase3-8b-descriptor-design.md` §10.5 の「exact な列挙を事前登録の凍結範囲へ書く」
   要件と、証拠源 (scheduler accounting) の設計が未確定だからである。
6. **8b の production 配線は行わない。** 本決定の時点では 8b の実行系から新 core を
   import も call もしない。途中状態を production から到達不能に保つ。

**理由:**

- 8c の受理集合の実体は path pin ではなく `s8c_preregistration_evidence.py` の
  **AST ベースの述語 probe** である。関数の実在・関数内の呼出し関係・live node の属性名と
  文字列定数・到達性・top-level 名を要求するため、素直な再 export や本体の移動で拒否理由が動く。
  この事実は `grep -rn "<成果物パス>"` では見つからない型の pin であり、
  実装形状を決める前に確かめる必要があった。
- 8c の attempt registry には、分類受領証を封印した後に値を見て terminal の失敗理由を
  付け替え、次の slot を取る経路が今日開いている ({{F:terminal-reason-override-after-value}})。
  8b がこれを継承すると絶対規律 2 に抵触する。一方 8c 側を締めると D672 の
  「受理集合を変えない」に反する。**両立させる唯一の形が policy の profile 化**である。
- 段 4 で親は「未知 event は拒否されるので profile の event 表へ足すだけで安全に拡張できる」
  と論じたが、段 6 の敵対レビュー 2 本が独立に反証した。core の replay が
  「既知 4 種以外はすべて terminal」という `else` 分岐だったため、表に名前を足すだけで
  terminal の semantic が付いた。**拡張点を用意すること自体が穴になっていた**ため、
  fail-closed へ直した。

**却下した選択肢:**

- **8c 側の理由一致検査も締める** — 絶対規律 2 の面では正しいが、8c の受理集合が狭まり
  D672 の実装条件に反する。締める時期は凍結世代・事前登録との関係を含めて別途裁定する。
- **facade を再 export にする** — 記述量は減るが C03 の拒否理由が変わる。
- **recovery (引き取り) event を本 wave で実装する** — 受理集合を変える判断であり、
  §10.5 にも規定が無い。誰が stale を宣言できるかの fencing 設計も要る。
- **8b の再走理由集合を実装子判断で決める** — 受理集合を変えるため許されない。
- **8b を production へ配線してから裁定を待つ** — 途中状態が production から到達可能になる。
