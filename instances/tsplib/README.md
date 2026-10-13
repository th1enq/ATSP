# TSPLIB ATSP benchmark inputs

These ten instances occur in the official [TSPLIB ATSP catalog](https://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/atsp/atspindex.html).

The environment cannot download the Heidelberg gzip archives directly. The
plaintext matrices were fetched through the web tool from the
[TSPLib.Net mirror](https://github.com/pdrozdowski/TSPLib.Net/tree/master/TSPLIB95/atsp).
Where the web tool flattened whitespace, headers and matrix rows were
reformatted without changing numerical entries. All matrices have exactly
`DIMENSION²` entries. This is not a byte-for-byte archive comparison with the
Heidelberg originals. See `manifest.json` for actual retrieval URLs and hashes.

The numerical matrices are evaluated as provided. Only diagonal sentinel
entries are excluded from travel costs. There is no shortest-path closure,
symmetrization of the objective, or replacement with generated data.

Seven inputs are directed metrics: `ft53`, `ftv33`, `ftv35`, `ftv38`, `ftv44`,
`ftv47`, `ftv55`. The other three (`br17`, `p43`, `ry48p`) violate the triangle
inequality; their tours remain valid for the original objective, but the
metric approximation theorem does not apply to them.

Bottleneck optimum references come from Table 5 of LaRusic & Punnen,
[The asymmetric bottleneck traveling salesman problem: Algorithms, complexity and empirical analysis](https://cedric.cnam.fr/~bentzc/INITREC/Files/CB1.pdf),
Computers & Operations Research 43 (2014), 20–35.
The ordinary minimum-sum ATSP optima on the TSPLIB website are not used.

This is a ten-instance subset, not the complete 19-instance official catalog.
