---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1795-attempt-evidence
seq: 1
title: [T-1795] D965 に従い attempt 対応の永続証拠を二重条件で成立させた (code + tests + insight、branch worktree-dev-wave-t1795-attempt-evidence、変異 14/14 KILLED、束ね経路の実機試走で証拠を実測)
---

## 本文

- **D952 が「束ね経路では成立しない」と書いた attempt 対応の永続証拠を、実機で成立させた。**
  束ね経路 (`--task mutation`) を計算ノードへ 1 回投入し、collection + baseline + 変異 1 件を
  完走させて sidecar を得た。sidecar は `izanagi-dev-wave-mutation-attempts-local/v1` を名乗り、
  root の `local_authorization` に実 job の値 (bnode084、`0:963533.nqsv`、submission dir、
  request SHA-256) を持つ。設計は {{D:local-attempt-marker-admission}}。
- **記録から外側 job へ機械的に到達できることを実物で確かめた。** sidecar の `submission_dir` から
  `request.json` と `compute-visible.json` を読み、request SHA・PBS job ID・hostname が
  記録と一致し、外側 request の `task` が `mutation` であり、受領証の request_id が
  記録の job ID に対応することを確認した。**これが「attempt 対応」の実体である。**
- **敵対検査 2 本と親の実測が、独立に同じ穴へ到達した。** 計算ノード判定の変異が後段の
  hostname 照合に隠れて帰属しない件で、段 6 レビュー B と親が別々に到達した。負例の
  hostname を 3 か所すべて非 compute の同一値へ揃えて再照準し、本走で当該変異が
  ちょうど 1 件のテストで検出されることを確認した。**再照準しなければ「診断文字列だけの赤」を
  kill と誤記録していた。**
- **裁定になかった防御を 2 つ削った。** pytest 子への marker 非伝播と、証拠 file の読取前後
  fstat 比較である。どちらも射程内の攻撃経路を名指しできず、無効化しても落ちるテストが無かった。
  ユーザーの「仮想リスク向けの gate・検査の追加は scope 外」に従った。symlink 非追跡と
  通常 file 判定は既存作法なので残した。
- **テストが基盤の遮断口を迂回していた。** 新 leaf が自前で socket を import して hostname を
  読んでいたため、機械の素性を無効化する既存の autouse fixture が効かず、実ノード名と比較して
  6 件が赤になった。素性の取得を唯一の正本へ寄せて解消し、重複していた helper も消えた。
  **実装の論理は正しく、素性の取得口だけが違っていた。**
- **同じ焦点走がログインノードと計算ノードで別の結果を出した。** 信号処理系 5 件は
  ログインノードでは wrapper 子が即中断して必ず落ち、計算ノードでは通る。main 単独の
  probe worktree でも同じ 5 件が同じ形で落ちたので非帰属と判定した。
- **変異本走は共有木の事後検査で 1 度落ちた。** 走行中に別 wave の land で main が進んだためで、
  自分の走行が原因ではない。観測 root には共有 main checkout が入るので、
  **独立 clone を source にして取り直し**、rc=0 で成立させた。1 回目の結果も消さず残している。
- 起動条件で 3 度止まった (変異の category が閉集合外、runner entrypoint を絶対 path で指定、
  試走 spec の category)。**いずれも道具が起動前に fail-closed で止めたもので、変異は 1 件も
  走っていない。** 束ね経路が 3 回目で通るのは worklog 977 と同型である。
- 本 session では待ち手と Monitor の完了報告が繰り返し先行し、1 度は報告時刻が実時刻より
  15 分先だった。完了判定は完了マーカーの非空・期待成果物の実在・process の生死の 3 点で行った。
- **受入全走は本 wave と無関係な赤で 1 度止まった。** `test_codex_reasoning_ab.py` の 26 node
  (5 failed + 21 error) が落ちたが、同 file は 1 byte も変更していない。現行 main 単独の
  probe worktree で同じ内訳が再現したので非帰属である。原因は repo 外へ pin した過去 session の
  消失で、記録は F20 の再発として残した (揮発領域の唯一コピーという同型)。**この赤は D1144 に従い停止理由にしない。**
  修正は編集面の衝突を避けるため別の単独 wave へ一本化し、本 wave は同 file を触らない。
  その修正が main へ着地した後に main を取り込んで受入を投げ直した。**attempt 2 は
  19083 passed / 92 skipped / 0 failed で rc=0。** 沈黙した件数も本 wave の 2 実測で閉じた
  (修正前の main 単独で当該 file は collected 626、修正後は collected 629。赤 26 件は
  25 件が skip へ落ち 1 件は緑に戻った)。
- **受入投入の順序を 1 度誤った。** attempt 2 の後に台帳の数の訂正を commit したため、
  取り込み対象の tip が受入時と食い違った。land は `landing_tip != tested_tip` を
  forward main merge に限るので、記録の編集は受入より前に済ませておく必要がある。
  訂正を捨てずに受入を取り直した。
- **親は当初この赤の処置を「検出力は失われない」と見立てたが、独立相談が file:line で反証した。**
  production の reject 述語は弱まらないが、実 corpus・独立 golden 二経路・実 prompt の置換数・
  完全 replay の結合被覆には代替が無く、登録済み mutation killer も止まる。
  **失われる検出力は実在する。** 見立てを訂正して記録した。

## 次の一手差分

### 完了

- [T-1795] D965 の設計を実装し、束ね経路の実機試走で attempt 対応の永続証拠を実測した。
  変異 14/14 KILLED、焦点走 491 passed。scope 外とした 4 件は本文と {{D:local-attempt-marker-admission}} に明記した。
  remaining: none
  base: d474c3764359b46178517b6c3dc56be32b36ab3e792e3f720062046de004118d
