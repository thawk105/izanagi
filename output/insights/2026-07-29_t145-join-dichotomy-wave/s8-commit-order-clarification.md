authority: none
default_effect: no-state-change

# T-145 段8 — mutation anchorと記録commitの順序明確化

## 実測した無駄

`DW-O19` はtracked mutationを統合commit後に限定する。一方で `CLAUDE.md` はphase完了を実装と同じ
commitへ含め、`DW-S07`はmutation台帳をinsightへ凍結するよう要求する。順序が明記されていなかったため、
T-145ではcode-only provisional commitで本走した後、並行mainとphase記録を統合してcommit identityが
変わり、最終anchor上で同じmutationを再走した。

## 是正

`DW-O19` に次の順序を明記した。

1. codeとphase完了を同じ統合commitへ固定
2. そのcommitをanchorにtracked mutationを本走
3. commit identityを含むraw ledger/harnessは後続の記録commitへ置く
4. mutation後にanchorをamendせず、台帳の自己hash循環を作らない

権限、mutation復元、phase同commit、provenance、push境界は変更しない。

初回追記は `docs/dev-wave/**` hard ceilingを192 bytes超過し、`check_docs`と実repo testが赤になった。
ceilingは上げず、既存 `DW-O19` の重複表現を意味等価に縮約して上の順序を統合した。fail-fastでない
shell列により赤の後へcommitが進んだため、同commitを緑確認後にamendした。
