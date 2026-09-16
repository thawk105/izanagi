# 段 1〜6 の逐語保存

authority: none
default_effect: no-state-change

本 dir は [T-2702] wave (`dev-wave-t2702-digest-indicator-consistency`) の親 brief、段 2 plan、段 3 敵対相談 2 本、
段 4 裁定 (plan v2)、段 5 実装子報告、段 6 レビュー 2 本と fix 子報告を逐語で保存したものである。
可変状態の正本ではない。Codex の model は全段 `gpt-6-astra`、plan / consult は `reasoning=medium`、
author / review / fix は docs 権威から導出 (受領証の requested/recorded とも gpt-6-astra)。

| file | 中身 | 受理検査 |
|---|---|---|
| `stage1-brief.md` | 親の段 1 brief (runner.py の 2 経路名は逆で、段 2 が訂正) | — (親が書いた) |
| `stage2-plan.md` | 段 2 plan (`stage=plan`, `sandbox=read-only`) | `check_codex_output.py` rc=0 |
| `stage3-consult-a.md` | 段 3 相談 A (lane `sol`、正しさ境界と意味の整合) | rc=0 |
| `stage3-consult-b.md` | 段 3 相談 B (lane `luna`、実効性・テスト・変異の帰属) | rc=0 |
| `stage4-adjudication-plan-v2.md` | 親の段 4 裁定 = plan v2 (実装の正本) | — (親が書いた) |
| `stage5-author.md` | 段 5 実装子の報告 (`stage=author`, `sandbox=workspace-write`) | rc=0 |
| `stage6-review-a.md` | 段 6 レビュー A (正しさ・意味論・不変条件、GO) | rc=0 |
| `stage6-review-b.md` | 段 6 レビュー B (テスト検出力・変異・波及、GO) | rc=0 |
| `stage6-fix-1.md` | 段 6 fix 子の報告 (レビュー A 所見 5 / 6、文言だけ) | rc=0 |

## 可逆最小正規化 (DW-S07)

保存時に `git diff --check` の行末空白に抵触した 7 file について、各行末の空白を除去し、末尾に改行 1 byte を
足した (可視文字不変)。`stage1-brief.md` と `stage4-adjudication-plan-v2.md` は無変更。復元法 (原文 = launcher が
保存した最終メッセージ本文、末尾改行なし): `stage6-review-a.md` は所見間の空行 25 本が「空白 3 個」の行
(75 bytes 除去 + 改行 1 byte 追加 = −74)、`stage2-plan.md` / `stage3-consult-a.md` / `stage3-consult-b.md` /
`stage5-author.md` は `## 総括` 節の 4 行の行末に空白 2 個 (8 除去 + 1 追加 = −7)、`stage6-fix-1.md` は同 2 行
(4 除去 + 1 追加 = −3)。これらを戻せば下表の原文 sha256 に一致する。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 除去 bytes |
|---|---|---|---|---|---|
| `stage2-plan.md` | `5ae1e1e2772f296a5f1b6f9e8b29f9eaa16001cabf12336aebdb917554951e73` | 15929 | `7eeec84963990b260337e6a6a8f2343eabae57e3d72e60d8054ad64cfea64173` | 15922 | 7 |
| `stage3-consult-a.md` | `9508fa9b57fc13da1d6a100c7405cc6ad30d11d0595061a0c3aef016be6cf883` | 12661 | `326e91904b224c249bef24eaf727f660bf32ce947e89880334f9dfc4bf31a616` | 12654 | 7 |
| `stage3-consult-b.md` | `f3cc783b7f8af4d0169d6bccd8a65becfdaa809e18f4657e47c45ce2d14becce` | 14536 | `6eaf447b22782531a58df3361ef39d4f9d4e5b1a8ca32411a9e6e96bf0273dba` | 14529 | 7 |
| `stage5-author.md` | `ebdc505bb89bfacd4c04ced00d955574ce9e7707eb21711ec05412d5cf12d384` | 4522 | `627d22d6891589f7f1635aaff2fb01609303dff01883c11443fef3b5c0be8d76` | 4515 | 7 |
| `stage6-fix-1.md` | `fdf7ebcc832cfca73949b31cad541cacae8a84e9aa910173d72f53d8b4fc326c` | 1278 | `22607cc526b7ab91ce68acbab7ca215f5dcca891e3e69cfe56f62af0bb8ee81d` | 1275 | 3 |
| `stage6-review-a.md` | `4b7586f2a3625b41b5f55087f016484f0ed5a543069bbbac326246318dcc6f38` | 7542 | `cd231bc2ce7705e2ec9f1101b5fa566caaaf0f6bda1ce38df6d2695aef544540` | 7468 | 74 |
| `stage6-review-b.md` | `8cfc9aa8aad201e21bb42ba3d50a5df1e485d011d5aa3d71a6165d0b15beefd6` | 13462 | `06c301828506a7e590a2a9b938caa3efb3fda956cd4fb97637acc0072f17a0c4` | 13455 | 7 |
