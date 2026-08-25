---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-26
wave: dev-wave-t1697-closed-critic
seq: 1
---

## {{D:b4-closed-critic-no-new-role-file}}. 閉じた critic 起動は新規 role file を作らず、未改変 role を projected provider へ渡す形で足す

**決定 (D904 の実装形):** B-4 用の閉じた critic 起動は、`.claude/agents/` へ新しい role file を
足さず、**未改変の `critic.md` を `ClaudeProjectedRoleProvider` へ渡す route-local な module**
として実装する。実体は `orchestrator/campaign/p3_b4_closed_critic.py`。

**理由:**
- 新規 role file は `orchestrator/codex_roles/review_ledger.py` の `EXPECTED_ROLE_COUNT` と
  role 名を key にする pin 群 (`SOURCE_FILE_SHA256` / `ROLE_MANIFEST_SHA256` /
  `DESCRIPTION_SHA256` / `SCHEMA_SHA256` / `ROLE_IO_CONTRACTS`)、`codex_roles/manifest.json`、
  および `test_reflux_originless_compatibility.py` の originless baseline の追随を一斉に強制する。
  D904 が求めたのは「起動形の追加」であって役割の追加ではない。
- 同じ `critic` role に対して別の入出力 schema を projected 起動で使う先例が main に実在する
  (8c の `p3_autonomous_workload_trial.py`)。review ledger の I/O contract は Codex adapter 側の
  契約であり、route-local な payload schema を禁じていない。段 3 の所見「pin 迂回である」は
  この先例により refuted とした。

**却下した選択肢:**
- **`critic-b4-closed.md` を新設する** — 上記 pin 閉包を全部動かす。role file を触る変更として
  ユーザー承認は得ているが、承認は「起動形の追加」に対するものであり役割追加ではない。
- **既存 `critic.md` から `Bash` を外す** — D904 が既に却下済み。通常の合成経路が同時に変わる。

## {{D:b4-certified-receipt-has-no-injection-seam}}. certified な閉鎖証拠は注入口を持たず、注入は test-only 入口へ分離する

**決定:** 閉じた critic 起動の certified 経路は、実行器 (`runner`)・実行 binary
(`executable`)・PATH 解決 (`which`)・repository root のいずれも呼び手から受け取らない。
certified factory は固定名 `claude` を PATH から解決し、repository root を module 位置から導出する。
注入が要る検査は `evidence_class="test-only"` を固定した別入口へ分離し、
pair 検査は両 receipt の `evidence_class` 一致を要求して混成を拒否する。
**結果として、実 CLI を通さずに certified receipt を作る経路は repo 内に存在しない。**

**理由:**
- 敵対レビューが、偽 executable または stateful runner を渡すだけで「道具ゼロ・非開示・
  fresh controller」の 3 性質すべてが自己整合した偽 receipt を作れることを示した。
  閉鎖証拠の trust root を、検証対象自身が選べる形だった。
- 中間案として module 属性 (`_CERTIFIED_RUNNER` / `_CERTIFIED_WHICH`) を certified 判定の
  seam にしたが、焦点再レビューが「属性を差し替えるだけで certified を名乗れる」と判定した。
  テスト自身がその操作で certified 正例を作っており、境界が実地でどこにも効いていなかった。

**保証しないこと (恒真な保証にしないため明記する):**
- **同一 process の Python コードが検査を無効化する経路は閉じない。** これは Python の性質であり、
  本決定はテストと通常の呼び手が偽の実行器で certified を名乗れないことだけを保証する。
- **PATH に置かれた binary の同一性は認証しない。** 解決後の絶対 path と sha256 を receipt へ
  残すのみで、監査は receipt の読み手が行う。

**帰結として残した穴:** certified と test-only の混成拒否には専用の負例が無い。
certified receipt を実 CLI 無しに作れないという本決定の帰結であり、当該変異は
**未登録の生存変異**として台帳へ残した (登録すると偽造経路をテストが作り直すことになる)。
