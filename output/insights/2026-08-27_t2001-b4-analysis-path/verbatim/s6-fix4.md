## 前提の確認

指定された 4 資料を全文確認しました。Web 検索、docs 編集、commit、所有外 8 ファイルの編集は行っていません。

親の `149 passed / 1 failed` は修正前の実走記録として扱い、今回の緑には含めていません。

## 対応

`partial`

以下を実装し、AST による依存分離を確認しました。

- selection probe: manifest 生成と先頭 n 行だけを検査
- violation probe: manifest を生成せず、full registry の違反件数だけを検査
- rank probe: ledger、manifest、artifact path を使わず、contract 型から直接作った 201 block を検査
- 呼び出し順の入れ替えには依存していません
- assertion の削除や緩和、skip、xfail、期待メッセージの変更はありません

`partial` の理由は、指定 runner が `rc=16` で停止し、修正後テストを実走できなかったためです。

## probe の反応表

以下は AST で確認した所有関係です。追加した反応 assertion 自体は未実走です。

| 変異 | selection probe | violation probe | rank probe |
|---|---|---|---|
| 選択関数を逆順にする | 反応: `first n` | 非反応 | 非反応 |
| 違反件数の導出を適格性処理後へ移す | 非反応 | 反応: `violation` | 非反応 |
| 順位規則で `missing` の位置を変える | 非反応 | 非反応 | 反応: `status rank` |

## 変更したもの

- [p3_b4_analysis_prereg_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_prereg_consumer.py)

  - rank probe を contract の `B4BlockObservation` と `B4ContractBinding` の直接構築へ変更
  - 6 勝、195 tie、`A_hat = 69/134 < A_min` でも成立することを直接検査
  - violation probe を 1 件の不適格な汚染 attempt と full registry 違反件数の検査へ限定
  - 不要になった統合 artifact fixture helper を削除

- [test_p3_b4_analysis_prereg_consumer.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py)

  - 3 変異 x 3 probe の帰属 assertion を追加
  - monkeypatch は test 内だけで変異を表現するために残し、production 注入 seam を作らない理由を docstring に記録
  - self-runner を維持

## 実走結果

実行コマンド:

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py -q -rf
```

結果:

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
child_started=false
child rc=16
```

実走 nodeid は 0 件、緑の範囲も 0 件です。

静的検査では以下を確認しました。

- 変更 2 ファイル: `AST_OK`
- 3 probe の依存先: `STATIC_PROBE_OWNERSHIP_OK`
- monkeypatch 判断の docstring: `MONKEYPATCH_SEAM_DOCSTRING_OK`
- self-runner 維持
- 結合文字 U+0300〜U+036F なし

## 波及可能性

- rank probe は adapter、ledger、manifest の変異へ反応しなくなり、contract の順位、score、`A_min` の非閾値性だけを担当します。
- violation probe は manifest 選択や順位評価を通らず、full registry の違反件数だけを担当します。
- selection probe の入力には違反行がなく、違反件数の導出順変更には反応しません。
- production API や注入経路は追加していません。
- consumer source の変更により closure member の digest は変わりますが、receipt は実 bytes から再計算されます。

## 未了と限界

- 修正後の consumer test 全体は未実走です。
- 親が確認済みだった 149 件が修正後も緑かは未確認です。
- 追加した probe 帰属 test も未実走です。
- 親による 5 test file の再実走が必要です。

## 総括

behavior probe の入力を分離し、選択関数の逆順変異が rank probe に先取りされる原因を除去しました。静的には 3 変異の帰属が成立していますが、dispatch 障害により実走確認がないため、結果は `partial` です。