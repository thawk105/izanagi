---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-vhash-interval-gc
seq: 3
---

## 新規

### {{F:parent-ruling-overrode-safer-recommendations}}. 段 4 の親裁定が段 2 plan・段 3 相談の安全側の推奨を 3 度覆し、毎回実測の破損で差し戻された [手順漏れ]

- 事象: VHash md_18 (区間 GC) の段 4 で、親は次の 3 点で段 2 plan・段 3 相談と違う設計を裁定した。いずれも smoke で SIGSEGV・停止を起こした。
  - (1) 外した版の再利用条件を「stock の pop (wts < MinRts)」にした。推奨は「外した時点で走っていた全 tx の終了待ち」。
  - (2) 剪定条件 (d) の足場を committed の可視版に限った。
  - (3) blind write の install を lock なしの CAS のまま残した。推奨は lock 下の install。
  補正 3・4・5 と A13 の 4 巡の診断走行 (smoke3〜9b) を費やし、最後は再利用そのものを諦めた (補正 6 = {{D:igc-prototype-design}})。
- 根本原因: 裁定時に「費用が小さく性能を損なわない案」を優先した。子が挙げた反例 (read set の生ポインタ、足場の pending 版、削除と挿入の競合) を実走で確かめる前に退けた。
  lock を使わない連結リストの削除という既知の難所で、推奨を覆す根拠 (反例の否定) を裁定文に書いていなかった。
- 恒久対応: memory `ruling-override-needs-counterexample-refutation` — 段 4 で子の安全側推奨を覆すときは、子の反例を否定する論証を裁定文に書く。
  書けないなら推奨を採り、費用は計測で後から削る。
- 再発検知: 段 6 レビュー prompt に「段 4 裁定が段 2・3 の推奨を覆した箇所の列挙と、その根拠の有無」を検査項目として入れる (同 memory の How to apply)。

## 再発

### F1

- **再発: 2026-09-30** — VHash md_18 の段 5 B1-11 指示で、親が段 4 裁定 S8 (壊し正例は ronly_wait cell、帰属は長い read-only tx を含む辺) を「期待した経路で検出が 1 つ以上」と手で言い換えた。
  集計は、事前登録の正例が発火 0 のまま K・R の検出で verification=passed を出した。段 6 の敵対レビュー 2 本 (R1・B-01) が独立に must-fix として捕捉し、fix B1-12 で S8 の literal に戻した ({{D:igc-s8-positive-not-substituted}})。
  恒久対応は memory `ruling-literals-in-prompts-point-to-the-file` (裁定 file を正本と指し、literal を手で再記述しない) のまま。今回は field 名でなく**判定条件**の言い換えで、正しさゲートを緩める方向に働いた点を追記した。
