# 親の独立レビュー証跡 — role file 2 枚と adapter 2 枚 ([T-2145])

先例 (`docs/decisions.md` の役割契約節) が求める手順は次である。

> pin (manifest / adapter / review_ledger) は**起草者と別の実装単位**が、
> **親の独立レビュー証跡**を経て更新した。adapter JSON は sandbox 制約により、
> 検査器 renderer の期待 bytes を**親が review して適用**した。

本 wave はこれに従った。本文がその証跡である。

## 1. 何を変えたか、なぜ必要だったか

| file | 変更の理由 |
|---|---|
| `.claude/agents/coder-v4-autonomous-sort.md` | **本 wave の中核。** 受理言語を 79 値の閉じた IR 文法へ縮めたので、合成子の出力規約が変わる。D1451 が求める「別実験になる点の明示」もここに書く必要がある |
| `.claude/agents/auditor.md` | 段 6 レビュー A 所見 3。admission 通過後は構造上起こりえない型 (非 SWO・追加関数・呼び出し・loop・throw) を auditor の職務として列挙したままだと、誤判定が正準 IR を不当に拒否しうる。sort 軸に限り renderer / admission の事後条件と明記して veto の根拠から外した |

## 2. 起草者と更新者が別であること

| 成果物 | 起草した実装単位 | pin を更新した実装単位 |
|---|---|---|
| `coder-v4-autonomous-sort.md` | 段 5 実装子 | fix 第 3 巡の子 |
| `auditor.md` | fix 第 1 巡の子 | fix 第 3 巡の子 |

fix 第 3 巡の子は**どちらの agent file も起草していない**。要件を満たす。

## 3. 親が独立に確認したこと

### 3.1 role source の drift (実測)

`orchestrator/codex_roles/review_ledger.py` の `SOURCE_FILE_SHA256` に対する実測値。

| role | 記録値 (更新前) | 実測値 |
|---|---|---|
| `auditor` | `e33c65d446bedb5bc1d372f8bcdd1b59968a0a3093ff23f300cb0af0dddebc3e` | `a0912ebbc95e2f3641cfb1cbf0d609cfbe2deb7ba52d1c3057517b1bc69fab35` |
| `coder-v4-autonomous-sort` | `fbabef04095f73b7fc517290afc66d4fb8779144184eaf7c078fc17d50d7ca9a` | `0d98a362d6cde3e77a407851aaace7444086ee6add33dbd5df2f586db5666772` |

`EXPECTED_ROLE_COUNT` は 13 のまま。役割の増減は無い。

### 3.2 adapter の期待 bytes (親が renderer から取得して review)

`tools/check_codex_agents.py --write` は意図的に封じられており、同 tool の stderr が
「role-adapters は manifest renderer の期待 byte を review して apply する」と定めている。
親は `orchestrator/codex_roles/spec.expected_adapters()` から期待 bytes を取り出し、
現物との差分を読んだうえで適用した。

**差分に現れた top-level key は 2 つだけである。**

| key | 変化の内容 |
|---|---|
| `developer_instructions` | 埋め込まれた Claude role 本文が、編集後の `.md` と一致するよう更新された |
| `semantic_digest` | 上記本文の digest |

**変化していないことを親が確認した key:** `mode` (`static-dormant` 固定)、
`runtime_activation` (blocked のまま)、model / effort / tools の契約、
`role_manifest` 系、入出力 contract。

すなわち adapter の変更は**役割本文の機械的な伝播だけ**であり、権限・起動可否・
モデル方針・I/O 契約はいずれも動いていない。これが親の review 結論である。

### 3.3 適用後の検査 (親が実走)

    python3 tools/check_codex_agents.py
    OK: Codex agent roles (0 native active / 13 static dormant;
        runtime activation blocked: uncontrollable_additional_tools)
    rc=0

rc はパイプに通さず直接取得した。

## 4. 受理集合への影響

- `coder-v4-autonomous-sort.md` の変更は**合成子が出してよい文字列を狭める**方向である。
  79 値の正準形以外は機械の admission が拒否するので、agent 契約の記述は
  機械 gate に対して従属的であり、これ単独で受理集合を広げることはない。
- `auditor.md` の変更は **deny-only veto の発火条件を狭める**方向である。
  auditor は候補を受理する権限を持たない (`p3_s4_loop.py` の veto は `passed=False` しか作らない)
  ため、これによって受理集合が広がることはない。狭めた分は機械 admission が既に担保している。
- したがって**規律 2 に反しない**。過剰拒否を減らす向きの変更である。

## 5. 限界

- 本証跡は role source と adapter の**機械的整合**と**受理集合への向き**を確認したものであり、
  agent 本文の記述が実際の LLM 挙動をどう変えるかを測ったものではない。
  それは合成走を回すまで分からない。
- adapter の bytes は renderer が生成したものをそのまま適用した。親が手で書いた bytes は無い。
