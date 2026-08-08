---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-08
wave: dev-wave-t639-admission-scope
seq: 2
---

## {{D:admission-scope-deny-only}}. admission registry の適用 path を広げ、`tools/pegasus/` 外は deny class だけに閉じる

**決定:** admission registry (`tools/pegasus/admission_registry.json`) は repo 内の canonical な
相対 path を exact key として登録でき、hook は配置場所を問わずその entry で判定する。ただし
次の 3 点で受理集合が単調に縮むことだけを保証する。

1. **`tools/pegasus/` 外の entry は `unknown` / `dispatch-required` しか取れない。**
   loader・hook wrapper・hook lookup の 3 層が非 `tools/pegasus/` の `local-ok` を拒否し、
   非 `tools/pegasus/` path が sanctioned 集合へ入る経路を持たない。
2. **未登録 = 拒否の閉包は `tools/pegasus/` 配下にだけ残す。** それ以外の未登録 path は従来どおり
   通す。全 tool の分類完備は目標にしない。
3. **registry load 障害時**は、hook が静的に持つ非 `tools/pegasus/` 登録 path の投影も拒否側へ倒す。
   投影と正本の drift は集合一致の meta-test が塞ぐ。

強制面は Claude Code の Bash tool が実行 target と認識した綴りに限られる。cwd 相対・
`python3 -c`・未解析 launcher・Codex 子・ユーザー端末・cron・subprocess の内側は本決定の射程外で、
D103 / D105 と F121 の既知残穴のままである。

**理由:**
- 分類の実測はユーザー端末の手番であり (D175 族、F159)、AI 側で登録を増やすには
  「測らずに登録できるのは deny 側だけ」という非対称が必要になる。
- 適用 path を無条件に広げると、壊れた registry が管轄外 key へ `local-ok` を与えて
  重量コマンドの既存拒否を許可へ反転できる。既存の lookup 防壁 (管轄外 key を無視する) は
  registry と sanctioned が同時に汚染された整合的破損では素通りするため、
  無視ではなく deny sentinel にした。
- `tools/**` を prefix 閉包にすると日常 tool を全拒否し、分類完備 (未了のユーザー手番) を
  前提にしてしまう。

**却下した選択肢:**
- **prefix 閉包 (`tools/**` 未登録 = deny)** — 分類完備が前提になり、裁定の縮小版に反する。
- **非 `tools/pegasus/` の `local-ok` を許す一般化** — 受理集合が広がる方向を開き、
  既存 3 防壁 (lookup / negative corpus / loader fixture) の意味を失わせる。
- **静的 fallback を置かず load 障害時は素通りにする** — 障害時だけ fail-open になる。
