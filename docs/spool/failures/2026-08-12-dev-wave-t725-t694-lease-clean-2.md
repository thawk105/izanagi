---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-12
wave: dev-wave-t725-t694-lease-clean
seq: 2
---

## supersede 追記

- F191 **supersede: 2026-08-12** — 恒久対応の安全配線 点 1「親が用意した message template へ SHA だけ差し込む」は実装しない。待ち手は `git merge --no-ff --no-commit` → `git commit -F` で merge commit を作るので、取り込んだ main SHA は second parent として commit object に不可変に記録される (実在 commit `ce46e128` の parents で実測)。message 本文への差し込みより強く、改竄もできない。
- F191 **supersede: 2026-08-12** — 点 2「provenance preflight」は `git commit --dry-run -F` と行頭 `AI-Agent:` の存在検査では満たさない。`docs/ai-provenance.md` が commit 前に要求するのは `tools/check_ai_provenance.py --message-file` の rc=0 であり、こちらだけが product/model/reasoning/role の順と許可値を検査する (実測 0.097 秒・local 実行・形式違反を実検出)。待ち手は `stage=merge-message-provenance` としてこれを merge の後に実行する — checker は `MERGE_HEAD` の有無で検査対象 path を変えるため、merge 前だと staged path が空になり検出力が落ちる。
- F191 **supersede: 2026-08-12** — 点 3 後半の述語は option なしの `git status --porcelain` ではなく `git status --porcelain --untracked-files=no --ignore-submodules=none` とする。untracked まで拒否すると、`.gitignore` に無い実在の floor 生成物 (`output/env/pegasus/floor/attempts/submissions/`、`.../job-staging/`) を持つ稼働中 wave の受入が claim 前に rc=2 で止まることを実測したためで、untracked の扱いは裁定へ返した。
- F191 **supersede: 2026-08-12** — この検査が保証するのは「`git status` を実行したその時点で tracked 木が HEAD と一致していた」ことだけである。20〜40 分走る受入 command の走行中に入った変更は覆わないので、受入結果に「投入の瞬間に一致した」とも「走行中ずっと一致していた」とも書かない。走行中まで覆う設計は裁定へ返した。
