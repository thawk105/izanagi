# [T-1873] generation/search arm の出力単位 (D1066) — 実装 insight

- 対象 commit: `048b0b95a` (実装)、`936998cab` (正本と条件契約世代)
- branch: `worktree-dev-wave-t1873-generation-outcome-unit`
- 実測環境: Pegasus。焦点走は dispatch 経路。

## 1. 何を凍結したか

D1066 は generation/search 実験の arm outcome 単位を `G=2` の最終世代の canonical variant と定め、
判定 3 条件のうち入れ替え追従だけを「descriptor 条件付きの予測構成へ正規化した比較」へ読み替えた。
本 wave は 8b 設計へ §8 手続きに従う再凍結節を追記し、8c 事前登録 §4 へ 8c 固有の 2 点を足して、
同じ commit で条件契約の第 11 世代 record を発行した。判定器の版は据え置きである。

## 2. 裁定が空けた範囲を、狭い側へ埋めた

D1066 は on/off 差と反復単位の対比の扱いを定めていない。ここには次の対称な罠がある。

- **outcome の identity だけで on/off 差を見ると、条件がほぼ恒に成立する。** canonical variant の
  identity は genome と source token の hash なので、独立に合成された 2 つの variant がこれを
  共有することは実質的に起こらない。「異なる」は自動的に真になる。
- **正規形だけで見ると、identity が異なるのに同一と扱う。**

どちらの単独読みも一方向へ緩む。よって成立側は連言、不成立へ倒す側は選言を採った。

- 条件 1 (on/off 差) の成立 = variant が異なる **かつ** 正規形が異なる。
- 条件 3 の same-prediction 短絡 = variant が同じ **または** 正規形が同じ。

どちらも各単独読みより受理集合が狭い。**単独読みへ戻すのは緩和であり、別途ユーザー承認が要る。**
これは 8b の再凍結節にも明記した。

## 3. 段 3 の敵対相談が独立に見つけた 2 件

- **宣言があっても旧経路へ流れる fail-open。** 段 2 プランは「selector の cell 正規化が成功すれば
  そちらを優先する」としていた。2 本のレンズが独立に、`experiment_kind = "generation_search"` を
  宣言し、かつ旧 selector 形の cell も持つ入力が、最終世代の outcome を一切見ずに成立へ到達できると
  指摘した。宣言 marker を最初に判定し、混合入力を判定不能へ倒す形へ変えた。
- **定数の正規形で入れ替え追従が構造的に成立する族。** 「on arm は常に wire A、off arm は常に
  wire B」を返す生成器は、descriptor の中身に応答していないのに、on/off 差も入れ替え追従も
  対比も成立させられる。8b §6 は「一つの同一選択が複数 descriptor で予測されることは、
  データが完全なら descriptor 駆動を支持しないと報告する」と既に書いていた。
  入れ替え元の on 正規形が全 holdout で同一なら、完全なデータでも不成立とする形へ変えた。

## 4. 実装上の閂 — 公開面が exact pin されている

`s8c_result_judge.py` の public 関数集合と `__all__` は、8c の条件 7 評価器が exact 一致で pin する。
public 名を 1 つ足すだけで拒否理由が変わり、判定器の版上げ議論に入る。
本 wave の追加はすべて private に閉じ、公開面と `judge()` の signature、出力 3 表の
key・型・表名を変えていない。selector 経路の判定結果と 3 表 bytes は固定 SHA-256 で pin した。

## 5. 段 6 が閉じた 8 件

段 6 のレビュー 2 本が計 10 件を出し、8 件を採用、1 件を現物確認のうえ反証、1 件は親の担当と裁定した。
採用分はすべて受理集合を狭める向きである。

- 世代 1 の提案束縛が検査されておらず、世代 1 の記録が番号だけでも成立へ進めた。両世代を検証する形へ。
- 宣言 marker が `type(value) is str` で検査されていなかった。
- 入れ替え対応が解決できない行で、実 variant を「期待値」として表へ書いていた。`None` へ。
- 診断が不正値の実体と JSON path を残さず、逆に実行時の絶対 path を焼き込んでいた。
- テストが期待値を production 定数から自己導出しており、仕様 drift を殺せなかった。
- 混合入力・record 入替えの負例が過剰決定で、狙った 1 つの gate を検査していなかった。

**反証した 1 件。** 「同一 variant なのに正規形が異なる」入力が判定不能へ倒れることを欠陥とする指摘は、
意味のある収束 (同一 variant かつ同一正規形、別 variant かつ同一正規形) が既に条件 1 の不成立へ
到達しており、対応テストも実在して緑であることを現物で確かめて退けた。残る象限は入力が
自己矛盾しており、そこから負の主張を出す方が危険である。

## 6. 変異の単一理由性は再照準で成立した

実装子は M1 / M3 / M5 の単一理由性を「確認できない」と正直に報告した。原因は前後の層による
過剰決定である。次の形へ再照準して、局所の一時変異 + 即時復元で 6 件すべてを実測した。

- M1: 世代列の exact gate 自体を緩める (`[1, 2]` 以外も受理する)。
- M3: 入れ替え比較関数だけを軸の識別子のみの比較へ変える (正規形の構築と診断はそのまま)。
- M5: 混入拒否のうち `configuration_id` だけを無効化する。

|変異|落ちた node 数|
|---|---|
|M1 (世代列 gate を緩める)|3 (同一テストの 3 param)|
|M2 (`duplicate` を正常 outcome に足す)|1|
|M3 (入れ替え比較を軸のみにする)|1|
|M4 (入れ替え元の定数検査を外す)|1|
|M5 (`configuration_id` 混入拒否を外す)|1|
|M6 (条件 1 の連言を identity 単独にする)|1|

本走 (baseline + 6 変異) は baseline PASSED、6/6 KILLED、SURVIVED 0、MISMATCH 0。
落ちた node 集合は、親の局所実測・焦点再レビューの静的導出・本走の 3 者で一致した。

## 7. 親 brief の訂正

- **8b 設計 doc の bytes pin が保留中であることは、追記が凍結検査を赤にしないことを含意しない。**
  同 freeze の未既知性 scan は保留中も走り、同一 file 内での三軸語の同居を拒否する。
  追記後に実走して通ることを確かめた。
- 「8c の実走 artifact が存在しない」は「formal な 2 holdout × 3 arm の `G=2` terminal artifact が
  存在しない」に限定すべきだった。operational pilot の attempt artifact は存在する。

## 8. 本 wave が閉じていないこと

- **提案の wire から、実際にコンパイルされた述語・source token・variant identity までの鎖は
  再検証していない。** 検証は提案 artifact の bytes と binding digest の照合までである。
  鎖を閉じるための実走成果物が存在せず、8c 事前登録自身も個体 cross-binding を未実装と記す。
  最終 outcome を `certified` だけに限ったことと、cell 束縛の検査で穴は狭まったが、閉じてはいない。
- **判定の詳細な不一致は、判定器の構造化返値には残るが、凍結される 3 表からは復元できない。**
  入れ替え行の期待 variant を表へ載せたところまでが本 wave の範囲で、診断の sidecar 発行は
  新しい成果物の凍結と consumer を要するため scope 外とした。
- **供給側の配線は無い。** supervisor から判定器へ generation/search の結果を渡す production 経路、
  §5 の判定パラメータの発効結線、対計画用 pilot の事前登録はいずれも別タスクが所有する。
