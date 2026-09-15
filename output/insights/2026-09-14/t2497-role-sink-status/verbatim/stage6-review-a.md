以下は静的判定です。テスト・変異は実行していません。「KILLED／SURVIVED」は実測結果ではありません。

参照略号：

- **T** = `orchestrator/tests/test_p3_autonomous_workload_trial.py`
- **P** = `orchestrator/campaign/p3_autonomous_workload_trial.py`
- **R** = `/home/SFC/tanab/.claude/jobs/a196dbeb/tmp/t2497/stage4-ruling.md`
- **本 node** = `test_role_sink_bytes_vary_only_at_declared_declassifications`
- **負例 node** = `test_role_sink_report_complete_rejects_partial_reports`

## 検査 1 — 登録済み変異 M1〜M5 の kill 判定

| 変異 | 静的判定 | node・落ちる行・具体的理由 |
|---|---|---|
| M1 | KILLED | 負例 node、**T:2033** の context 終了時。形Aで helper が **T:1850** の cell を返し、`DID NOT RAISE`。形Bには到達しない。 |
| M2 | KILLED | 負例 node、**T:2060** の context 終了時。形Aは fatal_error があるため期待どおり拒否。形Bは key 不在で `get(...) is None` が真になり、`DID NOT RAISE`。 |
| M3 | KILLED | 負例 node、**T:2033** の context 終了時。形Aの partial を受理して戻り、`DID NOT RAISE`。 |
| M4 | KILLED | 本 node、**T:1928**。代入行を削除すると `cell` が未定義で `NameError`。**T:1970** の iterator 消費へ伝播する。 |
| M5 | KILLED | 本 node、**T:1922 → T:1847**。正常な内容を持つ report でも status が partial なので、新 helper が `AssertionError`。負例の partial 前提は変わらない。 |

**登録された5件に、静的に SURVIVED と判定するものはありません。** 実測の kill 判定、特に M5′ の旧版 SURVIVED は要検証です。

## 検査 2 — 未登録の生存変異

**must-fix：real — R:44 の保証範囲が過大。**

「2形あれば原因によらず complete 以外を拒否する性質が機械で守られる」は成立しません。**T:1847** の述語だけを次へ置換し、既存メッセージ・return を維持できます。

```python
assert report["cells"][0]["stop_reason"] not in {
    "supervisor-error", "role-invalid"
}, (
    f"wire={wire}: expected complete, got status={report['status']}"
)
```

形A・Bは同じメッセージで拒否され、本 node の `fixed-generation-budget` は通ります。したがって、baseline が正常なら**両 node は緑のまま、status 検査が消えます**。

壊れる具体シナリオは M5 と同じ「内容は正常、status のみ partial」の report です。この弱化 helper は全32件を受理します。

**成果物への影響：本 node の受理集合に `status="partial"` の report が戻るため、裁定の保証記述と変異評価は、この未検出の弱化を反映する必要があります。** production 変更や新しい framework の提案ではありません。

**nit／既知限界の具体化：real — T:1922。**

呼出し行を削除せず、次の1行へ置換しても生存します。

```python
cell = report["cells"][0]
```

既存の2利用箇所を変更する必要はありません。負例は helper を直接呼ぶため通り、本 node は status を検査しなくなります。

**成果物への影響：本 node の受理集合が status 未検査の状態へ戻ります。** R:29 の「helper ごと消し2か所を元に戻す」より小さい変異ですが、D387 の受容済み限界に属するため、追加防壁を must-fix にはしません。

## 検査 3 — 単一理由性

指定の2 node・登録された単独変異に限れば、静的に次のとおりです。

- **M1／M3：** 形Aの前提 assert は変更されず成立。cell 数を **T:2031** で確認しているため return の添字アクセスも成功し、唯一の赤理由は期待例外の不発です。
- **M2：** 形Aの拒否は捕捉されます。形Bでは **T:2057** が fatal_error 不在を固定し、唯一の赤理由は **T:2060** の期待例外不発です。
- **M4：** **T:1925** の payload 件数検査が先行しますが、呼出し削除は producer・payload を変更しません。正常 baseline ではそこを通り、**T:1928** の未定義参照だけで落ちます。ただし測っているのは**変数依存**で、status 判定の意味的な接続ではありません。
- **M5：** helper が payload・世代・横断 assert より先に実行されます。status 固定は producer の cells や payload を変えず、**T:1847** が直接の拒否箇所です。

**要検証：R:133–135。** 実走の失敗箇所が上記と一致して初めて単一理由性を確定できます。別 node を含む全 suite について単一理由とは主張できません。

## 検査 4 — pytest.raises の射程

**real、must-fix なし — T:2033–2036／2060–2063。**

捕捉範囲はそれぞれ helper 呼出し1行だけです。`run_trial` と成立条件 assert は外にあります。

`match` はアンカーなしの部分一致ですが、wire は固定の `00000` で、パターンに意味を変える正規表現メタ文字はありません。現行 helper 内で別の AssertionError が偶然通る具体経路は見つかりません。

ただし検査2のように、**異なる述語が同じメッセージで拒否する変異は通ります**。文言一致は拒否理由の同一性を保証しません。アンカー追加だけでは解消しません。

## 検査 5 — 恒真 assert

**nit：real — T:2028／2056。**

現行 producer は **P:3762** で、`supervisor-error` または `role-invalid` を持つ report を必ず partial にします。したがって、各形の stop_reason 前提が成立する範囲では、この2つの status assert は必ず真です。

ただし、これは**負例の前提固定**です。producer が complete を誤出力する変化では失敗し得るため、無条件の恒真式ではありません。害は小さく、削除理由にはなりません。

fatal_error の有無・型、cell 数、stop_reason の確認も指定経路の前提固定です。一般の report について恒真ではなく、helper の発火保証として数えなければ問題ありません。

## 総括

**must-fix は段4の保証範囲の訂正です。** M1〜M5 は静的には殺せますが、負例2形の stop_reason だけを見る弱化は生存し、status 検査を消せます。呼出し接続も1行置換で迂回できます。

現行実装は complete を直接検査しています。しかし、この変異集合から「原因によらない拒否まで機械的に守られた」として閉じることはできません。実走結果は未確認です。