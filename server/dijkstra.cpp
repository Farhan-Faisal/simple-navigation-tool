#include <queue>
#include <vector>
#include "dijkstra.h"

void dijkstra(const WDigraph& graph, int startVertex, 
    unordered_map<int, PIL>& searchTree) {

    // each active fire is stored as (v, (u, d)) 
    // which implies that it is a fire started at u
    // currently burning the (u,v) edge 
    // and will reach v at time d
    priority_queue<PIPIL, vector<PIPIL>, ComparablePIPIL> fires;

    // at time 0, the startVertex burns, we set the predecesor of
    // startVertex to startVertex (as it is the first vertex)
    fires.push(PIPIL(startVertex, PIL(startVertex, 0)));

    // while there is an active fire
    while (fires.size() > 0) {
        // finding the fire that reaches its endpoint earliest
        PIPIL earliestFire = fires.top();

        int v = earliestFire.first; 
        int u = earliestFire.second.first; 
        long long d = earliestFire.second.second;

        // remove this fire
        fires.pop();

        // if v is already "burned", there nothing to do
        if (searchTree.find(v) != searchTree.end()) {
            continue;
        }

        // record that 'v' is burned at time 'd' by a fire started from 'u'
        searchTree[v] = PIL(u, d);

        // now start fires from all edges exiting vertex 'v'
        for (auto iter = graph.neighbours(v); iter != graph.endIterator(v); iter++) {
            int nbr = *iter;

            // 'v' catches on fire at time 'd' and the fire will reach 'nbr'
            // at time d + (length of v->nbr edge)
            long long t_burn = d + graph.getCost(v, nbr);
            fires.push(PIPIL(nbr, PIL(v, t_burn)));
        }
    }
}