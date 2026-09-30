# 行末空白の可逆最小正規化 (DW-S07)

`git diff --check` に抵触する行末の空白・タブだけを削った (可視文字は不変)。原文は下の job dir の path に残っており、復元はその file を同じ名前へ複製する。

| file | 原文 sha256 | 原文 byte 数 | 変えた行数 | 原文の path |
|---|---|---:|---:|---|
| `data/probe1-run.log` | `dcf50ead1a10600f9dde27b6b8eb52a1fc7c9227468ce50ead602d676442d031` | 7192 | 4 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-shard0-load-20260930/probe1/run.log` |
| `data/probe2-run.log` | `f8f3261f46500b4cf86c309e01260e1cabf12576e6efb0d6497e62b19833a0b3` | 7446 | 17 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-shard0-load-20260930/probe2/run.log` |
| `data/probe3-run.log` | `5fa56d65a778893d9ffff5184d640d77d2c064aba2501253683199322cd7455f` | 5526 | 6 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-shard0-load-20260930/probe3/run.log` |
| `data/probe4-run.log` | `d2e7f8cc97b6c371bdbee67ace842ade114d16edeff1c96e9101574d6f9c59a1` | 5562 | 6 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-shard0-load-20260930/probe4/run.log` |
| `verbatim/s2-plan-out.md` | `2a54b0e6b9605542fdc7bdd8d6781e2f975a74de0df2b67b93d9da60c0ea332c` | 14003 | 3 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-shard0-load-20260930/codex/plan-out.md` |
| `verbatim/s3-consult-out.md` | `0749828d6e24cf718d7667c27082837bc8095558c9f8b023441121026c36d4f5` | 8587 | 3 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-shard0-load-20260930/codex/consult-out.md` |
| `verbatim/s5-author-u1-out.md` | `4abe465e763dd107bb87d46ae2f4f486904fe2aa5acb951c0f978d463d40fc64` | 3182 | 2 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-shard0-load-20260930/codex/author-u1-out.md` |
| `verbatim/s6-fix1-u1-out.md` | `8dded479bb348495f0161576101bcbebe84e84578bb3f45b3c4f467b623ede86` | 2578 | 1 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-shard0-load-20260930/codex/fix1-u1-out.md` |
| `verbatim/s6-fix2-u1-out.md` | `42161a69fc5d2e2e81429855d139d57cdd916d89484ae6ce34cbd7963ebb3248` | 2477 | 1 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-shard0-load-20260930/codex/fix2-u1-out.md` |
| `verbatim/s6-review-a-out.md` | `c61da67af233b58c790d349ac814abb9a850c60abf5509c692328308e1050175` | 5651 | 1 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-shard0-load-20260930/codex/review-a-out.md` |
