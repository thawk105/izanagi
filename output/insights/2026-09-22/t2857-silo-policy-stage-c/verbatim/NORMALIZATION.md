# 逐語の正規化の記録

DW-S07 に従い、`git diff --check` に掛かる行末空白だけを可逆に除いた (可視文字は不変)。原本は wave の job dir
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2857-silo-policy-stage-c/` と同 dir の `codex/`) に残る。復元は、原本と同じ行の行末へ
除いた空白を戻すこと (原本の sha256 で照合する)。

| file | 原本の sha256 | 原本の byte 数 | 行末空白を持つ行数 | 正規化後の sha256 | 正規化後の byte 数 |
|---|---|---|---|---|---|
| `s3-consult-B.md` | `0450e26846e499cbe94241bd718a1240fe96b900eaf004f55cbc0678db2d7c90` | 15775 | 26 | `51ebf2e978a6596bc3a4e1dc68a01564435aa7a73742b2c0ee7720936bb674d5` | 15723 |
| `s6-review-B.md` | `0811d4457836a7cbf450febdff7baeafa0cc4b858a2058d1d609e5bcd6b26499` | 7086 | 17 | `d2c6ddafd30443f5e9fc428a97943fb6007a19a3a63b8fea15cabf010181362a` | 7052 |
| `s6-fix-3.md` | `746e1642b1bef3438b45e354a915449b541f990a91fd4fb3758c29b52f536c7e` | 3185 | 1 | `30777689a884f864810b599dd8a37661adf2f229dfbf2fb0f5bfa767632b6051` | 3183 |
| `coverage-3-summary.txt` | `cc8444738e2f0b58a8e32c5e2826a6f52368b49883b9bfd35e0580c75f7af852` | 7876 | 1 | `a5867f5bf3a13e3fafb38ade3e4dfb7fb10349f3b13d7ceaf9a96d5842cc9629` | 7875 |
