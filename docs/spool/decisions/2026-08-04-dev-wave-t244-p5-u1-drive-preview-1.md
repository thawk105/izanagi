---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: dev-wave-t244-p5-u1-drive-preview
seq: 1
---

## {{D:u1-driver-injection-rejection}}. claude-headless の run_trial は explicit keyword の drive / preview 注入を拒否し、provider kind を exact plain str に限る

**決定 (1): 正式経路の driver 注入拒否は explicit keyword に限り、そのとおりに名乗る。**
`provider_kind == "claude-headless"` の `run_trial` は、caller が `drive` / `preview` keyword へ
sentinel 既定値以外を渡した呼び出しを artifact 作成前 (`run_root` 作成・journal・provider
初期化のすべてに先行) に拒否する。省略検出は private sentinel 既定値の identity 比較で行い、
gate 直後に module 現在値 (`trigger.drive_iteration` / `_preview`) へ一様解決する。
D148 決定 (2) が未閉として残した drive / preview 部分を、2026-08-04 のユーザー裁定
(worklog の /rulings 記録) に従って閉じる。ただし**「caller 差し替えを閉じた」とも
「P5 第 1 要件を閉じた」とも名乗らない** — 閉じたのは public `run_trial` の explicit keyword
admission の縮小だけである。

**非保証 (段 3・段 6 の敵対検証が確認した残存経路):** private sentinel の持込み (introspection
`__kwdefaults__` 経由で取得した sentinel を明示すれば gate は省略と区別できない)、module 属性の
再束縛、sentinel を束縛した wrapper / `functools.partial`、同一 process 並行実行中の差替え、
internal entrypoint への直接注入と driver 直接反復 (D114 のとおり)、保存済み artifact からの
事後判定 (journal / report schema に driver identity の field が無い)。これらは Python の
同一 process 内では構造的に防げず、機械対策を装う代わりに runbook / phase doc へ列挙した。

**決定 (2): provider_kind は exact plain str だけを受理する。** 状態付き `str` subclass が
membership 検査と各 gate の等値比較を選別的に通せる (段 3 の敵対相談が構成) ため、
`type(provider_kind) is not str` を全 gate の前で拒否する (D114 の `int` subclass → exact 型の
先例)。型違反の診断は membership 違反 (`unknown provider kind`) と分離した。

**受理集合の変化 (D96 手続):** 新たに拒否するのは (i) allowed 値と等値な `str` subclass の
`provider_kind`、(ii) `provider_kind="claude-headless"` かつ `providers is None` で `drive` /
`preview` の少なくとも一方が sentinel 以外の呼び出し、の二群だけである。両方省略・fixture の
明示注入・既存 providers 拒否・internal entrypoint・consumer / schema は不変。受理集合外の
観測可能な変更として、省略時の既定解決が定義時束縛から呼出時の module 現在値束縛 (late
binding) へ変わり、signature 既定値が関数 object から opaque な sentinel object へ変わる。
境界テストは同一変更単位で更新した (既存 2 テストの seam 移行を含む)。

**却下した選択肢:**

- `drive` / `preview` kwargs の撤去 — fixture 経路の正当利用 12 call を壊す。
- 既定関数 object との同一性比較による省略判定 — 既定関数を明示注入した呼び出しを省略と
  誤認する (変異登録で両極を殺す)。
- 新しい opt-in flag — 省くだけで検査が外れ恒真化する (D148 と同じ理由)。
- 自己申告 receipt + consumer — 下流が読まない field は恒真な保証 (D148 と同じ理由)。
- provider 別の resolver 分岐 — 分岐が増えるだけで omitted の意味変更は消えず、単純さを失う。
- テスト用注入手段の温存のための gate 免除 — 既存 2 テストは module 属性 seam へ移行して解決した。

**研究状態への影響:** certified 選択・材料レポート・proof chain・凍結 bytes は不変。変わるのは
自律試行の受理集合 (上記二群の拒否) だけである。
