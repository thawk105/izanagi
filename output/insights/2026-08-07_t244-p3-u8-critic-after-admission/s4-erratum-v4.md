# [T-244] P3 critic 後置 (U-8) — 段 4 裁定の訂正 (v4、v3 への追補)

## 1. 実装子が検出した第 2 の矛盾 (real、採用)

v3 は「direct `_run_workload` が critic を呼ばない」と「既存直呼びテストを無変更で通す」を
同時に要求していた。しかし既存の 2 テストは全 provider が 1 回ずつ呼ばれることを assert する。

- `test_run_workload_accepts_fresh_state` 系 (`test_p3_autonomous_workload_trial.py:1763`)
- `test_run_workload_rejects_actual_existing_campaign_state` の直後の正例 (同 `:1828`)

いずれも `assert all(len(provider.payloads) == 1 for provider in providers.values())` の 1 行である。

**判定: real / 採用。v3 §3 の 8 (既存直呼びテスト無変更) を撤回する。**

## 2. 親の追加実測

- 上記 2 行は、両テストの**主題ではない**。両テストの主題は campaign state の freshness 受理であり、
  当該行は「役割が一通り走った」ことの付随確認である。
- critic の payload を検査する他の assertion (`:894-897`, `:991`, `:1252`, `:2112-2113`) は
  すべて `run_trial` 経由である。critic は後置後も `run_trial` 経路では呼ばれるため、**追随不要**。
- `test_claude_transport.py:2086` の直呼びは `providers={}` かつ wall-budget 即時 break であり、
  critic を呼ばない。**追随不要**。

したがって追随が要るのは**上記 2 行だけ**である。

## 3. 名指しの追随許可 (これ以外の既存テスト編集は引き続き禁止)

`test_p3_autonomous_workload_trial.py` の `:1763` と `:1828` の各 1 行を、次の**同等以上に強い**
形へ差し替えることだけを許可する。

```python
assert all(
    len(providers[role].payloads) == 1
    for role in ("planner", "coder", "auditor")
)
assert providers["critic"].payloads == []
assert len(result["_pending_critics"]) == 1
```

(private key の実際の名前は実装に合わせる。要点は「planner/coder/auditor は 1 回」「critic は 0 回」
「pending が 1 件」の 3 点を同時に固定することである。)

**これは緩和ではなく追随である** — 検査点は 4 から 6 へ増え、新しい contract を固定する。
`payloads` の assert を単に削除すること、`critic` を providers から外すこと、
skip / xfail 化することは**禁止**する。

D96 の「境界テストを同じ変更単位で新しい受理集合へ追随させる」に該当する変更として記録する。

## 4. v3 からの他の変更

なし。v3 §2 (プラン v3)、§3 の 1〜7、§4 (変異事前登録)、§5 (scope 外所見) はそのまま有効。
