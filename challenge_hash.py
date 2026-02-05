import argparse
import hashlib
import sys

def compute_hash(alpha: int, beta: int, gamma: int, nonce: str) -> str:
    s = f"{alpha}-{beta}-{gamma}-{nonce}"
    return hashlib.sha256(s.encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser(prog="challenge_hash", description="Compute SHA256 for alpha-beta-gamma-nonce")
    parser.add_argument("--alpha", type=int, required=True)
    parser.add_argument("--beta", type=int, required=True)
    parser.add_argument("--gamma", type=int, required=True)
    parser.add_argument("--nonce", type=str, required=True)
    args = parser.parse_args()
    h = compute_hash(args.alpha, args.beta, args.gamma, args.nonce)
    print(h)
    print(f'{{"nonce":"{args.nonce}","hash":"{h}"}}')

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
