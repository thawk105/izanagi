## 所見

所見 1: E1 epoch 識別子を改変する変異が生き残る

重大度: must-fix

どこで壊れるか / 何が証明されていないか: 中央 gate の戻り値を、同じ `state="E1"`・`reason_code="recorded-closure"` だが別の有効な 64 桁 SHA を持つ `CampaignVerifierEpoch` に差し替えても、正例 4 assert はすべて通る。負例は E0 で先に終了し、他の S-1 node は autouse fixture が実 callee を差し替えるため検出しない。

実物の根拠: `orchestrator/campaign/s1_report.py:310-312`、`orchestrator/tests/test_s1_report.py:36-43`、`:593-598`。正例は `campaign_verifier_epoch` と scope を検査していない。

成果物への影響: `hard_gates.certified.campaign_verifier_epochs` に誤った epoch identity が掲載され、certified report の proof chain が別の closure を指しうる (`orchestrator/campaign/s1_report.py:117-124`, `:970-973`)。

所見 2: rejection reason の message 変更は変更前後とも生き残る

重大度: nit

どこで壊れるか / 何が証明されていないか: `campaign_verifier_epoch_rejected` の `message` を任意に変更しても、負例は `code` と epoch projection しか比較しない。`_generate` の JSON 比較は生成物と同じ生成物の再読なので検出にならない。

実物の根拠: message の生成は `orchestrator/campaign/s1_report.py:433-438`。assert は `orchestrator/tests/test_s1_report.py:536-549`、自己整合比較は `:229-230`。

成果物への影響: certified 選択と台帳は変わらないが、JSON・Markdown report の拒否説明文は無検出で変わる。

所見 3: M1・M2 の凍結された赤面説明が実際の最初の赤面と一致しない

重大度: nit

どこで壊れるか / 何が証明されていないか: M1 は単純な「reason 不在」ではなく、禁止された WAL 読取の assert が内部で `schedule_ledger_invalid` に変換され、その後の code assert が赤になる。M2 は 4 assert のどれかではなく、callee 行で未捕捉例外になる。

実物の根拠: M1 は `orchestrator/tests/test_s1_report.py:524-527`、`orchestrator/campaign/s1_report.py:556-560`、最終赤は `orchestrator/tests/test_s1_report.py:536`。M2 は `orchestrator/campaign/artifact_admission.py:967-974` から `orchestrator/tests/test_s1_report.py:593` へ例外が出る。

成果物への影響: production 成果物への直接影響はなく、変異台帳の赤理由の正確性だけが損なわれる。

所見 4: 新規 node は duration ledger に存在しない

重大度: nit

どこで壊れるか / 何が証明されていないか: 新規 node は収集集合へ加わるが、`acceptance_duration_ledger.json` に対応する key がない。G5 coverage は一件低下する。ただし 90% 閾値なので、この一件だけで必ず赤になるとは静的にはいえない。

実物の根拠: node は `orchestrator/tests/test_s1_report.py:553`。coverage 計算は `orchestrator/tests/test_acceptance_schedule_order.py:704-713`。ledger は 19,519 key (`orchestrator/tests/acceptance_duration_ledger.json:19523`) だが新規 nodeid は不在。

成果物への影響: certified 選択・report は不変だが、受入 duration ledger では当該 node が unknown-cost 扱いになる (`orchestrator/tests/conftest.py:1523-1543`, `:1583-1611`)。

## 事前登録 4 変異の帰属判定 (1 件ずつ、殺せる / 殺せない + 赤になる assert)

- M1: 殺せる。

  `orchestrator/campaign/s1_report.py:308-309` を削除すると、v1 lock は `_recorded_campaign_verifier_epoch` から E0 として返り (`orchestrator/campaign/artifact_admission.py:909-918`)、`HISTORICAL_RAW` も拒否せず返す (`:961-965`)。その結果 WAL 読取へ到達し、spy の `assert layout.root != rejected_layout.root` (`orchestrator/tests/test_s1_report.py:524-526`) が発火する。ただしこれは `_assess_campaign` の広い catch で `schedule_ledger_invalid` へ変換されるため、pytest 上で最初に赤になる assert は `reason["code"] == "campaign_verifier_epoch_rejected"` (`:536`)。

  単一理由性: E0 を拒否する前段はなく、後段の historical gate も拒否しない。失敗原因は局所 raise の欠落一つ。落ちる node もこの負例一つ。

- M2: 殺せる。ただし赤になる assert はない。

  purpose を `CERTIFIED_ACCEPTANCE` に戻すと、正しい v2 lock の記録 binding 検証後、中央 gate が patched `capture_contract_loader_binding` を呼ぶ (`orchestrator/campaign/artifact_admission.py:967-974`)。事前 seam 確認ですでに count は 1 なので、二度目の呼出しで `CampaignVerifierEpochRejected` が `orchestrator/tests/test_s1_report.py:593` から未捕捉で出て node が error になる。`:595-598` の assert には到達しない。

  単一理由性: helper は記録 HEAD blob から整合する v2 binding を作る (`orchestrator/tests/campaign_lock_test_support.py:10-20`, `:23-48`)。拒否理由は現行閉包 seam の失敗一つで、落ちる node も正例一つ。

- M3: 殺せる。

  中央 gate 呼出しを削って `return recorded.diagnostic` にすると spy は呼ばれない。最初に赤になるのは `assert observed_purposes == [HISTORICAL_RAW]` (`orchestrator/tests/test_s1_report.py:595`)。`capture_call_count == 1`、state、reason はそのまま通る。

  単一理由性: v2 decode・記録 binding 検証は通り、中央呼出しの欠落だけが赤理由。落ちる node は正例一つ。

- M4: 通常の別例外型への置換は殺せる。

  `ArtifactAdmissionError` 系なら validation failure (`orchestrator/campaign/s1_report.py:449-453`)、それ以外の通常の `Exception` なら外側で schedule failure (`:556-560`) になり、どちらも負例の code assert (`orchestrator/tests/test_s1_report.py:536`) が赤になる。

  単一理由性: 同じ E0 を独立に拒否する別 gate はなく、例外分類の相違一つ。落ちる node は負例一つ。なお `CampaignVerifierEpochRejected` の subclass は同じ catch と projection を通るため、exact class の差までは検出しないが、成果物上の拒否意味は変わらない。

## 生き残る変異 (検出力の穴)

重大な生存変異は E1 epoch identity の改変である。例えば `orchestrator/campaign/s1_report.py:310-312` で中央 gate を正しく一回呼んだ後、その戻り値を次の条件を満たす別インスタンスへ置換する変異が生き残る。

- `campaign_verifier_epoch="E1:" + "0" * 64`
- `state="E1"`
- `reason_code="recorded-closure"`

purpose spy と closure call count は変わらず、正例の state・reason も一致する。E0 負例は局所 raise でこの return に到達しない。他の S-1 node は `orchestrator/tests/test_s1_report.py:36-43` の fixture により実 callee を通らない。

軽微な生存変異として、`orchestrator/campaign/s1_report.py:435` の reason `message` の変更や、reason envelope への追加 field がある。これは変更前から生きており、段 4 で exact envelope 比較を不採用にした結果と整合するが、検出力の穴自体は実在する。

## 負例の検出力の変更前後比較

`author.patch:43-49` で変わったのは、合成した `CampaignVerifierEpochRejected(e0)` を投げる箇所を保存済み実 callee 呼出しへ置換した一点である。catch、projection、assert は同じままなので、下流の検出力は低下していない。

- `_rejected_epoch_projection` の既存 5 field:

  - `campaign_verifier_epoch`、`state`、`reason_code` の値変更は `orchestrator/tests/test_s1_report.py:537-539` が変更前後とも殺す。
  - `identity_scope`、`excluded_scope` の変更は exact dict (`:543-549`) が変更前後とも殺す。
  - field の追加・欠落も同 exact dict が殺す。
  - 実装位置は `orchestrator/campaign/s1_report.py:127-134`。

- reason envelope:

  - `code` の変更は `orchestrator/tests/test_s1_report.py:536` が変更前後とも殺す。
  - `message` の変更は変更前後とも誰も殺さない。
  - envelope 全体への追加 field も exact 比較がないため生き残る。

したがって「以前は殺せたが、実 callee 化後に殺せなくなった」対象は確認できない。逆に、以前は完全に bypass されていた decode、v1 E0 導出、局所 E0 raise の変異を負例が新たに通るため、上流側の検出力は増えている。

## 正例 4 assert の分類

- `observed_purposes == [HISTORICAL_RAW]` (`orchestrator/tests/test_s1_report.py:595`): 単なる回帰 pin。purpose の値と中央 gate 一回呼出しを固定するが、別経路の可用性 gate がないこと単独では証明しない。
- `capture_call_count == 1` (`:596`): 可用性 gate が外れたことの存在証明。`:585-586` の明示的な失敗 seam 呼出しで count を 1 にした後、実 S-1 callee が同 gate を再参照しないことを示す。
- `epoch.state == "E1"` (`:597`): 戻り値の回帰 pin。
- `epoch.reason_code == "recorded-closure"` (`:598`): 戻り値の回帰 pin。

結論: 存在証明は一本実在し、`capture_call_count == 1` である。ただし証明対象は既知の `capture_contract_loader_binding` 経路であり、epoch identity の正確性までは証明しない。

## 受入全走への波及判定

- `s1_report.py` の変更関数の production caller は `_assess_campaign` (`orchestrator/campaign/s1_report.py:411`, `:429`)。test 側で同 module を直接 import する consumer は `test_s1_report.py:17` だけだった。
- `campaign_lock_test_support.py` は変更されていない。新規 node が既存の stateless helper を追加利用するだけで、列挙された他 consumer の挙動は変わらない (`orchestrator/tests/campaign_lock_test_support.py:10-48`)。
- 中央 gate を monkeypatch する他 test は `test_backoff_requested_us.py:68-78`。その node 内で別 consumer を完全に stub 化しており、S-1 を呼ばない。monkeypatch は node 終了時に復元される。
- `test_t671_source_binding.py:688-704` は中央 gate 内の `capture_contract_loader_binding` call site 数を AST 検査する。変更先は `s1_report.py` の purpose だけなので期待集合は変わらない。
- `test_ccbench_spawn_sites.py` は production Python 全体を AST parse する (`:324-335`) が、新しい process call はない。exact inventory assert は `:1927-1934`。親実測の 18 passed と静的参照が一致する。
- exact suite node 集合を固定する `test_t1574_changed_suite_ledger_node_delta_is_exact` の対象一覧 (`orchestrator/tests/test_update_acceptance_duration_ledger.py:364-389`) に `test_s1_report.py` はない。
- G5 coverage meta-test は新規 node を収集するが ledger key はないため、coverage 分子が一件不足する (`orchestrator/tests/test_acceptance_schedule_order.py:704-713`)。閾値は 90% なので、この差分だけによる確定赤とは判定できない。

結論: 参照関係から確定的に落ちる外部 test は確認できない。全走固有の波及候補は duration-ledger coverage の一件低下だけである。

## scope 逸脱の判定

scope 逸脱は確認できない。

- diff は `orchestrator/campaign/s1_report.py` と `orchestrator/tests/test_s1_report.py` の二ファイルだけ。
- reason envelope 全体の exact dict 比較は追加されていない。
- scope 文字列 literal は追加されておらず、既存負例は production の `e0.identity_scope` と `e0.excluded_scope` を使う (`orchestrator/tests/test_s1_report.py:543-549`)。
- 新しい purpose、公開 API、一般化 wrapper、検査台帳はない。
- 追加された局所 E0 gate と historical purpose は段 4 の採用仕様どおり。
- duration ledger も編集されていない。

## 未確認事項

- 指示どおり mutation 実走と pytest 再実走はしていない。赤面は例外伝播と assert 順序からの静的判定。
- G5 の現在の厳密な coverage 比率は full collection を行っていないため未確認。新規 nodeid の ledger 不在だけを確認した。
- M4 の「別例外」に subclass を含めて exact type 差まで要求するかは凍結文から一意ではない。通常の別系統例外は殺せるが、同基底 class の subclass は区別しない。

## 総括

事前登録 M1〜M4 は、意味のある通常の変異としてはいずれも単一 node で殺せる。  
ただし M1 は code assert、M2 は assert 到達前の例外が実際の最初の赤面で、凍結説明とずれがある。  
変更前からの負例検出力低下はなく、実 callee 化により上流検出力は増えた。  
最大の穴は、E1 epoch identity を別の有効な SHA に差し替えても全テストが通り、certified report の proof chain を壊せる点である。