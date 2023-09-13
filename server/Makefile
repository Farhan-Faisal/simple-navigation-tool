# Makefile contents here
CC = g++
CFLAGS = -Wall

server: server.o digraph.o dijkstra.o
	@$(CC) $(CFLAGS) -o server server.o digraph.o dijkstra.o

server.o: server.cpp dijkstra.h
	@$(CC) $(CFLAGS) -c server.cpp

digraph.o: digraph.cpp dijkstra.h
	@$(CC) $(CFLAGS) -c digraph.cpp

dijkstra.o: dijkstra.cpp wdigraph.h dijkstra.h
	@$(CC) $(CFLAGS) -c dijkstra.cpp

.PHONY : clean
clean:
	@-rm *.o server