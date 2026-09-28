# 子エージェントの読書メモ (二次資料)

親 (`../README.md`) の比較表と 3 分類の材料として、原典を読んだ 5 本の子エージェント (Claude sonnet、2026-09-29) が
書いたメモの写しである。**一次資料は原典 (`../README.md` §11 の SHA-256 で同定) と親の README であり、
このメモは二次資料である。** 親が原典テキストで照合した逐語は `../README.md` に置いたものだけで、
ここにしか無い逐語・頁番号・判定は照合していない。

| file | 担当 | 元の SHA-256 (repo 外の原本) | 写しでの変更 |
|---|---|---|---|
| `A-ccbench-cidr.md` | CCBench §7、CIDR 2021 | `25877b5754bbf642791ad589b578aad9d0e5bae77ef192ecf254e84e5e7430ff` | 行末空白 1 行を除去 (可視文字は不変。復元は原本から) |
| `B-cicada-tictoc.md` | Cicada、TicToc | `b3fadf32eb349ba9707313812227a6b936ac36790360b1a074647d7906181b8b` | なし |
| `C1-mvcc-gc.md` | Steam、SAP HANA、vDriver、Wu 2017、LeanStore、PostgreSQL / Oracle | `cf7c92b0c485a9f3131e7f7ace037c2fc26aa0ba7874b6b72f4e84c0a6c228a3` | なし |
| `C2-mvcc-engines.md` | Hekaton、HyPer、ERMIA、BOHM、Silo、Freitag 2022、cMVBT | `fd7cff078666e193efc40487b6d223272b44a0f1acb3a1ebd946e58e5c2b2546` | なし |
| `D-ts-forwarding.md` | Sundial、MaaT、Bayer 1982、Shirakami、Rebirth-Retire、MV3C、Morty、Lomet 2012 (書誌のみ) | `4b1b6bca6d78211d2b9f92628aca356705ddf70935a9219737e2ff95ba156304` | なし |

メモ中の path (`/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/` など) は repo 外で、生存は保証されない。
Lomet 2012 の本文は親が直接読んだ (`../README.md` §6.1・§7・§8)。D のメモには Lomet 2012 の独立した節は無い。
