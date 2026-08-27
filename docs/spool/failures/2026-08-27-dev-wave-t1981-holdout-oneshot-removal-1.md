---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1981-holdout-oneshot-removal
seq: 1
---

## 新規

### {{F:fix-constraint-conflates-main-and-wave-tests}}. fix 子への「既存テストの期待値を変更するな」が広すぎて 1 巡を捨てた [手順漏れ]

- 事象: 段 6 fix 子が「実装を変えず報告して止める」を正しく選んで停止し、fix が 1 巡空転した。
  停止理由は、段 5 の実装子が**この wave で新設した**テストが親の裁定と正面衝突していたことである。
- 根本原因: 親の prompt (`DW-S06-B` の「既存テストの期待値を変更しない」をそのまま写したもの) が、
  **main に在るテスト**と**同 wave が新設・改変したテスト**を「既存」の一語で括っていた。
  前者は緩めてはならないが、後者は裁定と矛盾するなら裁定へ寄せて訂正するのが正しい。
- 恒久対応: fix 子の prompt で 2 種を分けて書く。判定は `git show main:<path>` に在るかで機械的に決まる。
  `docs/dev-wave/workers.md` への収容は L1.5 の byte 予算に阻まれ、D730 の手順
  (既存記述の削減を試す → 独立 3 例以上なら例外収容 → 最後に上限引き上げ) のうち
  **独立 3 例に満たない 1 例**のため見送った。2 例目が出たら同節へ収容する。
- 再発検知: fix 子が「期待値が誤りだと判断した」と報告して停止した回数。
  停止理由が「wave 自身が新設したテスト」なら本型の再発である。

### {{F:naming-ruling-overapplied-to-pinned-identifier}}. 命名の一般則を、既に機械検査で pin された既存 field 名へ過適用した [ドリフト]

- 事象: 親が「無修飾の `generation` を**新しい** field 名に使うな」(D197) と裁定したところ、
  段 5 の実装子が R33 role contract の**既存** field `"generation_id"` を
  `"n_pilot_design_generation_id"` へ改名した。`tools/check_docs.py` が
  `R33 role contract field 'generation' は exact 1 件が必要` で rc=1 になった。
  同 field は R33 事前登録の pin 済み契約名である。
- 根本原因: 裁定文が「新しい field 名」とだけ書き、**既存の pin 済み識別子は改名しない**を
  明示しなかった。加えて、この pin は `check_docs.py` 内の正規表現であり、
  **識別子名で grep しても pin として見つからない** — 機械検査を走らせて初めて出る。
- 恒久対応: 命名を一般則として裁定するときは、射程を「新規のみ」と明記する。
  識別子を改名する変更では、改名前に `python3 tools/check_docs.py` を実装子自身に走らせる
  (今回は fix 子が自分で走らせて戻した)。
- 再発検知: `check_docs.py` の `exact 1 件が必要` 系の違反が、
  wave の意図的な改名の副作用として出ること。

### {{F:blocker-moved-after-removal}}. 主経路を止める欠陥が、撤去の直後に別の欠陥へ移った [手順漏れ]

- 事象: D1124 に従って床値実測の一回性を撤去し、承認引数なしで実 qsub したところ
  (request `952615.nqsv`)、`already consumed` は消えたが job は 67 秒で
  `compiler input manifest の完全検証に失敗: external compiler input is unavailable` で落ちた。
  **cell 予約より手前のビルド段**であり、撤去の終端条件 (12 cell が再測定を妨げないことの実機確認) は
  満たせなかった。
- 根本原因: 撤去の対象だった関門の**手前**に、同じ主経路を止める別の欠陥が同日中に現れた。
  2026-08-27 05:54 の job `951456` はこのビルド段を通過して 350 秒地点の予約段まで到達していた。
- 恒久対応: 「関門 X を外せば主経路が通る」を実装だけで閉じない。**外した後に実機で最後まで通す**
  ことを終端条件にする (本 wave のユーザー指示がまさにこれであり、指示に従って項を閉じなかった)。
  帰属は main 単独で再現するかで決める — 本件は main (`98f61815c`) 単独の job `952631` が
  62 秒で**本文・失敗段ともに一致**する赤を出したため、wave の回帰ではないと確定した。
- 再発検知: 撤去 wave の終端実測が、撤去対象と無関係な段で落ちること。
