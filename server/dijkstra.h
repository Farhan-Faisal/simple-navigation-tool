#ifndef _DIJKSTRA_H_
#define _DIJKSTRA_H_

#include "wdigraph.h"
#include <utility>
#include <unordered_map>

using namespace std;

// typedef creates an alias for the specified type
// PIL is the value type of our searchTree 
typedef pair<int, long long> PIL;

// PIPIL is used to insert a key-value pair in our searchTree
// if we declare a variable 'x' as follows:  PIPIL x;
// x.first gives the start vertex of the edge, 
// x.second.first gives the end vertex of the edge, 
// x.second.second gives the cost of the edge
typedef pair<int, PIL> PIPIL;


class ComparablePIPIL {
public:
	// Define the function call operator: operator()
	bool operator() (const PIPIL& lhs, const PIPIL& rhs) const {
		// Compare burning times only
		return (lhs.second.second > rhs.second.second); // min heap
	}
};

void dijkstra(const WDigraph& graph, int startVertex,
              unordered_map<int, PIL>& tree);

#endif
