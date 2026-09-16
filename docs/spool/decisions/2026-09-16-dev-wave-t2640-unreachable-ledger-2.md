---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2640-unreachable-ledger
seq: 2
---

## {{D:no-ai-loss-acceptance}}. 到達不能 object の `accepted-loss` は AI の内容照合で代替しない

**決定:** `docs/unreachable-object-ledger.md` の `accepted-loss` は、台帳の逐語どおり
**人間が喪失を明示的に受容した場合にだけ**使う。AI が「内容が main に残っている」と照合できたことを
受容へ読み替えてはならない。AI が閉じられるのは救出 (`rescued`)、再到達確認
(`reachable-again`)、不在確認 (`object-missing`) の 3 つである。

救出か喪失受容かを AI に判断させる裁定 (D2044 項 7 など) は、**救出を選べば追加の承認待ちなしに
閉じられる**。救出の代償は小さい — 30 件の実測で恒久的に延命した object は 322 個 (commit 40 本)
だった。ref を作るだけなので working tree も main も変わらない。

**理由:**
- 台帳は `accepted-loss` を「人間が喪失を明示的に受容した場合」と定義している。この状態は監査が
  再報告しても stale 通知を出さない唯一の状態であり、通知対象集合を恒久的に縮める。
  根拠の強さを人間の受容に固定するのは、その効果に見合う。
- 内容照合は着地の証明ではない。basename と basename + `.gz` の候補集合に blob OID 一致が
  あったかしか言えず、別名への改名・mode・object type・探索範囲外の同一内容は見ていない。
  これで `accepted-loss` を出すと、`assessment_verdict` が `indeterminate` のまま
  実質的に `landed` を主張することになる。
- 救出は object を実際に保持するので、判定を甘くする方向の変更に当たらない。

**却下した選択肢:**
- 内容一致を人間の受容の代理とする — 裁定の拡大解釈であり、通知対象集合が根拠不足で縮む。
  段 2 plan と段 3 の敵対 2 レンズが独立に blocker と判定した。
- `pending` のまま記帳して閉じたことにする — 下界が近いか過ぎた entry は毎回
  `pending-ledger-entry` を出すので、常時 due の通知は止まらない。
- 既知良性の類型を記帳なしで認める契約へ変える — D2044 項 7 が明示的に却下している。
