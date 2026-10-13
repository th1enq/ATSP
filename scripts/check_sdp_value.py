"""Replay saved SDP primal/dual certificates without running optimizers."""
import argparse
import json
import gzip
from pathlib import Path
from sdp_dual_certificate import verify_sdp_value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    args=parser.parse_args()
    if args.input.suffix=='.gz':
        with gzip.open(args.input,'rt') as stream:
            raw=json.load(stream)
    else:
        raw=json.loads(args.input.read_text())
    if 'sdp_queries' not in raw:
        print(json.dumps(verify_sdp_value(raw),indent=2))
        return
    completed=[q for q in raw['sdp_queries'] if q['completed']]
    if not completed:
        raise ValueError('no completed SDP queries to verify')
    for q in completed:
        verify_sdp_value(q['certificate'])
    print(json.dumps(dict(verified_sdp_intervals=len(completed),
                         incomplete_sdp_queries=len(raw['sdp_queries'])-len(completed)),indent=2))


if __name__=='__main__':
    main()
