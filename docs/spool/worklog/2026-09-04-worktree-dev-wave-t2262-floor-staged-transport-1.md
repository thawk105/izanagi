---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: worktree-dev-wave-t2262-floor-staged-transport
seq: 1
title: [T-2262] 床値の staged transport を driver 内部の既定へ移した — 親 brief の誤りを 2 件自分で見つけて訂正し、official の関門が 2 本あることが分かった (コード + テスト + insight、branch worktree-dev-wave-t2262-floor-staged-transport、変異 6/6 KILLED)
---

## 本文

- D1562 の解消案 1 を実装した。設計判断は {{D:floor-payload-authority-is-the-verified-binding}}、
  部分 claim の扱いは {{D:floor-claim-basis-change-needs-new-run-id-not-a-migration}}。
  逐語・変異台帳は `output/insights/2026-09-04_t2262-floor-staged-transport/`。

- **親 brief の誤りを 2 件、親自身が段 2 投入後に見つけて訂正した。**
  1 件目は「既存の環境変数から payload の所在を導けない」。実際は投入 nonce が PBS 経由で
  job 環境へ入り、job 本体が 32 桁 hex を必須検証し、driver が import する module が既に読んでいる。
  誤った前提のまま起草させても採用できないため、稼働中の起草子を停止して保全し
  (`ABORTED-s2-plan-attempt1.md`)、brief に erratum を足して投げ直した。
  2 件目は「official の起動を止めているのは staged transport だけ」。実際は §8 の承認束縛方式が
  未裁定であることを理由とする無条件拒否が CLI と core の二重で存在する。
  段 3 の 2 レンズと段 6 のレビュー 2 本がいずれも独立に追認した。
  **本 wave 完了後も床値 official は起動できない。外れたのは 2 本のうち transport 側 1 本である。**

- 段 3 のレンズ A が、親の provisional 裁定 (生の環境変数を authority にする形) を反証した。
  core が検証する submit receipt は予約束縛の nonce で選ばれるため、生の環境変数を使うと
  「payload を選ぶ nonce」と「receipt を検証した nonce」が切り離される。親がコードで裏を取り、
  検証済み束縛から導く形へ裁定を変えた。この指摘が無ければ、literal を変えずに意味だけ緩む
  実装になっていた。

- 段 3 のレンズ B が、親の「凍結 bytes pin は不在」という閉包結論を反証した。歴史的な投入 receipt が
  job script の bytes を記録している。親が実測して決着させた: 現 main の同 script の sha256 は
  receipt の記録値と**既に不一致**で main は緑であり、現 bytes を照合する生きた検査は存在しない。
  更新対象の凍結 pin は不在という結論自体は保つが、「pin は一切ない」という言い方は誤りだった。
  記録は当時の事実であり書き換えない (規律 7)。

- **稼働中の別 wave との編集面衝突を、方針を変えて回避した。** 段 6 のレビュー B が
  「driver 内で複製を子 process として起こすと審査済み process 起動点の台帳を変える」と指摘し、
  親が実測すると同台帳を稼働 wave が編集中で、local main 側でも別 wave が変更していた。
  複製を in-process に変えて台帳に触れずに済ませた。

- **段 6 のレビュー A が、設計の要を守るはずのテストが効いていないことを見つけた。** 導出した値を
  分類器へ渡す前に同名の変数へ再代入する回帰を入れても緑のままだった。fix でこの回帰を
  構造で拒否する形にし、変異でも単独 node で kill されることを確認した。
  ただしこの検査は同名の再代入だけを見る。別名を経由する回帰は射程外であり、限界として記録する。

- 変異は 6 件を事前登録し、**baseline 緑・6/6 KILLED・期待 node と完全一致**で通した。
  事前登録した 7 件目は取り下げた。事前不在検査と排他作成の両方が同じ入力を拒否するため
  単一理由にできない。実装子と段 6 のレビューが独立に同じ結論を出した。冗長 gate として実装には残す。

- 変異の観測で親のミスが 2 件あった。1 件目は置換後の文字列に一意化用の文脈行を残さず構文を壊し、
  テスト file 全体が収集エラーになって失敗 node を抽出できず fail-closed で停止した。
  harness は作業ツリーを正しく復元した。2 件目は「束縛が無いとき拒否する」変異を、単に落ちるだけの
  弱い形で書いていた。対象テストは正しい環境変数と payload を用意したうえで staging が起きないことまで
  見る設計なので、環境変数へフォールバックする忠実な形へ差し替え、単独 probe で狙った 1 node だけが
  赤になることを確認してから本走へ入れた。

- **焦点走で出た赤 5 件は非帰属と判定した。** いずれも本 wave の編集面外の checkpoint 証跡 index 機構で、
  単独再走では 7 passed (rc=0) と再現しなかった。同じ走行の runner が pytest 完走後に 23 時間ハングして
  おり ({{F:runner-hangs-after-pytest-completes}})、実行環境側の要因と見る。
  親はこのハングを完了待ちと誤認し、待たずに次の走行を重ねて同一 worktree からの並行 dispatch を
  起こした。`DW-O26` の直列化規律に違反しており、孤児 hold の撤去で復旧した。

## 次の一手差分

### 完了

- [T-2262] staged transport を driver 内部の production 既定へ移した。導出は検証済み予約束縛から行い、
  18 名集合と判定式は literal 無変更のまま意味を保った。変異 6/6 KILLED。
  official の起動には §8 の関門が別に残るが、それは本項の scope 外であり新規項目へ分けた。
  remaining: none
  base: 584b15777c386a0088696f7a2cad35928eb2b9d8ce010f66d457d46a19218fb1

### 新規

- {{T:floor-official-section8-permit-gate}} **P1・新規・裁定待ち**:
  床値 official は §8 の承認束縛方式が未裁定であることを理由に、CLI と core の二重で無条件拒否される。
  正規 job script も pilot 固定である。transport 側の関門は解けたので、**残るのはこの 1 本だけ**である。
  D1396 は承認束縛の実装を明示的に見送っており、解除は裁定に属する。
  承認束縛の方式を決めるか、決めないなら official が起動できないことを正本へ明記するかを裁定へ返す。
  **本項が解けるまで床値の正式走行は起動できない。**
