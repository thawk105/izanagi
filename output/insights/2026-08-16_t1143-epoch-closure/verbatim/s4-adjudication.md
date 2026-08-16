# 段 4 裁定 + プラン v2 + 変異事前登録 ([T-1143])

親 (Claude) が段 2 プランと段 3 敵対 2 本 (lens A = sol, lens B = luna、いずれも NO-GO) を
裁定した結果。2 レンズは独立に同じ blocker (`verifier/__init__.py` の再 export shim) へ収束した。

## 1. 所見の裁定

| 所見 | 判定 | 採否 | scope |
|---|---|---|---|
| A1 弱化 → commit → fresh lock は新 E1 として受理される。閉じるのは lock 後の drift だけ | real | 採用 (名乗りの限定として) | 記録面 |
| A2 D268 の名乗りを「適用された正しさ規則」へ拡張できない | real | 採用 | 記録面 |
| A3/A4, B1 exact 13 は裁定の literal を超える。exact 12 では shim 経路が開いたまま | real | **exact 12 で実装し、shim は裁定パッケージへ返す** | 実装 = 12、shim = scope 外 |
| A5 `report.py` は import 時に判定を変えうる | real | 不採用 (実装せず) | scope 外・裁定パッケージ |
| A6 CLI (`cli.py` / `__main__.py` / `verify.py`) は別 gate | real | 不採用 | scope 外・裁定パッケージ |
| A7 `__pycache__` / monkeypatch / `sys.modules` / `PYTHONPATH` は開いたまま | real | 採用 (記録のみ) | 記録面 (D268 の制限箇条書きを継承) |
| A8 未束縛 bootstrap (`campaign_lock.py` 等) が root of trust | real | 採用 (記録のみ) | 記録面 (D268 の既存記述を継承) |
| A9 pipeline の推移依存 (calibrator/buildcache/build_admission/source_digest 等) は未束縛 | real | 採用 (記録のみ) | 記録面 |
| A10 4 path 追加が効く層と効かない層の区別が無い | real | 採用 (層別表を worklog へ) | 記録面 |
| A11, B2 oracle judge は epoch の意味を認証せず、scope は非空文字列としか検査されない | real (実測で確認: `s8b_oracle_artifacts.py:167-171`) | 不採用 (実装せず) | scope 外・裁定パッケージ |
| A12, B4 path-removal 変異の赤理由が一意にならない | real | 採用 (変異設計を差し替え) | 実装面 |
| A13, B7 親の「pin 0 件」が path 検索だけ | real | 採用 (key 側検索を実施済み。主張を限定) | 記録面 |
| B3 `artifact_admission.py` 自身が閉包の一員なので、未 commit 中は certified fixture が赤 | real | 採用 (運用制約として。テスト実走は統合 commit 後に親が行う) | 運用 |
| B5 T126 qualification の identity closure は verifier/core.py しか含まない | real | 不採用 (実装せず) | scope 外・裁定パッケージ |
| B6 domain `/v1` 据え置きで旧 8 と新 12 の E1 namespace が区別できない | real | **据え置きを維持** | 記録面 + 裁定パッケージ |
| B8 D268 と `docs/failures.md` の「8 path」記述 | 部分 real | **D268 は supersede fragment で更新。`docs/failures.md` の記述は書き換えない** | 記録面 |

### 主要裁定の理由

**(P1) exact 12 で land する。** 裁定文 #11 は
`orchestrator/verifier/{core,dsg,model,parse}.py` を exact に名指ししており、ユーザーが承認した
推奨もこの 4 file だった。exact tuple は v2 wire の受理言語そのもの (`campaign_lock.py:167-180`)
であり、批准された契約である。lens A が示したとおり、shim を入れるかは 12 / 13 / 14 / 16 と
連続する脅威モデルの選択であって、親が独断で 1 点を選ぶ性質のものではない。
**したがって 4 file を実装し、`__init__.py` / `report.py` / CLI は択一パッケージでユーザーへ返す。**
worklog には「shim 経路は閉じていない」を必ず書く。

**(P2) domain は `/v1` 据え置き。** 実 corpus の v2 lock は 0 件で、preimage に path が入るため
旧 8 と新 12 の digest は必ず異なる (`artifact_admission.py:738-747`)。上げると
`E1` prefix を固定する layer3 / S1 / S8b の golden まで変更面が広がり、裁定の範囲を超える。
旧新の namespace 曖昧性は裁定パッケージへ返す。

**(P3) excluded_scope は真を書ける文言にする。**
`orchestrator/verifier/` の Python source は exact 8 file。束縛する 4 を差し引いた
`__init__.py` / `__main__.py` / `cli.py` / `report.py` を exact に列挙する。

**(P4) 定数名・wire key は変えない。** D268 決定 2 を継承。

**`docs/failures.md` を書き換えない理由。** 当該記述は 2026-08-11 に起きた事故の記録であり、
「その時点で 8 path だった」は事実である。歴史記録の遡及改変はしない (insights の逐語と同じ扱い)。
現行契約は D268 の supersede fragment が持つ。

## 2. プラン v2 (実装子への確定仕様)

段 2 プランの表を基に、次の差分を確定する。

- **exact 12 とする。** `__init__.py` は追加しない。プランの exact 13 案は採らない。
- 追加順序は tuple 末尾へ `core.py` → `dsg.py` → `model.py` → `parse.py`。既存 8 の順序は変えない。
- `_CAMPAIGN_VERIFIER_EPOCH_DOMAIN` は変更しない。
- `CAMPAIGN_VERIFIER_EPOCH_SCOPE` の新値:
  `enforcement source closure (exact 12 path; witness gate 本体 pipeline.py と verifier 実装 core/dsg/model/parse を含む)`
- `CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE` の新値:
  `verifier package のうち orchestrator/verifier/{__init__,__main__,cli,report}.py の implementation bytes は束縛しない`
- 新規テストの parametrize は **production tuple から導かず、verifier 4 path を literal に持つ**
  (A12/B4 対応。production から path を外す変異で node が消えないようにする)。
- `test_artifact_admission.py` の scope assert は部分一致でなく **exact equality** にする。
- 固定件数依存はすべて 12 へ直す。親が実測した既知箇所:
  `test_artifact_admission.py:1059` の `== 8`、`test_s6_sort_sweep.py:619` と
  `test_s8a_trigger_sweep.py:829` の docstring。**実装子はこれで網羅と見なさず自分で全数を洗う。**
- docs は実装子が触らない。

## 3. 変異事前登録 (DW-M01)

runner 範囲 = `orchestrator/tests/test_t671_source_binding.py`,
`orchestrator/tests/test_artifact_admission.py`,
`orchestrator/tests/test_campaign_lock_codec.py`。

| ID | 変異 | 層 | 単一理由性の根拠 | 期待 |
|---|---|---|---|---|
| M1 | `campaign_lock.py` の tuple から `orchestrator/verifier/core.py` を削除 | negative | 追加 path の membership を要求する層は独立 tuple test と新規 literal parametrize test だけ。前後に同じ入力を拒否する層は無い | KILLED |
| M2 | 同 `dsg.py` を削除 | negative | 同上 | KILLED |
| M3 | 同 `model.py` を削除 | negative | 同上 | KILLED |
| M4 | 同 `parse.py` を削除 | negative | 同上 | KILLED |
| M5 | `CAMPAIGN_VERIFIER_EPOCH_SCOPE` を旧 exact 8 文字列へ戻す | negative | scope の exact equality assert 1 層のみ | KILLED |
| M6 | `CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE` を旧文字列へ戻す | negative | 同上 | KILLED |
| M7 | `artifact_admission.py` の記録 map と現在 map の比較を常に不一致にする | positive | 過剰拒否の正例。clean な closure でも certified 受理が落ちることを検出する既存正例テストが唯一の層 | KILLED |

- **期待 node は fix 後の最終 commit で完全集合を再導出する** (DW-M08)。本登録は位置と理由の
  事前固定であって node の事前固定ではない。初回走は probe と明記し erratum を残す。
- 本走は `--runner-mode dispatch`、runner argv に `--force-dispatch` を入れる。

## 4. ユーザーへ返す裁定パッケージ (実装しない real 所見)

1. **verifier package のどこまでを closure に入れるか** (A3/A4/A5/A6, B1)。
   - (a) exact 12 のまま (本 wave の結果)。`__init__.py` の 1 行差し替えで
     `core/dsg/model/parse` の bytes を変えずに gate を無効化できる経路が残る。
   - (b) exact 13 = `__init__.py` を追加。`pipeline.py:30` が実際に解決する dispatch 面を閉じる。
   - (c) exact 14 = さらに `report.py`。import 時の判定差し替えと rejection payload を閉じる。
   - (d) exact 16 = さらに `cli.py` / `__main__.py`。CLI gate も名乗りに含める
     (lens A は wrapper `orchestrator/verify.py` も要ると指摘)。
   - **費用の時計**: 裁定 #11 が根拠にした「実データに v2 lock が 0 件」は現時点でも成立している
     (実測 32 lock 全件 v1)。campaign を回して v2 lock が積まれると、以後の拡張は既存成果物を壊す。
2. **epoch の cross-version namespace** (A11, B2, B6)。`s8b_oracle_artifacts.py:167-171` は
   scope を非空文字列としか検査せず、judge は `state=E1` と `certified_eligible=true` だけで
   採用する。旧 8-path 定義の E1 を新 closure の certified 選択へ混ぜない機構が無い。
   択一: (a) domain を `/v2` へ上げる / (b) oracle 側で現行 scope の exact 一致を要求する /
   (c) 現状維持 (v2 lock 0 件なので実物は無い)。
3. **T126 qualification の identity closure** (B5)。`REQUIRED_CODE_IDENTITY_PATHS` は
   `verifier/core.py` だけを含み、`dsg/model/parse` を含まない。qualification 成果物が
   旧 correctness 実装を指し続ける。
