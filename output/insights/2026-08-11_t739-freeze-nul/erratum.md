# erratum — 逐語の可逆最小正規化 (2026-08-11 [T-739])

commit 前の機械走査で、逐語に (a) 生の NUL byte、(b) 行末空白、(c) 末尾 newline の欠落 が見つかった。
いずれも `git diff --check` と repo の走査に抵触するため、**可視文字を変えない可逆最小正規化**を
施した。原文の digest と byte 数、復元法を以下に記録する (D88)。

## 復元法

1. `«NUL»` を byte `0x00` へ戻す。
2. 行末空白と末尾 newline は復元しない (原文 digest との照合にのみ使う)。
   これらは表示に影響しない空白であり、原文 byte 列が必要な場合は下表の digest で同定する。

## 対象

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 施した正規化 |
|---|---|---:|---|---:|---|
| `verbatim/s2-plan.md` | `452845df6cfa922619b7655c8f5d11f2ef29ec1eb79bf5d852e2acf19a897431` | 21610 | `0c6212d34b7be40b3fd3269996115626146ba81e9d1e4bf4768d6b01196e71fe` | 21611 | 末尾に newline を 1 個補完 |
| `verbatim/s3-lensA.md` | `7de017ab3a54dcb51cb8f55245b220f0d6c9b253d98f5c30fbc5489e346847c3` | 20549 | `48c3e59025b12737a5597847e2940336f1ee8e50803e0fcb50cdf08a8a35c720` | 20550 | 末尾に newline を 1 個補完 |
| `verbatim/s3-lensB.md` | `93d9bd314b7d56de66094b25245abb1604f9dd242b5f1eab630a580cbec109bc` | 17659 | `86c1d86c751071c61c6b7472850f914e4b5faede4e17f906f49b886a6c918b07` | 17620 | 末尾空白を 20 行から除去、末尾に newline を 1 個補完 |
| `verbatim/s4-adjudication.md` | `f00a0b57acb2505c991b31dc5f1ed1f25281d51dc356ed4267845b2ebfb03382` | 13960 | `e83547b0d6cdcae6ed9524f789c3200b5f2ad60ecc1f447bb3d86e097f564291` | 13972 | 生 NUL 2 個を `«NUL»` へ defang |
| `verbatim/s5-impl-out.md` | `1f8b9e3dca817da430e6eab4219b83ec368de623c2b95dbaa96457e5c39f93e2` | 12466 | `d0cde8513c33b03f81ce03328cff00a1d77e16946168adc7d2032026a6a8d885` | 12467 | 末尾に newline を 1 個補完 |
| `verbatim/s6-fix-out.md` | `c6c7d535a0d8b8e0feb7858bbba42a76fd11cdab279a91be68d7a1db3345b026` | 2892 | `ef529cb98a4067edad39f59a040d2e9ae9f5a01da673e769934402726b3f0830` | 2893 | 末尾に newline を 1 個補完 |
| `verbatim/s6-review1.md` | `94a2f5d7469037d05c762bb5992d58b52397b24a2be4ebcd37ffc24fbbc52f1f` | 4776 | `112e52b9839508840f91767260c7ff45fc5282e1cd632f9c7d9302c34ec929a3` | 4777 | 末尾に newline を 1 個補完 |
| `verbatim/s6-review2.md` | `d107620751da352c4a8832cbfd39b28a77d0ccd935823e913c23d935d9d8e18d` | 5244 | `9f7911fb356f386a8677286c2bab9eb5e0f8ad527ecf2afa501732e32a0a4f75` | 5229 | 末尾空白を 8 行から除去、末尾に newline を 1 個補完 |
