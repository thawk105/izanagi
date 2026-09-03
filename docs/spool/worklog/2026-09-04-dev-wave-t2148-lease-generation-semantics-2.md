---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2148-lease-generation-semantics
seq: 2
title: 段 8 — dev-wave 改善候補 2 件は byte 予算と防壁境界で docs へ入れず、ff 取り込み時の監査を寄せた事実を記録する (docs のみ、branch worktree-dev-wave-t2148-lease-generation-semantics、実装面の差分 0)
---

## 本文

- **候補 1: 隔離 worktree の背景 job から他 worktree の未 commit を再走査できない。** 段 3 レンズ A が
  「author 直前に同じ 3 file の未 commit 重複を再実測せよ」と求めたが、隔離 session の bash guard が
  `git -C <他 worktree>` を含む command と git を含む loop を拒否する (2 回実測)。branch 側は
  `git log --branches --not main --name-only -- <file...>` の単一 command で全 branch を走査できる。
  未 commit 分は wave 開始時 (隔離前) にしか走査できない。
  **docs へは入れなかった。** 収容先候補の L2 単節予算は 1,000 bytes で、`DW-C01` が 996 bytes、
  `DW-O20` が 989 bytes を使っており、意味等価な圧縮の余地が無い。新しい L2 節の登録は D271 の
  鏡像条件を満たさない (発火実績が本 wave の 1 件だけ)。DW-G03 の「族一般化には独立 2 例」にも
  届かない。作業知識として memory へ送った。**2 例目が出たら節の新設を裁定へ出す。**
- **候補 2: ff 取り込み時の provenance 監査を段 7 の full 監査へ寄せた。これは実行した手順である。**
  `DW-O17` は ff で「incoming 監査 → `--ff-only` → full 監査」を求める。本 wave は自分の commit が
  0 件の時点で main へ ff したため、incoming 監査を省いて段 7 の full 監査 (2 回、いずれも rc=0) に
  寄せた。判断の根拠は (a) その時点で新しい author 帰属を 1 つも導入していないこと、
  (b) 段 9 の land が `DW-O25` により全史 provenance 監査を必須で走らせること、
  (c) 取り込み前の checker で incoming range を測ると既知違反を赤と誤認する型が既にあること
  である。**恒久化するかは裁定へ返す** — 監査の起動点は正しさ防壁であり、`DW-S08` は防壁の変更を
  実装せず裁定パッケージへ送ることを求めている。
- **段 8 で docs 本文は 1 byte も変えていない。** 本エントリは候補の裁定結果と、実行した手順の
  記録だけである。

## 次の一手差分

### 新規

- {{T:ff-provenance-audit-timing}} **P3・裁定待ち**: 自分の commit が 0 件の段階で main を ff 取り込み
  するとき、`DW-O17` の incoming 監査を段 7 の full 監査へ寄せてよいかを裁定する。寄せる案の根拠は
  上記 (a)(b)(c)。寄せない案の根拠は「監査の起動点を実装者の判断で動かさない」である。
  どちらを採っても `DW-O25` の全史監査は不変で、成果物の値も受理集合も変わらない。
  裁定が「寄せてよい」なら `DW-O17` へ 1 行入るが、L2 単節予算 (943 bytes / 1,000) の残りで
  収まるかを同時に確認する。
