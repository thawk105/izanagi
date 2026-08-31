# [T-1814] 完了証明層を C10 で開いた — 実測の記録

- 日付: 2026-09-01
- branch: `worktree-dev-wave-t1814-c10-satisfaction`
- 一次資料: D1026 (裁定)、D438 (終端を閉じたまま残した理由)、D959 (層としての閉塞)、D458 (版と世代)
- 実測はすべて親が repo 外の probe か `tools/run_tests.py` で実走した。子の申告は再掲しない。

## 1. 着手前 — 判定器は 9 条件で「意図的な終端」だけで止まっていた

現行 HEAD に対する `PredicateRegistry().evaluate_all` の結果:

| 条件 | status | reason_code |
|---|---|---|
| C03 | UNSATISFIED | manifest-registry-proof-undefined |
| C05 | EVIDENCE_UNDEFINED | schedule-schema-absent |
| C08 | EVIDENCE_UNDEFINED | prereg-binding-proof-undefined |
| C01・C02・C04・C06・C07・C09・C10・C11・C12 | EVIDENCE_UNDEFINED | completion-proof-not-machine-checkable |

機械検査対象 10 件のうち 9 件は実質検査を通過し、fail-closed の終端だけで止まっていた。
**先例の選定は「どれなら通るか」ではなく「どれが最小閉包か」の問題だった。**

## 2. 決定的な実測 — 強化前の C10 は中身の空な実装を区別できない

合成 repo 4 本に評価器を実走した結果、**4 つとも同じ終端**へ到達した。

| fixture | 強化前 | 強化後 |
|---|---|---|
| 正直な形 (ただし reader は `pass`) | EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable | UNSATISFIED / cross-binding-verifier-incomplete |
| reader call を `if False:` 枝へ | 同上 | UNSATISFIED / cross-binding-verifier-incomplete |
| 受入側が `except Exception: pass` | 同上 | UNSATISFIED / cross-binding-verifier-incomplete |
| 受入側の call を `if False:` 枝へ | 同上 | UNSATISFIED / cross-binding-verifier-incomplete |

原因は `_called_names` が `ast.walk` で関数全体を走査し、呼び出しを**名前一致だけ**で数えること。
到達可能性も戻り値の使用も例外の伝播も見ない。
**終端を素朴に充足へ差し替えると、中身の無い 3 実装が充足と認定される。**

## 3. プランの中心提案を実測で覆した — データフロー追跡は本番を偽赤にする

段 2 プランは「reader 内で読取結果が digest 照合へ渡り、不一致が raise へ到達する」ことまで
静的に追跡する案だった。本番の受入経路に当てると:

```
production call in assert_trial_registry_acceptance() at trial_registry.py:6086
  live=True  reachable_use=False
```

本番は `cross_binding_receipts[trial_id] = verify_s8c_cross_binding(...)` の subscript 代入で、
既存 helper は subscript target を追わない。**追跡を課すと正しい実装が赤になる。**
D96 が同種の静的検査を「無害な refactor で偽赤になる」として却下した形そのものである。

代替として置いた必達の関門が **「実 repository で C10 が充足を返すこと」** である。
実 repo が落ちれば偽赤、合成の空実装が通れば恒真 — 1 つの関門で両方を塞ぐ。

## 4. 塞げないもの — 静的解析の原理的な限界

段 3 レンズ A が、強化後の検査でも空の実装を構成できることを実証した。

```python
globals()["verify_s8c_cross_binding"] = lambda **_: {"receipt_sha256": "0" * 64}
```

親も独立に確認した。`_functions()` はこの代入を見ず、`verify_s8c_cross_binding` を
無傷の定義として返す。**静的判定器に実行時の再束縛は原理的に見えない。**

したがって条件本文へ限界 6 項を列挙した — 実行時の再束縛、定数でない述語による意味的に偽の guard、
呼び出し結果の実効寄与、`getattr` / 高階関数経由の dispatch、宣言 field の reader 引数への実束縛、
reader が実際に bytes を読み digest を照合すること。条件 12 が同じ様式で自らの限界を明記した
うえで機械検査対象になっている先例に倣った。

## 5. 宣言 field の束縛は検査していない — 3 変異で切り分けた

| 変異 | 結果 |
|---|---|
| A: field 名を tuple からも束縛箇所からも除去 | UNSATISFIED |
| B: field 名を tuple からだけ除去 (束縛は無傷、文字列は別箇所に残る) | SATISFIED |
| C: 束縛だけを壊す (tuple は無傷) | SATISFIED |

検査が要求するのは「12 個の field 名が live な位置に文字列として現れること」までである。
これは裁定どおりの挙動 (データフロー追跡は不採用) だが、正本の限界一覧に無かったため追記した。

## 6. `contextlib.suppress` は塞いだ — 主張を弱めるより検査を合わせる

正本の条件 10 が「その call が catch-and-continue で握り潰されない」と明示的に主張している以上、
限界として宣言するのではなく塞ぐ方が正しいと裁定した。

| fixture | 結果 |
|---|---|
| 握り潰し無し | SATISFIED |
| `contextlib.suppress(...)` | UNSATISFIED / cross-binding-acceptance-unreachable |
| `from contextlib import suppress` | 同上 |
| `import suppress as quiet` | 同上 |
| 例外を握り潰さない普通の `with` | **SATISFIED (過剰拒否なし)** |

## 7. 変異 matrix — 4/4 KILLED

| id | 変異 | 落ちたテスト |
|---|---|---|
| B-057-M1 | 充足可能集合を空に戻す | 11 |
| B-057-M2 | 充足の終端を非充足へ倒す | 11 |
| B-057-M3 | 握り潰し検査を無効化 | 6 (suppress の 4 綴りと N7 / N8 だけ) |
| B-057-M4 | 判定器版を v6 へ戻す | 3 |

M3 が狙った検査のテストだけを落とすことが、その検査が実際に効いている直接の証拠である。

本走は 3 回要した。1 回目は期待 node に xdist group 接尾辞を含めて起動前中止、2 回目は接尾辞を
外して比較器と形式が合わず 2 件が MISMATCH (生存は 0、差分は同じ 2 テストの接尾辞のみ)、
3 回目で group を持つ 3 テストを `--deselect` して 4/4 一致。F71 への再発として記録した。

## 8. 受理集合への影響

発効は 12 条件すべての充足を要求するため、**8c 事前登録は本 wave の後も未発効**である。
測定認可・certified 選択・proof chain・campaign 起動可否は 1 件も変わらない。
変わるのは条件レベルの受理集合 1 bit と、`ActivationReport` / gate report / 報告 digest /
enforcement source closure の epoch である。
