---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t881-focused-run
seq: 1
title: 変更 file 焦点走の増分を実測して義務を DW-O18 へ強化した — 受入の後段へ走行を足さない (docs のみ、branch worktree-dev-wave-t881-focused-run)
---

## 本文

ユーザー裁定「増分を実測し、10 秒未満なら段 6 受入へ焦点走を追加、10 秒以上なら `DW-O18` の
焦点走規定を強化」に従って実測し、**(c) を採った**。設計判断は {{D:focal-run-rides-along}}。

**実測 (Pegasus gen_S、tip 49cf6a5f、本 wave の worktree checkout、queue は空いていた):**

| 対象 | test 数 | 直列 (全走 junit 由来) | job Elapse | login 往復 wall |
|---|---|---|---|---|
| `test_t793_report.py` | 9 | 1.17s | 8s | 26.79s |
| `test_spool_fold.py` | 158 | 17.66s | 10s | 26.89s |
| `test_campaign.py` | 298 | 86.68s | 16s | 32.00s |
| argv error で pytest 即死 | 0 | — | 5s | 26.87s |

**分岐の根拠は「dispatch が必ず要る」ことである。** `tools/run_tests.py` の dispatch 免除集合は
非実行 flag だけ (`--collect-only` / `--co` / `--help` / `--version` / `--markers` / `--fixtures` /
`--fixtures-per-test` / `--trace-config` / `--setup-plan`) で、**test を実際に走らせる焦点走は
login から必ず計算ノードへ回る**。よって wave が実際に払う増分の下限は **26.8 秒**であり、
閾値 10 秒を 2.7 倍超える。仮に受入と同一 job へ畳んでも (それ自体 `run_tests.py` の改修が要る)、
job 設定だけで 5 秒、最小の実 file で 8 秒、現実に触られた file で 10〜16 秒であり、
やはり閾値を割らない。

**焦点走のコストは file 依存で、median は安いが尾が重い。** 全走 junit (9336 test) の file 別
直列時間は p50 1.17s / p90 31.9s / max 1330.8s (`test_codex_reasoning_ab.py`) で、
179 file 中 **33 file が 10 秒以上**。直近 60 commit のうち test file を触ったのは 9 commit で
**いずれも 1 file**、その 5 種の直列時間は 0.76 / 1.17 / 17.66 / 86.68 / 284.39 秒だった。
「1 本足すだけ」の見積りが安く見えるのは median を見たときだけである。

**採った形:** 焦点走の義務を、受入の後段に足す新しい走行ではなく、`DW-O18` (親がテスト・受入を
走らせる直前に読む節) の既存規定の強化として書いた。変更した test file は受入全走の前に
別 process の単独走で 1 度確認する、全走の緑はその file 単独の緑を含意しない、既に回す走行へ
相乗りさせ受入の後へ足さない、の 3 点。段 6 の fix 巡回で親はどのみちテストを走らせるので、
**義務は「その走行のうち 1 本を単独走にせよ」に落ち、追加 dispatch は原則 0 本**になる。
恒久ルール「開発するほどテストが遅くなる構造を作らない」への整合はここで取っている。

本 wave は docs のみで実装面ゼロのため、子は起動していない (`DW-C00` 軽量版)。`DW-O18` を
参照するテストは節 ID の実在だけを pin しており本文を pin しないことを確認済み。

## 次の一手差分

### 完了

- [T-881] 増分を実測 (login 往復 26.8〜32.0 秒 / job 内 5〜16 秒) して 10 秒以上を確定し、
  (c) `DW-O18` の焦点走規定強化を実装した。
  remaining: none
  base: e6aea4e02aef6078ab5f8ffaaa3eab0540b4ed86d83dcce9ca23cba742d43fed
