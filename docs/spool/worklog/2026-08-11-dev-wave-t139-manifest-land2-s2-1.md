---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t139-manifest-land2-s2
seq: 1
title: T-139 land 2 session 2 — 承認 manifest の実装は停止し Git trust root だけ入れた、裁定 4 問を返す (コード + docs、変異 8/8、branch worktree-dev-wave-t139-manifest-w2)
---

## 本文

- **ユーザー裁定 RP-1 (a) の実装は段 2 と段 3 の 2 レンズが独立に NO-GO とし、親が段 4 で
  7 件を「本 session では実装しない」と裁定した。** 実装したのは §S7 #2 (Git trust root
  部分集合) の 1 件だけである。裁定パッケージ = `output/insights/2026-08-11_t139-manifest-land2-s2/`。
- **停止の理由 1: 承認済み文書だけでは受理述語が一意に決まらない箇所が 4 件ある。**
  §6.3 の 3 者再読は `CMakeCache.txt` の raw pointer が schema に無く構成できない。
  §4.13 の create-only 被覆は authoritative な intent 母集合が無い。§6.1 の stage 間整合は
  peer receipt を誰が同定するかが未定義。§6.8 の `J` 再導出は transcript の canonical byte
  grammar が無い。**`record-items-v2.md` と `receipt-schema-v1.json` は D282 で exact bytes
  承認済みで、本 session は bytes を変更できない。**
- **停止の理由 2: D291 の land で承認根が `F_r` と `F_p` の 2 本になり、manifest 表現が未裁定に
  なった。** `addendum_b` の exact bytes 承認は D291 側にしか無く、承認根なしで解決すると
  §S7 #1 の穴を `addendum_b` role で新設することになる。共有 1 個の `approved_blobs` へ
  両者の role を union する形は D291 の「2 role ちょうど」を破る。
- **停止の理由 3: D292 により、RP-4 (a) の条件が揃っても別の canonical decision なしには
  pilot は開かない。** ただし D292 が定めたのは解除権限と手続きだけで、解除条件の中身は
  定めていない。3 文書の凍結承認は将来の条件候補としては残る。
- **段 6 の敵対レビュー B が親の裁定パッケージ自身へ must-fix 6 件を出し、親は 7 件を撤回・
  訂正した。** 最も重い誤りは「公表 core 3 文書の凍結承認 + fold は D291 として既に起きた」で、
  **これは偽である** — D291 が承認したのは 2 role ちょうどで、追補 P の blob は明示的に未承認。
  また「新規の休眠コードを積むことではなく既存の穴を塞ぐこと」は production 結線済みと
  誤読させるため撤回した。`orchestrator/preregistration/` を呼ぶ非 test caller は repo 全体で
  **0 件**である。
- **段 3 の第 2 レンズは 3 回投入した。** 1 回目は必読資料 1 件が worktree 未取り込みで
  fail-closed (正しい停止だが 1 巡無駄)、2 回目は `--max-cli-reported-tokens` の既定 100 万を
  超えて SIGTERM (23 分・50 model call を消費して**成果物ゼロ**)。3 回目が rc=0 で返った。
- **段 1 の実測が前 session の裁定根拠を 1 本崩した。** RP-2 の事実欄にある
  「本環境の `/usr/bin/git` は owner nobody」は、前 session の lensA が **codex 子の sandbox 内**で
  測った値だった。親環境の実測は `uid/gid = 0/0` (root)。本 session の lensA が
  `/proc/self/uid_map` を読み、host UID だけを namespace UID 0 へ写す構成で host root が
  overflow UID 65534 に見えることを確認した。**RP-2 (a) の選択と実装部分集合は不変**だが、
  却下理由「(b) を採ると本環境を拒否する」1 本が消えた。あわせて両レンズが
  「RP-2 (a) を『owner に依存しないので十分』と記録してはならない」と一致した
  (部分集合は owner に依存しないが、十分性は独立には証明されていない)。
- **変異検査が静的レビュー 2 本の見落としを 1 件見つけた** (F126 の再発として記録)。
  1 巡目で `extensions.partialClone` の拒否 gate を殺す変異が SURVIVED した。負例の
  `match="partial clone"` が隣接 gate の別 message にも当たるため、**gate を消しても同じ test が
  緑のまま**だった。照合を拒否理由の完全一致へ厳格化し、同型の緩い照合 6 nodeid を同時に直した
  (production は無変更)。2 巡目は 8/8 一致・MISMATCH 0。
- **`GIT_NO_LAZY_FETCH` は段 4 の 8 項目に無かった追加である。** 親の列挙漏れであり、
  promisor 拒否の補助防壁で受理集合を広げる方向が構造的に無いため、段 6 で維持を裁定した。
- **受入全走: rc=0 / 8877 passed / 20 skipped / 570.15 秒** (request `903840.nqsv`、
  tested tip `1fb9d5e0`)。**lease 取得に 1 時間 48 分**かかった (待ち手は正本
  `tools/dev_wave_wait.py` の 30 秒間隔 claim loop、上限 7200 秒)。取得後に待ち手が local main を
  取り込んでから走った。焦点 4 file の実走は fix 前 96 passed → fix 後 110 passed。
- **段 8 の改善候補は 5 件。3 件は `docs/dev-wave/**` の L1.5 予算に当たるため [T-789] へ回付した**
  (RP-5 (a) と同じ制約・同じ routing 先。裁定パッケージ Q5)。**2 件は本 session で処理した** —
  (i) 待ち手 script が「exit 0・stdout 空」で完了通知を出す事象を 5 回実測し
  (producer 生存、`.done` も成果物も無し)、結果を job dir のファイルへも書く運用を memory へ追記。
  (ii) 変異 spec の root exact key で 1 度弾かれたが、**これは既存 memory が既に正しく
  記述しており、親の適用漏れだった。**新規記録はしない。
- **段 9 で land しない** (S6 (a)、本 session は最終ではない)。branch tip を次 session へ引き渡す。

## 次の一手差分

### carry

- [T-139]
