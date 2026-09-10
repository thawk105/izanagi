## 総括

must-fix はありません。所見は fail-closed なテストの脆さ 1 件のみです。  
判定器の変更は既存条件への純粋な論理積追加で、受理集合は狭化する以外にありません。`TOKEN_ONLY_C04` の参照先も C04 の検査だけです。  
2 負例は baseline 通過後、3 件目の call edge だけを除去しており、拒否理由は単一です。  
既存期待値の反転・緩和・skip・削除、および hash・絶対 path・時刻などの揮発 payload はありません。  
read-only 制約に従い、レビューは静的検査のみで、テスト実走はしていません。

## 所見

### 実 repo 負例の逐語照合は無害な整形でも失敗する

file: [test_s8c_preregistration_predicates.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:352)

`started_trial_call` が引数の改行、インデント、`ROOT` の綴りまで固定しています。production が意味を保ったまま整形されると、意味検査へ進む前に `count == 1` が失敗します。ただしテスト自体が赤になるため、欠落を見逃して緑になる fail-open ではなく、明確に fail-closed です。

成果物影響: certified 選択・レポート・台帳の値や受理集合を誤って広げることはなく、無害な整形で検証パイプラインを偽赤にするだけです。  
重さ: **nit**

受理集合については、[s8c_preregistration_evidence.py:2065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:2065) の既存 `all(...)` に純粋な `_declared_call` を一つ加えただけなので、旧拒否入力が新たに通る経路はありません。`TOKEN_ONLY_C04` の全参照は C04 negative-control、C04 reachability-error 検査、新規 C04 負例に閉じており、他 condition の parametrize 入力には流入しません。

単一理由性も破れませんでした。両負例とも baseline が `EVIDENCE_UNDEFINED` まで通ることを先に確認し、mutation 後も `main → run_trial`、先行二辺、contract の declared path、registry の両定義を維持します。後段の `forbid_trial_restart` 定義検査も成立したままで、初めて偽になるのは `reject_started_trial` の `_declared_call` だけです。

実 repo 負例は [_snapshot_current_commit:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:153) が評価対象 HEAD の evidence blob を `git archive` し、その p3/registry bytes を直接使用します。したがって `TOKEN_ONLY_C04` と registry stub の両層だけで、この実 repo 検査を通す抜け道はありません。

## scope 外の real 所見

新規所見はありません。段 4 で裁定済みの限界は残ります。すなわち、実 production blob 自体を同じ名前・call edge を保った no-op stub に置換すれば検査を通せます。また、呼出し位置・支配関係と契約 `field_paths` も検査対象外です。

成果物影響: 実処理が無効でも C04 レポートが `UNSATISFIED` へ変わらず、静的受理集合が実効的な lifecycle 防壁より広いままになり得ます。これは既裁定どおり、本 wave の must-fix ではありません。