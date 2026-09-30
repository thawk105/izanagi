# 可逆な最小正規化の記録 (DW-S07)

`git diff --check` に抵触する行末空白だけを除いた。可視文字は変えていない。原文は job dir に残っている。

| file | 原文 sha256 | 原文 byte 数 | 行末空白の行数 | 正規化後 sha256 | 正規化後 byte 数 | 復元元 (原文) |
|---|---|---:|---:|---|---:|---|
| `data/p2-H-reds.txt` | `cd22ef5fb3e134231190a595b539d7acd9078fc3f80bb88921e3fb3d330eab05` | 9805 | 2 | `5e141bc1ab4e3ddbb325e3b96f9bda6414ebed115bcb0f90e904bcf36d70ec1f` | 9803 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-pyc-warm-20260930/meas/out/p2-H-reds.txt` |
| `reviews/plan-out.md` | `6d804dbd57dd4acc132f20f3c95aadd8254ca2815c72d77c7a00f93b2777e718` | 11570 | 3 | `bc68ad45329d7cbd313929065cc5548242e349cb1eeadb055dc79d1a6984d3c9` | 11564 | `/work/1/SFC/tanab/dev-wave-jobs/acceptance-pyc-warm-20260930/codex/plan-out.md` |

正規化は `sed 's/[[:space:]]*$//'`。復元は上の復元元を写すか、各行末に元の空白 (plan-out.md は 3 行とも半角空白 2 個の Markdown 改行、p2-H-reds.txt は pytest の出力行末の半角空白 1 個) を戻す。
