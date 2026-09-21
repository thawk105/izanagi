# 行末空白の可逆正規化 (段 7、DW-S07)

次の写しは行末の空白 (space / tab) だけを削った。可視文字は不変。原文は job dir にあり、下の sha256 / bytes と行ごとの空白列で復元できる
(各行の末尾へ記載の空白を戻すと原文 bytes に一致する)。

## measure/S01-set21.log
- 原文 sha256 646a8328ca3a1a9a8105c29c80596a2e87b9a0d0a33ee90a9b3f8d60fd2622da / 8657 bytes → 正規化後 sha256 a16a92d06dfda64e4dfaddc7d9312b2f54dd664b6fc66f3c5c77f26bffbbbc72 / 8655 bytes
- 行末空白 (行番号: 削った文字列の repr): 41: ' ', 62: ' '

## measure/S02-solo-test_b5_contrast_launch.log
- 原文 sha256 db84bf29164419c7b2f9e9d7adaa85d471248ee5896fc6a99c0cf045ed0b9113 / 4680 bytes → 正規化後 sha256 e155513ce85e98df5740455d8ddedbd83c1da52eb77aea04032a537eb900cd93 / 4678 bytes
- 行末空白 (行番号: 削った文字列の repr): 15: ' ', 37: ' '

## measure/S03-solo-test_b5_generator_contrast.log
- 原文 sha256 78fe9a57607b6daa747b4d922ef72e2f4fe73ed1466f6855e23eb54db32e531e / 4767 bytes → 正規化後 sha256 7d4b5637e5d440356508154463660ff32d98d58b2b4e4e93dd796305a45af7cb / 4765 bytes
- 行末空白 (行番号: 削った文字列の repr): 15: ' ', 38: ' '

## measure/S04-solo-test_b5_generator_contrast_report.log
- 原文 sha256 c92da62a9c266d4617652f8df8df77b209b5d299fc629efdda4786c3a2f39048 / 4713 bytes → 正規化後 sha256 5e84c6f9b1e2c98405f395c89e14df27a30b29139cab0265e0abe0235101ced7 / 4711 bytes
- 行末空白 (行番号: 削った文字列の repr): 15: ' ', 37: ' '

## measure/S05-solo-test_ccbench_spawn_sites.log
- 原文 sha256 c2123cb293801e3bd0fe47206663ef84c40bb23d18d74220d459692904807ff3 / 4808 bytes → 正規化後 sha256 18fe9cbc800dcfcb1f92638966ed81100c1de8724e6588a2498f9d19c5dd5160 / 4806 bytes
- 行末空白 (行番号: 削った文字列の repr): 15: ' ', 38: ' '

## measure/S06-solo-test_hooks.log
- 原文 sha256 d5f04d2cee8df73436d15b37a82da5da34df4cba44ba6c1324ea8c46406034bc / 5193 bytes → 正規化後 sha256 a3544ee613d195dd125d0323419079f8858ae6bb81679f118b998119d4b5b734 / 5191 bytes
- 行末空白 (行番号: 削った文字列の repr): 15: ' ', 43: ' '

## measure/S07-solo-test_p3_s4_loop.log
- 原文 sha256 503a1c5de94705535d85bc9ae279251f46ba9210939f8873d676dadf92bc2fed / 5306 bytes → 正規化後 sha256 cf5efb543eb24910a12c5466637e6ba772b8ad359260a96663751209a17edcdb / 5304 bytes
- 行末空白 (行番号: 削った文字列の repr): 15: ' ', 45: ' '

## measure/S08-solo-test_p3_s4_loop_job_contract.log
- 原文 sha256 d1b8b06a0ebc13f6bac08955ac15bf366d491655d942ff198dbc9f60edc1ef22 / 4829 bytes → 正規化後 sha256 39d401bb9f132c91d92ae18f5eb82064f7a981c194fc877d0e4c4596f4af6334 / 4827 bytes
- 行末空白 (行番号: 削った文字列の repr): 15: ' ', 39: ' '

## measure/S09-set23.log
- 原文 sha256 1eb19af170616437368da4f00e18b623c15abbcec658b9a47a2d1dc2810a7162 / 8612 bytes → 正規化後 sha256 5c7fd690f6bef66494b81e800bed3696c2ce7a5ecd20df28d68419fcb31e5dda / 8610 bytes
- 行末空白 (行番号: 削った文字列の repr): 41: ' ', 62: ' '

## measure/S10-set21b.log
- 原文 sha256 3cb7e1b08648e1b9e1e19fd07648d69cbc453f32355651663e6aef3fdead40d5 / 8613 bytes → 正規化後 sha256 3e66c842293140207cc73f4b1c6148abff3a6e05e037593c96e8eecc3191243a / 8611 bytes
- 行末空白 (行番号: 削った文字列の repr): 41: ' ', 62: ' '

## s3-consult.md
- 原文 sha256 607f644fbdaed770bf5fcca9aff4b40d01423fc14a05b2d187db9126e5c11e4c / 14850 bytes → 正規化後 sha256 a3bcd68586413f994d49edd78ccc0eade0910102cd6c505cad62288ea7787d3d / 14758 bytes
- 行末空白 (行番号: 削った文字列の repr): 5: '  ', 6: '  ', 9: '  ', 10: '  ', 13: '  ', 14: '  ', 17: '  ', 18: '  ', 21: '  ', 22: '  ', 25: '  ', 26: '  ', 29: '  ', 30: '  ', 33: '  ', 34: '  ', 37: '  ', 38: '  ', 41: '  ', 42: '  ', 45: '  ', 46: '  ', 49: '  ', 50: '  ', 53: '  ', 54: '  ', 57: '  ', 58: '  ', 61: '  ', 62: '  ', 65: '  ', 66: '  ', 69: '  ', 70: '  ', 73: '  ', 74: '  ', 77: '  ', 78: '  ', 81: '  ', 82: '  ', 88: '  ', 92: '  ', 96: '  ', 100: '  ', 104: '  ', 108: '  '
