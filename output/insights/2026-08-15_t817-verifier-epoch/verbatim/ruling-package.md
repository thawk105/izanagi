# 裁定パッケージ — [T-817] 実装 wave で出た scope 外の real 所見

wave = `dev-wave-t817-epoch` / branch `worktree-dev-wave-t817-epoch`
一次資料 = 同 directory の `brief.md` / `s2-plan.md` / `s3-lens-a.md` / `s3-lens-b.md` /
`s4-adjudication.md` / `s5-unit*.md` / `s6-review-*.md`

---

## Q1 (主問): epoch の束縛範囲を verifier 実装まで広げるか

### 実測 (親が独立に確認)

`campaign_verifier_epoch` は v2 lock の authority
(`campaign_lock.py:19-38` の `contract_loader_blob_sha256s`) に束縛した。この authority が
pin しているのは **exact 8 path** である。

```
env_contract.py / env_contract_activation.py / execution_guard.py / loop.py /
pipeline.py / wal.py / ident.py / artifact_admission.py
```

**この 8 path に、正しさ判定の実体である `orchestrator/verifier/` が入っていない。**
`pipeline.py:29` が `from ..verifier import result_to_dict, verify_trace_dir` で呼んでおり、
判定本体は `orchestrator/verifier/{core,dsg,model,parse}.py` にある。

### 何が起きうるか

E1 の lock を作った後で `orchestrator/verifier/model.py` だけを書き換え、
`VerifyResult.certified` を常に真にすることができる。epoch は 8 path しか見ないので**変わらない**。
その結果、anomaly を含む run が COMMIT され、同じ `campaign_verifier_epoch` の certified 集合が
拡大する。replay / S1 / Layer3 / S8b の選択値へ未検証 variant が入る。

これは段 3 レンズ A が blocker として出し、親が実コードで確認した。

### 本 wave で行ったこと (scope 内)

**名乗りを過大にしない。** epoch の docstring と構造化診断に、束縛するのは
「enforcement source closure (exact 8 path、witness gate 本体 `pipeline.py` を含む)」であり、
`orchestrator/verifier/*` の実装 bytes は束縛しないことを明記した。
E0 の意味も「この closure の下で検証されていない記録」に限定して記述している。

### 選択肢

| 選択肢 | 内容 | コスト / 帰結 |
|---|---|---|
| **(a)** | `CONTRACT_LOADER_RELATIVE_PATHS` に `orchestrator/verifier/{core,dsg,model,parse}.py` を加え、epoch が実際に verifier 実装を束縛するようにする | **実 corpus に v2 lock は 0 件なので、壊れる既存成果物は無い。** 効くのは将来 run だけ。`campaign_lock.py` の exact path tuple と、それを使うテスト群の更新が要る。authority の**契約自体の変更**なので、裁定 Q3 の「既存 authority へ束縛する」を超える |
| **(b)** | 現状維持 (名乗りの限定だけで終える) | 追加コストゼロ。ただし「verifier epoch」という名前が verifier を束縛しない状態が残る |
| **(c)** | 名前を束縛範囲に合わせて改める (例: `campaign_enforcement_closure_epoch`) | 名実が一致する。裁定 Q3 が固定した識別子名を変えることになる |

**親の推奨 = (a)。** 理由: 規律 2 の趣旨は「正しさが検証されていない証拠の上に certified を
積まない」であり、正しさ判定の実体が束縛外にあると、その趣旨が将来の書き換えに対して守られない。
実 corpus に v2 lock が 0 件である今が、**壊れる成果物ゼロで closure を広げられる唯一の窓**である。
(b) は名実の乖離が残る。(c) は名前を実態に合わせるだけで、穴そのものは塞がらない。

**親が本 wave で (a) をやらなかった理由**: 裁定 Q3 は「**既存**の authority へ束縛する」であり、
authority の定義を変えることまでは委任されていないと読んだ。並走タスクが manifest schema を
触っている点も考慮した。

---

## Q2: [T-834] を本 wave の分類表で閉じてよいか

[T-834] は「旧 certified / 旧 fitness を読む生きた consumer 8 経路を、certified を名乗る受理集合か
歴史解析の生値かに分類する」タスクで、[T-817] Q1 の scope 確定の前提として起票されていた。

本 wave は **16 経路**を実コードで分類し、そのすべてに受理目的を表明させた
(裁定 §5 の表)。[T-834] が挙げた 8〜10 経路はすべて含まれ、さらに
`s6_sort_sweep` / `s8a_trigger_sweep` / `backoff_sweep_report` /
`autonomous_trial_completeness` / p3 loop 群 / `tools/plotting/plot_backoff.py` /
`critic/online_digest` が**追加で見つかった** (段 3 の敵対レンズ 2 本が独立に発見)。

- **(a) [T-834] を本 wave で閉じる** ← **親の推奨**。分類は実装済みで、機械的に検査もされている。
- (b) 別途 [T-834] として棚卸しを続ける。分類表が本当に悉皆かを独立に検査したい場合。

---

## 変わらないこと

- CCBench (`external/ccbench`) は 1 bit も変えていない。
- 既存 WAL、`output/s1-freeze/*`、`output/s8b-freeze/*` の bytes は 1 bit も変えていない。
- `campaign.lock` の wire contract (`IDENTITY_KEYS` / `AUTHORITY_KEYS` / `V2_KEYS` /
  `CONTRACT_LOADER_RELATIVE_PATHS`) と `search_config` は不変。既存 campaign の ID (dir 名) も不変。
- 裁定 Q2 のとおり、WAL と stdout の突き合わせ機構は作っていない。
- [T-860] (guided WAL の位置づけ) と [T-861] (歴史 campaign の admission) には触れていない。
  guided の online digest は「現行の分析用途をそのまま歴史側として明示する」に留め、
  格上げも格下げもしていない。
- 絶対規律 1〜6。
