---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t1209-verifier-identity
seq: 3
---

## 再発

### F71

- **再発: 2026-09-17** — 変異 spec の期待 node に、**変異下でしか生まれない parametrize id**
  (存在しない path を identity 集合へ足す変異で増える
  `test_every_required_identity_path_is_tracked_in_this_repo[<新 path>]`) を書いたところ、
  harness の起動前検査 `期待 node が pytest collection に実在しない` で fail-closed 停止した
  (走行 0、作業ツリーは clean のまま)。preflight は **baseline の** pytest collection と突き合わせる
  ので、baseline に存在しない node は正しい形式でも登録できない。F71 の「書き手が実 nodeid の形を
  確かめずに書いた」型の派生で、今回は形式ではなく**存在する時点**を確かめていなかった。
  是正は再照準 — 変異を「path を tracked な兄弟 file へ置換する」形にして、期待 node を baseline に
  実在する新 test だけにした (KILLED 一致)。初回 spec と attempt json は
  `output/insights/2026-09-17/t1209-verifier-identity/` に erratum として残した。
  **期待 node は `--collect-only` の baseline 集合に含まれるものだけを書き、変異で増減する
  parametrize id を期待に入れない。**
