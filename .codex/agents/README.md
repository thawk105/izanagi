# Codex role adapter — native 0 / static 16 / runtime blocked

`.claude/agents/*.md` は role 本文と Claude Code 固有の model/tools 契約の正本である。
Codex 版は自動発見されない `.codex/role-adapters/*.json` に全 16 件を置き、共有 manifest と renderer、
semantic policy、checker で同期する。初版判断は D54、native profile の休眠化は D55、当時の 13 件の
静的移植と runtime 裁定は D56 とする。14 件目の `coder-v4-autonomous-k2` は D1429 (合成の既定を
知識水準 K2 にする裁定) を受けて足した K2 宣言アーム用の兄弟 role。15・16 件目は T-2865 の方策軸用 C++ / IR coder role。runtime は全件 blocked。

現行状態は次の 3 軸を混同しない。

| 面 | 状態 | 意味 |
|---|---|---|
| native profile | active 0 / 発見可能 profile 0 | `.codex/agents/*.toml` と project `[agents.<name>]` は禁止 |
| static adapter | 16 / 16 定義済み | Claude 本文・metadata・I/O・capability lowering を byte-stable JSON に移植済み |
| runtime activation | active 0 / blocked 16 | `input.additional_tools` を構造的に除去できないため実行禁止 |

static adapter は実行可能 profile ではない。`dormant` は「無効な TOML を残す」という意味でも、
prompt 規律だけで隔離できたという意味でもない。

`selector-8b` も tool-less Claude role の static/dormant projection のみで、Codex runtime は blocked のままとする。

## 静的移植の契約

各 adapter は移植元本文を exact 1 回、Codex product override より前へ埋め込む。Claude の tool は
Codex 子へ再付与せず、`Read/Grep/Glob` は trusted input projection、`Bash/Write` は trusted driver、
`Edit` は構造化提案へ lower する。全 role の model/effort、top-level closed envelope と重要 field の
schema、禁止入力 class、recursive forbidden-key policy、consumer 配線状態を manifest に明示する。
`semantic_projection_mode` は direct/mediated という変換方式の分類であり、製品間の意味等価性や
producer/consumer の実配線を証明する値ではない。

opaque string と意図的に open な object subtree は安全に再解釈できないため完全検査の対象外であり、
その内容を射影する trusted producer が禁止情報を除く。`consumer: null` の role は standalone typed
proposal 定義までで、既存の
研究 pipeline へ自動採用される配線を意味しない。

`spawn_agent` の `task_name` を `auditor` などにしても profile selector にはならず、generic child の
名前が変わるだけである。child や親が自然言語 final で「profile を受領した」「拒否した」と申告しても、
spawn event と tool event が無ければ実行証拠に数えない。generic child を dormant role の代替として
扱ってはならない。

## runtime の blocker と再開条件

Codex CLI 0.144.2 の raw Responses request では top-level `body.tools` が空でも、developer
`input.additional_tools` に `exec` / `collaboration` / `request_user_input` / `wait` が注入される。
`exec` と `collaboration` の下には file 操作や agent fan-out に到達し得る宣言面がある。
したがって top-level tool 0 件や JSONL 上の tool event 不在を「tool-free」の証拠にしない。

`tools/run_codex_role.py` の既定動作は外部 model と credential を使わず、実 CLI thread で custom loopback
provider 宛ての raw request と outer namespace を attestation するだけである。これは production provider の
request capture ではない。`--live` も同じ loopback preflight 後に必ず
`BLOCKED_BY_RUNTIME_TOOL_SURFACE` で失敗し、credential 読込・official-provider command の経路自体を持たない。
bubblewrap の host repo/home 非表示と forced `view_image` の `ENOENT` は defense-in-depth 証拠であり、
active 化の十分条件には数えない。forced fixture は outer namespace だけを検査するため内側を
`danger-full-access` にするが、pinned outer bubblewrap・loopback provider 内に限定し、active role 設定には使わない。
probe は host の loopback server へ到達するため network namespace を共有する。provider URL は
`127.0.0.1` の一時 port に固定するが、network 隔離の証拠には数えない。

wire attestation は top-level key 集合、message/content boundary と順序、`additional_tools` 全 descriptor、
forced fixture だけに許す tool history を exact に固定する。request は strict UTF-8/JSON として読み、
重複 key、非有限数、過深入力を拒否する。Codex/bubblewrap は検証した bytes を runtime 用に固定してから
実行し、pathname の初回 hash と後続実行を別実体にしない。ただし同一 UID の敵対 process に対する
provenance や network 隔離は証明しない。loopback/outer sandbox は active 化の十分条件ではない。

次の 3 共通条件をすべて満たすまで、runtime E2E は **BLOCKED** である。未実行を skip や成功として
数えず、active 数を 0 のまま保つ。

1. **全 tool surface の exact allowlist:** filesystem sandbox だけでなく、built-in tool、shell、
   MCP server、apps/connectors、skills、plugins を含む child の全 surface を role ごとの許可集合に
   固定できる。省略フィールドによる親からの継承は許可しない。
2. **event-based E2E:** standalone では実 `codex exec` thread ID、adapter/instruction/input digest、
   exact tool inventory と許可外 local/remote read・write・再帰 Codex・agent fan-out の拒否 event を検査する。
   tool 許可集合が空の role には「許可 tool の実行」を求めず、非空の場合のみ positive event を求める。
3. **policy 再分類:** D55/D56、`tools/check_codex_agents.py`、専用テストを同時に更新し、独立レビュー後に
   初めて active runtime を実装する。native を選ぶ場合だけ active profile も生成する。

native custom profile を再採用する場合だけは、上記に加えて明示 profile selector と spawn event 上の
非空 child thread ID / agent type / child instruction digest を必須とする。`task_name` の命名と成功自己申告は
その positive control に数えない。

Codex hook adapter だけでは条件 2 を満たさない。local file write を止めても、継承した MCP/apps 等の
外部 read・write 面は残るためである。

## 整合性検査

role の意味変更は対応する `.claude/agents/*.md` に入れる。
`orchestrator/codex_roles/review_ledger.py` は自動生成物と独立したレビュー済み source/description/schema、
full role manifest、共通 developer instruction template の SHA-256 と role 別 I/O 契約の固定台帳である。
direct JSON 例を持つ 9 role は source の入力・出力 shape parity、mediated の 7 role は固定 source hash +
reviewed I/O obligations で移植契約を結び、台帳の明示レビュー無しに再生成だけで追従しない。checker は
Claude と Codex の全単射、
frontmatter、description の JSON quote、本文の埋込・digest、model/effort、capability lowering、I/O schema、
semantic policy、consumer、adapter の期待 byte、native discovery 0 を同時に検査する。通常確認は次で行う。

```sh
python3 tools/check_codex_agents.py
python3 -m pytest -q orchestrator/tests/test_codex_agents.py orchestrator/tests/test_codex_role_runtime.py
```

`--write` は native profile 生成との誤認を避けるため fail-closed に拒否する。自然言語の成功文、TOML の
load/parse、prompt 文字列の存在だけを selector、実 spawn、権限拒否の証明にしてはならない。
