#include <iostream>
#include <cassert>
#include <fstream>
#include <string>
#include <string.h>
#include <list>

#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>

#include "wdigraph.h"
#include "dijkstra.h"

#define BUFFER_SIZE 256

struct Point {
    long long lat, lon;
};

// returns the manhattan distance between two points
long long manhattan(const Point& pt1, const Point& pt2) {
  long long dLat = pt1.lat - pt2.lat, dLon = pt1.lon - pt2.lon;
  return abs(dLat) + abs(dLon);
}

// finds the id of the point that is closest to the given point "pt"
int findClosest(const Point& pt, const unordered_map<int, Point>& points) {
  pair<int, Point> best = *points.begin();

  for (const auto& check : points) {
    if (manhattan(pt, check.second) < manhattan(pt, best.second)) {
      best = check;
    }
  }
  return best.first;
}

// read the graph from the file that has the same format as the "Edmonton graph" file
void readGraph(const string& filename, WDigraph& g, unordered_map<int, Point>& points) {
  ifstream fin(filename);
  string line;

  while (getline(fin, line)) {
    // split the string around the commas, there will be 4 substrings either way
    string p[4];
    int at = 0;
    for (auto c : line) {
      if (c == ',') {
        // start new string
        ++at;
      }
      else {
        // append character to the string we are building
        p[at] += c;
      }
    }

    if (at != 3) {
      // empty line
      break;
    }

    if (p[0] == "V") {
      // new Point
      int id = stoi(p[1]);
      assert(id == stoll(p[1])); // sanity check: asserts if some id is not 32-bit
      points[id].lat = static_cast<long long>(stod(p[2])*100000);
      points[id].lon = static_cast<long long>(stod(p[3])*100000);
      g.addVertex(id);
    }
    else {
      // new directed edge
      int u = stoi(p[1]), v = stoi(p[2]);
      g.addEdge(u, v, manhattan(points[u], points[v]));
    }
  }
}

int create_and_open_fifo(const char * pname, int mode) {
  // creating a fifo special file in the current working directory
  // with read-write permissions for communication with the plotter
  // both proecsses must open the fifo before they can perform
  // read and write operations on it
  if (mkfifo(pname, 0666) == -1) {
    cout << "Unable to make a fifo. Ensure that this pipe does not exist already!" << endl;
    exit(-1);
  }

  // opening the fifo for read-only or write-only access
  // a file descriptor that refers to the open file description is
  // returned
  int fd = open(pname, mode);

  if (fd == -1) {
    cout << "Error: failed on opening named pipe." << endl;
    exit(-1);
  }

  return fd;
}


/*
   Description: 
     - Reads coordinates from pipe (fd in)
     - Preprocesses the string into the required formatted lon long
     - Stores the start and end latitudes and longitudes in sPoint and ePoint

   Arguments:
     - sPoint (Point *): pointer to struct of lat and lon values of start point
     - ePoint (Point *): pointer to struct of lat and lon values of end point
     - in (int): File descriptor to pipe in which client writes to
  Returns:
     - (int): 1 if 'Q' is read from in pipe; 0 otherwise
*/
int read_request(Point *sPoint, Point * ePoint, int in){
  // Will read everything from pipe for easier manipulation afterwards
  char from_pipe[BUFFER_SIZE];
  memset(from_pipe, 0, BUFFER_SIZE);
  
  // Will store individual coordinates before loading into points
  char temp_coordinate[BUFFER_SIZE];
  memset(temp_coordinate, 0, BUFFER_SIZE);

  int counter = 0;

  // Read from inpipe into from_pipe
  // Storing the total number of characters read
  int ret_val = read(in, &from_pipe, sizeof(from_pipe));

  // Check if read failed
  if (ret_val < 0){ 
      cout << "read failed" << endl;
      exit(1);
  }
  if (from_pipe[0] == 'Q'){
    // Server needs to be closed if this happens
    return 1;
  }

  // 

  int index = 0;
  for (int i = 0; i < ret_val; i++){
    char c = from_pipe[i];
    temp_coordinate[index] = c;
    index++;


    // Means got the start latitude
    if (counter < 2 && c == ' '){
      temp_coordinate[index] = '\0';
      (*sPoint).lat = static_cast<long long>(stod(temp_coordinate)*100000);
      memset(temp_coordinate, 0, BUFFER_SIZE);
      index = 0;
      counter++;
    }
    
    // Got the start longitude
    else if (counter < 2 && c == '\n'){
      temp_coordinate[index] = '\0';
      (*sPoint).lon = static_cast<long long>(stod(temp_coordinate)*100000);
      memset(temp_coordinate, 0, BUFFER_SIZE);
      index = 0;
      counter++;
    }
    
    // Got the end latitude
    else if (counter >= 2 && c == ' '){
      temp_coordinate[index] = '\0';
      (*ePoint).lat = static_cast<long long>(stod(temp_coordinate)*100000);
      memset(temp_coordinate, 0, BUFFER_SIZE);
      index = 0;
      counter++;
    }

    // Got the end longitude
    else if (counter >= 2 && c == '\n'){
      temp_coordinate[index] = '\0';
      (*ePoint).lon = static_cast<long long>(stod(temp_coordinate)*100000);
      memset(temp_coordinate, 0, BUFFER_SIZE);
      index = 0;
      counter++;
    }
  }
  return ret_val;
}



// keep in mind that in part 1, the program should only handle 1 request
// in part 2, you need to listen for a new request the moment you are done
// handling one request
int main() {
  WDigraph graph;
  unordered_map<int, Point> points;

  const char *inpipe = "inpipe";
  const char *outpipe = "outpipe";

  // Open the two pipes
  int in = create_and_open_fifo(inpipe, O_RDONLY);
  cout << "inpipe opened..." << endl;
  int out = create_and_open_fifo(outpipe, O_WRONLY);
  cout << "outpipe opened..." << endl;  

  // build the graph
  readGraph("server/edmonton-roads-2.0.1.txt", graph, points);

  // read a request
  Point sPoint, ePoint;
  
  // Read a request from the plotter
  int ret_val = read_request(&sPoint, &ePoint, in);


  // c is guaranteed to be 'R', no need to error check

  // run dijkstra's algorithm, this is the unoptimized version that
  // does not stop when the end is reached but it is still fast enough
  while (ret_val != 1){
    
    // get the points closest to the two points we read
    int start = findClosest(sPoint, points), end = findClosest(ePoint, points);


    unordered_map<int, PIL> tree;
    dijkstra(graph, start, tree);

    // NOTE: in Part II you will use a different communication protocol than Part I
    // So edit the code below to implement this protocol

    // no path
    if (tree.find(end) == tree.end()) {
        char message[BUFFER_SIZE] = "Already at destination\n";
        if (write(out, message, BUFFER_SIZE) < 0){
          cout << "write failed" << endl;
        }
    }
    else {
      // read off the path by stepping back through the search tree
      list<int> path;
      while (end != start) {
        path.push_front(end);
        end = tree[end].first;
      }
      path.push_front(start);

      // No need to output all those N and W
      // // output the path
      // cout << "N " << path.size() << endl;

      // // c is guaranteed to be 'A', no need to error check
      // cin >> c;

      for (int v : path) {
        // Need to construct string here
        string latitude = to_string(double(points[v].lat)/100000);
        latitude.pop_back();

        string coordinate = latitude + " " + to_string(double(points[v].lon)/100000);
        char buffer[BUFFER_SIZE];
        for (int i = 0; i < int(coordinate.size()); i++){
          buffer[i] = coordinate[i];
        }
        
        // Erase the end of string character
        // Replace with new line character
        buffer[coordinate.size() - 1] = '\n';
        
        // Write the string to out_pipe with error checking
        if (write(out, buffer, coordinate.size()) < 0){
          cout << "write failed" << endl;
        }

      }
    }
    
    // Write the character indicating that all waypoints have been printed
    char buffer[3] = "E\n";
    if (write(out, buffer, 2*sizeof(char)) < 0){
        cout << "write failed" << endl;
    }

    memset(buffer, 0, 3);
    // Immediately listen for the next request
    ret_val = read_request(&sPoint, &ePoint, in);

  }
  // Pipe closed from server end
  // Close pipe
  if (close(in) < 0 || close(out) < 0){
    cout << "close failed" << endl;
    exit(1);
  }
  
  // Unlink pipe
  unlink(inpipe);
  unlink(outpipe);
  return 0;
}
