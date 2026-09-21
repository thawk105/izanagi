---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: worktree-dw-provenance-cold-diag
seq: 1
title: T-2803 着地後の残存受領証から全史 provenance 監査の再利用可能性を事後診断し、計算ノード dispatch を対照測定した — 着地後の母集団に依頼の 4 種の主分類に入る行は無く、dispatch は受入・land と別 partition に落ちる、裁定パッケージ第 1 案は局所修正なし (診断のみ・実装 0 行、branch worktree-dw-provenance-cold-diag)
---

## 本文

- ユーザー依頼 (2026-09-21、dev-wave 引数の逐語は insight `verbatim/origin.md`) の範囲で 1 wave。起点は entry 1769 ([T-2803]、D2192) の「他 binding・partition・混雑時・計算ノード・実 land の連鎖は未測定」。
  数値・分類・限界・裁定パッケージはすべて一次資料 `output/insights/2026-09-21/provenance-receipt-land-chain-diag/README.md` (生 stdout と dispatch 受領証は `measurements/`、逐語は `verbatim/`) にあり、ここには再掲しない。
  結論は残存受領証からの事後推定であって当時の再利用の実績ではない (同 README §7)。decisions fragment は無し (裁定パッケージは起票せず insight §8、採否はユーザー)。専用 handoff は job dir (repo 外)。
- 起点 local main `5efd69367` (fresh worktree、HEAD == main、開始 gate rc 0)。段構成は軽量版 + 診断 wave の型 (段 2 を省き、段 3 相談 1 本、段 5 author 4 巡、段 6 review 1 本 + 焦点再レビュー)。
- **段 3 相談は must-fix 9 / should 2 / nit 1 を出し全件 real・採用。** 親の前提実測は「bindings 一致 + 祖先」を再利用の実績と呼び、land 側の祖先候補なしの tip を取り違え、1 秒で拒否された land に 206 秒を結んでいた。
  login で監査を 3 走する計画は性能測定 = 計算ノードの規律に当たるので削り、「混雑時 = headroom 不足」「主因は初回だけ」「区画統一で 30〜55 秒」を撤回した。
- **段 6 review (read-only 1 本) は数値を照合したうえで must-fix 9 で NO-GO → 全件 real・反映。** 主因は (a) replay と実装の非同値条件の書き漏れ、(b) 分類ラベルを原因の実証として書いた過剰な断定、(c) 計算ノードと main 履歴の出所不足。
  (c) の是正で親の記述の誤りが 1 件出た — **main の checker が変わった回数を 2 回と書いていたが、reflog を読む probe (段 5 の 4 巡目) で 3 回だった** (T-2804 の land を見落としていた)。焦点再レビューは closed 9 / partial 5 で 2 件を追加是正した。
- probe 5 本は Codex author の unit worktree (`.codex/worktrees/pcd-unit-probe`、branch `dev-wave-pcd-unit-probe`) の ignored 領域に書かれ、tracked 差分 0。正本は job dir へ退避し、repo には `.txt` の逐語だけを置いた。
- 事故 (自分起因、実害小): (1) 親が段 1 と段 4 後に read-only の診断 script を自分で書いて走らせた (F75 型の近接、repo には入れていない)。値は仮説に格下げし、確定値と系統表は author の probe の出力へ置き換えた。
  (2) author 1 巡目 prompt の git 許可一覧に `ls-files` / `ls-tree` を入れ忘れ replay が未判定で止まった。(3) 同 prompt の checker 系統表で T-2804 枝の旧形 2 版を新形に入れていた。
- 工数: codex 6 本 (consult 1、author 4、review 1) + 焦点再レビュー、計算ノード 2 request (14603 / 14604)、login の read-only 走 (目録 3、replay 1、突合 1、reflog 1)。

## 次の一手差分
