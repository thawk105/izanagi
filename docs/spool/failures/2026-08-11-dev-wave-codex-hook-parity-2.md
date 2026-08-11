---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-codex-hook-parity
seq: 2
---

## 新規

### {{F:codex-web-search-evidence}}. Codex 子が web 検索を使うと成果物が必ず不採用になる [手順漏れ]

- 事象: `codex exec` は rc=0 で完走し出力も生成されたのに receipt が `evidence_status=invalid` /
  `accepted=false` になり、`-o` の最終成果物が書かれない。段 3 の 1 本が 1531 秒・入力 530 万 token を
  消費して不採用になった。
- 根本原因: Codex の `web_search` イベントは `item` オブジェクト内に `id` キーを 2 回持つ
  (`"id":"item_34"` と `"id":"exec-…"`)。`tools/codex_worker_launch.py` の stdout 解析は重複キーを
  拒否する strict parser を使うため `stdout_invalid` が立ち、`_evidence_status()` が invalid を返す。
  rollout 側の証跡 (model・effort・cwd・session_meta・turn_context・usage) はすべて正常だった。
- 恒久対応: 当面は子 prompt に web 検索禁止を明記する (repo 内の一次資料だけを根拠にさせる)。
  解析側で重複キーを許容するか、worker 起動時に web 検索を機械的に無効化するかは裁定へ回す。
- 再発検知: receipt の `evidence_status` が invalid のとき、stdout イベントに `web_search` が
  含まれるかを見る。含まれていれば本 F。

### {{F:codex-cannot-write-own-config-dir}}. Codex は `.codex/` 配下へ構造的に書けない [手順漏れ]

- 事象: 段 5 の実装子が `.codex/hooks.json` だけを作れず、`patch rejected: writing outside of the
  project; rejected by user approval settings` で拒否された。sandbox は `workspace-write`、
  approval は `never`、ディレクトリは書き込み可能だった。
- 根本原因: Codex が自分の設定ディレクトリへの書き込みを自己保護として拒否する。D95 は `.codex/`
  配下の非 md/rst を実装面 (Codex author 必須) と定めているため、規約と実行可能性が正面衝突する。
- 恒久対応: 当該ファイルだけ親が書き、commit trailer に `role=author` を製品別に分けて記す
  (本 wave は Codex author 行と Claude author 行を scope 付きで併記した)。
- 再発検知: `.codex/` 配下の実装面を Codex 子へ割り当てた時点で本 F を想起する。
