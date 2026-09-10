# T-2579 段4裁定・plan v2

- planと敵対相談2本は全て終了rc0、出力検査rc0。対象3file/5hunk、30関数/51node、4集合各30登録を静的照合した。
- 採用: 指定3fileの既存差分だけ回収する。各module fixture実体が1回取得し、function用と返却用のdeep copyを両方保持する。
- real・説明訂正: 現行conftestはprocess-memo以外のsuffixを除去する。同一worker集約・全体1回・timeout解消・速度改善は保証しない。briefを訂正した。
- refuted: 全worker合計1回でなければ裁定違反という解釈。D1936項43はmodule fixtureを承認した限定回収で、scheduler追加を求めていない。承認前提を覆す未見事実なし。
- real・変異計画修正: planの負例注入除去は弱い。既存production detached拒否だけを一時無効化し、正常な既存負例が受理されることを検出する変異へ再照準。
- refuted: 二段copy欠落、site偽装必須、既存正負期待の変更、現HEADへの巻戻し。独立copyと別root委譲は静的に保持する。個別copy削除の検出力は未証明、新testは足さない。
- 権限: 恒久実装は別Codex authorが指定3fileだけ書く。親は統合・docs・既存harnessによる一時変異と復元・全実測を担当する。
- 禁止署名: productionのdetached/clean/HEAD/source拒否を恒久変更しない。正例は既存R1の正当manifest受理。負例はdetached=Falseだけを持つ既存test。
- 変異事前登録: M1 templateのdetached=False（正例が拒否へ変わる）、M2 production detached拒否無効化（負例が受理へ変わる）、M3 r1登録をinventory/parent-onlyから同時削除（独立golden検査が拒否）。
- M3は片集合削除のimport errorを避けるため二集合を同時編集し、goldenは固定。期待失敗は各1node、実collection/baselineと単一理由をharnessで照合する。
- 本waveは検出力追加でなくfixture共有範囲・既存分類登録の回収。新旧test検出力差分の主張はしない。DW-M08の新テスト比較対象なし。
- 段4前にrulings-inboxを再走査、対象への追加裁定なし。DW-G01〜G05は既存限定scopeで成立。新gate・一般化・CC前提の追加なし。
- 関連走: t1259のfile単独、test_real_repo_serializationのfile単独、check_codex_agents/check_docs。固定anchor後に変異、段7/8後の最終tipへ正式受入。
