"""Anchor the prediction record to Bitcoin, so "frozen before the outcome" is provable.

    python src/anchor.py                 # anchor if the record changed, upgrade pending proofs
    python src/anchor.py --verify KEY    # Merkle proof for a ledger row, KEY = "<ts>:<pair>:<hold>"

Each anchor is a Merkle root over every ledger row and every shadow execution
at that moment. The root is written to data/anchors/<id>.root.txt and stamped
with OpenTimestamps (`ots stamp`), which commits it to the Bitcoin blockchain
through public calendar servers - no wallet, key or fee. Pending proofs are
upgraded on later runs once the calendar's Bitcoin transaction confirms.

What this proves: a row whose hash is under a confirmed root existed before
that Bitcoin block. A prediction anchored before its hold ended cannot have
been written with knowledge of the outcome. What it does not prove: that the
row is correct, or that no other rows were withheld before the first anchor.

Anyone can check a root without trusting this repo: upload the .root.txt and
its .ots file at https://opentimestamps.org, or run `ots verify`.
"""
import argparse, datetime as dt, hashlib, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import model, ledger
from score import EXECUTIONS, execution_key

ANCHORS = os.path.join(model.DATA, "anchors")
INDEX = os.path.join(ANCHORS, "index.json")


def leaf(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                     default=str).encode()).hexdigest()


def merkle(leaves):
    """Root and full level list; odd nodes are carried up unchanged."""
    levels = [leaves]
    while len(levels[-1]) > 1:
        cur, nxt = levels[-1], []
        for i in range(0, len(cur), 2):
            if i + 1 < len(cur):
                nxt.append(hashlib.sha256(bytes.fromhex(cur[i]) + bytes.fromhex(cur[i + 1])).hexdigest())
            else:
                nxt.append(cur[i])
        levels.append(nxt)
    return levels[-1][0], levels


def proof(levels, i):
    path = []
    for level in levels[:-1]:
        sib = i ^ 1
        if sib < len(level):
            path.append({"side": "left" if sib < i else "right", "hash": level[sib]})
        i //= 2
    return path


def row_key(r):
    ev = r.get("evidence") or {}
    return execution_key(r.get("ts"), ev.get("pair"), ev.get("hold_days"))


def record_leaves():
    rows = ledger.read_all()
    execs = {}
    if os.path.exists(EXECUTIONS):
        with open(EXECUTIONS, encoding="utf-8") as f:
            execs = json.load(f)
    leaves = [("ledger", row_key(r), leaf(r)) for r in rows]
    leaves += [("execution", k, leaf(v)) for k, v in sorted(execs.items())]
    return leaves


def _index():
    if not os.path.exists(INDEX):
        return []
    with open(INDEX, encoding="utf-8") as f:
        return json.load(f)


def _ots(*args):
    exe = shutil.which("ots")
    if not exe:
        return None
    p = subprocess.run([exe, *args], capture_output=True, text=True, timeout=120)
    return p.stdout + p.stderr


def bitcoin_height(ots_path):
    out = _ots("info", ots_path) or ""
    heights = [int(h) for h in re.findall(r"BitcoinBlockHeaderAttestation\((\d+)\)", out)]
    return min(heights) if heights else None


def run():
    os.makedirs(ANCHORS, exist_ok=True)
    index = _index()
    leaves = record_leaves()
    hashes = [h for _, _, h in leaves]
    if not hashes:
        print("[anchor] nothing to anchor")
        return
    root, _ = merkle(hashes)
    if not index or index[-1]["root"] != root:
        aid = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        root_file = os.path.join(ANCHORS, f"{aid}.root.txt")
        with open(root_file, "w", encoding="utf-8") as f:
            f.write(root + "\n")
        with open(os.path.join(ANCHORS, f"{aid}.leaves.json"), "w", encoding="utf-8") as f:
            json.dump([{"kind": k, "id": i, "hash": h} for k, i, h in leaves], f)
        stamped = _ots("stamp", root_file) is not None and os.path.exists(root_file + ".ots")
        index.append({"id": aid, "root": root, "n_leaves": len(hashes),
                      "n_ledger_rows": sum(1 for k, _, _ in leaves if k == "ledger"),
                      "created_utc": aid, "stamped": stamped, "bitcoin_block": None})
        print(f"[anchor] new root {root[:16]}... over {len(hashes)} leaves "
              f"({'stamped' if stamped else 'NOT stamped - ots client missing'})")
    upgraded = 0
    for a in index:
        ots_file = os.path.join(ANCHORS, f"{a['id']}.root.txt.ots")
        if a.get("stamped") and not a.get("bitcoin_block") and os.path.exists(ots_file):
            _ots("upgrade", ots_file)
            h = bitcoin_height(ots_file)
            if h:
                a["bitcoin_block"] = h
                upgraded += 1
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1)
    print(f"[anchor] {len(index)} anchors, {upgraded} newly confirmed in Bitcoin")


def first_anchor_for(key):
    """Earliest anchor whose leaf set contains the ledger row with this key."""
    for a in _index():
        path = os.path.join(ANCHORS, f"{a['id']}.leaves.json")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            leaves = json.load(f)
        for i, lf in enumerate(leaves):
            if lf["kind"] == "ledger" and lf["id"] == key:
                return a, leaves, i
    return None, None, None


def verify(key):
    rows = [r for r in ledger.read_all() if row_key(r) == key]
    if not rows:
        print(f"no ledger row with key {key}")
        return 1
    a, leaves, i = first_anchor_for(key)
    if not a:
        print("row not anchored yet")
        return 1
    h = leaf(rows[0])
    if h != leaves[i]["hash"]:
        print("MISMATCH: the row changed after it was anchored")
        return 1
    root, levels = merkle([lf["hash"] for lf in leaves])
    node = h
    for step in proof(levels, i):
        pair = (step["hash"] + node) if step["side"] == "left" else (node + step["hash"])
        node = hashlib.sha256(bytes.fromhex(pair)).hexdigest()
    ok = node == root == a["root"]
    print(json.dumps({"ledger_row": key, "leaf": h, "root": root, "anchor": a["id"],
                      "bitcoin_block": a.get("bitcoin_block"), "proof_ok": ok}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", metavar="KEY")
    args = ap.parse_args()
    sys.exit(verify(args.verify) if args.verify else run())
