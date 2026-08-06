---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t529-activation-impl
seq: 2
---

## {{D:activation-authority-blocked-by-entry-surface}}. 活性化権限は入口面が Python 層に閉じるまで実装しない

**決定:** 契約世代の活性化権限は、D196 の保留を継続する。保留の根拠は D196 から次のとおり更新する。

- D196 の理由 (a)(historical resolver を production consumer へ配線する) は**充足した**。
  配線先の全 site 走査で追加配線先が 0 件であることが確定し、
  合法な後継世代を current にしても記録 hash からの解決経路が committed floor protocol を
  受理することを実 artifact 上で確認した。current 束縛の live admission が拒否するのは
  D202 が意図した設計であり、proof chain の破壊ではない。
- D196 の理由 (b)(発火する正例を書けない) は**充足していない**。正規の 2 世代目が存在せず、
  `DW-G04` が要求する artifact path も計測 ID も書けない。module 属性 patch による合成正例は
  import 時の初期化経路を駆動しないため、複数世代を import 時に拒否する実装でも通る。
  すなわち永久 fuse と観測的に区別できない。
- あらたに、**裁定された設計そのものが 2 入口で実現できない**ことが判明した。
  floor の公式経路は shell wrapper が Python driver 起動より前に attempt ディレクトリと
  driver の stdout / stderr / launch marker を書く。適格性の driver は `.git` を持たない
  git-archive 済み source stage から起動され、authority root は CLI 解析後にしか判らない。
  「全入口が最初の書込み前に同じ活性化状態を検査する」という要件は、この 2 入口では
  Python 層だけでは満たせない。

**理由:**
- 部分実装すると、入口被覆率の過大報告と「永久 fuse と区別できない保証」の 2 つを同時に
  台帳へ残す。後者は D176 が型分離を却下した理由と同型の失敗であり、前者は
  「実装したふりをしない」という既存規律に直接反する。
- 記録 hash からの世代解決を「当時 active だった証明」として扱ってよいかは未裁定のまま残っている。
  activation record の trust root を何にするか (裁定済み) とは別の問いであり、
  未活性の後継世代を記録した artifact まで再検証が受理するかどうかを決める。
- 入口面が shell へ跨る以上、gate を Python 層だけへ足すと、gate の外側で書かれた artifact が
  試行台帳に残る。これは活性化権限の有無と独立に閉じるべき欠陥であり、
  certified writer 閉包の側で扱う。

**却下した選択肢:**
- Python 層に立つ入口だけへ receipt を結線し、残りを後続 wave へ送る —
  「最初の書込み前に保護した」と数えられない入口を保護済みとして数えることになる。
- 合成した後継世代 (temp commit) の正例を発火証拠として認めて実装を進める —
  `DW-G04` が要求するのは実在 artifact path か計測 ID であり、合成試験だけが
  発火証拠として台帳に残る状態を作る。
- shell wrapper へも gate を複製する — 同じ検査を 2 言語で二重管理することになり、
  片側だけが更新される事故面を新設する。閉包側で 1 か所に寄せる方が狭い。
