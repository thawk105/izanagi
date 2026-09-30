## 直したこと (file:line)

[launch_promo_confirm.py:180](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:180) で、使い捨て clone の `cc/cicada` を `git rm` で除き、C から `git checkout` して mode ごと復元するようにしました。probe 作成後、C と probe の Cicada tree hash、および tip と probe の Cicada 以外の tree manifest を照合し、結果に記録します。ci の dry-run でもこの照合を実行します。D297 検査器の呼び方と受理条件は変更していません。

## login で行った検査と結果 (未実走の明記)

ci の `--dry-run` は **rc=0**。C と probe の Cicada tree hash はともに `0db663e41a86eb3cffc91045e0399cb965f3aa1b`、Cicada 以外の manifest も tip と probe で一致しました。Python 構文検査、`git diff --check`、`check_codex_agents.py`、`check_docs.py` も rc=0 です。CI build と D297 検査器の本走は今回**未実走**です。

## 総括

probe の file mode を含む tree 復元と一致検査を実装し、ci の dry-run で確認しました。