---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t523-holdout-admission
seq: 2
---

## 新規

### {{F:holdout-triple-in-test-fixture}}. holdout 保護を実装する wave が、そのテストで holdout 三軸を同居させ未知性証拠を汚染した [計測汚染] [テスト代表性]

- 事象: holdout 実測の admission を実装した wave が、追加したテストファイルに
  読み比率 80・偏り 0.9・rmw 0 の三軸を同居させた。freeze の未知性検査は
  「同一ファイルが三軸の正規表現すべてに一致したら 1 hit」と数えるため、H1 の
  conjunction hit が 1 件立ち、launch certificate の clean scan が拒否に倒れた。
  親が全 12,645 file を走査して範囲を確定した (H1 = 当該 1 file、H2 = 0 件)。
- **同じ wave で 2 度起きた。2 度目は記録段である。** 段 6 レビューの逐語を
  `output/insights/` へ commit した時点で、レビューが攻撃例として引用した workload dict が
  三軸を作り、再び clean scan が拒否に倒れた。**実装だけでなく、証拠を記録する行為そのものが
  汚染源になる。** 段 7 契約が凍結前の三軸走査と可逆 defang を求めているのはこのためだが、
  親はそれを実施せずに commit していた。可逆 defang + erratum で解消した。
- 根本原因: 保護対象を扱う実装は、その保護対象の識別子を fixture や逐語に書きたくなる。
  既存テストが合成 fixture へ実物と違う holdout 名を使い、直後に「実 holdout 名が
  セル ID に現れない」ことを assert しているのは、まさにこれを避けるためだった。
  同 wave の別段では、この対になった 2 行の片方だけを書き換えて赤にする違反も起きている
  (52 箇所の一括改名を親が差し戻した)。
- 恒久対応: 保護対象を扱う wave では、**コードだけでなく逐語・材料・fragment を含む
  追加変更した全 file** に対し `orchestrator/campaign/s8b_holdout_freeze.search_repository` を
  親が走らせ、全 holdout の `conjunction_hits` が空であることを land 前に実測する。
  **記録 commit の後にも走らせる** (記録そのものが汚染源になるため)。
  fixture や逐語が保護比率を必要とする場合も、偏りと rmw の literal を同じ file に置かない。
- 再発検知: launch certificate の clean scan (`clean_scan_digest`) が受入全走で発火する。
  **ただし通常の焦点テスト走では当該経路が走らず、変異 harness の baseline と
  受入全走でしか検出されない。** 焦点走の緑を根拠に汚染なしと判断してはならない。

### {{F:dynamic-node-id-cannot-be-preregistered}}. 実行時に決まる node ID は変異 spec へ事前登録できない [手順漏れ]

- 事象: 変異の期待 node に、実行時サフィックスが付く real-repo 変種の node ID が含まれた。
  変異 harness は期待 node が pytest の collection に実在することを事前検査するため、
  この ID を登録できず起動前に停止した (`期待 node が pytest collection に実在しない`)。
- 根本原因: pytest の collection 時 ID と実行時 ID が一致しない test が存在する。
  変異の期待集合は実行時の失敗 node から作るため、両者の空間差がそのまま登録不能になる。
- 恒久対応: 当該 test を変異 runner の対象から明示的に外し (`--deselect`)、
  期待集合からも除く。**外した test が何によって担保されるかを worklog に書く**
  (本件では受入全走)。除外を黙って行わない。
- 再発検知: harness の事前検査そのもの (fail-closed で起動前に停止する)。
